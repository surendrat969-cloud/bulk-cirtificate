from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict, AliasChoices

class RecipientCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    recipient_name: str = Field(
        ...,
        validation_alias=AliasChoices("recipient_name", "name"),
        min_length=1,
        max_length=255,
        description="Full name of the recipient"
    )
    recipient_email: EmailStr = Field(
        ...,
        validation_alias=AliasChoices("recipient_email", "email"),
        description="Valid email address of recipient"
    )
    course_name: Optional[str] = Field(
        None,
        max_length=255,
        description="Optional course or award title override"
    )
    issue_date: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("issue_date", "date"),
        max_length=50,
        description="Optional issue date override (e.g. YYYY-MM-DD)"
    )

    @field_validator('recipient_name')
    def validate_name_not_blank(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError('Recipient name cannot be empty or whitespace')
        return cleaned


class JobCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str = Field(
        ...,
        validation_alias=AliasChoices("title", "certificate_title"),
        min_length=1,
        max_length=255,
        description="Certificate title or job name"
    )
    event_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Event name"
    )
    organization: Optional[str] = Field(
        None,
        max_length=255,
        description="Organization or issuer name"
    )
    default_course_name: Optional[str] = Field(
        None,
        max_length=255,
        description="Default course name if recipient does not specify one"
    )
    issue_date: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("issue_date", "date"),
        max_length=50,
        description="Issue date (e.g. YYYY-MM-DD)"
    )
    file_format: Literal["png", "pdf"] = Field(
        "png",
        description="Output format: png or pdf"
    )
    recipients: List[RecipientCreate] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="List of recipients (1 to 1000)"
    )

    @field_validator('title', 'event_name')
    def validate_non_empty_strings(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError('Field cannot be empty or whitespace')
        return cleaned

    @field_validator('recipients')
    def validate_recipients_list(cls, v: List[RecipientCreate]) -> List[RecipientCreate]:
        if not v:
            raise ValueError('At least one recipient must be provided')
        if len(v) > 1000:
            raise ValueError('Maximum recipient limit per job is 1000')
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
    organization: Optional[str] = None
    file_format: str
    status: str
    total_count: int
    processed_count: int
    success_count: int
    failed_count: int
    progress: float = Field(..., description="Progress percentage from 0.0 to 100.0")
    created_at: datetime
    updated_at: datetime


class JobDetailResponse(JobResponse):
    certificates: List[CertificateResponse] = []
