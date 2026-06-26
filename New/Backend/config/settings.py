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
LLM_API_URL = "http://127.0.0.1:8001/v1"
LLAMA_EXE = ROOT_DIR / "llamacpp" / "llama-server.exe"

# Auto-detect Model
DEFAULT_MODEL = ""
candidates = list(MODELS_DIR.glob("*.gguf"))
if candidates:
    DEFAULT_MODEL = str(candidates[0])

# --- AUDIO TOOLS ---
WHISPER_DIR = ROOT_DIR / "Whisper"
WHISPER_EXE = WHISPER_DIR / "whisper-server.exe"
WHISPER_MODEL = WHISPER_DIR / "models" / "ggml-medium-q5_0.bin"

PIPER_DIR = ROOT_DIR / "Piper"
PIPER_EXE = PIPER_DIR / "piper.exe"
PIPER_VOICE = PIPER_DIR / "en_US-amy-medium.onnx"
