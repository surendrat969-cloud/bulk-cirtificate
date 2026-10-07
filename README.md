# Bulk Certificate Generator API

A high-performance Python backend API built with **FastAPI**, **SQLAlchemy**, and **Pillow (PIL)** for generating personalized certificates in bulk. 

The system accepts batch requests for multiple recipients, validates input data, generates high-resolution certificates asynchronously in background workers, tracks job progress in real time, isolates individual failures, and provides endpoints to download generated certificates individually or as batch ZIP archives.

---

## Features

- **Bulk Processing**: Accepts requests containing hundreds of recipients in a single API call.
- **Asynchronous Execution**: Uses FastAPI background worker processing so API clients receive immediate HTTP 202 Accepted responses without blocking.
- **Partial Failure Resilience**: Failures during generation for a specific recipient (e.g., corrupt characters or missing fields) are isolated. Valid certificates in the same job continue generating successfully.
- **Real-Time Progress Tracking**: Endpoint returns live progress metrics (`total_count`, `processed_count`, `success_count`, `failed_count`) and per-recipient status breakdown.
- **Flexible File Formats**: Supports outputting certificates in high-resolution **PNG** or **PDF** format.
- **Batch Export**: Allows downloading all completed certificates in a job as a single compressed `.zip` archive.
- **Auto OpenAPI Documentation**: Interactive Swagger UI (`/docs`) and ReDoc (`/redoc`) available out of the box.

---

## Technology Stack

- **Language**: Python 3.10+
- **Web Framework**: FastAPI (Starlette)
- **ORMs & Database**: SQLAlchemy 2.0 with SQLite relational database
- **Validation**: Pydantic V2 & email-validator
- **Certificate Engine**: Pillow (PIL) for image/PDF rendering
- **Testing**: pytest & HTTPX

---

## Project Structure

```text
bulk-certificate-generator/
├── app/
│   ├── api/
│   │   ├── certificates.py    # File retrieval & metadata endpoints
│   │   └── jobs.py            # Job creation, status, and batch zip endpoints
│   ├── config.py              # Application settings and storage paths
│   ├── database.py            # SQLAlchemy database engine and session setup
│   ├── main.py                # FastAPI app initialization and middleware
│   ├── models.py              # Relational DB models (Job, Certificate)
│   ├── schemas.py             # Pydantic validation and response models
│   └── services/
│       ├── generator.py       # Pillow certificate rendering engine
│       └── job_processor.py   # Asynchronous background job processor
├── tests/
│   ├── conftest.py            # Pytest test fixtures and DB setup
│   ├── test_api.py            # API endpoint integration tests
│   ├── test_failure_handling.py # Partial failure resilience unit tests
│   └── test_generator.py      # Certificate rendering engine tests
├── requirements.txt           # Project Python dependencies
└── README.md                  # Project documentation
```

---

## Setup Instructions

### 1. Prerequisites
Ensure Python 3.10+ is installed on your system.

### 2. Install Dependencies
Install all required packages from `requirements.txt`:

```bash
pip install -r requirements.txt
```

---

## Running the Application

Start the development server using `uvicorn`:

```bash
uvicorn app.main:app --reload --port 8000
```

Once running:
- **API Base URL**: `http://localhost:8000`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`

---

## Running Tests

Execute the complete test suite using `pytest`:

```bash
pytest tests/ -v
```

Tests cover:
1. Job creation (`POST /api/v1/jobs`)
2. Input validation (invalid emails, empty names, missing fields)
3. Certificate generation engine (PNG and PDF rendering)
4. Job status tracking and progress counters
5. Partial failure resilience (individual recipient failures)
6. File retrieval and ZIP batch export

---

## API Usage Guide

### 1. Submit Certificate Generation Job
**Endpoint**: `POST /api/v1/jobs`

Submit a job request containing batch metadata and a list of recipients.

#### Example Request:
```bash
curl -X POST "http://localhost:8000/api/v1/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Full Stack Web Development Bootcamp",
    "event_name": "Tech Academy 2026",
    "default_course_name": "Full Stack Engineering",
    "issue_date": "October 07, 2026",
    "file_format": "png",
    "recipients": [
      {
        "recipient_name": "Alice Johnson",
        "recipient_email": "alice@example.com"
      },
      {
        "recipient_name": "Bob Smith",
        "recipient_email": "bob@example.com",
        "course_name": "Advanced Python & FastAPI"
      }
    ]
  }'
```

#### Example Response (HTTP 202 Accepted):
```json
{
  "id": "e9a1b2c3-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
  "title": "Full Stack Web Development Bootcamp",
  "event_name": "Tech Academy 2026",
  "file_format": "png",
  "status": "pending",
  "total_count": 2,
  "processed_count": 0,
  "success_count": 0,
  "failed_count": 0,
  "created_at": "2026-10-07T18:15:00Z",
  "updated_at": "2026-10-07T18:15:00Z"
}
```

---

### 2. Check Job Progress & Status
**Endpoint**: `GET /api/v1/jobs/{job_id}`

Query live progress and detailed status for each recipient in the batch.

#### Example Request:
```bash
curl -X GET "http://localhost:8000/api/v1/jobs/e9a1b2c3-4d5e-6f7a-8b9c-0d1e2f3a4b5c"
```

#### Example Response:
```json
{
  "id": "e9a1b2c3-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
  "title": "Full Stack Web Development Bootcamp",
  "event_name": "Tech Academy 2026",
  "file_format": "png",
  "status": "completed",
  "total_count": 2,
  "processed_count": 2,
  "success_count": 2,
  "failed_count": 0,
  "created_at": "2026-10-07T18:15:00Z",
  "updated_at": "2026-10-07T18:15:02Z",
  "certificates": [
    {
      "id": "c1111111-2222-3333-4444-555555555555",
      "job_id": "e9a1b2c3-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
      "recipient_name": "Alice Johnson",
      "recipient_email": "alice@example.com",
      "course_name": "Full Stack Engineering",
      "issue_date": "October 07, 2026",
      "status": "completed",
      "file_format": "png",
      "download_url": "/api/v1/certificates/c1111111-2222-3333-4444-555555555555",
      "error_message": null,
      "created_at": "2026-10-07T18:15:00Z",
      "updated_at": "2026-10-07T18:15:01Z"
    }
  ]
}
```

---

### 3. Retrieve Individual Certificate File
**Endpoint**: `GET /api/v1/certificates/{certificate_id}`

Download or view the generated PNG image or PDF document.

#### Example Request:
```bash
curl -O -J "http://localhost:8000/api/v1/certificates/c1111111-2222-3333-4444-555555555555"
```

---

### 4. Download Batch ZIP Archive
**Endpoint**: `GET /api/v1/jobs/{job_id}/download`

Download all completed certificates for a job in a single `.zip` file.

#### Example Request:
```bash
curl -O -J "http://localhost:8000/api/v1/jobs/e9a1b2c3-4d5e-6f7a-8b9c-0d1e2f3a4b5c/download"
```

---

## Design & Architecture Decisions

1. **FastAPI & Asynchronous Background Tasks**:
   - Bulk certificate creation involves heavy rendering operations. By queueing job processing in `BackgroundTasks`, the API immediately returns HTTP 202 Accepted to the client. This keeps the backend responsive regardless of batch size.

2. **Per-Recipient Failure Isolation**:
   - Each recipient is rendered inside an isolated `try...except` block in `job_processor.py`.
   - If rendering fails for one recipient, the exception string is logged to `error_message`, `failed_count` is incremented, and processing continues immediately for the remaining recipients.
   - The job's overall status reflects partial completion (`partially_completed`) if some recipients fail, allowing valid certificates to be retrieved without re-running the whole batch.

3. **Pillow Rendering Engine**:
   - Pillow provides cross-platform, zero-dependency image and PDF generation in pure Python.
   - Certificates feature double borders, gold/navy accents, dynamic text positioning, corner polygons, and verification seals.

4. **Relational Database Design**:
   - `Job` table manages batch execution states, overall status, and progress metrics.
   - `Certificate` table manages per-recipient state, file locations, and error messages.
