import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Job, Certificate
from app.services.generator import generate_certificate_file

logger = logging.getLogger(__name__)

def process_certificate_job(job_id: str, db: Session = None):
    """
    Background worker task to process bulk certificate generation for a job.
    Isolates per-recipient failures to ensure maximum completion rate.
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

        job.status = "processing"
        job.updated_at = datetime.now(timezone.utc)
        db.commit()

        certificates = db.query(Certificate).filter(Certificate.job_id == job_id).all()

        for cert in certificates:
            try:
                cert.status = "generating"
                db.commit()

                # Generate file
                file_path = generate_certificate_file(
                    certificate_id=cert.id,
                    recipient_name=cert.recipient_name,
                    event_name=job.event_name,
                    course_name=cert.course_name,
                    issue_date=cert.issue_date,
                    file_format=cert.file_format
                )

                cert.status = "completed"
                cert.file_path = file_path
                cert.error_message = None
                job.success_count += 1

            except Exception as e:
                logger.exception(f"Failed to generate certificate for {cert.recipient_name} ({cert.id}): {e}")
                cert.status = "failed"
                cert.error_message = str(e)
                job.failed_count += 1

            finally:
                job.processed_count += 1
                cert.updated_at = datetime.now(timezone.utc)
                job.updated_at = datetime.now(timezone.utc)
                db.commit()

        # Update final job status
        if job.success_count == job.total_count:
            job.status = "completed"
        elif job.success_count > 0 and job.failed_count > 0:
            job.status = "partially_completed"
        else:
            job.status = "failed"

        job.updated_at = datetime.now(timezone.utc)
        db.commit()
        logger.info(f"Job {job_id} processing completed. Status: {job.status}")

    except Exception as exc:
        logger.exception(f"Fatal error occurred while processing job {job_id}: {exc}")
        if 'job' in locals() and job:
            job.status = "failed"
            db.commit()
    finally:
        if should_close_session:
            db.close()
