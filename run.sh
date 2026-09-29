#!/usr/bin/env bash
# Starts the FastAPI backend (port 8000) and the Streamlit frontend (port 8501).
cd "$(dirname "$0")"
[ -d venv ] && source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null
uvicorn legalEaseAPI.main:app --reload --port 8000 &
BACK=$!
trap "kill $BACK" EXIT
streamlit run frontend/app.py
