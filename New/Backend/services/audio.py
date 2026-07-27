# Backend/services/audio.py
import asyncio
import os
import uuid
import logging
from typing import Tuple
from fastapi.responses import StreamingResponse
from Backend.config.settings import WHISPER_MODEL, PIPER_VOICE, DATA_DIR

logger = logging.getLogger("AUDIO")

try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None

try:
    import piper
except ImportError:
    piper = None


class AudioService:
    def __init__(self):
        self.temp_dir = DATA_DIR / "temp_audio"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.last_transcription_error = ""
        self.whisper_model = None
        self.piper_voice_inst = None

    def _set_error(self, message: str):
        self.last_transcription_error = message
        logger.error(message)

    def load_whisper(self):
        if self.whisper_model is None and WhisperModel is not None:
            logger.info("Loading Whisper model...")
            # Set cpu_threads to 8 to leverage high-performance CPU cores
            self.whisper_model = WhisperModel(
                WHISPER_MODEL, 
                device="cpu", 
                compute_type="int8",
                cpu_threads=8
            )
            logger.info("Whisper model loaded.")

    def load_piper(self):
        if self.piper_voice_inst is None and piper is not None:
            json_file = PIPER_VOICE.with_name(PIPER_VOICE.name + ".json")
            if not PIPER_VOICE.exists() or not json_file.exists():
                logger.info(f"Piper voice missing at {PIPER_VOICE}, downloading automatically...")
                try:
                    from huggingface_hub import hf_hub_download
                    import shutil
                    PIPER_VOICE.parent.mkdir(parents=True, exist_ok=True)
                    tmp_dir = PIPER_VOICE.parent / "tmp_download"
                    hf_hub_download(repo_id="rhasspy/piper-voices", filename="en/en_US/amy/medium/en_US-amy-medium.onnx", local_dir=tmp_dir)
                    hf_hub_download(repo_id="rhasspy/piper-voices", filename="en/en_US/amy/medium/en_US-amy-medium.onnx.json", local_dir=tmp_dir)
                    shutil.move(tmp_dir / "en" / "en_US" / "amy" / "medium" / "en_US-amy-medium.onnx", PIPER_VOICE)
                    shutil.move(tmp_dir / "en" / "en_US" / "amy" / "medium" / "en_US-amy-medium.onnx.json", json_file)
                    shutil.rmtree(tmp_dir, ignore_errors=True)
                    logger.info("Piper voice downloaded successfully.")
                except Exception as e:
                    logger.error(f"Failed to auto-download Piper voice: {e}")
                    return

            if PIPER_VOICE.exists():
                logger.info("Loading Piper voice...")
                self.piper_voice_inst = piper.PiperVoice.load(str(PIPER_VOICE))
                logger.info("Piper voice loaded.")

    async def transcribe(self, audio_bytes: bytes) -> str:
        text, _ = await self.transcribe_with_meta(audio_bytes)
        return text

    async def transcribe_with_meta(self, audio_bytes: bytes) -> Tuple[str, str | None]:
        if WhisperModel is None:
            return "", "faster-whisper is not installed"
            
        file_id = uuid.uuid4()
        wav_path = self.temp_dir / f"{file_id}.wav"
        
        with open(wav_path, "wb") as f:
            f.write(audio_bytes)

        try:
            def _do_transcribe():
                self.load_whisper()
                # language="en" skips the language detection pass entirely
                # condition_on_previous_text=False avoids repetition loops & speeds up decoding
                segments, info = self.whisper_model.transcribe(
                    str(wav_path),
                    language="en",
                    beam_size=1,
                    vad_filter=True,
                    condition_on_previous_text=False
                )
                return " ".join([segment.text for segment in segments])

            text = await asyncio.to_thread(_do_transcribe)
            self.last_transcription_error = ""
            return text.strip(), None
        except Exception as e:
            self._set_error(f"Transcription request failed: {e}")
            return "", self.last_transcription_error
        finally:
            if wav_path.exists():
                os.remove(wav_path)

    async def piper_generator(self, text: str):
        if piper is None:
            logger.error("piper is not installed")
            return
            
        try:
            # Piper synthesis is CPU intensive, ideally should run in thread, but it's a generator.
            # We'll just run it synchronously for chunks and sleep to yield to event loop.
            self.load_piper()
            if self.piper_voice_inst:
                for chunk in self.piper_voice_inst.synthesize(text):
                    import numpy as np
                    # Convert the float32 [-1, 1] audio array to 16-bit PCM bytes (which synthesize_stream_raw used to output)
                    audio_bytes = (chunk.audio_float_array * 32767.0).astype(np.int16).tobytes()
                    yield audio_bytes
                    await asyncio.sleep(0.001)
        except Exception as e:
            logger.error(f"Piper Error: {e}")

    async def synthesize(self, text: str):
        return StreamingResponse(self.piper_generator(text), media_type="audio/wav")

audio_service = AudioService()
