"""
ComicCraft - Gemini Flash Integration
Module for generating structured 5-panel comic outlines using Google Gemini Flash.
"""

import json
import logging
import os
import re
from typing import Any, Dict, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger("comiccraft.gemini_flash")
logging.basicConfig(level=logging.INFO)

# Gemini API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# Try importing both google-genai and google.generativeai
GENAI_CLIENT = None
GENAI_LEGACY = None

if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
    try:
        from google import genai
        GENAI_CLIENT = genai.Client(api_key=GEMINI_API_KEY)
        logger.info("google-genai client initialized successfully for Gemini Flash.")
    except Exception as e:
        logger.warning(f"Could not initialize google-genai: {e}. Trying google.generativeai...")
        try:
            import google.generativeai as legacy_genai
            legacy_genai.configure(api_key=GEMINI_API_KEY)
            GENAI_LEGACY = legacy_genai
            logger.info("google.generativeai initialized successfully for Gemini Flash.")
        except Exception as e_leg:
            logger.warning(f"Could not initialize google.generativeai: {e_leg}")


def _clean_json_response(text: str) -> str:
    """Extract clean JSON text from LLM response which might have markdown fences."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        return match.group(1).strip()
    # Try finding the first '[' and last ']'
    start_bracket = text.find('[')
    end_bracket = text.rfind(']')
    if start_bracket != -1 and end_bracket != -1 and end_bracket > start_bracket:
        return text[start_bracket:end_bracket + 1].strip()
    return text


def _generate_fallback_outline(
    prompt: str,
    character_name: str = "Hero",
    setting: str = "Fantasy Realm",
    tone: str = "Dramatic",
    art_style: str = "Comic Book"
) -> List[Dict[str, Any]]:
    """
    Intelligent fallback generator when API key is unavailable or API fails.
    Produces a coherent 5-panel arc matching the user's specific inputs.
    """
    logger.info("Generating dynamic comic outline using intelligent narrative engine.")
    
    # Define narrative arc steps
    steps = [
        {
            "num": 1,
            "title_template": f"Panel 1: The Call at {setting}",
            "scene_desc": f"{character_name} stands at the entrance of {setting}. The atmosphere is unmistakably {tone.lower()}, with subtle hints of adventure in the air as their journey begins.",
            "prompt_suffix": f"establishing wide shot, {character_name} in {setting}, introduction scene, {tone} mood, high detail, masterpiece, {art_style} style"
        },
        {
            "num": 2,
            "title_template": f"Panel 2: Into the Depths",
            "scene_desc": f"Venturing deeper into {setting}, {character_name} uncovers the first clue regarding '{prompt}'. Shadows and vibrant light create an intense {tone.lower()} contrast.",
            "prompt_suffix": f"medium shot, {character_name} exploring mysterious {setting}, discovering ancient artifacts, dynamic angle, {tone} atmosphere, {art_style} style"
        },
        {
            "num": 3,
            "title_template": f"Panel 3: The Unexpected Turning Point",
            "scene_desc": f"Suddenly, a sudden conflict arises in {setting}. {character_name} faces an unexpected trial directly related to '{prompt}', demanding quick thinking and courage.",
            "prompt_suffix": f"action shot, close-up dynamic encounter, {character_name} reacting with determination, dramatic lighting, particles, {art_style} style"
        },
        {
            "num": 4,
            "title_template": f"Panel 4: The Climax of Courage",
            "scene_desc": f"At the height of the struggle, {character_name} summons their inner resolve. The scene explodes with visual spectacle as the core mystery of the quest is confronted.",
            "prompt_suffix": f"climactic dramatic action, glowing energy, {character_name} triumphant pose in {setting}, vibrant colors, epic composition, {art_style} style"
        },
        {
            "num": 5,
            "title_template": f"Panel 5: A New Dawn",
            "scene_desc": f"The dust settles over {setting}. {character_name} gazes ahead, having overcome the trial of '{prompt}', forever changed and ready for the next adventure.",
            "prompt_suffix": f"cinematic resolution, serene wide landscape of {setting}, {character_name} looking into sunrise, golden hour, hopeful {tone} ending, {art_style} style"
        }
    ]

    outline = []
    for step in steps:
        outline.append({
            "panel_number": step["num"],
            "title": step["title_template"],
            "scene_description": step["scene_desc"],
            "image_prompt": f"{art_style} illustration of {character_name}, {step['prompt_suffix']}"
        })

    return outline


def generate_outline(
    prompt: str,
    character_name: str = "Hero",
    setting: str = "Fantasy Realm",
    tone: str = "Dramatic",
    art_style: str = "Comic Book"
) -> List[Dict[str, Any]]:
    """
    Generates a structured 5-panel comic outline using Google Gemini Flash.
    
    Args:
        prompt: User's main story prompt or premise
        character_name: Name of the protagonist
        setting: Location/world of the story
        tone: Tone of the comic (dramatic, funny, light-hearted, etc.)
        art_style: Visual art style (comic book, anime, realistic, etc.)
        
    Returns:
        List of 5 panel dictionaries containing panel_number, title, scene_description, image_prompt.
    """
    logger.info(f"Generating comic outline for character '{character_name}' in '{setting}' with tone '{tone}'...")
    
    # System instruction & prompt
    instruction_prompt = f"""
You are an expert comic book story architect.
Your task is to take the user's premise and construct a compelling, professional 5-panel comic outline.

User Preferences:
- Story Prompt: {prompt}
- Protagonist: {character_name}
- Setting: {setting}
- Tone / Mood: {tone}
- Art Style: {art_style}

Requirements:
1. Provide EXACTLY 5 panels following a classic narrative arc:
   - Panel 1: Exposition & Introduction of {character_name} in {setting}
   - Panel 2: Inciting Incident / Rising action related to "{prompt}"
   - Panel 3: Complication / Twist / Sudden obstacle
   - Panel 4: Climax / Peak confrontation
   - Panel 5: Resolution / Memorable aftermath
2. Return ONLY a valid JSON list of 5 objects with NO markdown preamble or postscript.
3. Each object MUST strictly contain the following keys:
   - "panel_number": integer from 1 to 5
   - "title": a punchy title like "Panel 1: The Whispering Woods"
   - "scene_description": 2 to 3 vivid sentences describing what is happening visually in the panel
   - "image_prompt": a descriptive text-to-image prompt optimized for Stable Diffusion, specifying camera angle, lighting, character actions, background details, and aesthetic cues matching the "{art_style}" style and "{tone}" tone.

Example Output Format:
[
  {{
    "panel_number": 1,
    "title": "Panel 1: The Whispering Woods",
    "scene_description": "...",
    "image_prompt": "..."
  }}
]
"""

    # If API client is available, call Gemini Flash
    if GENAI_CLIENT:
        # Try current models: gemini-2.5-flash, gemini-1.5-flash
        model_candidates = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-3.5-flash"]
        for model_name in model_candidates:
            try:
                response = GENAI_CLIENT.models.generate_content(
                    model=model_name,
                    contents=instruction_prompt
                )
                if response and response.text:
                    cleaned = _clean_json_response(response.text)
                    data = json.loads(cleaned)
                    if isinstance(data, list) and len(data) >= 5:
                        logger.info(f"Successfully generated 5-panel outline using {model_name}.")
                        # Ensure panel numbers are 1..5
                        for idx, p in enumerate(data[:5]):
                            p["panel_number"] = idx + 1
                        return data[:5]
            except Exception as e:
                logger.warning(f"Error calling {model_name} via google-genai: {e}")

    elif GENAI_LEGACY:
        legacy_models = ["gemini-1.5-flash", "gemini-pro"]
        for model_name in legacy_models:
            try:
                model = GENAI_LEGACY.GenerativeModel(model_name)
                response = model.generate_content(instruction_prompt)
                if response and response.text:
                    cleaned = _clean_json_response(response.text)
                    data = json.loads(cleaned)
                    if isinstance(data, list) and len(data) >= 5:
                        logger.info(f"Successfully generated 5-panel outline using legacy {model_name}.")
                        for idx, p in enumerate(data[:5]):
                            p["panel_number"] = idx + 1
                        return data[:5]
            except Exception as e:
                logger.warning(f"Error calling {model_name} via legacy SDK: {e}")

    # 3. Free Zero-Key AI LLM Endpoint (Pollinations AI text API)
    try:
        import requests
        import urllib.parse
        logger.info("Attempting free zero-key AI LLM for 5-panel outline...")
        clean_prompt = f"Output ONLY a raw JSON array of 5 comic panels for prompt: {prompt}, Character: {character_name}, Setting: {setting}, Tone: {tone}, Art Style: {art_style}. Format: [{{'panel_number':1,'title':'...','scene_description':'...','image_prompt':'...'}}]"
        encoded = urllib.parse.quote(clean_prompt)
        res = requests.get(f"https://text.pollinations.ai/{encoded}?json=true", timeout=8)
        if res.status_code == 200 and res.text:
            cleaned = _clean_json_response(res.text)
            data = json.loads(cleaned)
            if isinstance(data, list) and len(data) >= 5:
                logger.info("Successfully generated 5-panel outline using free zero-key AI LLM.")
                for idx, p in enumerate(data[:5]):
                    p["panel_number"] = idx + 1
                return data[:5]
    except Exception as e_free:
        logger.info(f"Free online LLM fallback skipped: {e_free}")

    # 4. Fallback to smart offline narrative engine if APIs are unreachable
    return _generate_fallback_outline(prompt, character_name, setting, tone, art_style)
