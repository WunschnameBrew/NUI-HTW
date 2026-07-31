import os
import sys
import json
import pytest
import sqlite3
import asyncio
import tempfile
from pathlib import Path

import Backend.api.routes as routes

sys.path.append(str(Path(__file__).resolve().parents[1]))

from Backend.services.emotion import emotion_service
from Backend.services.memory import MemoryService


@pytest.fixture
def temp_memory_service(tmp_path):
    db_path = tmp_path / "test_ai_hub.db"
    service = MemoryService(db_path=str(db_path))
    asyncio.run(service.start())
    yield service
    asyncio.run(service.clear_history(session_id="session-a"))
    asyncio.run(service.clear_history(session_id="session-b"))


def test_emotion_classification_happy():
    result = emotion_service.classify_emotion("I am so excited and thrilled!")
    assert result["emotion"] == "happy"
    assert result["valence"] == "positive"
    assert result["valence_score"] > 0
    assert result["intensity"] >= 0.5
    assert result["confidence"] >= 0.5
    assert result["source"] == "user"


def test_emotion_classification_sad():
    result = emotion_service.classify_emotion("I feel terrible and lonely")
    assert result["emotion"] == "sad"
    assert result["valence"] == "negative"


def test_emotion_classification_angry():
    result = emotion_service.classify_emotion("I am furious and angry")
    assert result["emotion"] == "angry"
    assert result["valence"] == "negative"


def test_emotion_classification_worried():
    result = emotion_service.classify_emotion("I am worried about the deadline")
    assert result["emotion"] == "worried"
    assert result["valence"] == "negative"


def test_emotion_classification_surprised():
    result = emotion_service.classify_emotion("Wow, I did not expect that")
    assert result["emotion"] in {"surprised", "neutral"}


def test_emotion_classification_neutral():
    result = emotion_service.classify_emotion("Please summarize this document")
    assert result["emotion"] == "neutral"
    assert result["valence"] == "neutral"


def test_emotion_classification_unknown_falls_back_to_neutral():
    result = emotion_service.classify_emotion("asdf qwer zxcv")
    assert result["emotion"] == "neutral"
    assert result["valence"] == "neutral"


def test_emotion_classification_negated_happy_falls_back():
    result = emotion_service.classify_emotion("I am not happy about this")
    assert result["emotion"] in {"neutral", "worried"}
    assert result["valence"] in {"neutral", "negative"}


def test_emotion_classification_ambiguous_falls_back():
    result = emotion_service.classify_emotion("I am happy but also very sad")
    assert result["emotion"] in {"neutral", "sad", "worried"}


def test_emotion_classification_invalid_input_is_safe():
    result = emotion_service.classify_emotion(None)
    assert result["emotion"] == "neutral"
    assert result["valence"] == "neutral"
    assert result["valence_score"] == 0.0
    assert result["intensity"] == 0.0
    assert result["source"] == "user"


def test_emotion_event_validation_invalid_source_is_sanitized():
    event = emotion_service.build_event("I am happy", source="system")
    assert event["emotion"] == "happy"
    assert event["valence"] == "positive"
    assert -1.0 <= event["valence_score"] <= 1.0
    assert 0.0 <= event["intensity"] <= 1.0
    assert 0.0 <= event["confidence"] <= 1.0
    assert event["source"] == "user"


def test_emotion_schema_has_required_fields_and_ranges():
    result = emotion_service.classify_emotion("I am very happy!")
    assert set(result.keys()) == {"emotion", "valence", "valence_score", "intensity", "confidence", "source"}
    assert result["emotion"] in {"happy", "sad", "angry", "worried", "surprised", "neutral"}
    assert result["valence"] in {"positive", "negative", "neutral"}
    assert -1.0 <= result["valence_score"] <= 1.0
    assert 0.0 <= result["intensity"] <= 1.0
    assert 0.0 <= result["confidence"] <= 1.0


def test_emotion_intensifier_increases_intensity():
    weak = emotion_service.classify_emotion("I am happy")
    strong = emotion_service.classify_emotion("I am extremely happy!!!")
    assert strong["intensity"] >= weak["intensity"]


def test_emotion_weak_cues_stay_low_intensity():
    result = emotion_service.classify_emotion("I am a little worried")
    assert result["emotion"] in {"worried", "neutral"}
    assert result["intensity"] <= 0.65


def test_emotion_emoji_signal_supported():
    result = emotion_service.classify_emotion("I passed my exam 😍")
    assert result["valence"] == "positive"
    assert result["valence_score"] > 0


def test_emotion_mixed_statement_resolves_ambiguity():
    result = emotion_service.classify_emotion("I love this but I am also anxious")
    assert result["emotion"] in {"neutral", "worried", "happy"}
    assert result["valence"] in {"neutral", "negative", "positive"}


def test_memory_saves_when_enabled(temp_memory_service):
    asyncio.run(temp_memory_service.save_interaction("user", "hello", session_id="session-a"))
    asyncio.run(temp_memory_service.save_interaction("assistant", "hi", session_id="session-a"))
    history = asyncio.run(temp_memory_service.get_recent_history(limit=5, session_id="session-a"))
    assert len(history) == 2


def test_memory_not_saved_when_disabled(temp_memory_service):
    asyncio.run(temp_memory_service.save_interaction("user", "hello", session_id="session-a", enabled=False))
    history = asyncio.run(temp_memory_service.get_recent_history(limit=5, session_id="session-a"))
    assert history == []


def test_memory_not_retrieved_when_disabled(monkeypatch):
    class FakeMemory:
        async def get_recent_history(self, limit=5, session_id=None):
            raise AssertionError("get_recent_history should not be called when use_memory is false")

    monkeypatch.setattr("Backend.api.routes.memory_service", FakeMemory())

    async def run():
        messages = [message async for message in routes._build_messages(
            prompt="hello",
            history=[],
            system_prompt_name="",
            use_memory=False,
            session_id="s1",
        )]
        assert any(msg["role"] == "user" and msg["content"] == "hello" for msg in messages)

    asyncio.run(run())


def test_database_migration_adds_session_id_and_keeps_rows():
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("INSERT INTO conversations (role, content) VALUES (?, ?)", ("user", "legacy-row"))
    conn.commit()
    conn.close()

    service = MemoryService(db_path=db_path)
    asyncio.run(service.start())

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(conversations)")
    cols = [row[1] for row in cur.fetchall()]
    cur.execute("SELECT role, content, session_id FROM conversations ORDER BY id ASC")
    rows = cur.fetchall()
    conn.close()
    os.remove(db_path)

    assert "session_id" in cols
    assert rows[0][0] == "user"
    assert rows[0][1] == "legacy-row"
    assert rows[0][2] == "default"


def test_history_ordering(temp_memory_service):
    asyncio.run(temp_memory_service.save_interaction("user", "first", session_id="session-a"))
    asyncio.run(temp_memory_service.save_interaction("assistant", "second", session_id="session-a"))
    history = asyncio.run(temp_memory_service.get_recent_history(limit=5, session_id="session-a"))
    assert [entry["content"] for entry in history] == ["first", "second"]


def test_session_separation(temp_memory_service):
    asyncio.run(temp_memory_service.save_interaction("user", "one", session_id="session-a"))
    asyncio.run(temp_memory_service.save_interaction("user", "two", session_id="session-b"))
    history_a = asyncio.run(temp_memory_service.get_recent_history(limit=5, session_id="session-a"))
    history_b = asyncio.run(temp_memory_service.get_recent_history(limit=5, session_id="session-b"))
    assert len(history_a) == 1 and history_a[0]["content"] == "one"
    assert len(history_b) == 1 and history_b[0]["content"] == "two"


def test_clear_one_session_does_not_clear_another(temp_memory_service):
    asyncio.run(temp_memory_service.save_interaction("user", "a", session_id="session-a"))
    asyncio.run(temp_memory_service.save_interaction("user", "b", session_id="session-b"))
    asyncio.run(temp_memory_service.clear_history(session_id="session-a"))
    history_a = asyncio.run(temp_memory_service.get_recent_history(limit=5, session_id="session-a"))
    history_b = asyncio.run(temp_memory_service.get_recent_history(limit=5, session_id="session-b"))
    assert history_a == []
    assert len(history_b) == 1


def test_retrieved_history_in_prompt(monkeypatch):
    class FakeMemory:
        async def get_recent_history(self, limit=5, session_id=None):
            return [{"role": "user", "content": "remember this"}, {"role": "assistant", "content": "I remember"}]

        async def save_interaction(self, role, content, session_id=None, enabled=True):
            return None

    monkeypatch.setattr("Backend.api.routes.memory_service", FakeMemory())

    import Backend.api.routes as routes

    async def run():
        messages = [message async for message in routes._build_messages(prompt="hello", history=[], system_prompt_name="", use_memory=True, session_id="s1")]
        assert any(msg["content"] == "remember this" for msg in messages)
        assert any(msg["content"] == "I remember" for msg in messages)

    asyncio.run(run())


def test_retrieved_history_is_bounded(monkeypatch):
    long_msg = "x" * 3000

    class FakeMemory:
        async def get_recent_history(self, limit=5, session_id=None):
            return [
                {"role": "user", "content": long_msg},
                {"role": "assistant", "content": long_msg},
                {"role": "user", "content": long_msg},
            ]

    monkeypatch.setattr("Backend.api.routes.memory_service", FakeMemory())

    async def run():
        messages = [message async for message in routes._build_messages(prompt="hello", history=[], system_prompt_name="", use_memory=True, session_id="s1")]
        memory_content_chars = sum(len(msg["content"]) for msg in messages if msg["role"] in {"user", "assistant"} and msg["content"] != "hello")
        assert memory_content_chars <= routes.MAX_MEMORY_CHARS

    asyncio.run(run())


def test_current_user_message_not_added_twice(monkeypatch):
    class FakeMemory:
        async def get_recent_history(self, limit=5, session_id=None):
            return [{"role": "user", "content": "old"}]

        async def save_interaction(self, role, content, session_id=None, enabled=True):
            return None

    monkeypatch.setattr("Backend.api.routes.memory_service", FakeMemory())

    async def run():
        messages = [message async for message in routes._build_messages(prompt="hello", history=[], system_prompt_name="", use_memory=True, session_id="s1")]
        user_messages = [msg for msg in messages if msg["role"] == "user"]
        assert sum(1 for msg in user_messages if msg["content"] == "hello") == 1

    asyncio.run(run())


def test_voice_stream_skips_audio_when_piper_is_unavailable(monkeypatch):
    async def fake_stream_chat(messages, temperature=0.7, **kwargs):
        yield "Hello there. More text"

    monkeypatch.setattr(routes.llm_service, "stream_chat", fake_stream_chat)
    monkeypatch.setattr(routes.audio_service, "piper_generator", lambda text: None)

    async def run():
        response = await routes.chat_voice_stream_endpoint({
            "prompt": "hello",
            "history": [],
            "system_prompt_name": "",
            "use_memory": False,
            "session_id": "s1",
        })

        chunks = []
        async for chunk in response.body_iterator:
            if isinstance(chunk, bytes):
                chunks.append(chunk.decode("utf-8"))
            else:
                chunks.append(chunk)

        assert any("type\": \"text\"" in chunk for chunk in chunks)
        assert any("type\": \"emotion\"" in chunk for chunk in chunks)

    asyncio.run(run())


def test_voice_stream_survives_emotion_errors(monkeypatch):
    async def fake_stream_chat(messages, temperature=0.7, **kwargs):
        yield "Hello"

    def broken_event(*args, **kwargs):
        raise RuntimeError("emotion failed")

    monkeypatch.setattr(routes.llm_service, "stream_chat", fake_stream_chat)
    monkeypatch.setattr(routes, "_build_emotion_event", broken_event)
    monkeypatch.setattr(routes.audio_service, "piper_generator", lambda text: None)

    async def run():
        response = await routes.chat_voice_stream_endpoint({
            "prompt": "hello",
            "history": [],
            "system_prompt_name": "",
            "use_memory": False,
            "session_id": "s1",
        })

        packets = []
        async for chunk in response.body_iterator:
            text = chunk.decode("utf-8") if isinstance(chunk, bytes) else chunk
            for line in text.split("\n"):
                line = line.strip()
                if not line:
                    continue
                packets.append(json.loads(line))

        assert any(p.get("type") == "emotion" for p in packets)
        assert any(p.get("type") == "text" for p in packets)
        emotion_packets = [p for p in packets if p.get("type") == "emotion"]
        assert any(set(ep.keys()) >= {"emotion", "valence", "valence_score", "intensity", "confidence", "source"} for ep in emotion_packets)

    asyncio.run(run())


def test_build_messages_survives_memory_errors(monkeypatch):
    class BrokenMemory:
        async def get_recent_history(self, limit=5, session_id=None):
            raise RuntimeError("db unavailable")

    monkeypatch.setattr("Backend.api.routes.memory_service", BrokenMemory())

    async def run():
        messages = [message async for message in routes._build_messages(prompt="hello", history=[], system_prompt_name="", use_memory=True, session_id="s1")]
        assert any(msg["role"] == "user" and msg["content"] == "hello" for msg in messages)

    asyncio.run(run())


def test_request_normalization_helpers():
    assert routes._coerce_use_memory("false") is False
    assert routes._coerce_use_memory("yes") is True
    assert routes._normalize_session_id("invalid space") == "default"
    assert routes._normalize_session_id("session-1") == "session-1"
    assert routes._sanitize_prompt(12345) == ""


def test_transcribe_endpoint_returns_error_payload(monkeypatch):
    async def fake_transcribe_with_meta(_bytes):
        return "", "Whisper model not found."

    class DummyUpload:
        async def read(self):
            return b"dummy"

    monkeypatch.setattr(routes.audio_service, "transcribe_with_meta", fake_transcribe_with_meta)

    async def run():
        payload = await routes.transcribe_endpoint(DummyUpload())
        assert payload["transcription"] == ""
        assert "error" in payload

    asyncio.run(run())


def test_transcribe_endpoint_returns_text_without_error(monkeypatch):
    async def fake_transcribe_with_meta(_bytes):
        return "hello world", None

    class DummyUpload:
        async def read(self):
            return b"dummy"

    monkeypatch.setattr(routes.audio_service, "transcribe_with_meta", fake_transcribe_with_meta)

    async def run():
        payload = await routes.transcribe_endpoint(DummyUpload())
        assert payload["transcription"] == "hello world"
        assert "error" not in payload

    asyncio.run(run())
