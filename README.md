# 🎬 The Pitch Visualizer

The Pitch Visualizer is an AI-powered tool designed to transform text narratives—like customer success stories, game concepts, or movie pitches—into stunning, professional visual storyboards in seconds. 

It combines high-speed LLM reasoning with free open-source diffusion models to generate high-quality images without relying on expensive, proprietary API keys.

---

## 🚀 Architecture & Flow

```mermaid
graph TD
    A[User Inputs Story] -->|Browser UI| B(FastAPI Backend)
    
    subgraph 1. Prompt Engineering
        B -->|Sends Story| C{Llama 3 / Groq}
        C -->|Returns 4 Prompts| B
    end
    
    subgraph 2. Image Generation
        B -->|Sends Prompts| D{Flux / Pollinations.ai}
        D -->|Returns 4 Images| B
    end
    
    B -->|Sends Images & Text| E[Glassmorphism Storyboard UI]
    
    style A fill:#4F46E5,stroke:#3730A3,color:#fff
    style B fill:#3B82F6,stroke:#2563EB,color:#fff
    style C fill:#10B981,stroke:#059669,color:#fff
    style D fill:#EC4899,stroke:#DB2777,color:#fff
    style E fill:#8B5CF6,stroke:#7C3AED,color:#fff
```

### 🧠 The Flow in Plain English:
1. **You Type a Story:** You paste a short story into the website and click "Generate".
2. **The AI Reads It:** The website sends your story to our Python backend, which forwards it to an advanced text-AI (Groq's Llama 3). 
3. **Writing the Script:** The text-AI acts like a movie director. It chops your story into 4 scenes and writes a highly descriptive, short visual prompt for each scene (like *"Cinematic shot of a hacker at a computer"*).
4. **Drawing the Pictures:** Now that we have 4 visual prompts, our backend sends them to an Image-AI (Pollinations' Flux model). 
5. **The Final Output:** The Image-AI draws the 4 images and sends them back to the website to be displayed inside our stunning glass-themed interface!

## ✨ "Wow-Factor" Features

*   **▶️ Presentation Mode:** A built-in immersive pitch deck mode. When clicked, the screen darkens, the images slowly zoom (Ken Burns effect), and the browser natively narrates the story out loud using the Web Speech API.
*   **📥 PDF Export:** Instantly packages the generated storyboard and textual prompts into a clean, professional A4 PDF Pitch Deck using `html2pdf.js`.
*   **🔁 Advanced Error Handling:** The FastAPI backend proxy handles image rendering transparently. Rate limited? It uses exponential backoff to automatically retry image generation to ensure success.

## 🛠️ Design Choices & Prompt Engineering Methodology

Our architecture relies on an advanced two-step pipeline that separates **reasoning** from **generation**:

1. **System Prompting (The Director Role):** 
   We assigned the Groq Llama-3 LLM a highly specific system prompt: `You are an expert cinematic storyboard director.` This forces the LLM to think visually rather than theoretically.
2. **Strict Output Constraints (Token Optimization):** 
   Diffusion models like Flux begin to hallucinate or ignore keywords if a prompt exceeds 75 tokens. Therefore, our prompt engineering strictly instructs the LLM to output scene descriptions in under 15 words.
3. **Keyword Injection:** 
   The user selects a style (e.g., "Cinematic"). The LLM is instructed to append this exact style keyword alongside rendering parameters (like `highly detailed, 8k, masterpiece`) directly into the image prompt, ensuring the diffusion model has strong contextual anchors for every scene without the user needing to be a prompt engineer.

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
