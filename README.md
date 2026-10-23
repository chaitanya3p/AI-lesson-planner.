# Gemini AI Teacher Story & Lesson-Plan Assistant

This version matches the component order and general layout of the original fine-tuned Qwen Gradio interface while keeping Gemini as the generation backend. It does **not** use or claim to use the fine-tuned Qwen adapter.

## Files
- `app.py`: Gradio interface, Gemini API call, retries, lightweight automated checks, and Markdown download.
- `requirements.txt`: runtime dependencies.
- `render.yaml`: Render Blueprint configuration.

## Run locally
1. Install Python 3.10+.
2. Run `pip install -r requirements.txt`.
3. Set `GEMINI_API_KEY` as an environment variable.
4. Optional: set `GEMINI_MODEL` (default `gemini-2.5-flash`).
5. Run `python app.py` and open the local URL printed in the terminal.

## Deploy to Render
Push these files to the root of the GitHub repository connected to Render, then deploy. In Render → Environment, set `GEMINI_API_KEY` securely. Do not place API keys in source code or commit them to GitHub.

## Notes about metrics
The report includes simple automated checks for section structure, keyword coverage, story length, average sentence length, and a basic safety phrase scan. These are transparent heuristics, not formal ROUGE-L/distinct-2 scores or evidence of teacher trust, model quality, or regulatory compliance. Human review is required. Gemini retries are additional API calls and may use quota.
