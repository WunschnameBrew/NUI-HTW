# Koa-AI

Koa-AI is a local AI avatar application. It serves a browser-based 3D VRM avatar, sends chat messages to a local llama.cpp server, supports optional speech-to-text through Whisper, streams text-to-speech through Piper, and can store conversations in SQLite.

The project is designed to run locally. No hosted AI API is required when llama.cpp, Whisper, and Piper are available on the machine.

## Table of Contents

- [Features](#features)
- [Project Status](#project-status)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Quick Start](#quick-start)
- [Local Assets and Models](#local-assets-and-models)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Avatar Models and Animations](#avatar-models-and-animations)
- [Memory](#memory)
- [Privacy and Data Handling](#privacy-and-data-handling)
- [Known Limitations](#known-limitations)
- [Troubleshooting](#troubleshooting)
- [Third-Party Libraries and Tools](#third-party-libraries-and-tools)
- [Documentation TODOs](#documentation-todos)
- [Development Notes](#development-notes)

## Features

- Local LLM chat through an OpenAI-compatible llama.cpp endpoint
- Streaming assistant responses in the frontend
- Optional voice input through Whisper
- Optional text-to-speech output through Piper
- Interactive Three.js scene with a VRM avatar
- Runtime avatar model selection from local `.vrm` files
- Persona selection from local system prompt files
- Optional SQLite conversation memory
- Settings panel for memory, persona, model selection, and chat clearing

## Project Status

This project is a local prototype/demo for an AI avatar interface. Text chat, avatar rendering, persona selection, and local memory are implemented. Voice input and voice output are supported by the backend, but depend on local Whisper and Piper installations.

### Tested Environment

| Component        | Version / Details                                                                      |
|------------------|----------------------------------------------------------------------------------------|
| Operating system | Windows 11, Linux, macOS                                                               |
| Python           | 3.13                                                                                   |
| Browser          | <span style="color:red">TODO: Add the tested browser and version.</span>               |
| llama.cpp        | <span style="color:red">TODO: Add the tested llama.cpp build or commit/version.</span> |
| Whisper          | <span style="color:red">TODO: Add the tested Whisper server version and model.</span>  |
| Piper            | <span style="color:red">TODO: Add the tested Piper version and voice model.</span>     |

### Demo Scenario

<p>
  <strong><span style="color:red">TODO</span></strong><br>
  <span style="color:red">Add a short step-by-step demo flow, for example: start the local LLM, open the app, select a persona/avatar, send a text prompt, record a voice message, and clear the conversation history.</span>
</p>

Suggested structure:

1. Start the local llama.cpp server.
2. Start the FastAPI backend.
3. Open `http://127.0.0.1:8000`.
4. Select a persona and avatar model in the settings panel.
5. Send a text message or record a voice message.
6. Observe the streamed assistant response, voice output, and avatar animation.

### Screenshots / Demo Media

<p>
  <strong><span style="color:red">TODO</span></strong><br>
  <span style="color:red">Add screenshots or a GIF of the current UI. Recommended assets: main avatar view, settings panel, active conversation, and optional voice interaction demo.</span>
</p>

Suggested media placeholders:

```md
![Main avatar view](docs/screenshots/main-avatar-view.png)
![Settings panel](docs/screenshots/settings-panel.png)
![Conversation view](docs/screenshots/conversation-view.png)
```

## Architecture

```text
Browser
  |
  | serves UI + static assets
  v
FastAPI backend (port 8000)
  |-- /chat and /chat_voice_stream -> llama.cpp server (port 8001)
  |-- /transcribe                 -> Whisper server (port 8003)
  |-- Piper subprocess            -> streamed voice output
  |-- SQLite                      -> optional chat memory
```

The backend serves both the API and the frontend. The frontend uses CDN-hosted Three.js/VRM libraries and local avatar assets.

## Project Structure

```text
.
|-- README.md
|-- New/
|   |-- Backend/
|   |   |-- main.py                 # FastAPI app and static file mounting
|   |   |-- api/
|   |   |   `-- routes.py           # Chat, voice, metadata, history endpoints
|   |   |-- config/
|   |   |   `-- settings.py         # Paths, ports, model/tool locations
|   |   `-- services/
|   |       |-- animation.py         # Available VRMA animations
|   |       |-- audio.py             # Whisper transcription and Piper TTS
|   |       |-- llm.py               # llama.cpp streaming client
|   |       `-- memory.py            # SQLite conversation storage
|   |-- Frontend/
|   |   |-- index.html              # Browser UI
|   |   `-- static/
|   |       |-- css/
|   |       |-- js/
|   |       `-- assets/             # VRM models and animation files
|   |-- start_backend.bat           # Windows backend launcher
|   |-- start_llama.bat             # Windows llama.cpp launcher
|   `-- start_llama.sh              # macOS/Linux llama.cpp launcher
|-- Legacy.zip
`-- New.zip
```

## Requirements

Minimum requirements for text chat:

- Python 3.10 or newer
- A GGUF language model
- `llama-server` from llama.cpp
- A modern browser

Additional requirements for voice features:

- Whisper server executable and model file
- Piper executable and voice model
- Browser microphone permission

Python packages:

```bash
pip install fastapi uvicorn openai httpx python-multipart
```

Frontend libraries are currently loaded through CDNs:

- Three.js
- fflate
- GLTFLoader, FBXLoader, and OrbitControls
- `@pixiv/three-vrm`
- `@pixiv/three-vrm-animation`

### Dependency File

<p>
  <strong><span style="color:red">TODO</span></strong><br>
  <span style="color:red">Create <code>New/requirements.txt</code> with all Python dependencies and replace the inline <code>pip install ...</code> command above with <code>pip install -r requirements.txt</code>.</span>
</p>

### External Tool Setup

| Tool | Setup notes |
|---|---|
| Python | <span style="color:red">TODO: Add supported Python versions and installation notes.</span> |
| llama.cpp | <span style="color:red">TODO: Add download/build instructions for <code>llama-server</code> and explain where the executable should be placed.</span> |
| Whisper | <span style="color:red">TODO: Add download/setup instructions for the Whisper server and required model file.</span> |
| Piper | <span style="color:red">TODO: Add download/setup instructions for Piper and the required voice model.</span> |
| Browser | <span style="color:red">TODO: Add tested browser versions and microphone permission requirements.</span> |

## Quick Start

Run these commands from the repository root.

### 1. Install Python dependencies

Using a virtual environment is recommended:

```bash
python -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn openai httpx python-multipart
```

On Windows, activate the environment with:

```bat
.venv\Scripts\activate
```

### 2. Add a GGUF model

Place a GGUF model in:

```text
New/Llama_Models/
```

On Windows, the provided `start_llama.bat` expects this exact file:

```text
New/Llama_Models/model.gguf
```

On macOS/Linux, `start_llama.sh` automatically uses the first `.gguf` file in `New/Llama_Models/`.

### 3. Start llama.cpp

macOS/Linux:

```bash
cd New
chmod +x start_llama.sh
./start_llama.sh
```

Windows:

```bat
cd New
start_llama.bat
```

The llama.cpp OpenAI-compatible API should now be available at:

```text
http://127.0.0.1:8001/v1
```

### 4. Start the backend

Open a second terminal.

macOS/Linux:

```bash
cd New
python -m Backend.main
```

Windows:

```bat
cd New
start_backend.bat
```

The backend starts at:

```text
http://127.0.0.1:8000
```

### 5. Open the app

Open this URL in the browser:

```text
http://127.0.0.1:8000
```

## Local Assets and Models

The backend expects these local folders relative to `New/`:

```text
New/
|-- Llama_Models/                  # GGUF language models
|-- llamacpp/                      # Windows: llama-server.exe
|-- Whisper/                       # Windows: whisper-server.exe and models
|-- Piper/                         # Windows: piper.exe and voice model
|-- Persona/                       # Optional system prompts
`-- data/                          # Auto-created SQLite/temp data
```

Example files:

| Purpose | Example path |
|---|---|
| LLM model | `New/Llama_Models/model.gguf` |
| Whisper model | `New/Whisper/models/ggml-medium-q5_0.bin` |
| Piper voice | `New/Piper/en_US-amy-medium.onnx` |
| Persona | `New/Persona/Koa_Sys.txt` |

Persona files must follow this naming pattern:

```text
*_Sys.txt
```

For example, `Koa_Sys.txt` appears as `Koa` in the persona dropdown.

### Platform-Specific Tool Layout

| Platform | Required layout |
|---|---|
| Windows | <span style="color:red">TODO: Document the exact expected folders for <code>llamacpp/</code>, <code>Whisper/</code>, and <code>Piper/</code>, including executable filenames.</span> |
| macOS/Linux | <span style="color:red">TODO: Document how Whisper and Piper should be installed or referenced when <code>.exe</code> files are not used.</span> |

### Asset Metadata

| Asset type | Missing documentation |
|---|---|
| Default VRM avatar | <span style="color:red">TODO: Add source, author, license, and redistribution permission for the default avatar.</span> |
| VRMA animations | <span style="color:red">TODO: Add source, author, license, and conversion notes for bundled animation files.</span> |
| GGUF models | <span style="color:red">TODO: Add expected storage size range and clarify that model licenses depend on the selected model.</span> |

## Configuration

Main configuration file:

```text
New/Backend/config/settings.py
```

Important settings:

| Variable | Default / Meaning |
|---|---|
| `LLM_API_URL` | `http://127.0.0.1:8001/v1` |
| `LLAMA_EXE` | Local llama.cpp executable path |
| `MODELS_DIR` | Folder for GGUF models |
| `FRONTEND_DIR` | Folder served as the frontend |
| `DB_PATH` | SQLite database path |
| `WHISPER_EXE` | Whisper server executable |
| `WHISPER_MODEL` | Whisper model file |
| `PIPER_EXE` | Piper executable |
| `PIPER_VOICE` | Piper voice model |

The backend automatically creates `New/data/` and `New/Llama_Models/` if they do not exist.

### Environment Configuration

<p>
  <strong><span style="color:red">TODO</span></strong><br>
  <span style="color:red">Move machine-specific paths from <code>settings.py</code> into environment variables or a <code>.env</code> file.</span>
</p>

Suggested future variables:

```text
LLM_API_URL=
LLAMA_EXE=
WHISPER_EXE=
WHISPER_MODEL=
PIPER_EXE=
PIPER_VOICE=
```

### Ports

| Service | Port |
|---|---|
| FastAPI backend | `8000` |
| llama.cpp server | `8001` |
| Whisper server | `8003` |
| Piper | subprocess, no HTTP port |

<p>
  <strong><span style="color:red">TODO</span></strong><br>
  <span style="color:red">Add a <code>.env.example</code> file once environment-based configuration exists.</span>
</p>

## API Reference

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Serves `Frontend/index.html` |
| `GET` | `/get_system_prompts` | Lists persona files from `New/Persona/` |
| `GET` | `/get_models` | Lists `.vrm` avatar models from `Frontend/static/assets/` |
| `GET` | `/get_animations` | Lists `.vrma` animation files |
| `POST` | `/chat` | Streams a text-only assistant response |
| `POST` | `/transcribe` | Transcribes an uploaded audio file |
| `POST` | `/chat_voice_stream` | Streams text and base64 audio packets as NDJSON |
| `POST` | `/clear_history` | Deletes stored conversation history |

### Chat Payload

`POST /chat` and `POST /chat_voice_stream` expect a JSON body with these fields:

```json
{
  "prompt": "Hello",
  "history": [],
  "system_prompt_name": "Koa",
  "use_memory": true
}
```

## Avatar Models and Animations

Avatar models are stored as `.vrm` files in:

```text
New/Frontend/static/assets/
```

Animations are stored as `.vrma` files in:

```text
New/Frontend/static/assets/animations/converted_gltf/
```

The animation registry is:

```text
New/Frontend/static/assets/animations/index.md
```

Current animation states:

| State | File | Usage |
|---|---|---|
| `neutral` | `Idle.vrma` | Resting/default animation |
| `taunt` | `Taunt.vrma` | Gesture while the assistant is speaking |

More animation-specific documentation is available in:

```text
New/Frontend/static/assets/animations/README.md
```

## Memory

Conversation memory is stored in SQLite when the memory toggle is enabled:

```text
New/data/ai_hub.db
```

The backend stores user and assistant messages in the `conversations` table. Clearing history from the UI calls `/clear_history` and deletes stored conversation rows.

## Privacy and Data Handling

Koa-AI is intended to run locally. When all local tools are used, chat prompts, generated answers, and audio processing stay on the machine.

Current data handling:

- Chat history is stored in `New/data/ai_hub.db` when memory is enabled.
- Uploaded audio is temporarily written to `New/data/temp_audio/` during transcription.
- Temporary audio files are deleted after transcription completes.
- Frontend libraries are loaded from external CDNs, so the browser must contact those CDN hosts unless the dependencies are vendored locally.

### Sensitive Data

<p>
  <strong><span style="color:red">TODO</span></strong><br>
  <span style="color:red">Add a clear statement that explains whether this prototype is appropriate for private or sensitive data.</span>
</p>

### Data Deletion

To remove stored conversation history, delete:

```text
New/data/ai_hub.db
```

<p>
  <strong><span style="color:red">TODO</span></strong><br>
  <span style="color:red">Add platform-specific deletion commands for Windows and macOS/Linux.</span>
</p>

### Offline Operation

<p>
  <strong><span style="color:red">TODO</span></strong><br>
  <span style="color:red">Document how to vendor frontend dependencies locally if the app must run without CDN access.</span>
</p>

### Asset Licenses

<p>
  <strong><span style="color:red">TODO</span></strong><br>
  <span style="color:red">Document license restrictions for the selected GGUF model, avatar model, animation files, and Piper voice model.</span>
</p>

## Known Limitations

- The Windows launcher expects `New/Llama_Models/model.gguf`.
- The macOS/Linux llama launcher uses the first `.gguf` file it finds in `New/Llama_Models/`.
- Whisper and Piper paths are currently configured directly in `settings.py`.
- Voice features depend on local executables that are not included in this repository.
- The frontend depends on CDN-loaded libraries.
- There is no automated test suite yet.
- There is no dependency lock file or `requirements.txt` yet.

### Planned Improvements

| Area | Missing improvement |
|---|---|
| Model path | <span style="color:red">TODO: Make the Windows model path configurable without editing <code>start_llama.bat</code>.</span> |
| Startup scripts | <span style="color:red">TODO: Add cross-platform startup scripts for backend, LLM, Whisper, and Piper.</span> |
| Health checks | <span style="color:red">TODO: Add checks for llama.cpp, Whisper, Piper, and required frontend assets.</span> |
| Tests | <span style="color:red">TODO: Add basic automated tests for API routes and service initialization.</span> |

## Troubleshooting

### The app opens, but the LLM does not respond

- Make sure `llama-server` is running on port `8001`.
- Make sure a `.gguf` model exists in `New/Llama_Models/`.
- Check `LLM_API_URL` in `New/Backend/config/settings.py`.
- Check the backend terminal output for `[LLM Error: ...]`.

### Voice input does not work

- Allow microphone access in the browser.
- Use `http://localhost:8000` or `http://127.0.0.1:8000`; browser microphone APIs usually require localhost or HTTPS.
- Make sure `whisper-server.exe` and the Whisper model exist at the configured paths.
- Check `WHISPER_EXE` and `WHISPER_MODEL` in `settings.py`.

### Voice output does not work

- Make sure `piper.exe` and the Piper voice file exist at the configured paths.
- Check `PIPER_EXE` and `PIPER_VOICE` in `settings.py`.
- Check the backend terminal for Piper subprocess errors.

### The avatar is not displayed

- Make sure at least one `.vrm` file exists in `New/Frontend/static/assets/`.
- Check the browser console for CDN loading errors.
- Check the browser console for missing local asset paths.

### The frontend loads without styles or scripts

- Start the app through the backend at `http://127.0.0.1:8000`.
- Do not open `Frontend/index.html` directly from the filesystem, because the app expects backend routes and `/static/...` paths.

## Third-Party Libraries and Tools

Koa-AI uses or integrates with:

- FastAPI for the backend API and static file serving
- Uvicorn as the ASGI server
- OpenAI Python SDK as an OpenAI-compatible client for llama.cpp
- httpx for HTTP calls to the Whisper service
- SQLite for local conversation storage
- llama.cpp for local LLM inference
- Whisper for speech-to-text
- Piper for text-to-speech
- Three.js for 3D rendering
- pixiv three-vrm for VRM avatar loading
- pixiv three-vrm-animation for VRM animation support
- fflate and Three.js loaders for asset loading

### Links and Licenses

| Dependency / asset | Link | License / credit |
|---|---|---|
| FastAPI | <span style="color:red">TODO: Add official link.</span> | <span style="color:red">TODO: Add license.</span> |
| Uvicorn | <span style="color:red">TODO: Add official link.</span> | <span style="color:red">TODO: Add license.</span> |
| OpenAI Python SDK | <span style="color:red">TODO: Add official link.</span> | <span style="color:red">TODO: Add license.</span> |
| httpx | <span style="color:red">TODO: Add official link.</span> | <span style="color:red">TODO: Add license.</span> |
| llama.cpp | <span style="color:red">TODO: Add official link.</span> | <span style="color:red">TODO: Add license.</span> |
| Whisper | <span style="color:red">TODO: Add official link.</span> | <span style="color:red">TODO: Add license.</span> |
| Piper | <span style="color:red">TODO: Add official link.</span> | <span style="color:red">TODO: Add license.</span> |
| Three.js | <span style="color:red">TODO: Add official link.</span> | <span style="color:red">TODO: Add license.</span> |
| pixiv three-vrm | <span style="color:red">TODO: Add official link.</span> | <span style="color:red">TODO: Add license.</span> |
| pixiv three-vrm-animation | <span style="color:red">TODO: Add official link.</span> | <span style="color:red">TODO: Add license.</span> |
| Avatar asset | <span style="color:red">TODO: Add source link.</span> | <span style="color:red">TODO: Add author and license.</span> |
| Animation assets | <span style="color:red">TODO: Add source links.</span> | <span style="color:red">TODO: Add authors and licenses.</span> |
| Voice asset | <span style="color:red">TODO: Add source link.</span> | <span style="color:red">TODO: Add author and license.</span> |

## Documentation TODOs

### Screenshots

<p>
  <strong><span style="color:red">TODO</span></strong><br>
  <span style="color:red">Insert screenshots of the main avatar view and settings panel.</span>
</p>

Suggested paths:

```text
docs/screenshots/main-avatar-view.png
docs/screenshots/settings-panel.png
docs/screenshots/conversation-view.png
```

### Demo Media

<p>
  <strong><span style="color:red">TODO</span></strong><br>
  <span style="color:red">Insert a short demo GIF or video link.</span>
</p>

Suggested path:

```text
docs/demo/koa-ai-demo.gif
```

### First-Time Setup Guides

<p>
  <strong><span style="color:red">TODO</span></strong><br>
  <span style="color:red">Add full first-time setup guides for Windows and macOS/Linux.</span>
</p>

Suggested files:

```text
docs/setup/windows.md
docs/setup/macos-linux.md
```

### Dependency Setup

<p>
  <strong><span style="color:red">TODO</span></strong><br>
  <span style="color:red">Add <code>requirements.txt</code> and update the installation instructions accordingly.</span>
</p>

### Model and Hardware Guidance

<p>
  <strong><span style="color:red">TODO</span></strong><br>
  <span style="color:red">Add model recommendations, hardware expectations, and a short explanation of the frontend module structure.</span>
</p>

### Contribution and License

<p>
  <strong><span style="color:red">TODO</span></strong><br>
  <span style="color:red">Add contribution and license sections once the maintenance and licensing decisions are final.</span>
</p>

## Development Notes

- The project currently has no `requirements.txt`; dependencies are listed in this README.
- The frontend is plain HTML/CSS/JavaScript and does not require a Node.js build step.
- The current setup is optimized for local development and demonstration.
- For a cleaner setup, consider adding a `requirements.txt`, a cross-platform launcher, and environment-based configuration for local tool paths.
