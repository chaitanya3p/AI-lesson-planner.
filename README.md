# AI Lesson Planner — free deployment

This deployment uses the hosted Gemini API instead of loading the Qwen2.5-3B LoRA model locally.
Render provides a stable URL, but free services may sleep when idle.

## 1. Create an API key
1. Visit https://aistudio.google.com/apikey
2. Create a Gemini Developer API key.
3. Keep it private. Do not put it in source code or commit it to GitHub.
4. Check current free quotas/model availability: https://ai.google.dev/gemini-api/docs/pricing

## 2. Put these files on GitHub
Create a repository named `ai-lesson-planner` and upload `app.py`, `requirements.txt`,
`render.yaml`, and `README.md` to its root. Do not upload your API key.

## 3. Deploy on Render
1. Visit https://render.com and sign in with GitHub.
2. Choose New + → Blueprint, then connect your repository.
3. Render detects `render.yaml`; select the Free plan.
4. In the service Environment settings, set `GEMINI_API_KEY` to your key.
5. Keep `GEMINI_MODEL` as `gemini-2.5-flash` unless Google's current model list says otherwise.
6. Deploy and open the `https://....onrender.com` URL.

If Blueprint is unavailable, create a Web Service manually:
- Build command: `pip install -r requirements.txt`
- Start command: `python app.py`
- Plan: Free
- Add environment variable `GEMINI_API_KEY`

## 4. Test
Topic: Water Cycle; Subject: Science; Keywords: rain, clouds, river; click Generate lesson.

The URL remains stable while the service exists, but the free service can sleep after inactivity.
The app uses Gemini, not your fine-tuned LoRA adapter. Free quotas, availability and terms can change.
Do not enter confidential student data or secrets into the app.
