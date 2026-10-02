"""
ComicCraft - Comprehensive Verification & Test Suite
Tests all modules: Flash outline, Pro story, image generator, layout builder, PDF exporter, and FastAPI endpoints.
"""

import sys
import os
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from app.gemini_flash import generate_outline
from app.gemini_pro import generate_story, parse_story_to_panels
from app.image_generator import generate_image
from app.layout_builder import build_comic_layout
from app.exporters import save_pdf
from app.main import app


def test_core_pipeline():
    print("\n--- TEST 1: GEMINI FLASH OUTLINE GENERATION ---")
    outline = generate_outline(
        prompt="A brave fox exploring an enchanted forest",
        character_name="Finn",
        setting="Enchanted Forest",
        tone="Dramatic",
        art_style="Comic Book"
    )
    assert isinstance(outline, list), "Outline must be a list"
    assert len(outline) == 5, f"Expected 5 panels, got {len(outline)}"
    for idx, panel in enumerate(outline):
        assert "panel_number" in panel
        assert "title" in panel
        assert "scene_description" in panel
        assert "image_prompt" in panel
    print(f"SUCCESS: Generated 5-panel outline: {[p['title'] for p in outline]}")

    print("\n--- TEST 2: GEMINI PRO STORY GENERATION ---")
    story = generate_story(
        outline=outline,
        character_name="Finn",
        setting="Enchanted Forest",
        tone="Dramatic"
    )
    assert isinstance(story, str) and len(story) > 50, "Story must be a non-empty string"
    parsed_panels = parse_story_to_panels(story, outline)
    assert len(parsed_panels) == 5, f"Expected 5 parsed panels, got {len(parsed_panels)}"
    print(f"SUCCESS: Generated story and parsed {len(parsed_panels)} panel dialogues.")

    print("\n--- TEST 3: IMAGE GENERATOR ---")
    img_path = generate_image("A brave fox exploring an enchanted forest, comic art", panel_number=1, art_style="Comic Book")
    assert img_path.startswith("/static/panels/"), f"Unexpected image path: {img_path}"
    # Verify file exists on disk
    file_on_disk = PROJECT_ROOT / img_path.lstrip("/\\")
    assert file_on_disk.exists(), f"Image file not found on disk: {file_on_disk}"
    assert file_on_disk.stat().st_size > 500, f"Image file is empty: {file_on_disk}"
    print(f"SUCCESS: Generated panel image at: {img_path} ({file_on_disk.stat().st_size} bytes)")

    print("\n--- TEST 4: LAYOUT BUILDER ---")
    images = [img_path] * 5
    layout = build_comic_layout(outline, story, images)
    assert len(layout) == 5, f"Expected 5 layout items, got {len(layout)}"
    assert layout[0]["panel_number"] == 1
    assert layout[0]["image_path"] == img_path
    print(f"SUCCESS: Assembled comic layout with {len(layout)} panels.")

    print("\n--- TEST 5: PDF EXPORTER ---")
    pdf_url = save_pdf(
        layout=layout,
        title="Finn's Forest Adventure",
        author="ComicCraft AI",
        character_name="Finn",
        setting="Enchanted Forest",
        tone="Dramatic",
        art_style="Comic Book"
    )
    assert pdf_url.startswith("/static/exports/"), f"Unexpected PDF path: {pdf_url}"
    pdf_on_disk = PROJECT_ROOT / pdf_url.lstrip("/\\")
    assert pdf_on_disk.exists(), f"PDF not found on disk: {pdf_on_disk}"
    assert pdf_on_disk.stat().st_size > 1000, f"PDF file too small: {pdf_on_disk.stat().st_size} bytes"
    print(f"SUCCESS: Generated comic PDF at {pdf_url} ({pdf_on_disk.stat().st_size} bytes).")


def test_fastapi_endpoints():
    print("\n--- TEST 6: FASTAPI ENDPOINTS & WEB ROUTING ---")
    client = TestClient(app)

    # 1. GET /
    res_home = client.get("/")
    assert res_home.status_code == 200, f"Home returned {res_home.status_code}"
    assert "ComicCraft" in res_home.text
    print("SUCCESS: GET / returned 200 with home template.")

    # 2. GET /api/health
    res_health = client.get("/api/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"
    print("SUCCESS: GET /api/health returned healthy.")

    # 3. GET /test-image
    res_img = client.get("/test-image?prompt=test%20fox%20hero&art_style=Anime")
    assert res_img.status_code == 200
    assert "image_url" in res_img.json()
    print("SUCCESS: GET /test-image returned valid image URL.")

    # 4. POST /generate-comic/json
    res_api = client.post("/generate-comic/json", json={
        "story_prompt": "A robot learning to paint sunflowers in spring",
        "character_name": "Rusty",
        "setting": "Sunlit Garden",
        "tone": "Light-hearted",
        "art_style": "Watercolor"
    })
    assert res_api.status_code == 200, f"API returned {res_api.status_code}: {res_api.text}"
    api_data = res_api.json()
    assert api_data["status"] == "success"
    assert len(api_data["layout"]) == 5
    assert api_data["pdf_path"]
    print("SUCCESS: POST /generate-comic/json generated 5 panels and PDF.")

    # 5. POST /generate (Form Submission)
    res_form = client.post("/generate", data={
        "story_prompt": "A brave fox exploring an enchanted forest",
        "character_name": "Finn",
        "setting": "Enchanted Forest",
        "tone": "Dramatic",
        "art_style": "Comic Book"
    })
    assert res_form.status_code == 200, f"Form post returned {res_form.status_code}"
    assert "Download Your Comic as PDF" in res_form.text
    assert "PANEL 1" in res_form.text
    print("SUCCESS: POST /generate rendered comic_preview.html with full panels.")

    # 6. GET /export-success
    res_success = client.get(f"/export-success?pdf={api_data['pdf_path']}&title=Rusty%20Sunflower&character=Rusty")
    assert res_success.status_code == 200
    assert "Comic Export Successful!" in res_success.text
    print("SUCCESS: GET /export-success rendered confirmation page.")

    # 7. GET /download-pdf/{filename}
    filename = Path(api_data["pdf_path"]).name
    res_dl = client.get(f"/download-pdf/{filename}")
    assert res_dl.status_code == 200
    assert res_dl.headers["content-type"] == "application/pdf"
    assert len(res_dl.content) > 1000
    print(f"SUCCESS: GET /download-pdf/{filename} returned {len(res_dl.content)} bytes PDF.")

    print("\n[PASS] ALL TESTS PASSED SUCCESSFULLY! COMICCRAFT IS FULLY VERIFIED.")


if __name__ == "__main__":
    test_core_pipeline()
    test_fastapi_endpoints()
