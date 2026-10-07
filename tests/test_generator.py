import os
import pytest
from pathlib import Path
from app.services.generator import generate_certificate_file

def test_generate_png_certificate(tmp_path):
    cert_id = "test-uuid-png-123"
    recipient_name = "Alice Johnson"
    event_name = "Tech Summit 2026"
    course_name = "Advanced FastAPI Masterclass"
    issue_date = "October 07, 2026"

    file_path = generate_certificate_file(
        certificate_id=cert_id,
        recipient_name=recipient_name,
        event_name=event_name,
        course_name=course_name,
        issue_date=issue_date,
        file_format="png"
    )

    assert os.path.exists(file_path)
    assert file_path.endswith(".png")
    assert os.path.getsize(file_path) > 1000

def test_generate_pdf_certificate(tmp_path):
    cert_id = "test-uuid-pdf-456"
    recipient_name = "Bob Smith"
    event_name = "Python Developer Bootcamp"
    course_name = "Backend Engineering"
    issue_date = "October 07, 2026"

    file_path = generate_certificate_file(
        certificate_id=cert_id,
        recipient_name=recipient_name,
        event_name=event_name,
        course_name=course_name,
        issue_date=issue_date,
        file_format="pdf"
    )

    assert os.path.exists(file_path)
    assert file_path.endswith(".pdf")
    assert os.path.getsize(file_path) > 1000

def test_generator_raises_error_for_empty_name():
    with pytest.raises(ValueError, match="Recipient name cannot be empty"):
        generate_certificate_file(
            certificate_id="invalid-id",
            recipient_name="",
            event_name="Event",
            course_name="Course",
            issue_date="Date"
        )

def test_generator_simulated_failure_trigger():
    with pytest.raises(ValueError, match="Simulated rendering failure"):
        generate_certificate_file(
            certificate_id="trigger-fail-id",
            recipient_name="TRIGGER_FAIL Recipient",
            event_name="Event",
            course_name="Course",
            issue_date="Date"
        )
