# 🚀 Koa-AI (3D VRM Voice & Text Assistant)

Koa-AI is a real-time, 3D interactive AI avatar assistant featuring local LLM inference (`llama-cpp-python`), speech-to-text (`faster-whisper`), text-to-speech (`piper-tts`), continuous emotion analysis, VRM 3D model rendering, and dynamic body animation blending.

---

## 🛠️ Step-by-Step Setup & Running Guide

Follow these steps in order to get the project set up and running on your machine:

### Step 1: Prerequisites
- **Python 3.10 to 3.12** installed on your system.
- An internet connection for downloading initial dependencies and model weights.

---

### Step 2: Run Automatic Environment Setup
Open a terminal in the `New` folder (or double-click `setup.bat` on Windows) and run:

```bash
python setup_environment.py
```

This script will automatically:
1. Install all core Python dependencies (`fastapi`, `uvicorn`, `faster-whisper`, `piper-tts`, `llama-cpp-python`, etc.).
2. Prompt you to select your hardware acceleration (CPU, CUDA, Vulkan, or Metal).
3. Create the `Llama_Models` and `Piper` directories.
4. Auto-download the default GGUF LLM (`Dolphin3.0-Llama3.2-3B.Q4_K_S.gguf`) from HuggingFace.
5. Auto-download the default Piper TTS Voice (`en_US-amy-medium.onnx`).

---

### Step 3: (Optional) Convert Custom FBX Animations to VRMA
If you want to add new body animations for the avatar:

1. Drop your raw `.fbx` animation files into:
   `Frontend/static/assets/animations/raw_fbx/`
2. Run the VRMA converter utility:
   ```bash
   python convert_vrma.py -i Frontend/static/assets/animations/raw_fbx -o Frontend/static/assets/animations/converted_gltf
   ```
3. Register the converted `.vrma` files under their emotional category in:
   `Frontend/static/assets/animations/index.md`

---

### Step 4: Start the Application Server
Run the FastAPI backend server:

**On Windows:**
Double-click `start_backend.bat` or run:
```bash
python -m uvicorn Backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**On Linux / macOS:**
```bash
python3 -m uvicorn Backend.main:app --host 0.0.0.0 --port 8000 --reload
```

---

### Step 5: Launch the Interface
Open your web browser and navigate to:
👉 **`http://localhost:8000`**

- **Talk to Koa:** Click the microphone button to start voice recording. Clicking it again or hitting the **Stop** button will instantly interrupt audio output and cancel LLM generation.
- **Type to Koa:** Click the message icon to bring up the text input bar.
- **Change Personality:** Open the Settings drawer (cog icon) to switch between personas (e.g. `Concise` for punchy 1-2 sentence replies).
- **Persistent Memory:** Past conversation context is automatically saved to SQLite (`data/ai_hub.db`) and retrieved on subsequent messages.

---

## 📁 Project Structure

```
New/
├── Backend/               # FastAPI backend & services
│   ├── api/routes.py      # Main API endpoints (streaming chat, voice, memory)
│   ├── config/settings.py # System paths & configuration
│   └── services/          # Core modules (audio, llm, memory, emotion, animation)
├── Frontend/              # Web application interface
│   ├── index.html         # Single-page UI with 3D canvas
│   └── static/            # CSS styles, JS modules, 3D VRM assets, & animations
├── Persona/               # System prompt personas (Default_Sys.txt, Concise_Sys.txt)
├── Llama_Models/          # GGUF LLM weights (ignored by git)
├── Piper/                 # Piper ONNX voice models (ignored by git)
├── data/                  # SQLite database (ai_hub.db) (ignored by git)
├── setup_environment.py   # Automated setup script
├── convert_vrma.py        # FBX to VRMA conversion pipeline
└── README.md              # Setup & usage instructions
```
