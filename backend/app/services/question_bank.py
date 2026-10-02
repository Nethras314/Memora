"""Localized, culturally-familiar question banks for patient cognitive games.

Content is intentionally simple and everyday (festivals, foods, family,
daily objects) to stay approachable for elderly users with cognitive
impairment. Each language has its own curated set; any missing language
falls back to English so the game never returns nothing.
"""

import random
from typing import Any, Dict, List

DEFAULT_LANGUAGE = "en-IN"

# ---------------------------------------------------------------------------
# General Knowledge / memory recall
# ---------------------------------------------------------------------------
GK_BANK: Dict[str, List[Dict[str, Any]]] = {
    "en-IN": [
        {"question": "Which festival is called the festival of lights?", "options": ["Diwali", "Pongal", "Onam"], "answer": "Diwali", "hint": "We light small lamps at home."},
        {"question": "Which fruit is yellow and curved?", "options": ["Banana", "Apple", "Grapes"], "answer": "Banana", "hint": "Monkeys love it."},
        {"question": "What do we drink when we are thirsty?", "options": ["Water", "Oil", "Salt"], "answer": "Water", "hint": "It is clear and cool."},
        {"question": "How many days are there in one week?", "options": ["Five", "Seven", "Ten"], "answer": "Seven", "hint": "Sunday to Saturday."},
        {"question": "Which animal says 'meow'?", "options": ["Dog", "Cat", "Cow"], "answer": "Cat", "hint": "It likes to sit by the window."},
        {"question": "What do we use to brush our teeth?", "options": ["Toothbrush", "Spoon", "Comb"], "answer": "Toothbrush", "hint": "We use it with paste."},
        {"question": "Which meal do we eat in the morning?", "options": ["Breakfast", "Dinner", "Snack"], "answer": "Breakfast", "hint": "It starts the day."},
        {"question": "What colour is a ripe tomato?", "options": ["Red", "Blue", "Green"], "answer": "Red", "hint": "It is round and used in curry."},
        {"question": "Which bird is known for talking?", "options": ["Parrot", "Crow", "Pigeon"], "answer": "Parrot", "hint": "It is bright green."},
        {"question": "What do we wear on our feet?", "options": ["Shoes", "Hat", "Gloves"], "answer": "Shoes", "hint": "They come in pairs."},
    ],
    "hi-IN": [
        {"question": "रोशनी के त्योहार को क्या कहते हैं?", "options": ["दिवाली", "पोंगल", "ओणम"], "answer": "दिवाली", "hint": "घर में दीये जलाते हैं।"},
        {"question": "कौन सा फल पीला और मुड़ा हुआ होता है?", "options": ["केला", "सेब", "अंगूर"], "answer": "केला", "hint": "बंदर इसे पसंद करते हैं।"},
        {"question": "प्यास लगने पर हम क्या पीते हैं?", "options": ["पानी", "तेल", "नमक"], "answer": "पानी", "hint": "यह साफ़ और ठंडा होता है।"},
        {"question": "एक सप्ताह में कितने दिन होते हैं?", "options": ["पाँच", "सात", "दस"], "answer": "सात", "hint": "रविवार से शनिवार।"},
        {"question": "कौन सा जानवर 'म्याऊँ' करता है?", "options": ["कुत्ता", "बिल्ली", "गाय"], "answer": "बिल्ली", "hint": "यह खिड़की के पास बैठती है।"},
        {"question": "दाँत साफ़ करने के लिए क्या इस्तेमाल करते हैं?", "options": ["टूथब्रश", "चम्मच", "कंघी"], "answer": "टूथब्रश", "hint": "इसे पेस्ट के साथ इस्तेमाल करते हैं।"},
        {"question": "सुबह हम कौन सा खाना खाते हैं?", "options": ["नाश्ता", "रात का खाना", "नमकीन"], "answer": "नाश्ता", "hint": "इससे दिन शुरू होता है।"},
        {"question": "पका हुआ टमाटर किस रंग का होता है?", "options": ["लाल", "नीला", "हरा"], "answer": "लाल", "hint": "यह गोल होता है।"},
    ],
    "ta-IN": [
        {"question": "விளக்குகளின் திருவிழா எது?", "options": ["தீபாவளி", "பொங்கல்", "ஓணம்"], "answer": "தீபாவளி", "hint": "வீட்டில் விளக்கு ஏற்றுவோம்."},
        {"question": "எந்த பழம் மஞ்சள் நிறமாகவும் வளைந்தும் இருக்கும்?", "options": ["வாழைப்பழம்", "ஆப்பிள்", "திராட்சை"], "answer": "வாழைப்பழம்", "hint": "குரங்குகள் விரும்பும்."},
        {"question": "தாகம் எடுக்கும்போது என்ன குடிப்போம்?", "options": ["தண்ணீர்", "எண்ணெய்", "உப்பு"], "answer": "தண்ணீர்", "hint": "தெளிவாகவும் குளிராகவும் இருக்கும்."},
        {"question": "ஒரு வாரத்தில் எத்தனை நாட்கள்?", "options": ["ஐந்து", "ஏழு", "பத்து"], "answer": "ஏழு", "hint": "ஞாயிறு முதல் சனி வரை."},
        {"question": "எந்த விலங்கு 'மியாவ்' என்கிறது?", "options": ["நாய்", "பூனை", "பசு"], "answer": "பூனை", "hint": "ஜன்னல் அருகே அமரும்."},
        {"question": "பல் துலக்க எதைப் பயன்படுத்துவோம்?", "options": ["பல் துலக்கி", "கரண்டி", "சீப்பு"], "answer": "பல் துலக்கி", "hint": "பேஸ்டுடன் பயன்படுத்துவோம்."},
        {"question": "காலையில் எந்த உணவு சாப்பிடுவோம்?", "options": ["காலை உணவு", "இரவு உணவு", "சிற்றுண்டி"], "answer": "காலை உணவு", "hint": "நாள் தொடங்குகிறது."},
        {"question": "பழுத்த தக்காளி எந்த நிறம்?", "options": ["சிவப்பு", "நீலம்", "பச்சை"], "answer": "சிவப்பு", "hint": "வட்டமாக இருக்கும்."},
    ],
    "bn-IN": [
        {"question": "আলোর উৎসব কোনটি?", "options": ["দিওয়ালি", "পোঙ্গল", "ওণম"], "answer": "দিওয়ালি", "hint": "বাড়িতে প্রদীপ জ্বালাই।"},
        {"question": "কোন ফলটি হলুদ ও বাঁকানো?", "options": ["কলা", "আপেল", "আঙুর"], "answer": "কলা", "hint": "বানর খুব পছন্দ করে।"},
        {"question": "তেষ্টা পেলে আমরা কী খাই?", "options": ["জল", "তেল", "লবণ"], "answer": "জল", "hint": "এটি পরিষ্কার ও ঠান্ডা।"},
        {"question": "এক সপ্তাহে কত দিন?", "options": ["পাঁচ", "সাত", "দশ"], "answer": "সাত", "hint": "রবিবার থেকে শনিবার।"},
        {"question": "কোন প্রাণী 'মিউ' করে?", "options": ["কুকুর", "বিড়াল", "গরু"], "answer": "বিড়াল", "hint": "জানালার পাশে বসে।"},
        {"question": "দাঁত মাজার জন্য কী ব্যবহার করি?", "options": ["টুথব্রাশ", "চামচ", "চিরুনি"], "answer": "টুথব্রাশ", "hint": "পেস্টের সাথে ব্যবহার করি।"},
        {"question": "সকালে আমরা কোন খাবার খাই?", "options": ["সকালের নাশতা", "রাতের খাবার", "নাস্তা"], "answer": "সকালের নাশতা", "hint": "দিন শুরু হয় এটি দিয়ে।"},
        {"question": "পাকা টমেটোর রং কী?", "options": ["লাল", "নীল", "সবুজ"], "answer": "লাল", "hint": "এটি গোল।"},
    ],
    "as-IN": [
        {"question": "পোহৰৰ উৎসৱ কোনটো?", "options": ["দীপাৱলী", "পোংগল", "ওণম"], "answer": "দীপাৱলী", "hint": "ঘৰত চাকি জ্বলাওঁ।"},
        {"question": "কোনটো ফল হালধীয়া আৰু বেঁকা?", "options": ["কল", "আপেল", "আঙুৰ"], "answer": "কল", "hint": "বান্দৰে ভাল পায়।"},
        {"question": "পিয়াহ লাগিলে আমি কি খাওঁ?", "options": ["পানী", "তেল", "নিমখ"], "answer": "পানী", "hint": "ই চাফা আৰু ঠাণ্ডা।"},
        {"question": "এটা সপ্তাহত কিমান দিন?", "options": ["পাঁচ", "সাত", "দহ"], "answer": "সাত", "hint": "দেওবাৰৰ পৰা শনিবাৰ।"},
        {"question": "কোনটো জন্তুৱে 'মিঞাও' মাতে?", "options": ["কুকুৰ", "মেকুৰী", "গৰু"], "answer": "মেকুৰী", "hint": "খিৰিকীৰ কাষত বহে।"},
        {"question": "দাঁত ঘঁহিবলৈ কি ব্যৱহাৰ কৰোঁ?", "options": ["টুথব্ৰাছ", "চামুচ", "ফণি"], "answer": "টুথব্ৰাছ", "hint": "পেষ্টৰ সৈতে ব্যৱহাৰ কৰোঁ।"},
        {"question": "ৰাতিপুৱা আমি কোনটো আহাৰ খাওঁ?", "options": ["ৰাতিপুৱাৰ আহাৰ", "ৰাতিৰ আহাৰ", "জলপান"], "answer": "ৰাতিপুৱাৰ আহাৰ", "hint": "দিনটো ইয়াৰে আৰম্ভ হয়।"},
        {"question": "পকা বিলাহীৰ ৰং কি?", "options": ["ৰঙা", "নীলা", "সেউজীয়া"], "answer": "ৰঙা", "hint": "ই ঘূৰণীয়া।"},
    ],
}

# ---------------------------------------------------------------------------
# Attention / odd-one-out
# ---------------------------------------------------------------------------
ATTENTION_BANK: Dict[str, List[Dict[str, Any]]] = {
    "en-IN": [
        {"question": "Which one is different from the others?", "options": ["🍎 Apple", "🍌 Banana", "🚗 Car"], "answer": "🚗 Car", "explanation": "Car is a vehicle, the others are fruits."},
        {"question": "Which one does not belong here?", "options": ["🐶 Dog", "🐱 Cat", "🪑 Chair"], "answer": "🪑 Chair", "explanation": "Chair is furniture, the others are animals."},
        {"question": "Spot the odd item:", "options": ["☕ Tea Cup", "🥄 Spoon", "🌻 Flower"], "answer": "🌻 Flower", "explanation": "Flower is a plant, the others are kitchen items."},
        {"question": "Which one is not food?", "options": ["🍚 Rice", "🥖 Bread", "👟 Shoe"], "answer": "👟 Shoe", "explanation": "Shoe is clothing, the others are food."},
        {"question": "Which one cannot fly?", "options": ["🦅 Eagle", "🐘 Elephant", "🦜 Parrot"], "answer": "🐘 Elephant", "explanation": "Elephant walks, the others are birds."},
        {"question": "Which one is not for writing?", "options": ["✏️ Pencil", "🖊️ Pen", "🍫 Chocolate"], "answer": "🍫 Chocolate", "explanation": "Chocolate is food, the others write."},
    ],
    "hi-IN": [
        {"question": "इनमें से कौन अलग है?", "options": ["🍎 सेब", "🍌 केला", "🚗 कार"], "answer": "🚗 कार", "explanation": "कार वाहन है, बाकी फल हैं।"},
        {"question": "कौन यहाँ नहीं बैठता?", "options": ["🐶 कुत्ता", "🐱 बिल्ली", "🪑 कुर्सी"], "answer": "🪑 कुर्सी", "explanation": "कुर्सी फर्नीचर है, बाकी जानवर हैं।"},
        {"question": "अलग वस्तु पहचानें:", "options": ["☕ चाय का कप", "🥄 चम्मच", "🌻 फूल"], "answer": "🌻 फूल", "explanation": "फूल पौधा है, बाकी रसोई की चीज़ें हैं।"},
        {"question": "कौन खाना नहीं है?", "options": ["🍚 चावल", "🥖 रोटी", "👟 जूता"], "answer": "👟 जूता", "explanation": "जूता पहनने का है, बाकी खाना है।"},
        {"question": "कौन उड़ नहीं सकता?", "options": ["🦅 चील", "🐘 हाथी", "🦜 तोता"], "answer": "🐘 हाथी", "explanation": "हाथी चलता है, बाकी पक्षी हैं।"},
        {"question": "कौन लिखने के लिए नहीं है?", "options": ["✏️ पेंसिल", "🖊️ पेन", "🍫 चॉकलेट"], "answer": "🍫 चॉकलेट", "explanation": "चॉकलेट खाना है, बाकी लिखते हैं।"},
    ],
    "ta-IN": [
        {"question": "இவற்றில் எது வேறுபட்டது?", "options": ["🍎 ஆப்பிள்", "🍌 வாழைப்பழம்", "🚗 கார்"], "answer": "🚗 கார்", "explanation": "கார் வாகனம், மற்றவை பழங்கள்."},
        {"question": "இங்கு எது சேராதது?", "options": ["🐶 நாய்", "🐱 பூனை", "🪑 நாற்காலி"], "answer": "🪑 நாற்காலி", "explanation": "நாற்காலி தளவாடம், மற்றவை விலங்குகள்."},
        {"question": "மாறுபட்ட பொருளைக் கண்டறி:", "options": ["☕ தேநீர் கோப்பை", "🥄 கரண்டி", "🌻 பூ"], "answer": "🌻 பூ", "explanation": "பூ செடி, மற்றவை சமையலறைப் பொருட்கள்."},
        {"question": "எது உணவு அல்ல?", "options": ["🍚 சாதம்", "🥖 ரொட்டி", "👟 காலணி"], "answer": "👟 காலணி", "explanation": "காலணி அணிவது, மற்றவை உணவு."},
        {"question": "எதால் பறக்க முடியாது?", "options": ["🦅 கழுகு", "🐘 யானை", "🦜 கிளி"], "answer": "🐘 யானை", "explanation": "யானை நடக்கும், மற்றவை பறவைகள்."},
        {"question": "எழுதுவதற்கு எது இல்லை?", "options": ["✏️ பென்சில்", "🖊️ பேனா", "🍫 சாக்லேட்"], "answer": "🍫 சாக்லேட்", "explanation": "சாக்லேட் உணவு, மற்றவை எழுதும்."},
    ],
    "bn-IN": [
        {"question": "এদের মধ্যে কোনটি আলাদা?", "options": ["🍎 আপেল", "🍌 কলা", "🚗 গাড়ি"], "answer": "🚗 গাড়ি", "explanation": "গাড়ি যানবাহন, বাকিগুলো ফল।"},
        {"question": "এখানে কোনটি মানায় না?", "options": ["🐶 কুকুর", "🐱 বিড়াল", "🪑 চেয়ার"], "answer": "🪑 চেয়ার", "explanation": "চেয়ার আসবাব, বাকিগুলো প্রাণী।"},
        {"question": "আলাদা জিনিসটি খুঁজুন:", "options": ["☕ চায়ের কাপ", "🥄 চামচ", "🌻 ফুল"], "answer": "🌻 ফুল", "explanation": "ফুল গাছ, বাকিগুলো রান্নাঘরের জিনিস।"},
        {"question": "কোনটি খাবার নয়?", "options": ["🍚 ভাত", "🥖 রুটি", "👟 জুতো"], "answer": "👟 জুতো", "explanation": "জুতো পরার জিনিস, বাকিগুলো খাবার।"},
        {"question": "কোনটি উড়তে পারে না?", "options": ["🦅 ঈগল", "🐘 হাতি", "🦜 টিয়া"], "answer": "🐘 হাতি", "explanation": "হাতি হাঁটে, বাকিগুলো পাখি।"},
        {"question": "কোনটি লেখার জন্য নয়?", "options": ["✏️ পেনসিল", "🖊️ কলম", "🍫 চকোলেট"], "answer": "🍫 চকোলেট", "explanation": "চকোলেট খাবার, বাকিগুলো লেখে।"},
    ],
    "as-IN": [
        {"question": "ইয়াৰ ভিতৰত কোনটো বেলেগ?", "options": ["🍎 আপেল", "🍌 কল", "🚗 গাড়ী"], "answer": "🚗 গাড়ী", "explanation": "গাড়ী বাহন, বাকীবোৰ ফল।"},
        {"question": "ইয়াত কোনটো নাখাটে?", "options": ["🐶 কুকুৰ", "🐱 মেকুৰী", "🪑 চকী"], "answer": "🪑 চকী", "explanation": "চকী আসবাব, বাকীবোৰ জন্তু।"},
        {"question": "বেলেগ বস্তুটো বিচাৰক:", "options": ["☕ চাহৰ কাপ", "🥄 চামুচ", "🌻 ফুল"], "answer": "🌻 ফুল", "explanation": "ফুল গছ, বাকীবোৰ পাকঘৰৰ বস্তু।"},
        {"question": "কোনটো খাদ্য নহয়?", "options": ["🍚 ভাত", "🥖 ৰুটি", "👟 জোতা"], "answer": "👟 জোতা", "explanation": "জোতা পিন্ধাৰ বস্তু, বাকীবোৰ খাদ্য।"},
        {"question": "কোনটো উৰিব নোৱাৰে?", "options": ["🦅 ঈগল", "🐘 হাতী", "🦜 ভাটৌ"], "answer": "🐘 হাতী", "explanation": "হাতী খোজ কাঢ়ে, বাকীবোৰ চৰাই।"},
        {"question": "কোনটো লিখিবলৈ নহয়?", "options": ["✏️ পেঞ্চিল", "🖊️ কলম", "🍫 চকোলেট"], "answer": "🍫 চকোলেট", "explanation": "চকোলেট খাদ্য, বাকীবোৰে লিখে।"},
    ],
}


def get_gk_question(language_code: str) -> Dict[str, Any]:
    bank = GK_BANK.get(language_code) or GK_BANK[DEFAULT_LANGUAGE]
    return random.choice(bank)


def get_attention_question(language_code: str) -> Dict[str, Any]:
    bank = ATTENTION_BANK.get(language_code) or ATTENTION_BANK[DEFAULT_LANGUAGE]
    return random.choice(bank)
