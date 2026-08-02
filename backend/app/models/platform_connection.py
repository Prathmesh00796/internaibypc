import enum
import uuid

from sqlalchemy import String, ForeignKey, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDPrimaryKeyMixin, TimestampMixin
from app.models.job import JobSource


class ConnectionStatus(str, enum.Enum):
    CONNECTED = "connected"
    EXPIRED = "expired"
    REVOKED = "revoked"
    ERROR = "error"


class PlatformConnection(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Represents a user's link to an external job platform (via OAuth token
    or API key, never a scraped password). Used to enable searching that
    platform's opportunities and, where the platform's API explicitly
    supports it, submitting applications on the user's behalf.
    """
    __tablename__ = "platform_connections"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    platform: Mapped[JobSource] = mapped_column(Enum(JobSource), nullable=False)
    status: Mapped[ConnectionStatus] = mapped_column(Enum(ConnectionStatus), default=ConnectionStatus.CONNECTED)

    # OAuth tokens are stored encrypted at the application layer.
    access_token_encrypted: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    refresh_token_encrypted: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    external_account_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    supports_auto_submit: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship("User", back_populates="platform_connections")
