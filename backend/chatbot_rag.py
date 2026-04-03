import os
import random
import re

# --- ADVANCED KNOWLEDGE BASE ---
# Structured with granular categories and actionable, professional advice.

KNOWLEDGE_BASE = {
    # --- GENERAL NAVIGATION (NEW) ---
    "resume_general": [
        "Let's craft a winning resume. What specific area do you need help with?",
        "• **Structure & Format:** (Type 'structure')",
        "• **Writing Impactful Bullets:** (Type 'content')",
        "• **Handling Career Gaps:** (Type 'gaps')"
    ],
    "interview_general": [
        "Interviewing is a skill you can master. What do you want to practice?",
        "• **Behavioral Questions & STAR Method:** (Type 'behavioral')",
        "• **Technical & Coding Rounds:** (Type 'technical')",
        "• **Questions to ask the Interviewer:** (Type 'questions to ask')"
    ],
    "skills_general": [
        "I can provide roadmaps for different tech careers. Which one interests you?",
        "• **Backend Engineering:** (Type 'backend')",
        "• **Frontend Engineering:** (Type 'frontend')",
        "• **Data Science & Analytics:** (Type 'data')"
    ],

    # --- RESUME SECTION ---
    "resume_structure": [
        "**Resume Structure:** Use a clean, reverse-chronological format. Sections: Header, Summary (optional), Skills, Experience, Education, Projects.",
        "**Formatting:** Keep it to 1 page (unless 10+ years exp). Use standard fonts (Arial, Calibri) size 10-12. Save as PDF.",
        "**Visuals:** Avoid photos, charts, or skill bars (e.g., '90% Python'). ATS scanners cannot read them properly."
    ],
    "resume_content": [
        "**The XYZ Formula:** Describe achievements as: 'Accomplished [X] as measured by [Y], by doing [Z]'. Example: 'Reduced load times by 20% (Y) by refactoring legacy API code (Z).'",
        "**Active Verbs:** Start every bullet with a power verb: Engineered, Spearheaded, Optimized, Orchestrated, Designed (avoid 'Responsible for').",
        "**Tailoring:** Scan the Job Description (JD). If it asks for 'React' and 'Agile', ensure those exact words appear in your Skills or Experience."
    ],
    "resume_gaps": [
        "**Handling Gaps:** Be honest but brief. List gaps as 'Career Break' or 'Sabbatical' if needed. Focus on professional development (courses, freelancing) done during that time.",
        "**Functional Resumes:** If you have large gaps or are switching careers, consider a 'Functional' resume format that groups skills rather than just chronology."
    ],

    # --- INTERVIEW PREP ---
    "interview_behavioral": [
        "**The STAR Method:** Answer behavioral questions (e.g., 'Tell me about a challenge') using: \n- **S**ituation (Context)\n- **T**ask (Your responsibility)\n- **A**ction (What you did - focus on 'I', not 'We')\n- **R**esult (Outcome/Impact).",
        "**Common Questions:** Prepare stories for: Leadership, Failure, Conflict Resolution, and Innovation."
    ],
    "interview_technical": [
        "**Coding:** Practice LeetCode (Easy/Medium) for DSA. Focus on Arrays, HashMaps, and Trees.",
        "**System Design:** For senior roles, study scalability, load balancing, and database choices (SQL vs NoSQL).",
        "**Take-Home Tests:** Document your code, write tests, and include a README. Code quality matters as much as the solution."
    ],
    "interview_questions_to_ask": [
        "**Ask the Interviewer:** \n1. 'How does the team balance technical debt vs. new features?'\n2. 'What does success look like in the first 90 days?'\n3. 'How has the team evolved over the past year?'"
    ],

    # --- SALARY NEGOTIATION ---
    "salary_strategy": [
        "**The Golden Rule:** Never give the first number. If asked, say: 'I'm open to competitive market rates for this level of responsibility. What is the budget for this role?'",
        "**Research:** Check Levels.fyi, Glassdoor, and Blind for accurate data points based on location and seniority.",
        "**Counter-Offers:** Always negotiate. 'I'm very excited about the offer. Based on my research and experience, I was looking for something in the [X] range. Can we bridge that gap?'"
    ],

    # --- SKILLS & GROWTH ---
    "skills_backend": [
        "**Backend Roadmap:** Python (Django/FastAPI) or Node.js. Databases (PostgreSQL, MongoDB). APIs (REST, GraphQL). Docker/Kubernetes basics.",
        "**Cloud:** Learn basics of AWS (EC2, S3, Lambda) or Azure. Certification helps."
    ],
    "skills_frontend": [
        "**Frontend Roadmap:** HTML/CSS/JS mastery. Modern Framework (React, Vue, or Angular). State Management (Redux, Context). CSS Frameworks (Tailwind).",
        "**Portfolio:** Build distinct projects: E-commerce site, Dashboard, or Real-time chat app."
    ],
    "skills_data": [
        "**Data Science:** Python (Pandas, NumPy, Scikit-Learn). SQL (Window functions, Joins). Visualization (Tableau/PowerBI). Statistics basics.",
        "**Projects:** Kaggle competitions or cleaning/visualizing a unique public dataset."
    ],

    # --- NETWORKING ---
    "networking_linkedin": [
        "**LinkedIn Optimization:** Headline should be 'Role | Key Skills | Value Prop'. About section should tell your story. Skills section should be full.",
        "**Cold Messaging:** Keep it short. 'Hi [Name], I'm a [Role] admiring [Company]'s work in [Area]. Would love to ask 2 questions about your team culture. No referral needed.'"
    ]
}

# --- INTENT MAPPING ---
# Specific patterns go first so they override general ones
PATTERNS = {
    # 1. Resumes
    "resume_gaps": [r"gap", r"break", r"unemployed"],
    "resume_content": [r"bullet", r"word", r"verb", r"write", r"content", r"describe", r"summary"],
    "resume_structure": [r"format", r"template", r"layout", r"structure"],
    "resume_general": [r"^1$", r"\b1\b", r"resume", r"cv"], # Catch-all for "1" or generic resume

    # 2. Interviews
    "interview_behavioral": [r"behavioral", r"soft skill", r"situation", r"tell me about", r"star method"],
    "interview_technical": [r"technical", r"coding", r"code", r"leetc", r"system design", r"whiteboard"],
    "interview_questions_to_ask": [r"ask interview", r"ask the hir", r"question for", r"end of interview"],
    "interview_general": [r"^2$", r"\b2\b", r"interview", r"prep", r"prepare"], # Catch-all for "2"
    
    # 3. Skills
    "skills_backend": [r"backend", r"server", r"database", r"api", r"python", r"java", r"node"],
    "skills_frontend": [r"frontend", r"ui", r"ux", r"react", r"angular", r"css", r"html", r"design"],
    "skills_data": [r"data", r"sql", r"analyst", r"scientist", r"machine learning", r"ai"],
    "skills_general": [r"^3$", r"\b3\b", r"skill", r"learn", r"develop", r"roadmap"], # Catch-all for "3"

    # 4. Salary
    "salary_strategy": [r"^4$", r"\b4\b", r"salary", r"money", r"pay", r"negotiat", r"offer", r"compensat", r"raise"],
    
    # Extras
    "networking_linkedin": [r"network", r"linkedin", r"connect", r"message", r"referral"]
}

def get_response(user_message):
    """
    Advanced RAG-style response generation.
    Matches user intent to granular knowledge categories and formats a professional response.
    """
    if not user_message:
        return "I'm ready to help. What's on your mind regarding your career?"
    
    message = user_message.lower().strip()
    
    # 1. Direct Pattern Matching (Priority)
    detected_intents = []
    for category, keywords in PATTERNS.items():
        for pattern in keywords:
            if re.search(pattern, message):
                detected_intents.append(category)
                break # Move to next category
    
    # 2. Response Construction
    if detected_intents:
        primary_intent = detected_intents[0]
        
        advice_list = KNOWLEDGE_BASE.get(primary_intent, [])
        if not advice_list:
            return "I understood the topic, but I'm updating my database for that specific area. Ask me generally about resumes or interviews!"

        # Create a rich response
        intro = {
            "resume_general": "📚 **Resume Guide:**",
            "interview_general": "🎯 **Interview Guide:**",
            "skills_general": "🚀 **Skills & Roadmaps:**",
            "resume_structure": "Creating a solid foundation is key. Here's how to structure it:",
            "resume_content": "Content is king. Here is how to write impactful bullets:",
            "resume_gaps": "Addressing gaps confidently is important:",
            "interview_behavioral": "Behavioral questions require stories. Use this framework:",
            "interview_technical": "For technical rounds, focus on these fundamentals:",
            "salary_strategy": "Negotiation is expected. Here is your strategy:",
            "networking_linkedin": "Networking effectively involves strategy:",
            "skills_backend": "For Backend Engineering, the industry looks for:",
            "skills_frontend": "For Frontend roles, mastering these is essential:",
            "skills_data": "Data roles demand a mix of coding and analysis:"
        }.get(primary_intent, "Here is professional advice on that topic:")

        # Join all points for a comprehensive "tell everything" feel
        body = "\n\n".join([f"🔹 {item}" for item in advice_list])
        
        return f"{intro}\n\n{body}"

    # 3. Smart Conversational Fallback
    greetings = ["hi", "hello", "hey", "start", "menu", "help"]
    if any(w in message for w in greetings):
        return ("👋 Hello! I am your Professional Career AI.\n\n"
                "I can give you detailed guides on:\n"
                "1. **Resume Optimization** (Structure, Keywords, Gaps)\n"
                "2. **Interview Mastery** (STAR Method, System Design)\n"
                "3. **Technical Roadmaps** (Frontend, Backend, Data)\n"
                "4. **Salary Negotiation** (Tactics, Scripts)\n\n"
                "Type a number (1-4) or ask me a specific question!")

    # 4. Contextual Unknown
    return ("I want to give you the most accurate advice. Could you specify if you are asking about:\n"
            "1. **Resume writing** techniques?\n"
            "2. **Interview** preparation?\n"
            "3. **Skill** development?\n"
            "4. **Salary** negotiation?\n"
            "(Please type 1, 2, 3, or 4)")