"""
ComicCraft - FastAPI Routes
Main application routing logic for user interactions, API endpoints, AI pipelines, and comic exports.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from app.gemini_flash import generate_outline
from app.gemini_pro import generate_story
from app.image_generator import generate_image
from app.layout_builder import build_comic_layout
from app.exporters import save_pdf

logger = logging.getLogger("comiccraft.routes")
logging.basicConfig(level=logging.INFO)

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
EXPORTS_DIR = BASE_DIR / "static" / "exports"
PANELS_DIR = BASE_DIR / "static" / "panels"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
router = APIRouter()


class PromptRequest(BaseModel):
    """Pydantic schema for JSON-based comic generation requests."""
    story_prompt: str = Field(..., min_length=3, description="Main idea or premise for the comic story", example="A brave fox exploring an enchanted forest")
    character_name: str = Field(default="Hero", description="Name of the main protagonist", example="Finn the Fox")
    setting: str = Field(default="Enchanted Forest", description="Location or world setting", example="Enchanted Forest")
    tone: str = Field(default="Dramatic", description="Mood of the story: Dramatic, Funny, Light-hearted, Poetic", example="Dramatic")
    art_style: str = Field(default="Comic Book", description="Visual style: Comic Book, Anime, Realistic, Pixel Art, Watercolor, Noir", example="Anime")


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Loads the homepage (index.html) where users submit their comic story details."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"page_title": "ComicCraft - AI Comic Story Creator"}
    )


@router.post("/generate", response_class=HTMLResponse)
async def generate_comic_form(
    request: Request,
    story_prompt: str = Form(...),
    character_name: str = Form("Hero"),
    setting: str = Form("Enchanted Forest"),
    tone: str = Form("Dramatic"),
    art_style: str = Form("Comic Book")
):
    """
    Handles form submission from index.html:
    1. Calls Gemini Flash to generate a 5-panel outline.
    2. Calls Gemini Pro to expand into narration and dialogue.
    3. Calls generate_image() for each panel to create illustrations.
    4. Builds the comic layout.
    5. Saves and exports the comic to PDF.
    6. Renders comic_preview.html with the generated comic strip.
    """
    try:
        logger.info(f"Form submission received: prompt='{story_prompt}', character='{character_name}', tone='{tone}', style='{art_style}'")

        # 1. Generate 5-Panel Outline via Gemini Flash
        outline = generate_outline(
            prompt=story_prompt,
            character_name=character_name,
            setting=setting,
            tone=tone,
            art_style=art_style
        )

        # 2. Generate Story Narration and Dialogues via Gemini Pro
        story_content = generate_story(
            outline=outline,
            character_name=character_name,
            setting=setting,
            tone=tone
        )

        # 3. Generate Illustrations for each panel
        images = []
        for panel in outline:
            p_num = panel.get("panel_number", len(images) + 1)
            img_prompt = panel.get("image_prompt", f"{art_style} scene of {character_name}")
            img_path = generate_image(prompt=img_prompt, panel_number=p_num, art_style=art_style)
            images.append(img_path)

        # 4. Build Structured Comic Layout
        layout = build_comic_layout(outline=outline, story_content=story_content, images=images)

        # 5. Compile and Export Comic to PDF
        comic_title = f"{character_name}'s Adventure in {setting}"
        pdf_path = save_pdf(
            layout=layout,
            title=comic_title,
            author="ComicCraft AI",
            character_name=character_name,
            setting=setting,
            tone=tone,
            art_style=art_style
        )
        pdf_filename = Path(pdf_path).name

        return templates.TemplateResponse(
            request=request,
            name="comic_preview.html",
            context={
                "title": comic_title,
                "story_prompt": story_prompt,
                "character_name": character_name,
                "setting": setting,
                "tone": tone,
                "art_style": art_style,
                "layout": layout,
                "pdf_url": pdf_path,
                "pdf_filename": pdf_filename
            }
        )

    except Exception as e:
        logger.error(f"Error during comic generation: {e}", exc_info=True)
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "error_message": f"Comic generation failed: {str(e)}. Please check your prompt and try again."
            },
            status_code=500
        )


@router.post("/generate-comic/json")
async def generate_comic_json(req: PromptRequest):
    """
    API route that accepts JSON payloads, triggers the full comic creation pipeline,
    and returns comic layout data along with the generated PDF path.
    """
    try:
        logger.info(f"JSON API Request received for prompt: '{req.story_prompt}'")

        # 1. Outline
        outline = generate_outline(
            prompt=req.story_prompt,
            character_name=req.character_name,
            setting=req.setting,
            tone=req.tone,
            art_style=req.art_style
        )

        # 2. Story
        story_content = generate_story(
            outline=outline,
            character_name=req.character_name,
            setting=req.setting,
            tone=req.tone
        )

        # 3. Images
        images = []
        for panel in outline:
            p_num = panel.get("panel_number", len(images) + 1)
            img_prompt = panel.get("image_prompt", f"{req.art_style} scene of {req.character_name}")
            img_path = generate_image(prompt=img_prompt, panel_number=p_num, art_style=req.art_style)
            images.append(img_path)

        # 4. Layout
        layout = build_comic_layout(outline=outline, story_content=story_content, images=images)

        # 5. PDF Export
        comic_title = f"{req.character_name}'s Adventure in {req.setting}"
        pdf_path = save_pdf(
            layout=layout,
            title=comic_title,
            author="ComicCraft AI",
            character_name=req.character_name,
            setting=req.setting,
            tone=req.tone,
            art_style=req.art_style
        )

        return JSONResponse({
            "status": "success",
            "title": comic_title,
            "metadata": {
                "story_prompt": req.story_prompt,
                "character_name": req.character_name,
                "setting": req.setting,
                "tone": req.tone,
                "art_style": req.art_style
            },
            "outline": outline,
            "story": story_content,
            "layout": layout,
            "pdf_path": pdf_path,
            "pdf_filename": Path(pdf_path).name,
            "download_url": f"/download-pdf/{Path(pdf_path).name}"
        })

    except Exception as e:
        logger.error(f"API Error in /generate-comic/json: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export-success", response_class=HTMLResponse)
async def export_success(
    request: Request,
    pdf: Optional[str] = None,
    title: Optional[str] = "Your Comic Strip",
    character: Optional[str] = "Hero"
):
    """
    Displays the Comic Export Success page confirming the successful creation and download of the comic.
    Provides a CTA button to create another comic.
    """
    pdf_filename = Path(pdf).name if pdf else None
    download_url = f"/download-pdf/{pdf_filename}" if pdf_filename else pdf

    return templates.TemplateResponse(
        request=request,
        name="export_success.html",
        context={
            "pdf_url": pdf or "/static/exports/",
            "pdf_filename": pdf_filename,
            "download_url": download_url,
            "comic_title": title,
            "character_name": character
        }
    )


@router.get("/test-image")
@router.post("/test-image")
async def test_image(
    prompt: str = "A cybernetic fox perched on a neon rooftop, futuristic city, comic book style",
    art_style: str = "Comic Book"
):
    """
    Developer utility route to test image generation directly from a prompt
    without generating a full comic storyline.
    """
    try:
        img_url = generate_image(prompt=prompt, panel_number=1, art_style=art_style)
        return JSONResponse({
            "status": "success",
            "prompt": prompt,
            "art_style": art_style,
            "image_url": img_url,
            "message": "Image generated successfully."
        })
    except Exception as e:
        logger.error(f"Image generation test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Image test failed: {str(e)}")


@router.get("/download-pdf/{filename}")
async def download_pdf(filename: str):
    """Directly serves the requested PDF as a downloadable file attachment."""
    safe_name = os.path.basename(filename)
    file_path = EXPORTS_DIR / safe_name
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Requested comic PDF was not found.")
        
    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=safe_name,
        headers={"Content-Disposition": f'attachment; filename="{safe_name}"'}
    )


@router.get("/api/health")
async def health_check():
    """Health status and configuration inspection endpoint."""
    gemini_key_set = bool(os.getenv("GEMINI_API_KEY", "").strip())
    hf_key_set = bool(os.getenv("HF_API_KEY", "").strip())
    
    return {
        "status": "healthy",
        "service": "ComicCraft AI",
        "version": "1.0.0",
        "gemini_api_configured": gemini_key_set,
        "hf_api_configured": hf_key_set,
        "storage": {
            "panels_directory": str(PANELS_DIR),
            "exports_directory": str(EXPORTS_DIR)
        }
    }
