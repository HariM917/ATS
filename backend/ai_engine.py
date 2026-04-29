import os
import torch
# Optimization for production/restricted memory environments
torch.set_num_threads(1)
from dotenv import load_dotenv
import logging

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)

# Load environment variables from .env file
load_dotenv()
import re
import docx2txt
import pickle
import gc
import time
import requests
from pdfminer.high_level import extract_text as extract_pdf_text
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances
from sklearn.base import BaseEstimator, TransformerMixin
from pathlib import Path
import datetime
import numpy as np
import sys

# --- HUGGING FACE INFERENCE API SETUP ---
HF_TOKEN = os.environ.get("HF_TOKEN")
HF_API_URL = "https://api-inference.huggingface.co/models/sentence-transformers/all-mpnet-base-v2"

# Global caches for models to prevent repeated loading/intermittent failures
LOCAL_MODEL_CACHE = None
LOCAL_CLASSIFIER_CACHE = None
EMBEDDING_CACHE = {} # Production Cache to prevent redundant computation
VERSION = "Elite-v1.9.4-STABLE"

# --- LOCAL EMBEDDING MODEL SETUP ---
from sentence_transformers import SentenceTransformer

def get_embeddings_safe(texts):
    """Elite Local Embedding Generator with Production Caching."""
    global LOCAL_MODEL_CACHE, EMBEDDING_CACHE
    try:
        if LOCAL_MODEL_CACHE is None:
            logging.info(">>> INFRA: Loading Light Model (all-MiniLM-L6-v2) for production stability...")
            LOCAL_MODEL_CACHE = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Performance Cache Logic
        results = []
        texts_to_encode = []
        text_indices = []

        for i, text in enumerate(texts):
            if text in EMBEDDING_CACHE:
                results.append(EMBEDDING_CACHE[text])
            else:
                results.append(None) # Placeholder
                texts_to_encode.append(text)
                text_indices.append(i)

        if texts_to_encode:
            print(f"🧠 [AI] Encoding {len(texts_to_encode)} chunks...")
            new_embs = LOCAL_MODEL_CACHE.encode(texts_to_encode, convert_to_numpy=True, show_progress_bar=False)
            print("🧠 [AI] Encoding complete.")
            for i, emb in enumerate(new_embs):
                orig_idx = text_indices[i]
                results[orig_idx] = emb
                EMBEDDING_CACHE[texts_to_encode[i]] = emb # Save to cache
        
        return np.array(results)
    except Exception as e:
        logging.error(f">>> INFRA ERROR: Local embedding failed: {e}")
        # Dynamic fallback: Use 768 if possible, or 384
        dim = 768 # Default for mpnet
        return np.zeros((len(texts), dim))

def warm_up():
    """Preloads models to ensure first request is instant."""
    logging.info(">>> INFRA: Performing Warm-Start Preload...")
    get_embeddings_safe(["warmup"])
    load_classifier()
    logging.info(">>> INFRA: Warm-Start Complete. System is now Live.")

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
    if not SKILL_DICTIONARY:
        raise ValueError("Skill dictionary is empty")
    logging.info(f">>> INFRA: Loaded {len(SKILL_DICTIONARY)} skills from dataset.")
except Exception as e:
    logging.warning(f">>> INFRA WARNING: Could not load full skill dataset ({e}). Using basic fallback.")
    SKILL_DICTIONARY = ["python", "java", "react", "sql", "communication", "machine learning", "deep learning", "nlp", "aws", "docker"]

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# --- AGGRESSIVE MOCKING ---
class BERTVectorizer(BaseEstimator, TransformerMixin):
    def __init__(self, model_name='all-mpnet-base-v2'):
        self.model_name = model_name
        self.model = None
    def fit(self, X, y=None): return self
    def transform(self, X): 
        # Dynamic dimension return for mock
        return np.zeros((len(X), 768)) 

if "__main__" in sys.modules:
    setattr(sys.modules["__main__"], 'BERTVectorizer', BERTVectorizer)

class CustomUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if name == 'BERTVectorizer': return BERTVectorizer
        if name in ['NearestCentroid', 'HistGradientBoostingClassifier', 'RandomForestClassifier']:
            module_map = {
                'NearestCentroid': 'sklearn.neighbors',
                'HistGradientBoostingClassifier': 'sklearn.ensemble',
                'RandomForestClassifier': 'sklearn.ensemble'
            }
            return getattr(__import__(module_map[name], fromlist=[name]), name)
        return super().find_class(module, name)

def load_classifier():
    """Elite Robust Loader: Loads the hybrid model once and caches it."""
    global LOCAL_CLASSIFIER_CACHE
    if LOCAL_CLASSIFIER_CACHE is not None:
        return LOCAL_CLASSIFIER_CACHE
        
    # Check for both possible names (legacy support)
    possible_paths = [
        os.path.join(BASE_DIR, "hybrid_role_model.pkl"),
        os.path.join(BASE_DIR, "resume_classifier.pkl")
    ]
    
    # Force search in parent if not found in backend/
    model_path = None
    for p in possible_paths:
        if os.path.exists(p):
            model_path = p
            break
            
    if not model_path:
        logging.error(f"INFRA ERROR: No model file found in {BASE_DIR}")
        return None
        
    try:
        gc.collect()
        with open(model_path, 'rb') as f:
            # We use the CustomUnpickler to handle mocking
            model = CustomUnpickler(f).load()
            LOCAL_CLASSIFIER_CACHE = model
            logging.info(f">>> INFRA: Classifier loaded successfully from {os.path.basename(model_path)} [{VERSION}]")
            return model
    except Exception as e:
        logging.error(f">>> INFRA ERROR: Failed to load classifier: {e}")
        return None

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

def extract_sections(text: str) -> dict:
    """Splits resume into key sections using common headers."""
    sections = {"skills": "", "experience": "", "projects": "", "other": text}
    
    # Common headers and their variations
    patterns = {
        "skills": r'(?i)\b(?:skills|technical skills|competencies|expertise|tools)\b',
        "experience": r'(?i)\b(?:experience|work history|employment|professional experience)\b',
        "projects": r'(?i)\b(?:projects|academic projects|personal projects)\b'
    }
    
    # Find all header positions
    found = []
    for key, pattern in patterns.items():
        for m in re.finditer(pattern, text):
            found.append((m.start(), key))
    
    # Sort and slice
    found.sort()
    if not found:
        return sections
        
    for i in range(len(found)):
        start_idx, key = found[i]
        end_idx = found[i+1][0] if i+1 < len(found) else len(text)
        sections[key] = text[start_idx:end_idx].strip()
        
    return sections

def preprocess_text(text: str) -> str:
    # Basic cleaning
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s\-\.\+]', '', text) # Keep +, . (for C++, .NET)
    return text.strip()

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
    """Production Robust Experience Detection: Balanced between strictness and inclusivity."""
    text_lower = text.lower()

    # BALANCED FILTER: Include professional, internship, and technical role indicators
    valid_work_indicators = [
        "work experience", "professional experience", "employment", "company", 
        "intern", "internship", "freelance", "developer", "engineer", "analyst"
    ]
    if not any(k in text_lower for k in valid_work_indicators):
        return 0.0

    # STRICT regex for years: Must include 'experience' or 'exp' nearby
    matches = re.findall(r'(\d+)\+?\s*(?:years?|yrs?|yr?).{0,20}(?:experience|exp)', text_lower)

    years = 0
    for match in matches:
        try:
            years = max(years, int(match))
        except: pass

    return float(years)

def extract_years_from_jd(text: str) -> float:
    """Extracts required years of experience from a Job Description."""
    patterns = [
        r'(\d+)\+?\s*(?:years?|yrs?|yr?)\s*(?:of\s*)?experience',
        r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:required|needed|preferred)',
        r'minimum\s*(\d+)\s*years?'
    ]
    clean_text = text.lower()
    for pattern in patterns:
        matches = re.findall(pattern, clean_text)
        if matches:
            try:
                return float(max([int(m) for m in matches]))
            except: continue
    return 0.0

def predict_role(resume_texts, top_k: int = 3) -> list:
    """Predicts roles using the Hybrid Boosting model with full local fallback."""
    safe_texts = [text[:8000] for text in resume_texts]
    results = []
    try:
        model_data = load_classifier()
        if not model_data: 
            logging.error(">>> DEBUG: Model data missing in load_classifier()")
            return [["Model Unavailable"]] * len(resume_texts)
        
        # --- ELITE DEBUGGING ---
        logging.info(f">>> DEBUG: MODEL TYPE: {type(model_data)}")
        boosting = None
        classes = []

        if isinstance(model_data, dict):
            logging.info(f">>> DEBUG: DICT KEYS: {list(model_data.keys())}")
            # Try specific keys or fallback to first boosting-like object
            boosting = model_data.get("boosting") or model_data.get("model")
            classes = model_data.get("classes", [])
        else:
            # It's a Pipeline
            steps = model_data.named_steps
            # Robust: Try 'clf', 'model', or simply the last step
            boosting = steps.get("clf") or steps.get("model") or list(steps.values())[-1]
            classes = getattr(boosting, "classes_", [])
            
        logging.info(f">>> DEBUG: Using classifier: {type(boosting)}")
        
        # USE THE SAFE EMBEDDING PATH
        embeddings = get_embeddings_safe(safe_texts)
        if embeddings is None: 
            logging.error(">>> DEBUG: Embeddings failed (Both HF and Local)")
            return [["Prediction Unavailable"]] * len(resume_texts)
        
        if not boosting: 
            logging.error(">>> DEBUG: Classifier could not be extracted from model object")
            return [["Prediction Unavailable"]] * len(resume_texts)
        
        # Predict Probs
        probs_list = boosting.predict_proba(embeddings)
        
        # Dynamic Dimension Safety Check
        embedding_dim = embeddings.shape[1]
        logging.info(f">>> INFRA: Inference using {embedding_dim} dimensions.")

        for probs in probs_list:
            top_idx = np.argsort(probs)[::-1][:top_k]
            results.append(classes[top_idx].tolist())
            
        logging.info(f">>> INFRA: Predicted {len(results)} roles successfully.")
        return results
    except Exception as e:
        logging.error(f">>> DEBUG: Predict Role Critical Failure: {e}")
        return [["Prediction Unavailable"]] * len(resume_texts)

def get_dynamic_weights(role: str, years: float) -> dict:
    """Elite Feature: Adjusts weights based on role type and seniority."""
    # Default: 40% Semantic, 30% Skills, 20% Role, 10% Experience
    weights = {"semantic": 0.4, "skills": 0.3, "role": 0.2, "exp": 0.1}
    
    role = str(role).lower()
    # Management/HR roles value experience more
    if any(m in role for m in ["manager", "hr", "lead", "director"]):
        weights = {"semantic": 0.3, "skills": 0.2, "role": 0.2, "exp": 0.3}
    # Technical roles value specific skills more
    elif any(t in role for t in ["engineer", "developer", "architect", "analyst"]):
        weights = {"semantic": 0.3, "skills": 0.5, "role": 0.1, "exp": 0.1}
        
    # Seniority adjustment
    if years > 5:
        weights["exp"] += 0.1
        weights["semantic"] -= 0.1
        
    return weights

def batch_compute_match_score(resume_texts: list, job_description: str) -> list:
    """
    Elite Hybrid Scoring:
    1. Section-based Analysis
    2. Semantic Skill Matching (handling synonyms)
    3. Dynamic Weighting
    """
    jd_sections = extract_sections(job_description)
    jd_skills_text = jd_sections["skills"] if jd_sections["skills"] else job_description
    jd_skills_list = extract_skills(jd_skills_text)
    
    jd_text_clean = preprocess_text(job_description)[:8000]
    resume_texts_clean = [preprocess_text(t)[:8000] for t in resume_texts]
    
    all_texts = [jd_text_clean] + resume_texts_clean
    
    # USE THE SAFE UNIFIED EMBEDDING PATH
    print("🧠 [AI] Generating embeddings...")
    start_emb = time.time()
    embeddings = get_embeddings_safe(all_texts)
    print(f"⏱️ Embedding generation took {time.time() - start_emb:.2f}s")

    final_results = []
    try:
        model_data = load_classifier()
        if not model_data: 
            return [{"match_percentage": 0, "top_roles": ["Error"], "experience": "0", "skills": []}] * len(resume_texts)
        
        # Robust check: Is it a Hybrid Dictionary or a legacy Pipeline?
        if isinstance(model_data, dict):
            boosting = model_data.get("boosting")
            classes = model_data.get("classes", [])
        else:
            # It's a Pipeline
            boosting = model_data.named_steps.get("clf")
            classes = getattr(boosting, "classes_", [])

        jd_emb = embeddings[0] if embeddings is not None else None
        
        for i, text in enumerate(resume_texts):
            print(f"🔍 [AI] Processing Resume {i+1}...")
            
            # --- Text Extraction ---
            print("🔍 [AI] Extracting sections...")
            r_sections = extract_sections(text)
            
            print("🔍 [AI] Extracting skills...")
            r_skills_list = extract_skills(text)
            all_possible_skills = r_skills_list 
            
            print("🔍 [AI] Extracting experience...")
            years = extract_years_of_experience(text)
            
            # --- Semantic Similarity ---
            print("🔍 [AI] Calculating semantic similarity...")
            semantic_score = 0.5 # Baseline
            if jd_emb is not None and embeddings is not None:
                sim = cosine_similarity([jd_emb], [embeddings[i+1]])[0][0]
                semantic_score = max(0, min(1, (float(sim) + 0.1) * 1.2))
            
            # --- Role Validation (Boosting) ---
            validation_score = 0.5
            predicted_role = "General Professional"
            top_ranked_roles = []

            if boosting and embeddings is not None:
                try:
                    print(f"🧠 [AI] Running hybrid scoring for resume {i+1}...")
                    # Get probabilities for all classes
                    probs = boosting.predict_proba([embeddings[i+1]])[0]
                    top_indices = np.argsort(probs)[::-1][:3] # Top 3
                    
                    classes = boosting.classes_
                    for idx in top_indices:
                        role_name = classes[idx]
                        classifier_conf = float(probs[idx])
                        
                        # Hybrid Semantic Blend (30% weight to text similarity)
                        role_emb = get_embeddings_safe([role_name])
                        res_emb = embeddings[i+1].reshape(1,-1)
                        semantic_sim = float(cosine_similarity(role_emb, res_emb)[0][0])
                        
                        hybrid_conf = (classifier_conf * 0.7) + (semantic_sim * 0.3)
                        
                        if hybrid_conf > 0.2: # Filter noise
                            top_ranked_roles.append({
                                "role": role_name,
                                "confidence": round(hybrid_conf, 3)
                            })
                    
                    if top_ranked_roles:
                        predicted_role = top_ranked_roles[0]["role"]
                        validation_score = top_ranked_roles[0]["confidence"]
                    print(f"✅ [AI] Scoring complete. Predicted: {predicted_role}")
                except Exception as e:
                    logging.error(f">>> INFRA ERROR: Role ranking failed: {e}")
            # --- PART 1: Bulletproof Raw Skill Extraction (Zero Filtering) ---
            logging.info(f">>> DEBUG: Processing Resume {i+1} for Skills...")
            
            # SKILL_DICTIONARY is already a flat list from get_all_unique_skills()
            ALL_SKILLS_FLAT = [s.lower().strip() for s in SKILL_DICTIONARY]

            def extract_skills_raw(raw_text, skill_list):
                text_lower = raw_text.lower().strip()
                found = []
                for skill in skill_list:
                    if len(skill) > 2 and skill in text_lower: # Min length 2 to avoid single-char noise
                        found.append(skill.title()) # Return in Title Case for UI
                return sorted(list(set(found)))

            start_skills = time.time()
            all_possible_skills = extract_skills_raw(text, ALL_SKILLS_FLAT)
            print(f"⏱️ Skill extraction took {time.time() - start_skills:.2f}s")
            
            # Fallback to existing logic if empty or too small
            if len(all_possible_skills) < 3:
                all_possible_skills = extract_skills(text)
            
            found_skills_final = all_possible_skills
            
            # Simplified Scoring (Direct Signal Match with JD)
            jd_skills_norm = [s.lower().strip() for s in jd_skills_list]
            matched_with_jd = [s for s in found_skills_final if s.lower().strip() in jd_skills_norm]
            
            skill_score = len(matched_with_jd) / len(jd_skills_list) if jd_skills_list else 1.0
            logging.info(f">>> DEBUG: Detected {len(found_skills_final)} Total Skills.")

            # --- Production Semantic Role Mapping (Ranked) ---
            SPECIFIC_ROLES = [
                "Machine Learning Engineer", "Data Scientist", "Full Stack Developer", 
                "Frontend Engineer", "Backend Engineer", "DevOps Engineer", 
                "Cloud Architect", "UI/UX Designer", "Product Manager", "HR Manager",
                "QA Engineer", "Mobile Developer", "Cybersecurity Analyst", "Data Engineer"
            ]
            
            top_ranked_roles = []
            best_role = predicted_role
            try:
                role_embs = get_embeddings_safe(SPECIFIC_ROLES)
                res_emb = embeddings[i+1].reshape(1, -1)
                sims = cosine_similarity(res_emb, role_embs)[0]
                
                # Get Top 3 Roles
                top_indices = np.argsort(sims)[::-1][:3]
                for idx in top_indices:
                    top_ranked_roles.append({
                        "role": SPECIFIC_ROLES[idx],
                        "confidence": float(sims[idx])
                    })
                
                # Production Semantic Blending
                top_conf = top_ranked_roles[0]["confidence"]
                top_name = top_ranked_roles[0]["role"]
                
                if top_conf > 0.80:
                    best_role = top_name
                elif top_conf > 0.60: # Lowered for more inclusivity
                    best_role = f"{predicted_role} ({top_name})"
                
                # STRATEGIC HARD OVERRIDES
                jd_low = job_description.lower()
                res_low = text.lower()
                if "machine learning" in jd_low and ("ml" in res_low or "machine learning" in res_low):
                    best_role = "Machine Learning Engineer"
                elif "data science" in jd_low and ("data science" in res_low or "data scientist" in res_low):
                    best_role = "Data Scientist"
                elif "frontend" in jd_low and ("react" in res_low or "frontend" in res_low):
                    best_role = "Frontend Engineer"
            except:
                top_ranked_roles = [{"role": predicted_role, "confidence": 0.7}]

            # --- Elite Constraint Tuning ---
            weights = get_dynamic_weights(best_role, years)
            required_years = extract_years_from_jd(job_description)
            
            gap_penalty = 1.0
            if years < required_years:
                gap = required_years - years
                gap_penalty = max(0.5, 1.0 - (gap * 0.1))

            seniority_penalty = 1.0
            if years == 0 and any(kw in job_description.lower() for kw in ["senior", "lead", "staff", "head", "principal"]):
                seniority_penalty = 0.60
            
            adj_semantic_score = semantic_score
            if years == 0:
                adj_semantic_score = min(semantic_score, 0.75)

            match_percentage = int((
                (adj_semantic_score * weights["semantic"]) + 
                (skill_score * weights["skills"]) + 
                (validation_score * weights["role"]) + 
                (min(1.0, float(years)/10) * weights["exp"])
            ) * 100 * gap_penalty * seniority_penalty)
            
            # NaN and Range Protection
            if np.isnan(match_percentage): match_percentage = 10
            match_percentage = min(99, max(10, match_percentage))

            # --- Production Reasoning Layer ---
            reasoning = []
            if matched_with_jd: reasoning.append(f"Strong alignment in {', '.join(matched_with_jd[:3])}.")
            
            missing_skills = list(set(jd_skills_norm) - set(matched_with_jd))
            if missing_skills: reasoning.append(f"Missing core skills: {', '.join(missing_skills[:3])}.")
            
            exp_gap = required_years - years
            if exp_gap > 0: reasoning.append(f"Candidate is {int(exp_gap)} years short of requirement.")
            elif years >= required_years and required_years > 0: reasoning.append("Perfect experience alignment.")

            final_results.append({
                "match_percentage": match_percentage,
                "final_score": float(match_percentage) / 100.0,
                "top_roles": [r["role"] for r in top_ranked_roles],
                "role_rankings": top_ranked_roles,
                "predicted_role": predicted_role,
                "experience": f"{int(years)} Years" if years > 0 else "Fresher",
                "jd_required_years": int(required_years),
                "all_skills": found_skills_final,
                "total_skills": len(found_skills_final),
                "missing_skills": missing_skills[:5],
                "summary_reasoning": " ".join(reasoning),
                "BACKEND_VERSION": VERSION
            })
            
    except Exception as e:
        logging.error(f"Elite Scoring Critical Failure: {e}")
        return [{"match_percentage": 10, "top_roles": ["Model Error"], "experience": "0", "skills": []}] * len(resume_texts)

    # --- Batch Ranking Context ---
    if len(final_results) > 1:
        # Sort by match percentage to find rank
        ranked = sorted(final_results, key=lambda x: x["match_percentage"], reverse=True)
        top_score = ranked[0]["match_percentage"]
        for i, res in enumerate(final_results):
            # Find its rank in the sorted list
            rank = next(idx for idx, item in enumerate(ranked) if item == res) + 1
            res["batch_rank"] = f"{rank}/{len(final_results)}"
            res["relative_strength"] = "Top Candidate" if res["match_percentage"] == top_score else "Competitive"

    return final_results

def compute_match_score(resume_text: str, job_description: str) -> dict:
    """Wrapper for backward compatibility or single resume matching."""
    results = batch_compute_match_score([resume_text], job_description)
    return results[0] if results else {}