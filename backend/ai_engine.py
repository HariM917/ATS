import os
import re
import docx2txt
import numpy as np
import datetime
import requests
from pathlib import Path
from pdfminer.high_level import extract_text as extract_pdf_text

# ================= CONFIG ================= #

HF_TOKEN = os.getenv("HF_TOKEN")

if not HF_TOKEN:
    raise Exception("HF_TOKEN not set in environment variables")

API_URL = "https://api-inference.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2"

HEADERS = {
    "Authorization": f"Bearer {HF_TOKEN}"
}

# Skill dictionary (expand anytime)
SKILL_DICTIONARY = [
    "python", "java", "c++", "react", "node", "sql",
    "machine learning", "deep learning", "nlp",
    "communication", "teamwork", "leadership"
]

# ================= TEXT EXTRACTION ================= #

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
        return re.sub(r'\s+', ' ', text).strip()
    except Exception as e:
        print("Text extraction error:", e)
        return ""

# ================= PREPROCESS ================= #

def preprocess_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9\+\#\.\s]', '', text)
    return text

# ================= SKILL MATCH ================= #

def extract_skills(text: str) -> list:
    clean_text = preprocess_text(text)
    found = []
    for skill in SKILL_DICTIONARY:
        if skill in clean_text:
            found.append(skill)
    return found

# ================= EXPERIENCE ================= #

def extract_years_of_experience(text: str) -> float:
    pattern = r'(\d+)\+?\s*(years?|yrs?)'
    matches = re.findall(pattern, text.lower())
    
    if matches:
        return float(matches[0][0])
    
    # fallback using year range
    date_pattern = r'\b(19|20)\d{2}\b'
    years = [int(y) for y in re.findall(date_pattern, text)]
    
    if len(years) >= 2:
        return float(max(years) - min(years))
    
    return 0.0

# ================= HUGGING FACE EMBEDDING ================= #

def get_embedding(text):
    response = requests.post(
        API_URL,
        headers=HEADERS,
        json={"inputs": text}
    )

    if response.status_code != 200:
        raise Exception(f"HF API Error: {response.text}")

    return response.json()

# ================= COSINE SIMILARITY ================= #

def cosine_similarity(vec1, vec2):
    v1 = np.array(vec1)
    v2 = np.array(vec2)

    if np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
        return 0.0

    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))

# ================= MAIN MATCH FUNCTION ================= #

def compute_match_score(resume_text: str, job_description: str) -> dict:

    # Limit size (prevents timeout)
    r_text = preprocess_text(resume_text)[:1000]
    jd_text = preprocess_text(job_description)[:1000]

    # Extract skills
    found_skills = extract_skills(r_text)

    # Semantic similarity (HF API)
    try:
        emb1 = get_embedding(r_text)
        emb2 = get_embedding(jd_text)
        semantic_score = cosine_similarity(emb1, emb2)
    except Exception as e:
        print("HF API failed:", e)
        semantic_score = 0.0

    # Keyword score fallback
    jd_words = set(jd_text.split())
    match_count = sum(1 for w in jd_words if w in r_text)
    keyword_score = match_count / len(jd_words) if jd_words else 0

    # Experience
    exp_years = extract_years_of_experience(r_text)
    exp_display = "Fresher" if exp_years == 0 else f"{exp_years} Years"

    # Final weighted score
    final_score = (semantic_score * 0.7) + (keyword_score * 0.3)
    final_score = min(1.0, final_score)

    return {
        "final_score": round(final_score, 2),
        "semantic_score": round(semantic_score, 2),
        "keyword_score": round(keyword_score, 2),
        "experience": exp_display,
        "skills": found_skills
    }

# ================= OPTIONAL TEST ================= #

if __name__ == "__main__":
    resume = "I have 2 years experience in Python, machine learning and NLP."
    jd = "Looking for Python developer with NLP experience"

    result = compute_match_score(resume, jd)
    print(result)