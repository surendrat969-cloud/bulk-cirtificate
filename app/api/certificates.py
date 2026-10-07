from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Certificate, CERT_STATUS_COMPLETED
from app.schemas import CertificateResponse
from app.services.generator import sanitize_filename

router = APIRouter(prefix="/api/v1/certificates", tags=["Certificates"])


def build_cert_response(cert: Certificate) -> CertificateResponse:
    """Build CertificateResponse schema instance."""
    download_url = f"/api/v1/certificates/{cert.id}" if cert.status == CERT_STATUS_COMPLETED else None
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


@router.get("/{certificate_id}")
def download_certificate(certificate_id: str, db: Session = Depends(get_db)):
    """
    Retrieve/download the generated certificate file (PNG image or PDF document).
    """
    cert = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not cert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found")

    if cert.status != CERT_STATUS_COMPLETED or not cert.file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Certificate generation status is '{cert.status}'. File is not available for retrieval."
        )

    file_path = Path(cert.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate file does not exist on storage disk"
        )

    media_type = "application/pdf" if cert.file_format.lower() == "pdf" else "image/png"
    safe_name = sanitize_filename(cert.recipient_name)
    filename = f"certificate_{safe_name}.{cert.file_format.lower()}"

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename
    )


@router.get("/{certificate_id}/metadata", response_model=CertificateResponse)
def get_certificate_metadata(certificate_id: str, db: Session = Depends(get_db)):
    """
    Retrieve JSON metadata for a specific certificate.
    """
    cert = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not cert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found")

    return build_cert_response(cert)
