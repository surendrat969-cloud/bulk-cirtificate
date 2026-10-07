import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Job, Certificate
from app.schemas import JobCreate, JobResponse, JobDetailResponse, CertificateResponse
from app.services.job_processor import process_certificate_job
from app.config import settings

router = APIRouter(prefix="/api/v1/jobs", tags=["Jobs"])

def build_cert_response(cert: Certificate) -> CertificateResponse:
    download_url = f"/api/v1/certificates/{cert.id}" if cert.status == "completed" else None
    return CertificateResponse(
        id=cert.id,
        job_id=cert.job_id,
        recipient_name=cert.recipient_name,
        recipient_email=cert.recipient_email,
        course_name=cert.course_name,
        issue_date=cert.issue_date,
        status=cert.status,
        file_format=cert.file_format,
        download_url=download_url,
        error_message=cert.error_message,
        created_at=cert.created_at,
        updated_at=cert.updated_at
    )

@router.post("", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
def create_certificate_job(
    payload: JobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Submit a bulk certificate generation job with a list of recipients.
    Processes certificate generation asynchronously in the background.
    """
    default_date = payload.issue_date or datetime.now(timezone.utc).strftime("%B %d, %Y")

    new_job = Job(
        title=payload.title,
        event_name=payload.event_name,
        default_course_name=payload.default_course_name,
        file_format=payload.file_format,
        status="pending",
        total_count=len(payload.recipients),
        processed_count=0,
        success_count=0,
        failed_count=0
    )
    db.add(new_job)
    db.flush()

    for item in payload.recipients:
        course = item.course_name or payload.default_course_name or "Certificate of Completion"
        date_str = item.issue_date or default_date
        cert = Certificate(
            job_id=new_job.id,
            recipient_name=item.recipient_name,
            recipient_email=item.recipient_email,
            course_name=course,
            issue_date=date_str,
            status="pending",
            file_format=payload.file_format
        )
        db.add(cert)

    db.commit()
    db.refresh(new_job)

    # Queue background task for processing certificates
    background_tasks.add_task(process_certificate_job, new_job.id)

    return new_job

@router.get("", response_model=List[JobResponse])
def list_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Retrieve a list of all certificate generation jobs.
    """
    jobs = db.query(Job).order_by(Job.created_at.desc()).offset(skip).limit(limit).all()
    return jobs

@router.get("/{job_id}", response_model=JobDetailResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """
    Get detailed job status, progress metrics, and individual certificate results.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    certificates = db.query(Certificate).filter(Certificate.job_id == job_id).all()
    cert_responses = [build_cert_response(c) for c in certificates]

    return JobDetailResponse(
        id=job.id,
        title=job.title,
        event_name=job.event_name,
        file_format=job.file_format,
        status=job.status,
        total_count=job.total_count,
        processed_count=job.processed_count,
        success_count=job.success_count,
        failed_count=job.failed_count,
        created_at=job.created_at,
        updated_at=job.updated_at,
        certificates=cert_responses
    )

@router.get("/{job_id}/download")
def download_job_certificates_zip(job_id: str, db: Session = Depends(get_db)):
    """
    Download a ZIP archive containing all successfully generated certificates for a job.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    completed_certs = db.query(Certificate).filter(
        Certificate.job_id == job_id,
        Certificate.status == "completed"
    ).all()

    if not completed_certs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No completed certificates available for download in this job"
        )

    zip_filename = f"job_{job_id[:8]}_certificates.zip"
    zip_path = settings.ZIPS_DIR / zip_filename

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for cert in completed_certs:
            if cert.file_path and Path(cert.file_path).exists():
                file_ext = cert.file_format.lower()
                clean_name = "".join(c for c in cert.recipient_name if c.isalnum() or c in (' ', '_', '-')).strip()
                arcname = f"{clean_name}_{cert.id[:8]}.{file_ext}"
                zipf.write(cert.file_path, arcname=arcname)

    return FileResponse(
        path=zip_path,
        media_type="application/zip",
        filename=zip_filename
    )
