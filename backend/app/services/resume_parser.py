"""
Resume parsing service.

Strategy:
1. Extract raw text with PyMuPDF (fast, good general extraction).
2. Fall back to / supplement with pdfplumber for tables (education/experience
   often tabular) since pdfplumber handles table structure better.
3. Run spaCy NER + rule-based matching to pull out structured entities:
   name, email, phone, skills, education, experience, cgpa, languages, certs.

This is a heuristic pipeline, not a magic bullet — resumes are wildly
inconsistent in format. We bias toward high precision on skills/contact
info (used for autofill) and best-effort on the rest (shown to the user
for manual correction).
"""
import re
from dataclasses import dataclass, field

import fitz  # PyMuPDF
import pdfplumber
import spacy

from app.core.logging_config import logger

# Load once at module import. In production this should be a singleton
# managed by the app lifecycle (see app.main lifespan) to avoid reloading
# the model per-request.
try:
    _nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.warning("spaCy model 'en_core_web_sm' not found; run `python -m spacy download en_core_web_sm`")
    _nlp = spacy.blank("en")

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_RE = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3,5}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}")
CGPA_RE = re.compile(r"(?:cgpa|gpa)\s*[:\-]?\s*(\d{1,2}(?:\.\d{1,2})?)\s*(?:/\s*(\d{1,2}(?:\.\d{1,2})?))?", re.I)

SECTION_HEADERS = {
    "skills": ["skills", "technical skills", "core competencies", "technologies"],
    "projects": ["projects", "personal projects", "academic projects"],
    "education": ["education", "academic background", "qualification"],
    "experience": ["experience", "work experience", "internships", "professional experience"],
    "certificates": ["certifications", "certificates", "licenses"],
    "languages": ["languages", "spoken languages"],
}

# A reasonably broad seed skill vocabulary for matching against free text.
# In production this should be a maintained, larger taxonomy (or an ML
# classifier), but a curated list works well for tech-internship resumes.
SKILL_VOCAB = [
    "python", "java", "javascript", "typescript", "c++", "c", "c#", "go", "rust",
    "react", "next.js", "vue", "angular", "node.js", "express", "django", "flask",
    "fastapi", "spring boot", "sql", "postgresql", "mysql", "mongodb", "redis",
    "docker", "kubernetes", "aws", "gcp", "azure", "git", "github", "linux",
    "machine learning", "deep learning", "nlp", "computer vision", "pytorch",
    "tensorflow", "scikit-learn", "pandas", "numpy", "data analysis", "ai",
    "ml", "html", "css", "tailwind", "rest api", "graphql", "ci/cd", "jenkins",
    "figma", "excel", "power bi", "tableau", "airflow", "spark", "hadoop",
    "solidity", "blockchain", "unity", "flutter", "kotlin", "swift", "android",
    "ios", "web development", "software development", "devops", "testing",
    "selenium", "playwright", "cybersecurity", "networking",
]


@dataclass
class ParsedResume:
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    skills: list[str] = field(default_factory=list)
    projects: list[str] = field(default_factory=list)
    education: list[dict] = field(default_factory=list)
    experience: list[str] = field(default_factory=list)
    cgpa: str | None = None
    languages: list[str] = field(default_factory=list)
    certificates: list[str] = field(default_factory=list)
    raw_text: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "skills": self.skills,
            "projects": self.projects,
            "education": self.education,
            "experience": self.experience,
            "cgpa": self.cgpa,
            "languages": self.languages,
            "certificates": self.certificates,
        }


def extract_text_pymupdf(file_path: str) -> str:
    text_parts = []
    with fitz.open(file_path) as doc:
        for page in doc:
            text_parts.append(page.get_text())
    return "\n".join(text_parts)


def extract_tables_pdfplumber(file_path: str) -> list[list[list[str]]]:
    tables = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_tables = page.extract_tables()
            if page_tables:
                tables.extend(page_tables)
    return tables


def _find_section(lines: list[str], keys: list[str]) -> str | None:
    """Find header names in text (case-insensitive, whole-line match)."""
    for line in lines:
        cleaned = line.strip().lower().rstrip(":")
        if cleaned in keys:
            return line
    return None


def _extract_section_text(text: str, section_key: str) -> str:
    """
    Grab the block of text between a recognized section header and the
    next recognized section header (naive but effective for most resumes).
    """
    lines = text.split("\n")
    all_headers_lower = {h.lower() for headers in SECTION_HEADERS.values() for h in headers}
    target_headers = SECTION_HEADERS.get(section_key, [])

    start_idx = None
    for i, line in enumerate(lines):
        if line.strip().lower().rstrip(":") in target_headers:
            start_idx = i + 1
            break
    if start_idx is None:
        return ""

    end_idx = len(lines)
    for i in range(start_idx, len(lines)):
        if lines[i].strip().lower().rstrip(":") in all_headers_lower:
            end_idx = i
            break

    return "\n".join(lines[start_idx:end_idx]).strip()


def _extract_skills(text: str) -> list[str]:
    text_lower = text.lower()
    found = set()
    for skill in SKILL_VOCAB:
        # word-boundary-ish match to avoid partial hits like "c" inside "docker"
        pattern = r"(?<![a-zA-Z0-9+#])" + re.escape(skill) + r"(?![a-zA-Z0-9+#])"
        if re.search(pattern, text_lower):
            found.add(skill)
    return sorted(found)


def _extract_name(text: str, doc) -> str | None:
    # Heuristic: the name is usually the first PERSON entity found near the
    # top of the document, or simply the first non-empty line if short.
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text.strip()

    first_lines = [l.strip() for l in text.split("\n")[:5] if l.strip()]
    for line in first_lines:
        if len(line.split()) <= 4 and not EMAIL_RE.search(line) and not PHONE_RE.search(line):
            return line
    return None


def _extract_cgpa(text: str) -> str | None:
    match = CGPA_RE.search(text)
    if match:
        value = match.group(1)
        scale = match.group(2)
        return f"{value}/{scale}" if scale else value
    return None


def _extract_languages(section_text: str) -> list[str]:
    if not section_text:
        return []
    # split on commas/newlines/bullets
    parts = re.split(r"[,\n•\-]", section_text)
    return [p.strip() for p in parts if p.strip() and len(p.strip()) < 30]


def _extract_list_items(section_text: str) -> list[str]:
    if not section_text:
        return []
    lines = [l.strip(" •-\t") for l in section_text.split("\n") if l.strip()]
    return [l for l in lines if l]


def parse_resume(file_path: str) -> ParsedResume:
    """
    Main entry point. Returns a ParsedResume dataclass; caller is
    responsible for persisting `.to_dict()` to Resume.parsed_data.
    """
    text = extract_text_pymupdf(file_path)
    if not text.strip():
        logger.warning(f"PyMuPDF extracted no text from {file_path}; resume may be scanned/image-based")

    doc = _nlp(text[:100_000])  # cap for performance on huge docs

    email_match = EMAIL_RE.search(text)
    phone_match = PHONE_RE.search(text)

    skills_section = _extract_section_text(text, "skills")
    skills = _extract_skills(skills_section) if skills_section else []
    # Also scan full text in case skills aren't under a dedicated header
    if not skills:
        skills = _extract_skills(text)

    education_section = _extract_section_text(text, "education")
    experience_section = _extract_section_text(text, "experience")
    projects_section = _extract_section_text(text, "projects")
    certs_section = _extract_section_text(text, "certificates")
    languages_section = _extract_section_text(text, "languages")

    parsed = ParsedResume(
        name=_extract_name(text, doc),
        email=email_match.group(0) if email_match else None,
        phone=phone_match.group(0) if phone_match else None,
        skills=skills,
        projects=_extract_list_items(projects_section),
        education=[{"raw": e} for e in _extract_list_items(education_section)],
        experience=_extract_list_items(experience_section),
        cgpa=_extract_cgpa(text),
        languages=_extract_languages(languages_section),
        certificates=_extract_list_items(certs_section),
        raw_text=text,
    )
    return parsed
