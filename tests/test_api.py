import pytest
from app.services.job_processor import process_certificate_job

def test_health_check(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_create_job_success(client):
    payload = {
        "title": "Annual Developer Conference",
        "event_name": "DevCon 2026",
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
    assert data["total_count"] == 2
    assert data["status"] == "pending"
    assert "id" in data

def test_input_validation_empty_recipients(client):
    payload = {
        "title": "Invalid Job",
        "event_name": "Event",
        "recipients": []
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422

def test_input_validation_invalid_email(client):
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
    payload = {
        "title": "Blank Name Job",
        "event_name": "Event",
        "recipients": [
            {"recipient_name": "   ", "recipient_email": "valid@example.com"}
        ]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422

def test_job_processing_and_certificate_retrieval(client, db_session):
    payload = {
        "title": "Python Workshop",
        "event_name": "PyClub",
        "default_course_name": "FastAPI Essentials",
        "file_format": "png",
        "recipients": [
            {"recipient_name": "Charlie Brown", "recipient_email": "charlie@example.com"}
        ]
    }
    create_res = client.post("/api/v1/jobs", json=payload)
    assert create_res.status_code == 202
    job_id = create_res.json()["id"]

    # Process job synchronously using db_session
    process_certificate_job(job_id, db=db_session)

    # Fetch status
    status_res = client.get(f"/api/v1/jobs/{job_id}")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["status"] == "completed"
    assert status_data["success_count"] == 1
    assert status_data["failed_count"] == 0
    assert len(status_data["certificates"]) == 1

    cert = status_data["certificates"][0]
    assert cert["status"] == "completed"
    assert cert["download_url"] is not None

    # Retrieve individual certificate file
    download_res = client.get(cert["download_url"])
    assert download_res.status_code == 200
    assert download_res.headers["content-type"] == "image/png"
    assert len(download_res.content) > 1000

    # Retrieve certificate metadata
    meta_res = client.get(f"/api/v1/certificates/{cert['id']}/metadata")
    assert meta_res.status_code == 200
    meta_data = meta_res.json()
    assert meta_data["recipient_name"] == "Charlie Brown"

    # Retrieve batch ZIP file
    zip_res = client.get(f"/api/v1/jobs/{job_id}/download")
    assert zip_res.status_code == 200
    assert zip_res.headers["content-type"] == "application/zip"
    assert len(zip_res.content) > 500

def test_list_jobs(client):
    res = client.get("/api/v1/jobs")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
