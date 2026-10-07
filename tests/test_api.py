import pytest
from app.services.job_processor import process_certificate_job
from app.models import JOB_STATUS_PENDING, JOB_STATUS_COMPLETED

def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_create_job_success(client):
    """Test successful job submission with standard payload."""
    payload = {
        "title": "Annual Developer Conference",
        "event_name": "DevCon 2026",
        "organization": "Tech Foundation",
        "default_course_name": "Microservices Architecture",
        "file_format": "png",
        "recipients": [
            {"recipient_name": "John Doe", "recipient_email": "john@example.com"},
            {"recipient_name": "Jane Smith", "recipient_email": "jane@example.com"}
        ]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["event_name"] == payload["event_name"]
    assert data["organization"] == payload["organization"]
    assert data["total_count"] == 2
    assert data["processed_count"] == 0
    assert data["status"] == JOB_STATUS_PENDING
    assert data["progress"] == 0.0
    assert "id" in data

def test_create_job_flexible_aereo_payload(client):
    """Test job submission using Aereo prompt field names (certificate_title, date, name, email)."""
    payload = {
        "event_name": "Python Workshop",
        "organization": "Aereo",
        "certificate_title": "Certificate of Participation",
        "date": "2026-10-01",
        "recipients": [
            {"name": "Surendra", "email": "surendra@example.com"},
            {"name": "Rahul", "email": "rahul@example.com"}
        ]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert data["title"] == "Certificate of Participation"
    assert data["event_name"] == "Python Workshop"
    assert data["organization"] == "Aereo"
    assert data["total_count"] == 2
    assert data["status"] == JOB_STATUS_PENDING

def test_input_validation_empty_recipients(client):
    """Test validation failure for empty recipient array."""
    payload = {
        "title": "Invalid Job",
        "event_name": "Event",
        "recipients": []
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422

def test_input_validation_invalid_email(client):
    """Test validation failure for malformed recipient email."""
    payload = {
        "title": "Bad Email Job",
        "event_name": "Event",
        "recipients": [
            {"recipient_name": "Invalid Email", "recipient_email": "not-an-email"}
        ]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422

def test_input_validation_blank_name(client):
    """Test validation failure for whitespace-only recipient name."""
    payload = {
        "title": "Blank Name Job",
        "event_name": "Event",
        "recipients": [
            {"recipient_name": "   ", "recipient_email": "valid@example.com"}
        ]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422

def test_input_validation_too_many_recipients(client):
    """Test validation failure when recipient count exceeds 1000."""
    recipients = [{"recipient_name": f"User {i}", "recipient_email": f"user{i}@example.com"} for i in range(1001)]
    payload = {
        "title": "Huge Batch Job",
        "event_name": "Event",
        "recipients": recipients
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422

def test_job_processing_and_certificate_retrieval(client, db_session):
    """Test full workflow: create job, process background task, check progress, retrieve file and metadata."""
    payload = {
        "title": "FastAPI Essentials",
        "event_name": "PyClub",
        "file_format": "png",
        "recipients": [
            {"recipient_name": "Charlie Brown", "recipient_email": "charlie@example.com"}
        ]
    }
    create_res = client.post("/api/v1/jobs", json=payload)
    assert create_res.status_code == 202
    job_id = create_res.json()["id"]

    # Execute background worker task synchronously with db_session
    process_certificate_job(job_id, db=db_session)

    # Query detailed status
    status_res = client.get(f"/api/v1/jobs/{job_id}")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["status"] == JOB_STATUS_COMPLETED
    assert status_data["success_count"] == 1
    assert status_data["failed_count"] == 0
    assert status_data["progress"] == 100.0
    assert len(status_data["certificates"]) == 1

    cert = status_data["certificates"][0]
    assert cert["status"] == "COMPLETED"
    assert cert["download_url"] is not None

    # Retrieve certificate image file
    download_res = client.get(cert["download_url"])
    assert download_res.status_code == 200
    assert download_res.headers["content-type"] == "image/png"
    assert len(download_res.content) > 1000

    # Retrieve certificate metadata
    meta_res = client.get(f"/api/v1/certificates/{cert['id']}/metadata")
    assert meta_res.status_code == 200
    meta_data = meta_res.json()
    assert meta_data["recipient_name"] == "Charlie Brown"
    assert meta_data["status"] == "COMPLETED"

    # Retrieve batch ZIP archive
    zip_res = client.get(f"/api/v1/jobs/{job_id}/download")
    assert zip_res.status_code == 200
    assert zip_res.headers["content-type"] == "application/zip"
    assert len(zip_res.content) > 500

def test_list_jobs(client):
    """Test listing jobs with pagination."""
    res = client.get("/api/v1/jobs?skip=0&limit=10")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_non_existent_job_and_certificate_404(client):
    """Test 404 responses for non-existent job and certificate UUIDs."""
    res_job = client.get("/api/v1/jobs/00000000-0000-0000-0000-000000000000")
    assert res_job.status_code == 404

    res_cert = client.get("/api/v1/certificates/00000000-0000-0000-0000-000000000000")
    assert res_cert.status_code == 404

    res_meta = client.get("/api/v1/certificates/00000000-0000-0000-0000-000000000000/metadata")
    assert res_meta.status_code == 404
