import os
import re
import docx2txt
import pandas as pd
import pickle
import gc
import time
import requests
from pdfminer.high_level import extract_text as extract_pdf_text
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances
from pathlib import Path
import datetime
import numpy as np
import sys

# --- HUGGING FACE INFERENCE API SETUP ---
HF_TOKEN = os.environ.get("HF_TOKEN")
HF_API_URL = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"

def get_hf_embeddings(texts):
    """Fetches semantic embeddings directly from Hugging Face Cloud API to save RAM."""
    if not HF_TOKEN:
        print("⚠️ No HF_TOKEN found. Cannot use Hugging Face API.")
        return None
        
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    try:
        for attempt in range(3):
            response = requests.post(HF_API_URL, headers=headers, json={"inputs": texts}, timeout=20)
            if response.status_code == 200:
                return np.array(response.json())
            elif 'loading' in response.text.lower():
                print(f"⏳ HF Cloud Model is warming up (Attempt {attempt+1}/3)... waiting 5s.")
                time.sleep(5)
            else:
                print(f"❌ HF API Error: {response.text}")
                return None
    except Exception as e:
        print(f"❌ HF API Request failed: {e}")
        return None
    return None

# --- CRITICAL RENDER FREE TIER FIXES ---
os.environ["TOKENIZERS_PARALLELISM"] = "false" 

try:
    import transformers
    if not hasattr(transformers.models.bert.modeling_bert, 'BertSdpaSelfAttention'):
        transformers.models.bert.modeling_bert.BertSdpaSelfAttention = transformers.models.bert.modeling_bert.BertSelfAttention
except ImportError:
    pass

try:
    from ats_skills_dataset import get_all_unique_skills
    SKILL_DICTIONARY = get_all_unique_skills()
except ImportError:
    SKILL_DICTIONARY = ["python", "java", "react", "sql", "communication"]

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'resume_classifier.pkl')

try:
    import train_model
    if "__main__" in sys.modules:
        setattr(sys.modules["__main__"], 'BERTVectorizer', train_model.BERTVectorizer)
except ImportError:
    pass

classifier_model = None

def load_classifier():
    """Loads the trained model and patches it to use Hugging Face API."""
    global classifier_model
    
    if classifier_model is None:
        if not os.path.exists(MODEL_PATH):
            return None
        try:
            gc.collect()
            print("⏳ Opening resume_classifier.pkl into memory...")
            with open(MODEL_PATH, "rb") as f:
                classifier_model = pickle.load(f)
            
            # --- HUGGING FACE API MONKEY PATCH ---
            if hasattr(classifier_model, 'named_steps') and 'bert' in classifier_model.named_steps:
                bert_step = classifier_model.named_steps['bert']
                if HF_TOKEN:
                    print("🚀 HF_TOKEN detected! Offloading AI to the cloud...")
                    original_transform = bert_step.transform
                    
                    def hf_transform(self, X):
                        texts = X.tolist() if hasattr(X, 'tolist') else list(X)
                        emb = get_hf_embeddings(texts)
                        if emb is not None: return emb
                        print("⚠️ HF API failed, falling back to local processing...")
                        return original_transform(X)
                        
                    import types
                    bert_step.transform = types.MethodType(hf_transform, bert_step)
                    
                    # 🔥 DELETE LOCAL MODEL FROM RAM!
                    if hasattr(bert_step, 'model'):
                        del bert_step.model
                        bert_step.model = None
                        gc.collect()
            gc.collect() 
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return None
            
    return classifier_model

def extract_text(path: str) -> str:
    ext = Path(path).suffix.lower()
    text = ""
    try:
        if ext == ".pdf":
            text = extract_pdf_text(path)
        elif ext == ".docx":
            text = docx2txt.process(path)
        elif ext == ".txt":
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    except Exception as e:
        return ""

def preprocess_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9\+\#\.\s]', '', text) 
    return text

def extract_skills(text: str) -> list:
    clean_text = preprocess_text(text)
    found_skills = set()
    padded_text = f" {clean_text} "
    for skill in SKILL_DICTIONARY:
        escaped_skill = re.escape(skill.lower())
        pattern = r'(?:^|[\s\(\[\{,])' + escaped_skill + r'(?:$|[\s\)\]\},])'
        if re.search(pattern, padded_text):
            found_skills.add(skill)
    return list(found_skills)

def extract_years_of_experience(text: str) -> float:
    pattern = r'(\d+)\+?\s*(?:years?|yrs?)'
    matches = re.findall(pattern, text.lower())
    years = 0.0
    if matches:
        years = max([float(m) for m in matches])
    date_pattern = r'\b(19|20)\d{2}\b'
    all_years = [int(y) for y in re.findall(date_pattern, text)]
    if len(all_years) >= 2:
        min_year = min(all_years)
        max_year = max(all_years)
        current_year = datetime.datetime.now().year
        if max_year > current_year: max_year = current_year
        calculated_years = max_year - min_year
        if calculated_years > years: years = calculated_years
    return round(float(years), 1) if years <= 50 else 0.0

def predict_role(resume_text: str, top_k: int = 3) -> list:
    model = load_classifier()
    if not model: return ["Model Not Loaded"]
    safe_text = resume_text[:2000]

    try:
        bert = model.named_steps["bert"]
        clf = model.named_steps["clf"]

        if hasattr(clf, "predict_proba"):
            probs = model.predict_proba([safe_text])[0]
            top_k_indices = np.argsort(probs)[::-1][:top_k]
            return model.classes_[top_k_indices].tolist()
        elif hasattr(clf, "centroids_"):
            embedding = bert.transform([safe_text])
            distances = euclidean_distances(embedding, clf.centroids_)[0]
            sorted_idx = distances.argsort() 
            return clf.classes_[sorted_idx][:top_k].tolist()
        else:
            return [model.predict([safe_text])[0]]
    except Exception as e:
        return ["Prediction Error"]

def compute_match_score(resume_text: str, job_description: str) -> dict:
    r_text = preprocess_text(resume_text)[:2000] 
    jd_text = preprocess_text(job_description)[:2000]
    
    found_skills = extract_skills(r_text)
    predicted_roles = predict_role(r_text, top_k=3)
    primary_role = predicted_roles[0] if predicted_roles else "Unknown"
    
    semantic_score = 0.0
    keyword_score = 0.0
    semantic_success = False
    
    if HF_TOKEN:
        try:
            embeddings = get_hf_embeddings([r_text, jd_text])
            if embeddings is not None and len(embeddings) == 2:
                sim = cosine_similarity([embeddings[0]], [embeddings[1]])
                semantic_score = max(0, min(1, (float(sim[0][0]) + 0.1) * 1.2))
                
                jd_skills = extract_skills(jd_text)
                if len(jd_skills) > 0:
                    intersection = set(found_skills).intersection(set(jd_skills))
                    keyword_score = len(intersection) / len(jd_skills)
                else:
                    jd_words = set(jd_text.split())
                    keyword_score = sum(1 for word in jd_words if word in r_text) / len(jd_words) if jd_words else 0.0
                semantic_success = True
        except Exception as e:
            print(f"⚠️ HF API Match Error: {e}. Falling back to TF-IDF.")
            
    if not semantic_success:
        try:
            vect = TfidfVectorizer(stop_words="english")
            vectors = vect.fit_transform([r_text, jd_text])
            semantic_score = float(cosine_similarity(vectors[0], vectors[1])[0][0])
            jd_skills = extract_skills(jd_text)
            if len(jd_skills) > 0:
                keyword_score = len(set(found_skills).intersection(set(jd_skills))) / len(jd_skills)
            else:
                keyword_score = semantic_score
        except ValueError:
            pass

    role_bonus = 0.0
    common_words = set(primary_role.lower().split()).intersection(set(jd_text.split()))
    if len(common_words) > 0:
        role_bonus = 0.35 if len(common_words) >= 2 or primary_role.lower() in jd_text else 0.20

    experience_years = extract_years_of_experience(r_text)
    
    final_score = min(1.0, (semantic_score * 0.5) + (keyword_score * 0.3) + role_bonus)
    gc.collect()

    return {
        "final_score": round(final_score, 2),
        "skill_match": round(semantic_score, 2),
        "experience_score": round(keyword_score, 2),
        "experience_years": "Fresher" if experience_years == 0 else f"{experience_years} Years",
        "found_skills": list(found_skills),
        "predicted_role": primary_role,
        "top_predicted_roles": predicted_roles
    }