import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Connector(Base):
    __tablename__ = "connectors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type: Mapped[str] = mapped_column(String(20))  # 'sharepoint', 'google_drive'
    name: Mapped[str] = mapped_column(String(200))
    config: Mapped[dict] = mapped_column(JSONB)  # site_id, folder paths, etc.
    oauth_tokens: Mapped[dict | None] = mapped_column(JSONB)
    delta_token: Mapped[str | None] = mapped_column(Text)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sync_interval_minutes: Mapped[int] = mapped_column(Integer, default=60)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SyncedFile(Base):
    __tablename__ = "synced_files"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    connector_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("connectors.id"))
    remote_id: Mapped[str] = mapped_column(String(500))
    remote_path: Mapped[str | None] = mapped_column(Text)
    document_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"))
    remote_modified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    etag: Mapped[str | None] = mapped_column(String(200))
