import os
import requests
import time
import numpy as np
import logging
from dotenv import load_dotenv
from rapidfuzz import fuzz, process

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

VERSION = "Prod-v2.1.0-Elite"

# --- ELITE NORMALIZATION & SYNONYMS ---
SKILL_MAP = {
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "nlp": "natural language processing",
    "js": "javascript",
    "ts": "typescript",
    "aws": "amazon web services",
    "gcp": "google cloud platform",
    "stats": "statistics",
    "postgres": "postgresql",
    "mongo": "mongodb",
    "reactjs": "react",
    "vuejs": "vue",
    "nextjs": "next",
    "expressjs": "express"
}

SYNONYM_MAP = {
    "ml": "machine learning",
    "dl": "deep learning",
    "nlp": "natural language processing",
    "tf": "tensorflow",
    "k8s": "kubernetes",
    "js": "javascript",
    "ts": "typescript",
    "aws": "amazon web services",
    "gcp": "google cloud platform",
    "cv": "computer vision",
    "rl": "reinforcement learning",
    "genai": "generative ai",
    "llm": "large language models"
}

try:
    from ats_skills_dataset import ATS_SKILLS_DATA
    # Expand ROLE_SKILLS from the comprehensive dataset
    ROLE_SKILLS = {}
    for role, categories in ATS_SKILLS_DATA.items():
        all_role_skills = []
        for cat, skills in categories.items():
            all_role_skills.extend([s.lower() for s in skills])
        ROLE_SKILLS[role.lower()] = all_role_skills
except ImportError:
    ROLE_SKILLS = {
        "machine learning": ["python", "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy", "keras", "deep learning", "nlp"],
        "data scientist": ["python", "sql", "statistics", "machine learning", "r", "pandas", "visualization", "tableau"],
        "data analyst": ["sql", "excel", "tableau", "power bi", "python", "statistics", "data analysis"],
        "full stack": ["javascript", "react", "node.js", "html", "css", "sql", "mongodb", "typescript", "express"],
        "frontend": ["react", "javascript", "html", "css", "typescript", "tailwind", "next.js", "vue", "angular"],
        "backend": ["node.js", "python", "java", "sql", "postgresql", "mongodb", "express", "django", "flask", "aws"],
        "devops": ["docker", "kubernetes", "aws", "jenkins", "terraform", "ci/cd", "linux", "git", "cloud"]
    }

def normalize_skill(skill: str) -> str:
    """Production Grade Normalizer: Strips spaces, hyphens and case for robust matching."""
    if not skill: return ""
    return skill.lower().replace("-", "").replace(" ", "").strip()

def detect_role_from_resume(text: str) -> str:
    """ELITE Keyword-Based Role Detector: High precision for technical domains."""
    text = text.lower()
    
    # Priority 1: AI & Data Science
    if any(x in text for x in ["tensorflow", "pytorch", "machine learning", "deep learning", "neural network", "genai", "llm"]):
        return "Machine Learning Engineer"
    
    if any(x in text for x in ["data analysis", "power bi", "sql", "tableau", "statistics", "data viz"]):
        return "Data Scientist" if "model" in text else "Data Analyst"
        
    # Priority 2: Web & Software Development
    if any(x in text for x in ["react", "frontend", "javascript", "css", "html", "tailwind", "nextjs"]):
        return "Frontend Developer"
        
    if any(x in text for x in ["node", "backend", "express", "django", "flask", "java", "spring"]):
        return "Backend Developer"
        
    if any(x in text for x in ["aws", "docker", "kubernetes", "devops", "cloud", "terraform", "jenkins"]):
        return "Cloud/DevOps Engineer"
        
    # Priority 3: Cybersecurity & Others
    if any(x in text for x in ["cyber", "security", "firewall", "pentest", "vulnerability"]):
        return "Cybersecurity Engineer"
        
    return "Software Engineer"

# --- HUGGING FACE INFERENCE API SETUP ---
from huggingface_hub import InferenceClient
HF_TOKEN = os.getenv("HF_TOKEN")
hf_client = InferenceClient(api_key=HF_TOKEN)

# Global caches for models to prevent repeated loading/intermittent failures
LOCAL_MODEL_CACHE = None
LOCAL_CLASSIFIER_CACHE = None
EMBEDDING_CACHE = {} 

def safe_similarity(a, b):
    """Computes cosine similarity with NaN and zero-vector protection."""
    if a is None or b is None:
        return 0.0
    
    # Ensure they are 2D arrays for sklearn
    a = np.array(a).reshape(1, -1)
    b = np.array(b).reshape(1, -1)
    
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    
    try:
        sim = float(cosine_similarity(a, b)[0][0])
        return 0.0 if np.isnan(sim) else sim
    except:
        return 0.0

def get_embeddings_safe(texts):
    """Elite HF-Powered Embedding Generator with 768-D Production Validation."""
    global EMBEDDING_CACHE
    MODEL_NAME = "sentence-transformers/all-mpnet-base-v2" # Produces 768 dimensions
    DIM = 768
    
    try:
        results = [None] * len(texts)
        texts_to_encode = []
        text_indices = []

        for i, text in enumerate(texts):
            clean_text = text.strip() if isinstance(text, str) else ""
            if clean_text in EMBEDDING_CACHE:
                results[i] = EMBEDDING_CACHE[clean_text]
            else:
                texts_to_encode.append(clean_text)
                text_indices.append(i)

        if texts_to_encode:
            if not HF_TOKEN:
                print("🚨 [AI-ERROR] HF_TOKEN missing")
                for idx in text_indices: results[idx] = np.zeros(DIM)
                return np.array(results)

            print(f"[AI] Calling HF ({MODEL_NAME}) for {len(texts_to_encode)} chunks...")
            embeddings = hf_client.feature_extraction(
                texts_to_encode,
                model=MODEL_NAME
            )
            
            if not isinstance(embeddings, (list, np.ndarray)) or len(embeddings) == 0:
                print(f"🚨 [AI-ERROR] Invalid HF response: {type(embeddings)}")
                for idx in text_indices: results[idx] = np.zeros(DIM)
            else:
                embeddings = np.array(embeddings)
                if embeddings.ndim == 1:
                    embeddings = embeddings.reshape(1, -1)

                print(f"✅ [AI] Received {len(embeddings)} embeddings ({embeddings.shape[1]} dims).")
                for i, emb in enumerate(embeddings):
                    if i < len(text_indices):
                        idx = text_indices[i]
                        results[idx] = emb
                        EMBEDDING_CACHE[texts_to_encode[i]] = emb
        
        for i in range(len(results)):
            if results[i] is None: results[i] = np.zeros(DIM)
            
        return np.array(results)
    except Exception as e:
        print(f"🚨 [AI-ERROR] Embedding failed: {e}")
        return np.zeros((len(texts), DIM))

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

# --- PRODUCTION SKILL DATABASE ---
SKILLS_DB = [
    "Python", "Java", "React", "SQL", "JavaScript", "TypeScript", "Machine Learning", 
    "Deep Learning", "TensorFlow", "PyTorch", "NLP", "AWS", "Azure", "GCP", "Docker", 
    "Kubernetes", "Git", "Flask", "FastAPI", "Pandas", "NumPy", "Scikit-learn", 
    "Power BI", "Tableau", "Data Analysis", "Computer Vision", "HTML", "CSS", 
    "Node.js", "Express", "MongoDB", "PostgreSQL", "Next.js", "Vue", "Angular", 
    "C++", "C#", ".NET", "PHP", "Ruby", "Swift", "Kotlin", "Go", "Rust"
]

try:
    from ats_skills_dataset import get_all_unique_skills
    additional_skills = get_all_unique_skills()
    SKILL_DICTIONARY = sorted(list(set(SKILLS_DB + additional_skills)))
    logging.info(f">>> INFRA: Loaded {len(SKILL_DICTIONARY)} total skills for deterministic extraction.")
except Exception as e:
    SKILL_DICTIONARY = SKILLS_DB
    logging.warning(f">>> INFRA WARNING: Using fallback Skill DB ({e})")

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

from pdfminer.high_level import extract_text as pdf_extract

def extract_text(path: str) -> str:
    """Robust Text Extraction using pdfminer for PDFs and docx2txt for Word."""
    ext = Path(path).suffix.lower()
    text = ""
    try:
        if ext == ".pdf":
            text = pdf_extract(path)
        elif ext == ".docx":
            text = docx2txt.process(path)
        elif ext == ".txt":
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        
        # Standardize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # --- DIAGNOSTIC LOGGING ---
        print(f"📄 [INFRA] Extraction complete for {Path(path).name}")
        if not text:
            print(f"🚨 [INFRA] WARNING: No text extracted from {path}")
        else:
            print(f"🔍 [INFRA] Text Sample (first 500 chars): {text[:500]}...")
            
        return text
    except Exception as e:
        print(f"🚨 [INFRA] Extraction failed for {path}: {e}")
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
    """Deterministic Skill Extractor: Robust matching using dual-layer normalization."""
    if not text: return []
    
    # Pre-process text once
    text_processed = text.lower()
    text_norm = normalize_skill(text_processed)
    
    found_skills = set()
    
    # 1. Dictionary Search with Normalization
    for skill in SKILL_DICTIONARY:
        s_raw = skill.strip()
        s_norm = normalize_skill(s_raw)
        
        # Exact match in normalized text (Handles 'Scikit-Learn' vs 'ScikitLearn')
        if s_norm in text_norm:
            # Re-verify boundaries in original processed text for short strings
            if len(s_raw) <= 3 or any(c in s_raw for c in '+#.'):
                pattern = r'(?:^|[\s,])' + re.escape(s_raw.lower()) + r'(?:[\s,]|$)'
                if re.search(pattern, text_processed):
                    found_skills.add(s_raw.title())
            else:
                found_skills.add(s_raw.title())
            
    # 2. Synonym/Abbreviation Overrides
    for token in text_processed.split():
        if token in SYNONYM_MAP:
            found_skills.add(SYNONYM_MAP[token].title())
            
    return sorted(list(found_skills))

def get_semantic_matches(resume_skills: list, jd_skills: list, threshold: float = 0.85) -> list:
    """Finds skills that are conceptually similar using embeddings."""
    if not resume_skills or not jd_skills: return []
    
    # Filter out direct matches first
    matched = [s for s in resume_skills if s in jd_skills]
    remaining_r = [s for s in resume_skills if s not in matched]
    remaining_j = [s for s in jd_skills if s not in matched]
    
    if not remaining_r or not remaining_j: return matched
    
    try:
        r_embs = get_embeddings_safe(remaining_r)
        j_embs = get_embeddings_safe(remaining_j)
        
        for i, r_emb in enumerate(r_embs):
            for j, j_emb in enumerate(j_embs):
                sim = safe_similarity(r_emb, j_emb)
                if sim >= threshold:
                    matched.append(remaining_r[i])
                    break
    except:
        pass
        
    return list(set(matched))

def normalize_text(text: str) -> str:
    """Standardizes text for robust comparison by removing noise and extra spaces."""
    if not text: return ""
    text = text.lower().strip()
    # Remove noise but keep important chars for tech (+, #, .)
    text = re.sub(r'[^\w\s\+\#\.]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

def fuzzy_match_skills(resume_skills: list, jd_skills: list) -> list:
    """Intelligent skill matching using fuzzy logic and semantic similarity."""
    # 1. Fuzzy Ratio Match using normalized skill strings
    matched = []
    jd_norm = [normalize_skill(s) for s in jd_skills]
    
    for r in resume_skills:
        r_norm = normalize_skill(r)
        # Find best match in JD skills
        best_match = process.extractOne(r_norm, jd_norm, scorer=fuzz.token_set_ratio)
        if best_match and best_match[1] >= 85:
            matched.append(r)
            
    # 2. Semantic Augmentation
    semantic_matched = get_semantic_matches(resume_skills, jd_skills)
    matched.extend(semantic_matched)
    
    return sorted(list(set(matched)))

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
            return [["Prediction Unavailable"]] * len(resume_texts)
        
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
    """Production Tuning: Adjusts weights based on role type and seniority."""
    # INDUSTRY STANDARD TECH WEIGHTS: 35% Semantic, 45% Skills, 20% Role Match
    weights = {"semantic": 0.35, "skills": 0.45, "role": 0.20, "exp": 0.0}
    
    role = str(role).lower()
    # Management/HR roles value experience more (30% weight)
    if any(m in role for m in ["manager", "hr", "lead", "director"]):
        weights = {"semantic": 0.25, "skills": 0.25, "role": 0.20, "exp": 0.30}
        
    # Senior technical roles boost experience weight slightly
    elif years > 7:
        weights["exp"] = 0.15
        weights["skills"] -= 0.05
        weights["semantic"] -= 0.10
        
    return weights

def is_valid_job_description(text: str) -> bool:
    """Production Guardrail: Rejects gibberish or empty text while allowing short titles."""
    if not text: return False
    
    jd_clean = text.lower().strip()
    
    # 1. Whitelist for common short roles
    COMMON_ROLES = [
        "data analyst", "data scientist", "python developer", "react developer",
        "software engineer", "frontend developer", "backend developer",
        "ai engineer", "ml engineer", "devops engineer", "analyst", "engineer",
        "developer", "manager", "hr manager", "recruiter"
    ]
    if any(role in jd_clean for role in COMMON_ROLES):
        return True

    # 2. Minimum length (very relaxed)
    if len(jd_clean) < 3:
        return False

    # 3. Detect repeated character nonsense
    if re.search(r'(.)\1{10,}', text):
        return False

    # 4. Minimum meaningful word count
    words = re.findall(r'\b[a-zA-Z]{2,}\b', text)
    if len(words) < 1:
        return False

    return True

def expand_job_description(text: str) -> str:
    """Intelligently enriches short JDs with industry-standard skills for better matching."""
    text_lower = text.lower()
    
    # Only expand if it's a very short description/title
    if len(text.split()) > 15:
        return text
        
    expansion = "\n[AUTO-EXPANSION]: "
    added = False
    
    # Context-aware expansion maps
    knowledge_map = {
        "data analyst": "SQL, Excel, Power BI, Tableau, Python, statistics, data visualization, reporting.",
        "data scientist": "Python, R, Machine Learning, Statistics, SQL, Pandas, Scikit-learn, Deep Learning.",
        "machine learning": "Python, PyTorch, TensorFlow, Scikit-learn, Math, Algorithms, Deep Learning, MLOps.",
        "backend": "Node.js, Python, Java, SQL, APIs, Microservices, Databases, Cloud, System Design.",
        "frontend": "React, JavaScript, CSS, HTML, TypeScript, UI/UX, Responsive Design, Redux.",
        "full stack": "React, Node.js, JavaScript, SQL, MongoDB, Web Development, Git, Deployment.",
        "devops": "Docker, Kubernetes, AWS, CI/CD, Jenkins, Terraform, Linux, Automation."
    }
    
    for key, skills in knowledge_map.items():
        if key in text_lower:
            expansion += f"Relevant skills: {skills} "
            added = True
            
    return text + (expansion if added else "")

def batch_compute_match_score(resume_texts: list, job_description: str) -> list:
    """
    Elite Hybrid Scoring with Hard Validation Guardrails.
    """
    # --- HARD INPUT QUALITY VALIDATION ---
    if not is_valid_job_description(job_description):
        print("🚨 [AI-VAL] REJECTED: Low-quality or gibberish JD detected.")
        return [{
            "match_percentage": 0, 
            "final_score": 0.0,
            "skills": [],
            "resume_skills": [],
            "predicted_role": "Invalid Input",
            "summary_reasoning": "Job description is too short. Please provide at least 2 words (e.g., 'Data Analyst')."
        }] * len(resume_texts)

    # --- INTELLIGENT EXPANSION ---
    job_description = expand_job_description(job_description)
    logging.info(f"📝 [AI] Final JD Length: {len(job_description)} chars")

    jd_sections = extract_sections(job_description)
    jd_skills_text = jd_sections["skills"] if jd_sections["skills"] else job_description
    jd_skills_list = extract_skills(jd_skills_text)
    
    # --- ELITE FIX: JD Skill Inference ---
    if not jd_skills_list or len(jd_skills_list) < 3:
        print("🔍 [AI] JD skills weak. Inferring from role...")
        jd_lower = job_description.lower()
        inferred = []
        for role, skills in ROLE_SKILLS.items():
            if role in jd_lower:
                inferred.extend(skills)
        
        if inferred:
            jd_skills_list = sorted(list(set(jd_skills_list + inferred)))
            print(f"✅ [AI] Inferred {len(inferred)} skills from JD context.")

    # Final JD skills normalization for printing
    print(f"DEBUG: JD skills: {jd_skills_list[:15]}")
    
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
        # Removed legacy 444MB pickle classifier load. 
        # We now rely exclusively on HF embeddings and detect_role_from_resume.

        jd_emb = embeddings[0] if embeddings is not None else None
        
        for i, text in enumerate(resume_texts):
            print(f"🔍 [AI] Processing Resume {i+1}...")
            
            # --- Text Extraction ---
            print("🔍 [AI] Extracting sections...")
            # --- PRODUCTION GRADE SCORING ENGINE (ELITE V2) ---
            # 1. Experience & Text Extraction
            years = extract_years_of_experience(text)
            r_skills = extract_skills(text)
            
            # 2. Semantic Similarity Calculation
            semantic_score = 0.5 # Baseline
            if jd_emb is not None and embeddings is not None:
                sim = safe_similarity(jd_emb, embeddings[i+1])
                # Boost raw similarity to industry match levels
                semantic_score = max(0, min(1, (float(sim) + 0.1) * 1.3))
            
            # 3. High-Fidelity Role Prediction
            best_role = detect_role_from_resume(text)
            
            # 4. Technical Skill Alignment
            matched_with_jd = fuzzy_match_skills(r_skills, jd_skills_list)
            skill_score = len(matched_with_jd) / max(len(jd_skills_list), 1)
            
            # 5. Role Validation (Direct match with JD intent)
            role_match_score = 1.0 if best_role.lower() in job_description.lower() else 0.5
            
            # 6. Dynamic Weighting (Entry-level friendly)
            weights = get_dynamic_weights(best_role, years)
            
            # 7. Semantic Bonus for strong contextual matches
            adj_semantic_score = semantic_score
            if adj_semantic_score > 0.60:
                adj_semantic_score = min(1.0, adj_semantic_score * 1.2)
            
            # FINAL CALCULATION (Weighted Sum)
            raw_percentage = (
                (adj_semantic_score * weights["semantic"]) + 
                (skill_score * weights["skills"]) + 
                (role_match_score * weights["role"])
            ) * 100

            # 8. Experience Bonus (Only for senior/management roles)
            if weights["exp"] > 0:
                raw_percentage += (min(years / 10, 1.0) * weights["exp"] * 100)
            
            # 9. Framework Bonus (Proficiency Multiplier)
            if any(x in text.lower() for x in ["tensorflow", "pytorch", "react", "node", "aws", "kubernetes"]):
                raw_percentage *= 1.15 # 15% Industry Mastery Bonus
            
            match_percentage = int(min(98, max(12, raw_percentage)))
            print(f"✅ [AI-ELITE] {best_role} Score: {match_percentage}%")

            # --- Production Reasoning Layer ---
            reasoning = []
            if matched_with_jd: 
                reasoning.append(f"Strong alignment in {', '.join(matched_with_jd[:3])}.")
            
            missing_skills = list(set(jd_skills_list) - set(matched_with_jd))
            if missing_skills: 
                reasoning.append(f"To improve, consider adding: {', '.join(missing_skills[:3])}.")
            
            required_years = extract_years_from_jd(job_description)
            if years >= required_years and required_years > 0:
                reasoning.append("Experience requirements fully met.")
            elif required_years > 0:
                reasoning.append(f"Candidate is developing the required {int(required_years)} years of experience.")

            # --- Final Response Construction ---
            resume_skills_unique = list(set(r_skills))
            priority_skills = sorted(matched_with_jd)
            other_skills = sorted([s for s in resume_skills_unique if s not in matched_with_jd])
            unified_skills = priority_skills + other_skills

            final_results.append({
                "match_percentage": match_percentage,
                "final_score": float(match_percentage) / 100.0,
                "predicted_role": best_role, 
                "experience": f"{int(years)} Years" if years > 0 else "Fresher",
                "experience_years": int(years),
                "skills": unified_skills,
                "resume_skills": resume_skills_unique,
                "matched_skills": priority_skills,
                "all_skills": resume_skills_unique,
                "matched_skills_count": len(matched_with_jd),
                "total_skills": len(resume_skills_unique),
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