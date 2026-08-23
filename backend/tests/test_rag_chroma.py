"""Comprehensive tests for Sentence Transformers + ChromaDB RAG retrieval pipeline."""
import os
import shutil
import tempfile
import pytest

from app import db, seed
from backend.app.services import rag


@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup clean SQLite and ChromaDB test directories."""
    temp_dir = tempfile.mkdtemp()
    chroma_path = os.path.join(temp_dir, "chroma_test_db")
    db_path = os.path.join(temp_dir, "test.db")
    
    os.environ["TCI_DB_PATH"] = db_path
    os.environ["CHROMA_DB_PATH"] = chroma_path
    os.environ["CHROMA_COLLECTION_NAME"] = "test_telecom_kb"
    os.environ["EMBEDDING_MODEL"] = "all-MiniLM-L6-v2"
    os.environ["TOP_K"] = "3"
    
    # Reset singletons
    rag._embedding_model = None
    rag._chroma_client = None
    rag.CHROMA_DB_PATH = chroma_path
    rag.CHROMA_COLLECTION_NAME = "test_telecom_kb"
    rag.EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    rag.TOP_K = 3

    db.init_db()
    seed.seed_accounts()
    seed.seed_kb()

    yield

    # Teardown
    rag._embedding_model = None
    rag._chroma_client = None
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_chroma_and_embedding_initialization():
    """Test ChromaDB client and SentenceTransformer model lazy initialization."""
    model = rag.get_embedding_model()
    assert model is not None
    client = rag.get_chroma_client()
    assert client is not None
    collection = rag.get_collection()
    assert collection.name == "test_telecom_kb"


def test_document_indexing_and_count():
    """Test indexing KB documents and verifying ChromaDB count."""
    count = rag.rebuild_index()
    assert count > 0
    
    collection = rag.get_collection()
    assert collection.count() == count


def test_duplicate_document_indexing():
    """Test that indexing duplicate documents updates/upserts rather than duplicating or failing."""
    count1 = rag.rebuild_index()
    collection = rag.get_collection()
    initial_count = collection.count()
    assert initial_count == count1

    # Re-indexing same documents
    count2 = rag.rebuild_index()
    assert count2 == count1
    assert collection.count() == initial_count


def test_empty_query():
    """Test empty query handling."""
    rag.rebuild_index()
    assert rag.retrieve("") == []
    assert rag.retrieve("   ") == []
    assert rag.retrieve(None) == []


def test_empty_collection():
    """Test query on empty collection before indexing (should auto-rebuild or return empty)."""
    # Empty documents
    results = rag.retrieve("broadband down")
    assert isinstance(results, list)


def test_semantic_retrieval_recharge_issue():
    """Test semantic query retrieval for recharge issue."""
    rag.rebuild_index()
    query = "I recharged my phone but plan is still not active and money was deducted"
    results = rag.retrieve(query, top_k=2, kinds=("sop",))
    
    assert len(results) > 0
    top_hit = results[0]
    assert "doc_id" in top_hit
    assert "title" in top_hit
    assert "body" in top_hit
    assert "similarity" in top_hit
    assert 0.0 <= top_hit["similarity"] <= 1.0
    assert "Recharge" in top_hit["title"] or "billing" in top_hit["category"].lower()


def test_semantic_retrieval_router_issue():
    """Test semantic query retrieval for router red light issue."""
    rag.rebuild_index()
    query = "my wifi router has red light and internet not working"
    results = rag.retrieve(query, top_k=2, kinds=("sop",))
    
    assert len(results) > 0
    top_hit = results[0]
    assert "Router" in top_hit["title"] or "network" in top_hit["category"]
    assert top_hit["similarity"] >= 0.3


def test_retrieval_kinds_filtering():
    """Test filtering by doc kind."""
    rag.rebuild_index()
    sop_results = rag.retrieve("broadband down", top_k=5, kinds=("sop",))
    for doc in sop_results:
        assert doc["kind"] == "sop"

    incident_results = rag.retrieve("Raj Nagar node failure", top_k=5, kinds=("incident_writeup",))
    for doc in incident_results:
        assert doc["kind"] == "incident_writeup"


def test_persistence_across_reconnect():
    """Test that ChromaDB persists vectors to disk when reconnecting client."""
    count = rag.rebuild_index()
    assert count > 0

    # Simulate application restart: clear memory singletons and reconnect
    rag._chroma_client = None
    rag._embedding_model = None

    reloaded_client = rag.get_chroma_client()
    reloaded_col = reloaded_client.get_collection("test_telecom_kb")
    assert reloaded_col.count() == count

    results = rag.retrieve("router red light", top_k=1)
    assert len(results) == 1
    assert "Router" in results[0]["title"]
