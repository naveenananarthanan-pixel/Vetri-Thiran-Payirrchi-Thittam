"""LegalEase - Streamlit frontend. Run with:  streamlit run frontend/app.py"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # so `config` and `ai_core` can be imported

import requests
import streamlit as st

from ai_core.generator import (
    format_docx,
    format_html_preview,
    format_pdf,
    sanitize_text,
    slugify,
)
from config import BACKEND_URL, REQUEST_TIMEOUT, WEB_LOGO_PATH

st.set_page_config(page_title="LegalEase", page_icon="⚖️", layout="centered")

# ------------------------------------------------------------------ header
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if WEB_LOGO_PATH.exists():
        st.image(str(WEB_LOGO_PATH), use_container_width=True)
    else:
        st.markdown("<h1 style='text-align:center;'>⚖️ LegalEase</h1>", unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center;'>AI Legal Document Generator</h2>", unsafe_allow_html=True)

# ------------------------------------------------------------------ session state
for key, default in {"generated_text": "", "show_edit": False, "meta": {}}.items():
    st.session_state.setdefault(key, default)

# ------------------------------------------------------------------ inputs
document_type = st.text_input("Document Type (Ex: Agreement, Contract, NDA)")
parties = st.text_area("Parties Involved")
terms = st.text_area("Terms & Conditions (Use semicolons for bullet points)")
dates = st.text_input("Effective Date")

if st.button("Generate Document"):
    if not (document_type.strip() and parties.strip() and terms.strip()):
        st.warning("Please fill in Document Type, Parties Involved and Terms & Conditions.")
    else:
        with st.spinner("Drafting your document with Gemini..."):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/generate",
                    json={
                        "document_type": document_type,
                        "parties": parties,
                        "terms": terms,
                        "dates": dates,
                    },
                    timeout=REQUEST_TIMEOUT,
                )
                if response.ok:
                    text = sanitize_text(response.json()["document"])
                    st.session_state.generated_text = text
                    st.session_state.edit_area = text  # reset the editor
                    st.session_state.show_edit = False
                    st.session_state.meta = {"document_type": document_type, "terms": terms}
                    st.success("✅ Document Generated Successfully!")
                else:
                    try:
                        detail = response.json().get("detail", response.text)
                    except ValueError:
                        detail = response.text
                    if isinstance(detail, list):  # FastAPI validation errors
                        detail = "; ".join(str(d.get("msg", d)) for d in detail)
                    st.error(f"Backend error ({response.status_code}): {detail}")
            except requests.exceptions.ConnectionError:
                st.error(f"Cannot reach the backend at {BACKEND_URL}. Is uvicorn running?")
            except requests.exceptions.Timeout:
                st.error("The request timed out. Please try again.")

if not st.session_state.generated_text:
    st.info("Click 'Generate Document' to start")
    st.stop()

# ------------------------------------------------------------------ preview
meta = st.session_state.meta
doc_type = meta.get("document_type", document_type or "Legal Document")
doc_terms = meta.get("terms", "")
generated_text = st.session_state.generated_text

styled_html = format_html_preview(generated_text)
st.markdown(
    "<div style='background:#111827;color:#e5e7eb;padding:20px 24px;border-radius:10px;"
    "max-height:420px;overflow-y:auto;border:1px solid #1f2937;font-family:Georgia,serif;"
    f"font-size:15px;'>{styled_html}</div>",
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------ edit
if st.button("✏️ Click to Edit Document"):
    st.session_state.show_edit = not st.session_state.show_edit
    st.session_state.edit_area = st.session_state.generated_text


def _apply_edit():
    st.session_state.generated_text = st.session_state.edit_area


if st.session_state.show_edit:
    st.text_area("Edit Document Below:", height=300, key="edit_area", on_change=_apply_edit)
    generated_text = st.session_state.get("edit_area", generated_text)
    st.session_state.generated_text = generated_text

# ------------------------------------------------------------------ downloads
base = slugify(doc_type)
st.download_button(
    "📄 Download as .TXT",
    data=generated_text.encode("utf-8"),
    file_name=f"{base}.txt",
    mime="text/plain",
)
st.download_button(
    "📝 Download as .DOCX",
    data=format_docx(generated_text, doc_type, doc_terms),
    file_name=f"{base}.docx",
    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
)
st.download_button(
    "📕 Download as .PDF",
    data=format_pdf(generated_text, doc_type, doc_terms),
    file_name=f"{base}.pdf",
    mime="application/pdf",
)
st.caption("AI-generated drafts are not legal advice. Have a qualified lawyer review important documents.")
