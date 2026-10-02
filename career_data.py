"""18 curated paths, separate from immutable saved analysis snapshots.

Sequences follow the linked skill curricula; effort includes overlapping practice
and projects, not a sum of all skill durations. See docs/CAREER_ROADMAPS.md.
"""
from skill_guides import SKILL_GUIDES, slugify

CATEGORIES = ('Software Development', 'Data & AI', 'Design', 'Cloud & Infrastructure', 'Cybersecurity', 'Quality', 'Business')
DISCLAIMER = ('Career recommendations and learning timelines are educational guidance based on your resume and selected goals. '
               'They are not guarantees of employment or professional competency.')

def path(id, title, category, description, core, supporting, tools, fundamentals, advanced, sequence, effort, projects, difficulty='Foundation → intermediate'):
    split = lambda text: text.split('|') if text else []
    stages = []
    for text in sequence:
        stage, skills = text.split(':', 1)
        stages.append(dict(title=stage, skills=split(skills)))
    return dict(id=id, slug=slugify(title), title=title, category=category, description=description,
                core=split(core), supporting=split(supporting), tools=split(tools), fundamentals=split(fundamentals),
                advanced=split(advanced), stages=stages, effort=effort, difficulty=difficulty,
                projects=[dict(title=p[0], description=p[1], difficulty=level, skills=split(p[2]))
                          for p, level in zip(projects, ('Beginner','Intermediate','Advanced'))])

CAREERS = [
path('frontend','Frontend Developer','Software Development','Build accessible, responsive browser interfaces.',
 'HTML|CSS|JavaScript|React|Git','Testing|Communication','React|TypeScript','REST API|UI/UX','TypeScript|Authentication',
 ['Web structure:HTML|CSS','Browser behavior:JavaScript|REST API','Reusable interfaces:Git|React','Quality and delivery:Testing|TypeScript|Authentication'],(220,440),
 [('Personal portfolio','Build semantic pages that work with keyboard and phone screens.','HTML|CSS'),('Weather dashboard','Handle API loading, errors and accessible search.','JavaScript|REST API'),('Storefront UI','Create reusable components, tests and an authenticated flow in a local demo.','React|Testing|Authentication')]),
path('ui-ux','UI/UX Designer','Design','Investigate user needs and design testable, accessible product experiences.',
 'UI/UX|Figma|User Research|Prototyping','Communication','Figma','UI/UX|User Research','HTML|CSS',
 ['Understand people:UI/UX|User Research','Explore layouts:Figma','Test interactions:Prototyping','Handoff and iteration:Communication|HTML|CSS'],(180,360),
 [('Task-flow study','Map a confusing workflow and identify evidence-backed problems.','UI/UX|User Research'),('Booking prototype','Create and test a mobile flow with consent-based participants.','Figma|Prototyping'),('Design case study','Document research, iterations, accessibility and a developer handoff.','Communication|HTML|CSS')]),
path('data-analyst','Data Analyst','Data & AI','Clean, query and explain data to support business decisions.',
 'SQL|Excel|Python|Pandas|Data Visualization','Communication|Statistics','Power BI|Pandas','Statistics','Experimentation',
 ['Reliable reporting:Excel|SQL','Repeatable cleaning:Python|Pandas','Explain patterns:Statistics|Data Visualization|Power BI','Decision support:Communication|Experimentation'],(200,400),
 [('Sales workbook','Audit formulas and explain monthly trends.','Excel'),('SQL customer analysis','Answer business questions with joins and documented assumptions.','SQL|Pandas'),('Dashboard decision brief','Present metrics, uncertainty and actionable recommendations.','Power BI|Statistics|Communication')]),
path('ml-intern','Machine Learning Intern','Data & AI','Prepare datasets and evaluate basic models under supervision.',
 'Python|Machine Learning|Scikit-learn|NumPy|Statistics','Pandas|Git','Scikit-learn|Pandas','Statistics|Model Evaluation','PyTorch',
 ['Numerical foundations:Python|NumPy|Pandas','Reason about data:Statistics','Learn from examples:Machine Learning|Scikit-learn','Report experiments:Model Evaluation|Git'],(280,560),
 [('Dataset explorer','Clean data and document missing values without target leakage.','Pandas|NumPy'),('Baseline classifier','Compare a simple baseline and classifier on a held-out split.','Scikit-learn|Machine Learning'),('Experiment report','Run cross-validation, analyze errors and write limitations.','Model Evaluation|Statistics|Git')]),
path('python-backend','Python Backend Developer','Software Development','Build validated APIs and reliable server-side applications.',
 'Python|SQL|Flask|REST API|Git','Testing|Communication','Flask|PostgreSQL','Authentication','Django|Docker',
 ['Programming workflow:Python|Git','Data and HTTP:SQL|PostgreSQL|REST API','Application development:Flask|Authentication','Reliable operations:Testing|Docker'],(260,520),
 [('Reporting CLI','Process files with clear validation and errors.','Python'),('Inventory API','Design data constraints, pagination and tested endpoints.','SQL|Flask|REST API'),('Private workspace','Build owner-only sessions, regression tests and container deployment.','Authentication|Testing|Docker')]),
path('qa-engineer','QA Engineer','Quality','Design test coverage, reproduce defects and automate meaningful checks.',
 'Testing|Selenium|Postman|Python|Git','SQL|Agile','Selenium|Postman','REST API|Testing','CI/CD',
 ['Test thinking:Testing|REST API','API investigation:Postman|SQL','Automation practice:Python|Git|Selenium','Release confidence:CI/CD|Agile'],(180,360),
 [('Exploratory test plan','Document boundary cases and reproducible bug reports.','Testing'),('API collection','Exercise valid, invalid and unauthorized requests.','Postman|REST API'),('Regression pipeline','Run isolated browser and API tests in CI with useful failure reports.','Selenium|Python|CI/CD')]),
path('cloud-support','Cloud Support Associate','Cloud & Infrastructure','Troubleshoot cloud services, permissions and connectivity; not design every cloud system.',
 'Linux|AWS|Networking|Docker|Python','Communication|Monitoring','AWS|Docker','Cloud Fundamentals|Networking','Terraform',
 ['Understand systems:Linux|Networking','Cloud service basics:Cloud Fundamentals|AWS','Troubleshoot workloads:Docker|Monitoring','Support automation:Python|Communication'],(200,400),
 [('Service diagnosis','Investigate a failed local service and write a runbook.','Linux'),('Cloud support scenarios','Explain IAM, storage and connectivity problems without paid provisioning.','AWS|Networking'),('Support toolkit','Automate log summaries and document escalation criteria.','Python|Monitoring|Communication')]),
path('security','Cybersecurity Analyst','Cybersecurity','Assess risks and investigate security evidence in authorized environments.',
 'Cybersecurity|Networking|Linux|Wireshark|SIEM','Communication|Python','Wireshark|SIEM','Authentication|Networking','Threat Detection|Incident Response',
 ['System foundations:Linux|Networking','Understand attack surfaces:Authentication|Cybersecurity','Analyze evidence:Wireshark|SIEM','Risk and response:Threat Detection|Incident Response|Communication'],(320,640),
 [('Network analysis lab','Inspect synthetic traces and explain normal vs suspicious traffic.','Wireshark|Networking'),('Web vulnerability lab','Practice approved academy labs and document mitigations.','Cybersecurity|Authentication'),('Security investigation','Correlate synthetic logs and write an evidence-backed response brief.','SIEM|Incident Response')]),
path('full-stack','Full Stack Developer','Software Development','Connect accessible web interfaces to secure APIs and relational data.',
 'HTML|CSS|JavaScript|React|Python|SQL|REST API|Git','Testing|Communication','Flask|PostgreSQL|Docker','Authentication','TypeScript|CI/CD',
 ['Web foundations:HTML|CSS|JavaScript|Git','UI and HTTP:React|REST API','Server and data:Python|SQL|PostgreSQL|Flask','Secure integration:Authentication|Testing','Deliver a complete system:Docker|CI/CD'],(450,850),
 [('Interactive portfolio','Build a responsive UI with real form validation.','HTML|CSS|JavaScript'),('Task management app','Connect React to a Flask API and relational database.','React|Flask|PostgreSQL'),('Private team workspace','Test ownership, containers and release gates end to end.','Authentication|Docker|CI/CD')]),
path('software-engineer','Software Engineer','Software Development','Design maintainable software, reason about algorithms and test system behavior.',
 'Python|Data Structures|Software Design|Testing|Git','Communication|Agile','Java|SQL','Data Structures|Software Design','CI/CD|Authentication',
 ['Programming fluency:Python|Git','Algorithmic reasoning:Data Structures','Maintainable systems:Testing|Software Design|SQL','Team delivery:Agile|CI/CD|Communication','Broaden language skills:Java'],(420,840),
 [('Searchable CLI','Choose data structures and measure complexity.','Python|Data Structures'),('Library service','Design modular interfaces, persistence and regression tests.','Software Design|SQL|Testing'),('Resilient application','Write failure-mode tests, CI and a design-tradeoff report.','CI/CD|Software Design|Communication')]),
path('data-scientist','Data Scientist','Data & AI','Explore data, design experiments and communicate defensible model-based insights.',
 'Python|SQL|Statistics|Pandas|Machine Learning|Model Evaluation','Communication|Data Visualization','NumPy|Scikit-learn','Statistics|Experimentation','Feature Engineering|Model Serving',
 ['Data programming:Python|NumPy|Pandas|SQL','Statistical reasoning:Statistics|Data Visualization','Experiments and baselines:Experimentation|Machine Learning|Scikit-learn','Model judgment:Model Evaluation|Feature Engineering','Communicate and operationalize:Communication|REST API|Docker|Model Serving'],(500,1000),
 [('Exploration report','Analyze a public dataset with uncertainty and quality checks.','Pandas|Statistics'),('Experiment proposal','State a hypothesis, confounders and an analysis plan.','Experimentation|SQL'),('Decision-support model','Evaluate a pipeline, document errors and demonstrate inference.','Scikit-learn|Model Evaluation|Model Serving')], 'Foundation → advanced'),
path('ai-ml-engineer','AI/ML Engineer','Data & AI','Engineer model training and production inference, beyond beginner experimentation.',
 'Python|Machine Learning|Model Evaluation|Deep Learning|Model Serving','Testing|Git|Statistics','PyTorch|Docker|REST API','Software Design|Model Evaluation','NLP|Computer Vision|Monitoring',
 ['Programming and numerical work:Python|NumPy|Pandas|Git','Statistical ML:Statistics|Machine Learning|Scikit-learn|Model Evaluation','Neural models:Deep Learning|PyTorch','Production inference:REST API|Docker|Model Serving|Testing','Specialize responsibly:NLP|Computer Vision|Monitoring'],(650,1300),
 [('Tabular baseline','Measure leakage-free validation and inference behavior.','Scikit-learn|Model Evaluation'),('Neural application','Compare a neural model against a baseline and inspect failures.','PyTorch|Deep Learning'),('Inference service','Validate inputs, benchmark latency and monitor model/service failures.','Model Serving|Docker|Monitoring')], 'Intermediate → advanced'),
path('devops','DevOps Engineer','Cloud & Infrastructure','Automate software delivery and operate services with reliable feedback loops.',
 'Linux|Networking|Git|Docker|CI/CD|Terraform','Python|Testing','Kubernetes|AWS|Monitoring','Cloud Fundamentals|Shell Scripting','Kubernetes|Monitoring',
 ['Operate a system:Linux|Networking|Git|Shell Scripting','Package and test:Docker|Testing','Automate delivery:CI/CD','Cloud and infrastructure:Cloud Fundamentals|AWS|Terraform','Orchestrate and observe:Kubernetes|Monitoring'],(450,900),
 [('Containerized app','Package an API with reproducible local dependencies.','Docker'),('Delivery pipeline','Test and build artifacts with protected deployment gates.','Git|CI/CD'),('Infrastructure lab','Run a local cluster, test rollbacks and document monitoring/runbooks.','Kubernetes|Terraform|Monitoring')]),
path('cloud-engineer','Cloud Engineer','Cloud & Infrastructure','Design and provision secure, observable cloud infrastructure.',
 'Cloud Fundamentals|AWS|Networking|Linux|Terraform','Python|Communication','Docker|Terraform|Monitoring','Authentication|Networking','Kubernetes|CI/CD',
 ['Infrastructure foundations:Linux|Networking|Cloud Fundamentals','Secure cloud design:AWS|Authentication','Repeatable provisioning:Terraform|Git','Workload operations:Docker|Monitoring','Delivery and resilience:Testing|CI/CD|Kubernetes'],(400,800),
 [('Architecture brief','Explain identity, network boundaries and a cost budget.','AWS|Networking'),('Infrastructure plan','Build reusable modules and review plans without billable deployment.','Terraform|Git'),('Recovery exercise','Test restore/rollback and write operational runbooks in a local lab.','Docker|Monitoring|Testing')]),
path('business-analyst','Business Analyst','Business','Clarify stakeholder needs and translate business questions into testable requirements.',
 'Business Analysis|Communication|Excel|SQL','Statistics|Agile','Power BI','Business Analysis|Experimentation','Python|Data Visualization',
 ['Frame the problem:Business Analysis|Communication','Analyze evidence:Excel|SQL|Statistics','Visualize decisions:Data Visualization|Power BI','Validate improvements:Agile|Experimentation'],(180,380),
 [('Process map','Interview consenting participants and document pain points.','Business Analysis|Communication'),('KPI analysis','Write a metric dictionary and query an example dataset.','Excel|SQL'),('Improvement proposal','Combine dashboard, acceptance criteria and an experiment plan.','Power BI|Experimentation|Agile')]),
path('mobile-app','Mobile App Developer','Software Development','Build accessible mobile experiences that handle offline use and device constraints.',
 'Mobile Development|Flutter|REST API|Testing|Git','UI/UX|Communication','Flutter','Authentication|Networking','CI/CD|Software Design',
 ['Platform and interface basics:REST API|Mobile Development|UI/UX','Cross-platform building:Flutter|Git','Reliable device behavior:Authentication|Testing','Release workflow:CI/CD|Software Design'],(350,700),
 [('Habit tracker','Build accessible screens with local storage.','Flutter|Mobile Development'),('Offline notes app','Handle sync conflicts, permissions and connectivity failures.','REST API|Authentication'),('Release-quality prototype','Add tests, automated builds and a privacy-aware design report.','Testing|CI/CD|Software Design')]),
path('soc-analyst','SOC Analyst','Cybersecurity','Triage alerts, correlate logs and escalate incidents using operational playbooks.',
 'Networking|Linux|SIEM|Threat Detection|Incident Response','Communication|Python','SIEM|Wireshark','Cybersecurity','Shell Scripting',
 ['Read system evidence:Linux|Networking|Wireshark','Security foundations:Cybersecurity','Monitor and triage:SIEM|Threat Detection','Respond and hand off:Incident Response|Communication','Reduce repetitive work:Python|Shell Scripting'],(300,600),
 [('Log triage lab','Classify synthetic events and identify missing evidence.','Linux|Networking'),('Detection casebook','Test alert rules and document false positives.','SIEM|Threat Detection'),('Incident tabletop','Build a timeline, escalation path and containment decisions in a lab.','Incident Response|Communication')]),
path('mlops','MLOps Engineer','Data & AI','Automate reproducible ML pipelines, model delivery and monitoring.',
 'Machine Learning|Python|Docker|CI/CD|MLflow|ML Pipelines','Linux|Git|Model Evaluation','Kubernetes|Terraform|Monitoring','Model Evaluation|Software Design','Kubernetes|Threat Detection',
 ['Software and systems:Python|Linux|Git|Networking|Testing','Understand model behavior:NumPy|Pandas|Statistics|Machine Learning|Model Evaluation','Package and track:Docker|MLflow|REST API|Model Serving','Automate model operations:CI/CD|ML Pipelines','Operate at scale:Cloud Fundamentals|AWS|Terraform|Kubernetes|Monitoring'],(600,1200),
 [('Tracked experiment','Record data versions, parameters, metrics and artifacts.','MLflow|Model Evaluation'),('Validated training pipeline','Add quality checks and a model promotion gate.','ML Pipelines|CI/CD'),('Monitored model release','Version an inference service and exercise rollback/drift alerts locally.','Model Serving|Kubernetes|Monitoring')], 'Intermediate → advanced'),
]
BY_ID = {c['id']: c for c in CAREERS}
BY_SLUG = {c['slug']: c for c in CAREERS}

def compact_role(career):
    """Only score metadata belongs in analysis/list responses, not roadmap bodies."""
    return dict(id=career['id'], title=career['title'], slug=career['slug'], category=career['category'],
                description=career['description'], required=[dict(skill=s, weight=3 if i < 2 else 2) for i,s in enumerate(career['core'])],
                optional=list(dict.fromkeys(career['supporting'] + career['advanced'])), project=career['projects'][1]['description'])

def alignment_label(score):
    return 'Strong skill alignment' if score >= 75 else 'Moderate skill alignment' if score >= 45 else 'Developing alignment' if score > 0 else 'Several foundational skills still need development'

def personalize(career, record, progress, hours):
    skills = {s['name']: s for s in record['result']['skills']} if record else {}
    steps = []
    seen = set()
    for stage in career['stages']:
        for name in stage['skills']:
            if name in seen:
                continue
            seen.add(name)
            guide = SKILL_GUIDES[name]
            evidence = skills.get(name)
            steps.append(dict(guide, stage=stage['title'], status=progress.get(guide['slug'], 'not_started'),
                              detected=bool(evidence), evidence=evidence.get('evidence', []) if evidence else [],
                              weeks=(round(guide['hours'][0]/hours,1),round(guide['hours'][1]/hours,1))))
    completed = sum(s['status']=='completed' for s in steps)
    next_step = next((s for s in steps if s['status']!='completed' and not s['detected']), None) or next((s for s in steps if s['status']!='completed'), None)
    return dict(steps=steps, percent=round(100*completed/len(steps)) if steps else 0,
                completed=completed, next_step=next_step, months=tuple(round(n/hours/4.35,1) for n in career['effort']))
