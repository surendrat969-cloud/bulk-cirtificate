import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"
CERTIFICATES_DIR = STORAGE_DIR / "certificates"
ZIPS_DIR = STORAGE_DIR / "zips"

# Ensure directories exist
CERTIFICATES_DIR.mkdir(parents=True, exist_ok=True)
ZIPS_DIR.mkdir(parents=True, exist_ok=True)

class Settings(BaseModel):
    PROJECT_NAME: str = "Bulk Certificate Generator API"
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/certificates.db"
    STORAGE_DIR: Path = STORAGE_DIR
    CERTIFICATES_DIR: Path = CERTIFICATES_DIR
    ZIPS_DIR: Path = ZIPS_DIR
    
settings = Settings()
