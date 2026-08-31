"""
TalentFlow AI — Multi-Layer Document & Resume Parser
Layers: PyMuPDF -> pdfplumber -> pdfminer -> text sanitizer
"""
import os
import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def extract_text_from_file(file_path: str) -> str:
    """Extract raw text from PDF, DOCX, or TXT with multi-layer fallback."""
    if not file_path or not os.path.exists(file_path):
        logger.warning(f"[PARSER] File not found: {file_path}")
        return ""

    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return _extract_pdf_layers(file_path)
    elif ext in (".docx", ".doc"):
        return _extract_docx(file_path)
    elif ext in (".txt", ".md"):
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read().strip()
        except Exception as e:
            logger.error(f"[PARSER] Failed reading TXT file {file_path}: {e}")
            return ""
    else:
        logger.warning(f"[PARSER] Unsupported extension '{ext}' for file {file_path}")
        return ""


def _extract_pdf_layers(file_path: str) -> str:
    """Layer 1: PyMuPDF (fitz) -> Layer 2: pdfplumber -> Layer 3: pdfminer."""
    # Layer 1: PyMuPDF
    try:
        import fitz
        doc = fitz.open(file_path)
        text_parts = []
        for page in doc:
            t = page.get_text()
            if t:
                text_parts.append(t)
        doc.close()
        full_text = "\n".join(text_parts).strip()
        if len(full_text) >= 100:
            return full_text
    except Exception as e:
        logger.debug(f"[PARSER] Layer 1 (fitz) failed: {e}")

    # Layer 2: pdfplumber
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text_parts.append(t)
        full_text = "\n".join(text_parts).strip()
        if len(full_text) >= 100:
            return full_text
    except Exception as e:
        logger.debug(f"[PARSER] Layer 2 (pdfplumber) failed: {e}")

    # Layer 3: pdfminer
    try:
        from pdfminer.high_level import extract_text as miner_extract
        text = miner_extract(file_path)
        if text and len(text.strip()) >= 50:
            return text.strip()
    except Exception as e:
        logger.debug(f"[PARSER] Layer 3 (pdfminer) failed: {e}")

    return ""


def _extract_docx(file_path: str) -> str:
    try:
        import docx2txt
        text = docx2txt.process(file_path)
        return (text or "").strip()
    except Exception as e:
        logger.error(f"[PARSER] docx2txt failed on {file_path}: {e}")
        return ""


def extract_sections(text: str) -> Dict[str, str]:
    """Segment resume text into structured sections: skills, experience, education, projects."""
    if not text:
        return {}

    section_keywords = {
        "skills": ["skills", "technical skills", "technologies", "competencies", "core competencies", "tools"],
        "experience": ["experience", "work experience", "employment", "professional experience", "work history"],
        "education": ["education", "academic background", "qualifications", "academics"],
        "projects": ["projects", "personal projects", "academic projects", "key projects"],
    }

    # Find section header line locations
    lines = text.splitlines()
    section_map = {}
    current_section = "general"
    current_lines = []

    for line in lines:
        cleaned_line = line.strip().lower()
        matched = False
        for sec_name, synonyms in section_keywords.items():
            if any(cleaned_line.startswith(syn) or cleaned_line == syn or f"{syn}:" in cleaned_line for syn in synonyms):
                if current_lines:
                    section_map[current_section] = "\n".join(current_lines).strip()
                current_section = sec_name
                current_lines = []
                matched = True
                break
        if not matched:
            current_lines.append(line)

    if current_lines:
        section_map[current_section] = "\n".join(current_lines).strip()

    return section_map
