# frontend/app.py - Streamlit user interface
import os
import sys

# let the frontend import config.py and ai_core from the project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import streamlit as st

from ai_core.generator import (format_docx, format_html_preview, format_pdf,
                               sanitize_text)
from config import API_URL, WEB_LOGO_PATH

st.set_page_config(page_title="LegalEase", layout="centered")

# Logo (centered) and title
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if os.path.exists(WEB_LOGO_PATH):
        st.image(WEB_LOGO_PATH, use_container_width=True)
    else:
        st.markdown("<h1 style='text-align:center'>LegalEase</h1>", unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center;'>AI Legal Document Generator</h2>",
            unsafe_allow_html=True)

# Inputs
document_type = st.text_input("Document Type (Ex: Agreement, Contract, NDA)")
parties = st.text_area("Parties Involved")
terms = st.text_area("Terms & Conditions (Use semicolons for bullet points)")
dates = st.text_input("Effective Date")

if st.button("Generate Document"):
    if not all([document_type.strip(), parties.strip(), terms.strip(), dates.strip()]):
        st.warning("Please fill in all the fields.")
    else:
        try:
            with st.spinner("Generating your document..."):
                response = requests.post(API_URL, json={
                    "document_type": document_type,
                    "parties": parties,
                    "terms": terms,
                    "dates": dates,
                }, timeout=180)
            if response.status_code == 200:
                st.session_state.generated_text = sanitize_text(response.json()["document"])
                st.session_state.doc_type = document_type
                st.session_state.terms = terms
                st.session_state.show_edit = False
                st.success("Document Generated Successfully!")
            else:
                st.error(f"Backend error: {response.text}")
        except requests.exceptions.ConnectionError:
            st.error("Cannot reach the backend. Start it with: uvicorn legalEaseAPI.main:app --reload")
        except Exception as e:
            st.error(f"Something went wrong: {e}")

if "generated_text" in st.session_state:
    generated_text = st.session_state.generated_text
    doc_type = st.session_state.doc_type

    # Dark scrollable HTML preview
    styled_html = format_html_preview(generated_text)
    st.markdown(
        "<div style='background:#0e1525;padding:18px;border-radius:10px;"
        "max-height:350px;overflow-y:auto'>" + styled_html + "</div>",
        unsafe_allow_html=True,
    )

    # Edit
    if st.button("✏️ Click to Edit Document"):
        st.session_state.show_edit = True
    if st.session_state.get("show_edit"):
        edited_text = st.text_area("Edit Document Below:", generated_text, height=300)
        st.session_state.generated_text = edited_text
        generated_text = edited_text

    # Downloads
    name = doc_type.replace(" ", "_").lower()
    st.download_button("📄 Download as .TXT", data=generated_text,
                       file_name=f"{name}.txt", mime="text/plain")
    st.download_button("📝 Download as .DOCX",
                       data=format_docx(generated_text, doc_type, st.session_state.terms),
                       file_name=f"{name}.docx",
                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    st.download_button("📕 Download as .PDF", data=format_pdf(generated_text, doc_type),
                       file_name=f"{name}.pdf", mime="application/pdf")
else:
    st.info("Click 'Generate Document' to start")
