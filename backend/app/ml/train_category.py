"""Offline Category Classification Model Training.

Trains a TF-IDF + Logistic Regression model on an augmented telecom complaint
taxonomy and evaluates on a held-out stratified test split (25%).

Saves artifacts using Joblib to the models/ directory:
- category_model.joblib
- category_vectorizer.joblib
- category_metrics.json

Usage:
    python -m app.ml.train_category
    or:
    python backend/app/ml/train_category.py
"""
import json
import logging
import os
import random
import sys

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
"""Offline Category Classification Model Training.

Trains a TF-IDF + Multi-Label Logistic Regression (OneVsRest) model on an augmented
telecom complaint taxonomy and evaluates on a held-out test split.

Supports multi-label classification for complaints addressing multiple issue domains
(e.g., Network, Billing, and Service simultaneously).

Saves artifacts using Joblib to the models/ directory:
- category_model.joblib
- category_vectorizer.joblib
- category_mlb.joblib
- category_metrics.json

Usage:
    python -m app.ml.train_category
    or:
    python backend/app/ml/train_category.py
"""
import json
import logging
import os
import random
import sys
from typing import List, Tuple, Union

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.metrics import accuracy_score, classification_report, f1_score, precision_score, recall_score, hamming_loss
from sklearn.model_selection import train_test_split

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Base directory paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(CURRENT_DIR, "models")
MODEL_PATH = os.path.join(MODELS_DIR, "category_model.joblib")
VECTORIZER_PATH = os.path.join(MODELS_DIR, "category_vectorizer.joblib")
MLB_PATH = os.path.join(MODELS_DIR, "category_mlb.joblib")
METRICS_PATH = os.path.join(MODELS_DIR, "category_metrics.json")

# Telecom domain category taxonomy
CATEGORIES = ["network", "billing", "service", "device", "other"]

# Annotated representative telecom complaint corpus (English, Hindi transliteration, Hinglish)
# Supports single-label and multi-label composite complaints
_BASE_CORPUS: List[Tuple[str, Union[str, List[str]]]] = [
    # --- Network ---
    ("broadband down no connectivity in my area since morning", ["network"]),
    ("internet not working router shows red light", ["network"]),
    ("wifi completely dead since last night neighbours also affected", ["network"]),
    ("frequent call drops when talking for a few minutes", ["network"]),
    ("call quality very bad voice keeps cutting", ["network"]),
    ("mobile data extremely slow pages take forever to load", ["network"]),
    ("4g speed very slow this week barely one mbps", ["network"]),
    ("no signal inside my house since yesterday evening", ["network"]),
    ("network gone totally cannot make any calls", ["network"]),
    ("fiber connection keeps disconnecting every hour", ["network"]),
    ("internet speed dropped drastically after recharge", ["network"]),
    ("5g network showing but no data passing through", ["network"]),
    ("net nahi chal raha hai subah se internet band hai", ["network"]),
    ("wifi connect nahi ho raha hai signal weak hai", ["network"]),
    ("calling issue call disconnect ho raha hai baar baar", ["network"]),
    ("data speed bahut slow hai video buffering ho rahi hai", ["network"]),
    ("no network tower signal red light blinking on modem", ["network"]),
    ("broadband fiber line broken during construction work", ["network"]),
    ("high latency ping spike playing online games impossible", ["network"]),
    ("sim showing emergency calls only no cellular service", ["network"]),

    # --- Billing ---
    ("charged twice for my monthly plan need refund immediately", ["billing"]),
    ("extra charges added to bill which i never used", ["billing"]),
    ("recharge not reflecting but money deducted from bank", ["billing"]),
    ("international roaming pack charged but never activated", ["billing"]),
    ("autopay deducted twice this month very frustrating", ["billing"]),
    ("bill amount wrong this cycle overcharged for data", ["billing"]),
    ("refund pending for one month for failed recharge", ["billing"]),
    ("hidden charges on my postpaid bill every month", ["billing"]),
    ("payment successful but plan not credited money gone", ["billing"]),
    ("wrong late fee added even though payment was on time", ["billing"]),
    ("bill me extra charge laga diya refund kab milega", ["billing"]),
    ("paise cut gaye par recharge activate nahi hua", ["billing"]),
    ("balance kat gaya bina kisi reason ke refund chahiye", ["billing"]),
    ("invoice wrong amount GST calculation incorrect on bill", ["billing"]),
    ("auto debit done two times refund transaction id provided", ["billing"]),
    ("payment failed at gateway amount debited from account", ["billing"]),
    ("tariff plan cost increased without prior notification", ["billing"]),
    ("security deposit refund not credited after connection cancellation", ["billing"]),

    # --- Service ---
    ("requested plan upgrade a week ago still not activated", ["service"]),
    ("new connection installation pending for ten days despite payment", ["service"]),
    ("sim porting request stuck no update from support", ["service"]),
    ("waiting two weeks for new connection no response", ["service"]),
    ("customer care keeps disconnecting my call no resolution", ["service"]),
    ("service request closed without actually fixing anything", ["service"]),
    ("shifting connection to new address taking forever", ["service"]),
    ("plan change requested but old plan still active", ["service"]),
    ("technician never arrived for scheduled appointment", ["service"]),
    ("executive misbehaved on customer care call need escalation", ["service"]),
    ("naya connection lagwane ke liye apply kiya tha koi nahi aaya", ["service"]),
    ("porting request reject kardi without valid reason", ["service"]),
    ("address change request pending for 15 days", ["service"]),
    ("kyc verification stuck unable to activate sim card", ["service"]),
    ("appointment booked for fiber installation engineer did not visit", ["service"]),
    ("service ticket marked resolved without customer confirmation", ["service"]),
    ("esim activation qr code not received on registered email", ["service"]),
    ("dnd service not working still getting spam promotional calls", ["service"]),

    # --- Device ---
    ("router provided by company keeps restarting every hour", ["device"]),
    ("set top box remote not working need replacement", ["device"]),
    ("company modem hangs repeatedly needs replacement", ["device"]),
    ("5g not working on my new phone even though plan supports it", ["device"]),
    ("ont device blinking red light needs replacement", ["device"]),
    ("sim card not detected in phone after damage", ["device"]),
    ("router overheating and dropping wifi need new unit", ["device"]),
    ("power adapter of modem burnt need new adapter", ["device"]),
    ("set top box not turning on power light is off", ["device"]),
    ("landline instrument dead no dial tone handset issue", ["device"]),
    ("modem baar baar band ho raha hai restart problem", ["device"]),
    ("remote control buttons not working set top box stuck", ["device"]),
    ("ont router defective unit please replace under warranty", ["device"]),
    ("lan port on router not functioning ethernet not detected", ["device"]),
    ("device overheating turning off automatically after 10 minutes", ["device"]),

    # --- Other ---
    ("app login not working otp never arrives", ["other"]),
    ("want to know about family plan options and pricing", ["other"]),
    ("how do i check my remaining data balance", ["other"]),
    ("update my email address and mobile number on the account", ["other"]),
    ("website not letting me download my invoice pdf", ["other"]),
    ("need gst invoice for my corporate connection tax filing", ["other"]),
    ("app crash on opening payment page unable to login", ["other"]),
    ("information required for international roaming packs and rates", ["other"]),
    ("change account ownership transfer connection to family member", ["other"]),
    ("app me login nahi ho raha otp receive nahi ho raha", ["other"]),
    ("profile details update karni hai email and phone number", ["other"]),
    ("corporate business plan enquiry need sales representative contact", ["other"]),

    # --- Multi-Label Composite Complaints (Network + Billing + Service, etc.) ---
    ("internet down broadband not working, charged twice on bill, and service installation pending", ["network", "billing", "service"]),
    ("wifi connectivity dead since morning, money deducted from account without plan, and customer service technician not responding", ["network", "billing", "service"]),
    ("facing network issue with slow internet speed, extra billing deduction, and pending service request", ["network", "billing", "service"]),
    ("broadband fiber cut no internet, overcharged on monthly bill invoice, and support service appointment missed", ["network", "billing", "service"]),
    ("internet connectivity broken, wrong billing amount charged, and customer care service unresolved", ["network", "billing", "service"]),
    ("net band hai, bill me extra paise kat gaye aur customer service koi response nahi de rahi", ["network", "billing", "service"]),
    ("wifi signal weak no data, double payment recharge deducted, and installation technician never visited", ["network", "billing", "service"]),
    
    # Network + Billing
    ("internet not working and extra charges added to my monthly bill", ["network", "billing"]),
    ("broadband connectivity down after money deducted for recharge", ["network", "billing"]),
    ("data speed slow and charged twice for monthly subscription", ["network", "billing"]),
    ("wifi dead and overcharged on invoice need refund and speed fix", ["network", "billing"]),

    # Network + Service
    ("broadband fiber broken and technician did not show up for appointment", ["network", "service"]),
    ("internet connection not working and porting request stuck with support", ["network", "service"]),
    ("frequent call drops and customer service ticket closed without fixing", ["network", "service"]),
    ("wifi not working and waiting for new connection activation", ["network", "service"]),

    # Network + Device
    ("router overheating and dropping internet wifi connection constantly", ["network", "device"]),
    ("ont modem blinking red light and broadband connectivity down", ["network", "device"]),
    ("set top box wifi disconnected and network streaming buffering", ["network", "device"]),

    # Billing + Service
    ("charged extra fee on bill and technician never arrived for installation", ["billing", "service"]),
    ("money deducted for plan upgrade but customer care service not activating", ["billing", "service"]),
    ("double payment charged and customer service request rejected", ["billing", "service"]),
]

_FILLERS = [
    "please help", "very urgent", "since yesterday", "this is bad", "second time",
    "kindly resolve", "asap", "really frustrated", "in my locality", "immediately",
    "customer support", "facing problem", "kripya madad kare", "jaldi theek kare", ""
]


def _normalize(text: str) -> str:
    """Normalize Hinglish / text strings for consistent tokenization."""
    t = text.lower().strip()
    # Basic Hinglish expansions
    substitutions = {
        "nahi": "not", "band": "down", "kharab": "bad", "paise": "money",
        "kaam": "work", "subah": "morning", "karo": "do", "kripya": "please",
        "jaldi": "urgent", "madad": "help", "baar": "time", "naya": "new"
    }
    for k, v in substitutions.items():
        t = t.replace(k, v)
    return t


def _augment_corpus(corpus: List[Tuple[str, Union[str, List[str]]]], rng: random.Random) -> List[Tuple[str, List[str]]]:
    """Augment labeled seed data with word dropout, noise injection, and suffix perturbation."""
    augmented = []
    for text, label in corpus:
        labels_list = [label] if isinstance(label, str) else list(label)
        words = text.split()
        # Original
        augmented.append((text, labels_list))
        # Word dropout
        if len(words) > 3:
            dropped = " ".join(w for w in words if rng.random() > 0.15)
            if dropped.strip():
                augmented.append((dropped, labels_list))
        # Suffix filler
        augmented.append((f"{text} {rng.choice(_FILLERS)}".strip(), labels_list))
        # Word order variation
        shuffled = words[:]
        rng.shuffle(shuffled)
        augmented.append((" ".join(shuffled), labels_list))
    return [(t, l) for t, l in augmented if t.strip()]


def train_and_save(random_state: int = 42) -> dict:
    """Train multi-label category classification pipeline and save artifacts."""
    logger.info("Starting offline training of Multi-Label Category Model...")
    os.makedirs(MODELS_DIR, exist_ok=True)
    
    rng = random.Random(random_state)
    augmented = _augment_corpus(_BASE_CORPUS, rng)
    
    texts = [_normalize(t) for t, _ in augmented]
    labels = [l for _, l in augmented]
    
    logger.info("Total augmented training samples: %d across %d classes", len(texts), len(CATEGORIES))
    
    # 1. MultiLabelBinarizer
    mlb = MultiLabelBinarizer(classes=CATEGORIES)
    y_bin = mlb.fit_transform(labels)
    
    # Stratified or random split for multi-label data
    x_train, x_test, y_train, y_test = train_test_split(
        texts, y_bin, test_size=0.25, random_state=random_state
    )
    
    # 2. TF-IDF Vectorizer
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        sublinear_tf=True,
        min_df=1,
        max_df=0.95
    )
    x_train_vec = vectorizer.fit_transform(x_train)
    x_test_vec = vectorizer.transform(x_test)
    
    # 3. Multi-Label Classifier (One-vs-Rest Logistic Regression with sigmoid probabilities)
    base_lr = LogisticRegression(
        C=10.0,
        max_iter=1000,
        class_weight="balanced",
        random_state=random_state
    )
    classifier = OneVsRestClassifier(base_lr)
    classifier.fit(x_train_vec, y_train)
    
    # 4. Evaluation on held-out test split
    predictions = classifier.predict(x_test_vec)
    
    acc = float(accuracy_score(y_test, predictions))
    prec_macro = float(precision_score(y_test, predictions, average="macro", zero_division=0))
    rec_macro = float(recall_score(y_test, predictions, average="macro", zero_division=0))
    f1_macro = float(f1_score(y_test, predictions, average="macro", zero_division=0))
    h_loss = float(hamming_loss(y_test, predictions))
    
    report = classification_report(
        y_test, predictions, target_names=CATEGORIES, output_dict=True, zero_division=0
    )
    
    metrics = {
        "accuracy": round(acc, 4),
        "precision_macro": round(prec_macro, 4),
        "recall_macro": round(rec_macro, 4),
        "macro_f1": round(f1_macro, 4),
        "hamming_loss": round(h_loss, 4),
        "train_samples": len(x_train),
        "test_samples": len(x_test),
        "categories": CATEGORIES,
        "classification_report": report
    }
    
    logger.info("Evaluation Results on Held-out Split:")
    logger.info("  Accuracy (Subset): %.4f", acc)
    logger.info("  Precision (Macro): %.4f", prec_macro)
    logger.info("  Recall (Macro):    %.4f", rec_macro)
    logger.info("  F1-Score (Macro):  %.4f", f1_macro)
    logger.info("  Hamming Loss:      %.4f", h_loss)
    
    # 5. Save artifacts with Joblib
    joblib.dump(classifier, MODEL_PATH)
    joblib.dump(vectorizer, VECTORIZER_PATH)
    joblib.dump(mlb, MLB_PATH)
    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
        
    logger.info("Saved category model to %s", MODEL_PATH)
    logger.info("Saved category vectorizer to %s", VECTORIZER_PATH)
    logger.info("Saved category mlb to %s", MLB_PATH)
    logger.info("Saved metrics to %s", METRICS_PATH)
    
    return metrics


if __name__ == "__main__":
    metrics = train_and_save()
    print(f"\nTraining complete. Macro-F1: {metrics['macro_f1']}, Accuracy: {metrics['accuracy']}")

