import pandas as pd
import numpy as np
import pickle
import os
import re
import json
import zipfile
import datetime
import gc
from sklearn.model_selection import train_test_split
from sklearn.neighbors import NearestCentroid
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score
from sklearn.base import BaseEstimator, TransformerMixin

# --- Configuration ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CSV_PATH = os.path.join(BASE_DIR, "job_dataset.csv")
ZIP_PATH = os.path.join(BASE_DIR, "archive (3).zip")
MODEL_PATH = os.path.join(BASE_DIR, 'resume_classifier.pkl')

class BERTVectorizer(BaseEstimator, TransformerMixin):
    def __init__(self, model_name='all-mpnet-base-v2'):
        self.model_name = model_name
        self.model = None

    def fit(self, X, y=None):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError("Please install sentence-transformers")
        if self.model is None:
            print(f"Loading {self.model_name}...")
            self.model = SentenceTransformer(self.model_name)
        return self

    def transform(self, X):
        if self.model is None: self.fit(X)
        texts = X.tolist() if hasattr(X, 'tolist') else list(X)
        return self.model.encode(texts, show_progress_bar=True, normalize_embeddings=True)

def infer_role_from_text(text):
    text = str(text).lower()
    keywords = {
        "Data Scientist": ["data science", "machine learning", "nlp", "pytorch", "tensorflow"],
        "Software Engineer": ["software engineer", "backend", "frontend", "full stack", "java", "python", "c#"],
        "Web Developer": ["react", "angular", "javascript", "node.js", "html", "css"],
        "DevOps Engineer": ["docker", "kubernetes", "aws", "azure", "ci/cd", "jenkins"],
        "HR Manager": ["recruiter", "human resources", "talent", "hiring"]
    }
    for role, keys in keywords.items():
        if any(k in text for k in keys): return role
    return "General Professional"

def load_data():
    all_data = []
    print(f">>> INFRA: Checking for training dataset at {ZIP_PATH}...")
    
    if os.path.exists(ZIP_PATH):
        try:
            with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
                # Find the largest CSV file in the zip
                csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
                if csv_files:
                    target_csv = max(csv_files, key=lambda f: zip_ref.getinfo(f).file_size)
                    print(f">>> INFRA: Training on {target_csv}...")
                    with zip_ref.open(target_csv) as f:
                        df = pd.read_csv(f)
                        
                        # Column Mapping for archive(3)
                        text_col = 'Resume_str' if 'Resume_str' in df.columns else next((c for c in df.columns if 'resume' in c.lower() or 'text' in c.lower()), None)
                        role_col = 'Category' if 'Category' in df.columns else next((c for c in df.columns if 'role' in c.lower() or 'category' in c.lower()), None)
                        
                        if text_col:
                            print(f">>> INFRA: Loaded {len(df)} professional samples.")
                            for _, row in df.iterrows():
                                all_data.append({
                                    "text": str(row[text_col]), 
                                    "role": str(row[role_col]) if role_col else infer_role_from_text(row[text_col])
                                })
        except Exception as e:
            print(f">>> INFRA ERROR: ZIP load failed: {e}")

    # Fallback to local CSV if ZIP fails
    if not all_data and os.path.exists(CSV_PATH):
        try:
            df = pd.read_csv(CSV_PATH)
            text_col = next((c for c in df.columns if 'resume' in c.lower() or 'text' in c.lower()), None)
            role_col = next((c for c in df.columns if 'role' in c.lower() or 'category' in c.lower()), None)
            if text_col:
                for _, row in df.iterrows():
                    all_data.append({"text": str(row[text_col]), "role": str(row[role_col]) if role_col else infer_role_from_text(row[text_col])})
        except: pass

    return pd.DataFrame(all_data)

def train():
    print("--- Training Hybrid Resume Intelligence (Centroid + Boosting) ---")
    df = load_data()
    if len(df) == 0: return

    # Merge Weak Classes
    counts = df['role'].value_counts()
    weak_classes = counts[counts < 10].index
    df['role'] = df['role'].apply(lambda x: 'General/Other' if x in weak_classes else x)
    print(f"Merged {len(weak_classes)} weak classes into 'General/Other'.")

    X = df['text']
    y = df['role']

    # Generate Embeddings (Once for both models)
    vectorizer = BERTVectorizer(model_name='all-mpnet-base-v2')
    print("Generating High-Precision Embeddings...")
    X_embeddings = vectorizer.fit_transform(X)

    # 1. Centroid Model (For Ranking)
    print("Training Centroid Model...")
    centroid_clf = NearestCentroid()
    centroid_clf.fit(X_embeddings, y)

    # 2. Boosting Model (For Validation)
    print("Training Boosting Model...")
    boosting_clf = HistGradientBoostingClassifier(max_iter=100, max_depth=5, random_state=42)
    boosting_clf.fit(X_embeddings, y)

    # Save as Hybrid Package
    model_package = {
        "vectorizer": vectorizer, # We'll swap this with mock in engine
        "centroid": centroid_clf,
        "boosting": boosting_clf,
        "classes": boosting_clf.classes_,
        "timestamp": datetime.datetime.now().isoformat()
    }

    print(f"Saving Hybrid Model to {MODEL_PATH}...")
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model_package, f)
    print("SUCCESS: Hybrid intelligence system deployed!")

if __name__ == "__main__":
    train()