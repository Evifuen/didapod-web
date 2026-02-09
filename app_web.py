import streamlit as st
import edge_tts
import asyncio
import os
import base64
import speech_recognition as sr
from deep_translator import GoogleTranslator
from pydub import AudioSegment
import pandas as pd
import requests
import re

# ==========================================
# BASE DE DATOS EN LA NUBE (APPS SCRIPT)
# ==========================================
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwbUqyrHKND1oougAUdjNr944XDKlI8psAdlCUKDN_rJQzjcv46RdDTjkTuLIPxGn78YA/exec"  # <-- SOLO ESTE CAMPO DEBES CAMBIAR

def register_email_cloud(email: str) -> bool:
    try:
        r = requests.post(APPS_SCRIPT_URL, data={"email": email}, timeout=10)
        if r.ok:
            return True
        else:
            st.error(f"Error HTTP {r.status_code}")
            return False
    except Exception as e:
        st.error(f"Error conectando con la nube: {e}")
        return False


def check_email_limit(email: str) -> int:
    """Recupera los registros de Apps Script en CSV automáticamente."""
    try:
        csv_url = APPS_SCRIPT_URL + "?format=csv"
        df = pd.read_csv(csv_url)
        return df[df.apply(lambda r: email in str(r), axis=1)].shape[0]
    except:
        return 0

# ==========================================
# EL RESTO DE TU APP QUEDA IGUAL
# ==========================================

st.set_page_config(page_title="DIDAPOD - DidactAI", page_icon="🎙️", layout="centered")

def get_base64_logo(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            data = f.read()
            return base64.b64encode(data).decode()
    return None

logo_data = get_base64_logo("logo2.png")

st.markdown("""
<style>
/* ... ESTILO ... */
</style>
""", unsafe_allow_html=True)

# LOGIN
if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    with st.form("login"):
        st.markdown("### 🔐 ACCESS PANEL")
        user_email = st.text_input("Email Address")
        u = st.text_input("User", value="admin")
        p = st.text_input("Pass", type="password", value="didactai2026")
        
        if st.form_submit_button("Login"):
            if u == "admin" and p == "didactai2026":
                if user_email and "@" in user_email:
                    attempts = check_email_limit(user_email)
                    if attempts >= 2:
                        st.error("🚫 Access denied.")
                    else:
                        if register_email_cloud(user_email):
                            st.session_state["auth"] = True
                            st.rerun()
                else:
                    st.error("Invalid email.")
    st.stop()

# ... EL RESTO DE TU APP SIGUE IGUAL...

