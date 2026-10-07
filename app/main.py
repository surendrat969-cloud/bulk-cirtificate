from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.api import jobs, certificates

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    init_db()
    yield
    # Shutdown actions (if any)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Bulk Certificate Generation API with async processing, progress tracking, and resilient failure handling.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Enable CORS for web client integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(jobs.router)
app.include_router(certificates.router)

@app.get("/", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "docs": "/docs"
    }
