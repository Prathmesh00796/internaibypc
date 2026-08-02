"""
Unit tests for resume parser text-extraction helpers (regex/section logic
that doesn't require an actual PDF file or spaCy model).
"""
from app.services.resume_parser import (
    EMAIL_RE, PHONE_RE, CGPA_RE, _extract_skills, _extract_section_text,
)


class TestRegexExtraction:
    def test_email_extraction(self):
        text = "Contact me at jane.doe@example.com for more info"
        match = EMAIL_RE.search(text)
        assert match.group(0) == "jane.doe@example.com"

    def test_phone_extraction(self):
        text = "Phone: +91 98765 43210"
        match = PHONE_RE.search(text)
        assert match is not None

    def test_cgpa_extraction_with_scale(self):
        text = "Academic record: CGPA: 8.5/10"
        match = CGPA_RE.search(text)
        assert match.group(1) == "8.5"
        assert match.group(2) == "10"

    def test_cgpa_extraction_without_scale(self):
        text = "GPA - 3.7"
        match = CGPA_RE.search(text)
        assert match.group(1) == "3.7"


class TestSkillExtraction:
    def test_finds_known_skills(self):
        text = "Proficient in Python, React, and PostgreSQL. Familiar with Docker."
        skills = _extract_skills(text)
        assert "python" in skills
        assert "react" in skills
        assert "postgresql" in skills
        assert "docker" in skills

    def test_avoids_false_positive_substring(self):
        # "c" should not match inside "docker" or "react"
        text = "Experience with Docker and React"
        skills = _extract_skills(text)
        assert "c" not in skills

    def test_no_skills_found(self):
        text = "This resume has no recognizable technical skills listed."
        skills = _extract_skills(text)
        assert skills == []


class TestSectionExtraction:
    def test_extracts_section_between_headers(self):
        text = "Skills\nPython\nReact\nSQL\nEducation\nB.Tech Computer Science"
        section = _extract_section_text(text, "skills")
        assert "Python" in section
        assert "Education" not in section

    def test_missing_section_returns_empty(self):
        text = "Just some random resume text with no headers"
        section = _extract_section_text(text, "skills")
        assert section == ""
