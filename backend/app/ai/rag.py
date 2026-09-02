"""
TalentFlow AI — Production RAG Career Assistant
Hybrid Retrieval (FAISS + BM25) → Reranking → LLM Synthesis → Source Attribution → Caching → Graceful Fallback
"""
import time
import hashlib
import logging
from typing import Dict, Any, List, Optional
from collections import OrderedDict
import numpy as np

from .embeddings import get_embedding
from .vector_store import VectorStore
from .text_processor import clean_text
from ..core.config import settings

logger = logging.getLogger(__name__)


# Expanded Curated Knowledge Base (12+ entries)
KNOWLEDGE_BASE = [
    {
        "id": "kb_1", "category": "resume",
        "question": "How to make my resume ATS friendly?",
        "content": "To make a resume ATS friendly: 1) Use clean standard headings (Experience, Education, Skills). 2) Avoid multi-column layouts, tables, and graphic text boxes. 3) Use standard fonts like Inter, Arial, or Calibri. 4) Save and upload in standard PDF or DOCX format. 5) Include exact keywords and tools matching the target job description."
    },
    {
        "id": "kb_2", "category": "interview",
        "question": "How to answer STAR method behavioral questions?",
        "content": "Structure behavioral interview responses with STAR: Situation (set the scene), Task (describe your responsibility), Action (explain the specific steps you took), Result (quantify outcomes and lessons learned)."
    },
    {
        "id": "kb_3", "category": "career",
        "question": "How to highlight Python machine learning skills?",
        "content": "Highlight ML projects with production impact: state model architecture (e.g. Transformers, XGBoost), data volume handled, evaluation metrics (F1-score, NDCG), latency optimizations, and deployment tools (Docker, FastAPI, ONNX)."
    },
    {
        "id": "kb_4", "category": "salary",
        "question": "How to negotiate salary effectively?",
        "content": "Research industry market rates on Levels.fyi/Glassdoor, anchor with your top value range, focus on total compensation (base, equity, bonuses), and always express genuine enthusiasm for the team."
    },
    {
        "id": "kb_5", "category": "resume",
        "question": "What are common resume mistakes to avoid?",
        "content": "Avoid: 1) Generic objective statements instead of targeted summaries. 2) Listing duties instead of achievements. 3) Typos and grammatical errors. 4) Including irrelevant personal information. 5) Using an unprofessional email address. 6) Making the resume longer than 2 pages without justification."
    },
    {
        "id": "kb_6", "category": "interview",
        "question": "How to prepare for a technical coding interview?",
        "content": "Practice on LeetCode/HackerRank focusing on arrays, strings, trees, graphs, and dynamic programming. Review Big-O complexity analysis. Practice explaining your thought process out loud. Study the company's tech stack. Prepare 2-3 questions to ask the interviewer about team culture and technical challenges."
    },
    {
        "id": "kb_7", "category": "career",
        "question": "How to transition from one tech role to another?",
        "content": "Build bridge projects that combine your current expertise with the target role. Take relevant certifications (AWS, Google Cloud, etc.). Contribute to open-source projects in the target domain. Network with professionals in the target role through LinkedIn and meetups. Highlight transferable skills in your resume."
    },
    {
        "id": "kb_8", "category": "resume",
        "question": "How to quantify achievements on a resume?",
        "content": "Use the XYZ formula: Accomplished [X] as measured by [Y] by doing [Z]. Examples: 'Reduced API response time by 40% by implementing Redis caching layer' or 'Increased test coverage from 45% to 92% across 3 microservices'. Always use numbers, percentages, or dollar amounts."
    },
    {
        "id": "kb_9", "category": "career",
        "question": "How to build a strong GitHub portfolio?",
        "content": "Pin 6 best repositories showcasing different skills. Write clear README files with screenshots, architecture diagrams, and setup instructions. Include CI/CD badges. Contribute to popular open-source projects. Maintain a consistent commit history. Add a profile README with your tech stack and interests."
    },
    {
        "id": "kb_10", "category": "interview",
        "question": "How to handle system design interviews?",
        "content": "Follow the structured approach: 1) Clarify requirements and constraints. 2) Estimate scale (users, data, QPS). 3) Define high-level architecture. 4) Deep dive into critical components. 5) Address bottlenecks and trade-offs. 6) Discuss monitoring and failure scenarios. Practice with real systems like URL shorteners, chat apps, and news feeds."
    },
    {
        "id": "kb_11", "category": "career",
        "question": "What soft skills are most important for tech professionals?",
        "content": "Key soft skills: 1) Communication — explaining technical concepts to non-technical stakeholders. 2) Collaboration — working effectively in cross-functional teams. 3) Problem-solving — breaking down complex issues systematically. 4) Time management — prioritizing tasks and meeting deadlines. 5) Adaptability — learning new technologies and frameworks quickly."
    },
    {
        "id": "kb_12", "category": "resume",
        "question": "How to write a compelling professional summary?",
        "content": "Write 2-3 sentences highlighting: years of experience, key technical domains, notable achievements, and what you bring to the target role. Example: 'Full-stack engineer with 5+ years building scalable React/Node.js applications. Led migration of monolithic architecture to microservices, reducing deployment time by 70%. Passionate about developer experience and CI/CD automation.'"
    },
]


class LRUCache:
    """Simple LRU cache with TTL for RAG response caching."""

    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict = OrderedDict()

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        if key in self._cache:
            entry = self._cache[key]
            if time.time() - entry["timestamp"] < self.ttl_seconds:
                self._cache.move_to_end(key)
                return entry["value"]
            else:
                del self._cache[key]
        return None

    def put(self, key: str, value: Dict[str, Any]) -> None:
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = {"value": value, "timestamp": time.time()}
        if len(self._cache) > self.max_size:
            self._cache.popitem(last=False)


def _bm25_score(query_terms: List[str], doc_terms: List[str], k1: float = 1.5, b: float = 0.75, avg_dl: float = 50.0) -> float:
    """Simple BM25 scoring for lexical matching."""
    if not query_terms or not doc_terms:
        return 0.0
    dl = len(doc_terms)
    score = 0.0
    for qt in query_terms:
        tf = doc_terms.count(qt)
        if tf > 0:
            idf = 1.0  # Simplified: no corpus-level IDF
            numerator = tf * (k1 + 1)
            denominator = tf + k1 * (1 - b + b * dl / avg_dl)
            score += idf * numerator / denominator
    return score


class RAGCareerCoach:
    def __init__(self):
        self.vector_store = VectorStore(dimension=768)
        self.kb_items = KNOWLEDGE_BASE
        self._index_built = False
        self._cache = LRUCache(max_size=200, ttl_seconds=600)

    def _ensure_index(self):
        if self._index_built:
            return
        for item in self.kb_items:
            combined = f"{item['question']} {item['content']}"
            vec = get_embedding(combined)
            self.vector_store.add(vec, meta={"kb_index": self.kb_items.index(item), "id": item["id"]})
        self.vector_store.build_index()
        self._index_built = True
        logger.info(f"[RAG] Index initialized with {len(self.kb_items)} knowledge entries.")

    def _hybrid_search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Hybrid retrieval: FAISS semantic search + BM25 lexical search with score fusion."""
        self._ensure_index()
        query_clean = clean_text(query).lower()
        query_terms = query_clean.split()

        # Semantic search
        q_vec = get_embedding(query)
        semantic_results = self.vector_store.search(q_vec, top_k=top_k * 2, min_score=0.1)

        # BM25 lexical search
        bm25_scores = []
        for i, item in enumerate(self.kb_items):
            doc_text = f"{item['question']} {item['content']}".lower()
            doc_terms = doc_text.split()
            score = _bm25_score(query_terms, doc_terms)
            bm25_scores.append((i, score))
        bm25_scores.sort(key=lambda x: x[1], reverse=True)

        # Score fusion (weighted combination)
        fused = {}
        semantic_weight = 0.7
        lexical_weight = 0.3

        for idx, score, meta in semantic_results:
            kb_idx = meta.get("kb_index", idx)
            fused[kb_idx] = fused.get(kb_idx, 0) + semantic_weight * score

        for idx, score in bm25_scores[:top_k * 2]:
            if score > 0:
                # Normalize BM25 to 0-1 range
                max_bm25 = bm25_scores[0][1] if bm25_scores[0][1] > 0 else 1
                normalized = score / max_bm25
                fused[idx] = fused.get(idx, 0) + lexical_weight * normalized

        # Sort by fused score and return top_k
        ranked = sorted(fused.items(), key=lambda x: x[1], reverse=True)[:top_k]
        results = []
        for kb_idx, fused_score in ranked:
            if kb_idx < len(self.kb_items) and fused_score > 0.1:
                results.append({
                    "item": self.kb_items[kb_idx],
                    "relevance": round(fused_score, 3),
                })
        return results

    def answer_query(self, query: str) -> Dict[str, Any]:
        cleaned = query.strip()
        if not cleaned:
            return {"answer": "Please ask a career, resume, or hiring question!", "sources": [], "grounded": False}

        # Check cache
        cache_key = hashlib.md5(cleaned.lower().encode()).hexdigest()
        cached = self._cache.get(cache_key)
        if cached:
            cached["cached"] = True
            return cached

        # Fast Greeting Path
        lower_q = cleaned.lower()
        if any(lower_q == g for g in ["hi", "hello", "hey", "help", "who are you"]):
            return {
                "answer": "Hello! I am your TalentFlow AI Career Coach. I can help optimize your resume for ATS, prep for technical interviews, or answer questions about open roles.",
                "sources": [], "grounded": False, "cached": False,
            }

        # Hybrid Retrieval
        retrieved = self._hybrid_search(cleaned, top_k=3)
        sources = [
            {"id": r["item"]["id"], "question": r["item"]["question"], "relevance_score": r["relevance"]}
            for r in retrieved
        ]

        # Try LLM synthesis
        llm_reply = self._call_llm(cleaned, retrieved)
        if llm_reply:
            result = {
                "answer": llm_reply,
                "sources": sources,
                "grounded": True,
                "llm_used": True,
                "cached": False,
            }
            self._cache.put(cache_key, result)
            return result

        # Graceful fallback: synthesize from retrieved KB content directly
        if retrieved:
            best_items = retrieved[:2]
            synthesized_parts = []
            for r in best_items:
                synthesized_parts.append(r["item"]["content"])
            fallback_answer = " Additionally, ".join(synthesized_parts)
            result = {
                "answer": f"Based on our knowledge base: {fallback_answer}",
                "sources": sources,
                "grounded": True,
                "llm_used": False,
                "cached": False,
            }
            self._cache.put(cache_key, result)
            return result

        return {
            "answer": "For best ATS and career outcomes, focus on tailoring your skills to specific job descriptions, highlighting quantifiable metrics, and keeping resume formatting clean and readable.",
            "sources": [], "grounded": False, "llm_used": False, "cached": False,
        }

    def _call_llm(self, query: str, context_items: List[Dict[str, Any]]) -> Optional[str]:
        token = settings.ai.hf_token
        if not token or not context_items:
            return None

        context_text = "\n".join([f"- {c['item']['content']}" for c in context_items])
        prompt = f"<s>[INST] You are TalentFlow AI Career Assistant. Answer the question using this context:\n{context_text}\n\nQuestion: {query} [/INST]"

        try:
            import requests
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
