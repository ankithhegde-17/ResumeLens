"""Shared curated learning records. Hours are editorial planning ranges, not mastery claims.

Source curricula were checked on 2026-10-02. Free refers to reading the linked
material, not certification, cloud compute, commercial tools or hosted labs.
"""
import re

SOURCES = {
 'excel': ('Excel help and learning', 'Microsoft', 'https://support.microsoft.com/en-us/excel/', 'Documentation', 'Beginner'),
 'business': ('What is Business Analysis?', 'IIBA', 'https://www.iiba.org/professional-development/career-centre/what-is-business-analysis/', 'Documentation', 'Beginner'),
 'web': ('MDN web development curriculum', 'Mozilla', 'https://developer.mozilla.org/en-US/docs/Learn_web_development', 'Documentation', 'Beginner'),
 'react': ('React Quick Start', 'React', 'https://react.dev/learn', 'Documentation', 'Beginner'),
 'python': ('Python tutorial', 'Python Software Foundation', 'https://docs.python.org/3/tutorial/', 'Documentation', 'Beginner'),
 'sql': ('PostgreSQL tutorial', 'PostgreSQL', 'https://www.postgresql.org/docs/current/tutorial.html', 'Documentation', 'Beginner'),
 'git': ('Pro Git book', 'Git', 'https://git-scm.com/book/en/v2', 'Documentation', 'Beginner'),
 'http': ('HTTP overview', 'Mozilla', 'https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Overview', 'Documentation', 'Beginner'),
 'flask': ('Flask application tutorial', 'Pallets', 'https://flask.palletsprojects.com/en/stable/tutorial/', 'Documentation', 'Beginner'),
 'django': ('Django first application', 'Django Software Foundation', 'https://docs.djangoproject.com/en/stable/intro/tutorial01/', 'Documentation', 'Beginner'),
 'typescript': ('TypeScript handbook', 'Microsoft', 'https://www.typescriptlang.org/docs/handbook/intro.html', 'Documentation', 'Intermediate'),
 'java': ('Learn Java', 'Oracle / OpenJDK', 'https://dev.java/learn/', 'Documentation', 'Beginner'),
 'pandas': ('Pandas getting started', 'pandas', 'https://pandas.pydata.org/docs/getting_started/index.html', 'Documentation', 'Beginner'),
 'numpy': ('NumPy learning resources', 'NumPy', 'https://numpy.org/learn/', 'Documentation', 'Beginner'),
 'statistics': ('OpenIntro Statistics', 'OpenIntro', 'https://www.openintro.org/book/os/', 'Course', 'Beginner'),
 'ml': ('Scikit-learn getting started', 'scikit-learn', 'https://scikit-learn.org/stable/getting_started.html', 'Documentation', 'Intermediate'),
 'torch': ('PyTorch tutorials', 'PyTorch', 'https://docs.pytorch.org/tutorials/', 'Documentation', 'Intermediate'),
 'tensorflow': ('TensorFlow tutorials', 'Google', 'https://www.tensorflow.org/tutorials', 'Documentation', 'Intermediate'),
 'nlp': ('Hugging Face LLM course', 'Hugging Face', 'https://huggingface.co/learn/llm-course/chapter1/1', 'Course', 'Intermediate'),
 'docker': ('Docker getting started', 'Docker', 'https://docs.docker.com/get-started/', 'Documentation', 'Beginner'),
 'kubernetes': ('Kubernetes basics tutorials', 'Kubernetes', 'https://kubernetes.io/docs/tutorials/kubernetes-basics/', 'Documentation', 'Intermediate'),
 'cicd': ('GitHub Actions documentation', 'GitHub', 'https://docs.github.com/en/actions', 'Documentation', 'Intermediate'),
 'terraform': ('Terraform tutorials', 'HashiCorp', 'https://developer.hashicorp.com/terraform/tutorials', 'Documentation', 'Intermediate'),
 'aws': ('Overview of Amazon Web Services', 'AWS', 'https://docs.aws.amazon.com/whitepapers/latest/aws-overview/introduction.html', 'Documentation', 'Beginner'),
 'linux': ('Linux command line for beginners', 'Canonical', 'https://ubuntu.com/tutorials/command-line-for-beginners', 'Documentation', 'Beginner'),
 'security': ('Web Security Academy', 'PortSwigger', 'https://portswigger.net/web-security', 'Lab', 'Beginner'),
 'owasp': ('Web Security Testing Guide', 'OWASP', 'https://owasp.org/projects/web-security-testing-guide', 'Documentation', 'Intermediate'),
 'wireshark': ('Wireshark user guide', 'Wireshark', 'https://www.wireshark.org/docs/wsug_html_chunked/', 'Documentation', 'Beginner'),
 'siem': ('Elastic Security documentation', 'Elastic', 'https://www.elastic.co/docs/solutions/security', 'Documentation', 'Intermediate'),
 'attack': ('MITRE ATT&CK knowledge base', 'MITRE', 'https://attack.mitre.org/', 'Documentation', 'Intermediate'),
 'ux': ('UX basics study guide', 'Nielsen Norman Group', 'https://www.nngroup.com/articles/ux-basics-study-guide/', 'Documentation', 'Beginner'),
 'figma': ('Figma Design help', 'Figma', 'https://help.figma.com/hc/en-us/categories/360002042553-Figma-Design', 'Documentation', 'Beginner'),
 'testing': ('Python unittest guide', 'Python Software Foundation', 'https://docs.python.org/3/library/unittest.html', 'Documentation', 'Beginner'),
 'selenium': ('Selenium documentation', 'Selenium', 'https://www.selenium.dev/documentation/', 'Documentation', 'Intermediate'),
 'postman': ('Postman getting started', 'Postman', 'https://learning.postman.com/docs/getting-started/overview/', 'Documentation', 'Beginner'),
 'flutter': ('Learn Flutter', 'Google', 'https://docs.flutter.dev/learn', 'Documentation', 'Beginner'),
 'android': ('Android developer training', 'Google', 'https://developer.android.com/courses', 'Course', 'Beginner'),
 'mlflow': ('MLflow machine learning documentation', 'MLflow', 'https://mlflow.org/docs/latest/ml/', 'Documentation', 'Intermediate'),
 'powerbi': ('Power BI fundamentals', 'Microsoft', 'https://learn.microsoft.com/en-us/power-bi/fundamentals/', 'Documentation', 'Beginner'),
 'scrum': ('The Scrum Guide', 'Scrum Guides', 'https://scrumguides.org/scrum-guide.html', 'Documentation', 'Beginner'),
 'monitoring': ('Prometheus overview', 'Prometheus', 'https://prometheus.io/docs/introduction/overview/', 'Documentation', 'Intermediate'),
}

def slugify(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')

def resource(key):
    title, provider, url, kind, level = SOURCES[key]
    return dict(title=title, provider=provider, url=url, cost='Free', level=level,
                format=kind, checked='2026-10-02', note='Free learning material; certificates and service usage are not included.')

SKILL_GUIDES = {}

def guide(name, hours, prerequisites, topics, description, usefulness, project, sources, difficulty='Beginner', aliases=()):
    SKILL_GUIDES[name] = dict(name=name, slug=slugify(name), hours=hours, prerequisites=prerequisites.split('|') if prerequisites else [],
                            topics=topics.split('|'), description=description, usefulness=usefulness,
                            practice=project, difficulty=difficulty, aliases=list(aliases),
                            resources=[resource(key) for key in sources.split('|')])

guide('HTML',(12,24),'','Semantic elements|Forms|Accessible labels|Document structure','HTML describes the structure and meaning of a web page.','A sound structure helps users, assistive technology and search engines.','Build a semantic portfolio with a contact form.','web')
guide('CSS',(30,60),'HTML','Cascade|Flexbox and grid|Responsive layouts|Focus states','CSS controls layout and presentation.','It makes interfaces readable across screen sizes.','Create a responsive three-page portfolio.','web')
guide('JavaScript',(60,120),'HTML|CSS','Variables|Functions|Objects|DOM and events|Promises|Fetch|Error handling','JavaScript adds behavior to web interfaces.','It powers interactive forms, API calls and user feedback.','Build a weather dashboard with loading and error states.','web')
guide('React',(50,100),'HTML|CSS|JavaScript','Components|Props|State|Events|Hooks|Forms|API requests|Composition','React builds interfaces from reusable components.','It organizes complex interactive screens and state.','Build a searchable catalog with accessible forms.','react|web')
guide('Git',(8,16),'','Commits|Branches|Merging|Remotes|Pull requests','Git records changes to source code.','Teams can review, combine and recover work.','Track a small project and resolve a practice merge conflict.','git')
guide('Python',(60,120),'','Types|Control flow|Functions|Modules|Files|Exceptions|Virtual environments','Python is a general-purpose programming language.','It is used for automation, analysis, APIs and ML.','Build a CSV reporting command-line tool.','python')
guide('SQL',(25,60),'','Select|Joins|Grouping|Constraints|Transactions|Indexes','SQL queries and manages relational data.','It supports accurate reporting and reliable applications.','Answer ten business questions against a sample database.','sql')
guide('PostgreSQL',(25,50),'SQL','Schema design|Constraints|Transactions|Indexes|Query plans','PostgreSQL is a relational database system.','It stores structured application data with integrity checks.','Design an inventory schema and inspect slow queries.','sql')
guide('REST API',(20,45),'','HTTP methods|Status codes|JSON|Validation|Pagination|Idempotency','An API exposes data and operations through defined requests.','It connects web, mobile and server components.','Design an inventory CRUD API with failure cases.','http|flask',aliases=('restful apis',))
guide('Flask',(25,50),'Python|REST API','Routes|Templates|Requests|Validation|Sessions|Tests','Flask is a small Python web framework.','It supports understandable server-side applications.','Build a three-route app with CSRF and tests.','flask')
guide('Django',(45,80),'Python|SQL|REST API','Models|Views|Templates|Forms|Authentication|Tests','Django is a full-featured Python web framework.','It provides common web application building blocks.','Build a tested library lending app.','django',difficulty='Intermediate')
guide('TypeScript',(25,50),'JavaScript','Types|Interfaces|Unions|Generics|Compiler checks','TypeScript adds static type checking to JavaScript.','It helps catch interface and data-shape mistakes early.','Add type checking to a small API client.','typescript',difficulty='Intermediate')
guide('Java',(70,140),'','Classes|Interfaces|Collections|Exceptions|Streams|Testing','Java is a typed general-purpose language.','It is widely used for backend and enterprise software.','Build a tested library management CLI.','java')
guide('Pandas',(25,50),'Python','DataFrames|Loading data|Missing values|Joins|Grouping','Pandas manipulates tabular data in Python.','It helps clean and summarize datasets repeatably.','Clean a messy sales dataset with an audit report.','pandas')
guide('NumPy',(20,40),'Python','Arrays|Shapes|Indexing|Broadcasting|Vectorization','NumPy provides efficient numerical arrays.','It underpins much of scientific Python and ML.','Implement vectorized dataset summaries.','numpy')
guide('Statistics',(60,120),'','Distributions|Sampling|Uncertainty|Confidence intervals|Hypothesis testing|Regression','Statistics helps reason about data and uncertainty.','It prevents overconfident conclusions from limited observations.','Compare two groups and explain uncertainty and confounders.','statistics')
guide('Data Visualization',(25,50),'','Chart choice|Scales|Accessibility|Misleading graphs|Narrative','Visualization communicates data with charts.','It reveals patterns and explains decisions to others.','Create an accessible dashboard with three explained charts.','powerbi|pandas')
guide('Excel',(20,45),'','Formulas|Tables|Pivot tables|Data cleaning|Charts','Excel is a spreadsheet tool for calculations and analysis.','Many teams use it for operational reporting.','Create an auditable monthly sales workbook.','excel')
guide('Power BI',(30,60),'Data Visualization','Data loading|Relationships|Measures|Filters|Reports','Power BI models data and presents interactive reports.','It helps teams explore consistent business metrics.','Build a sales report with a documented metric dictionary.','powerbi')
guide('Machine Learning',(100,200),'Python|NumPy|Statistics','Supervised learning|Baselines|Splits|Leakage|Cross-validation|Metrics','ML learns patterns from examples rather than fixed rules.','It supports prediction when evaluated responsibly.','Compare a baseline and classifier on held-out data.','ml|statistics',difficulty='Intermediate')
guide('Scikit-learn',(30,60),'Machine Learning|Pandas','Estimators|Transformers|Pipelines|Model selection|Metrics','Scikit-learn provides standard ML algorithms and evaluation tools.','Its pipelines help make experiments reproducible and avoid leakage.','Build a cross-validated tabular classification pipeline.','ml',difficulty='Intermediate')
guide('Model Evaluation',(30,60),'Machine Learning','Precision and recall|Calibration|Error analysis|Subgroup checks|Drift','Model evaluation checks performance and failure modes.','It makes model claims testable instead of relying on training scores.','Write an error-analysis report with limitations.','ml|statistics',difficulty='Intermediate',aliases=('model evaluation',))
guide('Feature Engineering',(30,60),'Pandas|Machine Learning','Encoding|Scaling|Leakage prevention|Feature selection|Pipelines','Feature engineering prepares useful model inputs.','It improves the representation of real-world data.','Compare features using cross-validation and document leakage checks.','ml|pandas',difficulty='Intermediate')
guide('PyTorch',(70,140),'Machine Learning|NumPy','Tensors|Autograd|Training loops|Datasets|Checkpoints','PyTorch builds and trains neural networks.','It supports flexible deep-learning research and applications.','Train a small image classifier with an error report.','torch',difficulty='Intermediate')
guide('TensorFlow',(70,140),'Machine Learning|NumPy','Tensors|Keras|Training|Validation|Saving models','TensorFlow is a deep-learning toolkit.','It offers tools for training and deploying neural models.','Train and export a small classifier.','tensorflow',difficulty='Intermediate')
guide('Deep Learning',(120,240),'Machine Learning|NumPy','Neural networks|Optimization|Regularization|CNNs|Attention','Deep learning uses layered neural networks.','It handles complex image and language representations.','Compare a small neural model with a simpler baseline.','torch|tensorflow',difficulty='Advanced',aliases=('deep learning',))
guide('NLP',(60,120),'Machine Learning','Tokenization|Embeddings|Text classification|Evaluation|Privacy','NLP applies computation to language data.','It enables search, classification and language assistance.','Build a text classifier and inspect ambiguous examples.','nlp',difficulty='Intermediate')
guide('Computer Vision',(70,140),'Deep Learning','Image preprocessing|Classification|Transfer learning|Augmentation|Errors','Computer vision extracts useful signals from images.','It supports inspection and document/image applications.','Build an image classification demo with clear failure cases.','torch|tensorflow',difficulty='Advanced')
guide('Testing',(25,50),'','Test plans|Boundary cases|Assertions|Fixtures|Mocks|Regression','Testing verifies expected software behavior.','It reduces regressions and makes changes safer.','Design API cases including invalid requests and ownership; learn Python before the unittest coding exercises.','testing|owasp')
guide('Selenium',(25,50),'Testing','Locators|Waits|Forms|Navigation|Test isolation','Selenium automates real browsers.','It checks user-facing workflows beyond unit tests.','Automate a login and form workflow on a test app.','selenium',difficulty='Intermediate')
guide('Postman',(10,25),'REST API','Requests|Environments|Assertions|Collections','Postman helps explore and test APIs.','It makes HTTP workflows inspectable and reproducible.','Create a collection with positive and negative API cases.','postman')
guide('Linux',(25,60),'','Files|Permissions|Processes|Logs|Packages|Services','Linux is an operating-system family with useful server tools.','Many servers and containers run on Linux.','Diagnose a failed service in an isolated virtual machine.','linux')
guide('Networking',(40,80),'','TCP/IP|DNS|HTTP|Ports|Routing|TLS','Networking explains how systems communicate.','It supports reliable deployments and troubleshooting.','Explain a DNS and HTTP trace in a local lab.','http|wireshark')
guide('Shell Scripting',(20,45),'Linux','Variables|Pipes|Exit codes|Functions|Safe automation','Shell scripts automate command-line tasks.','They make repeatable system operations easier.','Write a backup script with failure handling.','linux',aliases=('shell scripting','bash scripting'))
guide('AWS',(40,90),'Networking','Shared responsibility|Compute|Storage|Identity|Costs','AWS supplies cloud infrastructure and managed services.','It supports scalable applications, with security and billing responsibilities.','Design a small deployment and budget before provisioning anything.','aws')
guide('Cloud Fundamentals',(35,70),'Networking','Service models|Regions|Identity|Reliability|Cost management','Cloud fundamentals explain on-demand computing services.','They help choose services and manage risks across vendors.','Compare two cloud architecture options on paper.','aws',aliases=('cloud fundamentals','cloud computing'))
guide('Docker',(25,50),'Linux','Images|Containers|Dockerfiles|Volumes|Networks|Compose','Docker packages applications into containers.','It helps make environments repeatable.','Containerize a small API with a persistent database.','docker')
guide('CI/CD',(30,60),'Git|Testing','Workflow triggers|Builds|Tests|Secrets|Artifacts|Deployment gates','CI/CD automates safe build, test and release workflows.','It makes releases repeatable and problems visible earlier.','Create a test-and-build pipeline with a manual release gate.','cicd',difficulty='Intermediate',aliases=('ci/cd','continuous integration','github actions'))
guide('Kubernetes',(60,120),'Docker|Linux|Networking','Pods|Deployments|Services|Config|Health probes|Rollouts','Kubernetes orchestrates container workloads.','It manages deployment and recovery of distributed services.','Deploy a local app and practice a rollback.','kubernetes',difficulty='Advanced',aliases=('kubernetes','k8s'))
guide('Terraform',(35,70),'Cloud Fundamentals','Providers|Plans|State|Modules|Safe changes','Terraform describes infrastructure as code.','It makes infrastructure changes reviewable and repeatable.','Plan a small infrastructure module without creating billable resources.','terraform',difficulty='Intermediate',aliases=('terraform','infrastructure as code'))
guide('Monitoring',(30,60),'Linux|Networking','Metrics|Logs|Alerts|Service indicators|Runbooks','Monitoring tracks system behavior and failures.','It helps diagnose reliability issues and reduce alert noise.','Instrument a local API and write an actionable alert.','monitoring',difficulty='Intermediate',aliases=('monitoring','prometheus'))
guide('Authentication',(35,70),'REST API','Sessions|Identity|Access control|CSRF|Secure cookies','Authentication verifies identity; authorization controls access.','Both protect private application data.','Test owner-only access and session expiry in a local app.','flask|owasp',difficulty='Intermediate',aliases=('authentication','authorization'))
guide('Data Structures',(60,120),'Python','Arrays|Maps|Stacks|Trees|Complexity|Algorithms','Data structures organize information for efficient use.','They support reasoning about performance and correctness.','Implement and benchmark a search index.','python|java',aliases=('data structures','algorithms'))
guide('Software Design',(50,100),'Python|Testing','Interfaces|Modularity|Error handling|Trade-offs|Maintainability','Software design organizes code and responsibilities.','It helps teams change systems without accidental coupling.','Refactor a small application and explain the boundaries.','java|testing',difficulty='Intermediate',aliases=('software design','design patterns'))
guide('Figma',(15,35),'','Frames|Components|Auto layout|Styles|Collaboration','Figma supports interface design and collaboration.','It connects visual exploration with reusable design components.','Create a component-based mobile prototype.','figma')
guide('UI/UX',(40,80),'','User needs|Interaction design|Information architecture|Accessibility','UI/UX focuses on useful, understandable experiences.','It makes products easier to navigate and use.','Redesign a confusing workflow and explain design decisions.','ux|web')
guide('User Research',(25,55),'UI/UX','Research questions|Interviews|Consent|Usability tests|Synthesis','User research investigates needs and behavior.','It grounds design choices in evidence rather than preference.','Run a small consent-based usability study and summarize limitations.','ux')
guide('Prototyping',(20,40),'Figma|UI/UX','Wireframes|Flows|Interactions|Testing|Iteration','Prototypes make design ideas testable before full implementation.','They help teams discover usability problems early.','Prototype a booking flow and revise after feedback.','figma|ux')
guide('Cybersecurity',(70,140),'Networking|Linux','Threat models|Access control|Web risks|Defense in depth|Ethics','Cybersecurity protects systems and information.','It supports risk reduction and responsible incident handling.','Document and fix vulnerabilities only in an authorized lab.','security|owasp')
guide('Wireshark',(20,45),'Networking','Capture|Filters|Protocols|DNS analysis|Privacy','Wireshark inspects network packets.','It helps diagnose communication and security issues.','Analyze a synthetic packet trace, not other people’s traffic.','wireshark')
guide('SIEM',(50,100),'Cybersecurity|Linux','Log ingestion|Queries|Detection rules|Triage|False positives','SIEM systems combine logs for security analysis.','They help analysts investigate alerts across systems.','Create a local synthetic-log detection and triage lab.','siem|attack',difficulty='Intermediate')
guide('Incident Response',(40,80),'Cybersecurity|SIEM','Triage|Containment|Evidence|Escalation|Lessons learned','Incident response coordinates investigation and recovery.','It reduces harm while preserving evidence and accountability.','Write a tabletop incident timeline and escalation playbook.','attack|owasp',difficulty='Intermediate',aliases=('incident response','incident handling'))
guide('Threat Detection',(50,100),'SIEM|Networking','ATT&CK mapping|Detection hypotheses|Rules|Testing|False positives','Threat detection turns evidence into testable alert logic.','It helps distinguish suspicious activity from normal behavior.','Test an ATT&CK-mapped rule against synthetic logs.','attack|siem',difficulty='Intermediate',aliases=('threat detection','threat hunting'))
guide('Business Analysis',(45,90),'','Stakeholders|Problem framing|Requirements|Process maps|Acceptance criteria','Business analysis clarifies needs and feasible improvements.','It connects stakeholders, data and implementation teams.','Write a process-improvement brief with measurable acceptance criteria.','business|scrum|powerbi',aliases=('business analysis','requirements gathering'))
guide('Communication',(15,35),'','Audience|Clear writing|Evidence|Presentations|Feedback','Communication shares information clearly and responsibly.','Technical work needs explanations that others can act on.','Present a dashboard recommendation and its limitations.','scrum|ux')
guide('Agile',(10,25),'','Iterative delivery|Backlogs|Feedback|Retrospectives','Agile approaches use short feedback cycles to adapt work.','They support collaboration under changing requirements.','Plan two iterations and review what changed.','scrum')
guide('Flutter',(60,120),'','Dart basics|Widgets|State|Navigation|Networking|Testing','Flutter builds cross-platform applications.','It enables shared UI code across supported platforms.','Build an offline-capable habit tracker.','flutter|android')
guide('Mobile Development',(60,120),'REST API','Platform lifecycle|Layouts|Accessibility|Storage|Permissions|Testing','Mobile development builds applications for handheld devices.','It requires care with connectivity, permissions and limited screens.','Build a notes app with offline storage and sync error handling.','android|flutter',aliases=('mobile development','android development'))
guide('MLflow',(35,70),'Machine Learning|Python','Experiments|Metrics|Artifacts|Registry|Reproducibility','MLflow records experiments and manages model artifacts.','It helps teams reproduce training and trace deployed models.','Track experiments and document a model promotion decision.','mlflow',difficulty='Intermediate',aliases=('mlflow','experiment tracking','model registry'))
guide('Model Serving',(40,80),'Machine Learning|REST API|Docker','Inference APIs|Validation|Latency|Versioning|Monitoring','Model serving exposes trained models for prediction.','It connects experiments to usable applications.','Serve a model with input validation and latency tests.','mlflow|flask',difficulty='Intermediate',aliases=('model serving','model deployment'))
guide('ML Pipelines',(60,120),'MLflow|CI/CD|Model Evaluation','Data checks|Training stages|Validation gates|Artifacts|Reproducible runs','ML pipelines connect repeatable data and model operations.','They reduce fragile manual steps and make changes auditable.','Automate a validated training-to-registry workflow.','mlflow|cicd',difficulty='Advanced',aliases=('ml pipelines','machine learning pipelines'))
guide('Experimentation',(40,80),'Statistics|SQL','Hypotheses|Experimental design|Bias|Uncertainty|Business impact','Experimentation tests decisions with controlled comparisons.','It supports careful interpretation of product or business changes.','Design an A/B experiment and state its assumptions.','statistics|pandas',difficulty='Intermediate',aliases=('experimentation','a/b testing'))

GUIDES_BY_SLUG = {g['slug']: g for g in SKILL_GUIDES.values()}
