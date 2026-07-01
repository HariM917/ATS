"""
FlowATS AI Engine — Production v3.0
Multi-layer resume parsing, 800+ skill taxonomy, weighted ATS scoring,
semantic role prediction, and production validation guards.
"""
import os
import re
import math
import time
import logging
import gc
import sys
import datetime
import docx2txt
import numpy as np
import pickle
from pathlib import Path
from dotenv import load_dotenv
from rapidfuzz import fuzz, process
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.base import BaseEstimator, TransformerMixin

load_dotenv()

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)

VERSION = "Prod-v3.0.0"
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# ============================================
# Part 4A: Resume Parsing Constants
# ============================================
MIN_RESUME_CHARS = 200
MIN_WORD_COUNT = 30

# ============================================
# Skill Normalization & Synonyms
# ============================================
SYNONYM_MAP = {
    "ml": "Machine Learning", "dl": "Deep Learning",
    "nlp": "Natural Language Processing", "tf": "TensorFlow",
    "k8s": "Kubernetes", "js": "JavaScript", "ts": "TypeScript",
    "aws": "Amazon Web Services", "gcp": "Google Cloud Platform",
    "cv": "Computer Vision", "rl": "Reinforcement Learning",
    "genai": "Generative AI", "llm": "Large Language Models",
    "sklearn": "Scikit-Learn", "postgres": "PostgreSQL",
    "mongo": "MongoDB", "reactjs": "React", "vuejs": "Vue",
    "nextjs": "Next.js", "expressjs": "Express",
    "fastapi": "FastAPI", "ci/cd": "CI/CD",
    "oop": "Object Oriented Programming",
    "dsa": "Data Structures and Algorithms",
}

# ============================================
# Part 4: Enterprise Skill Taxonomy (800+)
# ============================================
try:
    from ats_skills_dataset import ATS_SKILLS_DATA, get_all_unique_skills
    _dataset_skills = get_all_unique_skills()
    logging.info(f">>> INFRA: Loaded {len(_dataset_skills)} skills from ats_skills_dataset.")
except ImportError:
    _dataset_skills = []
    logging.warning(">>> INFRA: ats_skills_dataset not available, using built-in taxonomy.")

# Built-in comprehensive skill list (merged with dataset)
BUILTIN_SKILLS = [
    # AI/ML
    "Python", "TensorFlow", "PyTorch", "Keras", "Scikit-Learn", "XGBoost", "LightGBM",
    "CatBoost", "OpenCV", "YOLO", "Stable Diffusion", "LangChain", "FAISS", "MLflow",
    "Weights & Biases", "DVC", "Feature Engineering", "Model Evaluation",
    "Hyperparameter Tuning", "Transfer Learning", "GANs", "Transformers", "BERT", "GPT",
    "Attention Mechanism", "RAG", "Vector Databases", "Prompt Engineering", "Fine-Tuning",
    "RLHF", "MLOps", "Deep Learning", "Machine Learning", "Neural Networks",
    "Computer Vision", "Natural Language Processing", "Reinforcement Learning",
    "Generative AI", "Large Language Models", "Hugging Face", "NumPy", "SciPy",
    "Pandas", "Matplotlib", "Seaborn", "Plotly", "NLTK", "SpaCy", "Gensim",
    # Data Science
    "Statistics", "Hypothesis Testing", "A/B Testing", "Bayesian Inference",
    "Time Series Analysis", "Regression", "Classification", "Clustering", "PCA",
    "t-SNE", "Random Forest", "Gradient Boosting", "Ensemble Methods", "Data Mining",
    "Predictive Modeling", "Feature Selection", "Data Visualization", "Jupyter",
    "R", "SAS", "SPSS", "MATLAB",
    # Data Analytics
    "SQL", "Excel", "Power BI", "Tableau", "Looker", "Google Analytics",
    "Mixpanel", "Amplitude", "dbt", "Data Modeling", "ETL", "Data Warehousing",
    "Redshift", "BigQuery", "Snowflake", "Data Pipeline", "Data Lake",
    "Business Intelligence", "KPI", "Metrics", "Dashboards", "Reporting",
    # Software Engineering
    "Java", "C++", "C#", "Go", "Rust", "Scala", "Perl", "Ruby", "PHP",
    "Haskell", "Elixir", "Clojure", "Lua", "Shell Scripting", "Bash",
    "Design Patterns", "SOLID", "Clean Code", "TDD", "BDD", "DDD",
    "Microservices", "System Design", "Distributed Systems", "Concurrency",
    "Multithreading", "Data Structures", "Algorithms", "OOP", "Functional Programming",
    "REST", "GraphQL", "gRPC", "WebSockets", "Message Queues",
    "API Design", "API Gateway", "OAuth", "JWT",
    # Frontend
    "React", "Vue", "Angular", "Svelte", "Next.js", "Nuxt.js", "Gatsby",
    "TypeScript", "JavaScript", "HTML", "HTML5", "CSS", "CSS3", "Sass", "Less",
    "Tailwind CSS", "Material UI", "Chakra UI", "Ant Design", "Bootstrap",
    "Webpack", "Vite", "Rollup", "Parcel", "Babel",
    "SSR", "SSG", "PWA", "Web Components", "Web Accessibility",
    "Redux", "MobX", "Zustand", "Recoil", "Context API",
    "Responsive Design", "Cross-Browser Compatibility", "SEO",
    "Storybook", "Figma", "Sketch", "Adobe XD",
    # Backend
    "Node.js", "Django", "Flask", "FastAPI", "Spring Boot", "Spring",
    "Express", "NestJS", "Rails", "Laravel", "ASP.NET",
    "Redis", "PostgreSQL", "MongoDB", "MySQL", "SQLite",
    "Cassandra", "DynamoDB", "Elasticsearch", "Neo4j", "InfluxDB",
    "RabbitMQ", "Apache Kafka", "ActiveMQ", "Celery",
    "ORM", "SQLAlchemy", "Prisma", "TypeORM", "Sequelize",
    "Nginx", "Apache", "Load Balancing", "Caching",
    # Cloud
    "AWS", "Amazon Web Services", "S3", "EC2", "Lambda", "SageMaker",
    "ECS", "EKS", "RDS", "DynamoDB", "CloudFormation", "IAM",
    "VPC", "Route53", "CloudWatch", "CloudFront", "SNS", "SQS",
    "Azure", "Azure Functions", "Azure DevOps", "AKS", "Cosmos DB",
    "GCP", "Google Cloud", "Cloud Run", "Vertex AI", "Pub/Sub",
    "Firebase", "Heroku", "Vercel", "Netlify", "DigitalOcean",
    "Serverless", "IaC", "Infrastructure as Code",
    # DevOps
    "Docker", "Kubernetes", "Jenkins", "GitLab CI", "GitHub Actions",
    "CircleCI", "Travis CI", "Terraform", "Ansible", "Puppet", "Chef",
    "Prometheus", "Grafana", "Datadog", "New Relic", "ELK Stack",
    "Helm", "ArgoCD", "Istio", "Service Mesh",
    "Blue-Green Deployment", "Canary Deployment", "GitOps",
    "CI/CD", "Linux", "Unix", "Shell", "Git", "SVN",
    "Monitoring", "Logging", "Alerting",
    # Cybersecurity
    "Penetration Testing", "OWASP", "Burp Suite", "Metasploit", "Wireshark",
    "SIEM", "SOC", "ISO 27001", "SOC 2", "GDPR", "HIPAA",
    "Zero Trust", "Encryption", "PKI", "SSL/TLS",
    "Incident Response", "Digital Forensics", "Vulnerability Assessment",
    "Firewall", "IDS/IPS", "WAF", "DLP", "NIST",
    # Mobile
    "Swift", "Kotlin", "Flutter", "React Native", "SwiftUI",
    "Jetpack Compose", "Xamarin", "Ionic", "Cordova",
    "iOS", "Android", "App Store", "Google Play",
    "Push Notifications", "CoreData", "Room", "ARKit", "ARCore",
    # UI/UX
    "Wireframing", "Prototyping", "User Research", "Usability Testing",
    "Design Systems", "Information Architecture", "Interaction Design",
    "Color Theory", "Typography", "User Personas", "User Journey",
    "A/B Testing", "Heuristic Evaluation",
    # Data Engineering
    "Apache Spark", "Apache Flink", "Apache Beam", "Apache Airflow",
    "Dagster", "Prefect", "Luigi",
    "Delta Lake", "Apache Iceberg", "Apache Hudi",
    "Parquet", "Avro", "ORC", "Protobuf",
    "Data Lakehouse", "CDC", "Stream Processing", "Batch Processing",
    "Apache Hive", "Apache Pig", "Presto", "Trino",
    # QA/Testing
    "Selenium", "Cypress", "Playwright", "Puppeteer",
    "Jest", "Pytest", "JUnit", "TestNG", "Mocha", "Chai",
    "Appium", "JMeter", "Gatling", "Locust",
    "Load Testing", "API Testing", "E2E Testing",
    "BDD", "Cucumber", "Test Pyramid", "Test Automation",
    "SonarQube", "Code Coverage",
    # Blockchain/Web3
    "Solidity", "Ethereum", "Smart Contracts", "DeFi", "NFT",
    "Web3.js", "Ethers.js", "Hardhat", "Truffle", "IPFS",
    "Consensus Algorithms", "Hyperledger",
    # Soft Skills
    "Leadership", "Communication", "Problem Solving", "Critical Thinking",
    "Agile", "Scrum", "Kanban", "SAFe", "Lean",
    "Project Management", "Stakeholder Management", "Mentoring",
    "Public Speaking", "Technical Writing", "Collaboration",
    "JIRA", "Confluence", "Trello", "Asana", "Monday.com",
    ".NET", "C", "Objective-C", "Assembly",
]

SKILL_DICTIONARY = sorted(list(set(BUILTIN_SKILLS + _dataset_skills)))
logging.info(f">>> INFRA: Total skills in taxonomy: {len(SKILL_DICTIONARY)}")

# Role-skill mapping for inference
try:
    from ats_skills_dataset import ATS_SKILLS_DATA
    ROLE_SKILLS = {}
    for role, categories in ATS_SKILLS_DATA.items():
        all_role_skills = []
        for cat, skills in categories.items():
            all_role_skills.extend([s.lower() for s in skills])
        ROLE_SKILLS[role.lower()] = all_role_skills
except ImportError:
    ROLE_SKILLS = {
        "machine learning": ["python", "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy", "deep learning"],
        "data scientist": ["python", "sql", "statistics", "machine learning", "r", "pandas", "tableau"],
        "data analyst": ["sql", "excel", "tableau", "power bi", "python", "statistics"],
        "full stack": ["javascript", "react", "node.js", "html", "css", "sql", "mongodb", "typescript"],
        "frontend": ["react", "javascript", "html", "css", "typescript", "tailwind", "next.js", "vue"],
        "backend": ["node.js", "python", "java", "sql", "postgresql", "mongodb", "django", "flask"],
        "devops": ["docker", "kubernetes", "aws", "jenkins", "terraform", "ci/cd", "linux", "git"],
    }


# ============================================
# Part 6: Role Taxonomy for Semantic Prediction
# ============================================
ROLE_TAXONOMY = {
    "Machine Learning Engineer": "Builds ML models, training pipelines, feature engineering, model deployment, TensorFlow, PyTorch, scikit-learn, deep learning, neural networks",
    "Data Scientist": "Statistical analysis, hypothesis testing, data visualization, predictive modeling, R, Python, pandas, machine learning, experiment design",
    "Data Analyst": "SQL queries, dashboards, reporting, business intelligence, Excel, Tableau, Power BI, data visualization, KPIs, metrics",
    "AI Engineer": "LLMs, RAG systems, prompt engineering, vector databases, fine-tuning, generative AI, LangChain, transformers",
    "Backend Developer": "REST APIs, databases, server architecture, authentication, microservices, Node.js, Django, Flask, Spring Boot",
    "Frontend Developer": "React, Vue, Angular, UI/UX, responsive design, state management, CSS, JavaScript, TypeScript, web components",
    "Full Stack Developer": "End-to-end web development, frontend and backend, deployment, React, Node.js, databases, API design",
    "DevOps Engineer": "CI/CD, Docker, Kubernetes, cloud infrastructure, monitoring, Terraform, Jenkins, GitOps, automation",
    "Cloud Engineer": "AWS, Azure, GCP architecture, serverless, IaC, cost optimization, cloud migration, security",
    "Cybersecurity Analyst": "Penetration testing, vulnerability assessment, SIEM, incident response, OWASP, encryption, compliance",
    "Mobile Developer": "iOS, Android, Swift, Kotlin, Flutter, React Native, mobile UI, app deployment",
    "Data Engineer": "Apache Spark, Kafka, Airflow, ETL, data pipelines, data warehousing, Snowflake, BigQuery",
    "QA Engineer": "Test automation, Selenium, Cypress, unit testing, integration testing, CI/CD, quality assurance",
    "Software Engineer": "Programming, algorithms, data structures, system design, software development, object-oriented design",
    "UI/UX Designer": "Figma, Sketch, wireframing, prototyping, user research, design systems, interaction design",
}


# ============================================
# HuggingFace Embedding API
# ============================================
from huggingface_hub import InferenceClient
HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("HF_API_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN")
hf_client = InferenceClient(api_key=HF_TOKEN)

EMBEDDING_CACHE = {}
EMBEDDING_CACHE_MAX = int(os.getenv("EMBEDDING_CACHE_MAX", "500"))
EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"
DIM = 768

os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Fix transformers compatibility
try:
    import transformers
    if not hasattr(transformers.models.bert.modeling_bert, 'BertSdpaSelfAttention'):
        transformers.models.bert.modeling_bert.BertSdpaSelfAttention = transformers.models.bert.modeling_bert.BertSelfAttention
except (ImportError, AttributeError):
    pass


def safe_similarity(a, b):
    """Computes cosine similarity with NaN and zero-vector protection."""
    if a is None or b is None:
        return 0.0
    a = np.array(a).reshape(1, -1)
    b = np.array(b).reshape(1, -1)
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    try:
        sim = float(cosine_similarity(a, b)[0][0])
        return 0.0 if np.isnan(sim) else sim
    except Exception:
        return 0.0


def _cache_embedding(key, emb):
    if key in EMBEDDING_CACHE:
        EMBEDDING_CACHE[key] = emb
        return
    if len(EMBEDDING_CACHE) >= EMBEDDING_CACHE_MAX:
        oldest = next(iter(EMBEDDING_CACHE))
        EMBEDDING_CACHE.pop(oldest, None)
    EMBEDDING_CACHE[key] = emb


def get_embeddings_safe(texts):
    """HF-Powered Embedding Generator with caching and fallback."""
    global EMBEDDING_CACHE
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
                logging.error("[AI] HF_TOKEN missing — returning zero embeddings")
                for idx in text_indices:
                    results[idx] = np.zeros(DIM)
                return np.array(results)

            logging.info(f"[AI] Calling HF ({EMBEDDING_MODEL}) for {len(texts_to_encode)} chunks...")
            embeddings = hf_client.feature_extraction(texts_to_encode, model=EMBEDDING_MODEL)

            if not isinstance(embeddings, (list, np.ndarray)) or len(embeddings) == 0:
                for idx in text_indices:
                    results[idx] = np.zeros(DIM)
            else:
                embeddings = np.array(embeddings)
                if embeddings.ndim == 1:
                    embeddings = embeddings.reshape(1, -1)
                for i, emb in enumerate(embeddings):
                    if i < len(text_indices):
                        idx = text_indices[i]
                        results[idx] = emb
                        _cache_embedding(texts_to_encode[i], emb)

        for i in range(len(results)):
            if results[i] is None:
                results[i] = np.zeros(DIM)

        return np.array(results)
    except Exception as e:
        logging.error(f"[AI] Embedding failed: {e}")
        return np.zeros((len(texts), DIM))


def warm_up():
    """Preloads embedding API so first request is fast."""
    logging.info(">>> INFRA: Performing Warm-Start Preload...")
    get_embeddings_safe(["warmup flowats resume screening"])
    logging.info(">>> INFRA: Warm-Start Complete.")


# ============================================
# Part 4A: Multi-Layer Resume Parsing
# ============================================

def _extract_with_pymupdf(path):
    """Layer 1: PyMuPDF (fitz) — fastest, handles most PDFs."""
    try:
        import fitz
        doc = fitz.open(path)
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text("text"))
        doc.close()
        return "\n".join(text_parts)
    except Exception as e:
        logging.warning(f"[PARSER] PyMuPDF failed for {Path(path).name}: {e}")
        return ""


def _extract_with_pdfplumber(path):
    """Layer 2: pdfplumber — better for table-heavy resumes."""
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n".join(text_parts)
    except ImportError:
        logging.warning("[PARSER] pdfplumber not installed — skipping")
        return ""
    except Exception as e:
        logging.warning(f"[PARSER] pdfplumber failed for {Path(path).name}: {e}")
        return ""


def _extract_with_pdfminer(path):
    """Layer 3: pdfminer — legacy fallback."""
    try:
        from pdfminer.high_level import extract_text as pdf_extract
        return pdf_extract(path)
    except Exception as e:
        logging.warning(f"[PARSER] pdfminer failed for {Path(path).name}: {e}")
        return ""


def _extract_with_ocr(path):
    """Layer 4: OCR fallback using PyMuPDF + Tesseract for scanned PDFs."""
    try:
        import fitz
        from PIL import Image
        import pytesseract
        import io

        doc = fitz.open(path)
        text_parts = []
        for page in doc:
            pix = page.get_pixmap(dpi=300)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            page_text = pytesseract.image_to_string(img)
            if page_text.strip():
                text_parts.append(page_text)
        doc.close()
        return "\n".join(text_parts)
    except ImportError:
        logging.warning("[PARSER] Tesseract/pytesseract not available — OCR skipped")
        return ""
    except Exception as e:
        logging.warning(f"[PARSER] OCR failed for {Path(path).name}: {e}")
        return ""


def _validate_extraction(text, path):
    """Validates extracted text quality."""
    if not text:
        logging.error(f"[PARSER] ZERO text extracted from {Path(path).name}")
        return ""

    text = re.sub(r'\s+', ' ', text).strip()
    word_count = len(text.split())

    if len(text) < MIN_RESUME_CHARS or word_count < MIN_WORD_COUNT:
        logging.warning(
            f"[PARSER] LOW QUALITY: {Path(path).name} — "
            f"{len(text)} chars, {word_count} words"
        )

    return text


def extract_text(path):
    """Multi-layer resume parser with quality validation and OCR fallback."""
    ext = Path(path).suffix.lower()
    text = ""

    try:
        if ext == ".pdf":
            # Layer 1: PyMuPDF
            text = _extract_with_pymupdf(path)

            # Layer 2: pdfplumber
            if len(text.strip()) < 500:
                alt = _extract_with_pdfplumber(path)
                if len(alt.strip()) > len(text.strip()):
                    text = alt

            # Layer 3: pdfminer
            if len(text.strip()) < 500:
                alt = _extract_with_pdfminer(path)
                if len(alt.strip()) > len(text.strip()):
                    text = alt

            # Layer 4: OCR fallback
            if len(text.strip()) < 500:
                alt = _extract_with_ocr(path)
                if len(alt.strip()) > len(text.strip()):
                    text = alt

        elif ext == ".docx":
            text = docx2txt.process(path) or ""
        elif ext == ".txt":
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()

    except Exception as e:
        logging.error(f"[PARSER] Extraction failed for {path}: {e}")
        return ""

    text = _validate_extraction(text, path)
    logging.info(f"[PARSER] {Path(path).name}: {len(text)} chars extracted")
    return text


# ============================================
# Section Extraction
# ============================================

def extract_sections(text):
    """Splits resume into key sections."""
    sections = {"skills": "", "experience": "", "projects": "", "education": "", "certifications": "", "links": [], "other": text}

    headers = {
        "skills": r'(?i)\b(?:skills|technical skills|core competencies|technologies|tech stack|expertise|tools)\b',
        "experience": r'(?i)\b(?:experience|work history|employment|professional experience|work experience)\b',
        "projects": r'(?i)\b(?:projects|academic projects|personal projects|portfolio)\b',
        "education": r'(?i)\b(?:education|academic|qualifications|degrees?)\b',
        "certifications": r'(?i)\b(?:certifications?|licenses?|credentials?)\b',
    }

    # Extract links
    sections["links"] = re.findall(r'https?://[^\s,;)"]+', text)

    found = []
    for key, pattern in headers.items():
        for m in re.finditer(pattern, text):
            found.append((m.start(), key))

    found.sort()
    if not found:
        return sections

    for i in range(len(found)):
        start_idx, key = found[i]
        end_idx = found[i + 1][0] if i + 1 < len(found) else len(text)
        sections[key] = text[start_idx:end_idx].strip()

    return sections


def preprocess_text(text):
    """Basic cleaning for embedding."""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s\-\.\+\#]', '', text)
    return text.strip()


# ============================================
# Part 4: Triple-Layer Skill Extraction
# ============================================

def extract_skills(text):
    """Triple-layer skill extractor: regex + fuzzy + synonym expansion."""
    if not text:
        return []

    text_lower = text.lower()
    found_skills = set()

    # Layer 1: Exact + regex matching from taxonomy
    for skill in SKILL_DICTIONARY:
        s_raw = skill.strip()
        s_lower = s_raw.lower()

        # Special handling for short skills or those with special chars
        if len(s_raw) <= 2 or any(c in s_raw for c in '+#'):
            pattern = r'(?:^|[\s,;(])' + re.escape(s_lower) + r'(?:[\s,;)]|$)'
            if re.search(pattern, text_lower):
                found_skills.add(s_raw)
        elif ' ' in s_lower:
            # Multi-word skills: exact substring match
            if s_lower in text_lower:
                found_skills.add(s_raw)
        else:
            # Single word skills: word boundary match
            pattern = r'\b' + re.escape(s_lower) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.add(s_raw)

    # Layer 2: Synonym/abbreviation expansion
    for token in re.findall(r'\b\w+\b', text_lower):
        if token in SYNONYM_MAP:
            found_skills.add(SYNONYM_MAP[token])

    # Layer 3: Fuzzy matching for variant spellings
    words = re.findall(r'\b\w[\w\s\-\.]{2,30}\b', text_lower)
    skill_lower_set = {s.lower() for s in found_skills}
    for phrase in words:
        phrase_clean = phrase.strip()
        if phrase_clean in skill_lower_set:
            continue
        match = process.extractOne(phrase_clean, [s.lower() for s in SKILL_DICTIONARY], scorer=fuzz.ratio)
        if match and match[1] >= 88:
            # Find the original cased skill
            matched_skill = next((s for s in SKILL_DICTIONARY if s.lower() == match[0]), match[0])
            found_skills.add(matched_skill)

    return sorted(list(found_skills))


def get_semantic_matches(resume_skills, jd_skills, threshold=0.85):
    """Finds skills that are conceptually similar using embeddings."""
    if not resume_skills or not jd_skills:
        return []

    matched = [s for s in resume_skills if s in jd_skills]
    remaining_r = [s for s in resume_skills if s not in matched]
    remaining_j = [s for s in jd_skills if s not in matched]

    if not remaining_r or not remaining_j:
        return matched

    try:
        r_embs = get_embeddings_safe(remaining_r)
        j_embs = get_embeddings_safe(remaining_j)

        for i, r_emb in enumerate(r_embs):
            for j, j_emb in enumerate(j_embs):
                sim = safe_similarity(r_emb, j_emb)
                if sim >= threshold:
                    matched.append(remaining_r[i])
                    break
    except Exception:
        pass

    return list(set(matched))


def fuzzy_match_skills(resume_skills, jd_skills):
    """Skill matching using fuzzy logic + semantic similarity."""
    matched = []
    jd_lower = [s.lower() for s in jd_skills]

    for r in resume_skills:
        r_lower = r.lower()
        # Direct match
        if r_lower in jd_lower:
            matched.append(r)
            continue
        # Fuzzy match
        best = process.extractOne(r_lower, jd_lower, scorer=fuzz.token_set_ratio)
        if best and best[1] >= 85:
            matched.append(r)

    # Semantic augmentation
    semantic = get_semantic_matches(resume_skills, jd_skills)
    matched.extend(semantic)

    return sorted(list(set(matched)))


# ============================================
# Experience Extraction
# ============================================

def extract_years_of_experience(text):
    """Detects total years of experience from common resume phrasing."""
    if not text:
        return 0.0
    text_lower = text.lower()
    years = 0.0

    for match in re.findall(r'(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:professional\s+)?(?:experience|exp)?', text_lower):
        try:
            years = max(years, float(match))
        except ValueError:
            pass

    for match in re.findall(r'(?:total\s+)?experience\s*[:\-]?\s*(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)', text_lower):
        try:
            years = max(years, float(match))
        except ValueError:
            pass

    current_year = datetime.datetime.now().year
    range_patterns = [
        r'(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*(\d{4})\s*[-–—to]+\s*(?:present|current|now|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*)?(\d{4})?',
        r'\b(\d{4})\s*[-–—to]+\s*(?:present|current|now|(\d{4}))\b',
    ]
    span_years = 0.0
    for pattern in range_patterns:
        for start, end in re.findall(pattern, text_lower):
            try:
                y1 = int(start)
                y2 = current_year if not end or str(end).lower() in ("present", "current", "now", "") else int(end)
                if 1970 <= y1 <= current_year and y1 <= y2 <= current_year + 1:
                    span_years += max(0, y2 - y1)
            except (ValueError, TypeError):
                continue

    if span_years > 0:
        years = max(years, min(span_years, 40))

    return float(min(years, 40))


def extract_years_from_jd(text):
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
            except Exception:
                continue
    return 0.0


# ============================================
# Part 6: Semantic Role Prediction
# ============================================

def detect_role_from_resume(text, top_k=3):
    """Semantic role prediction using embedding similarity against role taxonomy."""
    if not text:
        return "Software Engineer", ["Software Engineer"]

    try:
        # Get resume embedding
        resume_emb = get_embeddings_safe([text[:8000]])[0]

        # Get role description embeddings (use cache)
        role_names = list(ROLE_TAXONOMY.keys())
        role_descriptions = list(ROLE_TAXONOMY.values())
        role_embs = get_embeddings_safe(role_descriptions)

        # Compute similarities
        scores = []
        for i, role_emb in enumerate(role_embs):
            sim = safe_similarity(resume_emb, role_emb)
            scores.append((role_names[i], sim))

        # Sort by similarity
        scores.sort(key=lambda x: x[1], reverse=True)
        top_roles = [s[0] for s in scores[:top_k]]
        best_role = scores[0][0] if scores else "Software Engineer"

        return best_role, top_roles

    except Exception as e:
        logging.warning(f"[AI] Semantic role prediction failed: {e}")
        # Fallback to keyword detection
        return _keyword_role_detection(text), ["Software Engineer"]


def _keyword_role_detection(text):
    """Fallback: keyword-based role detection."""
    text = text.lower()

    if any(x in text for x in ["tensorflow", "pytorch", "machine learning", "deep learning", "neural network"]):
        return "Machine Learning Engineer"
    if any(x in text for x in ["data analysis", "power bi", "tableau", "business intelligence"]):
        return "Data Analyst"
    if any(x in text for x in ["react", "frontend", "vue", "angular", "css"]):
        return "Frontend Developer"
    if any(x in text for x in ["node", "backend", "express", "django", "flask", "spring"]):
        return "Backend Developer"
    if any(x in text for x in ["docker", "kubernetes", "devops", "terraform", "jenkins"]):
        return "DevOps Engineer"
    if any(x in text for x in ["cyber", "security", "firewall", "pentest"]):
        return "Cybersecurity Analyst"
    if any(x in text for x in ["swift", "kotlin", "flutter", "react native", "ios", "android"]):
        return "Mobile Developer"

    return "Software Engineer"


# ============================================
# JD Utilities
# ============================================

def is_valid_job_description(text):
    """Rejects gibberish or empty text while allowing short titles."""
    if not text:
        return False
    jd_clean = text.lower().strip()
    COMMON_ROLES = [
        "data analyst", "data scientist", "python developer", "react developer",
        "software engineer", "frontend developer", "backend developer",
        "ai engineer", "ml engineer", "devops engineer", "analyst", "engineer",
        "developer", "manager", "hr manager", "recruiter"
    ]
    if any(role in jd_clean for role in COMMON_ROLES):
        return True
    if len(jd_clean) < 3:
        return False
    if re.search(r'(.)\1{10,}', text):
        return False
    words = re.findall(r'\b[a-zA-Z]{2,}\b', text)
    return len(words) >= 1


def expand_job_description(text):
    """Enriches short JDs with industry-standard skills."""
    text_lower = text.lower()
    if len(text.split()) > 15:
        return text

    expansion = "\n[AUTO-EXPANSION]: "
    added = False
    knowledge_map = {
        "data analyst": "SQL, Excel, Power BI, Tableau, Python, statistics, data visualization, reporting.",
        "data scientist": "Python, R, Machine Learning, Statistics, SQL, Pandas, Scikit-learn, Deep Learning.",
        "machine learning": "Python, PyTorch, TensorFlow, Scikit-learn, Math, Algorithms, Deep Learning, MLOps.",
        "backend": "Node.js, Python, Java, SQL, APIs, Microservices, Databases, Cloud, System Design.",
        "frontend": "React, JavaScript, CSS, HTML, TypeScript, UI/UX, Responsive Design, Redux.",
        "full stack": "React, Node.js, JavaScript, SQL, MongoDB, Web Development, Git, Deployment.",
        "devops": "Docker, Kubernetes, AWS, CI/CD, Jenkins, Terraform, Linux, Automation.",
        "cloud": "AWS, Azure, GCP, Serverless, Infrastructure as Code, Docker, Kubernetes.",
        "mobile": "Swift, Kotlin, Flutter, React Native, iOS, Android, App Development.",
        "cybersecurity": "Penetration Testing, OWASP, SIEM, Encryption, Compliance, Incident Response.",
    }

    for key, skills in knowledge_map.items():
        if key in text_lower:
            expansion += f"Relevant skills: {skills} "
            added = True

    return text + (expansion if added else "")


def _jd_role_match_score(predicted_role, job_description):
    """Fuzzy alignment between detected resume role and JD title/intent."""
    if not predicted_role or not job_description:
        return 0.5
    jd_lower = job_description.lower()
    role_lower = predicted_role.lower()
    if role_lower in jd_lower:
        return 1.0
    role_tokens = [t for t in re.split(r'[\s/]+', role_lower) if len(t) > 2]
    if role_tokens:
        hits = sum(1 for t in role_tokens if t in jd_lower)
        if hits >= 2:
            return 0.9
        if hits == 1:
            return 0.75
    best = process.extractOne(role_lower, [jd_lower[:2000]], scorer=fuzz.partial_ratio)
    if best and best[1] >= 72:
        return min(1.0, best[1] / 100.0)
    return 0.45


# ============================================
# Part 5: ATS Matching Engine
# ============================================

def batch_compute_match_score(resume_texts, job_description):
    """
    Production ATS Scoring Engine with weighted components.
    Skills (40%) + Semantic (25%) + Projects (15%) + Experience (10%) + Education (10%)
    """
    # Input validation
    if not is_valid_job_description(job_description):
        return [_empty_result("Job description is too short. Please provide at least 2 words.")] * len(resume_texts)

    job_description = expand_job_description(job_description)

    jd_sections = extract_sections(job_description)
    jd_skills_text = jd_sections["skills"] if jd_sections["skills"] else job_description
    jd_skills_list = extract_skills(jd_skills_text)

    # JD Skill Inference when extraction is weak
    if len(jd_skills_list) < 3:
        jd_lower = job_description.lower()
        inferred = []
        for role, skills in ROLE_SKILLS.items():
            if role in jd_lower:
                inferred.extend(skills)
        if inferred:
            jd_skills_list = sorted(list(set(jd_skills_list + [s.title() for s in inferred])))

    jd_text_clean = preprocess_text(job_description)[:8000]
    resume_texts_clean = [preprocess_text(t)[:8000] for t in resume_texts]

    # Generate embeddings
    all_texts = [jd_text_clean] + resume_texts_clean
    embeddings = get_embeddings_safe(all_texts)
    jd_emb = embeddings[0] if embeddings is not None else None

    required_years = extract_years_from_jd(job_description)

    final_results = []
    try:
        for i, text in enumerate(resume_texts):
            # Part 4A: Extraction quality gate
            if len(text.strip()) < MIN_RESUME_CHARS:
                result = _empty_result(
                    "Resume text could not be extracted. Please upload a text-based PDF."
                )
                result["predicted_role"] = "Extraction Failed"
                result["extraction_quality"] = "poor"
                final_results.append(validate_ats_result(result))
                continue

            # Extract sections and skills
            sections = extract_sections(text)
            skills_block = sections.get("skills") or text
            r_skills = extract_skills(skills_block) or extract_skills(text)
            years = extract_years_of_experience(text)

            # 1. Semantic Similarity (25%)
            semantic_score = 0.35
            if jd_emb is not None and embeddings is not None:
                sim = safe_similarity(jd_emb, embeddings[i + 1])
                semantic_score = max(0.0, min(1.0, float(sim)))

            # 2. Skill Match (40%)
            matched_with_jd = fuzzy_match_skills(r_skills, jd_skills_list)
            skill_score = len(matched_with_jd) / max(len(jd_skills_list), 1)
            skill_score = min(1.0, skill_score)

            # 3. Role Prediction + JD alignment
            best_role, top_roles = detect_role_from_resume(text)
            role_match = _jd_role_match_score(best_role, job_description)

            # 4. Projects relevance (15%)
            projects_text = sections.get("projects", "")
            if projects_text and jd_emb is not None:
                proj_emb = get_embeddings_safe([preprocess_text(projects_text)[:4000]])[0]
                project_score = safe_similarity(jd_emb, proj_emb)
            else:
                project_score = semantic_score * 0.8  # Fallback

            # 5. Experience alignment (10%)
            if required_years > 0:
                exp_score = min(years / required_years, 1.5) if years > 0 else 0.0
                exp_score = min(1.0, exp_score)
            else:
                exp_score = min(years / 10, 1.0) if years > 0 else 0.3

            # 6. Education relevance (10%)
            education_text = sections.get("education", "")
            if education_text and jd_emb is not None:
                edu_emb = get_embeddings_safe([preprocess_text(education_text)[:2000]])[0]
                education_score = safe_similarity(jd_emb, edu_emb)
            else:
                education_score = 0.4  # Default

            # Weighted sum
            raw = (
                semantic_score * 0.25
                + skill_score * 0.40
                + project_score * 0.15
                + exp_score * 0.10
                + education_score * 0.10
            )

            # Calibration: sigmoid stretch
            raw_calibrated = 1.0 / (1.0 + math.exp(-8 * (raw - 0.35)))
            match_percentage = int(min(95, max(5, round(raw_calibrated * 100))))

            # Reasoning
            reasoning = []
            if matched_with_jd:
                reasoning.append(f"Strong alignment in {', '.join(matched_with_jd[:3])}.")
            missing_skills = list(set(jd_skills_list) - set(matched_with_jd))
            if missing_skills:
                reasoning.append(f"Consider adding: {', '.join(missing_skills[:3])}.")
            if years >= required_years and required_years > 0:
                reasoning.append("Experience requirements met.")
            elif required_years > 0:
                reasoning.append(f"Building toward the required {int(required_years)} years of experience.")

            resume_skills_unique = list(set(r_skills))

            result = {
                "match_percentage": match_percentage,
                "final_score": float(match_percentage) / 100.0,
                "predicted_role": best_role,
                "top_roles": top_roles,
                "experience": f"{int(years)} Years" if years > 0 else "Fresher",
                "experience_years": int(years),
                "skills": sorted(list(set(list(matched_with_jd) + [s for s in resume_skills_unique if s not in matched_with_jd]))),
                "resume_skills": resume_skills_unique,
                "matched_skills": sorted(matched_with_jd),
                "all_skills": resume_skills_unique,
                "matched_skills_count": len(matched_with_jd),
                "total_skills": len(resume_skills_unique),
                "missing_skills": missing_skills[:5],
                "summary_reasoning": " ".join(reasoning),
                "BACKEND_VERSION": VERSION,
            }

            # Part 9A: Validate
            result = validate_ats_result(result)
            final_results.append(result)

    except Exception as e:
        logging.error(f"[ATS] Scoring Error: {e}")
        final_results.append(validate_ats_result(_empty_result(str(e))))

    # Batch ranking
    if len(final_results) > 1:
        ranked = sorted(final_results, key=lambda x: x["match_percentage"], reverse=True)
        top_score = ranked[0]["match_percentage"]
        for res in final_results:
            rank = next((idx for idx, item in enumerate(ranked) if item is res), 0) + 1
            res["batch_rank"] = f"{rank}/{len(final_results)}"
            res["relative_strength"] = "Top Candidate" if res["match_percentage"] == top_score else "Competitive"

    return final_results


def compute_match_score(resume_text, job_description):
    """Wrapper for single resume matching with validation."""
    try:
        results = batch_compute_match_score([resume_text], job_description)
        return validate_ats_result(results[0]) if results else _empty_result()
    except Exception as e:
        logging.error(f"[ATS] compute_match_score failed: {e}")
        return _empty_result()


# ============================================
# Part 9A: Production Validation Guards
# ============================================

def validate_ats_result(result):
    """Production guardrail: Ensures every ATS response is valid.
    Prevents NaN, undefined, null, or missing fields from reaching the frontend.
    """
    if not isinstance(result, dict):
        return _empty_result()

    # 1. Score validation
    score = result.get("match_percentage", 0)
    if score is None or (isinstance(score, float) and math.isnan(score)):
        score = 0
    try:
        score = int(max(0, min(100, float(score))))
    except (ValueError, TypeError):
        score = 0
    result["match_percentage"] = score

    final_score = result.get("final_score", 0.0)
    if final_score is None or (isinstance(final_score, float) and math.isnan(final_score)):
        final_score = 0.0
    try:
        final_score = float(max(0.0, min(1.0, float(final_score))))
    except (ValueError, TypeError):
        final_score = 0.0
    result["final_score"] = final_score

    # 2. Role validation
    role = result.get("predicted_role")
    if not role or not isinstance(role, str) or role.strip() == "":
        result["predicted_role"] = "Unknown"

    # 3. Skills array validation
    for field in ["skills", "resume_skills", "matched_skills", "all_skills", "missing_skills"]:
        val = result.get(field)
        if val is None or not isinstance(val, list):
            result[field] = []
        else:
            result[field] = [s for s in val if s and isinstance(s, str)]

    # top_roles
    if not isinstance(result.get("top_roles"), list):
        result["top_roles"] = [result.get("predicted_role", "Unknown")]

    # 4. String field validation
    if not result.get("summary_reasoning") or not isinstance(result.get("summary_reasoning"), str):
        result["summary_reasoning"] = "Analysis complete."
    if not result.get("experience") or not isinstance(result.get("experience"), str):
        result["experience"] = "Unknown"
    if not result.get("BACKEND_VERSION"):
        result["BACKEND_VERSION"] = VERSION

    # 5. Numeric field validation
    for field in ["experience_years", "matched_skills_count", "total_skills"]:
        val = result.get(field)
        if val is None:
            result[field] = 0
        else:
            try:
                val = float(val)
                if math.isnan(val):
                    val = 0
                result[field] = int(max(0, val))
            except (ValueError, TypeError):
                result[field] = 0

    return result


def _empty_result(reason="Unable to analyze this resume. Please ensure the file contains readable text."):
    """Safe empty result — never NaN, never null."""
    return {
        "match_percentage": 0,
        "final_score": 0.0,
        "predicted_role": "Unknown",
        "top_roles": ["Unknown"],
        "experience": "Unknown",
        "experience_years": 0,
        "skills": [],
        "resume_skills": [],
        "matched_skills": [],
        "all_skills": [],
        "missing_skills": [],
        "matched_skills_count": 0,
        "total_skills": 0,
        "summary_reasoning": reason,
        "BACKEND_VERSION": VERSION,
    }


# Legacy compat
class BERTVectorizer(BaseEstimator, TransformerMixin):
    def __init__(self, model_name='all-mpnet-base-v2'):
        self.model_name = model_name
        self.model = None
    def fit(self, X, y=None): return self
    def transform(self, X):
        return np.zeros((len(X), 768))

if "__main__" in sys.modules:
    setattr(sys.modules["__main__"], 'BERTVectorizer', BERTVectorizer)