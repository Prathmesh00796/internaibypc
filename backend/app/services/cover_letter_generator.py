"""
Cover letter generator.

Template-based generation using profile + job data. This avoids an
external LLM dependency for the core flow while still producing a
genuinely personalized letter; swap in an LLM call here if desired
(e.g. call Anthropic's API) — the function signature is the extension point.
"""
from app.models.job import Job
from app.models.profile import Profile


def generate_cover_letter(profile: Profile, job: Job) -> str:
    top_skills = [s.name for s in profile.skills[:5]] if profile.skills else []
    skills_line = ", ".join(top_skills) if top_skills else "a strong foundation in relevant technologies"

    top_project = profile.projects[0] if profile.projects else None
    project_line = (
        f"In particular, my project '{top_project.title}' let me apply these skills to a real problem."
        if top_project
        else "I've applied these skills through coursework and independent projects."
    )

    company_name = job.company.name if job.company else "your team"

    letter = f"""Dear Hiring Team at {company_name},

I am writing to express my interest in the {job.title} position. As a {profile.degree or "student"} \
at {profile.college or "my university"}{f", graduating in {profile.graduation_year}" if profile.graduation_year else ""}, \
I have developed {skills_line}, which I believe align well with what you're looking for in this role.

{project_line}

I'm particularly drawn to this opportunity because it offers hands-on experience in an area I'm \
genuinely excited about, and I'm confident my background would let me contribute meaningfully from day one.

I've attached my resume for your review and would welcome the chance to discuss how I can contribute \
to {company_name}. Thank you for your time and consideration.

Best regards,
{profile.full_name or "Applicant"}
"""
    return letter.strip()
