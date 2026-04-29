import os
import numpy as np
import faiss
import time
import json
from sentence_transformers import SentenceTransformer
from huggingface_hub import InferenceClient
from flask import session
import db_manager
from dotenv import load_dotenv

load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")
client = InferenceClient(token=HF_TOKEN)

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
        
    def get(self, query, user_role):
        if self.index is None: return None
        q_emb = self.model.encode([query])
        D, I = self.index.search(np.array(q_emb).astype('float32'), 1)
        
        if D[0][0] < self.threshold:
            hit = self.cached_responses[I[0][0]]
            if hit['role'] == user_role or hit['role'] == 'all':
                return hit['response']
        return None

    def add(self, query, response, user_role):
        q_emb = self.model.encode([query])
        if self.index is None:
            dim = q_emb.shape[1]
            self.index = faiss.IndexFlatL2(dim)
        
        self.index.add(np.array(q_emb).astype('float32'))
        self.cached_responses.append({"query": query, "response": response, "role": user_role})

QUERY_CACHE = {} # Still keep simple cache for exact matches
SEMANTIC_CACHE = None
LOG_FILE = "rag_observability.log"

def log_event(event_data):
    """Logs RAG events for observability"""
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            **event_data
        }) + "\n")

# --- RAG ENGINE ---
class RAGManager:
    def __init__(self):
        print("\n" + "="*50)
        print("[RAG] SYSTEM STARTUP: Wiping Caches & Initializing...")
        print("[RAG] Semantic Search Indexing in progress...")
        print("="*50 + "\n")
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

        print("[RAG] Rebuilding Index with fresh ATS data...")
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
            print(f"[RAG] Failed to index dynamic data: {e}")

        if self.documents:
            texts = [doc["text"] for doc in self.documents]
            embeddings = self.model.encode(texts)
            dim = embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dim)
            self.index.add(np.array(embeddings).astype('float32'))
            self.last_rebuild = current_time
            print(f"[RAG] Indexed {len(self.documents)} total points.")

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
    nav_keywords = ["hello", "hi", "help", "menu", "who are you", "start"]
    if any(k in q for k in nav_keywords):
        return "navigation"
    
    simple_keywords = ["resume format", "interview tips", "backend skills", "salary research"]
    if any(k in q for k in simple_keywords):
        return "simple"
    
    return "analysis"

def get_llm_generation(query, context, history, intent="general", reasoning=True):
    """Synthesizes an answer using HuggingFace LLM with a Conversational Human Persona"""
    if not HF_TOKEN or not context: return None
    history_str = "\n".join([f"User: {h['user']}\nAI: {h['ai']}" for h in history[-2:]])
    
    # Dynamic Human-Centric Personas
    personas = {
        "learning": "expert technical mentor",
        "resume": "professional resume strategist",
        "interview": "senior interview coach",
        "general": "world-class career strategist"
    }
    persona = personas.get(intent, personas["general"])
    
    prompt = f"""<|system|>
You are a {persona}. Your goal is to provide helpful, natural, and encouraging advice.
RULES:
1. Answer naturally and conversationally, like ChatGPT.
2. DO NOT mention "context", "database", "retrieval", or "sources".
3. DO NOT say "Based on the provided information".
4. Use clear paragraphs and only use bullet points for actionable steps.
5. If you don't know the answer, give your best general {intent} advice in a supportive tone.
6. Speak directly to the user as their mentor.

CONTEXT (Use this for your expertise, but don't mention it):
{context}

CHAT HISTORY:
{history_str}
<|user|>
{query}
<|assistant|>"""

    try:
        print(f"[LLM] Calling Zephyr-7B for query: {query[:50]}...")
        response = client.text_generation(
            prompt, model="HuggingFaceH4/zephyr-7b-beta",
            max_new_tokens=300, temperature=0.1, repetition_penalty=1.1
        )
        return response.strip()
    except Exception as e:
        print(f"[LLM ERROR]: {e}")
        log_event({"type": "llm_error", "error": str(e), "query": query[:50]})
        return None

def get_response(user_message):
    """Optimized & Observable RAG Pipeline"""
    global rag, SEMANTIC_CACHE
    print("🔥 [CORE] RAG PIPELINE ACTIVE - NEW CODE IS RUNNING")
    QUERY_CACHE.clear() # Temporary force-clear to solve ghost caching
    
    start_time = time.time()
    user_role = session.get("role", "candidate")
    
    if not user_message: return "I'm ready to help. What's on your mind?"
    
    # 1. QUERY CLASSIFICATION
    q_type = classify_query(user_message)
    if q_type == "navigation":
        return "I'm the TalentFlow AI. I can help with resume tips, interview prep, or exploring job matches. What would you like to do?"

    # 2. LATENCY OPTIMIZATION: CACHE DISABLED FOR HARDENING
    # if user_message in QUERY_CACHE:
    #     log_event({"query": user_message, "type": "exact_cache_hit", "latency": time.time() - start_time})
    #     return QUERY_CACHE[user_message]
    
    if rag is None: 
        rag = RAGManager()
        SEMANTIC_CACHE = SemanticCache(rag.model)
    
    sem_hit = SEMANTIC_CACHE.get(user_message, user_role)
    # 2. INTENT & DOMAIN DETECTION
    intent = "general"
    domain = "general"
    lower_msg = user_message.lower()
    
    # Domain Mapping
    if any(k in lower_msg for k in ["data science", "ml", "pandas", "numpy", "scikit"]): domain = "data_science"
    elif any(k in lower_msg for k in ["backend", "api", "django", "fastapi", "sql"]): domain = "backend"
    elif any(k in lower_msg for k in ["resume", "cv", "portfolio"]): domain = "resume"
    elif any(k in lower_msg for k in ["interview", "prep", "mock"]): domain = "interview"

    # Intent Mapping
    if any(k in lower_msg for k in ["learn", "roadmap", "how to", "study"]): intent = "learning"
    elif domain == "resume": intent = "resume"
    elif domain == "interview": intent = "interview"

    # 3. RETRIEVAL (Increased top_k for diversity)
    semantic_results = rag.search(user_message, user_role=user_role, k=8) # Fetch more for filtering
    if not semantic_results:
        return "I'm sorry, I don't have enough information to answer that based on your current access level."

    # 4. DOMAIN FILTERING
    filtered_results = [res for res in semantic_results if res.get('domain') == domain or res.get('domain') == 'general']
    if len(filtered_results) < 2:
        filtered_results = semantic_results[:3] # Fallback to top-k if filter too restrictive

    # 5. LLM GENERATION (Deduplicated context)
    unique_texts = []
    seen = set()
    sources = set()
    for res in filtered_results:
        # Clean technical tags like [Career Guide] before sending to LLM
        clean_text = res['text'].replace("[Career Guide]", "").strip()
        if clean_text not in seen:
            unique_texts.append(clean_text)
            seen.add(clean_text)
            sources.add(res['type'])
    
    context = "\n\n".join(unique_texts)
    history = session.get('chat_history', [])
    
    # ALWAYS use LLM with Human-Centric Persona
    ai_answer = get_llm_generation(user_message, context, history, intent=intent)
    
    if ai_answer is None or len(ai_answer.strip()) == 0:
        # Warm, encouraging fallback instead of robotic list
        tips = "\n".join([f"• {t[:120]}..." for t in unique_texts[:3]])
        ai_answer = f"I've put together some key strategies for your {intent} query:\n\n{tips}\n\nFocus on applying these steps one by one, and you'll see great progress!"

    # 6. OBSERVABILITY & FINAL CLEANUP
    latency = time.time() - start_time
    
    # POST-PROCESSING: Remove any accidental system leaks
    final_response = ai_answer.replace("Retrieval Result:", "").replace("Sources:", "").strip()
    
    log_event({
        "query": user_message, "type": "rag_query", "q_type": q_type, "latency": latency,
        "sources": list(sources), "role": user_role
    })

    # 6. MEMORY & CACHE UPDATE
    history.append({"user": user_message, "ai": final_response})
    session['chat_history'] = history[-5:]
    QUERY_CACHE[user_message] = final_response
    SEMANTIC_CACHE.add(user_message, final_response, user_role)
    
    return final_response