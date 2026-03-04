import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DocumentType(str, PyEnum):
    GENERAL = "general"
    PROPOSAL = "proposal"
    CONTRACT = "contract"
    CALCULATION = "calculation"
    DRAWING = "drawing"
    MEETING = "meeting"
    SPREADSHEET = "spreadsheet"
    AUDIO = "audio"


class DocumentStatus(str, PyEnum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(500))
    filename: Mapped[str] = mapped_column(String(500))
    mime_type: Mapped[str | None] = mapped_column(String(100))
    file_size: Mapped[int | None] = mapped_column(Integer)
    storage_path: Mapped[str] = mapped_column(String(1000))  # GCS path
    doc_type: Mapped[DocumentType] = mapped_column(Enum(DocumentType), default=DocumentType.GENERAL)
    status: Mapped[DocumentStatus] = mapped_column(Enum(DocumentStatus), default=DocumentStatus.UPLOADED)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    metadata_extra: Mapped[dict | None] = mapped_column(JSONB)
    error_message: Mapped[str | None] = mapped_column(Text)
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
