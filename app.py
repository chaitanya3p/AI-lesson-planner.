"""Gemini-powered teacher story and lesson-plan assistant.
Uses the same teacher-facing component arrangement as the fine-tuned Qwen Gradio UI.
Set GEMINI_API_KEY in the hosting provider's environment; never hard-code it here.
"""
import os
import re
import tempfile
import time
import requests
import gradio as gr

API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
DEMO = "Demo (offline templates - no AI model)"
GEMINI = "Gemini model"
SUBJECTS = ["Science", "Math", "EVS", "Social Science", "Values", "English"]

CSS = r"""
.gradio-container { max-width: 100% !important; padding: 22px 2.1% 28px !important; }
footer, .built-with, .gradio-container > .main > .wrap > footer { display: none !important; }
#app-title { margin: 0 0 8px 0; }
#app-subtitle { margin: 0 0 18px 0; }
#settings-row, #generator-row, #topic-keywords { border: 1px solid var(--border-color-primary); border-radius: 5px; padding: 12px; gap: 16px; }
#topic-keywords { margin-top: 14px; }
#generator-row { margin-top: 14px; align-items: center; }
#generate-btn { background: #ff710f !important; border: 1px solid #ff710f !important; color: white !important; font-weight: 600 !important; margin: 16px 0 14px !important; }
#generate-btn:hover { background: #ed6508 !important; }
#outputs { gap: 14px; }
label { font-size: 14px !important; }
@media (max-width: 700px) { .gradio-container { padding: 16px 12px !important; } #settings-row, #generator-row { padding: 10px; } }
"""


def demo_generate(grade, subject, topic, keywords):
    terms = [x.strip() for x in (keywords or "").split(",") if x.strip()]
    key_sentence = ", ".join(terms) if terms else topic
    story = (f"## {topic.title()}\n\nOne day, a curious Grade {grade} student began exploring {topic.lower()}. "
             f"With help from a teacher, the student observed examples, asked questions, and connected the idea to everyday life. "
             f"The class discussed {key_sentence}, shared observations, and learned that careful questions help us understand the world.\n\n"
             f"The student explained the new idea to a friend and thought of one way to use it outside the classroom.")
    lesson = (f"## Lesson plan: {topic.title()}\n\n**Grade:** {grade}  \n**Subject:** {subject}  \n**Duration:** 30 minutes\n\n"
              f"### Learning objectives\n1. Explain the main idea of {topic}.\n2. Identify examples related to {key_sentence}.\n3. Describe one real-life application.\n\n"
              f"### Materials\nBoard, paper, pencils, and relevant classroom examples.\n\n"
              f"### Teaching activities\n- **Warm-up (5 min):** Ask learners what they already know about {topic}.\n"
              f"- **Story and explanation (10 min):** Read the story and explain the key idea.\n"
              f"- **Guided activity (10 min):** Learners work in pairs to give examples using {key_sentence}.\n"
              f"- **Review (5 min):** Invite learners to explain one thing they learned.\n\n"
              f"### Assessment\nAsk learners to explain {topic} in their own words and give one example.\n\n"
              f"### Differentiation\nOffer picture cues and sentence starters; extend learning by asking confident learners for another example.\n\n"
              f"### Homework / extension\nFind or draw one everyday example connected to {topic}.")
    return story, lesson


def call_gemini(prompt):
    if not API_KEY:
        raise gr.Error("Gemini API key is not configured. Add GEMINI_API_KEY in Render → Environment settings.")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
    try:
        response = requests.post(
            url, params={"key": API_KEY}, headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}],
                 "generationConfig": {"temperature": 0.7, "maxOutputTokens": 3000}}, timeout=90)
    except requests.Timeout:
        raise gr.Error("Gemini request timed out. Please try again.")
    except requests.RequestException as exc:
        raise gr.Error(f"Could not connect to Gemini: {exc}")
    if response.status_code != 200:
        try:
            message = response.json().get("error", {}).get("message", response.text)
        except Exception:
            message = response.text
        raise gr.Error(f"Gemini API error ({response.status_code}): {message}")
    data = response.json()
    try:
        return "\n".join(part.get("text", "") for part in data["candidates"][0]["content"]["parts"]).strip()
    except (KeyError, IndexError, TypeError):
        raise gr.Error("Gemini returned an empty or unexpected response. Please try again.")


def split_sections(text):
    # Parse clear headings while retaining a usable fallback if Gemini varies its formatting.
    story_match = re.search(r"(?:^|\n)\s*(?:#{1,4}\s*)?(?:1[.)]\s*)?(?:SHORT STORY(?:\s*/\s*INTRODUCTION)?|STORY)\s*:?\s*", text, re.I)
    lesson_match = re.search(r"(?:^|\n)\s*(?:#{1,4}\s*)?(?:2[.)]\s*)?LESSON PLAN\s*:?\s*", text, re.I)
    quiz_match = re.search(r"(?:^|\n)\s*(?:#{1,4}\s*)?(?:3[.)]\s*)?(?:QUICK QUIZ|QUIZ|ASSESSMENT QUESTIONS)\s*:?\s*", text, re.I)
    if lesson_match:
        story = text[story_match.end():lesson_match.start()].strip() if story_match else text[:lesson_match.start()].strip()
        end = quiz_match.start() if quiz_match and quiz_match.start() > lesson_match.end() else len(text)
        lesson = text[lesson_match.end():end].strip()
        quiz = text[quiz_match.end():].strip() if quiz_match and quiz_match.start() > lesson_match.end() else "Quiz/assessment questions are included in the lesson plan."
        return story or text, lesson or "See generated response.", quiz
    return text, "The model did not return a separately headed lesson plan. Review the story/response and regenerate if needed.", "Quiz section was not detected."


def evaluate(story, lesson, keywords, grade):
    combined = f"{story}\n{lesson}".lower()
    terms = [x.strip().lower() for x in (keywords or "").split(",") if x.strip()]
    covered = [term for term in terms if term in combined]
    coverage = len(covered) / len(terms) if terms else 1.0
    required = ["learning objectives", "materials", "assessment"]
    structure_hits = [item for item in required if item in lesson.lower()]
    structure = len(structure_hits) / len(required)
    words = re.findall(r"\b[\w'-]+\b", story)
    sentences = [s for s in re.split(r"[.!?]+", story) if s.strip()]
    avg_sentence = len(words) / max(len(sentences), 1)
    readability_flag = "Review sentence length" if avg_sentence > 22 else "Sentence length looks manageable"
    safety_terms = ["graphic violence", "sexual content", "self-harm instructions"]
    safety_flag = "Review safety wording" if any(term in combined for term in safety_terms) else "No basic safety flag detected"
    passed = coverage >= 0.8 and structure >= 1.0 and safety_flag.startswith("No basic")
    metrics = (f"Structure pass: {structure*100:.0f}% ({len(structure_hits)}/{len(required)} required sections) | "
               f"Keyword coverage: {coverage*100:.0f}% ({len(covered)}/{len(terms) if terms else 0}) | "
               f"Story words: {len(words)} | Avg. words/sentence: {avg_sentence:.1f} | "
               f"Readability: {readability_flag} | Basic safety scan: {safety_flag} | "
               f"Overall automated checks: {'PASS' if passed else 'REVIEW'}")
    issues = []
    if coverage < 0.8: issues.append("keyword coverage below 80%")
    if structure < 1.0: issues.append("lesson-plan structure incomplete")
    if not safety_flag.startswith("No basic"): issues.append("basic safety flag detected")
    return {"passed": passed, "metrics": metrics, "issues": issues, "coverage": coverage}


def generate(grade, subject, topic, keywords, mode, retries):
    if not (topic or "").strip():
        raise gr.Error("Please enter a topic.")
    if not (keywords or "").strip():
        raise gr.Error("Please enter at least one keyword.")
    start = time.time()
    if mode == DEMO:
        story, lesson = demo_generate(grade, subject, topic.strip(), keywords)
        quiz = "Demo mode does not generate a separate quiz. Use Gemini model for the full generation workflow."
        trace = [{"attempt": 1, "issues": []}]
        result = evaluate(story, lesson, keywords, grade)
    else:
        last = None
        trace = []
        for attempt in range(int(retries) + 1):
            feedback = ""
            if last:
                feedback = "\nRevise the previous draft to fix these issues: " + "; ".join(last["issues"]) + ".\n"
            prompt = f"""You are a careful teacher-facing story and lesson-plan assistant. Create safe, age-appropriate classroom material and follow all requirements.
Grade: {grade}
Subject: {subject}
Topic: {topic.strip()}
Required keywords (include naturally): {keywords.strip()}
{feedback}
Return these exact sections in this order:
1. STORY
Write a short, engaging age-appropriate story/introduction related to the topic. Use the requested keywords naturally.
2. LESSON PLAN
Include exactly clear headings for Learning objectives (3 measurable objectives), Materials, Teaching activities with minute timings totalling 30 minutes, Assessment, Differentiation/support, and Homework/extension.
3. QUICK QUIZ
Include 5 grade-appropriate questions and a clearly marked answer key.
Use clear Markdown headings. Avoid harmful, discriminatory, frightening, or inappropriate content. Do not claim the material has been validated by a human teacher."""
            raw = call_gemini(prompt)
            story, lesson, quiz = split_sections(raw)
            last = evaluate(story, lesson, keywords, grade)
            trace.append({"attempt": attempt + 1, "issues": list(last["issues"])})
            if last["passed"]:
                break
        result = last
    if not story.strip() or not lesson.strip():
        raise gr.Error("The model returned incomplete content. Please generate again.")
    status = "Passed automated checks — teacher review still required." if result["passed"] else "Needs teacher review: " + "; ".join(result["issues"] or ["review content"])
    report = (f"{status}\n\nMetrics: {result['metrics']}\n\n"
              f"Attempts used: {len(trace)} / maximum {int(retries)+1}\n"
              f"Agent / retry trace:\n" + "\n".join(f"Attempt {t['attempt']}: {len(t['issues'])} issue(s) — {', '.join(t['issues']) or 'no flagged issues'}" for t in trace) +
              f"\n\nProvider: {'Gemini (' + MODEL + ')' if mode == GEMINI else 'Offline template demo'}\n"
              f"Generation time: {time.time()-start:.1f}s\n\nNote: these are lightweight automated checks, not a formal educational, safety, or model-quality evaluation. Always review before class.")
    md = f"# Story\n\n{story}\n\n# Lesson plan\n\n{lesson}\n\n# Quick quiz\n\n{quiz}\n\n# Evaluation report\n\n{report}\n"
    tmp = tempfile.mkdtemp(prefix="lesson_planner_")
    path = os.path.join(tmp, "lesson_plan.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(md)
    return story, lesson + "\n\n## Quick quiz\n\n" + quiz, report, path


with gr.Blocks(title="AI Teacher Story & Lesson-Plan Assistant", css=CSS, theme=gr.themes.Soft(primary_hue="orange", neutral_hue="slate")) as demo:
    gr.Markdown("# AI Teacher Story & Lesson-Plan Assistant", elem_id="app-title")
    gr.Markdown("Generate age-appropriate stories and structured lesson plans using an AI language model. The planner, generator and critic checks draft classroom materials. Always review before class.", elem_id="app-subtitle")
    with gr.Row(elem_id="settings-row"):
        grade = gr.Dropdown([1, 2, 3, 4, 5, 6, 7, 8], value=3, label="Grade", scale=1)
        subject = gr.Dropdown(SUBJECTS, value="Science", label="Subject", scale=1)
    with gr.Column(elem_id="topic-keywords"):
        topic = gr.Textbox(label="Topic", placeholder="Water cycle", lines=1, max_lines=1)
        keywords = gr.Textbox(label="Keywords (comma separated)", placeholder="rain, river, clouds", lines=1, max_lines=1)
    with gr.Row(elem_id="generator-row"):
        mode = gr.Radio([DEMO, GEMINI], value=GEMINI, label="Generator", scale=1)
        retries = gr.Slider(0, 3, value=2, step=1, label="Max critic retries", scale=2)
    btn = gr.Button("Generate", variant="primary", elem_id="generate-btn")
    with gr.Column(elem_id="outputs"):
        story = gr.Textbox(label="Story", lines=10, interactive=False)
        lesson = gr.Textbox(label="Lesson plan", lines=16, interactive=False)
        report = gr.Textbox(label="Critic report & metrics", lines=7, interactive=False)
        file = gr.File(label="Download lesson materials")
    btn.click(generate, [grade, subject, topic, keywords, mode, retries], [story, lesson, report, file])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", "7860")), share=False)
