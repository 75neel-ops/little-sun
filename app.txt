from __future__ import annotations

import hashlib
import io
import json
import os
import random
import re
import time
from typing import Any

import streamlit as st

try:
    from google import genai
except ImportError:
    genai = None

try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None

MODEL = "gemini-3.5-flash-lite"
APP_NAME = "Little Sun"

SUBJECTS_BY_CLASS = {
    1: ["English", "Bengali", "Mathematics", "Environmental Studies", "Computer Studies", "Arts Education"],
    2: ["English", "Bengali", "Mathematics", "Environmental Studies", "Computer Studies", "Arts Education"],
    3: ["English", "Bengali", "Mathematics", "Science", "Social Studies", "Computer Studies", "Arts Education"],
    4: ["English", "Bengali", "Mathematics", "Science", "Social Studies", "Computer Studies", "Arts Education"],
    5: ["English", "Bengali", "Mathematics", "Science", "Social Studies", "Computer Studies", "Arts Education"],
    6: ["English", "Bengali", "Mathematics", "Physics", "Chemistry", "Biology", "History", "Civics", "Geography", "Computer Studies", "Arts Education"],
    7: ["English", "Bengali", "Mathematics", "Physics", "Chemistry", "Biology", "History", "Civics", "Geography", "Computer Studies", "Arts Education"],
    8: ["English", "Bengali", "Mathematics", "Physics", "Chemistry", "Biology", "History", "Civics", "Geography", "Computer Studies", "Arts Education"],
}

st.set_page_config(page_title="Little Sun | Learn, practise, shine", page_icon="☀️", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Nunito:wght@500;600;700;800;900&display=swap');
:root { --sun:#ed9e27; --ink:#243548; --muted:#718092; --paper:#fffdf8; }
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; color:var(--ink); }
.stApp { background: radial-gradient(ellipse at 80% 0%, #fff0cf 0%, transparent 29%), #fffdf8; }
.block-container { padding-top:1.5rem; max-width:1180px; }
[data-testid="stSidebar"] { background:linear-gradient(170deg,#fff4db,#fffdf8 64%); border-right:1px solid #f2e6cf; }
h1,h2,h3 { font-family:'Nunito',sans-serif; color:#263950; letter-spacing:-.035em; }
.hero { background:linear-gradient(115deg,#fff0cc,#fff9e9 52%,#eef6ee); border:1px solid #f5e3bd; border-radius:28px; padding:2rem 2.2rem; margin:.2rem 0 1.5rem; box-shadow:0 12px 36px #4633000a; }
.hero h1 {font-size:2.65rem; margin:0;}.hero p {color:#687487;font-size:1.02rem;margin:.4rem 0 0;}
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
    return f"ICSE/CISCE school learning, Class {grade}, {subject}, chapter or topic: {topic.strip() or 'general revision'}"


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
    story = [Paragraph("Little Sun — Practice Paper", styles["Title"]), Spacer(1, 5*mm)]
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
    st.markdown('<div class="hero"><span class="sun">☀️</span><h1 style="display:inline">Little Sun</h1><p>Small steps, bright ideas, confident learning.</p></div>', unsafe_allow_html=True)


def render_setup() -> tuple[int, str, str]:
    with st.sidebar:
        st.markdown("## ☀️ Little Sun")
        st.caption("Your friendly ICSE learning companion")
        grade = st.selectbox("Choose your class", range(1, 9), format_func=lambda x: f"Class {x}", key="grade")
        subject = st.selectbox("Choose a subject", SUBJECTS_BY_CLASS[grade], key="subject")
        topic = st.text_input("Chapter or topic (optional)", placeholder="e.g. Plants around us", help="Chapter names differ between schools. Type your own chapter or leave it blank for a mixed revision set.")
        st.divider()
        st.caption("🌱 Made for Classes 1–8 · English & Bengali learning")
        st.caption("A teacher or parent can help check that topics match your school's textbook.")
    return grade, subject, topic


def home(grade: int, subject: str, topic: str) -> None:
    st.markdown(f"### Hello, Class {grade} learner! 👋")
    st.write(f"You’re ready to explore **{subject}**" + (f" · **{topic}**" if topic else "") + ". What shall we learn today?")
    cols = st.columns(3)
    cards = [("🔑", "Key words", "Learn the important words and ideas."), ("🎯", "Quick practice", "Try a fresh set of four-choice questions."), ("📝", "Practice paper", "Set your marks and time, then see your score."), ("✨", "Fun facts", "Find a surprising fact for your chapter.")]
    for i, (icon, name, blurb) in enumerate(cards):
        with cols[i % 3]:
            st.markdown(f'<div class="card"><div style="font-size:1.7rem">{icon}</div><b>{name}</b><p style="color:#718092;margin-bottom:0">{blurb}</p></div>', unsafe_allow_html=True)
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
                    st.markdown(f"<div class='card'><b>{item.get('term','')}</b><br><span style='color:#687487'>{item.get('meaning','')}</span></div>", unsafe_allow_html=True)


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
        c1.download_button("📄 Download paper and answer review (PDF)", data=pdf, file_name=f"little-sun-class-{grade}-{subject.lower().replace(' ','-')}-paper.pdf", mime="application/pdf", type="primary")
        blank = pdf_for_paper(grade, subject, topic, questions, marks, paper["minutes"])
        c2.download_button("🖨️ Download blank question paper (PDF)", data=blank, file_name=f"little-sun-class-{grade}-question-paper.pdf", mime="application/pdf")
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
st.markdown("<div style='text-align:center;color:#8a95a3;padding:2rem 0 1rem'>☀️ Little Sun · Keep asking, keep growing.</div>", unsafe_allow_html=True)
