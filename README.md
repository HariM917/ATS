# 🚀 TalentFlow: Elite AI Hiring Intelligence System

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://reactjs.org/)
[![FAISS](https://img.shields.io/badge/FAISS-Vector_Search-FF6F00.svg)](https://github.com/facebookresearch/faiss)

**TalentFlow** is a production-grade Applicant Tracking System (ATS) evolved with high-performance AI reasoning. It leverages Retrieval-Augmented Generation (RAG), semantic vector search, and hybrid machine learning to transform the hiring process from manual screening to intelligent talent discovery.

---

## 🌟 Key Features

### 🧠 Semantic RAG Chatbot
- **Advanced Retrieval**: Uses FAISS for sub-millisecond semantic search across static career guides and dynamic ATS data.
- **LLM Synthesis**: Integrated with HuggingFace (Zephyr-7B) for professional, context-aware career coaching and candidate analysis.
- **Observability**: Built-in logging for latency tracking, cache hits, and source attribution.

### 📊 Recruitment Intelligence Dashboard
- **Real-time Analytics**: Visual breakdown of application statuses, average match scores, and hiring funnels.
- **Elite Match Score**: Hybrid scoring algorithm combining BERT embeddings, keyword density, role validation, and experience analysis.
- **Batch Processing**: Rapidly rank hundreds of resumes against a Job Description in seconds.

### 🛡️ Enterprise-Grade Security
- **Role-Based Access Control (RBAC)**: Strict data isolation between HR Administrators and Candidates.
- **Performance Optimized**: Local embedding caching and lazy-loading models ensure the backend stays responsive under load.

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 18, TypeScript, Tailwind CSS, Lucide Icons, Framer Motion |
| **Backend** | Python, Flask, SQLite3 (Robust Schema) |
| **AI/ML** | Sentence-Transformers (MPNet), FAISS, HuggingFace Inference API, Scikit-Learn |
| **DevOps** | Render (Backend), Vercel (Frontend), Git |

---

## 🏗️ System Architecture (Production Grade)

```mermaid
graph TD
    User((User)) -->|HTTPS| Frontend[React TypeScript UI]
    
    subgraph "Security & Auth"
        Frontend -->|JWT Auth| Auth[Auth Layer]
        Auth -->|Validated| Backend[Flask API Engine]
        Backend -->|RBAC Check| RBAC[RBAC / Security Layer]
    end
    
    subgraph "AI Intelligence Core"
        RBAC -->|Search Query| RAG[RAG Manager]
        RAG -->|Vectorize| Embed[Embedding Model MPNet]
        Embed -->|Semantic Query| FAISS[(FAISS Vector Index)]
        FAISS -->|Top Context| RAG
        RAG -->|Synthesis| LLM[HuggingFace LLM]
        
        RBAC -->|Resume Analysis| Matcher[AI Match Engine]
        Matcher -->|Extract| Feature[Feature Extraction]
        Feature -->|Predict| ML[Hybrid Boosting Model]
    end
    
    subgraph "Async & Persistence"
        RBAC -->|SQL| DB[(SQLite Database)]
        RBAC -->|Cache Hit/Miss| Cache[Semantic Cache]
        
        RBAC -->|Async Task| Queue[Threaded Task Queue]
        Queue -->|Trigger| Email[Email Service / SMTP]
    end
    
    subgraph "Observability"
        Backend -->|Log Events| Logs[Observability Log]
        Logs -->|Monitor| Stats[Performance Metrics]
    end
```

---

## 🚀 Getting Started (Production Setup)

### 📋 Prerequisites
- **Python 3.9+** & **Node.js 18+**
- **Git LFS**: Required for downloading large model files (`resume_classifier.pkl`).
- **HuggingFace Token**: For the Zephyr-7B LLM engine.
- **SMTP Credentials**: (Optional) For automated candidate notifications.

### 🛠️ Installation & Setup

1. **Clone & Initialize LFS**
   ```bash
   git clone https://github.com/HariM917/ATS.git
   cd ATS
   git lfs install
   git lfs pull
   ```

2. **Backend Configuration**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
   Create a `.env` file in the `backend/` directory:
   ```env
   HF_TOKEN=your_huggingface_api_token
   SENDER_EMAIL=your_gmail@gmail.com
   SENDER_PASSWORD=your_app_password
   ```

3. **Launch Backend (Port 8000)**
   ```bash
   python app.py
   ```
   *Note: The server will warm-up the BERT/MPNet models on startup. Ensure port 8000 is available.*

4. **Frontend Configuration**
   ```bash
   cd ../frontend
   npm install
   npm run dev
   ```

### 🧪 Verification & Troubleshooting
- **Connection Test**: Open the dashboard and check if the "AI Assistant" responds.
- **CORS Issues**: Ensure the backend allows your frontend origin in `app.py`.
- **Hard Refresh**: If the UI shows old chatbot logic, press `Ctrl + Shift + R` to clear browser cache.
- **Model Loading**: First-time AI matching may take ~10s to load local models into memory.

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

---

## 🤝 Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

Developed with ❤️ by [Hari](https://github.com/HariM917)
