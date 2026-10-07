import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

def generate_uuid() -> str:
    """Generate a random UUID4 string."""
    return str(uuid.uuid4())

def get_utc_now() -> datetime:
    """Get timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)

# Status Constants
JOB_STATUS_PENDING = "PENDING"
JOB_STATUS_PROCESSING = "PROCESSING"
JOB_STATUS_COMPLETED = "COMPLETED"
JOB_STATUS_PARTIALLY_COMPLETED = "PARTIALLY_COMPLETED"
JOB_STATUS_FAILED = "FAILED"

CERT_STATUS_PENDING = "PENDING"
CERT_STATUS_GENERATING = "GENERATING"
CERT_STATUS_COMPLETED = "COMPLETED"
CERT_STATUS_FAILED = "FAILED"


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    event_name = Column(String(255), nullable=False)
    organization = Column(String(255), nullable=True)
    default_course_name = Column(String(255), nullable=True)
    file_format = Column(String(10), default="png", nullable=False)

    status = Column(String(30), default=JOB_STATUS_PENDING, nullable=False)

    total_count = Column(Integer, default=0, nullable=False)
    processed_count = Column(Integer, default=0, nullable=False)
    success_count = Column(Integer, default=0, nullable=False)
    failed_count = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

    certificates = relationship("Certificate", back_populates="job", cascade="all, delete-orphan")

    @property
    def progress(self) -> float:
        """Calculate live job completion percentage (0.0 to 100.0)."""
        if self.total_count == 0:
            return 0.0
        return round((self.processed_count / self.total_count) * 100, 2)


class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)

    recipient_name = Column(String(255), nullable=False)
    recipient_email = Column(String(255), nullable=False)
    course_name = Column(String(255), nullable=False)
    issue_date = Column(String(50), nullable=False)

    status = Column(String(30), default=CERT_STATUS_PENDING, nullable=False)
    file_path = Column(String(512), nullable=True)
    file_format = Column(String(10), default="png", nullable=False)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

    job = relationship("Job", back_populates="certificates")
