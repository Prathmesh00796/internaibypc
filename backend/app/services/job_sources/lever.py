"""
Lever Postings API connector.

Lever exposes a public, documented Postings API per company
(https://github.com/lever/postings-api) intended for external consumption.
Like Greenhouse, this is read-only for listings — application submission
still happens on the company's hosted Lever apply page, so results always
go through the manual review queue (allows_auto_submit=False).
"""
import httpx

from app.core.logging_config import logger
from app.models.job import JobSource, JobType
from app.services.job_sources.base import JobSourceConnector, RawListing

LEVER_API_BASE = "https://api.lever.co/v0/postings"


class LeverConnector(JobSourceConnector):
    source = JobSource.LEVER_API
    supports_auto_submit = False

    def __init__(self, company_site_tokens: list[str]):
        self.company_site_tokens = company_site_tokens

    async def fetch_listings(self, query: str | None = None, location: str | None = None) -> list[RawListing]:
        results: list[RawListing] = []
        async with httpx.AsyncClient(timeout=15.0) as client:
            for token in self.company_site_tokens:
                try:
                    resp = await client.get(f"{LEVER_API_BASE}/{token}?mode=json")
                    resp.raise_for_status()
                    postings = resp.json()
                except httpx.HTTPError as exc:
                    logger.warning(f"Lever fetch failed for site '{token}': {exc}")
                    continue

                for posting in postings:
                    title = posting.get("text", "")
                    if query and query.lower() not in title.lower():
                        continue

                    categories = posting.get("categories", {})
                    job_location = categories.get("location")
                    if location and job_location and location.lower() not in job_location.lower():
                        continue

                    is_internship = "intern" in title.lower()
                    description = posting.get("descriptionPlain") or posting.get("description", "")

                    results.append(
                        RawListing(
                            external_id=posting["id"],
                            title=title,
                            company_name=token,
                            description=description,
                            location=job_location,
                            is_remote=bool(job_location and "remote" in job_location.lower()),
                            job_type=JobType.INTERNSHIP if is_internship else JobType.FULL_TIME,
                            stipend_min=None,
                            stipend_max=None,
                            external_url=posting.get("hostedUrl", ""),
                            raw=posting,
                        )
                    )
        return results
