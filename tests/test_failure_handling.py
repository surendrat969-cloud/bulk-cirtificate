import pytest
from app.services.job_processor import process_certificate_job
from app.models import JOB_STATUS_PARTIALLY_COMPLETED, CERT_STATUS_COMPLETED, CERT_STATUS_FAILED

def test_individual_certificate_failure_resilience(client, db_session):
    """
    Verifies that a rendering failure for one recipient does NOT prevent other valid
    certificates in the same bulk job from being generated successfully.
    """
    payload = {
        "title": "Robustness Test Event",
        "event_name": "Tech Seminar",
        "organization": "Engineering Org",
        "default_course_name": "Resilient System Design",
        "file_format": "png",
        "recipients": [
            {"recipient_name": "Valid Recipient One", "recipient_email": "one@example.com"},
            {"recipient_name": "TRIGGER_FAIL Recipient Two", "recipient_email": "two@example.com"},
            {"recipient_name": "Valid Recipient Three", "recipient_email": "three@example.com"}
        ]
    }

    create_res = client.post("/api/v1/jobs", json=payload)
    assert create_res.status_code == 202
    job_id = create_res.json()["id"]

    # Execute background worker with db_session
    process_certificate_job(job_id, db=db_session)

    # Fetch detailed job status
    status_res = client.get(f"/api/v1/jobs/{job_id}")
    assert status_res.status_code == 200
    job_data = status_res.json()

    # Overall job status should be PARTIALLY_COMPLETED
    assert job_data["status"] == JOB_STATUS_PARTIALLY_COMPLETED
    assert job_data["total_count"] == 3
    assert job_data["processed_count"] == 3
    assert job_data["success_count"] == 2
    assert job_data["failed_count"] == 1
    assert job_data["progress"] == 100.0

    certificates = job_data["certificates"]
    assert len(certificates) == 3

    # Recipient 1: Valid
    c1 = next(c for c in certificates if c["recipient_email"] == "one@example.com")
    assert c1["status"] == CERT_STATUS_COMPLETED
    assert c1["download_url"] is not None
    assert c1["error_message"] is None

    # Recipient 2: Failed
    c2 = next(c for c in certificates if c["recipient_email"] == "two@example.com")
    assert c2["status"] == CERT_STATUS_FAILED
    assert c2["download_url"] is None
    assert c2["error_message"] is not None
    assert "Rendering failed for recipient" in c2["error_message"]

    # Recipient 3: Valid
    c3 = next(c for c in certificates if c["recipient_email"] == "three@example.com")
    assert c3["status"] == CERT_STATUS_COMPLETED
    assert c3["download_url"] is not None
    assert c3["error_message"] is None

    # Verify valid certificates can be downloaded
    res_c1 = client.get(c1["download_url"])
    assert res_c1.status_code == 200

    res_c3 = client.get(c3["download_url"])
    assert res_c3.status_code == 200

    # Verify downloading failed certificate returns 400 Bad Request
    res_c2_fail = client.get(f"/api/v1/certificates/{c2['id']}")
    assert res_c2_fail.status_code == 400

    # Verify batch ZIP download includes the 2 valid certificates
    zip_res = client.get(f"/api/v1/jobs/{job_id}/download")
    assert zip_res.status_code == 200
    assert len(zip_res.content) > 500
