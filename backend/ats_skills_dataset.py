# ats_skills_dataset.py

# A comprehensive dictionary mapping job roles to their relevant skills and keywords.
# This dataset is designed to help an ATS (Applicant Tracking System) match candidates
# to job descriptions by identifying key technical and soft skills.

ATS_SKILLS_DATA = {
    "Software Engineer": {
        "Languages": ["Python", "Java", "C++", "C#", "JavaScript", "TypeScript", "Go", "Rust", "Swift", "Kotlin", "Ruby", "PHP", "Scala", "Perl", "R", "Dart", "Objective-C", "Shell/Bash", "PowerShell", "Lua", "Haskell", "Erlang", "F#", "Assembly", "Matlab", "Cobol", "Fortran", "Lisp", "Scheme", "Prolog"],
        "Frameworks": ["React", "Angular", "Vue.js", "Django", "Flask", "Spring Boot", ".NET Core", "Express.js", "Ruby on Rails", "Laravel", "Symfony", "ASP.NET", "Next.js", "Nuxt.js", "Svelte", "FastAPI", "Koa.js", "Meteor", "Ember.js", "Backbone.js", "Gatsby", "Struts", "Hibernate", "Play Framework", "Micronaut", "Quarkus", "NestJS", "Fastify", "AdonisJS", "Sails.js", "Hapi.js"],
        "Tools": ["Git", "Docker", "Kubernetes", "Jenkins", "JIRA", "Postman", "AWS", "Azure", "Google Cloud", "Visual Studio Code", "IntelliJ IDEA", "Eclipse", "Vim", "Sublime Text", "Atom", "Notepad++", "Slack", "Microsoft Teams", "Zoom", "Trello", "Confluence", "Bitbucket", "GitLab", "GitHub Actions", "Travis CI", "CircleCI", "Heroku", "Netlify", "Vercel", "Rancher", "Helm", "Kustomize", "Maven", "Gradle", "NPM", "Yarn", "PNPM"],
        "Concepts": ["Data Structures", "Algorithms", "System Design", "Object-Oriented Programming", "REST APIs", "Microservices", "CI/CD", "Agile", "Scrum", "Kanban", "Test-Driven Development (TDD)", "Domain-Driven Design (DDD)", "Design Patterns", "SOLID Principles", "Clean Code", "Refactoring", "Debugging", "Version Control", "Code Review", "Multithreading", "Concurrency", "Parallelism", "Distributed Systems", "API Design", "Database Normalization", "SOA", "Event-Driven Architecture", "Serverless"]
    },
    "Data Scientist": {
        "Languages": ["Python", "R", "SQL", "Scala", "Julia", "Java", "C++", "MATLAB", "SAS", "Stata", "SPSS", "Octave"],
        "Libraries": ["Pandas", "NumPy", "Scikit-learn", "TensorFlow", "PyTorch", "Keras", "Matplotlib", "Seaborn", "NLTK", "Spacy", "OpenCV", "XGBoost", "LightGBM", "CatBoost", "Statsmodels", "Plotly", "Bokeh", "Altair", "Gensim", "Hugging Face Transformers", "FastAI", "Theano", "Caffe", "MXNet", "SciPy", "Scikit-Image", "Tesseract", "Pattern", "TextBlob", "VaderSentiment", "Umap", "T-SNE"],
        "Tools": ["Jupyter Notebooks", "Tableau", "Power BI", "Apache Spark", "Hadoop", "Excel", "AWS SageMaker", "Google Colab", "Anaconda", "RStudio", "Databricks", "Snowflake", "BigQuery", "Redshift", "Airflow", "MLflow", "Kubeflow", "DVC", "Weights & Biases", "Neptune.ai", "Comet.ml", "TensorBoard", "RapidMiner", "Alteryx", "KNIME"],
        "Concepts": ["Machine Learning", "Deep Learning", "Statistical Analysis", "Data Visualization", "Big Data", "Natural Language Processing", "Computer Vision", "Reinforcement Learning", "Time Series Analysis", "A/B Testing", "Hypothesis Testing", "Data Cleaning", "Feature Engineering", "Model Evaluation", "Model Deployment", "Regression Analysis", "Classification", "Clustering", "Dimensionality Reduction", "Neural Networks", "Bayesian Statistics", "Ensemble Methods", "Gradient Boosting", "Random Forest", "Supervised Learning", "Unsupervised Learning", "Semi-Supervised Learning", "Transfer Learning", "Anomaly Detection"]
    },
    "Frontend Developer": {
        "Languages": ["HTML", "HTML5", "CSS", "CSS3", "JavaScript", "TypeScript", "Sass", "Less", "Stylus", "CoffeeScript", "Elm", "PureScript"],
        "Frameworks": ["React", "Angular", "Vue.js", "Svelte", "Next.js", "Nuxt.js", "Bootstrap", "Tailwind CSS", "Material UI", "Chakra UI", "Ant Design", "Foundation", "Bulma", "Semantic UI", "Alpine.js", "Preact", "SolidJS", "Lit", "Stencil", "Emotion", "Styled Components", "Gatsby", "Vite", "Webpack", "Babel", "Rollup", "Parcel"],
        "Tools": ["Figma", "Adobe XD", "Sketch", "InVision", "Zeplin", "Chrome DevTools", "Visual Studio Code", "ESLint", "Prettier", "Jest", "Cypress", "Storybook", "Lighthouse", "PostCSS", "Gulp", "Grunt", "BrowserStack", "Lerna", "Nx", "TurboRepo", "Npm", "Yarn", "Pnpm"],
        "Concepts": ["Responsive Design", "Accessibility (a11y)", "State Management", "Redux", "MobX", "Zustand", "Recoil", "Context API", "Jotai", "XState", "SEO", "Web Performance", "Cross-Browser Compatibility", "Progressive Web Apps (PWA)", "Single Page Applications (SPA)", "Server-Side Rendering (SSR)", "Static Site Generation (SSG)", "Web Components", "CSS Grid", "Flexbox", "DOM Manipulation", "Event Handling", "AJAX", "Promises", "Async/Await", "Web Sockets", "GraphQL Client", "Apollo Client", "React Query"]
    },
    "Backend Developer": {
        "Languages": ["Python", "Java", "Node.js", "PHP", "Ruby", "Go", "C#", "C++", "Rust", "Scala", "Elixir", "Clojure", "Kotlin", "Perl"],
        "Frameworks": ["Django", "Flask", "Spring Boot", "Express.js", "Laravel", "Ruby on Rails", "ASP.NET", "FastAPI", "NestJS", "Koa.js", "Symfony", "CodeIgniter", "CakePHP", "Phoenix", "Play Framework", "Gin", "Echo", "Fiber", "AdonisJS", "Sails.js", "Hapi.js", "Tornado", "Sanic", "Actix-web", "Rocket", "Go-kit"],
        "Databases": ["PostgreSQL", "MySQL", "MongoDB", "Redis", "Cassandra", "Elasticsearch", "SQLite", "MariaDB", "Oracle Database", "Microsoft SQL Server", "DynamoDB", "CouchDB", "Neo4j", "Firebase Realtime Database", "Firestore", "InfluxDB", "TimescaleDB", "CockroachDB", "ScyllaDB", "ArangoDB", "Memcached"],
        "Concepts": ["REST APIs", "GraphQL", "Authentication", "OAuth", "JWT", "SAML", "OpenID Connect", "Microservices", "Serverless Architecture", "Caching", "Message Queues", "RabbitMQ", "Kafka", "ActiveMQ", "SQS", "WebSockets", "gRPC", "API Gateway", "Load Balancing", "Database Design", "ORM (Object-Relational Mapping)", "Containerization", "Distributed Systems", "Multitenancy", "Rate Limiting", "Webhooks", "Pub/Sub", "Event Sourcing", "CQRS"]
    },
    "DevOps Engineer": {
        "Languages": ["Python", "Bash", "Go", "Ruby", "Groovy", "PowerShell", "Perl"],
        "Tools": ["Docker", "Kubernetes", "Jenkins", "GitLab CI", "Terraform", "Ansible", "Chef", "Puppet", "Prometheus", "Grafana", "Nagios", "Splunk", "ELK Stack", "CircleCI", "Travis CI", "Bamboo", "TeamCity", "Vagrant", "Packer", "Consul", "Vault", "Istio", "Linkerd", "ArgoCD", "Helm", "Flux", "Datadog", "New Relic", "Dynatrace", "Graylog", "Fluentd", "Logstash"],
        "Cloud Platforms": ["AWS", "Azure", "Google Cloud Platform (GCP)", "IBM Cloud", "Oracle Cloud", "DigitalOcean", "Heroku", "Linode", "Vultr", "Alibaba Cloud", "OpenStack", "VMware Cloud"],
        "Concepts": ["CI/CD", "Infrastructure as Code (IaC)", "Containerization", "Orchestration", "Monitoring", "Logging", "Security (DevSecOps)", "Site Reliability Engineering (SRE)", "High Availability", "Disaster Recovery", "Scalability", "Automation", "Configuration Management", "Blue-Green Deployment", "Canary Deployment", "GitOps", "Service Mesh", "Infrastructure Monitoring", "Log Aggregation", "Load Testing"]
    },
    "Product Manager": {
        "Skills": ["Product Strategy", "Roadmapping", "User Research", "Agile/Scrum", "Data Analysis", "Stakeholder Management", "A/B Testing", "Prioritization", "Communication", "Leadership", "Problem Solving", "Negotiation", "Time Management", "Critical Thinking", "Market Analysis", "Business Modeling", "Revenue Growth", "Customer Empathy", "Storytelling", "Risk Management", "Product Launch", "Pricing Strategy", "Product Analytics"],
        "Tools": ["JIRA", "Trello", "Asana", "Figma", "Mixpanel", "Google Analytics", "Slack", "Microsoft Teams", "Confluence", "Notion", "Miro", "Lucidchart", "Productboard", "Aha!", "Pendo", "Amplitude", "Monday.com", "ClickUp", "Basecamp", "Airtable", "Optimizely", "Hotjar", "SurveyMonkey"],
        "Concepts": ["MVP (Minimum Viable Product)", "Product Lifecycle", "User Stories", "Market Research", "Competitive Analysis", "KPIs (Key Performance Indicators)", "OKRs (Objectives and Key Results)", "Product-Market Fit", "Go-to-Market Strategy", "Customer Journey Mapping", "Jobs to be Done (JTBD)", "Design Thinking", "Lean Startup", "SWOT Analysis", "Business Model Canvas", "Product Discovery", "Product Delivery", "Growth Hacking"]
    },
    "UI/UX Designer": {
        "Skills": ["User Interface Design", "User Experience Research", "Wireframing", "Prototyping", "Visual Design", "Interaction Design", "Information Architecture", "Usability Testing", "User Personas", "User Flows", "Design Systems", "Typography", "Color Theory", "Accessibility", "Empathy", "Sketching", "Storyboarding", "Card Sorting", "A/B Testing Analysis", "Information Hierarchy", "Responsive Design", "Mobile-First Design"],
        "Tools": ["Figma", "Sketch", "Adobe XD", "InVision", "Photoshop", "Illustrator", "Zeplin", "Axure RP", "Balsamiq", "Marvel", "Principle", "After Effects", "Origami Studio", "Webflow", "Protopie", "Framer", "Abstract", "Miro", "LottieFiles", "UxPin", "OmniGraffle"],
        "Concepts": ["Design Thinking", "Human-Computer Interaction (HCI)", "Mobile-First", "Microinteractions", "Material Design", "Human Interface Guidelines", "Atomic Design", "Heuristic Evaluation", "Cognitive Psychology", "Gestalt Principles", "Affordance", "Fitts's Law", "Hick's Law", "Jakob's Law", "Color Contrast Checker"]
    },
    "Cybersecurity Analyst": {
        "Skills": ["Network Security", "Penetration Testing", "Incident Response", "Vulnerability Assessment", "Risk Management", "Cryptography", "Ethical Hacking", "Security Auditing", "Forensics", "Security Operations", "Threat Intelligence", "Identity and Access Management (IAM)", "Security Awareness Training", "Malware Analysis", "Reverse Engineering", "Scripting", "Cloud Security", "Endpoint Protection", "Log Analysis", "Risk Assessment"],
        "Tools": ["Wireshark", "Metasploit", "Nmap", "Burp Suite", "Splunk", "Snort", "Nessus", "Kali Linux", "Aircrack-ng", "John the Ripper", "Hashcat", "Hydra", "OWASP ZAP", "Qualys", "CrowdStrike", "Carbon Black", "QRadar", "ArcSight", "LogRhythm", "Ghidra", "IDA Pro", "Autopsy", "FTK Imager", "Ncat", "Angry IP Scanner"],
        "Concepts": ["Firewalls", "SIEM", "IDS/IPS", "Malware Analysis", "Compliance", "GDPR", "HIPAA", "SOC 2", "PCI DSS", "ISO 27001", "Zero Trust", "Application Security", "Endpoint Security", "Data Loss Prevention (DLP)", "Social Engineering", "Phishing", "Ransomware", "DDoS", "MITRE ATT&CK", "Cyber Kill Chain", "Encryption", "PKI", "VPN", "SSO", "MFA", "NIST Framework"]
    },
    "Mobile App Developer": {
        "Languages": ["Swift", "Kotlin", "Java", "Dart", "Objective-C", "C#", "JavaScript", "TypeScript"],
        "Frameworks": ["React Native", "Flutter", "Xamarin", "Ionic", "SwiftUI", "UIKit", "Jetpack Compose", "NativeScript", "Cordova", "PhoneGap", "Framework7", "Onsen UI", "Cocoapods", "Gradle"],
        "Tools": ["Xcode", "Android Studio", "Firebase", "TestFlight", "App Store Connect", "Google Play Console", "Charles Proxy", "Flipper", "Realm", "SQLite", "Fastlane", "Bitrise", "Codemagic"],
        "Concepts": ["Mobile UI Design", "App Store Guidelines", "Push Notifications", "Offline Storage", "Performance Optimization", "Memory Management", "Multithreading", "REST APIs", "GraphQL", "Bluetooth Low Energy (BLE)", "Location Services", "Camera API", "Sensors", "Augmented Reality (AR)", "Virtual Reality (VR)", "Deep Linking", "App Lifecycle", "State Management", "In-App Purchases"]
    },
    "QA Engineer": {
        "Skills": ["Manual Testing", "Automated Testing", "Performance Testing", "Regression Testing", "Bug Tracking", "Test Planning", "Test Case Design", "Defect Reporting", "Quality Assurance", "Continuous Integration", "Agile Testing", "Exploratory Testing", "Usability Testing", "Security Testing", "API Testing", "Database Testing", "Mobile Testing", "Load Testing", "Stress Testing", "Sanity Testing"],
        "Tools": ["Selenium", "Appium", "JMeter", "Postman", "Cypress", "JIRA", "TestRail", "SoapUI", "LoadRunner", "Gatling", "Katalon Studio", "Robot Framework", "Cucumber", "TestComplete", "Bugzilla", "Mantis", "Playwright", "Puppeteer", "Sauce Labs", "BrowserStack", "SonarQube", "Sentry", "New Relic"],
        "Concepts": ["Test Plans", "Test Cases", "CI/CD Integration", "Load Testing", "Stress Testing", "End-to-End Testing", "Unit Testing", "Integration Testing", "System Testing", "Acceptance Testing", "Smoke Testing", "Sanity Testing", "Black Box Testing", "White Box Testing", "Test Pyramid", "Shift Left Testing", "Regression Suites", "Code Coverage", "Mocking"]
    },
    "Cloud Architect": {
        "Skills": ["Cloud Strategy", "Cloud Migration", "Solution Architecture", "Cost Optimization", "Security Architecture", "Disaster Recovery", "High Availability", "Scalability", "Performance Tuning", "Vendor Management", "Technical Leadership", "Network Design", "Compliance Management", "Virtualization", "Cloud Security", "Hybrid Cloud Architecture"],
        "Tools": ["AWS", "Azure", "Google Cloud Platform (GCP)", "Terraform", "Ansible", "Docker", "Kubernetes", "Jenkins", "Git", "Visio", "Lucidchart", "Draw.io", "CloudFormation", "ARM Templates", "Pulumi", "Packer", "Chef", "Puppet", "Rancher", "Helm", "Spinnaker"],
        "Concepts": ["IaaS", "PaaS", "SaaS", "Serverless", "Microservices", "Containers", "DevOps", "Hybrid Cloud", "Multi-Cloud", "Cloud Native", "Well-Architected Framework", "Compliance", "Governance", "Load Balancing", "CDN", "VPN", "VPC", "Identity Federation", "Auto Scaling", "Object Storage", "Block Storage", "Virtual Machines"]
    },
    "Database Administrator": {
        "Skills": ["Database Design", "Database Tuning", "Backup and Recovery", "Security Management", "Performance Monitoring", "Capacity Planning", "Data Migration", "Troubleshooting", "Scripting", "ETL", "Data Warehousing", "High Availability", "Replication", "Disaster Recovery", "Database Security", "Query Optimization"],
        "Tools": ["Oracle Database", "Microsoft SQL Server", "MySQL", "PostgreSQL", "MongoDB", "Redis", "Cassandra", "Elasticsearch", "SQL Developer", "SSMS", "Toad", "Navicat", "pgAdmin", "DBeaver", "DataGrip", "Percona", "Redgate", "MongoDB Compass", "Informatica", "Talend"],
        "Concepts": ["Relational Databases", "NoSQL Databases", "Normalization", "Indexing", "Replication", "Clustering", "Sharding", "ACID Properties", "CAP Theorem", "Data Integrity", "Data Modeling", "Stored Procedures", "Triggers", "Views", "Transactions", "Concurrency Control", "Locking", "Execution Plans", "Partitioning"]
    },
    "Network Engineer": {
        "Skills": ["Network Design", "Network Configuration", "Network Troubleshooting", "Network Security", "Routing and Switching", "Firewall Management", "VPN Configuration", "Wireless Networking", "Load Balancing", "Network Monitoring", "VoIP", "SDN", "Network Automation", "IP Address Management (IPAM)"],
        "Tools": ["Cisco Packet Tracer", "GNS3", "Wireshark", "SolarWinds", "Nagios", "PRTG", "Putty", "SecureCRT", "Ansible", "Python", "EVE-NG", "Tcpdump", "Nmap", "NetFlow Analyzer", "Cacti", "Zabbix", "F5 Big-IP", "NetBrain"],
        "Concepts": ["TCP/IP", "OSI Model", "LAN/WAN", "VLAN", "Subnetting", "DNS", "DHCP", "BGP", "OSPF", "EIGRP", "MPLS", "SD-WAN", "Network Virtualization", "Cloud Networking", "QoS", "NAT", "VPN", "IPSec", "SSL/TLS", "IPv4/IPv6", "Load Balancing Algorithms", "Intrusion Detection", "SDN Controllers"]
    },
    "System Administrator": {
        "Skills": ["Server Administration", "User Management", "Patch Management", "Backup and Recovery", "Scripting", "Monitoring", "Troubleshooting", "Virtualization", "Cloud Administration", "Security Hardening", "Active Directory Management", "Storage Management", "Disaster Recovery", "System Security"],
        "Tools": ["Active Directory", "Group Policy", "PowerShell", "Bash", "VMware", "Hyper-V", "Nagios", "Zabbix", "Splunk", "Ansible", "Puppet", "Chef", "SCCM", "WSUS", "Veeam", "Proxmox", "Citrix", "Office 365", "Webmin", "Cpanel", "SaltStack"],
        "Concepts": ["Windows Server", "Linux", "DNS", "DHCP", "LDAP", "Kerberos", "RAID", "LVM", "Filesystems", "Networking", "Security", "ITIL", "SLA", "Incident Management", "Change Management", "Asset Management", "Virtual Desktop Infrastructure (VDI)", "Kernel Tuning", "Log Analysis"]
    },
    "Technical Writer": {
        "Skills": ["Technical Writing", "Documentation", "Editing", "Proofreading", "Content Strategy", "Information Architecture", "User Research", "API Documentation", "Software Documentation", "Hardware Documentation", "Video Tutorials", "Knowledge Base Management", "Release Notes", "Copywriting", "Document Design"],
        "Tools": ["Microsoft Word", "Google Docs", "Markdown", "JIRA", "Confluence", "Git", "Sphinx", "Read the Docs", "MadCap Flare", "Adobe FrameMaker", "Snagit", "Visio", "Camtasia", "WordPress", "Zendesk Guide", "Swagger/OpenAPI", "Postman", "GitBook", "Redoc", "Docusaurus", "Canva"],
        "Concepts": ["Style Guides", "Documentation Life Cycle", "Audience Analysis", "Usability", "Accessibility", "Version Control", "Content Management Systems (CMS)", "DITA", "XML", "Simplified Technical English", "Localization", "Single Sourcing", "Structured Authoring", "Information Mapping", "Plagiarism Checking"]
    },
    "AI Engineer": {
        "Languages": ["Python", "C++", "Java", "Lisp", "Prolog", "Julia", "R"],
        "Models": ["Large Language Models (LLMs)", "GPT-4", "GPT-3.5", "Claude", "Llama", "Mistral", "Gemini", "BERT", "RoBERTa", "T5", "CLIP", "Stable Diffusion", "Midjourney", "DALL-E", "Whisper", "YOLO", "ResNet", "ViT (Vision Transformer)"],
        "Frameworks": ["LangChain", "LlamaIndex", "Hugging Face Transformers", "Hugging Face Accelerate", "Hugging Face Diffusers", "TensorFlow", "PyTorch", "Keras", "Autogen", "Semantic Kernel", "DeepSpeed", "Megatron-LM"],
        "Vector Databases": ["Pinecone", "Milvus", "Qdrant", "ChromaDB", "FAISS", "Weaviate", "Pgvector", "Elasticsearch Vector Search"],
        "Tools": ["OpenAI API", "Anthropic API", "Hugging Face Hub", "Replicate", "Ollama", "vLLM", "TensorRT", "ONNX", "RunPod", "Lambda Labs", "Weights & Biases", "Comet.ml", "Promptflow"],
        "Concepts": ["Generative AI", "RAG (Retrieval-Augmented Generation)", "Semantic Search", "Prompt Engineering", "Few-Shot Learning", "Zero-Shot Learning", "Chain-of-Thought", "Instruction Tuning", "Fine-Tuning", "LoRA", "QLoRA", "PEFT", "RLHF", "DPO", "Agentic Workflows", "Vector Embeddings", "Cosine Similarity", "Tokenizer", "Context Window", "Model Quantization", "Hallucination Mitigation", "Guardrails"]
    },
    "Data Engineer": {
        "Languages": ["SQL", "Python", "Scala", "Java", "Go", "Bash"],
        "Frameworks": ["Apache Spark", "Apache Flink", "Apache Beam", "PySpark", "Spark SQL", "Pandas", "Dask", "Ray"],
        "Orchestration": ["Apache Airflow", "Dagster", "Prefect", "Luigi", "Argo Workflows", "Kubeflow Pipelines"],
        "Databases & Warehouses": ["Snowflake", "Google BigQuery", "Amazon Redshift", "Databricks Delta Lake", "Apache Iceberg", "Apache Hudi", "PostgreSQL", "MySQL", "Cassandra", "Scipy", "ClickHouse", "SingleStore", "Elasticsearch"],
        "Data Pipelines & Streaming": ["Apache Kafka", "Apache Pulsar", "Apache Flink", "Spark Streaming", "Confluent", "RabbitMQ", "AWS Kinesis", "GCP Pub/Sub", "dbt (Data Build Tool)", "Fivetran", "Stitch", "Airbyte", "Debezium (CDC)"],
        "Formats & Storage": ["Parquet", "Avro", "ORC", "JSON", "CSV", "HDFS", "Amazon S3", "Google Cloud Storage", "Azure Blob Storage", "MinIO"],
        "Concepts": ["ETL (Extract Transform Load)", "ELT (Extract Load Transform)", "Data Lake", "Data Warehouse", "Data Lakehouse", "Data Modeling", "Star Schema", "Snowflake Schema", "Dimensional Modeling", "Data Governance", "Data Lineage", "Data Quality", "CDC (Change Data Capture)", "Batch Processing", "Stream Processing", "Partitioning", "Schema Registry", "Data Catalog"]
    },
    "Blockchain Developer": {
        "Languages": ["Solidity", "Go", "Rust", "C++", "JavaScript", "TypeScript", "Python", "Vyper", "Move"],
        "Frameworks": ["Truffle", "Hardhat", "Foundry", "Brownie", "Anchor (Solana)", "Substrate (Polkadot)", "OpenZeppelin"],
        "Libraries": ["Web3.js", "Ethers.js", "Web3.py", "Anchor JS"],
        "Platforms": ["Ethereum", "Solana", "Hyperledger Fabric", "Corda", "Polkadot", "Cosmos", "Polygon", "Arbitrum", "Optimism", "Binance Smart Chain (BSC)", "Avalanche"],
        "Concepts": ["Smart Contracts", "Decentralized Applications (dApps)", "Web3", "Consensus Algorithms", "Proof of Work (PoW)", "Proof of Stake (PoS)", "Proof of History (PoH)", "DeFi (Decentralized Finance)", "NFTs (Non-Fungible Tokens)", "Tokenomics", "ERC-20", "ERC-721", "ERC-1155", "Cryptographic Hashing", "Public Key Cryptography", "Zero-Knowledge Proofs (ZKP)", "zk-SNARKs", "IPFS", "DAO (Decentralized Autonomous Organization)", "Layer 2 Scaling", "Bridges", "EVM (Ethereum Virtual Machine)"]
    }
}

# Helper function to get all unique skills in a flat list
def get_all_unique_skills():
    unique_skills = set()
    for role, categories in ATS_SKILLS_DATA.items():
        for category, skills in categories.items():
            unique_skills.update([skill for skill in skills])
    return sorted(list(unique_skills))

# Helper function to get skills for a specific role
def get_skills_for_role(role_name):
    role_data = ATS_SKILLS_DATA.get(role_name)
    if not role_data:
        # Fuzzy match fallback
        from rapidfuzz import process, fuzz
        match = process.extractOne(role_name, list(ATS_SKILLS_DATA.keys()), scorer=fuzz.ratio)
        if match and match[1] >= 80:
            role_data = ATS_SKILLS_DATA[match[0]]
        else:
            return []
    
    skills_list = []
    for category, skills in role_data.items():
        skills_list.extend(skills)
    return skills_list

if __name__ == "__main__":
    # Example Usage
    print(f"Total Unique Skills: {len(get_all_unique_skills())}")
    print(f"Skills for Data Scientist: {len(get_skills_for_role('Data Scientist'))}")
    print(f"Skills for AI Engineer: {len(get_skills_for_role('AI Engineer'))}")