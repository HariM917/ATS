"""
FlowATS RAG Chatbot v3.0 — Production Career Intelligence Engine
=================================================================
Pipeline: Query → Preprocess → Fast-Path Check → Cache → Retrieval → Rerank → LLM → Response

Changes from v2:
  - Replaced broken SemanticCache (was making API calls for cache lookups) with fast fuzzy cache (<1ms)
  - Added query preprocessing (normalization, abbreviation expansion)
  - Added FAISS relevance threshold (filters junk results)
  - Fixed domain+intent conflict (tag-based scoring instead of exclusive filtering)
  - Upgraded LLM prompt with grounding, history, and structured output
  - Expanded knowledge base from 16 → 65+ items
  - Added fast path for greetings/navigation (responds in <50ms)
  - Replaced all print() with proper logging
"""

import os
import sys
import numpy as np
import faiss
import time
import json
import re
import logging
from huggingface_hub import InferenceClient
from flask import session
import db_manager
from dotenv import load_dotenv
from rapidfuzz import fuzz

# --- Encoding Fix (Windows) ---
for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, 'reconfigure') and stream.encoding != 'utf-8':
        try:
            stream.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass

logger = logging.getLogger(__name__)

# --- Environment ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
env_path = os.path.join(BASE_DIR, '.env')
load_dotenv(env_path)
HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("HF_API_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN")

if HF_TOKEN:
    logger.info(f"[RAG] HF_TOKEN loaded (ends ...{HF_TOKEN[-4:]})")
else:
    logger.error("[RAG] HF_TOKEN NOT FOUND — LLM features will be disabled")

# --- HuggingFace Clients ---
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
LLM_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"

hf_client = InferenceClient(api_key=HF_TOKEN) if HF_TOKEN else None

llm_client = InferenceClient(
    model=LLM_MODEL,
    token=HF_TOKEN,
    timeout=120
) if HF_TOKEN else None

# --- Observability ---
LOG_FILE = os.path.join(BASE_DIR, "rag_observability.log")

def log_event(event_data):
    """Append structured event to observability log."""
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                **event_data
            }, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.warning(f"[LOG] Write failed: {e}")


# ============================================
# 1. EXPANDED KNOWLEDGE BASE (65+ items)
# ============================================
KNOWLEDGE_BASE = {
    # --- Resume ---
    "resume_structure": {
        "domain": "resume",
        "tags": ["resume", "format", "structure", "ats"],
        "items": [
            "Use a clean, reverse-chronological format. Sections: Header, Summary, Skills, Experience, Education, Projects.",
            "Keep it to 1 page (unless 10+ years exp). Use standard fonts (Arial, Calibri) size 10-12. Save as PDF.",
            "Avoid photos, charts, or skill bars. ATS scanners cannot read them properly.",
            "Place your most relevant experience and skills at the top of your resume — recruiters spend only 6-7 seconds on an initial scan.",
            "Use a professional email address. Include LinkedIn URL and GitHub/portfolio link if applicable."
        ]
    },
    "resume_content": {
        "domain": "resume",
        "tags": ["resume", "bullets", "content", "writing"],
        "items": [
            "The XYZ Formula: Accomplished [X] as measured by [Y], by doing [Z]. Example: 'Reduced API latency by 40% by implementing Redis caching layer.'",
            "Start every bullet with a power verb: Engineered, Spearheaded, Optimized, Orchestrated, Automated, Designed.",
            "Tailor your resume to the Job Description (JD) keywords. Use the exact same terminology.",
            "Quantify results wherever possible: percentages, revenue impact, user counts, time saved.",
            "Include 3-5 bullet points per role, focusing on achievements not responsibilities.",
            "Remove outdated skills (jQuery, Flash) unless specifically requested in the JD."
        ]
    },
    "resume_mistakes": {
        "domain": "resume",
        "tags": ["resume", "mistakes", "tips"],
        "items": [
            "Common resume mistakes: typos, generic objective statements, including 'References available upon request', using personal pronouns (I, me, my).",
            "Don't list every technology you've ever used — curate a relevant skills section matching the target role.",
            "Avoid using tables or multi-column layouts — most ATS parsers break on complex formatting."
        ]
    },

    # --- Interview ---
    "interview_behavioral": {
        "domain": "interview",
        "tags": ["interview", "behavioral", "star", "soft skills"],
        "items": [
            "The STAR Method: Situation, Task, Action, Result. Focus on YOUR specific actions and measurable outcomes.",
            "Prepare stories for Leadership, Failure, Conflict Resolution, Innovation, and Working Under Pressure.",
            "For 'Tell me about yourself', use the Present-Past-Future framework: what you do now → key past achievements → why this role.",
            "Always prepare 3-5 thoughtful questions to ask the interviewer — shows genuine interest.",
            "Research the company's recent news, products, and culture before any interview."
        ]
    },
    "interview_technical": {
        "domain": "interview",
        "tags": ["interview", "technical", "coding", "dsa"],
        "items": [
            "Practice LeetCode (Easy/Medium) for DSA. Focus on Arrays, HashMaps, Trees, and Graphs.",
            "Study scalability, load balancing, and database choices (SQL vs NoSQL) for system design rounds.",
            "Document your code and write tests for take-home assignments — it shows engineering maturity.",
            "For system design: start with requirements → estimate scale → design API → choose storage → draw architecture → discuss trade-offs.",
            "Practice explaining your thought process out loud while coding — interviewers evaluate your problem-solving approach, not just the answer."
        ]
    },
    "interview_remote": {
        "domain": "interview",
        "tags": ["interview", "remote", "video"],
        "items": [
            "Test your camera, microphone, and internet connection 30 minutes before a video interview.",
            "Use a clean, professional background. Ensure good lighting on your face (window in front, not behind).",
            "Keep a notepad or document with key talking points visible on screen for reference."
        ]
    },

    # --- Data Science & ML ---
    "skills_data_science": {
        "domain": "data_science",
        "tags": ["data science", "analytics", "python", "roadmap"],
        "items": [
            "Data Science Roadmap: 1. Python (Pandas, NumPy), 2. SQL & Databases, 3. Statistics & Probability, 4. Data Visualization (Tableau/Seaborn), 5. Machine Learning (Scikit-Learn).",
            "Advanced DS: Deep Learning (PyTorch), Big Data (Spark), Cloud Deployment (AWS SageMaker / GCP Vertex AI).",
            "Build a portfolio with 3-5 end-to-end projects: data collection → EDA → modeling → deployment → documentation.",
            "Key DS tools: Jupyter Notebooks, Git, Docker, MLflow for experiment tracking, Streamlit for demos."
        ]
    },
    "skills_ml": {
        "domain": "data_science",
        "tags": ["machine learning", "ml", "deep learning", "ai", "roadmap"],
        "items": [
            "ML Roadmap: 1. Python Fundamentals, 2. Linear Algebra & Calculus, 3. NumPy/Pandas/Matplotlib, 4. Scikit-Learn (Regression/Classification/Clustering), 5. TensorFlow or PyTorch, 6. Neural Networks & Deep Learning, 7. MLOps (Docker, MLflow, CI/CD).",
            "Focus on: Feature Engineering, Model Validation (cross-validation), Hyperparameter Tuning (Optuna/GridSearch), and Production Deployment.",
            "Understand the bias-variance tradeoff, overfitting vs underfitting, and how to use regularization techniques.",
            "For NLP roles: learn Transformers, HuggingFace, BERT/GPT architecture, text preprocessing, and embeddings."
        ]
    },

    # --- Backend ---
    "skills_backend": {
        "domain": "backend",
        "tags": ["backend", "api", "server", "roadmap"],
        "items": [
            "Backend Roadmap: 1. Language (Python/Node/Java/Go), 2. Web Frameworks (FastAPI/Express/Spring), 3. Relational DBs (PostgreSQL), 4. NoSQL (MongoDB/Redis), 5. APIs (REST/GraphQL), 6. Caching & Message Queues (Redis/RabbitMQ), 7. CI/CD & Cloud (AWS/GCP/Azure).",
            "Learn to design RESTful APIs: proper HTTP methods, status codes, pagination, versioning, and error handling.",
            "Understand database indexing, query optimization, connection pooling, and ORM vs raw SQL tradeoffs.",
            "Practice writing unit tests (pytest/Jest) and integration tests. Aim for 80%+ code coverage in production."
        ]
    },

    # --- Frontend ---
    "skills_frontend": {
        "domain": "frontend",
        "tags": ["frontend", "react", "javascript", "css", "roadmap"],
        "items": [
            "Frontend Roadmap: 1. HTML5/CSS3/JS Fundamentals, 2. React or Vue, 3. TypeScript, 4. State Management (Zustand/Redux), 5. Testing (Vitest/Cypress), 6. Build Tools (Vite/Webpack), 7. Performance Optimization.",
            "Master CSS: Flexbox, Grid, responsive design, media queries, and modern techniques like CSS custom properties.",
            "Learn accessibility (a11y): semantic HTML, ARIA attributes, keyboard navigation, color contrast ratios.",
            "Build projects that showcase: API integration, form handling, authentication flows, and responsive layouts."
        ]
    },

    # --- DevOps & Cloud ---
    "skills_devops": {
        "domain": "devops",
        "tags": ["devops", "cloud", "docker", "kubernetes", "ci/cd", "roadmap"],
        "items": [
            "DevOps Roadmap: 1. Linux & Bash, 2. Git & GitHub Actions, 3. Docker & Docker Compose, 4. Kubernetes basics, 5. Cloud (AWS/GCP/Azure), 6. Terraform/IaC, 7. Monitoring (Prometheus/Grafana).",
            "Learn to write Dockerfiles, docker-compose.yml, and understand container networking and volumes.",
            "CI/CD pipelines: GitHub Actions, Jenkins, or GitLab CI. Automate testing, building, and deployment.",
            "Cloud certifications (AWS Solutions Architect, GCP Associate) significantly boost your resume for DevOps roles."
        ]
    },

    # --- Soft Skills ---
    "soft_skills": {
        "domain": "general",
        "tags": ["soft skills", "communication", "leadership", "teamwork"],
        "items": [
            "Communication is the #1 skill employers look for. Practice explaining complex technical concepts simply.",
            "Active listening: repeat back what you heard, ask clarifying questions, don't interrupt.",
            "Time management: use techniques like Pomodoro, time-blocking, or Eisenhower Matrix to prioritize work.",
            "Learn to give and receive feedback constructively. Use the SBI model: Situation, Behavior, Impact."
        ]
    },

    # --- Salary & Negotiation ---
    "salary_strategy": {
        "domain": "general",
        "tags": ["salary", "negotiation", "compensation", "offer"],
        "items": [
            "Never give the first number. Ask for the budget for the role instead: 'What is the compensation range for this position?'",
            "Research market rates on Levels.fyi, Glassdoor, Blind, and Payscale before any negotiation.",
            "Always negotiate counter-offers professionally. Base your ask on market data, not personal needs.",
            "Consider total compensation: base salary + equity/RSUs + signing bonus + benefits + WFH flexibility.",
            "If you have multiple offers, transparently communicate timelines to all companies. Never bluff."
        ]
    },

    # --- LinkedIn & Networking ---
    "linkedin_networking": {
        "domain": "general",
        "tags": ["linkedin", "networking", "job search", "personal brand"],
        "items": [
            "Optimize your LinkedIn headline: 'Role | Key Skill | Value Proposition' instead of just your job title.",
            "Write a compelling About section using first person. Tell your story: what drives you, what you've built, what you're looking for.",
            "Engage daily: comment on 3-5 posts, share insights, write 1-2 posts per week to build visibility.",
            "When reaching out to recruiters, personalize your message. Mention something specific about the company or role.",
            "Informational interviews are powerful: ask for 15-minute coffee chats, not jobs. Build relationships first."
        ]
    },

    # --- Cover Letter ---
    "cover_letter": {
        "domain": "resume",
        "tags": ["cover letter", "application", "writing"],
        "items": [
            "Cover letter structure: Hook (why this company) → Evidence (2-3 achievements matching the JD) → Close (call to action).",
            "Keep cover letters to 3-4 paragraphs, under 300 words. Hiring managers skim, not read.",
            "Customize each cover letter. Generic templates are instantly recognizable and get rejected."
        ]
    },

    # --- Career Transitions ---
    "career_transition": {
        "domain": "general",
        "tags": ["career change", "transition", "switching", "pivot"],
        "items": [
            "When switching careers: identify transferable skills, build projects in the new domain, and network with people already in that field.",
            "Bootcamps (for coding) or certifications (for cloud/data) can accelerate career transitions significantly.",
            "Frame your transition story positively: 'I chose to move into X because...' not 'I left Y because...'",
            "Consider freelancing or contract work in the new field to build real experience before a full-time switch."
        ]
    },

    # --- Freelancing ---
    "freelancing": {
        "domain": "general",
        "tags": ["freelance", "contract", "remote work", "self-employed"],
        "items": [
            "Popular freelancing platforms: Upwork, Toptal, Fiverr, and direct outreach via LinkedIn.",
            "Build a personal portfolio website showcasing your best 5-7 projects with case studies.",
            "Set your rates based on market research. Start competitive, then raise as you build reviews and reputation.",
            "Always use contracts and clear scope documents. Protect yourself with milestone-based payments."
        ]
    }
}

# ============================================
# 2. QUERY PREPROCESSING
# ============================================
ABBREVIATION_MAP = {
    "ds": "data science", "ml": "machine learning", "dl": "deep learning",
    "nlp": "natural language processing", "cv": "computer vision",
    "ai": "artificial intelligence", "fe": "frontend", "be": "backend",
    "js": "javascript", "ts": "typescript", "py": "python",
    "dsa": "data structures and algorithms", "oop": "object oriented programming",
    "sql": "structured query language", "k8s": "kubernetes",
    "tf": "tensorflow", "lc": "leetcode", "jd": "job description",
    "wfh": "work from home", "yoe": "years of experience",
    "devops": "development operations", "swe": "software engineer",
    "pm": "product manager", "ux": "user experience", "ui": "user interface",
}

def preprocess_query(query):
    """Normalize, expand abbreviations, and clean user query for better retrieval."""
    if not query:
        return ""
    q = query.strip().lower()
    # Remove excessive punctuation
    q = re.sub(r'[!?]{2,}', '?', q)
    q = re.sub(r'\.{2,}', '.', q)
    # Normalize whitespace
    q = re.sub(r'\s+', ' ', q)
    # Expand abbreviations (word-boundary aware)
    words = q.split()
    expanded = []
    for word in words:
        clean_word = re.sub(r'[^a-z0-9]', '', word)
        if clean_word in ABBREVIATION_MAP:
            expanded.append(ABBREVIATION_MAP[clean_word])
        else:
            expanded.append(word)
    return " ".join(expanded)


# ============================================
# 3. FAST CACHE (No API calls)
# ============================================
class FastCache:
    """Zero-latency response cache using exact match + fuzzy matching.
    No API calls needed — operates entirely in-memory.
    """
    def __init__(self, fuzzy_threshold=90, max_size=200):
        self.exact_cache = {}          # normalized_query → response
        self.query_list = []           # ordered list of cached queries
        self.fuzzy_threshold = fuzzy_threshold
        self.max_size = max_size

    def _normalize(self, text):
        return re.sub(r'\s+', ' ', text.strip().lower())

    def get(self, query, user_role="candidate"):
        """O(1) exact match, then O(n) fuzzy scan. No network calls."""
        norm = self._normalize(query)

        # Exact match — instant
        if norm in self.exact_cache:
            entry = self.exact_cache[norm]
            if entry['role'] == user_role or entry['role'] == 'all':
                logger.info("[CACHE] Exact hit")
                return entry['response']

        # Fuzzy match — still fast (<1ms for 200 entries)
        for cached_q in self.query_list:
            score = fuzz.ratio(norm, cached_q)
            if score >= self.fuzzy_threshold:
                entry = self.exact_cache[cached_q]
                if entry['role'] == user_role or entry['role'] == 'all':
                    logger.info(f"[CACHE] Fuzzy hit (score={score})")
                    return entry['response']

        return None

    def add(self, query, response, user_role="candidate"):
        norm = self._normalize(query)
        if norm in self.exact_cache:
            return  # Don't duplicate
        if len(self.exact_cache) >= self.max_size:
            # Evict oldest
            oldest = self.query_list.pop(0)
            self.exact_cache.pop(oldest, None)
        self.exact_cache[norm] = {
            'response': response,
            'role': user_role
        }
        self.query_list.append(norm)


# ============================================
# 4. NAVIGATION / FAST PATH RESPONSES
# ============================================
GREETING_PATTERNS = {"hello", "hi", "hey", "howdy", "hola", "sup", "yo"}
HELP_PATTERNS = {"help", "menu", "start", "options", "what can you do", "commands"}

GREETING_RESPONSE = (
    "Hello! I'm your FlowATS AI Career Coach. I can help you with:\n\n"
    "• **Resume optimization** — structure, content, ATS tips\n"
    "• **Interview preparation** — behavioral, technical, system design\n"
    "• **Career roadmaps** — Data Science, ML, Backend, Frontend, DevOps\n"
    "• **Salary negotiation** — research, strategy, counter-offers\n"
    "• **LinkedIn & networking** — profile optimization, outreach\n"
    "• **Job search strategy** — cover letters, career transitions\n\n"
    "What would you like to explore?"
)

def check_fast_path(query):
    """Returns an instant response for greetings/help, or None to continue pipeline."""
    words = set(query.lower().split())
    # Pure greeting (1-3 words)
    if len(words) <= 3 and words.intersection(GREETING_PATTERNS):
        return GREETING_RESPONSE
    if words.intersection(HELP_PATTERNS) and len(words) <= 5:
        return GREETING_RESPONSE
    return None


# ============================================
# 5. INTENT & DOMAIN DETECTION (Improved)
# ============================================
DOMAIN_KEYWORDS = {
    "data_science": ["data science", "ml", "machine learning", "pandas", "numpy", "scikit", "tensorflow", "pytorch", "deep learning", "analytics", "statistics"],
    "backend": ["backend", "api", "django", "fastapi", "flask", "express", "spring", "server", "database", "sql", "rest", "graphql"],
    "frontend": ["frontend", "react", "vue", "angular", "css", "html", "javascript", "typescript", "ui", "ux", "responsive"],
    "devops": ["devops", "docker", "kubernetes", "ci/cd", "aws", "gcp", "azure", "cloud", "terraform", "jenkins", "deployment"],
    "resume": ["resume", "cv", "portfolio", "cover letter", "application"],
    "interview": ["interview", "prep", "mock", "behavioral", "technical", "coding round", "system design"],
    "hr": ["candidate", "applicant", "hiring", "recruitment", "shortlist"],
}

INTENT_KEYWORDS = {
    "learning": ["learn", "roadmap", "how to", "study", "path", "guide", "become", "start", "beginner", "career path"],
    "resume": ["resume", "cv", "portfolio", "bullet", "format"],
    "interview": ["interview", "prepare", "mock", "behavioral", "technical"],
    "salary": ["salary", "negotiate", "compensation", "offer", "pay", "raise"],
    "networking": ["linkedin", "network", "connect", "outreach"],
}

def detect_intent_and_domain(query):
    """Returns (intent, domain, matched_tags) for better retrieval."""
    lower = query.lower()
    
    # Detect domain
    domain = "general"
    domain_score = 0
    for d, keywords in DOMAIN_KEYWORDS.items():
        matches = sum(1 for k in keywords if k in lower)
        if matches > domain_score:
            domain = d
            domain_score = matches

    # Detect intent
    intent = "general"
    intent_score = 0
    for i, keywords in INTENT_KEYWORDS.items():
        matches = sum(1 for k in keywords if k in lower)
        if matches > intent_score:
            intent = i
            intent_score = matches

    # Build combined tag set for retrieval boosting
    matched_tags = set()
    matched_tags.add(domain)
    matched_tags.add(intent)
    for word in lower.split():
        if len(word) > 3:  # skip short words
            matched_tags.add(word)

    return intent, domain, matched_tags


# ============================================
# 6. RAG ENGINE (Improved)
# ============================================
class RAGManager:
    def __init__(self):
        logger.info("=" * 50)
        logger.info("[RAG] SYSTEM STARTUP: HF Inference Mode")
        logger.info("=" * 50)
        self.documents = []
        self.index = None
        self.last_rebuild = 0
        self.refresh_interval = 600  # 10 minutes
        self.rebuild_index()

    def rebuild_index(self, force=False):
        """Builds FAISS index from knowledge base + live DB data."""
        current_time = time.time()
        if not force and self.index is not None and (current_time - self.last_rebuild < self.refresh_interval):
            return

        logger.info("[RAG] Rebuilding index...")
        new_docs = []

        # 1. Static Knowledge Base
        for category, config in KNOWLEDGE_BASE.items():
            tags = set(config.get("tags", []))
            for item in config["items"]:
                new_docs.append({
                    "text": item,
                    "category": category,
                    "type": "Career Guide",
                    "access": "all",
                    "domain": config["domain"],
                    "tags": tags
                })

        # 2. Dynamic Data from DB
        try:
            conn = db_manager.get_db_connection()
            jobs = conn.execute('SELECT title, description, required_skills FROM jobs').fetchall()
            for job in jobs:
                new_docs.append({
                    "text": f"Job Posting: {job['title']}. Description: {job['description']}. Required Skills: {job['required_skills']}",
                    "category": "ats_jobs",
                    "type": "Job Listing",
                    "access": "all",
                    "domain": "general",
                    "tags": {"job", "posting", "hiring"}
                })

            apps = conn.execute('SELECT candidate_name, score, status FROM applications ORDER BY score DESC LIMIT 50').fetchall()
            for app in apps:
                score_val = app['score'] if app['score'] is not None else 0
                new_docs.append({
                    "text": f"Candidate {app['candidate_name']} has an AI match score of {int(score_val*100)}% and is currently {app['status']}.",
                    "category": "ats_candidates",
                    "type": "Candidate Profile",
                    "access": "hr",
                    "domain": "hr",
                    "tags": {"candidate", "applicant", "score"}
                })
            conn.close()
        except Exception as e:
            logger.error(f"[RAG] DB indexing failed: {e}")

        # 3. Embed & Index (only if content changed)
        if len(new_docs) != len(self.documents) or self.index is None or force:
            self.documents = new_docs
            texts = [doc["text"] for doc in self.documents]

            if not hf_client or not texts:
                logger.error("[RAG] Skipping embedding phase (no token or no docs)")
                return

            logger.info(f"[RAG] Embedding {len(texts)} documents via HF API...")
            try:
                # Batch embed in chunks of 50 to prevent timeouts
                all_embeddings = []
                batch_size = 50
                for i in range(0, len(texts), batch_size):
                    batch = texts[i:i+batch_size]
                    emb = hf_client.feature_extraction(batch, model=EMBEDDING_MODEL)
                    all_embeddings.extend(emb)

                embeddings = np.array(all_embeddings).astype('float32')
                dim = embeddings.shape[1]
                self.index = faiss.IndexFlatL2(dim)
                self.index.add(embeddings)
                self.last_rebuild = current_time
                logger.info(f"[RAG] Index ready. {len(self.documents)} docs, {dim}D embeddings")
            except Exception as e:
                logger.error(f"[RAG] Embedding failed: {e}")

    def search(self, query, user_role="candidate", matched_tags=None, k=5):
        """Semantic search with relevance threshold and tag-based reranking."""
        # Don't call rebuild_index here — it's called in get_response once
        if self.index is None or not hf_client:
            return []

        try:
            q_emb = hf_client.feature_extraction([query], model=EMBEDDING_MODEL)
            q_emb = np.array(q_emb).astype('float32')
        except Exception as e:
            logger.error(f"[RAG] Query embedding failed: {e}")
            return []

        try:
            D, I = self.index.search(q_emb, k * 4)  # Over-retrieve for reranking
        except Exception as e:
            logger.error(f"[RAG] FAISS search failed: {e}")
            return []

        RELEVANCE_THRESHOLD = 1.5  # L2 distance cutoff
        results = []

        for dist, idx in zip(D[0], I[0]):
            if idx == -1:
                continue
            # Skip irrelevant results
            if dist > RELEVANCE_THRESHOLD:
                continue

            doc = self.documents[idx]

            # RBAC: strict access control
            if doc['access'] == 'hr' and user_role != 'hr':
                continue

            # Tag-based boost (replaces broken domain-exclusive filtering)
            tag_bonus = 0.0
            if matched_tags and doc.get('tags'):
                overlap = len(matched_tags.intersection(doc['tags']))
                tag_bonus = min(0.3, overlap * 0.1)  # Max 0.3 bonus

            # Keyword overlap bonus (lightweight)
            query_words = set(query.lower().split())
            doc_words = set(doc['text'].lower().split())
            word_overlap = len(query_words.intersection(doc_words))
            keyword_bonus = min(0.2, (word_overlap / max(1, len(query_words))) * 0.2)

            final_score = dist - tag_bonus - keyword_bonus
            results.append((final_score, doc))

        results.sort(key=lambda x: x[0])
        return [r[1] for r in results[:k]]


# ============================================
# 7. LLM GENERATION (Improved Prompt)
# ============================================
SYSTEM_PROMPT = """You are the FlowATS AI Career Coach — an expert career advisor.

CRITICAL RULES:
1. Answer ONLY using the provided context below. Do NOT make up facts.
2. If the context doesn't contain enough information, say "Based on my current knowledge..." and give general career advice.
3. Structure your response with bullet points or numbered lists when giving multiple tips.
4. Be concise but thorough. Aim for 3-5 key points.
5. Use a professional yet encouraging tone.
6. If the user asks about a specific technology or role, focus your answer on that area.
7. End with a follow-up question or actionable next step."""

def build_llm_messages(query, context, history=None):
    """Constructs the message array for the LLM with grounding context and history."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Inject conversation history (last 3 turns for context window efficiency)
    if history:
        recent = history[-3:] if len(history) > 3 else history
        for turn in recent:
            if isinstance(turn, dict):
                user_text = turn.get('user', '')
                ai_text = turn.get('ai', '')
                if user_text:
                    messages.append({"role": "user", "content": user_text})
                if ai_text:
                    messages.append({"role": "assistant", "content": ai_text})

    # Current query with grounding context
    user_content = f"User Question: {query}"
    if context and context.strip():
        user_content += f"\n\n--- Retrieved Knowledge ---\n{context}\n--- End Knowledge ---"
    
    messages.append({"role": "user", "content": user_content})
    return messages


def get_llm_generation(query, context, history=None, intent="general"):
    """Calls the LLM with grounding context and conversation history."""
    if not llm_client:
        logger.warning("[LLM] No client available (HF_TOKEN missing)")
        return None

    try:
        messages = build_llm_messages(query, context, history)
        logger.info(f"[LLM] Calling {LLM_MODEL} ({len(messages)} messages)...")

        response = llm_client.chat_completion(
            messages=messages,
            max_tokens=600,
            temperature=0.4,  # Lower for more factual responses
        )

        ai_text = response.choices[0].message.content

        if isinstance(ai_text, str) and len(ai_text.strip()) > 10:
            logger.info(f"[LLM] Success ({len(ai_text)} chars)")
            return ai_text.strip()

        logger.warning("[LLM] Response too short or empty")
        return None

    except Exception as e:
        logger.error(f"[LLM] Generation failed: {e}")
        return None


# ============================================
# 8. FALLBACK RESPONSE
# ============================================
def fallback_response(context, intent="general"):
    """Synthesizes an answer from retrieved context when LLM fails.
    If context is empty, pulls directly from the knowledge base using the intent.
    """
    intent_labels = {
        "learning": "mastering new skills",
        "resume": "crafting a standout resume",
        "interview": "acing your next interview",
        "salary": "salary negotiation",
        "networking": "professional networking",
        "general": "your career advancement"
    }
    label = intent_labels.get(intent, "your career advancement")

    # If no RAG context available, pull directly from knowledge base
    if not context or not context.strip():
        # Map intent → knowledge base categories
        intent_to_categories = {
            "resume": ["resume_structure", "resume_content", "resume_mistakes", "cover_letter"],
            "interview": ["interview_behavioral", "interview_technical", "interview_remote"],
            "learning": ["skills_data_science", "skills_ml", "skills_backend", "skills_frontend", "skills_devops"],
            "salary": ["salary_strategy"],
            "networking": ["linkedin_networking"],
            "general": ["resume_content", "interview_behavioral", "salary_strategy", "linkedin_networking"],
        }
        categories = intent_to_categories.get(intent, intent_to_categories["general"])
        
        kb_items = []
        for cat in categories:
            if cat in KNOWLEDGE_BASE:
                kb_items.extend(KNOWLEDGE_BASE[cat]["items"])
        
        if kb_items:
            # Pick up to 5 relevant items
            selected = kb_items[:5]
            body = "\n".join([f"• {item.rstrip('.')}." for item in selected])
            return (
                f"Here are key strategies for {label}:\n\n"
                f"{body}\n\n"
                f"Would you like more details on any of these, or a different topic?"
            )
        return GREETING_RESPONSE

    # Extract clean sentences from RAG context
    sentences = []
    for line in context.split("\n"):
        for part in line.split("."):
            clean = part.strip()
            if len(clean) > 25:
                sentences.append(clean)

    top = sentences[:5]
    if not top:
        return fallback_response("", intent)  # Recurse to KB lookup

    body = "\n".join([f"• {s.rstrip('.')}." for s in top])

    return (
        f"Here are key strategies for {label}:\n\n"
        f"{body}\n\n"
        f"Would you like more details on any of these, or a different topic?"
    )


# ============================================
# MAIN PIPELINE
# ============================================
# Lazy-initialized singletons
rag = None
response_cache = None


def get_response(user_message):
    """
    Production RAG Pipeline:
    Query → Preprocess → Fast-Path → Cache → Retrieve → Rerank → LLM → Cache → Response
    """
    global rag, response_cache
    start_time = time.time()

    user_role = session.get("role", "candidate")
    user_email = session.get("email", "anonymous")

    if not user_message or not user_message.strip():
        return "I'm ready to help. What's on your mind?"

    # Step 1: Preprocess
    processed_query = preprocess_query(user_message)
    logger.info(f"[PIPELINE] Query: '{processed_query[:80]}' | Role: {user_role}")

    # Step 2: Fast Path (greetings/help → instant response, no API calls)
    fast = check_fast_path(processed_query)
    if fast:
        latency = time.time() - start_time
        logger.info(f"[PIPELINE] Fast path response ({latency:.3f}s)")
        log_event({"query": user_message, "type": "fast_path", "latency": latency})
        return fast

    # Step 3: Initialize singletons
    if rag is None:
        rag = RAGManager()
        response_cache = FastCache()

    # Step 4: Check Cache (zero-latency, no API calls)
    cached = response_cache.get(processed_query, user_role)
    if cached:
        latency = time.time() - start_time
        log_event({"query": user_message, "type": "cache_hit", "latency": latency, "email": user_email})
        return cached

    try:
        # Step 5: Intent & Domain Detection
        intent, domain, matched_tags = detect_intent_and_domain(processed_query)
        logger.info(f"[PIPELINE] Intent={intent}, Domain={domain}, Tags={matched_tags}")

        # Step 6: Ensure index is fresh
        rag.rebuild_index()

        # Step 7: Semantic Retrieval with tag-based reranking
        results = rag.search(processed_query, user_role=user_role, matched_tags=matched_tags, k=6)
        logger.info(f"[PIPELINE] Retrieved {len(results)} documents")

        # Step 8: Build deduplicated context
        unique_texts = []
        seen = set()
        sources = set()
        for res in results:
            text = res['text'].strip()
            if text not in seen:
                unique_texts.append(text)
                seen.add(text)
                sources.add(res.get('type', 'Unknown'))

        context = "\n\n".join(unique_texts)
        logger.info(f"[PIPELINE] Context: {len(unique_texts)} chunks, {len(context)} chars")

        # Step 9: Get conversation history
        history = session.get('chat_history', [])
        if not history and user_email != "anonymous":
            history = db_manager.get_chat_history(user_email, limit=5)

        # Step 10: LLM Generation
        ai_answer = get_llm_generation(processed_query, context, history=history, intent=intent)

        if ai_answer and len(ai_answer.strip()) > 10:
            final_response = ai_answer.strip()
        else:
            logger.info("[PIPELINE] LLM failed, using fallback")
            final_response = fallback_response(context, intent)

        # Step 11: Observability
        latency = time.time() - start_time
        logger.info(f"[PIPELINE] Complete ({latency:.2f}s, {len(final_response)} chars)")
        log_event({
            "query": user_message, "type": "rag_query", "intent": intent,
            "domain": domain, "latency": latency,
            "sources": list(sources), "role": user_role, "email": user_email
        })

        # Step 12: Memory & Cache Update
        history.append({"user": user_message, "ai": final_response})
        session['chat_history'] = history[-5:]

        if user_email != "anonymous":
            db_manager.save_chat_message(user_email, user_role, user_message, final_response)

        response_cache.add(processed_query, final_response, user_role)

        return final_response

    except Exception as e:
        logger.error(f"[PIPELINE ERROR] {e}")
        log_event({"type": "pipeline_error", "error": str(e), "query": user_message[:50]})
        return fallback_response("", "general")