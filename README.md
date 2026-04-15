# 🎬 The Pitch Visualizer

The Pitch Visualizer is an AI-powered tool designed to transform text narratives—like customer success stories, game concepts, or movie pitches—into stunning, professional visual storyboards in seconds. 

Built for speed and flexibility, it combines high-speed LLM reasoning with open-source diffusion models to generate consistent, high-quality images without relying on expensive, proprietary API keys.

## 🚀 The Full Flow (How it Works)

The architecture is split into a robust backend proxy and a highly interactive frontend:

1. **User Input:** The user pastes a narrative into the UI and selects an artistic style (e.g., Cinematic, Anime, Vivid).
2. **LLM Prompt Engineering (Groq):** The backend intercepts the text and sends it to the **Groq API (Llama 3)**. The LLM acts as an expert Director, segmenting the story into 4 distinct scenes. For each scene, it authors a highly optimized, strictly limited (under 15 words) visual prompt.
3. **Backend Proxy & Retry Logic:** To avoid browser-based URL length errors and CORS issues, the FastAPI backend acts as a proxy. It fetches the images server-side. If the free image endpoint is under heavy traffic (returning a 502/429), the backend automatically implements a 3-attempt exponential backoff retry mechanism.
4. **Image Generation (Pollinations.ai):** The backend requests the images from **Pollinations.ai**, a powerful proxy that hooks directly into open-source diffusion models like **Flux** and **Stable Diffusion**. This provides DALL-E level quality at zero cost.
5. **Frontend Rendering:** The browser simultaneously downloads the images, presenting them in a beautiful Glassmorphism UI with premium skeleton-loading "shimmer" animations.

## ✨ "Wow-Factor" Features

*   **▶️ Presentation Mode:** A built-in immersive pitch deck mode. When clicked, the screen darkens, the images slowly zoom (Ken Burns effect), and the browser natively narrates the story out loud using the Web Speech API.
*   **📥 PDF Export:** Instantly packages the generated storyboard and textual prompts into a clean, professional A4 PDF Pitch Deck using `html2pdf.js`.
*   **🔁 Advanced Error Handling:** The UI includes manual retry buttons for individual failed frames, while the backend transparently handles standard rate limits.

## 🛠️ Tech Stack

*   **Frontend:** Vanilla JS, HTML5, CSS3 (Glassmorphism, CSS Grid, Custom Animations).
*   **Backend:** Python, FastAPI, Uvicorn.
*   **LLM Provider:** Groq (`llama-3.1-8b-instant`).
*   **Image Generation:** Pollinations.ai (Flux/Stable Diffusion).
*   **Package Management:** `uv`.

## 💻 Running Locally

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Yashraj0906/Pitch_Visualizer.git
   cd Pitch_Visualizer
   ```

2. **Set up your environment variables:**
   Create a `.env` file in the root directory and add your free Groq API key:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```

3. **Install dependencies and run the server:**
   Using `uv` (the blazing fast Python package manager):
   ```bash
   uv run uvicorn main:app --reload
   ```

4. **Open the app:**
   Navigate to `http://127.0.0.1:8000` in your web browser.
