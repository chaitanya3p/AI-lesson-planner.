import os
import requests
import gradio as gr

API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

def generate(topic, grade, subject, duration, keywords, style):
    if not API_KEY:
        return "Set GEMINI_API_KEY in Render Environment settings.", "", ""
    if not (topic or "").strip():
        return "Please enter a topic.", "", ""
    prompt = f"""You are an educational lesson-planning assistant.
Topic: {topic}
Grade/age group: {grade}
Subject: {subject}
Duration: {duration}
Keywords: {keywords or "Choose relevant keywords"}
Teaching style: {style}

Create practical, age-appropriate classroom material. Return these exact sections:
1. SHORT STORY / INTRODUCTION
2. LESSON PLAN
Include 3 learning objectives, materials, warm-up, timed teaching activities, assessment,
differentiation/support, and homework/extension.
3. QUICK QUIZ
Include 5 questions and an answer key. Use clear headings."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
    try:
        r = requests.post(url, params={"key": API_KEY},
            headers={"Content-Type": "application/json"},
            json={"contents":[{"parts":[{"text":prompt}]}],
                  "generationConfig":{"temperature":0.7,"maxOutputTokens":2500}},
            timeout=90)
        if r.status_code != 200:
            try:
                detail = r.json().get("error", {}).get("message", r.text)
            except Exception:
                detail = r.text
            return f"Gemini API error ({r.status_code}): {detail}", "", ""
        data = r.json()
        text = "\n".join(p.get("text","") for p in data["candidates"][0]["content"]["parts"]).strip()
        a, b, c = "2. LESSON PLAN", "3. QUICK QUIZ", ""
        i, j = text.find(a), text.find(b)
        if i >= 0 and j > i:
            return text[:i].strip(), text[i:j].strip(), text[j:].strip()
        return text, "See generated response above.", "Try generating again if sections are missing."
    except requests.Timeout:
        return "Request timed out. Please try again.", "", ""
    except Exception as e:
        return f"Request failed: {e}", "", ""

with gr.Blocks(title="AI Lesson Planner", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# AI Story & Lesson-Plan Generator\nGenerate a story, classroom lesson plan, and quiz using a hosted AI model.")
    with gr.Row():
        with gr.Column():
            topic = gr.Textbox(label="Topic", placeholder="Water Cycle")
            grade = gr.Dropdown(["Kindergarten","Grades 1–3","Grades 4–5","Grades 6–8","Grades 9–10","Grades 11–12","College / Adult learners"], value="Grades 4–5", label="Grade / age group")
            subject = gr.Textbox(label="Subject", value="Science")
            duration = gr.Dropdown(["15 minutes","30 minutes","45 minutes","60 minutes"], value="30 minutes", label="Duration")
            keywords = gr.Textbox(label="Keywords", placeholder="rain, clouds, river")
            style = gr.Dropdown(["Story-based","Activity-based","Visual and interactive","Simple explanation"], value="Story-based", label="Teaching style")
            btn = gr.Button("Generate lesson", variant="primary")
        with gr.Column():
            story = gr.Markdown()
            lesson = gr.Markdown()
            quiz = gr.Markdown()
    btn.click(generate, [topic, grade, subject, duration, keywords, style], [story, lesson, quiz])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", "7860")), share=False)
