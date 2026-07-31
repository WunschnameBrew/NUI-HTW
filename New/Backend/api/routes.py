# Backend/api/routes.py
from fastapi import APIRouter, UploadFile, File, Body
from fastapi.responses import StreamingResponse
import json
import base64
import re
import logging
import asyncio

from Backend.config.settings import FRONTEND_DIR
from Backend.services.llm import llm_service
from Backend.services.audio import audio_service
from Backend.services.memory import memory_service
from Backend.services.animation import animation_service
from Backend.services.emotion import emotion_service

router = APIRouter()
logger = logging.getLogger("ROUTES")

SESSION_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_.:-]{1,64}$")
MAX_PROMPT_CHARS = 2000
MAX_MEMORY_MESSAGES = 8
MAX_MEMORY_CHARS = 5000


def _coerce_use_memory(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off"}:
            return False
    return True


def _normalize_session_id(value) -> str:
    if not isinstance(value, str):
        return "default"
    candidate = value.strip()
    if not candidate or not SESSION_ID_PATTERN.fullmatch(candidate):
        return "default"
    return candidate


def _sanitize_prompt(value) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()[:MAX_PROMPT_CHARS]


def _normalize_history(value) -> list:
    if not isinstance(value, list):
        return []
    normalized = []
    for item in value:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = item.get("content")
        if role in {"user", "assistant"} and isinstance(content, str) and content.strip():
            normalized.append({"role": role, "content": content.strip()[:MAX_PROMPT_CHARS]})
    return normalized


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

@router.get("/get_history")
async def get_history(session_id: str = "default"):
    session_id = _normalize_session_id(session_id)
    history = await memory_service.get_recent_history(limit=50, session_id=session_id)
    return {"history": history}

# --- CORE CHAT & VOICE ---

async def _build_messages(prompt: str, history: list, system_prompt_name: str, use_memory: bool, session_id: str | None = None):
    sys_prompt = get_persona_text(system_prompt_name)
    messages = [{"role": "system", "content": sys_prompt}]

    if use_memory:
        try:
            recent_history = await memory_service.get_recent_history(limit=MAX_MEMORY_MESSAGES, session_id=session_id)
        except Exception as error:
            logger.warning("Memory retrieval failed: %s", error)
            recent_history = []

        if recent_history:
            bounded_history = []
            running_chars = 0
            for msg in reversed(recent_history):
                content = str(msg.get("content", "")).strip()
                role = msg.get("role")
                if role not in {"user", "assistant"} or not content:
                    continue
                if running_chars + len(content) > MAX_MEMORY_CHARS:
                    break
                bounded_history.append({"role": role, "content": content})
                running_chars += len(content)
            messages.extend(reversed(bounded_history))
            history = [] # Deduplicate: ignore frontend history if DB memory is active

    if history:
        for item in history:
            if item.get("role") in {"user", "assistant"}:
                messages.append({"role": item["role"], "content": item["content"]})

    if not any(msg.get("role") == "user" and msg.get("content") == prompt for msg in messages):
        messages.append({"role": "user", "content": prompt})

    for message in messages:
        yield message


def _build_emotion_event(text: str, source: str):
    emotion_data = emotion_service.build_event(text, source=source)
    return {"type": "emotion", **emotion_data}


@router.post("/chat")
async def chat_endpoint(req: dict = Body(...)):
    req = req or {}
    prompt = _sanitize_prompt(req.get("prompt", ""))
    history = _normalize_history(req.get("history", []))
    system_prompt_name = req.get("system_prompt_name", "")
    use_memory = _coerce_use_memory(req.get("use_memory", True))
    session_id = _normalize_session_id(req.get("session_id"))

    messages = [message async for message in _build_messages(prompt, history, system_prompt_name, use_memory, session_id=session_id)]

    async def generator():
        full_resp = ""
        async for token in llm_service.stream_chat(messages):
            full_resp += token
            yield token
        if use_memory:
            try:
                await memory_service.save_interaction("user", prompt, session_id=session_id, enabled=True)
                await memory_service.save_interaction("assistant", full_resp, session_id=session_id, enabled=True)
            except Exception as error:
                logger.warning("Memory save failed: %s", error)

    return StreamingResponse(generator(), media_type="text/plain")

@router.post("/transcribe")
async def transcribe_endpoint(audio_file: UploadFile = File(...)):
    content = await audio_file.read()
    text, error = await audio_service.transcribe_with_meta(content)
    payload = {"transcription": text}
    if error:
        payload["error"] = error
    return payload

@router.post("/chat_voice_stream")
async def chat_voice_stream_endpoint(req: dict = Body(...)):
    req = req or {}
    prompt = _sanitize_prompt(req.get("prompt", ""))
    history = _normalize_history(req.get("history", []))
    system_prompt_name = req.get("system_prompt_name", "")
    use_memory = _coerce_use_memory(req.get("use_memory", True))
    session_id = _normalize_session_id(req.get("session_id"))

    messages = [message async for message in _build_messages(prompt, history, system_prompt_name, use_memory, session_id=session_id)]

    async def response_generator():
        sentence_end_regex = re.compile(r'(?<=[.!?])\s+')
        text_buffer = ""
        full_resp = ""

        try:
            emotion_event = _build_emotion_event(prompt, "user")
        except Exception as error:
            logger.warning("Emotion event failed: %s", error)
            emotion_event = {
                "type": "emotion",
                "emotion": "neutral",
                "valence": "neutral",
                "valence_score": 0.0,
                "intensity": 0.0,
                "confidence": 0.0,
                "source": "user",
            }
        yield json.dumps(emotion_event) + "\n"

        try:
            async for token in llm_service.stream_chat(messages):
                full_resp += token
                yield json.dumps({"type": "text", "content": token}) + "\n"

                text_buffer += token
                parts = sentence_end_regex.split(text_buffer)

                if len(parts) > 1:
                    sentence_to_speak = parts[0].strip()
                    text_buffer = " ".join(parts[1:])

                    if sentence_to_speak:
                        audio_gen = audio_service.piper_generator(sentence_to_speak)
                        if audio_gen is not None:
                            async for audio_chunk in audio_gen:
                                if not audio_chunk:
                                    continue
                                b64_audio = base64.b64encode(audio_chunk).decode('utf-8')
                                yield json.dumps({"type": "audio", "data": b64_audio}) + "\n"

            if text_buffer.strip():
                audio_gen = audio_service.piper_generator(text_buffer.strip())
                if audio_gen is not None:
                    async for audio_chunk in audio_gen:
                        if not audio_chunk:
                            continue
                        b64_audio = base64.b64encode(audio_chunk).decode('utf-8')
                        yield json.dumps({"type": "audio", "data": b64_audio}) + "\n"

            if full_resp.strip():
                try:
                    assistant_emotion = _build_emotion_event(full_resp, "assistant")
                except Exception as error:
                    logger.warning("Assistant emotion event failed: %s", error)
                    assistant_emotion = {
                        "type": "emotion",
                        "emotion": "neutral",
                        "valence": "neutral",
                        "valence_score": 0.0,
                        "intensity": 0.0,
                        "confidence": 0.0,
                        "source": "assistant",
                    }
                yield json.dumps(assistant_emotion) + "\n"

            if use_memory:
                try:
                    await memory_service.save_interaction("user", prompt, session_id=session_id, enabled=True)
                    await memory_service.save_interaction("assistant", full_resp, session_id=session_id, enabled=True)
                except Exception as error:
                    logger.warning("Memory save failed in stream route: %s", error)
        except asyncio.CancelledError:
            logger.info("Stream cancelled by client (kill switch triggered).")
            raise

    return StreamingResponse(response_generator(), media_type="application/x-ndjson")

@router.post("/clear_history")
async def clear_history(req: dict | None = Body(None)):
    payload = req or {}
    session_id = _normalize_session_id(payload.get("session_id"))
    try:
        await memory_service.clear_history(session_id=session_id)
    except Exception as error:
        logger.warning("Memory clear failed: %s", error)
    return {"status": "cleared"}
