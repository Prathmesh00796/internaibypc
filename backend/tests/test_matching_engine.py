"""
Unit tests for the matching engine's pure scoring functions.
These don't require a database and run fast.
"""
from app.services.matching_engine import (
    score_skill_match, score_experience, score_cgpa,
    score_graduation_year, score_location, score_resume_similarity,
)


class TestSkillMatch:
    def test_perfect_overlap(self):
        assert score_skill_match(["python", "react", "sql"], ["python", "react", "sql"]) == 100.0

    def test_no_overlap(self):
        assert score_skill_match(["java"], ["python", "react"]) == 0.0

    def test_partial_overlap(self):
        score = score_skill_match(["python", "java"], ["python", "react", "sql", "aws"])
        assert score == 25.0  # 1/4 matched

    def test_no_job_requirements_returns_neutral(self):
        assert score_skill_match(["python"], None) == 70.0
        assert score_skill_match(["python"], []) == 70.0

    def test_case_insensitive(self):
        assert score_skill_match(["Python", "REACT"], ["python", "react"]) == 100.0


class TestExperience:
    def test_internship_no_experience_still_gets_baseline(self):
        assert score_experience(0, is_internship=True) == 60.0

    def test_internship_with_experience_scores_higher(self):
        assert score_experience(2, is_internship=True) > score_experience(0, is_internship=True)

    def test_full_time_no_experience_scores_zero(self):
        assert score_experience(0, is_internship=False) == 0.0

    def test_caps_at_100(self):
        assert score_experience(10, is_internship=True) == 100.0


class TestCGPA:
    def test_no_minimum_required(self):
        assert score_cgpa(7.5, None) == 100.0

    def test_meets_minimum(self):
        assert score_cgpa(8.0, 7.0) == 100.0

    def test_unknown_cgpa_neutral(self):
        assert score_cgpa(None, 7.0) == 50.0

    def test_below_minimum_partial_credit(self):
        score = score_cgpa(6.5, 7.0)
        assert 0 < score < 100


class TestGraduationYear:
    def test_no_restriction(self):
        assert score_graduation_year(2027, None) == 100.0

    def test_eligible_year(self):
        assert score_graduation_year(2027, [2026, 2027]) == 100.0

    def test_ineligible_year(self):
        assert score_graduation_year(2025, [2026, 2027]) == 20.0

    def test_unknown_year(self):
        assert score_graduation_year(None, [2027]) == 50.0


class TestLocation:
    def test_remote_job_always_matches(self):
        assert score_location(True, False, "Bangalore", ["Mumbai"]) == 100.0

    def test_wfh_only_preference_penalizes_onsite(self):
        assert score_location(False, True, "Bangalore", None) == 10.0

    def test_matching_preferred_location(self):
        assert score_location(False, False, "Bangalore, India", ["Bangalore"]) == 100.0

    def test_no_preference_neutral(self):
        assert score_location(False, False, "Bangalore", None) == 60.0


class TestResumeSimilarity:
    def test_identical_text_high_similarity(self):
        text = "python django react postgresql aws docker kubernetes"
        score = score_resume_similarity(text, text)
        assert score > 90.0

    def test_missing_text_neutral(self):
        assert score_resume_similarity(None, "some job description") == 50.0
        assert score_resume_similarity("resume text", None) == 50.0

    def test_unrelated_text_low_similarity(self):
        resume = "python django backend development"
        job = "photography camera lens portrait studio lighting"
        score = score_resume_similarity(resume, job)
        assert score < 30.0
