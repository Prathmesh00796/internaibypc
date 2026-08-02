"""
ATS-friendly resume generator.

Produces clean, single-column PDFs using reportlab — deliberately avoiding
tables/columns/graphics that trip up ATS parsers. Offers a couple of
lightweight visual variants (template="classic" | "modern") that differ
only in color accents/spacing, not layout complexity, to preserve
ATS-parseability across templates.
"""
from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable

from app.models.profile import Profile

TEMPLATE_ACCENTS = {
    "classic": colors.HexColor("#1a1a1a"),
    "modern": colors.HexColor("#4f46e5"),
}


def _build_styles(accent_color):
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="NameHeader", fontSize=20, leading=24, textColor=accent_color,
        fontName="Helvetica-Bold", spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        name="ContactLine", fontSize=9.5, leading=12, textColor=colors.HexColor("#444444"),
        spaceAfter=10,
    ))
    styles.add(ParagraphStyle(
        name="SectionHeader", fontSize=12, leading=16, textColor=accent_color,
        fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="ResumeBody", fontSize=10, leading=14, textColor=colors.HexColor("#222222"),
    ))
    styles.add(ParagraphStyle(
        name="ItemTitle", fontSize=10.5, leading=14, fontName="Helvetica-Bold",
    ))
    return styles


def generate_resume_pdf(profile: Profile, template: str = "classic") -> bytes:
    accent = TEMPLATE_ACCENTS.get(template, TEMPLATE_ACCENTS["classic"])
    styles = _build_styles(accent)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        topMargin=0.6 * inch, bottomMargin=0.6 * inch,
        leftMargin=0.7 * inch, rightMargin=0.7 * inch,
    )
    story = []

    # --- Header ---
    story.append(Paragraph(profile.full_name or "Your Name", styles["NameHeader"]))
    contact_bits = []
    if profile.location:
        contact_bits.append(profile.location)
    if profile.linkedin_url:
        contact_bits.append(profile.linkedin_url)
    if profile.github_url:
        contact_bits.append(profile.github_url)
    if profile.portfolio_url:
        contact_bits.append(profile.portfolio_url)
    story.append(Paragraph(" | ".join(contact_bits), styles["ContactLine"]))
    story.append(HRFlowable(width="100%", color=accent, thickness=1))

    # --- Education ---
    if profile.college or profile.degree:
        story.append(Paragraph("EDUCATION", styles["SectionHeader"]))
        edu_line = f"{profile.degree or ''} — {profile.college or ''}"
        details = []
        if profile.graduation_year:
            details.append(f"Class of {profile.graduation_year}")
        if profile.cgpa:
            details.append(f"CGPA: {profile.cgpa}")
        story.append(Paragraph(edu_line, styles["ItemTitle"]))
        if details:
            story.append(Paragraph(" | ".join(details), styles["ResumeBody"]))

    # --- Skills ---
    if profile.skills:
        story.append(Paragraph("SKILLS", styles["SectionHeader"]))
        skills_text = ", ".join(s.name for s in profile.skills)
        story.append(Paragraph(skills_text, styles["ResumeBody"]))

    # --- Experience ---
    if profile.experiences:
        story.append(Paragraph("EXPERIENCE", styles["SectionHeader"]))
        for exp in profile.experiences:
            date_range = ""
            if exp.start_date:
                end = "Present" if exp.is_current else (exp.end_date.strftime("%b %Y") if exp.end_date else "")
                date_range = f"{exp.start_date.strftime('%b %Y')} – {end}"
            title_line = f"{exp.role or ''} — {exp.company_name}"
            story.append(Paragraph(title_line, styles["ItemTitle"]))
            if date_range:
                story.append(Paragraph(date_range, styles["ResumeBody"]))
            if exp.description:
                story.append(Paragraph(exp.description, styles["ResumeBody"]))
            story.append(Spacer(1, 6))

    # --- Projects ---
    if profile.projects:
        story.append(Paragraph("PROJECTS", styles["SectionHeader"]))
        for proj in profile.projects:
            story.append(Paragraph(proj.title, styles["ItemTitle"]))
            if proj.tech_stack:
                story.append(Paragraph(", ".join(proj.tech_stack), styles["ResumeBody"]))
            if proj.description:
                story.append(Paragraph(proj.description, styles["ResumeBody"]))
            story.append(Spacer(1, 6))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
