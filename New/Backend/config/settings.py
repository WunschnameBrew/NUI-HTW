# Backend/config/settings.py
import os
import pathlib

# --- CORE PATHS ---
# Current file is at Backend/config/settings.py
CONFIG_DIR = pathlib.Path(__file__).parent.resolve()
BACKEND_DIR = CONFIG_DIR.parent.resolve()
ROOT_DIR = BACKEND_DIR.parent.resolve()

DATA_DIR = ROOT_DIR / "data"
FRONTEND_DIR = ROOT_DIR / "Frontend"
MODELS_DIR = ROOT_DIR / "Llama_Models"
DB_PATH = DATA_DIR / "ai_hub.db"

# Ensure dirs exist
for p in [DATA_DIR, MODELS_DIR]:
    p.mkdir(parents=True, exist_ok=True)

# --- LLM SETTINGS ---
# Local Inference via llama-cpp-python
LLM_CONTEXT_SIZE = 8192

# Auto-detect Model
DEFAULT_MODEL = ""
candidates = list(MODELS_DIR.glob("*.gguf"))
if candidates:
    DEFAULT_MODEL = str(candidates[0])

# --- AUDIO TOOLS ---
# distil-small.en provides sub-300ms response time on CPU with great accuracy for English chat
WHISPER_MODEL = "Systran/faster-distil-whisper-small.en"

PIPER_DIR = ROOT_DIR / "Piper"
PIPER_VOICE = PIPER_DIR / "en_US-amy-medium.onnx"
