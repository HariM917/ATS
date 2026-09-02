"""
TalentFlow AI — Text Cleaning, Normalization, and Chunking Utilities
Shared preprocessing pipeline for resume parsing, skill extraction, and RAG document processing.
"""
import re
import unicodedata
from typing import List, Optional


def clean_text(text: str) -> str:
    """Normalize unicode, strip control chars, collapse whitespace."""
    if not text:
        return ""
    # Normalize Unicode (e.g., smart quotes → standard)
    text = unicodedata.normalize("NFKD", text)
    # Remove control characters except newlines and tabs
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    # Normalize whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    # Collapse multiple blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def normalize_for_matching(text: str) -> str:
    """Lowercase and strip punctuation for matching comparisons."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^\w\s\.\+\#]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def chunk_text(text: str, max_chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks for embedding or RAG retrieval.
    
    Args:
        text: Input text to chunk
        max_chunk_size: Maximum characters per chunk
        overlap: Number of overlapping characters between chunks
    
    Returns:
        List of text chunks
    """
    if not text:
        return []
    
    # Split by paragraphs first
    paragraphs = re.split(r'\n\s*\n', text)
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        if len(current_chunk) + len(para) + 1 <= max_chunk_size:
            current_chunk = f"{current_chunk}\n{para}" if current_chunk else para
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            # Handle paragraphs larger than max_chunk_size
            if len(para) > max_chunk_size:
                words = para.split()
                current_chunk = ""
                for word in words:
                    if len(current_chunk) + len(word) + 1 <= max_chunk_size:
                        current_chunk = f"{current_chunk} {word}" if current_chunk else word
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = word
            else:
                current_chunk = para
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    # Add overlap between chunks
    if overlap > 0 and len(chunks) > 1:
        overlapped = [chunks[0]]
        for i in range(1, len(chunks)):
            prev_tail = chunks[i - 1][-overlap:] if len(chunks[i - 1]) >= overlap else chunks[i - 1]
            overlapped.append(f"{prev_tail} {chunks[i]}")
        return overlapped
    
    return chunks


def extract_email(text: str) -> Optional[str]:
    """Extract first email address from text."""
    match = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', text)
    return match.group(0).lower() if match else None


def extract_phone(text: str) -> Optional[str]:
    """Extract first phone number from text."""
    match = re.search(r'[\+]?[\d\s\-\(\)]{10,15}', text)
    return match.group(0).strip() if match else None


def extract_urls(text: str) -> List[str]:
    """Extract URLs (LinkedIn, GitHub, portfolio) from text."""
    pattern = r'https?://[^\s\)\]\>]+'
    return re.findall(pattern, text)
