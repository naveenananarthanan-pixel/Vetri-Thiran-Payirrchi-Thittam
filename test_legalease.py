"""Offline tests - no Gemini key or internet needed. Run:  pytest -q"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from ai_core import generator as g

SAMPLE = """## Freelance Work Contract

Agreement made this 15th day of April, 2025 \u2013 \u201cEffective Date\u201d.

**Between:**

Jane Doe (the "Service Provider") and TechNova Inc. (the "Client").

1. Services:
The Service Provider shall deliver **all work** by May 15, 2025.

* Payment within 7 days of invoice
* Client retains intellectual property rights
"""


def test_sanitize_removes_typographic_chars():
    out = g.sanitize_text("\u201cHi\u201d \u2014 it\u2019s \u2022 ok\u2026")
    assert out == '"Hi" - it\'s - ok...'


def test_parse_blocks_kinds_and_title_dedup():
    kinds = [k for k, _ in g.parse_blocks(SAMPLE, "Freelance Work Contract")]
    assert kinds[0] == "para"  # duplicate title heading removed
    assert "heading" in kinds and "bullet" in kinds


def test_html_preview_escapes():
    html = g.format_html_preview("<script>alert(1)</script>\n- item **bold**")
    assert "<script>" not in html and "<li>" in html and "<b>bold</b>" in html


def test_docx_bytes():
    data = g.format_docx(SAMPLE, "Freelance Work Contract", "A; B; C")
    assert data[:2] == b"PK"
    from docx import Document
    import io

    d = Document(io.BytesIO(data))
    assert len(d.tables) == 1 and len(d.tables[0].rows) == 4


def test_pdf_bytes():
    pytest.importorskip("fpdf")
    data = g.format_pdf(SAMPLE * 30, "Freelance Work Contract", "A; B; C")
    assert data[:4] == b"%PDF"


def test_api_generate(monkeypatch):
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient

    from legalEaseAPI import routes
    from legalEaseAPI.main import app

    monkeypatch.setattr(routes.gemini_generator, "generate_document", lambda *a: "DOC TEXT")
    client = TestClient(app)
    assert client.get("/").status_code == 200
    r = client.post("/generate", json={"document_type": "NDA", "parties": "A, B", "terms": "x;y", "dates": "today"})
    assert r.status_code == 200 and r.json() == {"document": "DOC TEXT"}
    assert client.post("/generate", json={"document_type": "", "parties": "", "terms": ""}).status_code == 422


def test_missing_key_gives_503(monkeypatch):
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient

    from ai_core.gemini_generator import GeminiDocumentGenerator
    from legalEaseAPI import routes
    from legalEaseAPI.main import app

    monkeypatch.setattr(routes, "gemini_generator", GeminiDocumentGenerator(api_key=""))
    r = TestClient(app).post("/generate", json={"document_type": "NDA", "parties": "A, B", "terms": "x;y"})
    assert r.status_code == 503
