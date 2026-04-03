# ats_skills_dataset.py

# A comprehensive dictionary mapping job roles to their relevant skills and keywords.
# This dataset is designed to help an ATS (Applicant Tracking System) match candidates
# to job descriptions by identifying key technical and soft skills.

ATS_SKILLS_DATA = {
    "Software Engineer": {
        "Languages": ["Python", "Java", "C++", "C#", "JavaScript", "TypeScript", "Go", "Rust", "Swift", "Kotlin", "Ruby", "PHP", "Scala", "Perl", "R", "Dart", "Objective-C", "Shell/Bash", "PowerShell", "Lua", "Haskell", "Erlang", "F#", "Assembly", "Matlab"],
        "Frameworks": ["React", "Angular", "Vue.js", "Django", "Flask", "Spring Boot", ".NET Core", "Express.js", "Ruby on Rails", "Laravel", "Symfony", "ASP.NET", "Next.js", "Nuxt.js", "Svelte", "FastAPI", "Koa.js", "Meteor", "Ember.js", "Backbone.js", "Gatsby", "Struts", "Hibernate", "Play Framework"],
        "Tools": ["Git", "Docker", "Kubernetes", "Jenkins", "JIRA", "Postman", "AWS", "Azure", "Google Cloud", "Visual Studio Code", "IntelliJ IDEA", "Eclipse", "Vim", "Sublime Text", "Atom", "Notepad++", "Slack", "Microsoft Teams", "Zoom", "Trello", "Confluence", "Bitbucket", "GitLab", "GitHub Actions", "Travis CI", "CircleCI", "Heroku", "Netlify", "Vercel"],
        "Concepts": ["Data Structures", "Algorithms", "System Design", "Object-Oriented Programming", "REST APIs", "Microservices", "CI/CD", "Agile", "Scrum", "Kanban", "Test-Driven Development (TDD)", "Domain-Driven Design (DDD)", "Design Patterns", "SOLID Principles", "Clean Code", "Refactoring", "Debugging", "Version Control", "Code Review", "Multithreading", "Concurrency", "Parallelism", "Distributed Systems", "API Design", "Database Normalization"]
    },
    "Data Scientist": {
        "Languages": ["Python", "R", "SQL", "Scala", "Julia", "Java", "C++", "MATLAB", "SAS", "Stata", "SPSS"],
        "Libraries": ["Pandas", "NumPy", "Scikit-learn", "TensorFlow", "PyTorch", "Keras", "Matplotlib", "Seaborn", "NLTK", "Spacy", "OpenCV", "XGBoost", "LightGBM", "CatBoost", "Statsmodels", "Plotly", "Bokeh", "Altair", "Gensim", "Hugging Face Transformers", "FastAI", "Theano", "Caffe", "MXNet"],
        "Tools": ["Jupyter Notebooks", "Tableau", "Power BI", "Apache Spark", "Hadoop", "Excel", "AWS SageMaker", "Google Colab", "Anaconda", "RStudio", "Databricks", "Snowflake", "BigQuery", "Redshift", "Airflow", "MLflow", "Kubeflow", "DVC", "Weights & Biases"],
        "Concepts": ["Machine Learning", "Deep Learning", "Statistical Analysis", "Data Visualization", "Big Data", "Natural Language Processing", "Computer Vision", "Reinforcement Learning", "Time Series Analysis", "A/B Testing", "Hypothesis Testing", "Data Cleaning", "Feature Engineering", "Model Evaluation", "Model Deployment", "Regression Analysis", "Classification", "Clustering", "Dimensionality Reduction", "Neural Networks", "Bayesian Statistics", "Ensemble Methods"]
    },
    "Frontend Developer": {
        "Languages": ["HTML", "CSS", "JavaScript", "TypeScript", "Sass", "Less", "Stylus", "CoffeeScript", "Elm", "PureScript"],
        "Frameworks": ["React", "Angular", "Vue.js", "Svelte", "Next.js", "Nuxt.js", "Bootstrap", "Tailwind CSS", "Material UI", "Chakra UI", "Ant Design", "Foundation", "Bulma", "Semantic UI", "Alpine.js", "Preact", "SolidJS", "Lit", "Stencil"],
        "Tools": ["Webpack", "Babel", "npm", "Yarn", "Git", "Figma", "Adobe XD", "Sketch", "InVision", "Zeplin", "Chrome DevTools", "Visual Studio Code", "Sublime Text", "Atom", "ESLint", "Prettier", "Jest", "Cypress", "Storybook", "Lighthouse", "PostCSS", "Gulp", "Grunt"],
        "Concepts": ["Responsive Design", "Accessibility (a11y)", "State Management (Redux, Context API, MobX, Recoil, Zustand, Jotai)", "SEO", "Web Performance", "Cross-Browser Compatibility", "Progressive Web Apps (PWA)", "Single Page Applications (SPA)", "Server-Side Rendering (SSR)", "Static Site Generation (SSG)", "Web Components", "CSS Grid", "Flexbox", "DOM Manipulation", "Event Handling", "AJAX", "Promises", "Async/Await", "Web Sockets"]
    },
    "Backend Developer": {
        "Languages": ["Python", "Java", "Node.js", "PHP", "Ruby", "Go", "C#", "C++", "Rust", "Scala", "Elixir", "Clojure", "Kotlin"],
        "Frameworks": ["Django", "Flask", "Spring Boot", "Express.js", "Laravel", "Ruby on Rails", "ASP.NET", "FastAPI", "NestJS", "Koa.js", "Symfony", "CodeIgniter", "CakePHP", "Phoenix", "Play Framework", "Gin", "Echo", "Fiber", "AdonisJS", "Sails.js", "Hapi.js"],
        "Databases": ["PostgreSQL", "MySQL", "MongoDB", "Redis", "Cassandra", "Elasticsearch", "SQLite", "MariaDB", "Oracle Database", "Microsoft SQL Server", "DynamoDB", "CouchDB", "Neo4j", "Firebase Realtime Database", "Firestore", "InfluxDB", "TimescaleDB"],
        "Concepts": ["REST APIs", "GraphQL", "Authentication (OAuth, JWT, SAML, OpenID Connect)", "Microservices", "Serverless Architecture", "Caching", "Message Queues (RabbitMQ, Kafka, ActiveMQ, SQS)", "WebSockets", "gRPC", "API Gateway", "Load Balancing", "Database Design", "ORM (Object-Relational Mapping)", "Containerization", "Distributed Systems", "Multitenancy", "Rate Limiting", "Webhooks"]
    },
    "DevOps Engineer": {
        "Languages": ["Python", "Bash", "Go", "Ruby", "Groovy", "PowerShell", "Perl"],
        "Tools": ["Docker", "Kubernetes", "Jenkins", "GitLab CI", "Terraform", "Ansible", "Chef", "Puppet", "Prometheus", "Grafana", "Nagios", "Splunk", "ELK Stack", "CircleCI", "Travis CI", "Bamboo", "TeamCity", "Vagrant", "Packer", "Consul", "Vault", "Istio", "Linkerd", "ArgoCD", "Helm", "Flux"],
        "Cloud Platforms": ["AWS", "Azure", "Google Cloud Platform (GCP)", "IBM Cloud", "Oracle Cloud", "DigitalOcean", "Heroku", "Linode", "Vultr", "Alibaba Cloud"],
        "Concepts": ["CI/CD", "Infrastructure as Code (IaC)", "Containerization", "Orchestration", "Monitoring", "Logging", "Security (DevSecOps)", "Site Reliability Engineering (SRE)", "High Availability", "Disaster Recovery", "Scalability", "Automation", "Configuration Management", "Blue-Green Deployment", "Canary Deployment", "GitOps", "Service Mesh"]
    },
    "Product Manager": {
        "Skills": ["Product Strategy", "Roadmapping", "User Research", "Agile/Scrum", "Data Analysis", "Stakeholder Management", "A/B Testing", "Prioritization", "Communication", "Leadership", "Problem Solving", "Negotiation", "Time Management", "Critical Thinking", "Market Analysis", "Business Modeling", "Revenue Growth", "Customer Empathy", "Storytelling", "Risk Management"],
        "Tools": ["JIRA", "Trello", "Asana", "Figma", "Mixpanel", "Google Analytics", "Slack", "Microsoft Teams", "Confluence", "Notion", "Miro", "Lucidchart", "Productboard", "Aha!", "Pendo", "Amplitude", "Monday.com", "ClickUp", "Basecamp", "Airtable"],
        "Concepts": ["MVP (Minimum Viable Product)", "Product Lifecycle", "User Stories", "Market Research", "Competitive Analysis", "KPIs (Key Performance Indicators)", "OKRs (Objectives and Key Results)", "Product-Market Fit", "Go-to-Market Strategy", "Customer Journey Mapping", "Jobs to be Done (JTBD)", "Design Thinking", "Lean Startup", "SWOT Analysis", "Business Model Canvas"]
    },
    "UI/UX Designer": {
        "Skills": ["User Interface Design", "User Experience Research", "Wireframing", "Prototyping", "Visual Design", "Interaction Design", "Information Architecture", "Usability Testing", "User Personas", "User Flows", "Design Systems", "Typography", "Color Theory", "Accessibility", "Empathy", "Sketching", "Storyboarding", "Card Sorting", "A/B Testing Analysis"],
        "Tools": ["Figma", "Sketch", "Adobe XD", "InVision", "Photoshop", "Illustrator", "Zeplin", "Axure RP", "Balsamiq", "Marvel", "Principle", "After Effects", "Origami Studio", "Webflow", "Protopie", "Framer", "Abstract", "Miro"],
        "Concepts": ["Design Thinking", "Human-Computer Interaction (HCI)", "Mobile-First Design", "Responsive Design", "Microinteractions", "Material Design", "Human Interface Guidelines", "Atomic Design", "Heuristic Evaluation", "Cognitive Psychology", "Gestalt Principles", "Affordance", "Fitts's Law", "Hick's Law"]
    },
    "Cybersecurity Analyst": {
        "Skills": ["Network Security", "Penetration Testing", "Incident Response", "Vulnerability Assessment", "Risk Management", "Cryptography", "Ethical Hacking", "Security Auditing", "Forensics", "Security Operations", "Threat Intelligence", "Identity and Access Management (IAM)", "Security Awareness Training", "Malware Analysis", "Reverse Engineering", "Scripting", "Cloud Security"],
        "Tools": ["Wireshark", "Metasploit", "Nmap", "Burp Suite", "Splunk", "Snort", "Nessus", "Kali Linux", "Aircrack-ng", "John the Ripper", "Hashcat", "Hydra", "OWASP ZAP", "Qualys", "CrowdStrike", "Carbon Black", "QRadar", "ArcSight", "LogRhythm", "Ghidra", "IDA Pro"],
        "Concepts": ["Firewalls", "SIEM", "IDS/IPS", "Malware Analysis", "Compliance (GDPR, HIPAA, SOC 2, PCI DSS, ISO 27001)", "Zero Trust", "Cloud Security", "Application Security", "Endpoint Security", "Data Loss Prevention (DLP)", "Social Engineering", "Phishing", "Ransomware", "DDoS", "MITRE ATT&CK", "Cyber Kill Chain", "Encryption", "PKI", "VPN"]
    },
    "Mobile App Developer": {
        "Languages": ["Swift", "Kotlin", "Java", "Dart", "Objective-C", "C#", "JavaScript", "TypeScript"],
        "Frameworks": ["React Native", "Flutter", "Xamarin", "Ionic", "SwiftUI", "UIKit", "Jetpack Compose", "NativeScript", "Cordova", "PhoneGap", "Framework7", "Onsen UI"],
        "Tools": ["Xcode", "Android Studio", "Firebase", "TestFlight", "App Store Connect", "Google Play Console", "CocoaPods", "Gradle", "Fastlane", "Realm", "SQLite", "Charles Proxy", "Flipper"],
        "Concepts": ["Mobile UI Design", "App Store Guidelines", "Push Notifications", "Offline Storage", "Performance Optimization", "Memory Management", "Multithreading", "REST APIs", "GraphQL", "Bluetooth Low Energy (BLE)", "Location Services", "Camera API", "Sensors", "Augmented Reality (AR)", "Virtual Reality (VR)", "Deep Linking", "App Lifecycle"]
    },
    "QA Engineer": {
        "Skills": ["Manual Testing", "Automated Testing", "Performance Testing", "Regression Testing", "Bug Tracking", "Test Planning", "Test Case Design", "Defect Reporting", "Quality Assurance", "Continuous Integration", "Agile Testing", "Exploratory Testing", "Usability Testing", "Security Testing", "API Testing", "Database Testing", "Mobile Testing"],
        "Tools": ["Selenium", "Appium", "JMeter", "Postman", "Cypress", "JIRA", "TestRail", "SoapUI", "LoadRunner", "Gatling", "Katalon Studio", "Robot Framework", "Cucumber", "TestComplete", "Bugzilla", "Mantis", "Playwright", "Puppeteer", "Sauce Labs", "BrowserStack"],
        "Concepts": ["Test Plans", "Test Cases", "CI/CD Integration", "API Testing", "Load Testing", "Stress Testing", "End-to-End Testing", "Unit Testing", "Integration Testing", "System Testing", "Acceptance Testing", "Smoke Testing", "Sanity Testing", "Black Box Testing", "White Box Testing", "Test Pyramid", "Shift Left Testing"]
    },
    "Cloud Architect": {
        "Skills": ["Cloud Strategy", "Cloud Migration", "Solution Architecture", "Cost Optimization", "Security Architecture", "Disaster Recovery", "High Availability", "Scalability", "Performance Tuning", "Vendor Management", "Technical Leadership", "Network Design", "Compliance Management", "Virtualization"],
        "Tools": ["AWS", "Azure", "Google Cloud Platform (GCP)", "Terraform", "Ansible", "Docker", "Kubernetes", "Jenkins", "Git", "Visio", "Lucidchart", "Draw.io", "CloudFormation", "ARM Templates", "Pulumi", "Packer", "Chef", "Puppet"],
        "Concepts": ["IaaS", "PaaS", "SaaS", "Serverless", "Microservices", "Containers", "DevOps", "Hybrid Cloud", "Multi-Cloud", "Cloud Native", "Well-Architected Framework", "Compliance", "Governance", "Load Balancing", "CDN", "VPN", "VPC", "Identity Federation"]
    },
    "Database Administrator": {
        "Skills": ["Database Design", "Database Tuning", "Backup and Recovery", "Security Management", "Performance Monitoring", "Capacity Planning", "Data Migration", "Troubleshooting", "Scripting", "ETL", "Data Warehousing", "High Availability", "Replication", "Disaster Recovery"],
        "Tools": ["Oracle Database", "Microsoft SQL Server", "MySQL", "PostgreSQL", "MongoDB", "Redis", "Cassandra", "Elasticsearch", "SQL Developer", "SSMS", "Toad", "Navicat", "pgAdmin", "DBeaver", "DataGrip", "Percona", "Redgate"],
        "Concepts": ["Relational Databases", "NoSQL Databases", "Normalization", "Indexing", "Replication", "Clustering", "Sharding", "ACID Properties", "CAP Theorem", "Data Integrity", "Data Modeling", "Stored Procedures", "Triggers", "Views", "Transactions", "Concurrency Control", "Locking"]
    },
    "Network Engineer": {
        "Skills": ["Network Design", "Network Configuration", "Network Troubleshooting", "Network Security", "Routing and Switching", "Firewall Management", "VPN Configuration", "Wireless Networking", "Load Balancing", "Network Monitoring", "VoIP", "SDN", "Network Automation"],
        "Tools": ["Cisco Packet Tracer", "GNS3", "Wireshark", "SolarWinds", "Nagios", "PRTG", "Putty", "SecureCRT", "Ansible", "Python", "EVE-NG", "Tcpdump", "Nmap", "NetFlow Analyzer", "Cacti", "Zabbix"],
        "Concepts": ["TCP/IP", "OSI Model", "LAN/WAN", "VLAN", "Subnetting", "DNS", "DHCP", "BGP", "OSPF", "EIGRP", "MPLS", "SD-WAN", "Network Virtualization", "Cloud Networking", "QoS", "NAT", "VPN", "IPSec", "SSL/TLS", "IPv4/IPv6"]
    },
    "System Administrator": {
        "Skills": ["Server Administration", "User Management", "Patch Management", "Backup and Recovery", "Scripting", "Monitoring", "Troubleshooting", "Virtualization", "Cloud Administration", "Security Hardening", "Active Directory Management", "Storage Management", "Disaster Recovery"],
        "Tools": ["Active Directory", "Group Policy", "PowerShell", "Bash", "VMware", "Hyper-V", "Nagios", "Zabbix", "Splunk", "Ansible", "Puppet", "Chef", "SCCM", "WSUS", "Veeam", "Proxmox", "Citrix", "Office 365"],
        "Concepts": ["Windows Server", "Linux", "DNS", "DHCP", "LDAP", "Kerberos", "RAID", "LVM", "Filesystems", "Networking", "Security", "ITIL", "SLA", "Incident Management", "Change Management", "Asset Management"]
    },
    "Technical Writer": {
        "Skills": ["Technical Writing", "Documentation", "Editing", "Proofreading", "Content Strategy", "Information Architecture", "User Research", "API Documentation", "Software Documentation", "Hardware Documentation", "Video Tutorials", "Knowledge Base Management", "Release Notes"],
        "Tools": ["Microsoft Word", "Google Docs", "Markdown", "JIRA", "Confluence", "Git", "Sphinx", "Read the Docs", "MadCap Flare", "Adobe FrameMaker", "Snagit", "Visio", "Camtasia", "WordPress", "Zendesk Guide", "Swagger/OpenAPI", "Postman"],
        "Concepts": ["Style Guides", "Documentation Life Cycle", "Audience Analysis", "Usability", "Accessibility", "Version Control", "Content Management Systems (CMS)", "DITA", "XML", "Simplified Technical English", "Localization", "Single Sourcing"]
    }
}

# Helper function to get all unique skills in a flat list
def get_all_unique_skills():
    unique_skills = set()
    for role, categories in ATS_SKILLS_DATA.items():
        for category, skills in categories.items():
            unique_skills.update([skill.lower() for skill in skills])
    return sorted(list(unique_skills))

# Helper function to get skills for a specific role
def get_skills_for_role(role_name):
    role_data = ATS_SKILLS_DATA.get(role_name)
    if not role_data:
        return []
    
    skills_list = []
    for category, skills in role_data.items():
        skills_list.extend(skills)
    return skills_list

if __name__ == "__main__":
    # Example Usage
    print(f"Total Unique Skills: {len(get_all_unique_skills())}")
    print(f"Skills for Data Scientist: {get_skills_for_role('Data Scientist')}")