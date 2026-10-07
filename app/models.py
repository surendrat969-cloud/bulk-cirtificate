import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

def get_utc_now():
    return datetime.now(timezone.utc)

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    event_name = Column(String(255), nullable=False)
    default_course_name = Column(String(255), nullable=True)
    file_format = Column(String(10), default="png", nullable=False)
    
    status = Column(String(30), default="pending", nullable=False)
    
    total_count = Column(Integer, default=0, nullable=False)
    processed_count = Column(Integer, default=0, nullable=False)
    success_count = Column(Integer, default=0, nullable=False)
    failed_count = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

    certificates = relationship("Certificate", back_populates="job", cascade="all, delete-orphan")

class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    
    recipient_name = Column(String(255), nullable=False)
    recipient_email = Column(String(255), nullable=False)
    course_name = Column(String(255), nullable=False)
    issue_date = Column(String(50), nullable=False)
    
    status = Column(String(30), default="pending", nullable=False)
    file_path = Column(String(512), nullable=True)
    file_format = Column(String(10), default="png", nullable=False)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

    job = relationship("Job", back_populates="certificates")
