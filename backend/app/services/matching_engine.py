"""
Job matching engine.

Scores a (profile, resume, job) triple on a 0-100 scale using a weighted
blend of:
  - skill_match:        overlap between profile/resume skills and job's required skills
  - experience:         presence/relevance of experience entries (internship-readiness proxy)
  - cgpa:                whether the user's CGPA clears the job's min_cgpa bar
  - graduation_year:     whether the user's grad year is in the job's eligible set
  - location:            remote match or same-city/region match
  - resume_similarity:   TF-IDF cosine similarity between resume text and job description

Weights are configurable via Settings (WEIGHT_*) so they can be tuned
without a code change.
"""
from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.core.config import settings
from app.models.job import Job
from app.models.profile import Profile


@dataclass
class MatchResult:
    total_score: float  # 0-100
    breakdown: dict[str, float]  # each sub-score 0-100, for transparency in the UI


def _normalize_skill(s: str) -> str:
    return s.strip().lower()


def score_skill_match(profile_skills: list[str], job_skills: list[str] | None) -> float:
    if not job_skills:
        return 70.0  # neutral-positive score when job doesn't specify required skills
    job_set = {_normalize_skill(s) for s in job_skills}
    profile_set = {_normalize_skill(s) for s in profile_skills}
    if not job_set:
        return 70.0
    overlap = job_set & profile_set
    return round(100 * len(overlap) / len(job_set), 2)


def score_experience(experience_count: int, is_internship: bool) -> float:
    if is_internship:
        # For internships, some relevant experience helps but isn't required.
        if experience_count == 0:
            return 60.0
        return min(100.0, 60.0 + experience_count * 15.0)
    # For full-time roles, weight experience more heavily.
    return min(100.0, experience_count * 25.0)


def score_cgpa(user_cgpa: float | None, min_cgpa: float | None) -> float:
    if min_cgpa is None:
        return 100.0
    if user_cgpa is None:
        return 50.0  # unknown — don't penalize heavily, but flag uncertainty
    if user_cgpa >= min_cgpa:
        return 100.0
    # Partial credit that decays as the gap widens
    gap = min_cgpa - user_cgpa
    return max(0.0, 100.0 - gap * 40.0)


def score_graduation_year(user_year: int | None, eligible_years: list[int] | None) -> float:
    if not eligible_years:
        return 100.0
    if user_year is None:
        return 50.0
    return 100.0 if user_year in eligible_years else 20.0


def score_location(
    is_remote_job: bool,
    wfh_only_preference: bool,
    job_location: str | None,
    preferred_locations: list[str] | None,
) -> float:
    if is_remote_job:
        return 100.0
    if wfh_only_preference:
        return 10.0  # user wants remote only but this job isn't remote
    if not preferred_locations or not job_location:
        return 60.0  # neutral when we lack info
    job_location_lower = job_location.lower()
    if any(loc.lower() in job_location_lower or job_location_lower in loc.lower() for loc in preferred_locations):
        return 100.0
    return 30.0


def score_resume_similarity(resume_text: str | None, job_description: str | None) -> float:
    if not resume_text or not job_description:
        return 50.0
    try:
        vectorizer = TfidfVectorizer(stop_words="english", max_features=2000)
        tfidf = vectorizer.fit_transform([resume_text, job_description])
        similarity = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
        return round(float(similarity) * 100, 2)
    except ValueError:
        # Can happen if text is empty after stopword removal
        return 50.0


def compute_match(
    profile: Profile,
    resume_text: str | None,
    resume_skills: list[str],
    job: Job,
) -> MatchResult:
    all_profile_skills = list({*(s.name for s in profile.skills), *resume_skills})

    skill_score = score_skill_match(all_profile_skills, job.skills_required)
    experience_score = score_experience(len(profile.experiences), job.job_type.value == "internship")
    cgpa_score = score_cgpa(profile.cgpa, job.min_cgpa)
    grad_year_score = score_graduation_year(profile.graduation_year, job.eligible_grad_years)
    location_score = score_location(
        job.is_remote, profile.work_from_home_only, job.location, profile.preferred_locations
    )
    similarity_score = score_resume_similarity(resume_text, job.description)

    breakdown = {
        "skill_match": skill_score,
        "experience": experience_score,
        "cgpa": cgpa_score,
        "graduation_year": grad_year_score,
        "location": location_score,
        "resume_similarity": similarity_score,
    }

    total = (
        skill_score * settings.WEIGHT_SKILL_MATCH
        + experience_score * settings.WEIGHT_EXPERIENCE
        + cgpa_score * settings.WEIGHT_CGPA
        + grad_year_score * settings.WEIGHT_GRAD_YEAR
        + location_score * settings.WEIGHT_LOCATION
        + similarity_score * settings.WEIGHT_RESUME_SIMILARITY
    )

    return MatchResult(total_score=round(total, 2), breakdown=breakdown)
