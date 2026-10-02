"""Explicit aliases, genuine source quotes, and conservative negation checks."""
import re

SKILLS = {
    'Python': ['python'], 'Java': ['java'], 'C++': ['c++'],
    'JavaScript': ['javascript', 'js'], 'TypeScript': ['typescript'],
    'HTML': ['html'], 'CSS': ['css'], 'React': ['react', 'reactjs', 'react.js'],
    'Flask': ['flask'], 'Django': ['django'], 'REST API': ['rest api', 'restful api', 'rest apis'],
    'SQL': ['sql'], 'PostgreSQL': ['postgresql', 'postgres'], 'Git': ['git'],
    'Pandas': ['pandas'], 'NumPy': ['numpy'], 'Excel': ['excel'],
    'Power BI': ['power bi', 'powerbi'], 'Tableau': ['tableau'],
    'Data Visualization': ['data visualization', 'data visualisation', 'data viz'],
    'Statistics': ['statistics', 'statistical analysis'],
    'Machine Learning': ['machine learning'], 'Scikit-learn': ['scikit-learn', 'sklearn'],
    'PyTorch': ['pytorch'], 'TensorFlow': ['tensorflow'],
    'NLP': ['nlp', 'natural language processing'], 'Computer Vision': ['computer vision'],
    'Testing': ['unit testing', 'software testing', 'test cases', 'pytest'],
    'Selenium': ['selenium'], 'Postman': ['postman'], 'Agile': ['agile'],
    'Linux': ['linux'], 'AWS': ['aws', 'amazon web services'], 'Docker': ['docker'],
    'Networking': ['networking', 'tcp/ip', 'network protocols'],
    'Cybersecurity': ['cybersecurity', 'cyber security'], 'Wireshark': ['wireshark'],
    'SIEM': ['siem'], 'Figma': ['figma'], 'UI/UX': ['ui/ux', 'ux design', 'ui design'],
    'Prototyping': ['prototyping', 'wireframes', 'wireframing'],
    'User Research': ['user research', 'usability testing'],
    'Communication': ['communication'], 'Problem Solving': ['problem solving', 'problem-solving'],
}

# Reuse the learning vocabulary; explicit names only, no inferred proficiency.
from skill_guides import SKILL_GUIDES
for _name, _guide in SKILL_GUIDES.items():
    if _name not in SKILLS:
        SKILLS[_name] = [_name.lower(), *_guide['aliases']]


def has_alias(text, alias):
    # These boundaries distinguish Java from JavaScript and Git from GitHub.
    return re.search(r'(?<![\w])' + re.escape(alias) + r'(?![\w])', text, re.I)


def candidates(pages):
    result = []
    for name, aliases in SKILLS.items():
        evidence = []
        for page in pages:
            for line in page['text'].splitlines():
                line = line.strip()
                if any(has_alias(line, alias) for alias in aliases):
                    caution = bool(re.search(r'\b(no experience|not familiar|do not know|never used|want to learn|plan to learn|learning goals|not yet)\b', line, re.I))
                    evidence.append(dict(page=page['number'], quote=line[:400], caution=caution))
        if evidence:
            result.append(dict(name=name, evidence=evidence[:4], caution=all(e['caution'] for e in evidence)))
    return sorted(result, key=lambda x: x['name'].lower())


def names_from_text(text):
    return [s['name'] for s in candidates([dict(number=1, text=text)]) if not s['caution']]
