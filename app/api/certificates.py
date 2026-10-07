from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Certificate
from app.schemas import CertificateResponse

router = APIRouter(prefix="/api/v1/certificates", tags=["Certificates"])

@router.get("/{certificate_id}")
def download_certificate(certificate_id: str, db: Session = Depends(get_db)):
    """
    Retrieve/download the generated certificate file (PNG or PDF).
    """
    cert = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not cert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found")

    if cert.status != "completed" or not cert.file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Certificate generation status is '{cert.status}'. File is not available."
        )

    file_path = Path(cert.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate file does not exist on disk"
        )

    media_type = "application/pdf" if cert.file_format.lower() == "pdf" else "image/png"
    filename = f"certificate_{cert.recipient_name.replace(' ', '_')}.{cert.file_format.lower()}"

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename
    )

@router.get("/{certificate_id}/metadata", response_model=CertificateResponse)
def get_certificate_metadata(certificate_id: str, db: Session = Depends(get_db)):
    """
    Retrieve certificate JSON metadata.
    """
    cert = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not cert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found")

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
