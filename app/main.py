"""
ComicCraft - AI Comic Story Creator
Main FastAPI Application Entrypoint
"""

import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routes import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("comiccraft")

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Ensure runtime directories exist
STATIC_DIR = BASE_DIR / "static"
PANELS_DIR = STATIC_DIR / "panels"
EXPORTS_DIR = STATIC_DIR / "exports"
CSS_DIR = STATIC_DIR / "css"
IMAGES_DIR = STATIC_DIR / "images"

for directory in [STATIC_DIR, PANELS_DIR, EXPORTS_DIR, CSS_DIR, IMAGES_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Initialize FastAPI app
app = FastAPI(
    title="ComicCraft - AI Comic Story Creator",
    description="Transform your imaginative prompts into personalized 5-panel comic books with Google Gemini AI and Stable Diffusion.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for external API clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Include main router
app.include_router(router)


@app.on_event("startup")
async def startup_event():
    logger.info("=====================================================")
    logger.info("  ComicCraft - AI Comic Story Creator Started")
    logger.info("  Web UI:   http://127.0.0.1:8000")
    logger.info("  API Docs: http://127.0.0.1:8000/docs")
    logger.info("  Theme:    Modern Crisp White Theme")
    logger.info("=====================================================")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
