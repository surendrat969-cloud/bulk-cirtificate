from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict

class RecipientCreate(BaseModel):
    recipient_name: str = Field(..., min_length=1, max_length=255, description="Full name of recipient")
    recipient_email: EmailStr = Field(..., description="Valid recipient email address")
    course_name: Optional[str] = Field(None, max_length=255, description="Course or award title override")
    issue_date: Optional[str] = Field(None, max_length=50, description="Issue date override (e.g. YYYY-MM-DD)")

    @field_validator('recipient_name')
    def name_must_not_be_blank(cls, v):
        if not v.strip():
            raise ValueError('Recipient name cannot be empty or whitespace')
        return v.strip()

class JobCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Job / Event title")
    event_name: str = Field(..., min_length=1, max_length=255, description="Event or Organization name")
    default_course_name: Optional[str] = Field("Certificate of Completion", max_length=255)
    issue_date: Optional[str] = Field(None, max_length=50, description="Default issue date (e.g. Oct 07, 2026)")
    file_format: Literal["png", "pdf"] = Field("png", description="Output format: png or pdf")
    recipients: List[RecipientCreate] = Field(..., min_length=1, description="List of recipient objects")

    @field_validator('recipients')
    def validate_recipients_non_empty(cls, v):
        if not v:
            raise ValueError('At least one recipient must be provided')
        return v

class CertificateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    recipient_name: str
    recipient_email: str
    course_name: str
    issue_date: str
    status: str
    file_format: str
    download_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    event_name: str
    file_format: str
    status: str
    total_count: int
    processed_count: int
    success_count: int
    failed_count: int
    created_at: datetime
    updated_at: datetime

class JobDetailResponse(JobResponse):
    certificates: List[CertificateResponse] = []
