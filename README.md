# Koa-AI – 3D VRM Voice & Text Assistant

Koa-AI is a locally running AI assistant with an interactive 3D VRM avatar. It combines local language-model inference, speech recognition, speech synthesis, emotion-driven avatar reactions, selectable personas, and optional conversation memory.

## Table of Contents

- [Project Status](#project-status)
- [Features](#features)
- [Requirements](#requirements)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Models and Configuration](#models-and-configuration)
- [Personas](#personas)
- [Avatars and Animations](#avatars-and-animations)
- [Conversation Memory](#conversation-memory)
- [Development](#development)
- [Known Limitations](#known-limitations)
- [Sources and Licenses](#sources-and-licenses)
- [Privacy](#privacy)
- [Troubleshooting](#troubleshooting)

## Project Status

Koa-AI is a university project and functional prototype. It is intended for local demonstration and development rather than production use.

Launch scripts are provided for:

- Windows
- macOS
- Linux

### Current Test Environment

The following environment is currently available for development and testing:

| Component | Version |
|---|---|
| Operating system | macOS 26.3.1 on Apple Silicon (`arm64`) |
| Python | 3.10.5 |
| Google Chrome | 150.0.7871.187 |
| Mozilla Firefox | 153.0 |

The environment and installed versions have been verified. A complete functional test of text chat, voice input, voice output, and VRM rendering is still pending. Windows and Linux are supported through the provided scripts but have not yet been documented as tested environments.

## Features

- Local GGUF inference with `llama-cpp-python`
- Streaming text responses and Piper voice output
- English voice input with `faster-whisper`
- Interactive Three.js scene with selectable VRM avatars
- Emotion-based facial expressions and VRMA body animations
- Selectable system-prompt personas
- Optional SQLite conversation memory
- Stop button for cancelling responses and audio playback

## Requirements

- Python 3.10 to 3.12
- A modern browser with WebGL support
- Microphone permission for voice input
- Internet access for the initial installation and model downloads
- Several gigabytes of free disk space

CPU inference works without a dedicated GPU. The setup also offers CUDA, Vulkan, and Apple Metal support where available.

## Quick Start

Clone or download the repository, open a terminal in the project folder, and change to the application directory:

```bash
cd New
```

### 1. Create a virtual environment

Using a virtual environment keeps the project dependencies separate from the system-wide Python installation.

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows:

```bat
python -m venv .venv
.venv\Scripts\activate
```

### 2. Run the automatic setup

macOS/Linux:

```bash
bash setup.sh
```

Windows:

```bat
setup.bat
```

Alternatively, run the setup script directly:

```bash
python setup_environment.py
```

The setup installs the Python dependencies and downloads the default language model and Piper voice. Select CPU by pressing Enter, or choose CUDA, Vulkan, or Metal when compatible hardware and drivers are available.

### 3. Start Koa-AI

macOS/Linux:

```bash
./start.sh
```

Windows:

```bat
start.bat
```

Alternatively:

```bash
python start.py
```

Open [http://localhost:8000](http://localhost:8000) in your browser. Initial startup may take longer while the local models are downloaded or loaded.

## Usage

- Click the microphone button to start or stop recording.
- Click the message button to enter a text prompt.
- Use the stop button to cancel the current response and audio playback.
- Open the settings to change the persona or avatar and enable or disable memory.
- Use **Clear history** to remove the stored conversation.

The project includes the `Default` and `Concise` personas.

### Typical Workflow

1. Start Koa-AI and wait until the models have loaded.
2. Open `http://localhost:8000`.
3. Select a persona and avatar in the settings.
4. Enter a text prompt or record a voice message.
5. Observe the streamed response, voice output, facial expression, and body animation.
6. Stop the response if needed or clear the conversation history in the settings.

## Project Structure

```text
New/
├── Backend/
│   ├── api/                 # FastAPI routes
│   ├── config/              # Paths and model configuration
│   ├── services/            # LLM, audio, memory, emotion, and animation logic
│   └── main.py              # FastAPI application
├── Frontend/
│   ├── index.html           # Browser interface
│   └── static/              # JavaScript, CSS, avatars, and animations
├── Persona/                 # System-prompt personas
├── Llama_Models/            # Local GGUF models
├── Piper/                   # Piper voice model
├── data/                    # SQLite database and temporary audio
├── setup_environment.py     # Automated installation
├── setup.bat / setup.sh     # Setup launchers
└── start.bat / start.sh     # Application launchers
```

## Models and Configuration

The main configuration is located in:

```text
New/Backend/config/settings.py
```

The default setup uses:

| Component | Model or location |
|---|---|
| Language model | `Dolphin3.0-Llama3.2-3B.Q4_K_S.gguf` |
| Whisper model | `Systran/faster-distil-whisper-small.en` |
| Piper voice | `en_US-amy-medium` |
| Conversation database | `New/data/ai_hub.db` |

To use another language model, place a `.gguf` file in `New/Llama_Models/` and adjust the model selection in `settings.py` if necessary.

## Personas

Persona files are stored in `New/Persona/` and follow this naming scheme:

```text
<Name>_Sys.txt
```

For example, `Concise_Sys.txt` appears as `Concise` in the settings. Add a UTF-8 text file following this scheme and reload the page to add another persona.

## Avatars and Animations

Place `.vrm` avatar models in:

```text
New/Frontend/static/assets/
```

Place `.vrma` animation files in:

```text
New/Frontend/static/assets/animations/converted_gltf/
```

Assign animations to emotion categories in `New/Frontend/static/assets/animations/index.md`:

```text
#happy
- Excited.vrma 1.0
- Happy Idle.vrma 1.0
```

Raw FBX source files can be stored in `animations/raw_fbx/`. An FBX-to-VRMA converter is not included in this repository.

## Conversation Memory

When memory is enabled, conversations are stored locally in:

```text
New/data/ai_hub.db
```

The history can be cleared from the settings. To remove all stored conversations manually, stop the application and delete the database file. It will be recreated on the next start.

## Development

Start the backend with automatic reload from the `New` directory:

```bash
python -m uvicorn Backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Run the tests with:

```bash
python -m pytest
```

## Known Limitations

- Voice input currently supports English only.
- Model loading and local inference can be slow without hardware acceleration.
- The first `.gguf` file found in `New/Llama_Models/` is selected automatically.
- The browser interface loads fonts and 3D libraries from external CDNs and is therefore not fully offline.
- Conversation memory is local to the backend installation and is not intended for isolated multi-user operation.
- FBX source animations cannot be converted inside this repository because no conversion tool is included.

## Sources and Licenses

### Project License

No project-wide license file is currently included. Without an explicit license, no general permission to copy, modify, or redistribute the project is granted.

<strong><span style="color:red">TODO</span></strong> (Choose a project license, add a `LICENSE` file, and state the license here.)

### Models and Assets

| Item | Source | License |
|---|---|---|
| Dolphin 3.0 Llama 3.2 GGUF | [QuantFactory/Dolphin3.0-Llama3.2-3B-GGUF](https://huggingface.co/QuantFactory/Dolphin3.0-Llama3.2-3B-GGUF) | <strong><span style="color:red">TODO</span></strong> (Add the applicable model license and any required attribution.) |
| `faster-distil-whisper-small.en` | [Systran/faster-distil-whisper-small.en](https://huggingface.co/Systran/faster-distil-whisper-small.en) | <strong><span style="color:red">TODO</span></strong> (Verify and add the model license.) |
| `en_US-amy-medium` voice | [rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices) | <strong><span style="color:red">TODO</span></strong> (Add the voice-specific license and attribution from its model card.) |
| `7523718638436607923.vrm` | <strong><span style="color:red">TODO</span></strong> (Add creator and original source URL.) | <strong><span style="color:red">TODO</span></strong> (Add the avatar's usage and redistribution license.) |
| `788686174174413810.vrm` | <strong><span style="color:red">TODO</span></strong> (Add creator and original source URL.) | <strong><span style="color:red">TODO</span></strong> (Add the avatar's usage and redistribution license.) |
| FBX and VRMA animations | <strong><span style="color:red">TODO</span></strong> (Add creator, asset pack, and original source URL.) | <strong><span style="color:red">TODO</span></strong> (Add the animation usage and redistribution license.) |

The VRMA integration references the open-source [fbx2vrma-converter](https://github.com/tk256ailab/fbx2vrma-converter). Runtime libraries such as FastAPI, `llama-cpp-python`, Piper, Three.js, and `@pixiv/three-vrm` remain subject to their own licenses.

## Privacy

Language-model inference, transcription, speech synthesis, and conversation storage run locally. The initial setup downloads packages and models from PyPI and Hugging Face, and the frontend loads some libraries and fonts from external CDNs.

Temporary microphone recordings are removed after transcription. Avoid processing sensitive information unless the local installation and the selected third-party models meet your security requirements.

## Troubleshooting

### No language model is loaded

- Make sure a `.gguf` file exists in `New/Llama_Models/`.
- Run the setup again if the default model download failed.
- If necessary, download the model from the source listed under [Sources and Licenses](#sources-and-licenses) and place it in `New/Llama_Models/`.
- Check the terminal for model-loading errors.

### Voice input does not work

- Open the application through `http://localhost:8000`.
- Grant microphone permission in the browser.
- Check the terminal for Whisper errors.

### Voice output does not work

- Make sure `en_US-amy-medium.onnx` and `en_US-amy-medium.onnx.json` exist in `New/Piper/`.
- Run the setup again if either file is missing.
- Check the terminal for Piper errors.

### Setup completed, but model files are missing

Verify that these files exist:

```text
New/Llama_Models/Dolphin3.0-Llama3.2-3B.Q4_K_S.gguf
New/Piper/en_US-amy-medium.onnx
New/Piper/en_US-amy-medium.onnx.json
```

Run the setup again if a download was interrupted. Existing valid files are reused.

### Hardware acceleration cannot be installed

Run the setup again and select CPU mode. For CUDA, Vulkan, or Metal, verify that the required drivers and build tools are installed.
