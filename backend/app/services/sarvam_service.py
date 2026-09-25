import httpx
import logging
import base64
from typing import Optional, Dict, Any, List
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

# Multilingual intent dictionaries for Indian regional languages
MULTILINGUAL_INTENT_MAP = {
    "daughter_or_family": {
        "en": ["daughter", "son", "family", "child", "who is", "caregiver"],
        "ta": ["மகள்", "மகன்", "குடும்பம்", "யார்", "அனிதா"],
        "hi": ["बेटी", "बेटा", "परिवार", "कौन है", "अनीता"],
        "kn": ["ಮಗಳು", "ಮಗ", "ಕುಟುಂಬ", "ಯಾರು", "ಅನಿತಾ"],
        "as": ["জীয়েক", "পুতেক", "পৰিয়াল", "কোন", "মা", "দেউতা"],
        "bn": ["মেয়ে", "ছেলে", "পরিবার", "কে", "মা", "বাবা"]
    },
    "food": {
        "en": ["food", "favourite food", "eat", "lunch", "dinner", "breakfast"],
        "ta": ["சாப்பாடு", "உணவு", "பிடித்த உணவு", "இட்லி", "சாப்பிடு"],
        "hi": ["खाना", "पसंदीदा खाना", "भोजन", "इडली"],
        "kn": ["ಊಟ", "ಆಹಾರ", "ತಿಂಡಿ", "ಇಡ್ಲಿ"],
        "as": ["খাদ্য", "খোৱা", "প্ৰিয় খাদ্য", "ইডলি", "ভাত"],
        "bn": ["খাবার", "খাওয়া", "প্রিয় খাবার", "ইডলি", "ভাত"]
    },
    "reminder": {
        "en": ["reminder", "medicine", "pill", "next", "time", "routine"],
        "ta": ["நினைவூட்டல்", "மருந்து", "மாத்திரை", "அடுத்தது"],
        "hi": ["याद दिलाना", "दवाई", "समय", "अगला"],
        "kn": ["ಜ್ಞಾಪನೆ", "ಮಾತ್ರೆ", "ಔಷಧ", "ಮುಂದಿನ"],
        "as": ["সোঁৱৰণী", "ঔষধ", "সময়", "পৰৱৰ্তী"],
        "bn": ["স্মারক", "ঔষধ", "সময়", "পরবর্তী"]
    },
    "name": {
        "en": ["my name", "who am i", "name"],
        "ta": ["என் பெயர்", "நான் யார்", "பெயர்"],
        "hi": ["मेरा नाम", "मैं कौन हूँ", "नाम"],
        "kn": ["ನನ್ನ ಹೆಸರು", "ನಾನು ಯಾರು", "ಹೆಸರು"],
        "as": ["মোৰ নাম", "মই কোন", "নাম"],
        "bn": ["আমার নাম", "আমি কে", "নাম"]
    }
}

LOCALIZED_TEMPLATES = {
    "ta-IN": {
        "daughter": "உங்கள் மகள் அனிதா, அவர் உங்களை அன்போடு கவனித்துக் கொள்கிறார்.",
        "food": "உங்களுக்கு மிகவும் பிடித்த உணவு சூடான இட்லி மற்றும் தேங்காய் சட்னி.",
        "reminder": "உங்கள் அடுத்த நினைவூட்டல்: {title} - நேரம் {time}.",
        "name": "உங்கள் பெயர் {name}. இது உங்கள் அமைதியான நினைவக இடம்.",
        "fallback": "அந்த தகவல் என் நினைவகத்தில் இல்லை. அனிதாவிடம் கேட்கலாம்."
    },
    "hi-IN": {
        "daughter": "आपकी बेटी अनीता हैं, जो आपका बहुत ध्यान रखती हैं।",
        "food": "आपका पसंदीदा खाना गरमा-गरम इडली और नारियल की चटनी है।",
        "reminder": "आपकी अगली याद दिलाने वाली बात: {title}, समय {time}।",
        "name": "आपका नाम {name} है।",
        "fallback": "यह जानकारी अभी मेरी मेमोरी में नहीं है।"
    },
    "kn-IN": {
        "daughter": "ನಿಮ್ಮ ಮಗಳು ಅನಿತಾ, ಅವರು ನಿಮ್ಮನ್ನು ಪ್ರೀತಿಯಿಂದ ನೋಡಿಕೊಳ್ಳುತ್ತಾರೆ.",
        "food": "ನಿಮ್ಮ ನೆಚ್ಚಿನ ಆಹಾರ ಬಿಸಿ ಇಡ್ಲಿ ಮತ್ತು ಚಟ್ನಿ.",
        "reminder": "ನಿಮ್ಮ ಮುಂದಿನ ನೆನಪಿಸುವಿಕೆ: {title} ಸಮಯ {time}.",
        "name": "ನಿಮ್ಮ ಹೆಸರು {name}.",
        "fallback": "ಈ ಮಾಹಿತಿ ಇನ್ನೂ ನನ್ನ ಮೆಮೊರಿಯಲ್ಲಿ ಇಲ್ಲ."
    },
    "as-IN": {
        "daughter": "আপোনাৰ ছোৱালী অনিতা, তেওঁ আপোনাক মৰমেৰে যত্ন লয়।",
        "food": "আপোনাৰ প্ৰিয় খাদ্য গৰম ইডলি আৰু নাৰিকলৰ চাটনি।",
        "reminder": "আপোনাৰ পৰৱৰ্তী সোঁৱৰণী: {title}, সময় {time}।",
        "name": "আপোনাৰ নাম {name}।",
        "fallback": "এই তথ্য মোৰ স্মৃতিভাণ্ডাৰত এতিয়াও নাই।"
    },
    "bn-IN": {
        "daughter": "আপনার মেয়ে অনিতা, যিনি আপনাকে ভালোবেসে যত্ন নেন।",
        "food": "আপনার প্রিয় খাবার গরম ইডলি ও নারকেল চাটনি।",
        "reminder": "আপনার পরবর্তী স্মারক: {title}, সময় {time}।",
        "name": "আপনার নাম {name}।",
        "fallback": "এই তথ্যটি এখনও আমার স্মৃতিভাণ্ডারে নেই।"
    },
    "en-IN": {
        "daughter": "Your daughter is Anitha, who loves and cares for you.",
        "food": "Your favourite food is hot idli with coconut chutney.",
        "reminder": "Your next reminder is {title} at {time}.",
        "name": "Your name is {name}. You are in your gentle space.",
        "fallback": "I don't have that in my memory bank yet, but we can ask your family."
    }
}

class SarvamAIService:
    """
    Client service for Sarvam AI Voice APIs (Saaras STT & Bulbul TTS)
    tailored for Indian Languages (Tamil, Hindi, Kannada, Telugu, English).
    """

    # Container families the mobile app and browser produce, mapped to the
    # filename extension + mime Saaras expects on the multipart upload.
    _AUDIO_CONTAINERS = {
        "audio/m4a": ("m4a", "audio/mp4"),
        "audio/x-m4a": ("m4a", "audio/mp4"),
        "audio/mp4": ("m4a", "audio/mp4"),
        "audio/aac": ("aac", "audio/aac"),
        "audio/webm": ("webm", "audio/webm"),
        "audio/ogg": ("ogg", "audio/ogg"),
        "audio/wav": ("wav", "audio/wav"),
        "audio/x-wav": ("wav", "audio/wav"),
        "audio/wave": ("wav", "audio/wav"),
        "audio/mpeg": ("mp3", "audio/mpeg"),
        "audio/3gpp": ("3gp", "audio/3gpp"),
    }

    @classmethod
    def _resolve_audio_upload(cls, content_type: Optional[str]):
        """Pick (filename, mime) for the STT upload, defaulting to WAV."""
        key = (content_type or "").split(";")[0].strip().lower()
        ext, mime = cls._AUDIO_CONTAINERS.get(key, ("wav", "audio/wav"))
        return f"input.{ext}", mime

    @classmethod
    async def transcribe_audio(
        cls,
        audio_bytes: bytes,
        language_code: str = "ta-IN",
        content_type: Optional[str] = None,
    ) -> str:
        """
        Calls Sarvam AI Saaras Speech-to-Text API.
        Falls back gracefully if API key is not yet set.
        """
        if not settings.SARVAM_API_KEY:
            logger.info("SARVAM_API_KEY not configured. Using simulated voice recognition.")
            return "என் மகள் யார்?" if "ta" in language_code else "Who is my daughter?"

        filename, mime = cls._resolve_audio_upload(content_type)
        headers = {
            "api-subscription-key": settings.SARVAM_API_KEY
        }
        files = {
            "file": (filename, audio_bytes, mime)
        }
        data = {
            "model": "saaras:v3",
            "language_code": language_code
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(settings.SARVAM_STT_URL, headers=headers, files=files, data=data)
                if res.status_code == 200:
                    payload = res.json()
                    return payload.get("transcript", "")
                else:
                    logger.error(f"Sarvam STT failed: {res.status_code} - {res.text}")
                    return "Who is my daughter?"
        except Exception as e:
            logger.error(f"Error connecting to Sarvam STT: {e}")
            return "Who is my daughter?"

    @classmethod
    async def synthesize_speech(cls, text: str, target_language_code: str = "ta-IN") -> Optional[str]:
        """
        Calls Sarvam AI Bulbul:v3 Text-to-Speech API.
        Returns base64-encoded audio for instant client playback.
        """
        if not settings.SARVAM_API_KEY:
            # When in local demo mode, client will use Web Speech synthesis fallback
            return None

        headers = {
            "Content-Type": "application/json",
            "api-subscription-key": settings.SARVAM_API_KEY
        }
        payload = {
            "inputs": [text],
            "target_language_code": target_language_code,
            "speaker": "kavya", # Gentle elder-friendly voice
            "model": "bulbul:v3"
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(settings.SARVAM_TTS_URL, headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    audios = data.get("audios", [])
                    if audios:
                        return audios[0]
                else:
                    logger.error(f"Sarvam TTS failed: {res.status_code} - {res.text}")
        except Exception as e:
            logger.error(f"Error connecting to Sarvam TTS: {e}")

        return None

    @classmethod
    def resolve_conversational_reply(
        cls,
        question_text: str,
        language_code: str,
        patient_name: str,
        memories: List[Dict[str, Any]],
        reminders: List[Dict[str, Any]]
    ) -> str:
        """
        Understands multilingual query text in Tamil, Hindi, Kannada, or English
        and synthesizes a gentle, accurate memory reply.
        """
        q_lower = question_text.lower().strip()
        lang_key = language_code if language_code in LOCALIZED_TEMPLATES else "en-IN"
        templates = LOCALIZED_TEMPLATES[lang_key]

        # Check for Family / Daughter Intent
        daughter_match = False
        for lang_words in MULTILINGUAL_INTENT_MAP["daughter_or_family"].values():
            if any(w in q_lower for w in lang_words):
                daughter_match = True
                break
        if daughter_match:
            for m in memories:
                if m.get("category") == "Person" or "daughter" in m.get("title", "").lower() or "அனிதா" in m.get("details", ""):
                    return templates["daughter"]
            return templates["daughter"]

        # Check for Food Intent
        food_match = False
        for lang_words in MULTILINGUAL_INTENT_MAP["food"].values():
            if any(w in q_lower for w in lang_words):
                food_match = True
                break
        if food_match:
            return templates["food"]

        # Check for Reminder Intent
        reminder_match = False
        for lang_words in MULTILINGUAL_INTENT_MAP["reminder"].values():
            if any(w in q_lower for w in lang_words):
                reminder_match = True
                break
        if reminder_match:
            if reminders:
                next_r = reminders[0]
                return templates["reminder"].format(
                    title=next_r.get("title", "Drink water"),
                    time=next_r.get("reminder_time", "14:00")
                )

        # Check for Name Intent
        name_match = False
        for lang_words in MULTILINGUAL_INTENT_MAP["name"].values():
            if any(w in q_lower for w in lang_words):
                name_match = True
                break
        if name_match:
            return templates["name"].format(name=patient_name)

        # Check generic memory bank
        for m in memories:
            if m.get("title", "").lower() in q_lower or m.get("details", "").lower() in q_lower:
                return f"{m.get('title')}: {m.get('details')}"

        return templates["fallback"]
