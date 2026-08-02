"""
Job source connector interface.

Every integration (official API, RSS/careers-page feed, etc.) implements
this interface. Two hard rules baked into the design:

1. `fetch_listings()` only ever READS public/permitted data. It must not
   perform authenticated scraping of a platform in a way that violates
   that platform's terms of service.

2. `supports_auto_submit` is False by default. It may only be set True
   for a connector backed by an official application-submission API
   (e.g. Greenhouse/Lever job-board APIs that explicitly support posting
   candidate applications) where the user has separately granted consent
   via a PlatformConnection. Everything else routes through the
   human-in-the-loop review queue.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.models.job import JobSource, JobType


@dataclass
class RawListing:
    """Normalized representation of a job/internship listing from any source."""
    external_id: str
    title: str
    company_name: str
    description: str
    location: str | None
    is_remote: bool
    job_type: JobType
    stipend_min: int | None
    stipend_max: int | None
    skills_required: list[str] = field(default_factory=list)
    min_cgpa: float | None = None
    eligible_grad_years: list[int] = field(default_factory=list)
    freshers_only: bool = False
    external_url: str = ""
    raw: dict = field(default_factory=dict)


class JobSourceConnector(ABC):
    source: JobSource
    supports_auto_submit: bool = False

    @abstractmethod
    async def fetch_listings(self, query: str | None = None, location: str | None = None) -> list[RawListing]:
        """Fetch current listings matching an optional query/location filter."""
        raise NotImplementedError

    async def submit_application(self, *args, **kwargs) -> dict:
        """
        Submit an application on the user's behalf. Only implemented by
        connectors where `supports_auto_submit` is True and only ever
        called after explicit user confirmation for that specific
        application (see app.services.application_service).
        """
        raise NotImplementedError(
            f"{self.source} does not support automated submission; "
            "route this application through the manual review queue."
        )
