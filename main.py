"""
The Pitch Visualizer — From Words to Storyboard
=================================================
FastAPI backend that transforms narrative text into visual storyboards
using Groq LLM for prompt engineering and Pollinations.ai for image generation.
"""

import json
import os
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from groq import Groq
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
load_dotenv()

app = FastAPI(
    title="The Pitch Visualizer",
    description="Transform narrative text into AI-generated visual storyboards",
    version="1.0.0",
)

templates = Jinja2Templates(directory="templates")

# Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# LLM model to use
LLM_MODEL = "llama-3.1-70b-versatile"

# Pollinations.ai settings
POLLINATIONS_BASE = "https://image.pollinations.ai/prompt"
IMAGE_WIDTH = 1024
IMAGE_HEIGHT = 1024

# Thread pool for parallel image generation
MAX_WORKERS = 5

# ---------------------------------------------------------------------------
# Style Mappings — appended to every image prompt for visual consistency
# ---------------------------------------------------------------------------
STYLE_SUFFIXES = {
    "Cinematic": "cinematic film still, 35mm photography, dramatic lighting, shallow depth of field, anamorphic lens flare",
    "Watercolor": "watercolor painting, soft washes, artistic brushstrokes, paper texture, delicate color blending",
    "3D Render": "3D render, octane render, volumetric lighting, studio lighting, high detail, subsurface scattering",
    "Cyberpunk": "cyberpunk aesthetic, neon lights, rainy night city, holographic elements, futuristic technology, purple and cyan tones",
    "Anime": "anime style, studio ghibli inspired, vibrant colors, detailed background, cel shading, soft ambient lighting",
    "Oil Painting": "oil painting on canvas, classical art style, rich textures, museum quality, impasto technique, warm tones",
}

# ---------------------------------------------------------------------------
# System Prompt — instructs the LLM to act as a Storyboard Director
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a professional Storyboard Director and Visual Prompt Engineer working for a top-tier creative agency.

Your task is to take a narrative paragraph and a target visual style, then:
1. Segment the narrative into 3 to 5 distinct scenes or key moments.
2. For each scene, write a highly detailed, visually descriptive image generation prompt.

STRICT RULES:
- Each enhanced prompt MUST include: specific subject description, clear action/pose, detailed setting/environment, lighting direction and quality, emotional mood, and camera composition/angle.
- NEVER use abstract, conceptual, or metaphorical language in prompts — be concrete, specific, and visual.
- Maintain character appearance consistency across all scenes (same clothing, hair, features).
- Maintain setting consistency where appropriate (same office, same city, etc.).
- Each prompt should be 2-3 sentences long, packed with visual detail.
- Do NOT include any text, watermarks, or logos in the image descriptions.
- Do NOT include the style suffix — it will be appended automatically.

You MUST return ONLY a valid JSON object with this exact structure (no markdown, no explanation, no extra text):
{
  "scenes": [
    {
      "scene_number": 1,
      "original_text_segment": "The exact portion of the original text this scene covers",
      "enhanced_image_prompt": "Your detailed, visually rich prompt for image generation"
    }
  ]
}"""


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------
class GenerateRequest(BaseModel):
    text: str
    style: str


class SceneResponse(BaseModel):
    scene_number: int
    original_text_segment: str
    enhanced_image_prompt: str
    image_url: str


# ---------------------------------------------------------------------------
# Core Functions
# ---------------------------------------------------------------------------
def segment_and_engineer_prompts(text: str, style: str) -> list[dict]:
    """
    Call Groq LLM to segment narrative text into scenes and generate
    enhanced image prompts for each scene.
    """
    user_message = f"""Narrative Text:
\"\"\"{text}\"\"\"

Visual Style: {style}

Segment this narrative into 3-5 key scenes and generate enhanced image prompts for each. 
Remember to be extremely visual and specific in your prompts. Return valid JSON only."""

    response = groq_client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.7,
        max_tokens=2048,
        response_format={"type": "json_object"},
    )

    result = json.loads(response.choices[0].message.content)
    return result.get("scenes", [])


def build_image_url(prompt: str, style: str) -> str:
    """
    Construct a Pollinations.ai image URL from an enhanced prompt + style suffix.
    """
    style_suffix = STYLE_SUFFIXES.get(style, "")
    full_prompt = f"{prompt}, {style_suffix}" if style_suffix else prompt

    encoded_prompt = urllib.parse.quote(full_prompt)
    return (
        f"{POLLINATIONS_BASE}/{encoded_prompt}"
        f"?width={IMAGE_WIDTH}&height={IMAGE_HEIGHT}&nologo=true"
    )


def prewarm_image(url: str) -> str:
    """
    Fire a GET request to Pollinations.ai to trigger image generation.
    Returns the URL once the image is ready (or on timeout).
    """
    try:
        requests.get(url, timeout=120)
    except requests.exceptions.Timeout:
        pass  # URL will still work — browser will load it
    except requests.exceptions.RequestException:
        pass  # Graceful fallback — return URL anyway
    return url


def generate_images_parallel(scenes: list[dict], style: str) -> list[dict]:
    """
    Build image URLs for all scenes and pre-warm them in parallel
    using ThreadPoolExecutor.
    """
    # Build URLs for each scene
    for scene in scenes:
        scene["image_url"] = build_image_url(scene["enhanced_image_prompt"], style)

    # Pre-warm all URLs in parallel (triggers Pollinations generation)
    urls = [scene["image_url"] for scene in scenes]

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(prewarm_image, url): url for url in urls}
        for future in as_completed(futures):
            future.result()  # Wait for all to complete

    return scenes


# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main storyboard UI."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/generate")
async def generate_storyboard(req: GenerateRequest):
    """
    Main endpoint: takes narrative text + style, returns a storyboard
    with segmented scenes, enhanced prompts, and generated image URLs.
    """
    # Validate input
    if not req.text or len(req.text.strip()) < 20:
        return JSONResponse(
            status_code=400,
            content={"error": "Please provide at least 20 characters of narrative text."},
        )

    if req.style not in STYLE_SUFFIXES:
        return JSONResponse(
            status_code=400,
            content={"error": f"Invalid style. Choose from: {', '.join(STYLE_SUFFIXES.keys())}"},
        )

    try:
        # Step 1: LLM reasoning — segment and engineer prompts
        scenes = segment_and_engineer_prompts(req.text, req.style)

        if not scenes:
            return JSONResponse(
                status_code=500,
                content={"error": "The LLM failed to segment the narrative. Please try again."},
            )

        # Step 2: Parallel image generation via Pollinations.ai
        scenes_with_images = generate_images_parallel(scenes, req.style)

        return {"scenes": scenes_with_images}

    except json.JSONDecodeError:
        return JSONResponse(
            status_code=500,
            content={"error": "The LLM returned invalid JSON. Please try again."},
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"An unexpected error occurred: {str(e)}"},
        )


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "The Pitch Visualizer"}
