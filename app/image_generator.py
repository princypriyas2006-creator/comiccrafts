"""
ComicCraft - Image Generator
Generates comic-style panel illustrations from prompts using Stable Diffusion,
cloud inference APIs, and an artistic fallback renderer.
"""

import hashlib
import logging
import os
import re
import time
import urllib.parse
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import requests

load_dotenv()

logger = logging.getLogger("comiccraft.image_generator")
logging.basicConfig(level=logging.INFO)

# Base directory paths
BASE_DIR = Path(__file__).resolve().parent.parent
PANELS_DIR = BASE_DIR / "static" / "panels"
PANELS_DIR.mkdir(parents=True, exist_ok=True)

# Environment keys
HF_API_KEY = os.getenv("HF_API_KEY", "").strip()

# Check for local diffusers pipeline if user has installed it and has CUDA
_SD_PIPELINE = None


def _get_sd_pipeline():
    """Lazily load local Diffusers Stable Diffusion pipeline if enabled & available."""
    global _SD_PIPELINE
    if _SD_PIPELINE is not None:
        return _SD_PIPELINE
    
    # Check if local pipeline is requested via env
    if os.getenv("ENABLE_LOCAL_SD", "false").lower() == "true":
        try:
            import torch
            from diffusers import StableDiffusionPipeline
            logger.info("Initializing local Stable Diffusion pipeline (runwayml/stable-diffusion-v1-5)...")
            device = "cuda" if torch.cuda.is_available() else "cpu"
            pipe = StableDiffusionPipeline.from_pretrained(
                "runwayml/stable-diffusion-v1-5",
                torch_dtype=torch.float16 if device == "cuda" else torch.float32
            )
            pipe = pipe.to(device)
            _SD_PIPELINE = pipe
            logger.info("Local Stable Diffusion loaded successfully.")
            return _SD_PIPELINE
        except Exception as e:
            logger.warning(f"Could not initialize local Stable Diffusion: {e}")
    return None


def sanitize_filename(prompt: str, max_length: int = 40) -> str:
    """Sanitizes prompt text to create a clean, safe filename."""
    # Remove non-alphanumeric chars
    slug = re.sub(r'[^a-zA-Z0-9\s_-]', '', prompt).strip()
    slug = re.sub(r'[\s_]+', '_', slug).lower()
    if not slug:
        slug = "comic_scene"
    return slug[:max_length]


def _generate_artistic_comic_canvas(
    prompt: str,
    panel_number: int,
    art_style: str,
    output_path: Path
) -> str:
    """
    Creates a rich, high-resolution comic book illustration with comic halftones,
    dynamic gradients, stylized comic panel borders, and dynamic action emblems.
    Guarantees instantaneous, zero-failure rendering in any environment.
    """
    width, height = 768, 768
    img = Image.new("RGB", (width, height), "#FFFFFF")
    draw = ImageDraw.Draw(img)

    # Style palette mapping
    style_lower = art_style.lower()
    if "anime" in style_lower:
        bg_top = (255, 235, 245)
        bg_bottom = (175, 205, 255)
        accent_color = (255, 75, 140)
        bubble_color = (255, 255, 255)
        sfx_text = "SUGOI!"
    elif "pixel" in style_lower:
        bg_top = (15, 23, 42)
        bg_bottom = (49, 46, 129)
        accent_color = (34, 197, 94)
        bubble_color = (254, 240, 138)
        sfx_text = "LEVEL UP!"
    elif "noir" in style_lower:
        bg_top = (30, 30, 30)
        bg_bottom = (10, 10, 10)
        accent_color = (239, 68, 68)
        bubble_color = (245, 245, 245)
        sfx_text = "CLICK..."
    elif "watercolor" in style_lower:
        bg_top = (254, 243, 199)
        bg_bottom = (191, 219, 254)
        accent_color = (13, 148, 136)
        bubble_color = (255, 255, 255)
        sfx_text = "SWOOSH!"
    else:  # classic comic book
        bg_top = (254, 240, 138)
        bg_bottom = (239, 68, 68)
        accent_color = (79, 70, 229)
        bubble_color = (255, 255, 255)
        sfx_text = ["POW!", "WHAM!", "BOOM!", "ZAP!", "KRAK!"][(panel_number - 1) % 5]

    # Render gradient
    for y in range(height):
        r = int(bg_top[0] + (bg_bottom[0] - bg_top[0]) * (y / height))
        g = int(bg_top[1] + (bg_bottom[1] - bg_top[1]) * (y / height))
        b = int(bg_top[2] + (bg_bottom[2] - bg_top[2]) * (y / height))
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Comic dot pattern / action speed lines
    center_x, center_y = width // 2, height // 2
    for angle_deg in range(0, 360, 15):
        import math
        rad = math.radians(angle_deg)
        x_edge = int(center_x + math.cos(rad) * width)
        y_edge = int(center_y + math.sin(rad) * height)
        draw.line([(center_x, center_y), (x_edge, y_edge)], fill=(255, 255, 255, 60), width=2)

    # Central comic action starburst / shield
    burst_points = []
    num_points = 14
    for i in range(num_points * 2):
        angle = i * (math.pi / num_points)
        radius = 240 if i % 2 == 0 else 140
        bx = center_x + radius * math.cos(angle)
        by = center_y + radius * math.sin(angle)
        burst_points.append((bx, by))
    
    # Draw starburst shadow and fill
    shadow_points = [(p[0] + 6, p[1] + 6) for p in burst_points]
    draw.polygon(shadow_points, fill=(15, 23, 42, 100))
    draw.polygon(burst_points, fill=bubble_color, outline=(15, 23, 42), width=4)

    # Stylized Panel Frame & Comic Header
    draw.rectangle([12, 12, width - 12, height - 12], outline=(15, 23, 42), width=6)
    draw.rectangle([20, 20, width - 20, height - 20], outline=(255, 255, 255), width=2)

    # Panel badge banner (top left)
    draw.rectangle([24, 24, 180, 70], fill=(15, 23, 42))
    draw.rectangle([28, 28, 176, 66], fill=accent_color)
    
    # Text drawing
    try:
        font_large = ImageFont.truetype("arialbd.ttf", 36)
        font_medium = ImageFont.truetype("arialbd.ttf", 22)
        font_small = ImageFont.truetype("arial.ttf", 16)
    except Exception:
        font_large = font_medium = font_small = ImageFont.load_default()

    # Badge text
    draw.text((38, 36), f"PANEL {panel_number}", fill=(255, 255, 255), font=font_medium)

    # Style pill (top right)
    style_text = art_style.upper()
    pill_w = len(style_text) * 11 + 30
    draw.rectangle([width - 24 - pill_w, 24, width - 24, 68], fill=(15, 23, 42))
    draw.rectangle([width - 22 - pill_w, 26, width - 26, 66], fill=(255, 255, 255))
    draw.text((width - 15 - pill_w, 36), style_text, fill=(15, 23, 42), font=font_small)

    # SFX burst text in center
    sfx = sfx_text if isinstance(sfx_text, str) else "ACTION!"
    sfx_w = len(sfx) * 22
    draw.text((center_x - sfx_w // 2 + 3, center_y - 25 + 3), sfx, fill=(15, 23, 42), font=font_large)
    draw.text((center_x - sfx_w // 2, center_y - 25), sfx, fill=accent_color, font=font_large)

    # Bottom scene prompt caption banner
    banner_y = height - 120
    draw.rectangle([24, banner_y, width - 24, height - 24], fill=(15, 23, 42))
    draw.rectangle([26, banner_y + 2, width - 26, height - 26], fill=(255, 255, 255))
    
    # Truncate prompt safely for preview on image
    clean_p = prompt.replace("\n", " ")
    if len(clean_p) > 75:
        clean_p = clean_p[:72] + "..."
    draw.text((36, banner_y + 12), f"Scene: {clean_p}", fill=(15, 23, 42), font=font_small)
    draw.text((36, banner_y + 36), f"Style: {art_style} | ComicCraft AI Studio", fill=(100, 116, 139), font=font_small)

    img.save(output_path, format="PNG", quality=95)
    return str(output_path)


def generate_image(prompt: str, panel_number: int = 1, art_style: str = "Comic Book") -> str:
    """
    Generates a comic-style image based on the provided image prompt.
    Sanitizes the prompt for safe filenames and saves the generated image
    to the static/panels directory.
    
    Returns:
        The relative web-accessible file path to the saved image (e.g., '/static/panels/...').
    """
    timestamp = int(time.time())
    slug = sanitize_filename(prompt, max_length=25)
    filename = f"panel_{panel_number}_{timestamp}_{slug}.png"
    output_path = PANELS_DIR / filename
    
    logger.info(f"Generating image for Panel {panel_number}: '{prompt[:60]}...'")

    # 1. Try local Stable Diffusion pipeline if initialized
    pipe = _get_sd_pipeline()
    if pipe:
        try:
            enhanced_prompt = f"{prompt}, {art_style} style, comic book art, detailed line work, vivid vibrant colors, masterpiece, 8k resolution"
            image = pipe(enhanced_prompt, num_inference_steps=25, guidance_scale=7.5).images[0]
            image.save(output_path)
            logger.info(f"Saved local Stable Diffusion image to {output_path}")
            return f"/static/panels/{filename}"
        except Exception as e:
            logger.warning(f"Local Stable Diffusion inference error: {e}")

    # 2. Try Pollinations Cloud AI generator (Stable Diffusion / FLUX based, fast, high aesthetic quality)
    try:
        enhanced_prompt = f"{prompt}, {art_style} comic book illustration, vibrant comic art, sharp ink lines, masterpiece, highly detailed, dramatic lighting"
        encoded_prompt = urllib.parse.quote(enhanced_prompt)
        # Free zero-key AI image generation (Stable Diffusion Turbo / FLUX free tier)
        pollinations_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=768&height=768&nologo=true&seed={timestamp + panel_number * 100}"
        
        logger.info(f"Requesting free AI illustration for Panel {panel_number}...")
        response = requests.get(pollinations_url, timeout=12)
        if response.status_code == 200 and len(response.content) > 5000:
            with open(output_path, "wb") as f:
                f.write(response.content)
            logger.info(f"Successfully retrieved and saved AI comic image to {output_path}")
            return f"/static/panels/{filename}"
        else:
            logger.warning(f"Free image service returned status {response.status_code}. Falling back to artistic canvas.")
    except Exception as e:
        logger.info(f"External image generation request bypassed/failed ({e}). Using artistic comic canvas.")

    # 3. Guaranteed High-Res Artistic Comic Canvas Fallback
    _generate_artistic_comic_canvas(prompt, panel_number, art_style, output_path)
    logger.info(f"Artistic comic panel saved to {output_path}")
    return f"/static/panels/{filename}"
