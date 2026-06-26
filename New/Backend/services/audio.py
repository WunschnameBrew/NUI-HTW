# Backend/services/audio.py
import asyncio
import subprocess
import os
import uuid
import httpx
import logging
from pathlib import Path
from fastapi.responses import StreamingResponse
from Backend.config.settings import WHISPER_EXE, WHISPER_MODEL, PIPER_EXE, PIPER_VOICE, DATA_DIR

logger = logging.getLogger("AUDIO")

class AudioService:
    def __init__(self):
        self.whisper_proc = None
        self.whisper_port = 8003
        self.temp_dir = DATA_DIR / "temp_audio"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    async def start_whisper(self):
        """Starts whisper-server.exe if not already running."""
        if self.whisper_proc and self.whisper_proc.poll() is None:
            return
        
        if not WHISPER_EXE.exists():
            logger.error(f"Whisper executable not found at {WHISPER_EXE}")
            return

        cmd = [str(WHISPER_EXE), "-m", str(WHISPER_MODEL), "--port", str(self.whisper_port), "--threads", "4"]
        try:
            self.whisper_proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            logger.info("Whisper server started.")
            await asyncio.sleep(2)
        except Exception as e:
            logger.error(f"Whisper Launch Error: {e}")

    async def transcribe(self, audio_bytes: bytes) -> str:
        """Transcribes audio bytes using Whisper server."""
        await self.start_whisper()
        
        # Save to temp wav for whisper-server (if it doesn't support direct bytes)
        file_id = uuid.uuid4()
        wav_path = self.temp_dir / f"{file_id}.wav"
        
        # NOTE: This assumes incoming bytes are already in a format Whisper likes (16k mono wav)
        # In a real scenario, we might need ffmpeg here to convert.
        with open(wav_path, "wb") as f:
            f.write(audio_bytes)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                with open(wav_path, "rb") as f:
                    resp = await client.post(
                        f"http://127.0.0.1:{self.whisper_port}/inference", 
                        files={"file": f}, 
                        data={"response_format": "json"}
                    )
                    text = resp.json().get("text", "").strip()
                    return text
        except Exception as e:
            logger.error(f"Transcription Error: {e}")
            return ""
        finally:
            if wav_path.exists():
                os.remove(wav_path)

    def piper_generator(self, text: str):
        """Generates raw PCM audio chunks for a given text using Piper."""
        if not PIPER_EXE.exists():
            return
        
        try:
            proc = subprocess.Popen(
                [str(PIPER_EXE), "-m", str(PIPER_VOICE), "--output-raw"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            proc.stdin.write(text.encode('utf-8'))
            proc.stdin.close()
            while True:
                chunk = proc.stdout.read(4096)
                if not chunk:
                    break
                yield chunk
            proc.wait()
        except Exception as e:
            logger.error(f"Piper Error: {e}")

    async def synthesize(self, text: str):
        """Returns a StreamingResponse for Piper audio."""
        return StreamingResponse(self.piper_generator(text), media_type="audio/wav")

audio_service = AudioService()
