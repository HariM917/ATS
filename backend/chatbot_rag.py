import os
import sys
import numpy as np
import faiss
import time
import json
import logging
from huggingface_hub import InferenceClient
import requests
from flask import session
import db_manager
from dotenv import load_dotenv

# FIX: Prevent Windows charmap codec crash on emoji/unicode in print()
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

logger = logging.getLogger(__name__)

# FIX: Explicitly load .env from current directory
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)
HF_TOKEN = os.getenv("HF_TOKEN")

# --- CRITICAL LLM DIAGNOSTICS ---
if HF_TOKEN:
    print(f"\n[AI-DIAGNOSTIC] HF_TOKEN loaded successfully. (Ends with ...{HF_TOKEN[-4:]})")
else:
    print("\n[AI-DIAGNOSTIC] ERROR: HF_TOKEN NOT FOUND IN ENVIRONMENT OR .ENV")
    print(f"[AI-DIAGNOSTIC] Checked path: {env_path}")

hf_client = InferenceClient(api_key=HF_TOKEN)

# CRITICAL: Switch to v0.2 for better routing stability on HF
client = InferenceClient(
    model="mistralai/Mistral-7B-Instruct-v0.2",
    token=HF_TOKEN,
    timeout=120
)

# --- ADVANCED KNOWLEDGE BASE ---
# --- ADVANCED KNOWLEDGE BASE ---
KNOWLEDGE_BASE = {
    "resume_structure": {
        "domain": "resume",
        "items": [
            "Use a clean, reverse-chronological format. Sections: Header, Summary, Skills, Experience, Education, Projects.",
            "Keep it to 1 page (unless 10+ years exp). Use standard fonts (Arial, Calibri) size 10-12. Save as PDF.",
            "Avoid photos, charts, or skill bars. ATS scanners cannot read them properly."
        ]
    },
    "resume_content": {
        "domain": "resume",
        "items": [
            "The XYZ Formula: Accomplished [X] as measured by [Y], by doing [Z].",
            "Start every bullet with a power verb: Engineered, Spearheaded, Optimized, Orchestrated.",
            "Tailor your resume to the Job Description (JD) keywords."
        ]
    },
    "interview_behavioral": {
        "domain": "interview",
        "items": [
            "The STAR Method: Situation, Task, Action, Result. Focus on your specific actions.",
            "Prepare stories for Leadership, Failure, Conflict Resolution, and Innovation."
        ]
    },
    "interview_technical": {
        "domain": "interview",
        "items": [
            "Practice LeetCode (Easy/Medium) for DSA. Focus on Arrays, HashMaps, and Trees.",
            "Study scalability, load balancing, and database choices (SQL vs NoSQL) for senior roles.",
            "Document your code and write tests for take-home assignments."
        ]
    },
    "skills_data_science": {
        "domain": "data_science",
        "items": [
            "Data Science Roadmap: 1. Python (Pandas, NumPy), 2. SQL & Databases, 3. Statistics & Probability, 4. Data Visualization (Tableau/Seaborn), 5. Machine Learning (Scikit-Learn).",
            "Advanced DS: Deep Learning (PyTorch), Big Data (Spark), Cloud Deployment (AWS/GCP)."
        ]
    },
    "skills_ml": {
        "domain": "data_science",
        "items": [
            "Machine Learning Roadmap: 1. Python Fundamentals, 2. Linear Algebra & Calculus, 3. NumPy/Pandas/Matplotlib, 4. Scikit-Learn (Regression/Clustering), 5. TensorFlow or PyTorch, 6. Neural Networks & Deep Learning, 7. MLOps (Docker, MLflow).",
            "Focus on: Feature Engineering, Model Validation, Hyperparameter Tuning, and Deployment."
        ]
    },
    "skills_backend": {
        "domain": "backend",
        "items": [
            "Backend Roadmap: 1. Language (Python/Node/Java), 2. Web Frameworks (FastAPI/Express/Spring), 3. Relational DBs (PostgreSQL), 4. NoSQL (MongoDB/Redis), 5. APIs (REST/GraphQL), 6. Caching & Message Queues, 7. CI/CD & Cloud."
        ]
    },
    "salary_strategy": {
        "domain": "general",
        "items": [
            "Never give the first number. Ask for the budget for the role instead.",
            "Research market rates on Levels.fyi, Glassdoor, and Blind.",
            "Always negotiate counter-offers professionally based on research."
        ]
    }
}

# --- OPTIMIZATION: SEMANTIC CACHE (HF-POWERED) ---
class SemanticCache:
    def __init__(self, threshold=0.15):
        self.threshold = threshold 
        self.index = None
        self.cached_responses = [] 
        
    def get(self, query, user_role, user_email):
        if self.index is None: return None
        try:
            # Use HF for cache query embedding
            q_emb = hf_client.feature_extraction(
                [query],
                model="sentence-transformers/all-MiniLM-L6-v2"
            )
            q_emb = np.array(q_emb).astype('float32')
            
            D, I = self.index.search(q_emb, 1)
            
            if D[0][0] < self.threshold:
                hit = self.cached_responses[I[0][0]]
                if (hit['role'] == user_role or hit['role'] == 'all') and hit['email'] == user_email:
                    return hit['response']
        except:
            pass
        return None

    def add(self, query, response, user_role, user_email):
        try:
            q_emb = hf_client.feature_extraction(
                [query],
                model="sentence-transformers/all-MiniLM-L6-v2"
            )
            q_emb = np.array(q_emb).astype('float32')
            
            if self.index is None:
                dim = q_emb.shape[1]
                self.index = faiss.IndexFlatL2(dim)
            
            self.index.add(q_emb)
            self.cached_responses.append({
                "query": query, "response": response, 
                "role": user_role, "email": user_email
            })
        except:
            pass

QUERY_CACHE = {} # Still keep simple cache for exact matches
SEMANTIC_CACHE = None
LOG_FILE = "rag_observability.log"

def log_event(event_data):
    """Logs RAG events for observability"""
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                **event_data
            }, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.error(f"[LOG ERROR] Failed to write to {LOG_FILE}: {e}")

# --- RAG ENGINE ---
class RAGManager:
    def __init__(self):
        logger.info("=" * 50)
        logger.info("[RAG] SYSTEM STARTUP: HF Inference Mode Active")
        logger.info("=" * 50)
        self.documents = []
        self.index = None
        self.model = None # Legacy attribute to prevent AttributeErrors
        self.last_rebuild = 0
        self.refresh_interval = 600 # 10 minutes
        # Initial build
        self.rebuild_index()

    def rebuild_index(self, force=False):
        """Builds index with lazy loading and semantic persistence."""
        current_time = time.time()
        
        # Performance optimization: Don't rebuild if index exists and not expired
        if not force and self.index is not None and (current_time - self.last_rebuild < self.refresh_interval):
            return

        logger.info("[RAG] Refreshing index with latest database state...")
        new_docs = []
        
        # 1. Load Static Knowledge
        for category, config in KNOWLEDGE_BASE.items():
            for item in config["items"]:
                new_docs.append({
                    "text": item, "category": category, "type": "Career Guide", 
                    "access": "all", "domain": config["domain"]
                })
        
        # 2. Load Dynamic Data
        try:
            conn = db_manager.get_db_connection()
            jobs = conn.execute('SELECT title, description, required_skills FROM jobs').fetchall()
            for job in jobs:
                new_docs.append({
                    "text": f"Job Posting: {job['title']}. Description: {job['description']}. Required Skills: {job['required_skills']}",
                    "category": "ats_jobs", "type": "Job Listing", "access": "all", "domain": "general"
                })
            
            apps = conn.execute('SELECT candidate_name, score, status FROM applications ORDER BY score DESC LIMIT 50').fetchall()
            for app in apps:
                new_docs.append({
                    "text": f"Candidate {app['candidate_name']} has an AI match score of {int(app['score']*100)}% and is currently {app['status']}.",
                    "category": "ats_candidates", "type": "Candidate Profile", "access": "hr", "domain": "hr"
                })
            conn.close()
        except Exception as e:
            logger.error(f"[RAG] DB Indexing Failed: {e}")

        # 3. Only Update if content changed or index missing
        if len(new_docs) != len(self.documents) or self.index is None or force:
            self.documents = new_docs
            texts = [doc["text"] for doc in self.documents]
            
            if not HF_TOKEN or not texts:
                logger.error("[RAG] Skipping embedding phase (No token/docs)")
                return

            logger.info(f"[RAG] Generating HF Embeddings for {len(texts)} documents...")
            try:
                embeddings = hf_client.feature_extraction(
                    texts,
                    model="sentence-transformers/all-MiniLM-L6-v2"
                )
                embeddings = np.array(embeddings).astype('float32')
                
                dim = embeddings.shape[1]
                self.index = faiss.IndexFlatL2(dim)
                self.index.add(embeddings)
                self.last_rebuild = current_time
                logger.info(f"✅ [RAG] Index refreshed. Count: {len(self.documents)}")
            except Exception as e:
                logger.error(f"[RAG] HF Vectorization Failed: {e}")
                return

    def search(self, query, user_role="candidate", k=5):
        self.rebuild_index()
        
        try:
            q_emb = hf_client.feature_extraction(
                [query],
                model="sentence-transformers/all-MiniLM-L6-v2"
            )
            q_emb = np.array(q_emb).astype('float32')
        except Exception as e:
            logger.error(f"[RAG] Search embedding failed: {e}")
            return []
            
        # SAFETY CHECK: Ensure index exists before search
        if self.index is None:
            logger.error("[RAG] Search attempted but index is None.")
            return []
        
        # FAISS search
        try:
            D, I = self.index.search(q_emb, k * 3) 
        except Exception as e:
            logger.error(f"[RAG] FAISS search failed: {e}")
            return []
        
        results = []
        for dist, idx in zip(D[0], I[0]):
            if idx != -1:
                doc = self.documents[idx]
                
                # RBAC Hardening: Strict filter
                if doc['access'] == 'hr' and user_role != 'hr':
                    log_event({"event": "rbac_violation_attempt", "query": query, "doc_type": doc['type']})
                    continue
                
                # Hybrid Scoring: Semantic Distance + Keyword Bonus
                query_words = set(query.lower().split())
                doc_words = set(doc['text'].lower().split())
                overlap = len(query_words.intersection(doc_words))
                
                # Normalize overlap bonus (max bonus 0.2)
                bonus = min(0.2, (overlap / max(1, len(query_words))) * 0.2)
                final_score = dist - bonus
                
                results.append((final_score, doc))
        
        results.sort(key=lambda x: x[0])
        return [r[1] for r in results[:k]]

# Lazy initialize
rag = None

def classify_query(query):
    """Categorizes query for cost/latency optimization (Dictionary Return)"""
    if not query:
        return {"type": "general"}
        
    q = str(query).lower()
    q_words = q.split()
    nav_keywords = ["hello", "hi", "help", "menu", "who", "start", "hey"]
    
    if any(k in q_words for k in nav_keywords):
        return {"type": "navigation"}
    
    simple_keywords = ["resume format", "interview tips", "backend skills", "salary research"]
    if any(k in q for k in simple_keywords):
        return {"type": "simple"}
        
    if any(k in q for k in ["roadmap", "how to", "career path", "guide"]):
        return {"type": "analysis"}
    
    return {"type": "general"}

def fallback_response(context, intent="general"):
    """Smart fallback: synthesizes a helpful answer from retrieved context when LLM fails."""
    if not context or not context.strip():
        return (
            "I'm here to support your career journey! I can provide guidance on resume optimization, "
            "interview strategies, technical skill roadmaps, and salary negotiation. "
            "What specific area can I help you with right now?"
        )

    # Extract clean sentences from context, filtering for quality
    sentences = []
    for line in context.split("\n"):
        parts = line.split(".")
        for p in parts:
            clean_p = p.strip()
            if len(clean_p) > 20: # Only keep substantial sentences
                sentences.append(clean_p)
    
    top = sentences[:5]

    intent_labels = {
        "learning": "mastering new skills",
        "resume": "crafting a standout resume",
        "interview": "acing your next interview",
        "general": "your career advancement"
    }
    label = intent_labels.get(intent, "your career advancement")

    body = "\n".join([f"• {s.rstrip('.')}." for s in top])
    
    # Structure it to look like a synthesized AI response
    return (
        f"Based on my analysis for {label}, here are the most effective strategies:\n\n"
        f"{body}\n\n"
        f"Would you like more details on any of these points, or shall we move on to another topic?"
    )


def get_llm_generation(query, context, history, intent="general", reasoning=True):
    if not HF_TOKEN:
        print("🚨 HF_TOKEN missing")
        return None

    try:
        print("🔁 Calling HuggingFace LLM (chat_completion)...")
        
        response = client.chat_completion(
            messages=[
                {"role": "system", "content": "You are a professional AI Career Coach. Give clear, structured, practical advice."},
                {"role": "user", "content": f"User Question: {query}\n\nRelevant Context:\n{context}"}
            ],
            max_tokens=500,
            temperature=0.7,
        )

        ai_text = response.choices[0].message.content

        print("🧠 LLM RAW OUTPUT:", ai_text)

        if isinstance(ai_text, str) and len(ai_text.strip()) > 5:
            print("✅ LLM SUCCESS")
            return ai_text.strip()

        print("🚨 LLM returned empty or too short")
        return None

    except Exception as e:
        print("🚨 LLM ERROR:", e)
        return None

def get_response(user_message):
    """Bulletproof RAG Pipeline with smart fallback chain."""
    global rag, SEMANTIC_CACHE
    logger.info("[CORE] RAG PIPELINE ACTIVE")
    QUERY_CACHE.clear()
    
    start_time = time.time()
    user_role = session.get("role", "candidate")
    user_email = session.get("email", "anonymous")
    
    if not user_message:
        return "I'm ready to help. What's on your mind?"
    
    try:
        # 1. QUERY CLASSIFICATION (With Safety Check)
        classification = classify_query(user_message) or {}
        q_type = classification.get("type", "general")
        logger.info(f"[CLASSIFY] type={q_type}, query={user_message[:60]}")
        
        # NOTE: Removed early navigation return to allow LLM to handle greetings naturally

        if rag is None: 
            rag = RAGManager()
            SEMANTIC_CACHE = SemanticCache()
        
        # 2. SEMANTIC CACHE (User-Aware)
        sem_hit = SEMANTIC_CACHE.get(user_message, user_role, user_email)
        if sem_hit:
            logger.info("[CACHE HIT] Returning cached response")
            log_event({"query": user_message, "type": "semantic_cache_hit", "latency": time.time() - start_time, "email": user_email})
            return sem_hit

        # 3. INTENT & DOMAIN DETECTION
        intent = "general"
        domain = "general"
        lower_msg = user_message.lower()
        
        if any(k in lower_msg for k in ["data science", "ml", "pandas", "numpy", "scikit"]): domain = "data_science"
        elif any(k in lower_msg for k in ["backend", "api", "django", "fastapi", "sql"]): domain = "backend"
        elif any(k in lower_msg for k in ["resume", "cv", "portfolio"]): domain = "resume"
        elif any(k in lower_msg for k in ["interview", "prep", "mock"]): domain = "interview"

        if any(k in lower_msg for k in ["learn", "roadmap", "how to", "study"]): intent = "learning"
        elif domain == "resume": intent = "resume"
        elif domain == "interview": intent = "interview"
        logger.info(f"[INTENT] intent={intent}, domain={domain}")

        # 4. RETRIEVAL
        semantic_results = rag.search(user_message, user_role=user_role, k=8)
        logger.info(f"[RAG] Retrieved {len(semantic_results)} documents")
        
        # 5. DOMAIN FILTERING
        filtered_results = [res for res in semantic_results if res.get('domain') == domain or res.get('domain') == 'general']
        if len(filtered_results) < 2:
            filtered_results = semantic_results[:3]

        # 6. BUILD CONTEXT (Deduplicated)
        unique_texts = []
        seen = set()
        sources = set()
        for res in filtered_results:
            clean_text = res['text'].replace("[Career Guide]", "").strip()
            if clean_text not in seen:
                unique_texts.append(clean_text)
                seen.add(clean_text)
                sources.add(res['type'])
        
        context = "\n\n".join(unique_texts)
        logger.info(f"[CONTEXT] {len(unique_texts)} unique chunks, {len(context)} chars")
        
        # --- PERSISTENT HISTORY ---
        history = session.get('chat_history', [])
        if not history and user_email != "anonymous":
            history = db_manager.get_chat_history(user_email, limit=5)
        
        # 7. LLM GENERATION (with retry)
        print(f">>> [DEBUG] Context length: {len(context)}")
        ai_answer = get_llm_generation(user_message, context, history, intent=intent)
        
        if isinstance(ai_answer, str) and len(ai_answer.strip()) > 5:
            print("✅ Using LLM response")
            final_response = ai_answer.strip()
        else:
            print("🚨 Falling back to smart response")
            final_response = fallback_response(context, intent)

        # 8. OBSERVABILITY & CLEANUP
        latency = time.time() - start_time
        logger.info(f"[DONE] latency={latency:.2f}s, response_len={len(final_response)}")
        
        log_event({
            "query": user_message, "type": "rag_query", "q_type": q_type, "latency": latency,
            "sources": list(sources), "role": user_role, "email": user_email
        })

        # 9. MEMORY & CACHE UPDATE
        history.append({"user": user_message, "ai": final_response})
        session['chat_history'] = history[-5:]
        
        if user_email != "anonymous":
            db_manager.save_chat_message(user_email, user_role, user_message, final_response)
            
        SEMANTIC_CACHE.add(user_message, final_response, user_role, user_email)
        
        return final_response

    except Exception as e:
        logger.error(f"[PIPELINE ERROR]: {e}")
        log_event({"type": "pipeline_error", "error": str(e), "query": user_message[:50]})
        return fallback_response("", "general")