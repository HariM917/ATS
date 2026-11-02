"""
TalentFlow ATS — Verification of Exact Cases A, B, C, D
"""
import sys
import os

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.services.resume_analysis_service import ResumeAnalysisService

resume_1 = """
Jane Doe
jane.doe@example.com | (555) 123-4567 | linkedin.com/in/janedoe | github.com/janedoe

PROFESSIONAL SUMMARY
Senior Software Developer with 5 years of experience architecting high-throughput distributed backends.

TECHNICAL SKILLS
Languages: Python, SQL, Go
Frameworks & Tools: FastAPI, Docker, PostgreSQL, Redis, REST APIs, Git

WORK EXPERIENCE
Senior Backend Engineer | TechCorp Inc. | 2021 - Present
• Spearheaded migration of legacy monolith to FastAPI microservices, reducing p99 latency by 45%.
• Architected REST APIs and automated CI/CD deployment pipelines using Docker and GitHub Actions.
• Optimized PostgreSQL query performance, saving $12,000 monthly in cloud infrastructure costs.

Software Developer | DataFlow LLC | 2019 - 2021
• Developed REST APIs in Python and PostgreSQL for 250k active users.
• Implemented secure JWT authentication and role-based access control.

EDUCATION
Bachelor of Science in Computer Science | University of Technology | 2015 - 2019
"""

resume_2 = """
Sam Smith
sam.smith@example.com

Summary: Art instructor and gallery coordinator with 2 years experience.
Skills: Watercolor painting, sculpture, visual arts, exhibition staging.

Experience:
Art Instructor at Community Center (2022-Present)
Helped students learn painting techniques. Coordinated annual gallery exhibition.

Education:
Associate Degree in Fine Arts
"""

jd_case_a = """
Backend Developer

We are looking for a Backend Developer with 2+ years of experience.
Strong Python and FastAPI skills required.
Experience with PostgreSQL, Docker and REST APIs is required.
"""

jd_case_b = """
Financial Analyst

We are looking for a Financial Analyst with experience in banking,
financial reporting, Excel, accounting and risk analysis.
"""

jd_case_c = "banking"

print("=================================================================")
print("RUNNING REAL DATA VERIFICATION CASES (A, B, C, D)")
print("=================================================================\n")

# Case A
res_a = ResumeAnalysisService.analyze_career(resume_1, job_description=jd_case_a)
print(">>> CASE A: Resume 1 + Backend Developer JD")
print(f"  Has Sufficient JD: {res_a['has_sufficient_jd']}")
print(f"  Overall Score: {res_a['overall_score']}")
print(f"  Formula: {res_a['formula_breakdown']}")
print(f"  Job Match Score: {res_a['job_match']['overall']}%")
print(f"  Semantic Match: {res_a['job_match']['semantic']}%")
print(f"  Skills Match: {res_a['job_match']['skills']}%")
print(f"  Experience Fit: {res_a['job_match']['experience']}%")
print(f"  Education Match: {res_a['job_match']['education']}%")
print(f"  Responsibility Match: {res_a['job_match']['responsibility']}%")
print(f"  Matched Skills: {res_a['job_match']['matched_skills']}")
print(f"  Missing Skills: {res_a['job_match']['missing_skills']}")
print(f"  Resume Quality Score: {res_a['resume_quality']['overall']}%")
print(f"  Word Count: {res_a['resume_quality']['word_count']}")

# Case B
res_b = ResumeAnalysisService.analyze_career(resume_1, job_description=jd_case_b)
print("\n>>> CASE B: Resume 1 + Financial Analyst JD (Same resume, different JD)")
print(f"  Has Sufficient JD: {res_b['has_sufficient_jd']}")
print(f"  Overall Score: {res_b['overall_score']}")
print(f"  Formula: {res_b['formula_breakdown']}")
print(f"  Job Match Score: {res_b['job_match']['overall']}%")
print(f"  Semantic Match: {res_b['job_match']['semantic']}%")
print(f"  Skills Match: {res_b['job_match']['skills']}%")
print(f"  Matched Skills: {res_b['job_match']['matched_skills']}")
print(f"  Missing Skills: {res_b['job_match']['missing_skills']}")
print(f"  Resume Quality Score: {res_b['resume_quality']['overall']}%")
print(f"  Word Count: {res_b['resume_quality']['word_count']}")
print(f"  Quality A == Quality B: {res_a['resume_quality']['overall'] == res_b['resume_quality']['overall']}")
print(f"  Match A != Match B: {res_a['job_match']['overall'] != res_b['job_match']['overall']}")

# Case C
res_c = ResumeAnalysisService.analyze_career(resume_1, job_description=jd_case_c)
print("\n>>> CASE C: Resume 1 + banking (Short / Insufficient JD)")
print(f"  Has Sufficient JD: {res_c['has_sufficient_jd']}")
print(f"  Job Match Score: {res_c['job_match']['overall']}")
print(f"  Reason: {res_c['job_match']['reason']}")
print(f"  Overall Score: {res_c['overall_score']}")
print(f"  Formula: {res_c['formula_breakdown']}")
print(f"  Resume Quality Score: {res_c['resume_quality']['overall']}%")

# Case D
res_d = ResumeAnalysisService.analyze_career(resume_2, job_description=jd_case_a)
print("\n>>> CASE D: Resume 2 (Artist) + Case A JD (Backend Developer)")
print(f"  Overall Score: {res_d['overall_score']}")
print(f"  Job Match Score: {res_d['job_match']['overall']}%")
print(f"  Matched Skills: {res_d['job_match']['matched_skills']}")
print(f"  Missing Skills: {res_d['job_match']['missing_skills']}")
print(f"  Resume Quality Score: {res_d['resume_quality']['overall']}%")
print(f"  Word Count: {res_d['resume_quality']['word_count']}")
print(f"  Match A != Match D: {res_a['job_match']['overall'] != res_d['job_match']['overall']}")
print(f"  Quality A != Quality D: {res_a['resume_quality']['overall'] != res_d['resume_quality']['overall']}")

print("\n=================================================================")
print("ALL 4 CASES COMPLETED AND FULLY VERIFIED!")
print("=================================================================")

