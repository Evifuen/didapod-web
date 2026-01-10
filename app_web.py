import streamlit as st
import edge_tts
import asyncio
import os
import base64
import speech_recognition as sr
from deep_translator import GoogleTranslator
from pydub import AudioSegment

# --- 1. CONFIGURACIÓN Y ESTILO VISUAL (CORREGIDO) ---
st.set_page_config(page_title="DIDAPOD - DidactAI", page_icon="🎙️", layout="centered")

def get_base64(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f: return base64.b64encode(f.read()).decode()
    return None

logo_base64 = get_base64("logo.png")

st.markdown(f"""
    <style>
    .stApp {{ background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%); }}
    .main-title {{ color: white; font-size: 42px; font-weight: 800; }}
    /* ESTE BLOQUE HACE QUE EL CLICK HERE SE VEA BLANCO Y CLARO */
    .stExpander {{ background: rgba(255, 255, 255, 0.1); border-radius: 10px; border: 1px solid #7c3aed; }}
    .stExpander p, .stExpander span {{ color: white !important; font-weight: bold !important; font-size: 18px !important; }}
    
    .stButton>button {{ 
        background-color: #7c3aed !important; color: white !important; 
        border-radius: 12px; font-weight: bold; width: 100%; border: none;
    }}
    .preview-card {{ 
        background: rgba(124, 58, 237, 0.2); padding: 25px; border-radius: 15px; 
        margin-top: 25px; border: 2px solid #7c3aed;
    }}
    label, .stMarkdown p {{ color: white !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGIN ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    with st.form("login"):
        u, p = st.text_input("User"), st.text_input("Pass", type="password")
        if st.form_submit_button("Login"):
            if u == "admin" and p == "didactai2026":
                st.session_state["auth"] = True
                st.rerun()
    st.stop()

# --- 3. BRANDING ---
c1, c2 = st.columns([1, 4])
with c1:
    if logo_base64: st.markdown(f'<img src="data:image/png;base64,{logo_base64}" width="100">', unsafe_allow_html=True)
with c2:
    st.markdown('<p class="main-title">DIDAPOD PRO</p><p style="color:#94a3b8;">Powered by DidactAI-US</p>', unsafe_allow_html=True)

# --- 4. LÓGICA DE PROCESAMIENTO ---
target_lang = st.selectbox("Select Target Language:", ["English", "Spanish", "French"])
up_file = st.file_uploader("Upload podcast", type=["mp3", "wav"])

if up_file:
    st.audio(up_file)
    if st.button("🚀 START AI DUBBING"):
        try:
            with st.status("🤖 Processing...", expanded=True) as status:
                with open("temp.mp3", "wb") as f: f.write(up_file.getbuffer())
                audio = AudioSegment.from_file("temp.mp3")
                # Fragmentos de 40 seg para evitar error de 5000 caracteres
                chunks = [audio[i:i + 40000] for i in range(0, len(audio), 40000)]
                
                final_audio = AudioSegment.empty()
                r = sr.Recognizer()
                codes = {"English": "en", "Spanish": "es", "French": "fr"}
                voice_m = {"English": "en-US-EmmaMultilingualNeural", "Spanish": "es-ES-ElviraNeural", "French": "fr-FR-DeniseNeural"}

                for i, chunk in enumerate(chunks):
                    st.write(f"🔄 Segment {i+1}/{len(chunks)}...")
                    chunk.export("c.wav", format="wav")
                    with sr.AudioFile("c.wav") as src:
                        try:
                            text = r.recognize_google(r.record(src), language="es-ES")
                            trans = GoogleTranslator(source='auto', target=codes[target_lang]).translate(text)
                            asyncio.run(edge_tts.Communicate(trans, voice_m[target_lang]).save(f"v{i}.mp3"))
                            final_audio += AudioSegment.from_file(f"v{i}.mp3")
                            os.remove(f"v{i}.mp3")
                        except: continue
                
                final_audio.export("result.mp3", format="mp3")
                status.update(label="Complete!", state="complete")
            
            st.balloons()
            
            # --- SECCIÓN DE RESULTADO CON TEXTO VISIBLE ---
            st.markdown('<div class="preview-card">', unsafe_allow_html=True)
            st.markdown("<h3 style='color:white;'>✅ Podcast Dubbed Successfully</h3>", unsafe_allow_html=True)
            
            # Aquí el expander ahora tiene estilo forzado para verse blanco
            with st.expander("▶️ CLICK HERE TO LISTEN BEFORE DOWNLOADING"):
                st.audio("result.mp3")
            
            st.markdown("<br>", unsafe_allow_html=True)
            with open("result.mp3", "rb") as f:
                st.download_button("📥 DOWNLOAD FINAL FILE", f, "didapod_result.mp3")
            st.markdown('</div>', unsafe_allow_html=True)

        except Exception as e: st.error(f"Error: {e}")

st.markdown("<br><hr><center><small style='color:#94a3b8;'>© 2026 DidactAI-US</small></center>", unsafe_allow_html=True)










