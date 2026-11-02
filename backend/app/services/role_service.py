"""
TalentFlow AI — Role Catalog & Secondary Specific Role Specialization Service.
Controls the authoritative taxonomy of specific job roles under the 22 occupational classes.
Provides specific role classification for candidate resumes and recruiter job definitions.
"""
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from ..models.role import RoleCatalog

logger = logging.getLogger(__name__)

# Authoritative catalog of specific roles grouped by 22 Occupational Classes
DEFAULT_ROLE_CATALOG: List[Dict[str, Any]] = [
    # 1. INFORMATION-TECHNOLOGY
    {
        "name": "Software Engineer",
        "slug": "software-engineer",
        "occupational_class": "INFORMATION-TECHNOLOGY",
        "description": "Designs, develops, tests, and optimizes scalable software systems, core algorithms, and robust microservices.",
        "aliases": ["Software Developer", "Applications Developer", "Programmer", "Computer Programmer", "Systems Developer"],
        "required_skills_default": ["Python", "Java", "C++", "Algorithms", "Data Structures", "System Design", "Git", "REST APIs", "Docker"],
        "experience_level": "Mid-Level"
    },
    {
        "name": "Software Developer",
        "slug": "software-developer",
        "occupational_class": "INFORMATION-TECHNOLOGY",
        "description": "Designs, writes, tests, and maintains full-lifecycle software applications, algorithmic solutions, and core services.",
        "aliases": ["Software Engineer", "Applications Developer", "Programmer", "Computer Programmer"],
        "required_skills_default": ["Python", "Java", "SQL", "Git", "REST APIs", "Data Structures", "Algorithms", "Docker"],
        "experience_level": "Mid-Level"
    },
    {
        "name": "Machine Learning Engineer",
        "slug": "machine-learning-engineer",
        "occupational_class": "INFORMATION-TECHNOLOGY",
        "description": "Designs, trains, and deploys scalable machine learning models and AI pipelines.",
        "aliases": ["ML Engineer", "AI/ML Engineer", "Machine Learning Specialist"],
        "required_skills_default": ["Python", "PyTorch", "TensorFlow", "Scikit-Learn", "Docker", "MLOps", "Transformers"],
        "experience_level": "Mid-Senior"
    },
    {
        "name": "AI Engineer",
        "slug": "ai-engineer",
        "occupational_class": "INFORMATION-TECHNOLOGY",
        "description": "Develops enterprise generative AI, LLM applications, RAG pipelines, and agentic workflows.",
        "aliases": ["Artificial Intelligence Engineer", "GenAI Engineer", "LLM Developer"],
        "required_skills_default": ["Python", "LangChain", "OpenAI API", "Hugging Face", "Vector Databases", "Prompt Engineering"],
        "experience_level": "Mid-Senior"
    },
    {
        "name": "Data Scientist",
        "slug": "data-scientist",
        "occupational_class": "INFORMATION-TECHNOLOGY",
        "description": "Extracts actionable insights and predictive signals from structured and unstructured data.",
        "aliases": ["Predictive Modeler", "Data Science Specialist"],
        "required_skills_default": ["Python", "R", "SQL", "Pandas", "NumPy", "Statistical Modeling", "Data Visualization"],
        "experience_level": "Mid-Senior"
    },
    {
        "name": "Backend Developer",
        "slug": "backend-developer",
        "occupational_class": "INFORMATION-TECHNOLOGY",
        "description": "Architects reliable backend servers, APIs, databases, and microservices.",
        "aliases": ["Backend Engineer", "Server-Side Developer"],
        "required_skills_default": ["Python", "FastAPI", "Flask", "Django", "PostgreSQL", "Redis", "REST APIs", "Docker"],
        "experience_level": "Mid-Level"
    },
    {
        "name": "Frontend Web Developer",
        "slug": "frontend-web-developer",
        "occupational_class": "INFORMATION-TECHNOLOGY",
        "description": "Builds modern, responsive web user interfaces and interactive single-page applications.",
        "aliases": ["Front-End Developer", "Frontend Developer", "Frontend Engineer", "UI Developer", "Web Developer"],
        "required_skills_default": ["React", "TypeScript", "JavaScript", "HTML5", "CSS3", "Tailwind CSS", "Redux", "Vite", "Next.js"],
        "experience_level": "Mid-Level"
    },
    {
        "name": "Full Stack Developer",
        "slug": "full-stack-developer",
        "occupational_class": "INFORMATION-TECHNOLOGY",
        "description": "Delivers end-to-end web applications combining robust backend services with modern frontends.",
        "aliases": ["Full Stack Engineer", "Web Applications Engineer"],
        "required_skills_default": ["React", "Node.js", "Python", "TypeScript", "PostgreSQL", "REST APIs", "Docker"],
        "experience_level": "Mid-Senior"
    },
    {
        "name": "Mobile App Developer",
        "slug": "mobile-app-developer",
        "occupational_class": "INFORMATION-TECHNOLOGY",
        "description": "Develops native and cross-platform mobile apps across iOS and Android ecosystems.",
        "aliases": ["iOS Developer", "Android Developer", "Mobile Engineer", "App Developer"],
        "required_skills_default": ["React Native", "Flutter", "Swift", "Kotlin", "iOS", "Android", "REST APIs", "Mobile UI"],
        "experience_level": "Mid-Level"
    },
    {
        "name": "DevOps Engineer",
        "slug": "devops-engineer",
        "occupational_class": "INFORMATION-TECHNOLOGY",
        "description": "Automates cloud infrastructure, continuous deployment pipelines, and operational reliability.",
        "aliases": ["Site Reliability Engineer", "SRE", "Cloud Operations Engineer"],
        "required_skills_default": ["Kubernetes", "Docker", "CI/CD", "Terraform", "AWS", "Linux", "GitHub Actions"],
        "experience_level": "Mid-Senior"
    },
    {
        "name": "Cloud Architect",
        "slug": "cloud-architect",
        "occupational_class": "INFORMATION-TECHNOLOGY",
        "description": "Designs scalable, high-availability enterprise cloud platforms and security governance.",
        "aliases": ["Cloud Solutions Architect", "Enterprise Cloud Architect"],
        "required_skills_default": ["AWS", "Azure", "GCP", "Microservices", "System Architecture", "Security", "Cost Optimization"],
        "experience_level": "Senior"
    },
    {
        "name": "Cloud Engineer",
        "slug": "cloud-engineer",
        "occupational_class": "INFORMATION-TECHNOLOGY",
        "description": "Implements and maintains cloud infrastructure, container orchestration, and serverless architectures.",
        "aliases": ["Cloud Infrastructure Engineer", "Cloud Systems Engineer"],
        "required_skills_default": ["AWS", "Azure", "GCP", "Terraform", "Docker", "Kubernetes", "Linux", "Cloud Architecture"],
        "experience_level": "Mid-Level"
    },
    {
        "name": "Database Developer",
        "slug": "database-developer",
        "occupational_class": "INFORMATION-TECHNOLOGY",
        "description": "Develops database schemas, indexes, stored procedures, ETL data pipelines, and queries.",
        "aliases": ["Database Engineer", "SQL Developer", "Data Warehouse Developer"],
        "required_skills_default": ["SQL", "PostgreSQL", "MySQL", "Database Design", "Stored Procedures", "Query Optimization", "ETL", "NoSQL"],
        "experience_level": "Mid-Level"
    },
    {
        "name": "Data Architect",
        "slug": "data-architect",
        "occupational_class": "INFORMATION-TECHNOLOGY",
        "description": "Architects enterprise data warehouses, lakes, ETL pipelines, and streaming infrastructure.",
        "aliases": ["Enterprise Data Architect", "Big Data Architect", "Data Pipeline Architect"],
        "required_skills_default": ["Data Modeling", "ETL", "Snowflake", "AWS Redshift", "SQL", "Apache Spark", "Big Data", "Data Governance"],
        "experience_level": "Senior"
    },
    {
        "name": "Cybersecurity Engineer",
        "slug": "cybersecurity-engineer",
        "occupational_class": "INFORMATION-TECHNOLOGY",
        "description": "Protects organizational assets through threat modeling, vulnerability defense, and compliance.",
        "aliases": ["Security Engineer", "InfoSec Specialist", "Cyber Security Analyst"],
        "required_skills_default": ["Network Security", "Penetration Testing", "SIEM", "Incident Response", "Firewalls", "SOC"],
        "experience_level": "Mid-Senior"
    },
    {
        "name": "Network Security Analyst",
        "slug": "network-security-analyst",
        "occupational_class": "INFORMATION-TECHNOLOGY",
        "description": "Monitors network perimeters, analyzes intrusion telemetry, and manages defensive security controls.",
        "aliases": ["Network Defense Analyst", "InfoSec Analyst"],
        "required_skills_default": ["Network Security", "Firewalls", "Wireshark", "IDS/IPS", "TCP/IP", "Linux", "VPN", "Cisco"],
        "experience_level": "Mid-Level"
    },
    {
        "name": "SOC Analyst",
        "slug": "soc-analyst",
        "occupational_class": "INFORMATION-TECHNOLOGY",
        "description": "Investigates security events, triages alerts, and executes incident containment protocols in 24/7 SOC environments.",
        "aliases": ["Security Operations Center Analyst", "Incident Responder"],
        "required_skills_default": ["SIEM", "Splunk", "Incident Response", "Threat Analysis", "SOC", "Vulnerability Scanning", "Log Analysis"],
        "experience_level": "Mid-Level"
    },
    {
        "name": "IT Analyst",
        "slug": "it-analyst",
        "occupational_class": "INFORMATION-TECHNOLOGY",
        "description": "Evaluates enterprise business requirements, implements technology systems, and optimizes IT workflows.",
        "aliases": ["IT Systems Analyst", "Technology Analyst", "Systems Analyst"],
        "required_skills_default": ["SQL", "Systems Analysis", "Requirements Gathering", "Data Warehousing", "Agile", "Excel", "JIRA"],
        "experience_level": "Mid-Level"
    },
    {
        "name": "Agile Project Manager",
        "slug": "agile-project-manager",
        "occupational_class": "INFORMATION-TECHNOLOGY",
        "description": "Leads software engineering teams using Scrum and Kanban to deliver software sprints on time.",
        "aliases": ["Scrum Master", "Technical Project Manager", "Agile Coach"],
        "required_skills_default": ["Agile Methodologies", "Scrum", "JIRA", "Sprint Planning", "Kanban", "Stakeholder Management", "SDLC"],
        "experience_level": "Mid-Senior"
    },
    {
        "name": "Data Analyst",
        "slug": "data-analyst",
        "occupational_class": "INFORMATION-TECHNOLOGY",
        "description": "Transforms business data into clear dashboards, visual KPIs, and operational reports.",
        "aliases": ["BI Analyst", "Business Intelligence Specialist"],
        "required_skills_default": ["SQL", "Tableau", "Power BI", "Excel", "Data Cleaning", "Analytics"],
        "experience_level": "Entry-Mid"
    },
    {
        "name": "QA Automation Engineer",
        "slug": "qa-automation-engineer",
        "occupational_class": "INFORMATION-TECHNOLOGY",
        "description": "Designs automated testing harnesses to guarantee software quality, stability, and speed.",
        "aliases": ["Software Quality Assurance", "SDET", "Test Automation Engineer"],
        "required_skills_default": ["Selenium", "Cypress", "PyTest", "Jest", "CI/CD Integration", "Test Automation"],
        "experience_level": "Mid-Level"
    },
    {
        "name": "Automation Test Engineer",
        "slug": "automation-test-engineer",
        "occupational_class": "INFORMATION-TECHNOLOGY",
        "description": "Builds and executes automated UI and API test frameworks for continuous integration.",
        "aliases": ["SDET", "Automated QA Specialist", "Test Engineer"],
        "required_skills_default": ["Selenium", "Cypress", "Python", "Test Automation", "CI/CD", "PyTest", "API Testing", "JIRA"],
        "experience_level": "Mid-Level"
    },

    # 2. ENGINEERING
    {
        "name": "Mechanical Engineer",
        "slug": "mechanical-engineer",
        "occupational_class": "ENGINEERING",
        "description": "Designs and tests mechanical devices, thermal systems, and manufacturing machinery.",
        "aliases": ["Mechanical Systems Engineer", "Thermal Systems Engineer"],
        "required_skills_default": ["SolidWorks", "AutoCAD", "Thermodynamics", "FEA Analysis", "Prototyping"],
        "experience_level": "Mid-Level"
    },
    {
        "name": "Mechanical Design Engineer",
        "slug": "mechanical-design-engineer",
        "occupational_class": "ENGINEERING",
        "description": "Designs mechanical mechanisms, 3D CAD modeling, structural FEA simulation, and precision tooling.",
        "aliases": ["CAD Design Engineer", "Mechanical Product Designer", "Electro-Mechanical Engineer"],
        "required_skills_default": ["SolidWorks", "AutoCAD", "GD&T", "FEA Analysis", "DFM/DFA", "3D CAD Modeling", "Prototyping", "Materials Science"],
        "experience_level": "Mid-Level"
    },
    {
        "name": "Electrical Engineer",
        "slug": "electrical-engineer",
        "occupational_class": "ENGINEERING",
        "description": "Develops electrical systems, circuit architectures, power networks, and control boards.",
        "aliases": ["Power Systems Engineer", "Electronics Designer"],
        "required_skills_default": ["Circuit Design", "PCB Layout", "Embedded Systems", "MATLAB", "Microcontrollers"],
        "experience_level": "Mid-Level"
    },
    {
        "name": "Civil Engineer",
        "slug": "civil-engineer",
        "occupational_class": "ENGINEERING",
        "description": "Plans and manages infrastructure projects including transport systems, bridges, and facilities.",
        "aliases": ["Structural Engineer", "Site Civil Engineer"],
        "required_skills_default": ["AutoCAD", "Structural Analysis", "Project Management", "Site Planning", "Geotechnical"],
        "experience_level": "Mid-Senior"
    },

    # 3. FINANCE
    {
        "name": "Financial Analyst",
        "slug": "financial-analyst",
        "occupational_class": "FINANCE",
        "description": "Analyzes financial performance, corporate valuations, and market forecasting models.",
        "aliases": ["Corporate Finance Analyst", "FP&A Analyst"],
        "required_skills_default": ["Financial Modeling", "Excel", "Valuation", "Budgeting", "Forecasting", "Variance Analysis"],
        "experience_level": "Mid-Level"
    },
    {
        "name": "Investment Analyst",
        "slug": "investment-analyst",
        "occupational_class": "FINANCE",
        "description": "Conducts portfolio research, equity valuation, and asset allocation strategy.",
        "aliases": ["Equity Research Analyst", "Portfolio Analyst"],
        "required_skills_default": ["Equity Research", "DCF Modeling", "Portfolio Management", "Capital Markets", "Bloomberg"],
        "experience_level": "Mid-Senior"
    },

    # 4. ACCOUNTANT
    {
        "name": "Certified Public Accountant",
        "slug": "certified-public-accountant",
        "occupational_class": "ACCOUNTANT",
        "description": "Oversees financial record integrity, tax compliance, and regulatory audit filings.",
        "aliases": ["Senior Accountant", "Corporate Controller", "CPA"],
        "required_skills_default": ["General Ledger", "GAAP", "Tax Compliance", "Financial Reporting", "Auditing"],
        "experience_level": "Senior"
    },
    {
        "name": "Tax Planner",
        "slug": "tax-planner",
        "occupational_class": "ACCOUNTANT",
        "description": "Specializes in corporate tax strategy, IRS compliance, tax minimization planning, and audit preparation.",
        "aliases": ["Tax Consultant", "Corporate Tax Specialist", "Tax Advisor"],
        "required_skills_default": ["Tax Strategy", "Corporate Tax Compliance", "IRS Regulations", "Tax Preparation", "Financial Planning", "GAAP"],
        "experience_level": "Mid-Senior"
    },
    {
        "name": "Auditor",
        "slug": "auditor",
        "occupational_class": "ACCOUNTANT",
        "description": "Examines corporate accounts and internal controls to ensure statutory and fiduciary accuracy.",
        "aliases": ["Internal Auditor", "Tax Auditor"],
        "required_skills_default": ["Internal Controls", "Risk Assessment", "Audit Procedures", "Compliance", "Excel"],
        "experience_level": "Mid-Level"
    },

    # 5. HEALTHCARE
    {
        "name": "Registered Nurse",
        "slug": "registered-nurse",
        "occupational_class": "HEALTHCARE",
        "description": "Provides patient diagnosis support, clinical treatment administration, and patient care management.",
        "aliases": ["Staff Nurse", "Clinical Nurse"],
        "required_skills_default": ["Patient Care", "BLS/ACLS", "Medication Administration", "Clinical Documentation", "Triage"],
        "experience_level": "Mid-Level"
    },
    {
        "name": "Clinical Psychologist",
        "slug": "clinical-psychologist",
        "occupational_class": "HEALTHCARE",
        "description": "Assesses, diagnoses, and treats mental health conditions using evidence-based cognitive and behavioral therapies.",
        "aliases": ["Licensed Psychologist", "Mental Health Clinician", "Behavioral Health Specialist"],
        "required_skills_default": ["Psychological Assessment", "Cognitive Behavioral Therapy (CBT)", "Clinical Diagnosis", "Patient Counseling", "Mental Health Treatment", "Case Documentation"],
        "experience_level": "Senior"
    },
    {
        "name": "Clinical Research Coordinator",
        "slug": "clinical-research-coordinator",
        "occupational_class": "HEALTHCARE",
        "description": "Coordinates clinical drug trials, patient consent protocols, and regulatory trial integrity.",
        "aliases": ["Clinical Trial Manager", "Medical Researcher"],
        "required_skills_default": ["GCP Guidelines", "Clinical Protocols", "Data Management", "Regulatory Compliance", "Patient Advocacy"],
        "experience_level": "Mid-Senior"
    },

    # 6. DESIGNER
    {
        "name": "UI/UX Designer",
        "slug": "ui-ux-designer",
        "occupational_class": "DESIGNER",
        "description": "Crafts user journeys, interactive wireframes, design systems, and responsive product interfaces.",
        "aliases": ["Product Designer", "User Experience Architect"],
        "required_skills_default": ["Figma", "Design Systems", "Prototyping", "User Research", "Wireframing", "Usability Testing"],
        "experience_level": "Mid-Senior"
    },
    {
        "name": "Product Brand Manager",
        "slug": "product-brand-manager",
        "occupational_class": "DESIGNER",
        "description": "Directs brand identity systems, product positioning aesthetics, visual guidelines, and design asset cohesion.",
        "aliases": ["Brand Design Lead", "Brand Identity Manager", "Creative Brand Strategist"],
        "required_skills_default": ["Brand Strategy", "Design Systems", "Visual Identity", "Figma", "Adobe Creative Suite", "Brand Guidelines", "Market Positioning"],
        "experience_level": "Mid-Senior"
    },
    {
        "name": "Graphic Designer",
        "slug": "graphic-designer",
        "occupational_class": "DESIGNER",
        "description": "Develops visual marketing collateral, corporate branding, digital assets, and print media.",
        "aliases": ["Visual Designer", "Brand Designer"],
        "required_skills_default": ["Adobe Photoshop", "Illustrator", "Typography", "Branding", "Layout Design"],
        "experience_level": "Mid-Level"
    },

    # 7. HR
    {
        "name": "Technical Recruiter",
        "slug": "technical-recruiter",
        "occupational_class": "HR",
        "description": "Sources, evaluates, and closes technical candidates across engineering and data disciplines.",
        "aliases": ["Talent Acquisition Specialist", "Recruiter"],
        "required_skills_default": ["Candidate Sourcing", "Interviewing", "ATS Systems", "LinkedIn Recruiter", "Offer Negotiation"],
        "experience_level": "Mid-Level"
    },
    {
        "name": "HR Business Partner",
        "slug": "hr-business-partner",
        "occupational_class": "HR",
        "description": "Aligns human resources strategy, talent development, and organizational policy with business goals.",
        "aliases": ["People Operations Manager", "HR Generalist"],
        "required_skills_default": ["Employee Relations", "Performance Management", "Talent Development", "HR Compliance", "Organizational Design"],
        "experience_level": "Senior"
    },

    # 8. SALES
    {
        "name": "Account Executive",
        "slug": "account-executive",
        "occupational_class": "SALES",
        "description": "Drives enterprise revenue by demonstrating software value, qualifying deals, and closing contracts.",
        "aliases": ["Enterprise Sales Representative", "Sales Director"],
        "required_skills_default": ["B2B Sales", "Deal Closing", "Pipeline Management", "CRM (Salesforce)", "Solution Selling"],
        "experience_level": "Mid-Senior"
    },
    {
        "name": "Sales Account Manager",
        "slug": "sales-account-manager",
        "occupational_class": "SALES",
        "description": "Manages enterprise client portfolios, secures contract renewals, identifies upsell opportunities, and drives retention.",
        "aliases": ["Key Account Manager", "Client Relationship Manager", "Commercial Account Executive"],
        "required_skills_default": ["Account Management", "Client Retention", "Contract Renewal", "Upselling", "CRM (Salesforce)", "Executive Negotiation"],
        "experience_level": "Mid-Level"
    },
    {
        "name": "Regional Sales Director",
        "slug": "regional-sales-director",
        "occupational_class": "SALES",
        "description": "Leads regional sales teams, forecasts territory revenues, executes enterprise commercial strategy, and closes high-value deals.",
        "aliases": ["Director of Sales", "Territory Sales Leader", "VP of Regional Sales"],
        "required_skills_default": ["Sales Leadership", "Territory Management", "Revenue Forecasting", "Enterprise Sales Strategy", "Executive Pitching", "Team Coaching"],
        "experience_level": "Director"
    },

    # 9. BUSINESS-DEVELOPMENT
    {
        "name": "Business Development Manager",
        "slug": "business-development-manager",
        "occupational_class": "BUSINESS-DEVELOPMENT",
        "description": "Identifies strategic growth opportunities, builds strategic partner networks, and expands market reach.",
        "aliases": ["Partnerships Manager", "Strategic Growth Lead"],
        "required_skills_default": ["Strategic Partnerships", "Market Research", "Contract Negotiation", "Revenue Growth", "Networking"],
        "experience_level": "Senior"
    },
    {
        "name": "Logistics Analyst",
        "slug": "logistics-analyst",
        "occupational_class": "BUSINESS-DEVELOPMENT",
        "description": "Analyzes supply chain distribution, optimizes freight carrier routing, minimizes landed costs, and streamlines supply chain operations.",
        "aliases": ["Supply Chain Analyst", "Distribution Specialist", "Logistics Operations Analyst"],
        "required_skills_default": ["Supply Chain Optimization", "Logistics Management", "Inventory Control", "ERP (SAP/Oracle)", "Data Analysis", "Freight Routing", "Cost Modeling"],
        "experience_level": "Mid-Level"
    },

    # 10. DIGITAL-MEDIA
    {
        "name": "Digital Marketing Strategist",
        "slug": "digital-marketing-strategist",
        "occupational_class": "DIGITAL-MEDIA",
        "description": "Develops multichannel digital campaigns, performance marketing funnels, and brand visibility.",
        "aliases": ["Performance Marketer", "Growth Marketing Specialist"],
        "required_skills_default": ["SEO/SEM", "Google Analytics", "Content Strategy", "Social Media Advertising", "Conversion Optimization"],
        "experience_level": "Mid-Level"
    },

    # 11. CONSULTANT
    {
        "name": "Management Consultant",
        "slug": "management-consultant",
        "occupational_class": "CONSULTANT",
        "description": "Advises executive leadership on operational efficiency, digital transformation, and restructuring.",
        "aliases": ["Strategy Consultant", "Business Advisory Specialist"],
        "required_skills_default": ["Problem Solving", "Strategy Frameworks", "Executive Presentation", "Process Optimization", "Change Management"],
        "experience_level": "Mid-Senior"
    },

    # 12. TEACHER
    {
        "name": "Computer Science Educator",
        "slug": "computer-science-educator",
        "occupational_class": "TEACHER",
        "description": "Instructs students in computer programming, algorithmic problem solving, and software engineering.",
        "aliases": ["STEM Instructor", "Lecturer"],
        "required_skills_default": ["Curriculum Design", "Pedagogy", "Programming Instruction", "Assessment Design", "Mentoring"],
        "experience_level": "Mid-Level"
    },

    # 13. PUBLIC-RELATIONS
    {
        "name": "Public Relations Specialist",
        "slug": "public-relations-specialist",
        "occupational_class": "PUBLIC-RELATIONS",
        "description": "Manages public reputation, corporate communications, media inquiries, and press releases.",
        "aliases": ["Communications Specialist", "Media Relations Manager"],
        "required_skills_default": ["Press Releases", "Media Relations", "Crisis Communications", "Corporate Storytelling", "Brand Messaging"],
        "experience_level": "Mid-Level"
    },
    {
        "name": "Event Coordinator",
        "slug": "event-coordinator",
        "occupational_class": "PUBLIC-RELATIONS",
        "description": "Plans, organizes, and coordinates large-scale corporate conferences, PR product launches, press events, and partner summits.",
        "aliases": ["Corporate Event Planner", "PR Events Specialist", "Event Producer"],
        "required_skills_default": ["Event Planning", "Vendor Negotiation", "Budget Management", "Public Relations", "Logistics Coordination", "Media Coordination", "Run of Show"],
        "experience_level": "Mid-Level"
    },

    # 14. CHEF
    {
        "name": "Executive Chef",
        "slug": "executive-chef",
        "occupational_class": "CHEF",
        "description": "Directs culinary kitchen operations, menu creation, food safety standards, and culinary teams.",
        "aliases": ["Head Chef", "Culinary Director"],
        "required_skills_default": ["Menu Development", "Culinary Arts", "Kitchen Operations", "Food Safety (HACCP)", "Cost Control"],
        "experience_level": "Senior"
    },

    # 15. AVIATION
    {
        "name": "Aviation Operations Specialist",
        "slug": "aviation-operations-specialist",
        "occupational_class": "AVIATION",
        "description": "Oversees flight scheduling, air traffic safety compliance, and aviation ground logistics.",
        "aliases": ["Flight Dispatcher", "Aviation Coordinator"],
        "required_skills_default": ["FAA Regulations", "Flight Dispatch", "Crew Scheduling", "Aviation Safety Management", "Logistics"],
        "experience_level": "Mid-Level"
    },

    # 16. BANKING
    {
        "name": "Commercial Loan Officer",
        "slug": "commercial-loan-officer",
        "occupational_class": "BANKING",
        "description": "Evaluates credit underwriting, capital lending requirements, and client relationship banking.",
        "aliases": ["Relationship Banker", "Credit Underwriter"],
        "required_skills_default": ["Credit Underwriting", "Lending Compliance", "Commercial Banking", "Financial Statement Analysis", "Risk Assessment"],
        "experience_level": "Mid-Level"
    },

    # 17. ADVOCATE
    {
        "name": "Corporate Legal Counsel",
        "slug": "corporate-legal-counsel",
        "occupational_class": "ADVOCATE",
        "description": "Advises corporations on commercial transactions, contract law, regulatory compliance, and risk.",
        "aliases": ["Staff Attorney", "Legal Counsel"],
        "required_skills_default": ["Contract Drafting", "Legal Research", "Corporate Governance", "Regulatory Compliance", "Dispute Resolution"],
        "experience_level": "Mid-Senior"
    },

    # 18. AGRICULTURE
    {
        "name": "Precision Agronomist",
        "slug": "precision-agronomist",
        "occupational_class": "AGRICULTURE",
        "description": "Optimizes crop yields, soil conservation, and modern sustainable agricultural technology.",
        "aliases": ["Agricultural Scientist", "Farm Operations Lead"],
        "required_skills_default": ["Crop Management", "Soil Science", "Precision Farming", "Irrigation Systems", "AgTech Software"],
        "experience_level": "Mid-Level"
    },

    # 19. APPAREL
    {
        "name": "Fashion Apparel Designer",
        "slug": "fashion-apparel-designer",
        "occupational_class": "APPAREL",
        "description": "Creates garment designs, technical tech packs, fabric sourcing, and seasonal apparel lines.",
        "aliases": ["Textile Designer", "Apparel Product Developer"],
        "required_skills_default": ["Garment Construction", "Tech Packs", "Textile Sourcing", "Pattern Making", "Trend Analysis"],
        "experience_level": "Mid-Level"
    },

    # 20. ARTS
    {
        "name": "Creative Art Director",
        "slug": "creative-art-director",
        "occupational_class": "ARTS",
        "description": "Guides creative conceptual vision across multimedia exhibitions, productions, and artistic campaigns.",
        "aliases": ["Visual Artist", "Lead Concept Artist"],
        "required_skills_default": ["Art Direction", "Concept Art", "Creative Storyboarding", "Visual Aesthetics", "Project Coordination"],
        "experience_level": "Senior"
    },

    # 21. CONSTRUCTION
    {
        "name": "Construction Project Manager",
        "slug": "construction-project-manager",
        "occupational_class": "CONSTRUCTION",
        "description": "Directs commercial and residential building projects, subcontractor schedules, and OSHA safety.",
        "aliases": ["General Superintendent", "Site Project Engineer"],
        "required_skills_default": ["Construction Management", "Cost Estimating", "OSHA Compliance", "Subcontractor Coordination", "Blueprint Reading"],
        "experience_level": "Senior"
    },

    # 22. FITNESS
    {
        "name": "Performance Strength Coach",
        "slug": "performance-strength-coach",
        "occupational_class": "FITNESS",
        "description": "Designs personalized athletic training programs, biometric monitoring, and injury rehabilitation.",
        "aliases": ["Certified Personal Trainer", "Exercise Physiologist"],
        "required_skills_default": ["Kinesiology", "Exercise Programming", "Biometrics", "Nutritional Coaching", "Injury Prevention (CSCS)"],
        "experience_level": "Mid-Level"
    }
]


class RoleService:
    """Manages role catalog access, database sync, and secondary specific role classification."""

    def __init__(self, db: Session):
        self.db = db

    def sync_role_catalog(self) -> None:
        """Syncs all roles from DEFAULT_ROLE_CATALOG into the database, inserting new roles and updating existing ones."""
        try:
            existing_roles = {r.slug: r for r in self.db.query(RoleCatalog).all()}
            for item in DEFAULT_ROLE_CATALOG:
                slug = item["slug"]
                if slug in existing_roles:
                    role = existing_roles[slug]
                    setattr(role, "name", item["name"])
                    setattr(role, "occupational_class", item["occupational_class"])
                    setattr(role, "description", item["description"])
                    setattr(role, "aliases", item["aliases"])
                    setattr(role, "required_skills_default", item["required_skills_default"])
                    setattr(role, "experience_level", item.get("experience_level", "Mid-Level"))
                    setattr(role, "active", True)
                else:
                    role = RoleCatalog(
                        name=item["name"],
                        slug=item["slug"],
                        occupational_class=item["occupational_class"],
                        description=item["description"],
                        aliases=item["aliases"],
                        required_skills_default=item["required_skills_default"],
                        experience_level=item.get("experience_level", "Mid-Level"),
                        active=True
                    )
                    self.db.add(role)
            self.db.flush()
        except Exception as e:
            logger.warning(f"[ROLES] Catalog sync warning: {e}")

    def seed_catalog_if_empty(self) -> None:
        """Seed or sync the database role catalog."""
        self.sync_role_catalog()

    def list_roles(
        self,
        occupational_class: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List active roles filtered by occupational class and optional text query."""
        self.sync_role_catalog()
        query = self.db.query(RoleCatalog).filter(RoleCatalog.active == True)

        if occupational_class:
            clean_class = occupational_class.strip().upper()
            query = query.filter(RoleCatalog.occupational_class == clean_class)

        roles = query.all()

        results = [r.to_dict() for r in roles]

        if search:
            s = search.strip().lower()
            filtered = []
            for r in results:
                name_match = s in r["name"].lower()
                desc_match = s in r["description"].lower()
                alias_match = any(s in a.lower() for a in r.get("aliases", []))
                skill_match = any(s in sk.lower() for sk in r.get("required_skills_default", []))
                if name_match or desc_match or alias_match or skill_match:
                    filtered.append(r)
            return filtered

        return results

    @classmethod
    def _score_candidates(cls, clean_text: str, candidates: list) -> Tuple[Optional[str], float]:
        best_role = None
        best_score = 0.0

        for role in candidates:
            score = 0.0
            # 1. Exact role name mention (high weight)
            role_name = role["name"].lower()
            if role_name in clean_text:
                score += 3.5

            # 2. Aliases match
            for alias in role.get("aliases", []):
                if alias.lower() in clean_text:
                    score += 2.5

            # 3. Required skills match
            skills = role.get("required_skills_default", [])
            matched_skills_count = 0
            for skill in skills:
                pattern = r'\b' + re.escape(skill.lower()) + r'\b'
                if re.search(pattern, clean_text):
                    matched_skills_count += 1

            if skills:
                skill_ratio = matched_skills_count / len(skills)
                score += (matched_skills_count * 1.2) + (skill_ratio * 3.0)

            if score > best_score:
                best_score = score
                best_role = role["name"]

        return best_role, best_score

    @classmethod
    def predict_specific_role(
        cls,
        resume_text: str,
        occupational_class: str
    ) -> Tuple[str, float]:
        """
        Secondary Specialization Layer:
        Predicts the specific role within an occupational class using domain profile scoring.
        If the primary domain yields no strong match (< 2.0), checks cross-domain catalog for exact role matches.
        Falls back to 'General {Class} Specialist' if confidence is low.
        """
        if not resume_text or not occupational_class:
            return "General Professional", 0.0

        clean_text = resume_text.lower()
        clean_class = occupational_class.strip().upper()

        # Find candidates for this occupational class
        candidates = [r for r in DEFAULT_ROLE_CATALOG if r["occupational_class"] == clean_class]
        best_role, best_score = cls._score_candidates(clean_text, candidates)

        # Cross-domain fallback if primary class has no specific match but an exact title exists elsewhere
        if best_score < 2.0:
            global_role, global_score = cls._score_candidates(clean_text, DEFAULT_ROLE_CATALOG)
            if global_score >= 3.0:
                best_role = global_role
                best_score = global_score

        # Calibrate confidence score
        if best_role:
            confidence = min(0.96, round(0.55 + (min(best_score, 8.0) / 8.0) * 0.40, 2))
            return best_role, float(confidence)

        # Fallback strictly to an actual real role in this domain (NEVER a synthetic or generalized role)
        if candidates:
            return candidates[0]["name"], 0.50
        return "Software Engineer", 0.50

    @classmethod
    def infer_specific_role_from_text(cls, text: str) -> Tuple[str, float]:
        """
        Infers an actual specific role from text (e.g., pasted Job Description or resume)
        by matching against real roles in the role corpus.
        NEVER returns synthetic or generalized role titles.
        """
        if not text:
            return "Software Engineer", 0.50

        clean_text = text.lower()
        best_role, best_score = cls._score_candidates(clean_text, DEFAULT_ROLE_CATALOG)
        if best_role and best_score >= 1.0:
            confidence = min(0.96, round(0.55 + (min(best_score, 8.0) / 8.0) * 0.40, 2))
            return best_role, float(confidence)

        return "Software Engineer", 0.50
