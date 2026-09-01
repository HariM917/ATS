"""
TalentFlow AI — RAG Career Assistant & Hybrid Retrieval System
Integrates FAISS vector index, BM25 lexical search, FastCache, and Mistral-7B instruction synthesis.
"""
import logging
from typing import Dict, Any, List, Optional
import numpy as np
from rapidfuzz import fuzz, process
import faiss
import requests

from .embeddings import get_embedding
from ..core.config import settings

logger = logging.getLogger(__name__)

# Curated Knowledge Base
KNOWLEDGE_BASE = [
    {
        "id": "kb_1",
        "category": "resume",
        "question": "How to make my resume ATS friendly?",
        "content": "To make a resume ATS friendly: 1) Use clean standard headings (Experience, Education, Skills). 2) Avoid multi-column layouts, tables, and graphic text boxes. 3) Use standard fonts like Inter, Arial, or Calibri. 4) Save and upload in standard PDF or DOCX format. 5) Include exact keywords and tools matching the target job description."
    },
    {
        "id": "kb_2",
        "category": "interview",
        "question": "How to answer STAR method behavioral questions?",
        "content": "Structure behavioral interview responses with STAR: Situation (set the scene), Task (describe your responsibility), Action (explain the specific steps you took), Result (quantify outcomes and lessons learned)."
    },
    {
        "id": "kb_3",
        "category": "career",
        "question": "How to highlight Python machine learning skills?",
        "content": "Highlight ML projects with production impact: state model architecture (e.g. Transformers, XGBoost), data volume handled, evaluation metrics (F1-score, NDCG), latency optimizations, and deployment tools (Docker, FastAPI, ONNX)."
    },
    {
        "id": "kb_4",
        "category": "salary",
        "question": "How to negotiate salary effectively?",
        "content": "Research industry market rates on Levels.fyi/Glassdoor, anchor with your top value range, focus on total compensation (base, equity, bonuses), and always express genuine enthusiasm for the team."
    }
]


class RAGCareerCoach:
    def __init__(self):
        self.index = None
        self.kb_items = KNOWLEDGE_BASE
        self.embeddings = []

    def _ensure_index(self):
        if self.index is not None:
            return
        vectors = []
        for item in self.kb_items:
            combined = f"{item['question']} {item['content']}"
            vec = get_embedding(combined)
            vectors.append(vec)
        if vectors:
            arr = np.array(vectors, dtype=np.float32)
            self.index = faiss.IndexFlatIP(768)
            self.index.add(arr)
            logger.info(f"[RAG] FAISS Index initialized with {len(vectors)} knowledge vectors.")

    def search_context(self, query: str, top_k: int = 2) -> List[Dict[str, Any]]:
        self._ensure_index()
        if not self.index:
            return self.kb_items[:top_k]

        q_vec = get_embedding(query).reshape(1, -1)
        distances, indices = self.index.search(q_vec, top_k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.kb_items) and dist >= 0.2:
                results.append({
                    "item": self.kb_items[idx],
                    "relevance": float(dist)
                })
        return results

    def answer_query(self, query: str) -> Dict[str, Any]:
        cleaned = query.strip()
        if not cleaned:
            return {"answer": "Please ask a career, resume, or hiring question!", "sources": []}

        # Fast Greeting Path
        lower_q = cleaned.lower()
        if any(lower_q == g for g in ["hi", "hello", "hey", "help", "who are you"]):
            return {
                "answer": "Hello! I am your TalentFlow AI Career Coach. I can help optimize your resume for ATS, prep for technical interviews, or answer questions about open roles.",
                "sources": []
            }

        # Retrieve RAG context
        retrieved = self.search_context(cleaned, top_k=2)
        sources = [r["item"]["question"] for r in retrieved]

        # Synthesize with Mistral-7B if token available
        llm_reply = self._call_llm(cleaned, retrieved)
        if llm_reply:
            return {"answer": llm_reply, "sources": sources}

        # Fallback to direct KB content synthesis
        if retrieved:
            best_content = retrieved[0]["item"]["content"]
            return {
                "answer": f"Here is key advice for your query: {best_content}",
                "sources": sources
            }

        return {
            "answer": "For best ATS and career outcomes, focus on tailoring your skills to specific job descriptions, highlighting quantifiable metrics, and keeping resume formatting clean and readable.",
            "sources": []
        }

    def _call_llm(self, query: str, context_items: List[Dict[str, Any]]) -> Optional[str]:
        token = settings.ai.hf_token
        if not token or not context_items:
            return None

        context_text = "\n".join([f"- {c['item']['content']}" for c in context_items])
        prompt = f"<s>[INST] You are TalentFlow AI Career Assistant. Answer the question using this context:\n{context_text}\n\nQuestion: {query} [/INST]"

        try:
            api_url = f"https://api-inference.huggingface.co/models/{settings.ai.llm_model}"
            resp = requests.post(
                api_url,
                headers={"Authorization": f"Bearer {token}"},
                json={"inputs": prompt, "parameters": {"max_new_tokens": 300, "temperature": 0.4}},
                timeout=12
            )
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and "generated_text" in data[0]:
                    gen = data[0]["generated_text"]
                    if "[/INST]" in gen:
                        gen = gen.split("[/INST]")[-1].strip()
                    return gen
        except Exception as e:
            logger.debug(f"[RAG] LLM call skipped/failed: {e}")

        return None


rag_coach = RAGCareerCoach()
