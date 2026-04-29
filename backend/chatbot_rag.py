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
KNOWLEDGE_BASE = {
    "resume_structure": [
        "Use a clean, reverse-chronological format. Sections: Header, Summary, Skills, Experience, Education, Projects.",
        "Keep it to 1 page (unless 10+ years exp). Use standard fonts (Arial, Calibri) size 10-12. Save as PDF.",
        "Avoid photos, charts, or skill bars. ATS scanners cannot read them properly."
    ],
    "resume_content": [
        "The XYZ Formula: Accomplished [X] as measured by [Y], by doing [Z].",
        "Start every bullet with a power verb: Engineered, Spearheaded, Optimized, Orchestrated.",
        "Tailor your resume to the Job Description (JD) keywords."
    ],
    "resume_gaps": [
        "Be honest but brief. Focus on professional development (courses, freelancing) done during the gap.",
        "Consider a 'Functional' resume format if you have large gaps or are switching careers."
    ],
    "interview_behavioral": [
        "The STAR Method: Situation, Task, Action, Result. Focus on your specific actions.",
        "Prepare stories for Leadership, Failure, Conflict Resolution, and Innovation."
    ],
    "interview_technical": [
        "Practice LeetCode (Easy/Medium) for DSA. Focus on Arrays, HashMaps, and Trees.",
        "Study scalability, load balancing, and database choices (SQL vs NoSQL) for senior roles.",
        "Document your code and write tests for take-home assignments."
    ],
    "salary_strategy": [
        "Never give the first number. Ask for the budget for the role instead.",
        "Research market rates on Levels.fyi, Glassdoor, and Blind.",
        "Always negotiate counter-offers professionally based on research."
    ],
    "skills_backend": [
        "Backend Roadmap: Python (Django/FastAPI) or Node.js. PostgreSQL/MongoDB. REST/GraphQL. Docker/Kubernetes.",
        "Cloud basics: AWS (EC2, S3, Lambda) or Azure."
    ],
    "skills_frontend": [
        "Frontend Roadmap: HTML/CSS/JS, React/Vue/Angular, Redux/Context, Tailwind CSS.",
        "Build projects like E-commerce sites, Dashboards, or Real-time apps."
    ]
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
        print("[RAG] Initializing Semantic Search Index...")
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
        
        for category, items in KNOWLEDGE_BASE.items():
            for item in items:
                self.documents.append({
                    "text": item, "category": category, "type": "Career Guide", "access": "all"
                })
        
        try:
            conn = db_manager.get_db_connection()
            jobs = conn.execute('SELECT title, description, skills FROM jobs').fetchall()
            for job in jobs:
                self.documents.append({
                    "text": f"Job Posting: {job['title']}. Description: {job['description']}. Required Skills: {job['skills']}",
                    "category": "ats_jobs", "type": "Job Listing", "access": "all"
                })
            
            apps = conn.execute('SELECT candidate_name, score, status FROM applications ORDER BY score DESC LIMIT 50').fetchall()
            for app in apps:
                self.documents.append({
                    "text": f"Candidate {app['candidate_name']} has an AI match score of {int(app['score']*100)}% and is currently {app['status']}.",
                    "category": "ats_candidates", "type": "Candidate Profile", "access": "hr"
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

def get_llm_generation(query, context, history, reasoning=True):
    """Synthesizes an answer using HuggingFace LLM with Reasoning Step"""
    if not HF_TOKEN or not context: return None
    history_str = "\n".join([f"User: {h['user']}\nAI: {h['ai']}" for h in history[-2:]])
    
    reasoning_prompt = "First, analyze the context to see if it contains the answer. Then, provide a concise response." if reasoning else ""
    
    prompt = f"""<|system|>
You are the TalentFlow AI Career Coach, a world-class professional advisor.
RULES:
1. Provide a clear, structured, and helpful answer using ONLY the provided CONTEXT.
2. {reasoning_prompt}
3. Use bullet points or numbered lists for actionable advice.
4. If the answer is not in the context, say: "I'm sorry, I don't have enough specific data in my system to answer that. However, I can help with resume tips, interview prep, or career paths."
5. Be professional, encouraging, and concise.
6. DO NOT mention "retrieval", "context", or internal system terms.

CONTEXT:
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
        return None

def get_response(user_message):
    """Optimized & Observable RAG Pipeline"""
    global rag, SEMANTIC_CACHE
    start_time = time.time()
    user_role = session.get("role", "candidate")
    
    if not user_message: return "I'm ready to help. What's on your mind?"
    
    # 1. QUERY CLASSIFICATION
    q_type = classify_query(user_message)
    if q_type == "navigation":
        return "I'm the TalentFlow AI. I can help with resume tips, interview prep, or exploring job matches. What would you like to do?"

    # 2. LATENCY OPTIMIZATION: CACHE CHECK
    if user_message in QUERY_CACHE:
        log_event({"query": user_message, "type": "exact_cache_hit", "latency": time.time() - start_time})
        return QUERY_CACHE[user_message]
    
    if rag is None: 
        rag = RAGManager()
        SEMANTIC_CACHE = SemanticCache(rag.model)
    
    sem_hit = SEMANTIC_CACHE.get(user_message, user_role)
    if sem_hit:
        log_event({"query": user_message, "type": "semantic_cache_hit", "latency": time.time() - start_time})
        return sem_hit

    # 3. RETRIEVAL
    semantic_results = rag.search(user_message, user_role=user_role)
    if not semantic_results:
        return "I'm sorry, I don't have enough information to answer that based on your current access level."

    # 4. LLM GENERATION
    context_parts = []
    sources = set()
    for res in semantic_results:
        # Provide clean text to LLM without the internal metadata tags
        context_parts.append(res['text'])
        sources.add(res['type'])
    context = "\n".join(context_parts)

    history = session.get('chat_history', [])
    
    # ALWAYS use LLM for synthesis to ensure a professional, human-like voice
    ai_answer = get_llm_generation(user_message, context, history)
    
    if ai_answer is None or len(ai_answer.strip()) == 0:
        # Professional fallback if LLM is busy or fails
        ai_answer = "I've synthesized the most relevant tips for you based on our career database:\n\n" + \
                    "\n".join([f"• {c[:150]}..." for c in context_parts[:3]])

    # 5. OBSERVABILITY & FINAL RESPONSE
    latency = time.time() - start_time
    
    # Professional source attribution
    source_footer = "\n\n📚 **Sources:** " + ", ".join(sources) if sources else ""
    final_response = f"{ai_answer}{source_footer}"
    
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