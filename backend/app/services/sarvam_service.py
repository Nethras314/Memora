import httpx
import logging
import base64
from typing import Optional, Dict, Any, List, Tuple
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
    },
    "greeting": {
        "en": ["hello", "good morning", "good afternoon", "good evening", "namaste", "vanakkam", "namaskar"],
        "ta": ["வணக்கம்", "காலை வணக்கம்", "மாலை வணக்கம்"],
        "hi": ["नमस्ते", "नमस्कार", "सुप्रभात", "शुभ संध्या"],
        "kn": ["ನಮಸ್ಕಾರ", "ಶುಭೋದಯ", "ಶುಭ ಸಂಜೆ"],
        "as": ["নমস্কাৰ", "শুভ ৰাতিপুৱা", "শুভ সন্ধিয়া"],
        "bn": ["নমস্কার", "শুভ সকাল", "শুভ সন্ধ্যা"]
    },
    "how_are_you": {
        "en": ["how are you", "how do you feel", "are you okay", "are you ok"],
        "ta": ["எப்படி இருக்கிறாய்", "நீ எப்படி", "எப்படி உள்ளது"],
        "hi": ["कैसे हो", "कैसी हो", "आप कैसे हैं", "कैसे हैं"],
        "kn": ["ಹೇಗಿದ್ದೀರಿ", "ಹೇಗಿದೆ"],
        "as": ["কেনে আছ", "আপুনি কেনে আছে"],
        "bn": ["কেমন আছেন", "কেমন আছো"]
    },
    "who_are_you": {
        "en": ["who are you", "what is your name", "what's your name", "your name"],
        "ta": ["நீ யார்", "உன் பெயர்", "உங்கள் பெயர் என்ன"],
        "hi": ["तुम कौन हो", "आप कौन हैं", "तुम्हारा नाम", "आपका नाम"],
        "kn": ["ನೀವು ಯಾರು", "ನಿಮ್ಮ ಹೆಸರು"],
        "as": ["আপুনি কোন", "আপোনাৰ নাম"],
        "bn": ["তুমি কে", "আপনি কে", "আপনার নাম"]
    },
    "comfort": {
        "en": ["lonely", "alone", "i am sad", "i'm sad", "i miss", "afraid", "scared", "worried", "tired", "unhappy", "crying"],
        "ta": ["தனிமை", "அழுகை", "பயம்", "கவலை", "சோகம்", "களைப்பு"],
        "hi": ["अकेला", "अकेली", "उदास", "डर", "चिंता", "थका"],
        "kn": ["ಒಂಟಿ", "ಭಯ", "ಚಿಂತೆ", "ದುಃಖ"],
        "as": ["অকলশৰীয়া", "ভয়", "চিন্তা", "দুখ"],
        "bn": ["একা", "ভয়", "চিন্তা", "দুঃখ"]
    },
    "thanks": {
        "en": ["thank", "thanks", "thank you", "love you", "i am fine", "i'm fine", "i am good"],
        "ta": ["நன்றி", "அன்பு"],
        "hi": ["धन्यवाद", "शुक्रिया", "प्यार"],
        "kn": ["ಧನ್ಯವಾದ", "ಪ್ರೀತಿ"],
        "as": ["ধন্যবাদ", "মৰম"],
        "bn": ["ধন্যবাদ", "ভালোবাসা"]
    },
    "orientation": {
        "en": ["what day", "what's the day", "which day", "what date", "what time is it", "what is the time", "what is today", "what's today"],
        "ta": ["இன்று என்ன தேதி", "என்ன நாள்", "நேரம் என்ன"],
        "hi": ["आज कौन सा दिन", "कौन सा दिन", "तारीख", "क्या समय"],
        "kn": ["ಇಂದು ಯಾವ ದಿನ", "ಸಮಯ ಎಷ್ಟು"],
        "as": ["আজি কি দিন", "সময় কি"],
        "bn": ["আজ কি দিন", "সময় কি"]
    }
}

# Which companion reaction each intent's reply should trigger on the client.
INTENT_MOOD = {
    "greeting": "happy",
    "how_are_you": "encourage",
    "who_are_you": "neutral",
    "comfort": "encourage",
    "thanks": "happy",
    "orientation": "neutral",
    "daughter_or_family": "happy",
    "food": "happy",
    "reminder": "neutral",
    "name": "happy",
    "memory": "happy",
    "fallback": "neutral",
}

LOCALIZED_TEMPLATES = {
    "ta-IN": {
        "daughter": "உங்கள் மகள் அனிதா, அவர் உங்களை அன்போடு கவனித்துக் கொள்கிறார்.",
        "food": "உங்களுக்கு மிகவும் பிடித்த உணவு சூடான இட்லி மற்றும் தேங்காய் சட்னி.",
        "reminder": "உங்கள் அடுத்த நினைவூட்டல்: {title} - நேரம் {time}.",
        "name": "உங்கள் பெயர் {name}. இது உங்கள் அமைதியான நினைவக இடம்.",
        "fallback": "அந்த தகவல் என் நினைவகத்தில் இல்லை. அனிதாவிடம் கேட்கலாம்.",
        "greeting": "வணக்கம்! உங்களுடன் இருப்பது மகிழ்ச்சி. இன்று எப்படி உணர்கிறீர்கள்?",
        "how_are_you": "நான் எப்போதும் உங்களுடன் அமைதியாக இருக்கிறேன். நீங்கள் எப்படி?",
        "who_are_you": "நான் MEMORA, உங்கள் மென்மையான துணை. உங்கள் நினைவுகளையும் நினைவூட்டல்களையும் அருகில் வைத்திருக்கிறேன்.",
        "comfort": "நீங்கள் தனியாக இல்லை, {name}. நான் இங்கே உங்களுடன் இருக்கிறேன், உங்கள் குடும்பம் உங்களை நேசிக்கிறது.",
        "thanks": "இது என் இதயத்தை மகிழ்விக்கிறது. உங்களுடன் இருப்பதில் மகிழ்ச்சி.",
        "orientation": "இன்று ஒரு அமைதியான நாள். மெதுவாக, ஒவ்வொரு படியாக முன்னேறுங்கள்."
    },
    "hi-IN": {
        "daughter": "आपकी बेटी अनीता हैं, जो आपका बहुत ध्यान रखती हैं।",
        "food": "आपका पसंदीदा खाना गरमा-गरम इडली और नारियल की चटनी है।",
        "reminder": "आपकी अगली याद दिलाने वाली बात: {title}, समय {time}।",
        "name": "आपका नाम {name} है।",
        "fallback": "यह जानकारी अभी मेरी मेमोरी में नहीं है।",
        "greeting": "नमस्ते! आपके साथ रहकर अच्छा लगता है। आज आप कैसा महसूस कर रहे हैं?",
        "how_are_you": "मैं हमेशा आपके साथ हूँ, शांत और सुनने के लिए तैयार। और आप?",
        "who_are_you": "मैं MEMORA हूँ, आपका कोमल साथी। मैं आपकी यादें और अनुस्मारक पास रखता हूँ।",
        "comfort": "आप अकेले नहीं हैं, {name}। मैं यहीं आपके साथ हूँ, और आपका परिवार आपका खयाल रखता है।",
        "thanks": "यह मेरा दिल खुश कर देता है। आपके साथ रहकर खुशी होती है।",
        "orientation": "आज एक शांत दिन है। धीरे-धीरे, एक-एक कदम चलें।"
    },
    "kn-IN": {
        "daughter": "ನಿಮ್ಮ ಮಗಳು ಅನಿತಾ, ಅವರು ನಿಮ್ಮನ್ನು ಪ್ರೀತಿಯಿಂದ ನೋಡಿಕೊಳ್ಳುತ್ತಾರೆ.",
        "food": "ನಿಮ್ಮ ನೆಚ್ಚಿನ ಆಹಾರ ಬಿಸಿ ಇಡ್ಲಿ ಮತ್ತು ಚಟ್ನಿ.",
        "reminder": "ನಿಮ್ಮ ಮುಂದಿನ ನೆನಪಿಸುವಿಕೆ: {title} ಸಮಯ {time}.",
        "name": "ನಿಮ್ಮ ಹೆಸರು {name}.",
        "fallback": "ಈ ಮಾಹಿತಿ ಇನ್ನೂ ನನ್ನ ಮೆಮೊರಿಯಲ್ಲಿ ಇಲ್ಲ.",
        "greeting": "ನಮಸ್ಕಾರ! ನಿಮ್ಮೊಂದಿಗೆ ಇರಲು ಸಂತೋಷ. ಇಂದು ಹೇಗೆ ಅನಿಸುತ್ತಿದೆ?",
        "how_are_you": "ನಾನು ಸದಾ ನಿಮ್ಮೊಂದಿಗೆ ಶಾಂತವಾಗಿದ್ದೇನೆ. ನೀವು ಹೇಗಿದ್ದೀರಿ?",
        "who_are_you": "ನಾನು MEMORA, ನಿಮ್ಮ ಮೃದು ಸಂಗಾತಿ. ನಿಮ್ಮ ನೆನಪುಗಳನ್ನು ಹತ್ತಿರ ಇಟ್ಟುಕೊಳ್ಳುತ್ತೇನೆ.",
        "comfort": "ನೀವು ಒಂಟಿಯಲ್ಲ, {name}. ನಾನು ಇಲ್ಲೇ ನಿಮ್ಮೊಂದಿಗಿದ್ದೇನೆ, ನಿಮ್ಮ ಕುಟುಂಬ ನಿಮ್ಮನ್ನು ಪ್ರೀತಿಸುತ್ತದೆ.",
        "thanks": "ಇದು ನನ್ನ ಹೃದಯವನ್ನು ಸಂತೋಷಪಡಿಸುತ್ತದೆ. ನಿಮ್ಮೊಂದಿಗೆ ಇರಲು ಸಂತೋಷ.",
        "orientation": "ಇಂದು ಶಾಂತ ದಿನ. ನಿಧಾನವಾಗಿ, ಒಂದೊಂದು ಹೆಜ್ಜೆಯಾಗಿ ಸಾಗಿ."
    },
    "as-IN": {
        "daughter": "আপোনাৰ ছোৱালী অনিতা, তেওঁ আপোনাক মৰমেৰে যত্ন লয়।",
        "food": "আপোনাৰ প্ৰিয় খাদ্য গৰম ইডলি আৰু নাৰিকলৰ চাটনি.",
        "reminder": "আপোনাৰ পৰৱৰ্তী সোঁৱৰণী: {title}, সময় {time}।",
        "name": "আপোনাৰ নাম {name}।",
        "fallback": "এই তথ্য মোৰ স্মৃতিভাণ্ডাৰত এতিয়াও নাই.",
        "greeting": "নমস্কাৰ! আপোনাৰ লগত থাকি ভাল লাগে। আজি আপুনি কেনে অনুভৱ কৰিছে?",
        "how_are_you": "মই সদায় আপোনাৰ লগত শান্তভাৱে আছোঁ। আপুনি কেনে আছে?",
        "who_are_you": "মই MEMORA, আপোনাৰ মৰমৰ সংগী। আপোনাৰ স্মৃতি ও সোঁৱৰণী ওচৰত ৰাখোঁ।",
        "comfort": "আপুনি অকলশৰীয়া নহয়, {name}। মই ইয়াতে আপোনাৰ লগত আছোঁ, আপোনাৰ পৰিয়ালে আপোনাক মৰম কৰে।",
        "thanks": "এইটোৱে মোৰ হৃদয় আনন্দিত কৰে। আপোনাৰ লগত থাকি ভাল পাওঁ।",
        "orientation": "আজি এটা শান্ত দিন। লাহে লাহে, এটা এটা খোজে আগবাঢ়ক।"
    },
    "bn-IN": {
        "daughter": "আপনার মেয়ে অনিতা, যিনি আপনাকে ভালোবেসে যত্ন নেন।",
        "food": "আপনার প্রিয় খাবার গরম ইডলি ও নারকেল চাটনি।",
        "reminder": "আপনার পরবর্তী স্মারক: {title}, সময় {time}।",
        "name": "আপনার নাম {name}।",
        "fallback": "এই তথ্যটি এখনও আমার স্মৃতিভাণ্ডারে নেই।",
        "greeting": "নমস্কার! আপনার সাথে থাকতে ভালো লাগে। আজ আপনি কেমন অনুভব করছেন?",
        "how_are_you": "আমি সবসময় আপনার সাথে শান্তভাবে আছি। আপনি কেমন আছেন?",
        "who_are_you": "আমি MEMORA, আপনার মৃদু সঙ্গী। আমি আপনার স্মৃতি ও স্মারক কাছে রাখি।",
        "comfort": "আপনি একা নন, {name}। আমি এখানেই আপনার সাথে আছি, আপনার পরিবার আপনাকে ভালোবাসে।",
        "thanks": "এটা আমার মন আনন্দিত করে। আপনার সাথে থাকতে ভালো লাগে।",
        "orientation": "আজ একটি শান্ত দিন। ধীরে ধীরে, এক ধাপ করে এগোন।"
    },
    "en-IN": {
        "daughter": "Your daughter is Anitha, who loves and cares for you.",
        "food": "Your favourite food is hot idli with coconut chutney.",
        "reminder": "Your next reminder is {title} at {time}.",
        "name": "Your name is {name}. You are in your gentle space.",
        "fallback": "I don't have that in my memory bank yet, but we can ask your family.",
        "greeting": "Hello! It's lovely to be with you. How are you feeling today?",
        "how_are_you": "I am always here with you, calm and listening. And you?",
        "who_are_you": "I am MEMORA, your gentle companion. I keep your memories and reminders close.",
        "comfort": "You are not alone, {name}. I am right here with you, and your family cares for you.",
        "thanks": "That warms my heart. I am happy to be here with you.",
        "orientation": "Today is a gentle day. Take it slowly, one calm step at a time."
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
    def _match_intent(cls, question_lower: str, intent: str) -> bool:
        for words in MULTILINGUAL_INTENT_MAP.get(intent, {}).values():
            if any(w in question_lower for w in words):
                return True
        return False

    @classmethod
    def resolve_conversational_reply(
        cls,
        question_text: str,
        language_code: str,
        patient_name: str,
        memories: List[Dict[str, Any]],
        reminders: List[Dict[str, Any]]
    ) -> str:
        """Backward-compatible wrapper returning only the reply text."""
        reply_text, _ = cls.resolve_conversational_reply_with_mood(
            question_text=question_text,
            language_code=language_code,
            patient_name=patient_name,
            memories=memories,
            reminders=reminders,
        )
        return reply_text

    @classmethod
    def resolve_conversational_reply_with_mood(
        cls,
        question_text: str,
        language_code: str,
        patient_name: str,
        memories: List[Dict[str, Any]],
        reminders: List[Dict[str, Any]]
    ) -> Tuple[str, str]:
        """
        Understands multilingual query text across the supported Indian languages
        and returns (reply_text, mood). `mood` drives the companion's reaction
        animation on the client (happy / encourage / neutral).
        """
        q_lower = (question_text or "").lower().strip()
        lang_key = language_code if language_code in LOCALIZED_TEMPLATES else "en-IN"
        templates = LOCALIZED_TEMPLATES[lang_key]

        def mood(intent: str) -> str:
            return INTENT_MOOD.get(intent, "neutral")

        if cls._match_intent(q_lower, "greeting"):
            return templates["greeting"], mood("greeting")
        if cls._match_intent(q_lower, "how_are_you"):
            return templates["how_are_you"], mood("how_are_you")
        if cls._match_intent(q_lower, "who_are_you"):
            return templates["who_are_you"], mood("who_are_you")
        if cls._match_intent(q_lower, "comfort"):
            return templates["comfort"].format(name=patient_name), mood("comfort")
        if cls._match_intent(q_lower, "thanks"):
            return templates["thanks"], mood("thanks")
        if cls._match_intent(q_lower, "orientation"):
            return templates["orientation"], mood("orientation")
        if cls._match_intent(q_lower, "daughter_or_family"):
            return templates["daughter"], mood("daughter_or_family")
        if cls._match_intent(q_lower, "food"):
            return templates["food"], mood("food")
        if cls._match_intent(q_lower, "reminder"):
            if reminders:
                next_r = reminders[0]
                return templates["reminder"].format(
                    title=next_r.get("title", "Drink water"),
                    time=next_r.get("reminder_time", "14:00")
                ), mood("reminder")
            return templates["fallback"], "neutral"
        if cls._match_intent(q_lower, "name"):
            return templates["name"].format(name=patient_name), mood("name")

        for m in memories:
            title = (m.get("title") or "").lower()
            details = (m.get("details") or "").lower()
            if (title and title in q_lower) or (details and details in q_lower):
                return f"{m.get('title')}: {m.get('details')}", mood("memory")

        return templates["fallback"], mood("fallback")
