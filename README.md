# 🎬 The Pitch Visualizer — From Words to Storyboard

Transform narrative text into a visually compelling, AI-generated storyboard in one click.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green?logo=fastapi)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 🌟 What It Does

Paste a customer success story (3-5 sentences), choose a visual style, and instantly receive a multi-panel storyboard with AI-generated images. The app:

1. **Segments** your narrative into 3-5 key scenes using an LLM
2. **Engineers** rich, visually descriptive prompts for each scene
3. **Generates** images in parallel using AI
4. **Displays** them as a beautiful sequential storyboard

## 🏗️ Architecture

```
User Input (text + style)
        │
        ▼
┌─────────────────────┐
│   Groq LLM API      │  ← Narrative segmentation + prompt engineering
│  (llama-3.1-70b)    │
└─────────┬───────────┘
          │ JSON array of scenes
          ▼
┌─────────────────────┐
│  ThreadPoolExecutor  │  ← Parallel image generation
│   (5 workers)       │
└─────────┬───────────┘
          │ Concurrent requests
          ▼
┌─────────────────────┐
│  Pollinations.ai    │  ← Free AI image generation (Flux model)
│  (No API key needed)│
└─────────┬───────────┘
          │ Image URLs
          ▼
┌─────────────────────┐
│  Storyboard UI      │  ← Beautiful HTML storyboard
│  (Jinja2 + JS)      │
└─────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- A free [Groq API key](https://console.groq.com/keys)

### Setup

```bash
# Clone the repository
git clone https://github.com/Yashraj0906/Pitch_Visualizer.git
cd Pitch_Visualizer

# Create virtual environment and install dependencies
uv venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # macOS/Linux

uv pip install -r requirements.txt

# Configure your API key
copy .env.example .env
# Edit .env and paste your GROQ_API_KEY
```

### Run

```bash
uvicorn main:app --reload
```

Open your browser at **http://127.0.0.1:8000** 🎉

## 🎨 Visual Styles

Choose from 6 curated art styles for visual consistency:

| Style | Description |
|-------|------------|
| 🎬 Cinematic | Film still, 35mm, dramatic lighting |
| 🎨 Watercolor | Soft washes, brushstrokes, paper texture |
| 🧊 3D Render | Octane render, volumetric lighting |
| 🌆 Cyberpunk | Neon lights, futuristic, holographic |
| 🌸 Anime | Studio Ghibli inspired, vibrant |
| 🖼️ Oil Painting | Classical art, rich canvas textures |

## 🔧 Tech Stack

| Component | Technology | Cost |
|-----------|-----------|------|
| Backend | FastAPI + Uvicorn | Free |
| LLM Reasoning | Groq API (llama-3.1-70b-versatile) | Free tier |
| Image Generation | Pollinations.ai (Flux model) | Free, no key |
| Frontend | Jinja2 + Vanilla JS + CSS | Free |
| Concurrency | Python ThreadPoolExecutor | Built-in |

## 📁 Project Structure

```
Pitch_Visualizer/
├── main.py              # FastAPI backend (routing, LLM, image gen)
├── requirements.txt     # Python dependencies
├── .env.example         # API key template
├── .gitignore           # Git ignore rules
├── README.md            # This file
└── templates/
    └── index.html       # Storyboard UI
```

## 🧠 Design Decisions

### Prompt Engineering
The Groq LLM acts as a **Storyboard Director** — it doesn't just split sentences, it understands the narrative arc and generates prompts with specific visual elements: subject, action, setting, lighting, mood, and composition.

### Visual Consistency
A **style suffix** (e.g., "cinematic film still, 35mm photography, dramatic lighting") is appended to every single prompt. This ensures all panels share a cohesive artistic style.

### Parallel Generation
Using `ThreadPoolExecutor` with 5 workers, all images generate simultaneously. A 4-panel storyboard takes ~10-15 seconds instead of ~60+ seconds sequentially.

## 📝 License

MIT License — feel free to use, modify, and distribute.
