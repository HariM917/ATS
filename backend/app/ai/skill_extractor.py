"""
TalentFlow AI — Triple-Layer Skill Extractor & Categorizer
1. Exact & Regex match against 800+ skill taxonomy
2. Synonym & Abbreviation expansion
3. RapidFuzz fuzzy matching with domain classification
"""
import re
import logging
from typing import List, Dict, Set, Tuple, cast, Any
from rapidfuzz import fuzz, process

logger = logging.getLogger(__name__)

# Curated multi-domain taxonomy
SKILL_TAXONOMY: Dict[str, List[str]] = {
    "Languages": ["Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Rust", "SQL", "HTML", "CSS", "R", "PHP", "Ruby", "Swift", "Kotlin"],
    "Frameworks": ["React", "Angular", "Vue.js", "Node.js", "Express", "Django", "Flask", "FastAPI", "Spring Boot", "Next.js", "ASP.NET"],
    "Databases": ["PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "Elasticsearch", "Cassandra", "Oracle", "DynamoDB"],
    "Cloud & DevOps": ["AWS", "Azure", "GCP", "Docker", "Kubernetes", "CI/CD", "Terraform", "Jenkins", "Linux", "Git", "Ansible"],
    "AI & Data Science": ["Machine Learning", "Deep Learning", "NLP", "PyTorch", "TensorFlow", "Pandas", "NumPy", "Scikit-Learn", "Computer Vision", "LLM", "Data Analysis", "Tableau", "Power BI"],
    "Finance & Accounting": ["Accounting", "Financial Analysis", "Financial Reporting", "Financial Modeling", "Risk Analysis", "Excel", "Auditing", "Budgeting", "Tax Planning", "Banking Operations", "Treasury", "Bookkeeping"],
    "Business & Management": ["Project Management", "Agile", "Scrum", "Product Management", "Business Analysis", "Strategy", "Operations Management", "Stakeholder Management", "CRM"],
    "Marketing & Sales": ["Digital Marketing", "SEO", "Content Strategy", "Sales Management", "Lead Generation", "Market Research", "Brand Management", "Social Media Marketing"],
    "Design & Creative": ["UI/UX", "Figma", "Adobe Photoshop", "Graphic Design", "Wireframing", "Prototyping", "User Research"],
    "Engineering & Operations": ["AutoCAD", "SolidWorks", "MATLAB", "Supply Chain", "Logistics", "Quality Assurance", "Six Sigma", "Procurement"]
}

SKILL_SYNONYMS: Dict[str, str] = {
    "ml": "Machine Learning",
    "dl": "Deep Learning",
    "nlp": "Natural Language Processing",
    "k8s": "Kubernetes",
    "js": "JavaScript",
    "ts": "TypeScript",
    "py": "Python",
    "postgres": "PostgreSQL",
    "reactjs": "React",
    "nodejs": "Node.js",
    "pbi": "Power BI",
    "ui/ux": "UI/UX",
    "ui": "UI/UX",
    "ux": "UI/UX"
}

# Optional external taxonomy override if installed dynamically
try:
    import importlib.util
    if importlib.util.find_spec("ats_skills_dataset") is not None:
        _ext = __import__("ats_skills_dataset")
        SKILL_TAXONOMY = getattr(_ext, "SKILL_TAXONOMY", SKILL_TAXONOMY)
        SKILL_SYNONYMS = getattr(_ext, "SKILL_SYNONYMS", SKILL_SYNONYMS)
except Exception:
    pass

# Build flat lookups
ALL_SKILLS: List[str] = []
SKILL_TO_CATEGORY: Dict[str, str] = {}
SKILL_LOWER_MAP: Dict[str, str] = {}

for category, skills in SKILL_TAXONOMY.items():
    for skill in skills:
        ALL_SKILLS.append(skill)
        SKILL_TO_CATEGORY[skill] = category
        SKILL_LOWER_MAP[skill.lower()] = skill


def extract_skills(text: str) -> List[str]:
    """Extract all relevant technical skills from candidate resume or JD text."""
    if not text:
        return []

    found_skills: Set[str] = set()
    cleaned_text = text.lower()

    # Layer 1: Synonym & Abbreviation Word Matching
    words = set(re.findall(r'\b[a-zA-Z0-9\.\+#]+\b', cleaned_text))
    for word, target_skill in SKILL_SYNONYMS.items():
        if word in words:
            found_skills.add(target_skill)

    # Layer 2: Exact & Boundary Regex matching against Taxonomy
    for skill_lower, original_name in SKILL_LOWER_MAP.items():
        # Special escape for C++, C#, .NET
        escaped = re.escape(skill_lower)
        pattern = rf'(?:\b|\W){escaped}(?:\b|\W)'
        if re.search(pattern, cleaned_text):
            found_skills.add(original_name)

    # Layer 3: Fuzzy matching on section words (if skill list was sparse)
    if len(found_skills) < 3:
        for word in words:
            if len(word) >= 4:
                match = process.extractOne(
                    word,
                    ALL_SKILLS,
                    scorer=cast(Any, fuzz.ratio),
                    score_cutoff=92.0,
                )  # type: ignore
                if match:
                    found_skills.add(match[0])

    return sorted(list(found_skills))


def categorize_skills(skills: List[str]) -> Dict[str, List[str]]:
    """Group extracted skills into structured domains."""
    categorized: Dict[str, List[str]] = {}
    for skill in skills:
        cat = SKILL_TO_CATEGORY.get(skill, "Other Skills")
        if cat not in categorized:
            categorized[cat] = []
        categorized[cat].append(skill)
    return categorized
