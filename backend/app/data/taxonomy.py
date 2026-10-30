"""
TalentFlow AI — Data Taxonomy
================================
Controlled category taxonomy for resume classification and role normalization.

Populated based on the canonical categories discovered in data/raw/clean_resume_data.csv.
Provides mapping from alias names / variants to standard canonical category names.

IMPORTANT: This module is TRAINING INFRASTRUCTURE only.
It must never be imported by the production application at runtime.
"""

from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# CANONICAL ROLE TAXONOMY (24 Categories from clean_resume_data.csv)
# ---------------------------------------------------------------------------
CANONICAL_TAXONOMY: Dict[str, Dict] = {
    "ACCOUNTANT": {
        "aliases": ["Accounting", "Auditor", "Bookkeeper", "Certified Public Accountant", "CPA"],
        "keywords": ["accounting", "ledger", "audit", "tax", "balance sheet", "reconciliation", "cpa", "gaap", "financial reporting"],
        "ats_role": "Accountant",
        "description": "Financial accounting, auditing, bookkeeping, and tax preparation.",
    },
    "ADVOCATE": {
        "aliases": ["Legal Counsel", "Lawyer", "Attorney", "Legal Advisor", "Paralegal", "Jurist"],
        "keywords": ["litigation", "court", "legal", "advocate", "counsel", "pleadings", "contract law", "jurisprudence", "compliance"],
        "ats_role": "Advocate",
        "description": "Legal representation, litigation, advocacy, and regulatory compliance.",
    },
    "AGRICULTURE": {
        "aliases": ["Agriculturalist", "Agronomist", "Farming", "Horticulture", "Crop Specialist"],
        "keywords": ["agriculture", "farming", "crops", "agronomy", "soil", "harvest", "horticulture", "irrigation", "livestock"],
        "ats_role": "Agriculture Specialist",
        "description": "Agricultural science, agronomy, farm operations, and agribusiness.",
    },
    "APPAREL": {
        "aliases": ["Fashion Designer", "Garment Specialist", "Textile", "Clothing", "Fashion"],
        "keywords": ["apparel", "textile", "garment", "fashion", "pattern making", "fabric", "tailoring", "merchandising"],
        "ats_role": "Apparel & Fashion Specialist",
        "description": "Apparel design, textile manufacturing, and fashion merchandising.",
    },
    "ARTS": {
        "aliases": ["Artist", "Fine Arts", "Visual Arts", "Performing Arts", "Musician", "Sculptor"],
        "keywords": ["arts", "fine arts", "painting", "sculpture", "curation", "exhibition", "creative", "illustration", "music"],
        "ats_role": "Arts Specialist",
        "description": "Visual arts, performing arts, creative design, and cultural curation.",
    },
    "AUTOMOBILE": {
        "aliases": ["Automotive", "Automotive Engineer", "Vehicle Mechanic", "Automobile Specialist"],
        "keywords": ["automobile", "automotive", "engine", "vehicle", "chassis", "powertrain", "mechanic", "diagnostics"],
        "ats_role": "Automobile Engineer",
        "description": "Automotive engineering, vehicle diagnostics, maintenance, and mechanics.",
    },
    "AVIATION": {
        "aliases": ["Aerospace", "Flight Attendant", "Pilot", "Aviation Specialist", "Aircraft Maintenance"],
        "keywords": ["aviation", "aircraft", "flight", "pilot", "cabin crew", "aerospace", "avionics", "faa", "air traffic"],
        "ats_role": "Aviation Specialist",
        "description": "Flight operations, aircraft maintenance, aerospace engineering, and piloting.",
    },
    "BANKING": {
        "aliases": ["Banker", "Investment Banker", "Retail Banker", "Commercial Banking", "Credit Analyst"],
        "keywords": ["banking", "credit analysis", "loans", "mortgage", "teller", "underwriting", "wealth management", "treasury"],
        "ats_role": "Banking Specialist",
        "description": "Commercial, retail, and investment banking operations and credit management.",
    },
    "BPO": {
        "aliases": ["Call Center", "Customer Care Representative", "Business Process Outsourcing", "Customer Support"],
        "keywords": ["bpo", "call center", "customer support", "telecalling", "inbound", "outbound", "voice process", "chat support"],
        "ats_role": "BPO Specialist",
        "description": "Business process outsourcing, contact center operations, and client servicing.",
    },
    "BUSINESS-DEVELOPMENT": {
        "aliases": ["Business Development Manager", "BDM", "Business Developer", "Strategic Partnerships", "Account Executive"],
        "keywords": ["business development", "lead generation", "b2b", "revenue growth", "client acquisition", "partnerships", "pipeline"],
        "ats_role": "Business Development Specialist",
        "description": "B2B growth, strategic partnerships, account expansion, and lead conversion.",
    },
    "CHEF": {
        "aliases": ["Cook", "Sous Chef", "Head Chef", "Culinary Specialist", "Executive Chef", "Pastry Chef"],
        "keywords": ["chef", "culinary", "cooking", "kitchen", "menu planning", "food preparation", "sous chef", "catering", "haccp"],
        "ats_role": "Chef",
        "description": "Culinary arts, professional cooking, menu design, and kitchen operations.",
    },
    "CONSTRUCTION": {
        "aliases": ["Civil Construction", "Site Engineer", "Building Contractor", "Structural Worker"],
        "keywords": ["construction", "site supervisor", "concrete", "scaffolding", "building", "safety inspection", "contractor", "civil work"],
        "ats_role": "Construction Specialist",
        "description": "Building construction, structural site supervision, and safety management.",
    },
    "CONSULTANT": {
        "aliases": ["Management Consultant", "Strategy Consultant", "Business Consultant", "Advisory"],
        "keywords": ["consultant", "advisory", "strategy", "management consulting", "process optimization", "transformation", "client engagement"],
        "ats_role": "Consultant",
        "description": "Management and strategy consulting, organizational design, and business advisory.",
    },
    "DESIGNER": {
        "aliases": ["Graphic Designer", "UI/UX Designer", "Product Designer", "Visual Designer"],
        "keywords": ["designer", "ui", "ux", "graphic design", "figma", "photoshop", "illustrator", "typography", "wireframing", "branding"],
        "ats_role": "UI/UX Designer",
        "description": "Graphic, visual, product, and digital user interface/user experience design.",
    },
    "DIGITAL-MEDIA": {
        "aliases": ["Digital Marketing", "Social Media Specialist", "Content Creator", "SEO Specialist"],
        "keywords": ["digital media", "social media", "content marketing", "seo", "sem", "google analytics", "digital campaigns", "copywriting"],
        "ats_role": "Digital Media Specialist",
        "description": "Digital marketing, social media strategy, content creation, and search engine optimization.",
    },
    "ENGINEERING": {
        "aliases": ["Engineer", "Mechanical Engineer", "Electrical Engineer", "Civil Engineer"],
        "keywords": ["engineering", "cad", "solidworks", "matlab", "mechanical", "electrical", "civil", "structural", "prototyping"],
        "ats_role": "Engineer",
        "description": "General, mechanical, electrical, structural, and civil engineering.",
    },
    "FINANCE": {
        "aliases": ["Financial Analyst", "Corporate Finance", "Wealth Advisor", "Portfolio Manager"],
        "keywords": ["finance", "financial analysis", "valuation", "financial modeling", "forecasting", "budgeting", "equity", "investment"],
        "ats_role": "Financial Analyst",
        "description": "Financial modeling, corporate valuation, budgeting, forecasting, and investment analysis.",
    },
    "FITNESS": {
        "aliases": ["Personal Trainer", "Gym Instructor", "Fitness Coach", "Strength Coach", "Yoga Instructor"],
        "keywords": ["fitness", "personal training", "gym", "workout", "nutrition", "strength", "conditioning", "kinesiology", "exercise"],
        "ats_role": "Fitness Coach",
        "description": "Physical fitness training, athletic coaching, and exercise instruction.",
    },
    "HEALTHCARE": {
        "aliases": ["Medical Professional", "Nurse", "Healthcare Specialist", "Clinical Assistant", "Doctor"],
        "keywords": ["healthcare", "nursing", "patient care", "clinical", "hospital", "medical records", "ehr", "triage", "pharmacology"],
        "ats_role": "Healthcare Specialist",
        "description": "Nursing, clinical patient care, healthcare administration, and medical assistance.",
    },
    "HR": {
        "aliases": ["Human Resources", "HR Generalist", "HR Manager", "Talent Acquisition", "Recruiter", "People Operations"],
        "keywords": ["human resources", "hr", "recruitment", "onboarding", "employee relations", "benefits", "payroll", "compliance", "shrm"],
        "ats_role": "HR Manager",
        "description": "Human resources management, recruitment, talent acquisition, and employee relations.",
    },
    "INFORMATION-TECHNOLOGY": {
        "aliases": ["IT", "Software Engineer", "Software Developer", "IT Specialist", "DevOps", "Full Stack Developer", "Network Engineer"],
        "keywords": ["information technology", "software", "python", "java", "sql", "aws", "cloud", "react", "docker", "kubernetes", "networking"],
        "ats_role": "Software Engineer",
        "description": "Software development, cloud architecture, IT infrastructure, and systems administration.",
    },
    "PUBLIC-RELATIONS": {
        "aliases": ["PR Specialist", "Media Relations", "Communications Officer", "Publicist", "Corporate Communications"],
        "keywords": ["public relations", "pr", "press release", "media relations", "crisis communications", "spokesperson", "brand reputation"],
        "ats_role": "Public Relations Specialist",
        "description": "Media relations, corporate communications, reputation management, and public affairs.",
    },
    "SALES": {
        "aliases": ["Sales Representative", "Account Manager", "Sales Executive", "Inside Sales", "Outside Sales"],
        "keywords": ["sales", "quota", "closing", "crm", "salesforce", "cold calling", "negotiation", "account management", "prospecting"],
        "ats_role": "Sales Representative",
        "description": "Direct sales, account management, quota achievement, and customer negotiation.",
    },
    "TEACHER": {
        "aliases": ["Educator", "Instructor", "Professor", "Faculty", "Tutor", "Academic"],
        "keywords": ["teacher", "education", "curriculum", "classroom", "lesson planning", "pedagogy", "grading", "student development"],
        "ats_role": "Teacher / Educator",
        "description": "Classroom instruction, pedagogy, curriculum planning, and academic mentoring.",
    },
}


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def get_all_canonical_roles() -> List[str]:
    """Return the list of all canonical role names."""
    return list(CANONICAL_TAXONOMY.keys())


def get_aliases_for_role(role: str) -> List[str]:
    """Return known aliases for a canonical role name."""
    entry = CANONICAL_TAXONOMY.get(role, {})
    return entry.get("aliases", [])


def find_canonical(label: str, case_sensitive: bool = False) -> Optional[str]:
    """
    Find the canonical role for a given label (alias or canonical name).
    Returns the canonical role name, or None if not found.
    """
    check_label = label if case_sensitive else label.strip().lower()

    for canonical, info in CANONICAL_TAXONOMY.items():
        c = canonical if case_sensitive else canonical.lower()
        if check_label == c:
            return canonical

        for alias in info.get("aliases", []):
            a = alias if case_sensitive else alias.lower()
            if check_label == a:
                return canonical

    return None


def is_taxonomy_populated() -> bool:
    """Return True if the taxonomy has been populated with real data."""
    return len(CANONICAL_TAXONOMY) > 0


def taxonomy_status_message() -> str:
    """Return a human-readable status message about taxonomy readiness."""
    return f"Canonical Taxonomy loaded: {len(CANONICAL_TAXONOMY)} active professions"
