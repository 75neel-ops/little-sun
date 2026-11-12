from __future__ import annotations

import hashlib
import io
import json
import os
import random
import re
import time
from pathlib import Path
from typing import Any

import streamlit as st
import streamlit.components.v1 as components

try:
    from google import genai
except ImportError:
    genai = None

try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None

MODEL = "gemini-3.5-flash-lite"
APP_NAME = "Little Moon"
PWA_INSTALL_URL = "https://75neel-ops.github.io/deepbluemonkey/little-moon/"

SUBJECTS_BY_CLASS = {
    1: ["English", "Bengali", "Mathematics", "Environmental Studies", "Computer Studies", "Art Education"],
    2: ["English", "Bengali", "Mathematics", "Environmental Studies", "Computer Studies", "Art Education"],
    3: ["English", "Bengali", "Mathematics", "The World Around Us (EVS)", "Computer Studies", "Computational Thinking & AI", "Art Education"],
    4: ["English", "Bengali", "Mathematics", "The World Around Us (EVS)", "Computer Studies", "Computational Thinking & AI", "Art Education"],
    5: ["English", "Bengali", "Mathematics", "The World Around Us (EVS)", "Computer Studies", "Computational Thinking & AI", "Art Education"],
    6: ["English", "Bengali", "Mathematics", "Science", "Social Science", "Computer Studies", "Computational Thinking & AI", "Art Education", "Physical Education & Well-being", "Work Education"],
    7: ["English", "Bengali", "Mathematics", "Science", "Social Science", "Computer Studies", "Computational Thinking & AI", "Art Education", "Physical Education & Well-being", "Work Education"],
    8: ["English", "Bengali", "Mathematics", "Science", "Social Science", "Computer Studies", "Computational Thinking & AI", "Art Education", "Physical Education & Well-being", "Work Education"],
}

# Broad chapter suggestions for common CBSE/NCERT school topics. Schools choose
# different textbooks, so students can always enter their own chapter below.
CHAPTERS = {
    "English": {
        1: ["Alphabet and sounds", "My family", "At school", "Animals around us", "Stories and poems", "Naming words", "Action words", "Simple sentences"],
        2: ["Reading short stories", "Poems and rhymes", "My neighbourhood", "Nouns and pronouns", "Doing words", "Describing words", "Simple tenses", "Sentence writing"],
        3: ["Stories and characters", "Poems and rhythm", "Comprehension", "Nouns and pronouns", "Verbs and tenses", "Adjectives and adverbs", "Punctuation", "Paragraph writing"],
        4: ["Fiction and fables", "Poetry", "Comprehension", "Parts of speech", "Tenses", "Direct and indirect speech", "Punctuation", "Letter writing"],
        5: ["Stories and biographies", "Poetry", "Comprehension", "Nouns and pronouns", "Tenses and verbs", "Prepositions and conjunctions", "Reported speech", "Essay writing"],
        6: ["Prose and short stories", "Poetry", "Drama", "Comprehension", "Parts of speech", "Tenses", "Active and passive voice", "Composition writing"],
        7: ["Prose and short stories", "Poetry", "Drama", "Comprehension", "Clauses and phrases", "Tenses and voice", "Reported speech", "Essay and letter writing"],
        8: ["Prose and short stories", "Poetry", "Drama", "Comprehension", "Sentence structure", "Clauses", "Voice and narration", "Essays and formal letters"],
    },
    "Bengali": {
        1: ["বর্ণপরিচয়", "স্বরবর্ণ ও ব্যঞ্জনবর্ণ", "সহজ শব্দ", "ছোট গল্প", "ছড়া ও কবিতা", "শব্দ দিয়ে বাক্য"],
        2: ["শব্দ ও বাক্য", "ছোট গল্প", "ছড়া ও কবিতা", "বিশেষ্য", "ক্রিয়াপদ", "অনুচ্ছেদ লেখা"],
        3: ["গল্প পাঠ", "কবিতা পাঠ", "শব্দার্থ", "বিশেষ্য ও সর্বনাম", "ক্রিয়াপদ ও কাল", "অনুচ্ছেদ রচনা"],
        4: ["গল্প ও রূপকথা", "কবিতা", "বোধপরীক্ষণ", "পদ পরিচয়", "লিঙ্গ ও বচন", "চিঠি ও অনুচ্ছেদ"],
        5: ["গল্প ও জীবনী", "কবিতা", "বোধপরীক্ষণ", "সমার্থক ও বিপরীত শব্দ", "কারক ও বিভক্তি", "রচনা ও পত্র"],
        6: ["গদ্য", "পদ্য", "নাটক", "বোধপরীক্ষণ", "সন্ধি ও সমাস", "কারক ও বিভক্তি", "প্রবন্ধ ও পত্র"],
        7: ["গদ্য ও ছোটগল্প", "কবিতা", "নাটক", "বোধপরীক্ষণ", "বাক্য ও পদপরিচয়", "বাগধারা", "প্রবন্ধ রচনা"],
        8: ["গদ্য ও ছোটগল্প", "কবিতা", "নাটক", "বোধপরীক্ষণ", "সমাস ও প্রত্যয়", "বাচ্য ও বাক্যরূপ", "প্রবন্ধ ও প্রতিবেদন"],
    },
    "Mathematics": {
        1: ["Numbers to 100", "Addition", "Subtraction", "Shapes", "Patterns", "Length and weight", "Time", "Money"],
        2: ["Numbers to 1,000", "Addition and subtraction", "Multiplication", "Division", "Fractions", "Shapes and lines", "Measurement", "Time and money"],
        3: ["Large numbers", "Addition and subtraction", "Multiplication and division", "Fractions", "Shapes and symmetry", "Length, mass and capacity", "Time", "Money"],
        4: ["Place value and large numbers", "Four operations", "Factors and multiples", "Fractions", "Decimals", "Geometry", "Measurement", "Perimeter and area"],
        5: ["Large numbers and Roman numerals", "Factors and multiples", "Fractions", "Decimals", "Percentage", "Geometry", "Area and volume", "Data handling"],
        6: ["Natural numbers and whole numbers", "Integers", "Fractions and decimals", "Ratio and proportion", "Basic algebra", "Lines and angles", "Triangles and quadrilaterals", "Mensuration and data handling"],
        7: ["Integers and rational numbers", "Fractions and decimals", "Ratio and proportion", "Simple equations", "Lines and angles", "Triangles", "Percentage and profit and loss", "Perimeter, area and data handling"],
        8: ["Rational numbers", "Exponents and powers", "Algebraic expressions", "Linear equations", "Direct and inverse proportion", "Quadrilaterals", "Mensuration", "Graphs and data handling"],
    },
    "Environmental Studies": {
        1: ["My body", "My family", "Food we eat", "Clothes we wear", "Our home", "Plants around us", "Animals around us", "Water and weather"],
        2: ["Healthy habits", "People who help us", "Our neighbourhood", "Plants and trees", "Animals and their homes", "Air and water", "Seasons", "Keeping our surroundings clean"],
        3: ["Living and non-living things", "Plants and their parts", "Animals and habitats", "Food and health", "Water in our lives", "Our environment", "Our neighbourhood", "Safety and first aid"],
        4: ["Plants and food", "Animals and habitats", "Human body and health", "Water and weather", "Our environment", "Maps and directions", "Transport and communication", "Community helpers"],
        5: ["Plant and animal life", "The human body", "Food, health and hygiene", "Natural resources", "Pollution and conservation", "Maps and our surroundings", "India and its regions", "Disaster safety"],
    },
    "Science": {
        3: ["Living and non-living things", "Plants", "Animals", "Human body and health", "Food and nutrition", "Air and water", "Light and sound", "Our Earth and environment"],
        4: ["Plants and photosynthesis", "Animals and adaptation", "Human body systems", "Food and health", "States of matter", "Force and energy", "Water cycle", "Environment"],
        5: ["Plant and animal life", "Human body systems", "Health and hygiene", "Materials and changes", "Force, work and energy", "Light and sound", "Earth and space", "Natural resources"],
        6: ["The wonderful world of science", "Diversity in the living world", "Mindful eating", "Exploring magnets", "Measurement of length and motion", "Materials around us", "Temperature and its measurement", "Water and its forms", "Methods of separation", "Living organisms and their surroundings"],
        7: ["Nutrition in plants and animals", "Heat and temperature", "Acids, bases and indicators", "Physical and chemical changes", "Motion and time", "Electric current and its effects", "Light", "Forests and ecosystems", "Wastewater and sanitation"],
        8: ["Crop production and management", "Microorganisms", "Materials: metals and non-metals", "Coal and petroleum", "Combustion and flame", "Conservation of plants and animals", "Reproduction in animals", "Force and pressure", "Sound", "Chemical effects of electric current", "Light", "Stars and the solar system"],
    },
    "The World Around Us (EVS)": {
        3: ["Our families and communities", "Plants and animals around us", "Food and health", "Water and its uses", "The places we live", "Travel and transport", "Our environment", "Caring for one another"],
        4: ["Living together", "Food and farming", "Water and weather", "Plants and animals", "Work around us", "Maps and directions", "Materials and making", "Caring for our environment"],
        5: ["Our interdependent world", "Food, health and nutrition", "Water and its journey", "Plants, animals and habitats", "Our community and work", "Maps and local places", "Materials and everyday life", "Environmental care"],
    },
    "Social Science": {
        6: ["Locating places on the Earth", "Oceans and continents", "Landforms and life", "Timeline and sources of history", "India's cultural roots", "Governance and democracy", "Local government", "Livelihoods and economic activities"],
        7: ["Geography and environment", "Weather, climate and water", "People and places", "Understanding the medieval past", "Regional cultures and kingdoms", "The Constitution and equality", "State government", "Markets and livelihoods"],
        8: ["Resources and their use", "Land, soil and water resources", "Agriculture and industries", "Tracing the modern past", "Colonialism and resistance", "India's freedom movement", "The Constitution and secularism", "Parliament and the judiciary"],
    },
    "Computational Thinking & AI": {
        3: ["Patterns and sequences", "Step-by-step instructions", "Sorting and grouping", "Simple algorithms", "Finding and fixing mistakes", "Data in our everyday lives", "Responsible use of technology"],
        4: ["Patterns and logical thinking", "Algorithms and flowcharts", "Breaking a task into steps", "Data and representation", "Debugging simple instructions", "What is artificial intelligence?", "Safety and fairness online"],
        5: ["Computational thinking", "Algorithms and flowcharts", "Patterns in data", "How computers learn from examples", "AI in daily life", "Testing and improving solutions", "Privacy and responsible AI"],
        6: ["Algorithms and decomposition", "Flowcharts and pseudocode", "Data collection and patterns", "Introduction to artificial intelligence", "Training data and predictions", "Simple block-based programming", "AI safety, fairness and privacy"],
        7: ["Computational thinking strategies", "Algorithms and decision trees", "Data representation", "Machine learning basics", "AI applications in society", "Building and testing a simple model", "Responsible and ethical AI"],
        8: ["Problem decomposition and algorithms", "Data and visualisation", "Machine learning and model evaluation", "AI and real-world applications", "Bias and fairness in AI", "Privacy and cybersecurity", "Designing a responsible AI solution"],
    },
    "Physical Education & Well-being": {
        6: ["Fitness and movement", "Games and teamwork", "Yoga and breathing", "Nutrition and hydration", "Personal hygiene", "Safety and first aid", "Emotional well-being"],
        7: ["Strength, flexibility and endurance", "Rules and fair play", "Yoga and mindfulness", "Balanced diet", "Growth and health", "Safety in physical activity", "Managing feelings and stress"],
        8: ["Fitness planning", "Sports skills and strategy", "Yoga and self-awareness", "Nutrition and healthy choices", "Adolescent health", "Injury prevention and first aid", "Mental and social well-being"],
    },
    "Work Education": {
        6: ["Planning a useful project", "Materials and tools", "Growing and caring for plants", "Making and repairing", "Community work", "Working safely", "Reflecting on a project"],
        7: ["Designing a solution", "Craft and productive work", "Food and home skills", "Gardening and sustainability", "Digital making", "Teamwork and responsibility", "Project reflection"],
        8: ["Identifying community needs", "Design and prototyping", "Sustainable making", "Practical household skills", "Entrepreneurship basics", "Safe and ethical work", "Presenting a project"],
    },
    "Art Education": {
        6: ["Lines, shapes and composition", "Colour and texture", "Art from India", "Drawing from observation", "Craft and design", "Music and rhythm", "Drama and expression"],
        7: ["Composition and perspective", "Colour theory", "Indian art traditions", "Printmaking and craft", "Music and performance", "Dance and movement", "Drama and storytelling"],
        8: ["Visual composition", "Perspective and design", "Indian and world art", "Craft and sustainable materials", "Music and rhythm", "Dance and theatre", "Art and community"],
    },
    "Computer Studies": {
        1: ["Parts of a computer", "Using a mouse", "Using a keyboard", "Drawing on a computer", "Computer safety"],
        2: ["Computer parts", "Keyboard and mouse", "Drawing and typing", "Using simple programs", "Staying safe online"],
        3: ["Computer hardware and software", "Keyboard skills", "Word processing", "Drawing tools", "Introduction to coding", "Internet safety"],
        4: ["Computer fundamentals", "Operating a computer", "Word processing", "Presentations", "Introduction to coding", "Internet and safety"],
        5: ["Hardware and software", "Word processing", "Spreadsheets", "Presentations", "Algorithms and coding", "Internet safety"],
        6: ["Computer systems", "Operating systems", "Word processing", "Spreadsheets", "Algorithms and flowcharts", "Programming basics", "Networks and cyber safety"],
        7: ["Computer hardware and software", "Word processing and presentations", "Spreadsheets", "Algorithms", "Programming", "Internet and networks", "Cyber safety"],
        8: ["Computer systems and networks", "Data representation", "Spreadsheets and databases", "Algorithms and flowcharts", "Programming concepts", "Web technologies", "Cyber safety and ethics"],
    },
    "Physics": {
        6: ["Measurement", "Motion and distance", "Simple machines", "Force", "Work and energy", "Light", "Heat", "Electricity and magnets"],
        7: ["Physical quantities and measurement", "Motion and time", "Force and pressure", "Work and energy", "Heat transfer", "Light", "Sound", "Electric current"],
        8: ["Measurements", "Motion", "Force and pressure", "Energy and simple machines", "Heat", "Light", "Sound", "Electricity and magnetism"],
    },
    "Chemistry": {
        6: ["Materials and their properties", "Solids, liquids and gases", "Separation of substances", "Changes around us", "Elements and compounds", "Water", "Air", "Acids and bases"],
        7: ["Matter and its composition", "Elements, compounds and mixtures", "Separation techniques", "Physical and chemical changes", "Atoms and molecules", "Air and atmosphere", "Water", "Acids, bases and salts"],
        8: ["Matter and its composition", "Elements and compounds", "Atoms and molecules", "Mixtures and separation", "Physical and chemical changes", "Acids, bases and salts", "Metals and non-metals", "Combustion"],
    },
    "Biology": {
        6: ["The cell", "Plant life", "Animal life", "Nutrition", "Human body", "Health and hygiene", "Adaptation", "Environment"],
        7: ["Cell structure", "Plant tissues", "Nutrition in plants", "Nutrition in animals", "Respiration and circulation", "Reproduction in plants", "Ecosystems", "Health"],
        8: ["Cell structure and function", "Microorganisms", "Plant physiology", "Human body systems", "Reproduction", "Health and disease", "Food chains", "Conservation of nature"],
    },
    "History": {
        3: ["Our past", "Family and community history", "Early people", "Early settlements", "Important people and events"],
        4: ["Sources of history", "Early humans", "Ancient civilisations", "Early India", "Great leaders and events"],
        5: ["Sources and timelines", "The Indus Valley civilisation", "The Vedic age", "Early kingdoms", "The Mauryan Empire", "The Gupta period", "Medieval India", "Modern India"],
        6: ["Sources of history", "The earliest people", "The first cities", "The Vedic period", "New ideas and religions", "The first empires", "The Gupta age", "Early medieval India"],
        7: ["Medieval India", "The Delhi Sultanate", "The Mughal Empire", "Regional kingdoms", "Bhakti and Sufi movements", "Art and architecture", "The coming of the Europeans", "The freedom movement"],
        8: ["The modern world", "The British in India", "The Revolt of 1857", "Social and religious reform", "The Indian national movement", "The freedom struggle", "India after independence", "World history themes"],
    },
    "Civics": {
        3: ["Rules at home and school", "Our community", "People who help us", "Working together", "Caring for public places"],
        4: ["Families and communities", "Local helpers", "Rules and responsibilities", "Local government", "Respecting differences"],
        5: ["Our country and its symbols", "Diversity in India", "Local self-government", "Rights and responsibilities", "Community participation"],
        6: ["Diversity and inclusion", "Local self-government", "Rural administration", "Urban administration", "Equality and justice", "Rules and laws"],
        7: ["Equality in a democracy", "State government", "The media", "Markets and consumers", "Gender and society", "Public services", "Role of the Constitution"],
        8: ["The Indian Constitution", "Fundamental rights and duties", "Parliament and law-making", "The judiciary", "The Union government", "Social justice", "Public facilities", "Citizenship"],
    },
    "Geography": {
        3: ["Our planet Earth", "Land and water", "Weather and seasons", "Maps and directions", "India and its neighbours"],
        4: ["The Earth and its movements", "Continents and oceans", "Maps and globes", "Mountains and plains", "Weather and climate", "India's states"],
        5: ["The Earth and globes", "Latitudes and longitudes", "Landforms", "Weather and climate", "Natural resources", "India: physical features", "Agriculture and industries", "Map skills"],
        6: ["The Earth in space", "Latitudes and longitudes", "Maps and scale", "The Earth's movements", "Major landforms", "India: physical features", "Climate and vegetation", "Resources"],
        7: ["Environment", "Interior of the Earth", "Changing landforms", "Atmosphere and weather", "Water and oceans", "Natural vegetation and wildlife", "India: people and resources", "Industries"],
        8: ["Representation of geographical features", "Landforms and their evolution", "Atmosphere and climate", "Water resources", "Natural vegetation", "Agriculture", "Mineral and power resources", "Industries and human resources"],
    },
    "Social Studies": {
        3: ["Our past", "Our community", "Maps and directions", "India around us", "People and occupations", "Caring for the environment"],
        4: ["Early people and history", "Communities and government", "Maps and globes", "Landforms", "India and its regions", "Our environment"],
        5: ["Ancient India", "Our Constitution and community", "India's physical features", "Climate and resources", "Agriculture and industries", "Maps and timelines"],
    },
    "Computer Studies": {
        1: ["Parts of a computer", "Using a mouse", "Using a keyboard", "Drawing on a computer", "Computer safety"],
        2: ["Computer parts", "Keyboard and mouse", "Drawing and typing", "Using simple programs", "Staying safe online"],
        3: ["Computer hardware and software", "Keyboard skills", "Word processing", "Drawing tools", "Introduction to coding", "Internet safety"],
        4: ["Computer fundamentals", "Operating a computer", "Word processing", "Presentations", "Introduction to coding", "Internet and safety"],
        5: ["Hardware and software", "Word processing", "Spreadsheets", "Presentations", "Algorithms and coding", "Internet safety"],
        6: ["Computer systems", "Operating systems", "Word processing", "Spreadsheets", "Algorithms and flowcharts", "Programming basics", "Networks and cyber safety"],
        7: ["Computer hardware and software", "Word processing and presentations", "Spreadsheets", "Algorithms", "Programming", "Internet and networks", "Cyber safety"],
        8: ["Computer systems and networks", "Data representation", "Spreadsheets and databases", "Algorithms and flowcharts", "Programming concepts", "Web technologies", "Cyber safety and ethics"],
    },
    "Art Education": {
        1: ["Lines and shapes", "Colours around us", "Drawing plants and animals", "Paper craft", "Music and rhythm"],
        2: ["Drawing with shapes", "Warm and cool colours", "Nature art", "Paper folding and craft", "Music and movement"],
        3: ["Lines, shapes and patterns", "Colour mixing", "Nature drawing", "Paper craft", "Music and rhythm"],
        4: ["Drawing and composition", "Colour and texture", "Folk art", "Craft and design", "Music and performance"],
        5: ["Elements of art", "Observation drawing", "Indian folk art", "Craft and design", "Music, dance and drama"],
        6: ["Elements and principles of art", "Still life and nature drawing", "Indian art forms", "Craft and design", "Music and theatre"],
        7: ["Drawing and composition", "Colour theory", "Indian visual arts", "Craft and model making", "Music, dance and drama"],
        8: ["Visual art and composition", "Perspective and design", "Indian and world art", "Printmaking and craft", "Music, dance and theatre"],
    },
}

st.set_page_config(page_title="Little Moon | Learn, practise, shine", page_icon=str(Path(__file__).parent / "assets" / "little_moon_icon.svg"), layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Nunito:wght@500;600;700;800;900&display=swap');
:root { color-scheme:light; --sun:#7896d4; --ink:#243548; --muted:#4d5d70; --paper:#fffdf8; }
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; color:var(--ink); }
.stApp { background: radial-gradient(ellipse at 80% 0%, #fff0cf 0%, transparent 29%), #fffdf8; }
.block-container { padding-top:1.5rem; max-width:1180px; }
[data-testid="stSidebar"] { background:linear-gradient(170deg,#fff4db,#fffdf8 64%); border-right:1px solid #f2e6cf; }
h1,h2,h3 { font-family:'Nunito',sans-serif; color:#263950; letter-spacing:-.035em; }
.hero { background:linear-gradient(115deg,#e9edff,#f7f8ff 52%,#eef6ff); border:1px solid #dce5fb; border-radius:28px; padding:2rem 2.2rem; margin:.2rem 0 1.5rem; box-shadow:0 12px 36px #2639500a; }
.hero h1 {font-size:2.65rem; margin:0;}.hero p {color:#4d5d70;font-size:1.02rem;margin:.4rem 0 0;}
.sun {font-size:2.2rem; margin-right:.35rem;}
.card {background:white;border:1px solid #eee9df;border-radius:20px;padding:1.2rem 1.35rem;box-shadow:0 7px 24px #26395008;margin-bottom:1rem;}
.eyebrow {font-size:.75rem;text-transform:uppercase;letter-spacing:.12em;font-weight:800;color:#bc7a18;}
.pill {display:inline-block;background:#fff0cc;border-radius:999px;padding:.35rem .8rem;color:#74501d;font-size:.82rem;font-weight:700;margin:.15rem .2rem .15rem 0;}
.fact {background:#fff8e9;border-left:4px solid #efb73c;border-radius:6px 14px 14px 6px;padding:1rem 1.2rem;margin:.7rem 0;color:#38485b;}
div.stButton > button {border-radius:12px;font-weight:700;border-color:#eadfcb;min-height:2.7rem;}
div.stButton > button[kind="primary"] {background:#315a44;border-color:#315a44;}
div[data-testid="stMetric"] {background:white;border:1px solid #eee9df;padding:1rem;border-radius:16px;}
.stTabs [data-baseweb="tab"] {font-weight:700;}
footer {visibility:hidden;}
</style>
""", unsafe_allow_html=True)


def secret_key() -> str:
    try:
        return str(st.secrets.get("GEMINI_API_KEY", "")).strip()
    except Exception:
        return os.getenv("GEMINI_API_KEY", "").strip()


def ai_json(prompt: str) -> Any:
    key = secret_key()
    if not key:
        raise RuntimeError("Add GEMINI_API_KEY in Streamlit Secrets to create learning content.")
    if genai is None:
        raise RuntimeError("Install the packages in requirements.txt and restart the app.")
    client = genai.Client(api_key=key)
    response = client.models.generate_content(model=MODEL, contents=prompt)
    text = (response.text or "").strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I)
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError("The learning service returned an unreadable answer. Please try again.") from exc


def content_language(subject: str) -> str:
    return "Bengali" if subject == "Bengali" else "English"


def topic_context(grade: int, subject: str, topic: str) -> str:
    return f"CBSE/NCERT school learning, Class {grade}, {subject}, chapter or topic: {topic.strip() or 'general revision'}"


def fingerprint(question: dict[str, Any]) -> str:
    clean = re.sub(r"\W+", " ", str(question.get("question", "")).lower()).strip()
    return hashlib.sha256(clean.encode("utf-8")).hexdigest()


def fresh_questions(grade: int, subject: str, topic: str, count: int, pool: str) -> list[dict[str, Any]]:
    topic_id = hashlib.sha256(f"{grade}|{subject}|{topic}".encode("utf-8")).hexdigest()[:16]
    seen_key = f"seen_{topic_id}"
    if seen_key not in st.session_state:
        st.session_state[seen_key] = set()
    seen: set[str] = st.session_state[seen_key]
    questions: list[dict[str, Any]] = []
    skipped = 0
    while len(questions) < count and skipped < 4:
        needed = max(count - len(questions) + 3, 5)
        seen_text_key = f"seen_text_{topic_id}"
        seen_texts = st.session_state.setdefault(seen_text_key, [])
        excluded = json.dumps(seen_texts[-60:], ensure_ascii=False) if seen_texts else "none so far"
        prompt = f"""Create {needed} age-appropriate multiple-choice questions for {topic_context(grade, subject, topic)}. Respond ONLY as a JSON array. Each item must have keys: question (string), choices (array of exactly four distinct strings), answer (the exact correct choice string), explanation (one clear helpful sentence explaining the answer). Avoid these previously asked question texts: {excluded}. Every question must have exactly one unambiguously correct answer. No trick questions. Never repeat excluded text or create a lightly reworded copy. Language: {content_language(subject)}. For Bengali subject use Bengali script. For other subjects use simple English. Do not include markdown."""
        data = ai_json(prompt)
        if not isinstance(data, list):
            continue
        for item in data:
            if not isinstance(item, dict):
                continue
            q = str(item.get("question", "")).strip()
            choices = item.get("choices", [])
            answer = str(item.get("answer", "")).strip()
            if not q or not isinstance(choices, list) or len(choices) != 4 or answer not in choices:
                continue
            ident = fingerprint(item)
            if ident in seen:
                continue
            item["choices"] = [str(c) for c in choices]
            item["answer"] = answer
            item["explanation"] = str(item.get("explanation", "A good answer matches the key idea in this topic."))
            item["_id"] = ident
            questions.append(item)
            seen.add(ident)
            seen_texts.append(q)
            if len(questions) == count:
                break
        skipped += 1
    if len(questions) < count:
        raise RuntimeError("I could not make enough new questions. Try another topic or start a new practice set.")
    return questions


def safe_message(error: Exception) -> None:
    st.error(str(error))
    if "API key" in str(error):
        st.caption("For local use, add GEMINI_API_KEY to .streamlit/secrets.toml. On Streamlit Cloud, add it in App settings → Secrets.")


def pdf_for_paper(grade: int, subject: str, topic: str, questions: list[dict[str, Any]], marks: int, minutes: int, score: int | None = None) -> bytes:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
        from reportlab.lib import colors
    except ImportError as exc:
        raise RuntimeError("PDF tools are not installed. Run pip install -r requirements.txt.") from exc
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm, topMargin=17*mm, bottomMargin=17*mm)
    styles = getSampleStyleSheet()
    story = [Paragraph("Little Moon — Practice Paper", styles["Title"]), Spacer(1, 5*mm)]
    meta = f"Class {grade}  |  {subject}  |  Topic: {topic or 'General revision'}  |  {marks} marks  |  {minutes} minutes"
    story += [Paragraph(meta, styles["Normal"]), Spacer(1, 4*mm), Paragraph("Name: ________________________________    Date: ______________", styles["Normal"]), Spacer(1, 7*mm)]
    points = max(1, marks // len(questions))
    for i, question in enumerate(questions, 1):
        story.append(Paragraph(f"<b>{i}. ({points} mark{'s' if points != 1 else ''})</b> {question['question']}", styles["BodyText"]))
        story.append(Spacer(1, 2*mm))
        for index, choice in enumerate(question["choices"]):
            story.append(Paragraph(f"{'ABCD'[index]}. {choice}", styles["Normal"]))
        story.append(Spacer(1, 5*mm))
    if score is not None:
        story += [Spacer(1, 5*mm), Paragraph(f"<b>Score: {score} / {marks}</b>", styles["Heading2"]), Spacer(1, 3*mm)]
        story.append(Paragraph("Answer key and explanations", styles["Heading2"]))
        for i, question in enumerate(questions, 1):
            story.append(Paragraph(f"{i}. <b>{question['answer']}</b> — {question['explanation']}", styles["BodyText"]))
            story.append(Spacer(1, 2*mm))
    doc.build(story)
    return output.getvalue()


def header() -> None:
    st.markdown('<div class="hero"><span class="sun">🌙</span><h1 style="display:inline">Little Moon</h1><p>Small steps, bright ideas, confident learning.</p></div>', unsafe_allow_html=True)


@st.dialog("Support Little Moon", width="large")
def donation_dialog() -> None:
    st.write("Thank you for supporting Little Moon. The secure donation form is provided by Razorpay.")
    components.html(
        '<form><script src="https://checkout.razorpay.com/v1/payment-button.js" '
        'data-payment_button_id="pl_Tvez6NOZsFJFmN" async></script></form>',
        height=620,
        scrolling=True,
    )


def chapters_for(grade: int, subject: str) -> list[str]:
    by_grade = CHAPTERS.get(subject, {})
    return by_grade.get(grade, ["General revision", "Key ideas and vocabulary"])


def render_setup() -> tuple[int, str, str]:
    with st.sidebar:
        st.markdown("## 🌙 Little Moon")
        st.caption("Your friendly CBSE learning companion")
        st.link_button("🌙 Install Little Moon", PWA_INSTALL_URL, use_container_width=True)
        st.caption("Add the moon icon to your desktop or phone.")
        grade = st.selectbox("Choose your class", range(1, 9), format_func=lambda x: f"Class {x}", key="grade")
        subject = st.selectbox("Choose a subject", SUBJECTS_BY_CLASS[grade], key="subject")
        chapter = st.selectbox("Choose a chapter", ["Select a chapter…", *chapters_for(grade, subject)], key="chapter_choice", help="These are common chapter suggestions. Your school may use different names.")
        custom_chapter = st.text_input("Or enter your own chapter", placeholder="Type a chapter if your syllabus differs", key="custom_chapter")
        topic = custom_chapter.strip() or ("" if chapter == "Select a chapter…" else chapter)
        st.divider()
        st.caption("🌱 Made for CBSE Classes 1–8 · English & Bengali learning")
        st.caption("Chapter suggestions are general. Match your school's textbook or enter your own chapter above.")
        st.divider()
        st.markdown("#### Support Little Moon")
        st.caption("If you find this app useful, you can support its development.")
        if st.button("💛 Donate with Razorpay", key="open_donation", use_container_width=True):
            donation_dialog()
        st.caption("App owner: **NilanjanC**")
    return grade, subject, topic


def home(grade: int, subject: str, topic: str) -> None:
    st.markdown(f"### Hello, Class {grade} learner! 👋")
    st.write(f"You’re ready to explore **{subject}**" + (f" · **{topic}**" if topic else "") + ". What shall we learn today?")
    cols = st.columns(3)
    cards = [("🔑", "Key words", "Learn the important words and ideas."), ("🎯", "Quick practice", "Try a fresh set of four-choice questions."), ("📝", "Practice paper", "Set your marks and time, then see your score."), ("✨", "Fun facts", "Find a surprising fact for your chapter.")]
    for i, (icon, name, blurb) in enumerate(cards):
        with cols[i % 3]:
            st.markdown(f'<div class="card"><div style="font-size:1.7rem">{icon}</div><b>{name}</b><p style="color:#4d5d70;margin-bottom:0">{blurb}</p></div>', unsafe_allow_html=True)
    st.info("Choose a section below to begin. If you know your chapter, add it in the left sidebar for more focused learning.")
    tabs = st.tabs(["🔑 Key words", "🎯 Quick practice", "📝 Practice paper", "✨ Fun facts"])
    with tabs[0]: keywords_panel(grade, subject, topic)
    with tabs[1]: quiz_panel(grade, subject, topic)
    with tabs[2]: paper_panel(grade, subject, topic)
    with tabs[3]: facts_panel(grade, subject, topic)


def keywords_panel(grade: int, subject: str, topic: str) -> None:
    st.subheader("Key words")
    st.write("Build your chapter word bank with simple, memorable meanings.")
    if st.button("✨ Make my key-word list", key="keywords_btn", type="primary"):
        with st.spinner("Finding the important words…"):
            try:
                prompt = f"For {topic_context(grade, subject, topic)}, create 10 important school-level key words or phrases with a short, child-friendly definition (one sentence). Choose the most useful words for revision. Output only valid JSON array with objects having keys 'term' and 'meaning'. Language: {content_language(subject)}. Bengali subject must use Bengali script. Others use simple English. No markdown."
                st.session_state.keywords = ai_json(prompt)
                st.session_state.kw_context = (grade, subject, topic)
            except Exception as exc:
                safe_message(exc)
    if st.session_state.get("kw_context") == (grade, subject, topic):
        items = st.session_state.get("keywords", [])
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    st.markdown(f"<div class='card'><b>{item.get('term','')}</b><br><span style='color:#4d5d70'>{item.get('meaning','')}</span></div>", unsafe_allow_html=True)


def quiz_panel(grade: int, subject: str, topic: str) -> None:
    st.subheader("Quick practice")
    st.write("A fresh set each time. Choose one answer, then check it to see why it’s right.")
    context = (grade, subject, topic)
    if st.session_state.get("quiz_context") != context:
        st.session_state.quiz = None
        st.session_state.quiz_context = context
    if st.button("🎲 Give me 5 new questions", key="new_quiz", type="primary"):
        with st.spinner("Making a fresh question set…"):
            try:
                st.session_state.quiz = fresh_questions(grade, subject, topic, 5, f"quiz_{grade}_{subject}_{topic}")
                st.session_state.quiz_answers = {}
                st.session_state.quiz_checked = set()
            except Exception as exc:
                safe_message(exc)
    for i, question in enumerate(st.session_state.get("quiz") or []):
        st.markdown(f"<div class='card'><span class='eyebrow'>Question {i+1}</span><br><b>{question['question']}</b></div>", unsafe_allow_html=True)
        answer = st.radio("Choose one answer", question["choices"], key=f"quiz_choice_{question['_id']}", index=None, label_visibility="collapsed")
        if st.button("Check answer", key=f"quiz_check_{question['_id']}"):
            st.session_state.quiz_answers[question["_id"]] = answer
            st.session_state.quiz_checked.add(question["_id"])
        if question["_id"] in st.session_state.get("quiz_checked", set()):
            chosen = st.session_state.quiz_answers.get(question["_id"])
            if chosen == question["answer"]:
                st.success("That’s right! 🌟 " + question["explanation"])
            else:
                st.error("Not quite. The right answer is **" + question["answer"] + "**.")
                st.info("💡 " + question["explanation"])


def paper_panel(grade: int, subject: str, topic: str) -> None:
    st.subheader("Make a practice paper")
    st.write("Choose the length of your test. Your score, right answers and review appear after you submit.")
    with st.form("paper_setup"):
        c1, c2 = st.columns(2)
        marks = c1.select_slider("Total marks", options=[5, 10, 15, 20, 25, 30, 40, 50], value=20)
        minutes = c2.select_slider("Time limit (minutes)", options=[5, 10, 15, 20, 30, 45, 60], value=20)
        submitted = st.form_submit_button("📝 Create my paper", type="primary")
    context = (grade, subject, topic)
    if submitted:
        with st.spinner("Preparing your paper…"):
            try:
                number = marks
                questions = fresh_questions(grade, subject, topic, number, f"paper_{grade}_{subject}_{topic}")
                st.session_state.paper = {"questions": questions, "marks": marks, "minutes": minutes, "started": time.time(), "context": context, "submitted": False}
                st.session_state.paper_responses = {}
            except Exception as exc:
                safe_message(exc)
    paper = st.session_state.get("paper")
    if not paper or paper.get("context") != context:
        return
    if paper.get("submitted"):
        render_results(paper, grade, subject, topic)
        return
    remaining = max(0, int(paper["minutes"] * 60 - (time.time() - paper["started"])))
    if remaining == 0:
        st.warning("Time is up. Your answers have been submitted.")
        paper["submitted"] = True
        st.session_state.paper_responses = {q["_id"]: st.session_state.get(f"paper_{q['_id']}") for q in paper["questions"]}
        render_results(paper, grade, subject, topic)
        return
    mins, secs = divmod(remaining, 60)
    st.markdown(f"### ⏱️ Time remaining: {mins:02d}:{secs:02d}")
    st.caption(f"{paper['marks']} marks · {len(paper['questions'])} questions")
    if st_autorefresh:
        st_autorefresh(interval=1000, key="paper_clock")
    for i, question in enumerate(paper["questions"]):
        st.markdown(f"**{i+1}. {question['question']}**")
        st.radio("Select an answer", question["choices"], key=f"paper_{question['_id']}", index=None, label_visibility="collapsed")
        st.write("")
    if st.button("Submit my answers", type="primary", key="submit_paper"):
        paper["submitted"] = True
        st.session_state.paper_responses = {q["_id"]: st.session_state.get(f"paper_{q['_id']}") for q in paper["questions"]}
        st.rerun()


def render_results(paper: dict[str, Any], grade: int, subject: str, topic: str) -> None:
    questions = paper["questions"]
    responses = st.session_state.get("paper_responses", {})
    marks = paper["marks"]
    raw = sum(responses.get(q["_id"]) == q["answer"] for q in questions)
    score = round(raw * marks / max(1, len(questions)))
    st.markdown("### Your result 🌟")
    st.metric("Score", f"{score} / {marks}", f"{raw} correct out of {len(questions)}")
    st.progress(raw / len(questions))
    for i, question in enumerate(questions, 1):
        chosen = responses.get(question["_id"])
        if chosen == question["answer"]:
            st.success(f"{i}. Correct — {question['answer']}")
        else:
            st.error(f"{i}. Your answer: {chosen or 'Not answered'} · Correct answer: {question['answer']}")
        st.caption(question["explanation"])
    c1, c2 = st.columns(2)
    try:
        pdf = pdf_for_paper(grade, subject, topic, questions, marks, paper["minutes"], score)
        c1.download_button("📄 Download paper and answer review (PDF)", data=pdf, file_name=f"little-moon-class-{grade}-{subject.lower().replace(' ','-')}-paper.pdf", mime="application/pdf", type="primary")
        blank = pdf_for_paper(grade, subject, topic, questions, marks, paper["minutes"])
        c2.download_button("🖨️ Download blank question paper (PDF)", data=blank, file_name=f"little-moon-class-{grade}-question-paper.pdf", mime="application/pdf")
    except Exception as exc:
        safe_message(exc)
    if st.button("Start another fresh paper", key="another_paper"):
        st.session_state.paper = None
        st.rerun()


def facts_panel(grade: int, subject: str, topic: str) -> None:
    st.subheader("Fun facts")
    st.write("Discover something surprising about what you’re learning!")
    if st.button("✨ Show me a fun fact", key="fact_btn", type="primary"):
        with st.spinner("Finding a fun fact…"):
            try:
                prompt = f"Give one accurate, surprising, age-appropriate fun fact about {topic_context(grade, subject, topic)}. Return only JSON object with keys 'fact' (2-3 simple sentences) and 'why_it_matters' (one sentence). Language: {content_language(subject)}. Bengali subject uses Bengali script; all other subjects use simple English. Avoid unsupported claims."
                st.session_state.fun_fact = ai_json(prompt)
                st.session_state.fact_context = (grade, subject, topic)
            except Exception as exc:
                safe_message(exc)
    fact = st.session_state.get("fun_fact")
    if fact and st.session_state.get("fact_context") == (grade, subject, topic):
        st.markdown(f"<div class='fact'><span class='eyebrow'>Did you know?</span><br><b>{fact.get('fact','')}</b><br><br>{fact.get('why_it_matters','')}</div>", unsafe_allow_html=True)


header()
grade, subject, topic = render_setup()
home(grade, subject, topic)
st.markdown("<div style='text-align:center;color:#536174;padding:2rem 0 1rem'>🌙 Little Moon · Created by <b>NilanjanC</b> · Keep asking, keep growing.</div>", unsafe_allow_html=True)

