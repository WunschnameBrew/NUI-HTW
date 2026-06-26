# Backend/api/routes.py
from fastapi import APIRouter, WebSocket, UploadFile, File, Body
from fastapi.responses import StreamingResponse
import json
import asyncio
import base64
import re
from pathlib import Path

from Backend.config.settings import FRONTEND_DIR
from Backend.services.llm import llm_service
from Backend.services.audio import audio_service
from Backend.services.memory import memory_service
from Backend.services.animation import animation_service

router = APIRouter()

def get_persona_text(persona_name: str) -> str:
    if not persona_name:
        return "You are a helpful AI."
    persona_path = FRONTEND_DIR.parent / "Persona" / f"{persona_name}_Sys.txt"
    if persona_path.exists():
        return persona_path.read_text(encoding="utf-8")
    return "You are a helpful AI."

# --- METADATA ENDPOINTS ---

@router.get("/get_system_prompts")
async def get_system_prompts():
    persona_dir = FRONTEND_DIR.parent / "Persona"
    if not persona_dir.exists(): return {"system_prompts": []}
    files = persona_dir.glob("*_Sys.txt")
    return {"system_prompts": [f.stem.replace("_Sys", "") for f in files]}

@router.get("/get_models")
async def get_models():
    assets_dir = FRONTEND_DIR / "static" / "assets"
    if not assets_dir.exists(): return {"models": []}
    files = assets_dir.glob("*.vrm")
    return {"models": [f.name for f in files]}

@router.get("/get_animations")
async def get_animations():
    anims = await animation_service.get_animations()
    return {"animations": anims}

# --- CORE CHAT & VOICE ---

@router.post("/chat")
async def chat_endpoint(req: dict = Body(...)):
    prompt = req.get("prompt", "")
    history = req.get("history", [])
    system_prompt_name = req.get("system_prompt_name", "")
    use_memory = req.get("use_memory", True)
    
    sys_prompt = get_persona_text(system_prompt_name)
    messages = [{"role": "system", "content": sys_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": prompt})

    async def generator():
        full_resp = ""
        async for token in llm_service.stream_chat(messages):
            full_resp += token
            yield token
        if use_memory:
            await memory_service.save_interaction("user", prompt)
            await memory_service.save_interaction("assistant", full_resp)

    return StreamingResponse(generator(), media_type="text/plain")

@router.post("/transcribe")
async def transcribe_endpoint(audio_file: UploadFile = File(...)):
    content = await audio_file.read()
    text = await audio_service.transcribe(content)
    return {"transcription": text}

@router.post("/chat_voice_stream")
async def chat_voice_stream_endpoint(req: dict = Body(...)):
    prompt = req.get("prompt", "")
    history = req.get("history", [])
    system_prompt_name = req.get("system_prompt_name", "")
    use_memory = req.get("use_memory", True)
    
    sys_prompt = get_persona_text(system_prompt_name)
    messages = [{"role": "system", "content": sys_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": prompt})

    async def response_generator():
        sentence_end_regex = re.compile(r'(?<=[.!?])\s+')
        text_buffer = ""
        full_resp = ""

        async for token in llm_service.stream_chat(messages):
            full_resp += token
            yield json.dumps({"type": "text", "content": token}) + "\n"
            
            text_buffer += token
            parts = sentence_end_regex.split(text_buffer)
            
            if len(parts) > 1:
                sentence_to_speak = parts[0].strip()
                text_buffer = " ".join(parts[1:])
                
                if sentence_to_speak:
                    # Stream audio for this sentence
                    for audio_chunk in audio_service.piper_generator(sentence_to_speak):
                        b64_audio = base64.b64encode(audio_chunk).decode('utf-8')
                        yield json.dumps({"type": "audio", "data": b64_audio}) + "\n"

        # Final sentence
        if text_buffer.strip():
            for audio_chunk in audio_service.piper_generator(text_buffer.strip()):
                b64_audio = base64.b64encode(audio_chunk).decode('utf-8')
                yield json.dumps({"type": "audio", "data": b64_audio}) + "\n"
        
        if use_memory:
            await memory_service.save_interaction("user", prompt)
            await memory_service.save_interaction("assistant", full_resp)

    return StreamingResponse(response_generator(), media_type="application/x-ndjson")

@router.post("/clear_history")
async def clear_history():
    await memory_service.clear_history()
    return {"status": "cleared"}
