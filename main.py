"""
The Pitch Visualizer — From Words to Storyboard
=================================================
FastAPI backend that transforms narrative text into visual storyboards
using Groq LLM for prompt engineering and Pollinations.ai for image generation.
"""

import json
import os
import random
import urllib.parse
import uuid

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
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
LLM_MODEL = "llama-3.1-8b-instant"

# Pollinations.ai settings
POLLINATIONS_BASE = "https://image.pollinations.ai/prompt"
IMAGE_WIDTH = 1024
IMAGE_HEIGHT = 1024

# In-memory store for generated scenes (session_id -> scenes list)
scene_store: dict[str, list[dict]] = {}

# ---------------------------------------------------------------------------
# Style Mappings — appended to every image prompt for visual consistency
# ---------------------------------------------------------------------------
STYLE_SUFFIXES = {
    "Cinematic": "cinematic film still, dramatic lighting, shallow depth of field, movie color grading",
    "Oil Painting": "oil painting on canvas, classical fine art, rich impasto textures, warm golden tones",
    "Vivid": "ultra vivid colors, high saturation, HDR, punchy contrast, sharp focus",
    "Black and White": "black and white photography, high contrast monochrome, dramatic shadows, film noir",
    "Anime": "anime style illustration, vibrant cel shading, detailed background, expressive characters",
}

# ---------------------------------------------------------------------------
# System Prompt — instructs the LLM to act as a Storyboard Director
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a Storyboard Director. Break a narrative into 3-5 scenes.

For each scene produce:
1. scene_description: One short vivid sentence (used as caption)
2. enhanced_image_prompt: A SHORT image prompt (MAX 15 words). Be concrete and visual. Example: "Woman in blue suit presenting charts to boardroom executives, golden hour light"

CRITICAL RULES:
- Prompts MUST be under 15 words. Shorter is better.
- Lead with subject, then action, then setting
- NO abstract concepts, NO metaphors, NO emotions as words
- Keep character appearance consistent across scenes
- NO text/logos/watermarks in prompts
- Do NOT add art style — it gets added automatically

Return ONLY valid JSON:
{
  "scenes": [
    {
      "scene_number": 1,
      "scene_description": "Caption sentence here",
      "enhanced_image_prompt": "Short concrete visual prompt here"
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
    scene_description: str
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
    user_message = f"""Narrative:
\"\"\"{text}\"\"\"

Style: {style}

Break into 3-5 scenes. Keep enhanced_image_prompt UNDER 15 words each. JSON only."""

    response = groq_client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.6,
        max_tokens=1024,
        response_format={"type": "json_object"},
    )

    result = json.loads(response.choices[0].message.content)
    return result.get("scenes", [])


# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main storyboard UI."""
    return templates.TemplateResponse(request, "index.html")


@app.post("/generate")
async def generate_storyboard(req: GenerateRequest):
    """
    Main endpoint: takes narrative text + style, returns a storyboard
    with segmented scenes, enhanced prompts, and image URLs served via proxy.
    """
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

        # Step 2: Generate a session ID and store scenes
        session_id = str(uuid.uuid4())[:8]
        
        # Build full prompts with style suffix and store them
        style_suffix = STYLE_SUFFIXES.get(req.style, "")
        for i, scene in enumerate(scenes):
            prompt = scene["enhanced_image_prompt"]
            full_prompt = f"{prompt}, {style_suffix}" if style_suffix else prompt
            scene["_full_prompt"] = full_prompt
            # Image URL points to our own proxy endpoint
            scene["image_url"] = f"/image/{session_id}/{i}"
        
        scene_store[session_id] = scenes
        
        # Clean up old sessions (keep max 20)
        if len(scene_store) > 20:
            oldest_key = next(iter(scene_store))
            del scene_store[oldest_key]

        return {"scenes": scenes}

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


@app.get("/image/{session_id}/{scene_index}")
async def proxy_image(session_id: str, scene_index: int):
    """
    Proxy endpoint that fetches images from Pollinations.ai on behalf of the browser.
    Retries up to 3 times with different seeds if Pollinations fails.
    """
    import time as _time
    
    # Look up the scene
    scenes = scene_store.get(session_id)
    if not scenes or scene_index >= len(scenes):
        return JSONResponse(status_code=404, content={"error": "Scene not found"})
    
    scene = scenes[scene_index]
    full_prompt = scene.get("_full_prompt", scene["enhanced_image_prompt"])
    encoded_prompt = urllib.parse.quote(full_prompt)
    
    MAX_RETRIES = 3
    RETRY_DELAYS = [0, 2, 5]  # seconds to wait before each attempt
    last_error = None
    
    for attempt in range(MAX_RETRIES):
        if RETRY_DELAYS[attempt] > 0:
            _time.sleep(RETRY_DELAYS[attempt])
        
        seed = random.randint(1, 999999)
        pollinations_url = (
            f"{POLLINATIONS_BASE}/{encoded_prompt}"
            f"?width={IMAGE_WIDTH}&height={IMAGE_HEIGHT}&nologo=true&seed={seed}"
        )
        
        try:
            resp = requests.get(pollinations_url, timeout=120)
            
            # Check if we got actual image data back
            content_type = resp.headers.get("content-type", "")
            if resp.status_code == 200 and "image" in content_type:
                return Response(
                    content=resp.content,
                    media_type=content_type,
                    headers={"Cache-Control": "public, max-age=3600"},
                )
            
            # Not an image — treat as error, retry
            last_error = f"Status {resp.status_code}, type: {content_type}"
            
        except requests.exceptions.RequestException as e:
            last_error = str(e)
    
    # All retries exhausted
    return JSONResponse(
        status_code=502,
        content={"error": f"Image generation failed after {MAX_RETRIES} attempts: {last_error}"}
    )


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "The Pitch Visualizer"}
