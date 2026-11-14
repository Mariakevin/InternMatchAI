import re

# Exact skill canonical names and their allowed aliases
SKILL_ALIASES: dict[str, str] = {
    "javascript": "javascript",
    "js": "javascript",
    "ecmascript": "javascript",
    "typescript": "typescript",
    "ts": "typescript",
    "python": "python",
    "py": "python",
    "python3": "python",
    "java": "java",  # Note: java is strictly separate from javascript!
    "c++": "c++",
    "cpp": "c++",
    "c#": "c#",
    "csharp": "c#",
    "golang": "go",
    "go": "go",
    "rust": "rust",
    "react": "react",
    "react.js": "react",
    "reactjs": "react",
    "react native": "react native",
    "angular": "angular",
    "angularjs": "angular",
    "vue": "vue",
    "vue.js": "vue",
    "vuejs": "vue",
    "next.js": "next.js",
    "nextjs": "next.js",
    "node.js": "node.js",
    "nodejs": "node.js",
    "node": "node.js",
    "express": "express",
    "express.js": "express",
    "fastapi": "fastapi",
    "django": "django",
    "flask": "flask",
    "html": "html",
    "html5": "html",
    "css": "css",
    "css3": "css",
    "tailwind": "tailwind css",
    "tailwind css": "tailwind css",
    "bootstrap": "bootstrap",
    "sql": "sql",
    "postgresql": "postgresql",
    "postgres": "postgresql",
    "mysql": "mysql",
    "sqlite": "sqlite",
    "mongodb": "mongodb",
    "redis": "redis",
    "graphql": "graphql",
    "rest api": "rest api",
    "restful api": "rest api",
    "apis": "rest api",
    "git": "git",
    "github": "git",
    "gitlab": "git",
    "docker": "docker",
    "kubernetes": "kubernetes",
    "k8s": "kubernetes",
    "aws": "aws",
    "amazon web services": "aws",
    "azure": "azure",
    "gcp": "gcp",
    "google cloud": "gcp",
    "linux": "linux",
    "bash": "bash",
    "shell scripting": "bash",
    "machine learning": "machine learning",
    "ml": "machine learning",
    "deep learning": "deep learning",
    "data science": "data science",
    "data analysis": "data analysis",
    "pandas": "pandas",
    "numpy": "numpy",
    "scikit-learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "tensorflow": "tensorflow",
    "pytorch": "pytorch",
    "nlp": "nlp",
    "natural language processing": "nlp",
    "computer vision": "computer vision",
    "excel": "excel",
    "microsoft excel": "excel",
    "power bi": "power bi",
    "powerbi": "power bi",
    "tableau": "tableau",
    "figma": "figma",
    "ui/ux": "ui/ux",
    "ui design": "ui/ux",
    "ux design": "ui/ux",
    "user experience": "ui/ux",
    "communication": "communication",
    "teamwork": "teamwork",
    "problem solving": "problem solving",
    "project management": "project management",
    "research": "research",
}

# Degree level mapping
DEGREE_LEVELS: dict[str, str] = {
    "b.tech": "undergraduate",
    "btech": "undergraduate",
    "b.e.": "undergraduate",
    "be": "undergraduate",
    "bca": "undergraduate",
    "b.sc": "undergraduate",
    "bsc": "undergraduate",
    "bs": "undergraduate",
    "bachelor": "undergraduate",
    "bba": "undergraduate",
    "b.com": "undergraduate",
    "bcom": "undergraduate",
    "m.tech": "postgraduate",
    "mtech": "postgraduate",
    "m.e.": "postgraduate",
    "me": "postgraduate",
    "mca": "postgraduate",
    "m.sc": "postgraduate",
    "msc": "postgraduate",
    "ms": "postgraduate",
    "master": "postgraduate",
    "mba": "postgraduate",
    "phd": "doctorate",
    "doctorate": "doctorate",
    "diploma": "diploma",
}

# Degree canonical aliases
DEGREE_ALIASES: dict[str, str] = {
    "b.tech": "b.tech",
    "btech": "b.tech",
    "bachelor of technology": "b.tech",
    "b.e": "b.tech",
    "b.e.": "b.tech",
    "be": "b.tech",
    "bachelor of engineering": "b.tech",
    "bca": "bca",
    "bachelor of computer applications": "bca",
    "b.sc": "b.sc",
    "bsc": "b.sc",
    "bs": "b.sc",
    "bachelor of science": "b.sc",
    "m.tech": "m.tech",
    "mtech": "m.tech",
    "m.e": "m.tech",
    "m.e.": "m.tech",
    "me": "m.tech",
    "master of technology": "m.tech",
    "mca": "mca",
    "master of computer applications": "mca",
    "m.sc": "m.sc",
    "msc": "m.sc",
    "ms": "m.sc",
    "master of science": "m.sc",
    "mba": "mba",
    "master of business administration": "mba",
    "phd": "phd",
    "diploma": "diploma",
}

# Discipline canonical aliases
DISCIPLINE_ALIASES: dict[str, str] = {
    "cs": "computer science",
    "cse": "computer science",
    "computer science": "computer science",
    "computer science and engineering": "computer science",
    "computer engineering": "computer science",
    "computer applications": "computer science",
    "it": "information technology",
    "information technology": "information technology",
    "info tech": "information technology",
    "data science": "data science",
    "ai": "artificial intelligence",
    "artificial intelligence": "artificial intelligence",
    "ai/ml": "data science",
    "ece": "electronics and communication",
    "electronics": "electronics and communication",
    "electronics and communication": "electronics and communication",
    "electrical": "electrical engineering",
    "electrical engineering": "electrical engineering",
    "eee": "electrical engineering",
    "mechanical": "mechanical engineering",
    "mechanical engineering": "mechanical engineering",
    "civil": "civil engineering",
    "civil engineering": "civil engineering",
}


def normalize_skill(term: str) -> str:
    cleaned = term.strip().casefold()
    cleaned = re.sub(r"[\s_-]+", " ", cleaned)
    # Check direct match in aliases
    if cleaned in SKILL_ALIASES:
        return SKILL_ALIASES[cleaned]
    # Check without special punctuation
    no_punct = re.sub(r"[^\w\s\+\#\.]", "", cleaned)
    if no_punct in SKILL_ALIASES:
        return SKILL_ALIASES[no_punct]
    return cleaned


def skill_aliases(canonical: str) -> list[str]:
    """Return every alias mapping to the canonical skill, including itself."""
    target = normalize_skill(canonical)
    aliases = {target}
    for alias, canon in SKILL_ALIASES.items():
        if canon == target:
            aliases.add(alias)
    return sorted(aliases, key=len, reverse=True)


def normalize_degree(term: str) -> str:
    cleaned = term.strip().casefold()
    cleaned = re.sub(r"[\s_]+", " ", cleaned)
    if cleaned in DEGREE_ALIASES:
        return DEGREE_ALIASES[cleaned]
    no_dots = cleaned.replace(".", "")
    if no_dots in DEGREE_ALIASES:
        return DEGREE_ALIASES[no_dots]
    return cleaned


def normalize_discipline(term: str) -> str:
    cleaned = term.strip().casefold()
    cleaned = re.sub(r"[\s_]+", " ", cleaned)
    if cleaned in DISCIPLINE_ALIASES:
        return DISCIPLINE_ALIASES[cleaned]
    return cleaned


def normalize_currency(term: str) -> str:
    """Map currency symbols/names to their ISO code, defaulting to USD."""
    cleaned = (term or "").strip().upper().rstrip(".")
    if cleaned in {"₹", "RS", "INR", "RUPEE", "RUPEES"}:
        return "INR"
    if cleaned in {"$", "US$", "USD", "DOLLAR", "DOLLARS"}:
        return "USD"
    if cleaned in {"€", "EUR", "EURO", "EUROS"}:
        return "EUR"
    if cleaned in {"£", "GBP", "POUND", "POUNDS"}:
        return "GBP"
    return cleaned or "USD"


def get_degree_level(degree_name: str) -> str:
    norm = normalize_degree(degree_name)
    if norm in DEGREE_LEVELS:
        return DEGREE_LEVELS[norm]
    # Check degree text substring
    lower = degree_name.casefold()
    if (
        "master" in lower
        or "postgrad" in lower
        or "m." in lower
        or "mtech" in lower
        or "mca" in lower
    ):
        return "postgraduate"
    if "phd" in lower or "doctor" in lower:
        return "doctorate"
    if "diploma" in lower:
        return "diploma"
    if (
        "bachelor" in lower
        or "undergrad" in lower
        or "b." in lower
        or "btech" in lower
        or "bca" in lower
    ):
        return "undergraduate"
    return "undergraduate"
