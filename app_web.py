import pandas as pd
from streamlit_gsheets import GSheetsConnection
import streamlit as st
import azure.cognitiveservices.speech as speechsdk
from deep_translator import GoogleTranslator
from pydub import AudioSegment
import speech_recognition as sr
import os
import base64

# --- 0. AUTOMATIC CREDENTIALS ---
AZURE_KEY = st.secrets["AZURE_SPEECH_KEY"]
AZURE_REGION = st.secrets["AZURE_SPEECH_REGION"]

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="DIDAPOD PRO", page_icon="🎙️", layout="centered")

def get_base64_logo(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

# Carga del logo (Asegúrate de que el archivo se llame logo2.png en GitHub)
logo_data = get_base64_logo("logo2.png")

# --- 2. PROFESSIONAL DESIGN (CORREGIDO) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0f172a !important; }}
    
    /* BOTÓN DE LOGIN EN NEGRO CON TEXTO BLANCO */
    div.stButton > button {{
        background-color: #000000 !important;
        color: #ffffff !important;
        border: 2px solid #ffffff !important;
        border-radius: 10px !important;
        padding: 10px 20px !important;
        font-weight: bold !important;
        width: 100% !important;
        height: 50px !important;
    }}

    div.stButton > button:hover {{
        background-color: #1e293b !important;
        border-color: #7c3aed !important;
        color: #7c3aed !important;
    }}

    /* Estilos para textos */
    h1, h2, h3, label, p, span {{ color: white !important; }}
    
    .logo-container {{
        text-align: center;
        margin-bottom: 30px;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. MOSTRAR LOGO ---
if logo_data:
    st.markdown(f'<div class="logo-container"><img src="data:image/png;base64,{logo_data}" width="250"></div>', unsafe_allow_html=True)

# --- 4. LOGIN & REGISTRATION ---
if "auth" not in st.session_state: 
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    with st.form("login"):
        st.markdown("### 📝 DIDAPOD PRO ACCESS")
        email_cliente = st.text_input("📧 Your Email for registration")
        u = st.text_input("Username", value="admin")
        p = st.text_input("Password", type="password", value="didactai2026")
        
        # El botón ahora será negro con texto blanco
        if st.form_submit_button("ENTER DIDAPOD"):
            if email_cliente and u == "admin" and p == "didactai2026":
                try:
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    try:
                        df_existente = conn.read()
                    except:
                        df_existente = pd.DataFrame(columns=["Email", "Date"])
                    
                    nuevo_registro = pd.DataFrame([{"Email": email_cliente, "Date": str(pd.Timestamp.now())}])
                    df_final = pd.concat([df_existente, nuevo_registro], ignore_index=True)
                    conn.update(data=df_final)
                    
                    st.session_state["auth"] = True
                    st.session_state["user_email"] = email_cliente 
                    st.rerun()
                except Exception as e:
                    st.error(f"Database connection error: {e}")
            else:
                st.error("Please enter a valid email and correct credentials.")
    st.stop() 

# --- 5. HEADER (CONTENIDO PRINCIPAL) ---
st.markdown("<h1 style='text-align:center;'>🎙️ DIDAPOD PRO</h1>", unsafe_allow_html=True)
st.write("---")

# Aquí continúa el resto de tu lógica de traducción y Azure...
