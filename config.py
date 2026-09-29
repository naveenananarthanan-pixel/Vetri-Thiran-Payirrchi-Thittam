"""Central configuration for LegalEase. Values come from the .env file."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")

IMAGE_DIR = BASE_DIR / "Image"
# Dark-text logo, used inside .docx and .pdf (white paper)
LOGO_PATH = IMAGE_DIR / "Logo.png"
# White-text logo, used on the dark Streamlit web page
WEB_LOGO_PATH = IMAGE_DIR / "inverseLogo.png"

COMPANY_FOOTER = "LegalEase Inc. | contact@legalease.com | All Rights Reserved."
REQUEST_TIMEOUT = 180  # seconds the frontend waits for Gemini
