"""Layer 5B/6 support — knowledge-base retrieval over SOPs, past resolved tickets
and incident write-ups.

Vector Retrieval using Sentence Transformers (all-MiniLM-L6-v2) and ChromaDB.
Eliminates TF-IDF and manual cosine similarity calculations in favor of dense
vector embeddings and persistent ChromaDB collection querying.
"""
import logging
import os
from typing import Any, Dict, List, Optional, Sequence, Union

import chromadb
from sentence_transformers import SentenceTransformer

from .. import db
from .etl import normalize_hinglish

logger = logging.getLogger(__name__)

# Configurable embedding model and ChromaDB persistence settings
EMBEDDING_MODEL = os.environ.get(
    "EMBEDDING_MODEL",
    os.environ.get("TCI_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
)
CHROMA_DB_PATH = os.environ.get(
    "CHROMA_DB_PATH",
    os.environ.get(
        "TCI_CHROMA_DIR",
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "chroma_db")
    )
)
CHROMA_COLLECTION_NAME = os.environ.get(
    "CHROMA_COLLECTION_NAME",
    os.environ.get("TCI_CHROMA_COLLECTION", "telecom_rag_kb")
)
TOP_K = int(os.environ.get("TOP_K", "3"))

_embedding_model: Optional[SentenceTransformer] = None
_chroma_client: Optional[chromadb.PersistentClient] = None


def get_embedding_model() -> SentenceTransformer:
    """Get or lazily initialize the SentenceTransformer embedding model singleton."""
    global _embedding_model
    if _embedding_model is None:
        try:
            logger.info(f"[RAG] Loading SentenceTransformer embedding model: {EMBEDDING_MODEL}")
            _embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        except Exception as exc:
            logger.error(f"[RAG] Failed to load SentenceTransformer model '{EMBEDDING_MODEL}': {exc}")
            raise
    return _embedding_model


def get_chroma_client() -> chromadb.PersistentClient:
    """Get or lazily initialize the persistent ChromaDB client."""
    global _chroma_client
    if _chroma_client is None:
        try:
            os.makedirs(CHROMA_DB_PATH, exist_ok=True)
            logger.info(f"[RAG] Initializing persistent ChromaDB client at: {CHROMA_DB_PATH}")
            _chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        except Exception as exc:
            logger.error(f"[RAG] Failed to initialize ChromaDB PersistentClient at '{CHROMA_DB_PATH}': {exc}")
            raise
    return _chroma_client


def get_collection():
    """Get or create the ChromaDB collection configured for cosine distance."""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=CHROMA_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )


def add_documents_to_chroma(documents: list[dict]) -> int:
    """Index or upsert prepared documents into ChromaDB with SentenceTransformer embeddings.
    
    Handles:
    - Empty document list
    - Invalid documents (missing title/body/doc_id)
    - Duplicate IDs (deduplicated preserving latest)
    - Embedding and ChromaDB upsert errors
    """
    if not documents or not isinstance(documents, list):
        logger.warning("[RAG] add_documents_to_chroma called with empty or invalid document list.")
        return 0

    valid_docs: dict[str, dict] = {}
    for idx, doc in enumerate(documents):
        if not isinstance(doc, dict):
            continue
        doc_id = str(doc.get("doc_id") or f"doc_{idx}").strip()
        if not doc_id:
            doc_id = f"doc_{idx}"
        
        title = str(doc.get("title") or "").strip()
        body = str(doc.get("body") or "").strip()
        if not title and not body:
            # Skip invalid document with neither title nor body
            continue

        valid_docs[doc_id] = {
            "doc_id": doc_id,
            "kind": str(doc.get("kind") or "generic"),
            "title": title,
            "body": body,
            "category": str(doc.get("category") or ""),
        }

    if not valid_docs:
        logger.warning("[RAG] No valid documents to index after validation.")
        return 0

    docs_list = list(valid_docs.values())

    try:
        model = get_embedding_model()
        collection = get_collection()

        ids = [d["doc_id"] for d in docs_list]
        texts_to_embed = [normalize_hinglish(f"{d['title']}\n{d['body']}".strip()) for d in docs_list]
        
        embeddings = model.encode(texts_to_embed, convert_to_numpy=True).tolist()

        metadatas = [
            {
                "doc_id": d["doc_id"],
                "kind": d["kind"],
                "title": d["title"],
                "category": d["category"],
            }
            for d in docs_list
        ]
        doc_bodies = [d["body"] for d in docs_list]

        collection.upsert(
            ids=ids,
            documents=doc_bodies,
            embeddings=embeddings,
            metadatas=metadatas
        )
        logger.info(f"[RAG] Successfully upserted {len(docs_list)} documents to ChromaDB collection '{CHROMA_COLLECTION_NAME}'.")
        return len(docs_list)
    except Exception as exc:
        logger.error(f"[RAG] Error during add_documents_to_chroma: {exc}", exc_info=True)
        return 0


def rebuild_index(force: bool = False) -> int:
    """Index SOP/FAQ docs + incident write-ups + a sample of resolved tickets into ChromaDB."""
    try:
        if not force:
            try:
                coll = get_collection()
                count = coll.count()
                if count > 0:
                    logger.info(f"[RAG] ChromaDB index already populated ({count} documents). Skipping redundant rebuild.")
                    return count
            except Exception:
                pass

        conn = db.connect()
        docs = [dict(r) for r in conn.execute(
            "SELECT doc_id, kind, title, body, category FROM kb_docs")]
        resolved = conn.execute(
            "SELECT complaint_id, text, category, resolution FROM complaints "
            "WHERE status='closed' AND resolution IS NOT NULL AND resolution != '' LIMIT 300").fetchall()
        for r in resolved:
            docs.append({
                "doc_id": f"resolved_{r['complaint_id']}",
                "kind": "resolved_ticket",
                "title": f"Resolved ticket {r['complaint_id']}",
                "body": f"Complaint: {r['text']} Resolution: {r['resolution']}",
                "category": r["category"] or ""
            })

        if not docs:
            logger.info("[RAG] No documents found in database to index.")
            return 0

        return add_documents_to_chroma(docs)
    except Exception as exc:
        logger.error(f"[RAG] Failed to rebuild index: {exc}", exc_info=True)
        return 0



def retrieve(query: str, top_k: int = TOP_K, kinds: tuple | None = None) -> list[dict]:
    """Top-k most similar KB docs using ChromaDB vector retrieval and SentenceTransformer query embeddings.
    
    Handles:
    - Empty query string
    - Empty collection (attempts auto-rebuild)
    - Kinds filtering
    - Graceful fallback on retrieval errors
    """
    if not query or not str(query).strip():
        return []

    try:
        collection = get_collection()
        total_docs = collection.count()
        if total_docs == 0:
            logger.info("[RAG] ChromaDB collection is empty. Triggering rebuild_index...")
            rebuild_index()
            total_docs = collection.count()
            if total_docs == 0:
                logger.warning("[RAG] ChromaDB collection remains empty after rebuild.")
                return []

        model = get_embedding_model()
        normalized_query = normalize_hinglish(str(query).strip())
        query_emb = model.encode([normalized_query], convert_to_numpy=True).tolist()

        where_filter = None
        if kinds:
            if len(kinds) == 1:
                where_filter = {"kind": kinds[0]}
            elif len(kinds) > 1:
                where_filter = {"kind": {"$in": list(kinds)}}

        effective_k = top_k if top_k is not None and top_k > 0 else TOP_K
        n_results = min(effective_k, total_docs) if total_docs > 0 else effective_k
        if n_results <= 0:
            return []

        # Vector retrieval via ChromaDB query mechanism (no manual cosine similarity)
        results = collection.query(
            query_embeddings=query_emb,
            n_results=n_results,
            where=where_filter,
            include=["metadatas", "documents", "distances"]
        )

        out = []
        if results and results.get("ids") and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                doc_id = results["ids"][0][i]
                meta = results["metadatas"][0][i] if results.get("metadatas") else {}
                body = results["documents"][0][i] if results.get("documents") else ""
                dist = results["distances"][0][i] if results.get("distances") else 1.0

                # In ChromaDB cosine space {"hnsw:space": "cosine"}, distance d = 1 - cos(theta)
                # Map distance to similarity score in [0.0, 1.0]
                similarity = max(0.0, min(1.0, 1.0 - dist))

                if similarity < 0.05:
                    continue

                out.append({
                    "doc_id": meta.get("doc_id", doc_id),
                    "kind": meta.get("kind", ""),
                    "title": meta.get("title", ""),
                    "body": body,
                    "category": meta.get("category", ""),
                    "similarity": round(float(similarity), 3),
                })

        return out
    except Exception as exc:
        logger.error(f"[RAG] Error during retrieval for query '{query}': {exc}", exc_info=True)
        return []


# Semantic alias
retrieve_relevant_documents = retrieve
