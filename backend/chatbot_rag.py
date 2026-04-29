import os
import sys
import numpy as np
import faiss
import time
import json
import logging
from sentence_transformers import SentenceTransformer
from huggingface_hub import InferenceClient
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
            "Data Science Roadmap: Python (Pandas/NumPy/Scikit-learn), SQL, Statistics, Linear Algebra.",
            "Visualization: Matplotlib, Seaborn, Tableau. Model Deployment: Flask/FastAPI, AWS/GCP.",
            "Machine Learning: Regression, Classification, Clustering, Deep Learning (TensorFlow/PyTorch)."
        ]
    },
    "skills_backend": {
        "domain": "backend",
        "items": [
            "Backend Roadmap: Python (Django/FastAPI) or Node.js (Express). PostgreSQL/MongoDB.",
            "REST/GraphQL APIs, Microservices, Caching (Redis), Message Queues (RabbitMQ/Kafka).",
            "Cloud & DevOps: Docker, Kubernetes, CI/CD, Serverless (AWS Lambda)."
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

# --- OPTIMIZATION: SEMANTIC CACHE & LOGGING ---
class SemanticCache:
    def __init__(self, model, threshold=0.15):
        self.model = model
        self.threshold = threshold # L2 distance threshold
        self.index = None
        self.cached_responses = [] # Stores (query, response, role)
        
    def get(self, query, user_role, user_email):
        if self.index is None: return None
        q_emb = self.model.encode([query])
        D, I = self.index.search(np.array(q_emb).astype('float32'), 1)
        
        if D[0][0] < self.threshold:
            hit = self.cached_responses[I[0][0]]
            # ELITE ISOLATION: Check both role AND email for semantic cache hits
            if (hit['role'] == user_role or hit['role'] == 'all') and hit['email'] == user_email:
                return hit['response']
        return None

    def add(self, query, response, user_role, user_email):
        q_emb = self.model.encode([query])
        if self.index is None:
            dim = q_emb.shape[1]
            self.index = faiss.IndexFlatL2(dim)
        
        self.index.add(np.array(q_emb).astype('float32'))
        self.cached_responses.append({
            "query": query, "response": response, 
            "role": user_role, "email": user_email
        })

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
        logger.info("[RAG] SYSTEM STARTUP: Wiping Caches & Initializing...")
        logger.info("[RAG] Semantic Search Indexing in progress...")
        logger.info("=" * 50)
        self.model = SentenceTransformer("all-mpnet-base-v2")
        self.documents = []
        self.last_rebuild = 0
        self.refresh_interval = 300 # 5 minutes
        self.rebuild_index()

    def rebuild_index(self):
        """Builds index from static knowledge + Dynamic ATS data"""
        current_time = time.time()
        if current_time - self.last_rebuild < self.refresh_interval and self.documents:
            return

        logger.info("[RAG] Rebuilding Index with fresh ATS data...")
        self.documents = []
        
        for category, config in KNOWLEDGE_BASE.items():
            for item in config["items"]:
                self.documents.append({
                    "text": item, "category": category, "type": "Career Guide", 
                    "access": "all", "domain": config["domain"]
                })
        
        try:
            conn = db_manager.get_db_connection()
            jobs = conn.execute('SELECT title, description, skills FROM jobs').fetchall()
            for job in jobs:
                self.documents.append({
                    "text": f"Job Posting: {job['title']}. Description: {job['description']}. Required Skills: {job['skills']}",
                    "category": "ats_jobs", "type": "Job Listing", "access": "all", "domain": "general"
                })
            
            apps = conn.execute('SELECT candidate_name, score, status FROM applications ORDER BY score DESC LIMIT 50').fetchall()
            for app in apps:
                self.documents.append({
                    "text": f"Candidate {app['candidate_name']} has an AI match score of {int(app['score']*100)}% and is currently {app['status']}.",
                    "category": "ats_candidates", "type": "Candidate Profile", "access": "hr", "domain": "hr"
                })
            conn.close()
        except Exception as e:
            logger.error(f"[RAG] Failed to index dynamic data: {e}")

        if self.documents:
            texts = [doc["text"] for doc in self.documents]
            embeddings = self.model.encode(texts)
            dim = embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dim)
            self.index.add(np.array(embeddings).astype('float32'))
            self.last_rebuild = current_time
            logger.info(f"[RAG] Indexed {len(self.documents)} total points.")

    def search(self, query, user_role="candidate", k=5):
        self.rebuild_index()
        q_emb = self.model.encode([query])
        # FAISS search
        D, I = self.index.search(np.array(q_emb).astype('float32'), k * 3) # Over-fetch for filtering
        
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
    """Categorizes query for cost/latency optimization"""
    q = query.lower()
    q_words = q.split()
    nav_keywords = ["hello", "hi", "help", "menu", "who", "start"]
    if any(k in q_words for k in nav_keywords):
        return "navigation"
    
    simple_keywords = ["resume format", "interview tips", "backend skills", "salary research"]
    if any(k in q for k in simple_keywords):
        return "simple"
    
    return "analysis"

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
        # 1. QUERY CLASSIFICATION
        q_type = classify_query(user_message)
        logger.info(f"[CLASSIFY] type={q_type}, query={user_message[:60]}")
        
        # NOTE: Removed early navigation return to allow LLM to handle greetings naturally

        if rag is None: 
            rag = RAGManager()
            SEMANTIC_CACHE = SemanticCache(rag.model)
        
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