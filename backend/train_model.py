import pandas as pd
import numpy as np
import pickle
import os
import re
import json
import zipfile
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, accuracy_score
from sklearn.base import BaseEstimator, TransformerMixin

# --- HOTFIX FOR HTTPX / DATASETS COMPATIBILITY ---
# Patches newer httpx versions to work with sentence_transformers
try:
    import httpx
    if not hasattr(httpx, 'RequestError'):
        httpx.RequestError = httpx.HTTPError
except ImportError:
    pass

# --- Configuration ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
# Priority: Check for CSV first, then Zip
CSV_PATH = os.path.join(BASE_DIR, "job_dataset.csv")
ZIP_PATH = os.path.join(BASE_DIR, "archive (3).zip")
MODEL_PATH = os.path.join(BASE_DIR, 'resume_classifier.pkl')

class BERTVectorizer(BaseEstimator, TransformerMixin):
    """
    Custom Transformer to generate Semantic Embeddings using Sentence Transformers.
    """
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.model_name = model_name
        self.model = None

    def fit(self, X, y=None):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError("Please install sentence-transformers: pip install sentence-transformers")
            
        if self.model is None:
            print(f"Loading {self.model_name} model (this requires internet the first time)...")
            try:
                self.model = SentenceTransformer(self.model_name)
            except Exception as e:
                print("\n" + "="*60)
                print("🚨 NETWORK ERROR: INTERNET CONNECTION REQUIRED 🚨")
                print(f"Failed to download the AI model '{self.model_name}' from HuggingFace.")
                print("Please ensure your internet is active and no firewall/VPN is blocking Python.")
                print("="*60 + "\n")
                raise RuntimeError("Internet connection required to download AI model weights.") from e
        return self

    def transform(self, X):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError("Please install sentence-transformers: pip install sentence-transformers")

        if self.model is None:
            try:
                self.model = SentenceTransformer(self.model_name)
            except Exception as e:
                raise RuntimeError("Internet connection required to download AI model weights.") from e
        
        # Ensure input is a list of strings
        if hasattr(X, 'tolist'):
            texts = X.tolist()
        else:
            texts = list(X)
            
        print("Generating semantic embeddings...")
        embeddings = self.model.encode(texts, show_progress_bar=True, normalize_embeddings=True)
        return embeddings

def infer_role_from_text(text):
    text = text.lower()
    keywords = {
        "Data Scientist": ["data scientist", "data science", "machine learning", "deep learning", "pandas", "numpy", "tensorflow"],
        "Python Developer": ["python developer", "django", "flask", "fastapi", "scripting"],
        "Java Developer": ["java developer", "spring boot", "hibernate", "j2ee", "maven"],
        "Web Developer": ["web developer", "react", "angular", "javascript", "html", "css", "node.js"],
        "DevOps Engineer": ["devops", "docker", "kubernetes", "aws", "ci/cd", "jenkins", "terraform"],
        "HR Manager": ["human resources", "recruiting", "talent acquisition", "employee relations"],
        "Project Manager": ["project manager", "scrum master", "agile", "stakeholder management", "pmp"]
    }
    
    for role in keywords:
        if role.lower() in text:
            return role
            
    scores = {role: 0 for role in keywords}
    for role, skills in keywords.items():
        for skill in skills:
            if skill in text:
                scores[role] += 1
    
    best_role = max(scores, key=scores.get)
    return best_role if scores[best_role] > 0 else "General"

def load_zip_data(zip_path):
    print(f"Extracting data from {zip_path}...")
    data_entries = []
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file in zip_ref.namelist():
                if file.endswith(".json") or file.endswith(".jsonl"):
                    with zip_ref.open(file) as f:
                        try:
                            content = f.read().decode('utf-8')
                            json_data = []
                            if file.endswith(".jsonl"):
                                for line in content.splitlines():
                                    if line.strip():
                                        json_data.append(json.loads(line))
                            else:
                                parsed = json.loads(content)
                                if isinstance(parsed, list):
                                    json_data = parsed
                                elif isinstance(parsed, dict):
                                    json_data = [parsed]

                            for item in json_data:
                                text = ""
                                label = None
                                if "data" in item and isinstance(item["data"], dict):
                                    text = item["data"].get("text", "")
                                    try:
                                        label = item['annotations'][0]['result'][0]['value']['choices'][0]
                                    except:
                                        label = None
                                elif "messages" in item:
                                    texts = [m.get('content', '') for m in item.get('messages', [])]
                                    text = " ".join(texts)
                                elif "resume_text" in item:
                                    text = item["resume_text"]
                                    label = item.get("Applied_Job_Role")
                                elif "text" in item:
                                    text = item["text"]
                                    label = item.get("label") or item.get("category")

                                if text:
                                    if not label:
                                        label = infer_role_from_text(text)
                                    data_entries.append({"text_features": text, "Applied_Job_Role": label})
                        except Exception as e:
                            print(f"Skipping file {file}: {e}")

                elif file.endswith(".csv"):
                    with zip_ref.open(file) as f:
                        try:
                            # FIX: Skip bad lines to avoid the tokenizing crash
                            try:
                                df_temp = pd.read_csv(f, on_bad_lines='skip')
                            except TypeError:
                                # Fallback for older Pandas versions
                                df_temp = pd.read_csv(f, error_bad_lines=False)

                            text_col = next((c for c in df_temp.columns if 'resume' in c.lower() or 'text' in c.lower()), None)
                            label_col = next((c for c in df_temp.columns if 'category' in c.lower() or 'role' in c.lower()), None)
                            
                            if text_col:
                                for _, row in df_temp.iterrows():
                                    text = str(row[text_col])
                                    label = str(row[label_col]) if label_col else infer_role_from_text(text)
                                    data_entries.append({"text_features": text, "Applied_Job_Role": label})
                        except Exception as e:
                            print(f"Error processing CSV {file}: {e}")
                            
    except zipfile.BadZipFile:
        print("Error: The zip file is corrupted.")
        return pd.DataFrame()
        
    print(f"✅ Extracted {len(data_entries)} resumes from zip.")
    return pd.DataFrame(data_entries)

def load_data():
    """Loads and merges both job_dataset.csv and zip data."""
    print("Loading datasets...")
    frames = []

    # 1. Load from job_dataset.csv
    if os.path.exists(CSV_PATH):
        print(f"Found CSV dataset at: {CSV_PATH}")
        try:
            df_csv = pd.read_csv(CSV_PATH)
            
            # Helper to safely get column string
            def get_col(df, col_name):
                if col_name in df.columns:
                    return df[col_name].fillna('').astype(str)
                return pd.Series([''] * len(df))

            # Feature Engineering for CSV
            df_csv['text_features'] = (
                get_col(df_csv, 'Skills') + " " + 
                get_col(df_csv, 'Responsibilities') + " " + 
                get_col(df_csv, 'Keywords') + " " + 
                get_col(df_csv, 'ExperienceLevel')
            ).str.lower()
            
            # Target Engineering
            if 'Title' in df_csv.columns:
                df_csv['Applied_Job_Role'] = df_csv['Title']
            
            if 'text_features' in df_csv.columns and 'Applied_Job_Role' in df_csv.columns:
                frames.append(df_csv[['text_features', 'Applied_Job_Role']])
                print(f"Loaded {len(df_csv)} records from CSV.")
        except Exception as e:
            print(f"Error reading CSV: {e}")

    # 2. Load from Zip
    if os.path.exists(ZIP_PATH):
        df_zip = load_zip_data(ZIP_PATH)
        if not df_zip.empty and 'text_features' in df_zip.columns and 'Applied_Job_Role' in df_zip.columns:
            frames.append(df_zip[['text_features', 'Applied_Job_Role']])
            print(f"Loaded {len(df_zip)} records from Zip.")
    
    if not frames:
        return pd.DataFrame()
        
    return pd.concat(frames, ignore_index=True)

def train():
    print("--- Training Resume Classifier (KNN on Merged Datasets) ---")
    
    # 1. Load Data
    df = load_data()

    if len(df) == 0:
        print("❌ No data available for training. Ensure 'job_dataset.csv' or 'archive (3).zip' exists.")
        return

    # Clean Data: Drop NaNs to prevent "ValueError: Input contains NaN"
    print(f"Original dataset size: {len(df)}")
    df = df.dropna(subset=['text_features', 'Applied_Job_Role'])
    # Ensure text_features are strings to avoid encoding issues with non-string objects (if any slipped through)
    df['text_features'] = df['text_features'].astype(str)
    print(f"Dataset size after cleaning: {len(df)}")

    if len(df) == 0:
        print("❌ No valid data available after cleaning.")
        return

    # 2. Prepare X and y
    print(f"Total Training Data: {len(df)} documents.")
    X = df['text_features']
    y = df['Applied_Job_Role']

    # 3. Split Data
    if len(df) < 5:
        X_train, X_test, y_train, y_test = X, X, y, y
    else:
        # Check class distribution for stratification
        class_counts = y.value_counts()
        if class_counts.min() > 1:
            stratify_param = y
        else:
            stratify_param = None
            
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=stratify_param
        )

    # 4. Define Pipeline
    print("Initializing KNN Pipeline...")
    pipeline = Pipeline([
        ('bert', BERTVectorizer(model_name='all-MiniLM-L6-v2')),
        ('clf', KNeighborsClassifier(n_neighbors=5, metric='cosine', weights='distance'))
    ])

    # 5. Fit
    print("Fitting model...")
    pipeline.fit(X_train, y_train)

    # 6. Evaluate
    print("Evaluating model...")
    y_pred = pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\n✅ Model Accuracy: {accuracy:.4f}")

    if len(df) > 10:
        # Top-K Accuracy
        try:
            print("Calculating Top-K Accuracy...")
            probs = pipeline.predict_proba(X_test)
            classes = pipeline.classes_
            
            for k in [3, 5]:
                if len(classes) >= k:
                    top_k_indices = np.argsort(probs, axis=1)[:, -k:]
                    top_k_classes = classes[top_k_indices]
                    
                    y_test_arr = np.array(y_test)
                    top_k_hits = [y_true in preds for y_true, preds in zip(y_test_arr, top_k_classes)]
                    top_k_acc = np.mean(top_k_hits)
                    print(f"✅ Top-{k} Accuracy: {top_k_acc:.4f}")
        except Exception as e:
            print(f"⚠️ Could not calculate Top-K Accuracy: {e}")

        print("\nClassification Report (Sample):")
        print(classification_report(y_test, y_pred, zero_division=0))

    # 7. Save
    print(f"Saving model to {MODEL_PATH}...")
    try:
        with open(MODEL_PATH, 'wb') as f:
            pickle.dump(pipeline, f)
        print("✅ Model saved successfully!")
    except Exception as e:
        print(f"❌ Error saving model: {e}")

if __name__ == "__main__":
    train()