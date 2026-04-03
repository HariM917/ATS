import os
import re
import docx2txt
import pandas as pd
import pickle
from pdfminer.high_level import extract_text as extract_pdf_text
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances
from pathlib import Path
import datetime
import numpy as np
import sys

# --- Import Skills Dataset ---
try:
    from ats_skills_dataset import get_all_unique_skills
    SKILL_DICTIONARY = get_all_unique_skills()
    print(f"✅ Loaded {len(SKILL_DICTIONARY)} skills from dataset.")
except ImportError:
    print("⚠️ ats_skills_dataset.py not found. Using fallback skills.")
    SKILL_DICTIONARY = ["python", "java", "react", "sql", "communication"]

# --- Import Semantic Matching (Optional) ---
try:
    from sentence_transformers import SentenceTransformer, util
    semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
    USE_SEMANTIC = True
    print("✅ Semantic model loaded successfully.")
except ImportError:
    USE_SEMANTIC = False
    print("⚠️ sentence-transformers not found. Falling back to TF-IDF.")

# --- Configuration ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'resume_classifier.pkl')
SKILL_WEIGHT = 0.4
SEMANTIC_WEIGHT = 0.6 
EXPERIENCE_WEIGHT = 0.0

# --- Import Training Module for Pickle Compatibility ---
try:
    import train_model
    # --- PICKLE FIX ---
    # When running app.py, it acts as the '__main__' module. The pickle file expects 
    # 'BERTVectorizer' to be defined in '__main__'. We inject it here to satisfy pickle.load().
    if "__main__" in sys.modules:
        setattr(sys.modules["__main__"], 'BERTVectorizer', train_model.BERTVectorizer)
except ImportError:
    print("⚠️ train_model.py not found. Model prediction might fail if custom classes are missing.")

# --- Model Loading Logic ---
classifier_model = None

def load_classifier():
    """Loads the trained model from disk if not already loaded."""
    global classifier_model
    if classifier_model is None:
        if not os.path.exists(MODEL_PATH):
            print("⚠️ resume_classifier.pkl not found. Run training first.")
            return None
        try:
            with open(MODEL_PATH, "rb") as f:
                classifier_model = pickle.load(f)
            print("✅ Resume Classifier Model loaded.")
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return None
    return classifier_model

# Attempt to load on startup
load_classifier()

def extract_text(path: str) -> str:
    """Detects file type and extracts text from single files."""
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
        print(f"Error extracting text from {path}: {e}")
        return ""

def preprocess_text(text: str) -> str:
    """Cleans text for analysis."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\+\#\.\s]', '', text) 
    return text

def extract_skills(text: str) -> list:
    """Matches text against the loaded SKILL_DICTIONARY."""
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
    """Heuristic to extract years of experience."""
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
        if calculated_years > years:
            years = calculated_years

    return round(float(years), 1) if years <= 50 else 0.0

def predict_role(resume_text: str, top_k: int = 3) -> list:
    """
    Predicts top K job roles. Supports both Centroid-based and Probability-based classifiers.
    """
    model = load_classifier()
    if not model:
        return ["Model Not Loaded"]

    try:
        # Extract steps from the pipeline
        bert = model.named_steps["bert"]
        clf = model.named_steps["clf"]

        # 1. Check if classifier supports predict_proba (Logistic, Voting, KNN, GB)
        if hasattr(clf, "predict_proba"):
            # Get probabilities for the single input text [0]
            probs = model.predict_proba([resume_text])[0]
            classes = model.classes_
            
            # Get indices of top k probabilities (descending order)
            # argsort sorts ascending, so we take slice from end
            top_k_indices = np.argsort(probs)[::-1][:top_k]
            roles = classes[top_k_indices]
            return roles.tolist()
            
        # 2. Check if classifier is Centroid-based (NearestCentroid) - Legacy support
        elif hasattr(clf, "centroids_"):
            embedding = bert.transform([resume_text])
            distances = euclidean_distances(embedding, clf.centroids_)[0]
            sorted_idx = distances.argsort() # Ascending distance = closest
            roles = clf.classes_[sorted_idx][:top_k]
            return roles.tolist()
            
        # 3. Fallback for single prediction models
        else:
            return [model.predict([resume_text])[0]]

    except Exception as e:
        print(f"Detailed Prediction Error: {e}")
        # Fallback to prevent crash
        return ["Prediction Error"]

def predict_job_role(text: str) -> str:
    """Legacy wrapper for single role prediction."""
    roles = predict_role(text, top_k=1)
    return roles[0] if roles else "Prediction Failed"

def compute_match_score(resume_text: str, job_description: str) -> dict:
    r_text = preprocess_text(resume_text)
    jd_text = preprocess_text(job_description)
    found_skills = extract_skills(r_text)
    
    # 1. AI Prediction (Role Classification)
    predicted_roles = predict_role(r_text, top_k=3)
    primary_role = predicted_roles[0] if predicted_roles else "Unknown"
    
    # 2. Similarity Score Calculation
    semantic_score = 0.0
    keyword_score = 0.0
    
    if USE_SEMANTIC:
        emb1 = semantic_model.encode(r_text, convert_to_tensor=True)
        emb2 = semantic_model.encode(jd_text, convert_to_tensor=True)
        cosine_scores = util.cos_sim(emb1, emb2)
        raw_similarity = float(cosine_scores[0][0])
        
        # Normalize semantic score
        semantic_score = max(0, min(1, (raw_similarity + 0.1) * 1.2))
        
        # Keyword Matching
        jd_skills = extract_skills(jd_text)
        if len(jd_skills) > 0:
            intersection = set(found_skills).intersection(set(jd_skills))
            keyword_score = len(intersection) / len(jd_skills)
        else:
            jd_words = set(jd_text.split())
            if len(jd_words) > 0:
                matches = sum(1 for word in jd_words if word in r_text)
                keyword_score = matches / len(jd_words)
            else:
                keyword_score = 0.0
    else:
        try:
            vect = TfidfVectorizer(stop_words="english")
            vectors = vect.fit_transform([r_text, jd_text])
            sim = cosine_similarity(vectors[0], vectors[1])
            semantic_score = float(sim[0][0])
        except ValueError:
            semantic_score = 0.0

    # 3. Role Alignment Bonus
    role_bonus = 0.0
    predicted_words = set(primary_role.lower().split())
    jd_words = set(jd_text.split())
    common_words = predicted_words.intersection(jd_words)
    
    if len(common_words) > 0:
        role_bonus = 0.20
        if len(common_words) >= 2 or primary_role.lower() in jd_text:
             role_bonus = 0.35

    # 4. Experience Calculation
    experience_years = extract_years_of_experience(r_text)
    
    # Display Logic: Show "Fresher" if 0 years detected
    display_experience = "Fresher" if experience_years == 0 else f"{experience_years} Years"

    # 5. Final Weighted Score
    final_score = (semantic_score * 0.5) + (keyword_score * 0.3) + role_bonus
    final_score = min(1.0, final_score)

    return {
        "final_score": round(final_score, 2),
        "skill_match": round(semantic_score, 2),
        "experience_score": round(keyword_score, 2),
        "experience_years": display_experience,
        "found_skills": found_skills,
        "predicted_role": primary_role,
        "top_predicted_roles": predicted_roles
    }