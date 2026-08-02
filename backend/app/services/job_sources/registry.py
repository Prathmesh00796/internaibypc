"""
Registry of active job source connectors.

Add/remove connectors here as new integrations are approved. Each
connector explicitly declares whether it supports automated submission;
per platform ToS, most do not, and their jobs will always be prepared
for manual user confirmation (see app.services.application_service).

NOTE on platforms like Internshala/LinkedIn/Indeed/Naukri: these do not
provide public application-submission APIs for third parties, and their
terms of service generally prohibit automated scraping or auto-applying
via bots. This registry intentionally does NOT include a scraper for
them. If/when a user connects their own account via an official OAuth
integration a platform offers, add a connector here gated behind that
user's PlatformConnection — never a shared credential scraper.
"""
from app.services.job_sources.base import JobSourceConnector
from app.services.job_sources.greenhouse import GreenhouseConnector
from app.services.job_sources.lever import LeverConnector

# Company board tokens should be managed via the admin panel / DB in a
# real deployment. Seed list here for demonstration/testing purposes.
DEFAULT_GREENHOUSE_BOARDS = ["stripe", "airbnb", "figma"]
DEFAULT_LEVER_BOARDS = ["netflix", "shopify"]


def get_active_connectors() -> list[JobSourceConnector]:
    return [
        GreenhouseConnector(company_board_tokens=DEFAULT_GREENHOUSE_BOARDS),
        LeverConnector(company_site_tokens=DEFAULT_LEVER_BOARDS),
    ]
