"""
TalentFlow AI — Resume Quality & ATS Document Formatting Analyzer.
Deterministic, multi-criteria document analysis inspecting layout, readability, typography,
section structure, bullet quality, grammar/spelling, consistency, and parser compatibility
across PDF, DOCX, and TXT files.
"""

import os
import re
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Common typos in technical resumes
COMMON_RESUME_TYPOS = {
    "seperate": "separate",
    "definately": "definitely",
    "managment": "management",
    "implemeted": "implemented",
    "responsibilites": "responsibilities",
    "responsiblities": "responsibilities",
    "databse": "database",
    "developement": "development",
    "experiance": "experience",
    "experince": "experience",
    "knowlege": "knowledge",
    "achived": "achieved",
    "maintainance": "maintenance",
    "tehnical": "technical",
    "enviornment": "environment",
    "enviroment": "environment",
    "reponsible": "responsible",
    "commited": "committed",
    "succesful": "successful",
    "oppurtunity": "opportunity",
    "calender": "calendar",
    "refering": "referring",
}

# Present-tense action verbs in past experience
PRESENT_TO_PAST_VERBS = {
    "develop": "developed",
    "create": "created",
    "manage": "managed",
    "build": "built",
    "design": "designed",
    "implement": "implemented",
    "lead": "led",
    "test": "tested",
    "write": "wrote",
    "maintain": "maintained",
    "analyze": "analyzed",
    "coordinate": "coordinated",
    "configure": "configured",
    "optimize": "optimized",
    "engineer": "engineered",
    "spearhead": "spearheaded",
}

# Strong action verbs commonly looked for in high-impact ATS resumes
STRONG_ACTION_VERBS = {
    "accelerated", "accomplished", "achieved", "acquired", "adapted", "administered",
    "advised", "analyzed", "architected", "automated", "built", "centralized",
    "championed", "collaborated", "constructed", "coordinated", "crafted", "created",
    "decreased", "delivered", "deployed", "designed", "developed", "directed",
    "eliminated", "enabled", "engineered", "established", "executed", "expanded",
    "facilitated", "formulated", "founded", "generated", "guided", "implemented",
    "improved", "increased", "initiated", "innovated", "inspected", "integrated",
    "introduced", "launched", "lead", "led", "managed", "maximized", "mentored",
    "migrated", "minimized", "modernized", "negotiated", "optimized", "orchestrated",
    "overhauled", "oversaw", "partnered", "pioneered", "planned", "produced",
    "programmed", "promoted", "reduced", "reengineered", "resolved", "restructured",
    "revamped", "scaled", "simplified", "spearheaded", "standardized", "streamlined",
    "strengthened", "supervised", "surpassed", "trained", "transformed", "unified",
    "upgraded", "validated", "yielded"
}

# Standard sections expected in ATS resumes
EXPECTED_SECTIONS = [
    {
        "key": "contact",
        "name": "Contact Information",
        "weight": 15,
        "patterns": [r'\b(email|phone|linkedin|github|portfolio|contact)\b', r'[\w\.-]+@[\w\.-]+\.\w+']
    },
    {
        "key": "experience",
        "name": "Work Experience / History",
        "weight": 25,
        "patterns": [r'\b(experience|work experience|employment history|work history|professional experience|career history)\b']
    },
    {
        "key": "skills",
        "name": "Skills & Competencies",
        "weight": 25,
        "patterns": [r'\b(skills|technical skills|core competencies|technologies|key skills|proficiencies)\b']
    },
    {
        "key": "education",
        "name": "Education & Qualifications",
        "weight": 20,
        "patterns": [r'\b(education|academic background|qualifications|degrees?|university|college|bachelor|master|phd)\b']
    },
    {
        "key": "summary",
        "name": "Summary / Objective",
        "weight": 10,
        "patterns": [r'\b(professional summary|executive summary|career summary|summary|objective|career objective|about me)\b']
    },
    {
        "key": "projects",
        "name": "Projects / Certifications",
        "weight": 5,
        "patterns": [r'\b(projects|key projects|certifications|certificates|licenses|achievements|publications)\b']
    }
]


class ResumeQualityAnalyzer:
    """Performs deep deterministic ATS formatting and document quality evaluation on resumes."""

    @classmethod
    def analyze_resume(cls, file_path: Optional[str] = None, raw_text: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze a resume from its disk path (if available) or raw text.
        Returns comprehensive formatting metrics, 8 granular subscores, detected issues, and recommendations.
        """
        text = raw_text or ""
        doc_type = "unknown"
        page_count = 1
        has_file = file_path and os.path.exists(file_path)

        pdf_meta = {
            "is_scanned": False,
            "has_tables": False,
            "table_count": 0,
            "multi_column": False,
            "fonts_detected": [],
            "font_count": 0,
            "tiny_fonts": False,
            "oversized_fonts": False,
        }

        if has_file and file_path:
            ext = os.path.splitext(file_path)[1].lower()
            doc_type = ext.replace(".", "")

            if ext == ".pdf":
                pdf_meta, extracted_text = cls._inspect_pdf(file_path)
                if not text and extracted_text:
                    text = extracted_text
                page_count = pdf_meta.get("page_count", 1)

            elif ext in [".docx", ".doc"]:
                docx_meta, extracted_text = cls._inspect_docx(file_path)
                if not text and extracted_text:
                    text = extracted_text
                page_count = docx_meta.get("estimated_pages", 1)

            elif ext == ".txt":
                if not text:
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            text = f.read()
                    except Exception as e:
                        logger.warning(f"Failed to read TXT resume: {e}")
                doc_type = "txt"

        # Text-based structural and writing analysis
        clean_text_words = text.split()
        if not text.strip() or len(clean_text_words) < 5:
            return {
                "resume_text_available": False,
                "error": "Resume text could not be extracted or is empty. Please upload a valid readable PDF, DOCX, or text file.",
                "overall": 0,
                "formatting_score": 0,
                "grade": "F",
                "is_ats_friendly": False,
                "document_type": doc_type,
                "page_count": page_count,
                "word_count": len(clean_text_words),
                "character_count": len(text),
                "subscores": {
                    "ats_readability": 0,
                    "formatting_layout": 0,
                    "section_structure": 0,
                    "bullet_quality": 0,
                    "grammar_spelling": 0,
                    "typography": 0,
                    "consistency": 0,
                    "contact_information": 0,
                    "structure": 0,
                    "layout": 0,
                    "section_organization": 0,
                    "document_integrity": 0,
                },
                "ats_readability": 0,
                "formatting_layout": 0,
                "section_structure": 0,
                "bullet_quality": 0,
                "grammar_spelling": 0,
                "typography": 0,
                "consistency": 0,
                "contact_information": 0,
                "detected_sections": [],
                "missing_sections": ["Contact Info", "Professional Summary", "Technical Skills", "Work Experience", "Education"],
                "issues": [{
                    "severity": "critical",
                    "problem": "Unreadable or Empty Document Text",
                    "evidence": "No extractable text layers found in uploaded file.",
                    "why_it_matters": "Applicant Tracking Systems (ATS) cannot parse image-only, scanned, or corrupted files, leading to automatic rejection.",
                    "recommendation": "Save and export your resume as a clean, text-based PDF or DOCX file directly from Google Docs or MS Word."
                }],
                "good_practices": [],
                "recommendations": ["Re-upload a selectable text-based PDF or DOCX file."],
                "grammar_issues": [],
                "spelling_issues": [],
                "metrics": {
                    "bullet_point_count": 0,
                    "bullet_styles_count": 0,
                    "has_contact_email": False,
                    "has_contact_phone": False,
                    "has_linkedin": False,
                    "has_github": False,
                    "action_verb_count": 0,
                    "measurable_results_count": 0,
                    "word_count": len(clean_text_words),
                    "character_count": len(text),
                }
            }

        text_analysis = cls._analyze_text_content(text)

        # Compute Granular Subscores (0 - 100)
        subscores = cls._compute_subscores(pdf_meta, text_analysis, doc_type, page_count)

        # Overall weighted formatting score (0 - 100)
        overall_score = round(
            subscores["ats_readability"] * 0.15 +
            subscores["formatting_layout"] * 0.15 +
            subscores["section_structure"] * 0.15 +
            subscores["bullet_quality"] * 0.15 +
            subscores["typography"] * 0.10 +
            subscores["grammar_spelling"] * 0.15 +
            subscores["consistency"] * 0.10 +
            subscores["contact_information"] * 0.05
        )
        overall_score = max(10, min(100, overall_score))

        # Assign letter grade
        grade = cls._assign_grade(overall_score)

        # Collect detailed structured issues, good practices, and recommendations
        issues, good_practices, recommendations = cls._generate_feedback(
            pdf_meta, text_analysis, subscores, doc_type, page_count
        )

        return {
            "resume_text_available": True,
            "overall": overall_score,
            "formatting_score": overall_score,
            "grade": grade,
            "is_ats_friendly": overall_score >= 70 and not pdf_meta.get("is_scanned", False),
            "document_type": doc_type,
            "page_count": page_count,
            "word_count": text_analysis["word_count"],
            "character_count": text_analysis["character_count"],
            "subscores": subscores,
            # Flattened subscore aliases for direct API access
            "ats_readability": subscores["ats_readability"],
            "formatting_layout": subscores["formatting_layout"],
            "section_structure": subscores["section_structure"],
            "bullet_quality": subscores["bullet_quality"],
            "grammar_spelling": subscores["grammar_spelling"],
            "typography": subscores["typography"],
            "consistency": subscores["consistency"],
            "contact_information": subscores["contact_information"],
            "detected_sections": text_analysis["detected_sections"],
            "missing_sections": text_analysis["missing_sections"],
            "issues": issues,
            "good_practices": good_practices,
            "recommendations": recommendations,
            "grammar_issues": text_analysis["grammar_issues"],
            "spelling_issues": text_analysis["spelling_issues"],
            "metrics": {
                "bullet_point_count": text_analysis["bullet_count"],
                "bullet_styles_count": len(text_analysis["bullet_symbols_found"]),
                "action_verb_count": text_analysis["action_verbs_found_count"],
                "measurable_results_count": text_analysis["metrics_count"],
                "has_contact_email": text_analysis["has_email"],
                "has_contact_phone": text_analysis["has_phone"],
                "has_linkedin": text_analysis["has_linkedin"],
                "has_github": text_analysis["has_github"],
                "multi_column_detected": pdf_meta["multi_column"],
                "tables_detected": pdf_meta["has_tables"],
                "is_scanned": pdf_meta["is_scanned"],
            }
        }

    @classmethod
    def _inspect_pdf(cls, file_path: str) -> Tuple[Dict[str, Any], str]:
        """Inspect PDF internal structure via PyMuPDF (fitz)."""
        meta = {
            "page_count": 1,
            "is_scanned": False,
            "has_tables": False,
            "table_count": 0,
            "multi_column": False,
            "fonts_detected": [],
            "font_count": 0,
            "tiny_fonts": False,
            "oversized_fonts": False,
        }
        all_text = []

        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            meta["page_count"] = doc.page_count
            total_images = 0
            fonts_set = set()
            multi_col_signals = 0

            for page_idx in range(doc.page_count):
                page = doc[page_idx]
                page_text = page.get_text() or ""
                all_text.append(page_text)

                # Check images
                imgs = page.get_images()
                total_images += len(imgs)

                # Check tables
                try:
                    tables = page.find_tables()
                    if tables and len(tables.tables) > 0:
                        meta["has_tables"] = True
                        meta["table_count"] += len(tables.tables)
                except Exception:
                    pass

                # Inspect font spans and block positions
                try:
                    pdict = page.get_text("dict")
                    page_width = page.rect.width
                    blocks = pdict.get("blocks", [])
                    x_mid = page_width / 2.0

                    left_blocks = 0
                    right_blocks = 0

                    for b in blocks:
                        if "lines" in b:
                            bbox = b.get("bbox", [0, 0, 0, 0])
                            # Check column positioning
                            if bbox[2] < (x_mid + 20) and bbox[0] < x_mid:
                                left_blocks += 1
                            elif bbox[0] > (x_mid - 20) and bbox[2] > x_mid:
                                right_blocks += 1

                            for l in b["lines"]:
                                for s in l.get("spans", []):
                                    fname = s.get("font", "")
                                    fsize = s.get("size", 10)
                                    if fname:
                                        clean_font = fname.split("+")[-1].replace("-", " ")
                                        fonts_set.add(clean_font)
                                    if fsize < 8.0:
                                        meta["tiny_fonts"] = True
                                    if fsize > 26.0:
                                        meta["oversized_fonts"] = True

                    if left_blocks >= 2 and right_blocks >= 2:
                        multi_col_signals += 1
                except Exception as font_err:
                    logger.debug(f"Font inspection skipped: {font_err}")

            doc.close()

            full_extracted = "\n".join(all_text)
            meta["fonts_detected"] = sorted(list(fonts_set))[:8]
            meta["font_count"] = len(fonts_set)
            meta["multi_column"] = multi_col_signals >= 1

            # Scanned document detection: has images but fewer than 60 words
            word_count = len(full_extracted.split())
            if word_count < 60 and total_images > 0:
                meta["is_scanned"] = True

            return meta, full_extracted

        except Exception as e:
            logger.warning(f"Error inspecting PDF with PyMuPDF: {e}")
            return meta, "\n".join(all_text)

    @classmethod
    def _inspect_docx(cls, file_path: str) -> Tuple[Dict[str, Any], str]:
        """Inspect DOCX document metadata and extract text."""
        meta = {
            "estimated_pages": 1,
            "has_tables": False,
            "table_count": 0,
            "multi_column": False,
            "fonts_detected": [],
            "font_count": 1,
            "is_scanned": False,
        }
        text = ""
        try:
            import docx2txt
            text = docx2txt.process(file_path) or ""
            words = len(text.split())
            meta["estimated_pages"] = max(1, round(words / 400.0))
        except Exception as e:
            logger.warning(f"Error processing DOCX: {e}")

        return meta, text

    @classmethod
    def _analyze_text_content(cls, text: str) -> Dict[str, Any]:
        """Examines the raw text for sections, bullet points, metrics, contact info, grammar, and typos."""
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        words = text.split()
        word_count = len(words)
        char_count = len(text)

        # Contact info
        has_email = bool(re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text))
        has_phone = bool(re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text))
        has_linkedin = bool(re.search(r'linkedin\.com/in/|linkedin:\s*@?[\w\-]+', text, re.IGNORECASE))
        has_github = bool(re.search(r'github\.com/|github:\s*@?[\w\-]+', text, re.IGNORECASE))

        # Detect sections
        detected_sections = []
        missing_sections = []
        for sec in EXPECTED_SECTIONS:
            found = False
            for pat in sec["patterns"]:
                if re.search(pat, text, re.IGNORECASE):
                    found = True
                    break
            if found:
                detected_sections.append(sec["name"])
            else:
                missing_sections.append(sec["name"])

        # Bullet point detection & style analysis
        bullet_count = 0
        bullet_chars = ("•", "-", "*", "–", "—", "▪", "▫", "►", "✓")
        bullet_symbols_found = set()
        long_bullets_count = 0
        bullet_lines = []

        for line in lines:
            first_char = line[0] if line else ""
            if first_char in bullet_chars or re.match(r'^\d+\.\s+', line):
                bullet_count += 1
                if first_char in bullet_chars:
                    bullet_symbols_found.add(first_char)
                bullet_lines.append(line)
                if len(line.split()) > 45:
                    long_bullets_count += 1

        # Action verbs
        text_lower_tokens = set(re.findall(r'\b[a-z]{4,}\b', text.lower()))
        matched_verbs = text_lower_tokens.intersection(STRONG_ACTION_VERBS)

        # Quantifiable metrics
        metric_matches = re.findall(
            r'(\b\d+(\.\d+)?%|\$\d+[\d,]*(\.\d+)?[kmbKMB]?|\b\d+[\d,]*\s*(users|clients|candidates|requests|queries|downloads|revenue|savings|dollars|percent|growth))',
            text
        )
        metrics_count = len(metric_matches)

        # Wall of text (dense paragraphs without bullets)
        long_paragraphs = 0
        for block in text.split("\n\n"):
            p_words = len(block.strip().split())
            if p_words > 65 and not any(block.strip().startswith(c) for c in bullet_chars):
                long_paragraphs += 1

        # Grammar & Spelling checks
        spelling_issues = []
        words_clean = [re.sub(r'[^\w]', '', w.lower()) for w in words]
        for w in words_clean:
            if w in COMMON_RESUME_TYPOS:
                corrected = COMMON_RESUME_TYPOS[w]
                spelling_issues.append({"word": w, "suggested": corrected})

        grammar_issues = []
        # Check repeated consecutive words e.g. "in in", "the the"
        repeated_word_matches = re.finditer(r'\b([a-zA-Z]{2,})\s+\1\b', text, re.IGNORECASE)
        for m in repeated_word_matches:
            dup = m.group(1)
            grammar_issues.append({
                "type": "duplicate_word",
                "current": f"{dup} {dup}",
                "suggested": dup,
                "detail": f"Duplicate word '{dup}' detected."
            })

        # Check for present tense verbs starting bullets in past experience
        in_experience_section = False
        for line in lines:
            line_lower = line.lower()
            if any(h in line_lower for h in ["experience", "employment", "work history"]):
                in_experience_section = True
            elif any(h in line_lower for h in ["education", "skills", "certifications", "projects"]):
                in_experience_section = False

            if in_experience_section:
                # Strip bullet prefix
                clean_l = re.sub(r'^[•\-\*▪▫►✓\d\.]+\s*', '', line).strip()
                tokens = clean_l.split()
                if tokens:
                    first_token = tokens[0].lower()
                    if first_token in PRESENT_TO_PAST_VERBS:
                        suggested_past = PRESENT_TO_PAST_VERBS[first_token]
                        snippet = clean_l[:45] + ("..." if len(clean_l) > 45 else "")
                        grammar_issues.append({
                            "type": "tense_inconsistency",
                            "current": snippet,
                            "suggested": f"{suggested_past.capitalize()} {snippet[len(first_token)+1:]}".strip(),
                            "detail": f"Experience bullet starts with present-tense verb '{first_token}'. Prefer past-tense '{suggested_past}'."
                        })
                        if len(grammar_issues) >= 3:
                            break

        # Date format consistency
        date_formats_found = set()
        if re.search(r'\b(0[1-9]|1[0-2])\/\d{4}\b', text):
            date_formats_found.add("MM/YYYY")
        if re.search(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b', text, re.IGNORECASE):
            date_formats_found.add("Month YYYY")
        if re.search(r'\b\d{4}\s*[-–—]\s*\d{4}\b', text):
            date_formats_found.add("YYYY - YYYY")

        return {
            "word_count": word_count,
            "character_count": char_count,
            "line_count": len(lines),
            "has_email": has_email,
            "has_phone": has_phone,
            "has_linkedin": has_linkedin,
            "has_github": has_github,
            "detected_sections": detected_sections,
            "missing_sections": missing_sections,
            "bullet_count": bullet_count,
            "bullet_symbols_found": bullet_symbols_found,
            "long_bullets_count": long_bullets_count,
            "action_verbs_found": sorted(list(matched_verbs)),
            "action_verbs_found_count": len(matched_verbs),
            "metrics_count": metrics_count,
            "long_paragraphs": long_paragraphs,
            "spelling_issues": spelling_issues[:4],
            "grammar_issues": grammar_issues[:4],
            "date_formats_found": date_formats_found,
        }

    @classmethod
    def _compute_subscores(
        cls,
        pdf_meta: Dict[str, Any],
        text_analysis: Dict[str, Any],
        doc_type: str,
        page_count: int
    ) -> Dict[str, int]:
        """Computes 8 granular 0-100 subscores across real detected document properties."""

        # 1. ATS Readability
        readability = 85
        wc = text_analysis["word_count"]
        if wc < 150:
            readability -= 45
        elif wc < 300:
            readability -= 20
        elif wc > 1500:
            readability -= 20

        if text_analysis["long_paragraphs"] > 2:
            readability -= 15
        elif text_analysis["long_paragraphs"] == 1:
            readability -= 5

        if text_analysis["bullet_count"] >= 8:
            readability += 15
        elif text_analysis["bullet_count"] == 0:
            readability -= 25

        ats_readability = max(10, min(100, readability))

        # 2. Formatting & Layout
        layout_score = 90
        if pdf_meta.get("multi_column", False):
            layout_score -= 20
        if pdf_meta.get("has_tables", False):
            layout_score -= 15
        if pdf_meta.get("is_scanned", False):
            layout_score = 10
        if page_count > 2:
            layout_score -= 15
        formatting_layout = max(15, min(100, layout_score))

        # 3. Section Structure
        sec_score = 40
        if "Contact Information" in text_analysis["detected_sections"]:
            sec_score += 15
        if "Work Experience / History" in text_analysis["detected_sections"]:
            sec_score += 25
        if "Skills & Competencies" in text_analysis["detected_sections"]:
            sec_score += 25
        if "Education & Qualifications" in text_analysis["detected_sections"]:
            sec_score += 15
        if "Summary / Objective" in text_analysis["detected_sections"]:
            sec_score += 10
        section_structure = max(15, min(100, sec_score))

        # 4. Bullet Quality
        bullet_score = 80
        if text_analysis["bullet_count"] == 0:
            bullet_score = 25
        elif text_analysis["bullet_count"] < 4:
            bullet_score = 55
        elif text_analysis["bullet_count"] >= 8:
            bullet_score += 15

        if len(text_analysis["bullet_symbols_found"]) > 1:
            bullet_score -= 15
        if text_analysis["long_bullets_count"] > 2:
            bullet_score -= 10
        bullet_quality = max(20, min(100, bullet_score))

        # 5. Typography
        type_score = 90
        if pdf_meta.get("font_count", 0) > 4:
            type_score -= 20
        if pdf_meta.get("tiny_fonts", False):
            type_score -= 20
        if pdf_meta.get("oversized_fonts", False):
            type_score -= 10
        typography = max(20, min(100, type_score))

        # 6. Grammar & Spelling
        gram_score = 92
        gram_score -= len(text_analysis["spelling_issues"]) * 12
        gram_score -= len(text_analysis["grammar_issues"]) * 10
        grammar_spelling = max(20, min(100, gram_score))

        # 7. Consistency
        cons_score = 88
        if len(text_analysis["bullet_symbols_found"]) > 1:
            cons_score -= 15
        if len(text_analysis["date_formats_found"]) > 1:
            cons_score -= 15
        if pdf_meta.get("font_count", 0) > 3:
            cons_score -= 10
        consistency = max(25, min(100, cons_score))

        # 8. Contact Information
        contact_score = 60
        if text_analysis["has_email"]:
            contact_score += 20
        if text_analysis["has_phone"]:
            contact_score += 15
        if text_analysis["has_linkedin"] or text_analysis["has_github"]:
            contact_score += 5
        contact_information = max(20, min(100, contact_score))

        return {
            "ats_readability": ats_readability,
            "formatting_layout": formatting_layout,
            "section_structure": section_structure,
            "bullet_quality": bullet_quality,
            "typography": typography,
            "grammar_spelling": grammar_spelling,
            "consistency": consistency,
            "contact_information": contact_information,
            # Backward-compatible subscore aliases
            "structure": section_structure,
            "layout": formatting_layout,
            "section_organization": section_structure,
            "document_integrity": ats_readability,
        }

    @classmethod
    def _assign_grade(cls, score: int) -> str:
        if score >= 90:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 60:
            return "C"
        return "Needs Improvement"

    @classmethod
    def _generate_feedback(
        cls,
        pdf_meta: Dict[str, Any],
        text_analysis: Dict[str, Any],
        subscores: Dict[str, int],
        doc_type: str,
        page_count: int
    ) -> Tuple[List[Dict[str, str]], List[str], List[str]]:
        """Generates detailed structured issues with evidence/why_it_matters, good practices, and actionable recommendations."""
        issues: List[Dict[str, str]] = []
        good_practices: List[str] = []
        recommendations: List[str] = []

        # 1. Scanned / OCR Check
        if pdf_meta.get("is_scanned", False):
            issues.append({
                "severity": "critical",
                "problem": "Unreadable scanned document",
                "evidence": f"Resume contains {page_count} pages with images but under 60 selectable text words.",
                "why_it_matters": "Applicant tracking systems cannot parse scanned raster images without OCR, resulting in automatic rejection.",
                "recommendation": "Export directly to a digital PDF from Word, Google Docs, or LaTeX with selectable text."
            })
            recommendations.append("Export directly to a digital PDF with selectable text rather than scanning a printout.")
        else:
            good_practices.append("Resume text is selectable and machine-readable")

        # 2. Layout & Columns
        if pdf_meta.get("multi_column", False):
            issues.append({
                "severity": "warning",
                "problem": "Multi-column layout detected",
                "evidence": "Text blocks span across multiple horizontal bounding boxes on the same line band.",
                "why_it_matters": "Many legacy ATS parsers read lines strictly horizontally across columns, scrambling employment timelines and skill contexts.",
                "recommendation": "Adopt a clean, single-column layout for guaranteed linear ATS readability."
            })
            recommendations.append("Switch to a single-column layout to prevent ATS reading order issues.")
        else:
            good_practices.append("Single-column flow detected — optimal for linear ATS scanning engines")

        # 3. Tables
        if pdf_meta.get("has_tables", False):
            issues.append({
                "severity": "info",
                "problem": "Table formatting detected",
                "evidence": f"Found {pdf_meta.get('table_count', 1)} table structure(s) in document.",
                "why_it_matters": "Nested tables can confuse parsing engines when extracting skill-to-job mappings.",
                "recommendation": "Replace tabular layouts with standard bulleted lists and clean dividers."
            })
            recommendations.append("Use standard bullet points instead of tables to present skills or work history.")
        else:
            good_practices.append("No problematic tables detected")

        # 4. Bullet Style & Consistency
        bullet_syms = text_analysis["bullet_symbols_found"]
        if len(bullet_syms) > 1:
            sym_list = ", ".join(f"'{s}'" for s in bullet_syms)
            issues.append({
                "severity": "warning",
                "problem": "Inconsistent bullet styles",
                "evidence": f"{len(bullet_syms)} different bullet styles detected ({sym_list}).",
                "why_it_matters": "Mixed bullet styles create visual clutter and can indicate poor document hygiene.",
                "recommendation": "Use one consistent bullet character (e.g. •) throughout the entire resume."
            })
            recommendations.append("Standardize on a single bullet point character (e.g., •) across all sections.")
        elif text_analysis["bullet_count"] >= 6:
            good_practices.append(f"Consistent bullet points utilized ({text_analysis['bullet_count']} bullets found)")
        elif text_analysis["bullet_count"] == 0:
            issues.append({
                "severity": "warning",
                "problem": "Missing bullet points",
                "evidence": "Zero bullet characters detected; responsibilities appear as dense paragraphs.",
                "why_it_matters": "Dense text reduces recruiter scannability and makes ATS keyword matching harder.",
                "recommendation": "Convert paragraph blocks into 1-2 line action-oriented bullet points."
            })
            recommendations.append("Convert dense paragraphs into concise, action-oriented bullet points.")

        # 5. Date Format Consistency
        date_formats = text_analysis["date_formats_found"]
        if len(date_formats) > 1:
            issues.append({
                "severity": "warning",
                "problem": "Inconsistent date formatting",
                "evidence": f"Multiple date syntax styles detected ({', '.join(date_formats)}).",
                "why_it_matters": "Inconsistent date patterns can confuse automated parsing of employment dates and duration.",
                "recommendation": "Standardize all work experience dates to one format (e.g. 'MM/YYYY - MM/YYYY' or 'Month YYYY - Present')."
            })
            recommendations.append("Standardize date formats across all experience entries.")
        else:
            good_practices.append("Experience dates are clearly structured")

        # 6. Grammar & Tense Issues
        if text_analysis["grammar_issues"]:
            for gi in text_analysis["grammar_issues"]:
                issues.append({
                    "severity": "warning",
                    "problem": "Possible grammar/tense issue",
                    "evidence": f'Current: "{gi["current"]}"',
                    "why_it_matters": "Inconsistent tenses or duplicate words detract from document professionalism.",
                    "recommendation": f'Suggested: "{gi["suggested"]}"'
                })
                recommendations.append(f'Revise grammar: Change "{gi["current"]}" to "{gi["suggested"]}".')
        else:
            good_practices.append("No obvious grammar issues detected")

        # 7. Spelling Issues
        if text_analysis["spelling_issues"]:
            for si in text_analysis["spelling_issues"]:
                issues.append({
                    "severity": "warning",
                    "problem": "Spelling mistake detected",
                    "evidence": f'Found "{si["word"]}" in resume text.',
                    "why_it_matters": "Spelling errors in technical keywords can prevent keyword matching in ATS databases.",
                    "recommendation": f'Correct "{si["word"]}" to "{si["suggested"]}".'
                })
                recommendations.append(f'Correct spelling of "{si["word"]}" to "{si["suggested"]}".')
        else:
            good_practices.append("No obvious spelling errors detected")

        # 8. Contact Information
        if not text_analysis["has_email"]:
            issues.append({
                "severity": "critical",
                "problem": "Missing contact email",
                "evidence": "No valid email address found in document header or body.",
                "why_it_matters": "ATS parsers require an email address to create or link candidate profiles.",
                "recommendation": "Add your primary email address prominently at the top of your resume."
            })
            recommendations.append("Ensure your primary email address is prominently visible at the top of page 1.")
        else:
            good_practices.append("Contact information is machine-readable and contains valid email")

        if not text_analysis["has_phone"]:
            issues.append({
                "severity": "info",
                "problem": "Missing phone number",
                "evidence": "No telephone number detected.",
                "why_it_matters": "Recruiters frequently use phone numbers for initial screening contact.",
                "recommendation": "Include a standard phone number with country/area code."
            })

        # 9. Typography
        if pdf_meta.get("font_count", 0) > 4:
            issues.append({
                "severity": "info",
                "problem": "Too many fonts detected",
                "evidence": f"{pdf_meta.get('font_count')} different fonts detected in PDF.",
                "why_it_matters": "Overly varied typography creates inconsistent visual hierarchy.",
                "recommendation": "Use at most 1-2 standard, legible typefaces (e.g. Arial, Calibri, Helvetica)."
            })
            recommendations.append("Limit typography to 1-2 clean, professional fonts.")
        elif pdf_meta.get("font_count", 0) in [1, 2, 3]:
            good_practices.append("Consistent primary font detected")

        # 10. Document Length
        if page_count > 2:
            issues.append({
                "severity": "warning",
                "problem": "Excessive document length",
                "evidence": f"Document length is {page_count} pages.",
                "why_it_matters": "Recruiters spend an average of 6-8 seconds scanning resumes; 1-2 pages is the industry standard.",
                "recommendation": "Condense older or less relevant responsibilities to fit within 1-2 pages."
            })
            recommendations.append("Trim older responsibilities to condense document length to 1-2 pages.")
        elif page_count in [1, 2]:
            good_practices.append(f"Ideal document length ({page_count} page{'s' if page_count > 1 else ''})")

        # 11. Section Headings
        for sec in text_analysis["missing_sections"]:
            severity = "warning" if sec in ["Work Experience / History", "Skills & Competencies"] else "info"
            issues.append({
                "severity": severity,
                "problem": f"Missing standard section: {sec}",
                "evidence": f"Could not detect a clear heading for '{sec}'.",
                "why_it_matters": f"ATS parsers search for standard '{sec}' headings to categorize candidate qualifications.",
                "recommendation": f"Add a distinct, clearly capitalized section heading for '{sec}'."
            })
            recommendations.append(f"Add a distinct section heading for '{sec}'.")

        if "Work Experience / History" in text_analysis["detected_sections"]:
            good_practices.append("Standard work experience section clearly detected")
        if "Skills & Competencies" in text_analysis["detected_sections"]:
            good_practices.append("Standard technical skills section clearly detected")

        return issues, good_practices, recommendations
