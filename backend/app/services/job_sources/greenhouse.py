"""
Greenhouse Job Board API connector.

Greenhouse publishes a public, unauthenticated Job Board API per company
(https://developers.greenhouse.io/job-board.html) explicitly intended for
third-party consumption — this is exactly the kind of "supported API"
integration the platform is designed around. No auto-submit: Greenhouse's
public job-board API is read-only; posting an application requires the
company's own hosted application form, so these listings always route
through the manual review queue.
"""
import httpx

from app.core.logging_config import logger
from app.models.job import JobSource, JobType
from app.services.job_sources.base import JobSourceConnector, RawListing

GREENHOUSE_API_BASE = "https://boards-api.greenhouse.io/v1/boards"


class GreenhouseConnector(JobSourceConnector):
    source = JobSource.GREENHOUSE_API
    supports_auto_submit = False  # public board API is read-only

    def __init__(self, company_board_tokens: list[str]):
        """
        company_board_tokens: Greenhouse "board token" per company, e.g. for
        boards-api.greenhouse.io/v1/boards/{token}/jobs. Maintain this list
        via the admin panel (Company management) rather than hardcoding.
        """
        self.company_board_tokens = company_board_tokens

    async def fetch_listings(self, query: str | None = None, location: str | None = None) -> list[RawListing]:
        results: list[RawListing] = []
        async with httpx.AsyncClient(timeout=15.0) as client:
            for token in self.company_board_tokens:
                try:
                    resp = await client.get(f"{GREENHOUSE_API_BASE}/{token}/jobs?content=true")
                    resp.raise_for_status()
                    data = resp.json()
                except httpx.HTTPError as exc:
                    logger.warning(f"Greenhouse fetch failed for board '{token}': {exc}")
                    continue

                for job in data.get("jobs", []):
                    title = job.get("title", "")
                    if query and query.lower() not in title.lower():
                        continue

                    job_location = (job.get("location") or {}).get("name")
                    if location and job_location and location.lower() not in job_location.lower():
                        continue

                    is_internship = "intern" in title.lower()
                    results.append(
                        RawListing(
                            external_id=str(job["id"]),
                            title=title,
                            company_name=token,
                            description=job.get("content", ""),
                            location=job_location,
                            is_remote=bool(job_location and "remote" in job_location.lower()),
                            job_type=JobType.INTERNSHIP if is_internship else JobType.FULL_TIME,
                            stipend_min=None,
                            stipend_max=None,
                            external_url=job.get("absolute_url", ""),
                            raw=job,
                        )
                    )
        return results
