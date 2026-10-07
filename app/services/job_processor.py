import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import (
    Job, Certificate,
    JOB_STATUS_PROCESSING, JOB_STATUS_COMPLETED,
    JOB_STATUS_PARTIALLY_COMPLETED, JOB_STATUS_FAILED,
    CERT_STATUS_GENERATING, CERT_STATUS_COMPLETED, CERT_STATUS_FAILED
)
from app.services.generator import generate_certificate_file

logger = logging.getLogger(__name__)

def process_certificate_job(job_id: str, db: Session = None):
    """
    Background worker task to process bulk certificate generation for a job.
    Isolates per-recipient rendering errors to guarantee partial completion resilience.
    """
    should_close_session = False
    if db is None:
        db = SessionLocal()
        should_close_session = True

    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found for background processing")
            return

        job.status = JOB_STATUS_PROCESSING
        job.updated_at = datetime.now(timezone.utc)
        db.commit()

        certificates = db.query(Certificate).filter(Certificate.job_id == job_id).all()

        for cert in certificates:
            try:
                cert.status = CERT_STATUS_GENERATING
                db.commit()

                # Generate certificate file
                file_path = generate_certificate_file(
                    certificate_id=cert.id,
                    recipient_name=cert.recipient_name,
                    event_name=job.event_name,
                    course_name=cert.course_name,
                    issue_date=cert.issue_date,
                    organization=job.organization,
                    file_format=cert.file_format
                )

                cert.status = CERT_STATUS_COMPLETED
                cert.file_path = file_path
                cert.error_message = None
                job.success_count += 1

            except Exception as e:
                logger.warning(f"Certificate generation failed for '{cert.recipient_name}' (ID: {cert.id}): {e}")
                cert.status = CERT_STATUS_FAILED
                # Store a clean user-safe error message
                cert.error_message = str(e)
                job.failed_count += 1

            finally:
                job.processed_count += 1
                cert.updated_at = datetime.now(timezone.utc)
                job.updated_at = datetime.now(timezone.utc)
                db.commit()

        # Update final job status
        if job.success_count == job.total_count:
            job.status = JOB_STATUS_COMPLETED
        elif job.success_count > 0 and job.failed_count > 0:
            job.status = JOB_STATUS_PARTIALLY_COMPLETED
        else:
            job.status = JOB_STATUS_FAILED

        job.updated_at = datetime.now(timezone.utc)
        db.commit()
        logger.info(f"Job {job_id} background processing finished. Status: {job.status}")

    except Exception as exc:
        logger.exception(f"Fatal unhandled error while processing job {job_id}: {exc}")
        if 'job' in locals() and job:
            job.status = JOB_STATUS_FAILED
            db.commit()
    finally:
        if should_close_session:
            db.close()
