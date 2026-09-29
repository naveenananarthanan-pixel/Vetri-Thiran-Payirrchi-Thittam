# LegalEase - AI Legal Document Generator

Streamlit frontend + FastAPI backend + Google Gemini. Generates legal documents, lets you edit them,
and exports to .txt, .docx and .pdf.

## Structure
```
LegalEase/
├── ai_core/
│   ├── gemini_generator.py   # Gemini API call (GeminiDocumentGenerator)
│   └── generator.py          # sanitize_text, format_docx, format_pdf, format_html_preview
├── legalEaseAPI/
│   ├── main.py               # FastAPI app, "/" route
│   └── routes.py             # DocumentRequest model, POST /generate, GET /health
├── frontend/app.py           # Streamlit UI
├── Image/                    # Logo.png (docs), inverseLogo.png (dark web UI)
├── tests/test_legalease.py
├── config.py  .env  requirements.txt  run.sh  run.bat  make_logos.py
```

## Setup (VS Code)
1. Install Python 3.10+ and open the LegalEase folder in VS Code (File > Open Folder).
2. Open a terminal (Ctrl+`) and create the virtual environment:
   - Windows: `python -m venv venv` then `venv\Scripts\activate`
   - macOS/Linux: `python3 -m venv venv` then `source venv/bin/activate`
3. `pip install -r requirements.txt`
4. Open `.env` and set `GEMINI_API_KEY` (free key: https://aistudio.google.com/app/apikey).
5. In VS Code press Ctrl+Shift+P > "Python: Select Interpreter" > choose the `venv` one.

## Run
Two terminals, both with the venv active:
```
uvicorn legalEaseAPI.main:app --reload        # backend  -> http://127.0.0.1:8000
streamlit run frontend/app.py                 # frontend -> http://localhost:8501
```
Shortcut: `run.bat` (Windows) or `./run.sh` (macOS/Linux/Git Bash) starts both.

## Test
- Offline unit tests (no key needed): `pytest -q`
- Backend: open http://127.0.0.1:8000/docs, try POST /generate.
- End to end in the UI, sample input:
  - Document Type: `Freelance Work Contract`
  - Parties: `Jane Doe (Service Provider), TechNova Inc. (Client)`
  - Terms: `Work must be delivered by May 15, 2025; Payment within 7 days of invoice; The client retains intellectual property rights; Confidentiality must be maintained at all times`
  - Effective Date: `April 15, 2025`
  Then Generate, Edit, and download all three formats.

## Troubleshooting
- "Cannot reach the backend": start uvicorn first (port 8000).
- 503 "GEMINI_API_KEY is not set": fix `.env`, restart uvicorn.
- 502 with a 404 / model error: change `GEMINI_MODEL` in `.env` (e.g. `gemini-2.5-flash`, `gemini-2.5-pro`).
- Replace the placeholder logos in `Image/` with your own (same file names).

AI-generated drafts are not legal advice; have a lawyer review important documents.
