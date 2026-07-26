import math
import re
from typing import Dict


class EmotionService:
    def __init__(self):
        self.categories = ["happy", "sad", "angry", "worried", "surprised", "neutral"]
        self._negations = {"not", "never", "no", "hardly", "rarely", "without", "isnt", "isn't", "dont", "don't", "cannot", "cant", "can't"}
        self._contrast_tokens = {"but", "however", "though", "although", "yet"}
        self._intensifiers = {
            "extremely": 1.8,
            "very": 1.4,
            "really": 1.35,
            "super": 1.45,
            "so": 1.25,
            "totally": 1.4,
            "absolutely": 1.5,
        }
        self._downtoners = {
            "slightly": 0.65,
            "somewhat": 0.75,
            "kinda": 0.75,
            "kind": 0.8,
            "a": 1.0,
            "little": 0.6,
            "bit": 0.75,
            "barely": 0.55,
        }
        self._emotion_weights = {
            "happy": {
                "happy": 1.0, "excited": 1.2, "joy": 1.2, "joyful": 1.2, "thrilled": 1.35,
                "love": 1.1, "great": 0.9, "awesome": 1.1, "wonderful": 1.1, "amazing": 1.1,
                "glad": 0.9, "delighted": 1.1, "pleased": 0.8, "proud": 0.8, "passed": 1.0,
            },
            "sad": {
                "sad": 1.0, "upset": 1.0, "unhappy": 1.1, "depressed": 1.4, "lonely": 1.1,
                "terrible": 1.2, "tragic": 1.3, "miserable": 1.3, "heartbroken": 1.4,
                "hopeless": 1.3, "gloomy": 1.0, "awful": 1.2,
            },
            "angry": {
                "angry": 1.2, "furious": 1.5, "mad": 1.0, "annoyed": 0.9, "hate": 1.2,
                "outraged": 1.5, "irritated": 1.0, "frustrated": 1.1, "rage": 1.4,
                "hostile": 1.2,
            },
            "worried": {
                "worried": 1.2, "anxious": 1.3, "nervous": 1.1, "afraid": 1.2, "scared": 1.2,
                "concerned": 1.0, "stress": 1.1, "stressed": 1.2, "uncertain": 1.0,
                "panic": 1.4, "fear": 1.2, "fearful": 1.2, "uneasy": 1.1,
            },
            "surprised": {
                "wow": 1.1, "surprised": 1.2, "unexpected": 1.1, "shocked": 1.3, "astonished": 1.4,
                "startled": 1.2, "unbelievable": 1.1, "speechless": 1.2, "whoa": 1.1,
            },
        }
        self._sentiment_lexicon = {
            "positive": {
                "happy": 0.8, "excited": 0.9, "joy": 0.9, "love": 0.9, "great": 0.7, "awesome": 0.9,
                "wonderful": 0.9, "amazing": 0.9, "delighted": 0.85, "passed": 0.8, "good": 0.6,
            },
            "negative": {
                "terrible": -0.9, "awful": -0.9, "sad": -0.75, "angry": -0.85, "furious": -1.0,
                "worried": -0.7, "anxious": -0.8, "nervous": -0.65, "depressed": -1.0, "hate": -0.9,
                "scared": -0.8, "upset": -0.75,
            },
        }
        self._emoji_sentiment = {
            "😍": 0.9, "😊": 0.7, "😄": 0.8, "😁": 0.8, "🎉": 0.8, "❤️": 0.8,
            "😢": -0.8, "😭": -0.9, "😡": -1.0, "😠": -0.95, "😟": -0.75, "😰": -0.8,
        }

    def _fallback_event(self, source: str = "user") -> Dict[str, object]:
        normalized_source = source if source in {"user", "assistant"} else "user"
        return {
            "emotion": "neutral",
            "valence": "neutral",
            "valence_score": 0.0,
            "intensity": 0.0,
            "confidence": 0.0,
            "source": normalized_source,
        }

    def _is_negated(self, tokens: list[str], idx: int) -> bool:
        start = max(0, idx - 3)
        return any(tok in self._negations for tok in tokens[start:idx])

    def _modifier_strength(self, tokens: list[str], idx: int) -> float:
        window = tokens[max(0, idx - 3):idx]
        strength = 1.0
        for tok in window:
            if tok in self._intensifiers:
                strength *= self._intensifiers[tok]
            if tok in self._downtoners:
                strength *= self._downtoners[tok]
        return max(0.3, min(strength, 2.0))

    def _valence_label(self, score: float) -> str:
        if score > 0.2:
            return "positive"
        if score < -0.2:
            return "negative"
        return "neutral"

    def classify_emotion(self, text: str, source: str = "user") -> Dict[str, object]:
        if not isinstance(text, str) or not text.strip():
            return self._fallback_event(source)

        raw_text = text.strip()
        cleaned = re.sub(r"[^\w\s'!?.,😍😊😄😁🎉❤️😢😭😡😠😟😰]", " ", raw_text.lower())
        tokens = re.findall(r"[a-zA-Z']+", cleaned)
        if not tokens:
            return self._fallback_event(source)

        emotion_scores = {name: 0.0 for name in self.categories if name != "neutral"}
        valence_acc = 0.0
        evidence = 0.0
        clause_weight = 1.0

        for idx, token in enumerate(tokens):
            if token in self._contrast_tokens:
                clause_weight = 1.35
                continue

            modifier = self._modifier_strength(tokens, idx)
            negated = self._is_negated(tokens, idx)

            for emotion, weights in self._emotion_weights.items():
                if token not in weights:
                    continue
                weight = weights[token] * modifier * clause_weight
                if negated:
                    # Negated positive emotions should not surface as positive.
                    if emotion in {"happy", "surprised"}:
                        emotion_scores["worried"] += 0.35 * weight
                        valence_acc -= 0.45 * weight
                        evidence += 0.4
                    else:
                        emotion_scores[emotion] += 0.25 * weight
                        valence_acc += 0.15 * weight
                        evidence += 0.25
                    continue

                emotion_scores[emotion] += weight
                evidence += 1.0

            if token in self._sentiment_lexicon["positive"]:
                sent_weight = self._sentiment_lexicon["positive"][token] * modifier * clause_weight
                valence_acc += -sent_weight if negated else sent_weight
            if token in self._sentiment_lexicon["negative"]:
                sent_weight = self._sentiment_lexicon["negative"][token] * modifier * clause_weight
                valence_acc += -sent_weight if negated else sent_weight

        for emoji, score in self._emoji_sentiment.items():
            if emoji in raw_text:
                valence_acc += score
                evidence += 0.8
                if score > 0.4:
                    emotion_scores["happy"] += 0.5
                if score < -0.6:
                    emotion_scores["angry"] += 0.6

        exclamations = raw_text.count("!")
        questions = raw_text.count("?")
        punctuation_boost = min(exclamations, 4) * 0.08 + min(questions, 3) * 0.05
        if questions > 0 and emotion_scores["worried"] > 0:
            emotion_scores["worried"] += 0.2

        sorted_scores = sorted(emotion_scores.items(), key=lambda kv: kv[1], reverse=True)
        top_emotion, top_score = sorted_scores[0]
        second_score = sorted_scores[1][1] if len(sorted_scores) > 1 else 0.0

        if top_score <= 0.45:
            top_emotion = "neutral"

        # Mixed/ambiguous inputs collapse to neutral when top signals are too close.
        if top_emotion != "neutral" and abs(top_score - second_score) < 0.28:
            top_emotion = "neutral"

        valence_score = math.tanh(valence_acc / 3.0)
        if top_emotion in {"sad", "angry", "worried"} and valence_score > 0.0:
            valence_score *= 0.2
        if top_emotion == "happy" and valence_score < 0.0:
            valence_score *= 0.2

        intensity_raw = (max(top_score, 0.0) / 3.0) + punctuation_boost
        intensity = round(max(0.0, min(intensity_raw, 1.0)), 2)

        confidence_raw = 0.25 + min(evidence / 6.0, 0.45) + min(max(top_score - second_score, 0.0) / 2.5, 0.3)
        if top_emotion == "neutral":
            confidence_raw = min(confidence_raw, 0.7)

        valence = self._valence_label(valence_score)

        return {
            "emotion": top_emotion,
            "valence": valence,
            "valence_score": round(max(-1.0, min(valence_score, 1.0)), 2),
            "intensity": intensity,
            "confidence": round(max(0.0, min(confidence_raw, 0.98)), 2),
            "source": source if source in {"user", "assistant"} else "user",
        }

    def build_event(self, text: str, source: str = "user") -> Dict[str, object]:
        try:
            event = self.classify_emotion(text, source=source)
            emotion = event.get("emotion", "neutral")
            valence = event.get("valence", "neutral")
            valence_score = float(event.get("valence_score", 0.0))
            intensity = float(event.get("intensity", 0.0))
            confidence = float(event.get("confidence", 0.55))
            out_source = event.get("source", source)
            if emotion not in self.categories:
                emotion = "neutral"
            if valence not in {"positive", "negative", "neutral"}:
                valence = "neutral"
            if out_source not in {"user", "assistant"}:
                out_source = "user"
            valence_score = round(max(-1.0, min(valence_score, 1.0)), 2)
            intensity = round(max(0.0, min(intensity, 1.0)), 2)
            confidence = round(max(0.0, min(confidence, 1.0)), 2)
            return {
                "emotion": emotion,
                "valence": valence,
                "valence_score": valence_score,
                "intensity": intensity,
                "confidence": confidence,
                "source": out_source,
            }
        except Exception:
            return self._fallback_event(source)


emotion_service = EmotionService()
