import streamlit as st
import edge_tts
import asyncio
import os
import base64
import speech_recognition as sr
from deep_translator import GoogleTranslator
from pydub import AudioSegment

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="DIDAPOD - DidactAI", page_icon="🎙️", layout="centered")

# Función mágica para que el logo cargue sí o sí
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Intentamos cargar el logo local
try:
    logo_base64 = get_base64_of_bin_file('logo.png')
    logo_html = f'<img src="data:image/png;base64,{logo_base64}" width="80" style="vertical-align: middle; margin-right: 20px; border-radius: 10px;">'
except:
    logo_html = "🎙️ " # Respaldo si el archivo no existe

st.markdown(f"""
    <style>
    .stApp {{ background-color: #0f172a !important; }}
    
    /* ENCABEZADO PERSONALIZADO */
    .main-header {{
        display: flex;
        align-items: center;
        margin-bottom: 20px;
    }}

    /* BOTÓN "CLICK HERE" MORADO CON TEXTO BLANCO */
    .stExpander {{ 
        background-color: #7c3aed !important; 
        border: 2px solid white !important; 
        border-radius: 12px !important;
    }}
    .stExpander summary, .stExpander summary * {{ 
        color: white !important; 
        font-weight: 800 !important; 
        font-size: 18px !important;
        text-transform: uppercase;
    }}
    
    /* BOTONES DE ACCIÓN */
    .stButton>button, .stDownloadButton>button {{ 
        background-color: #7c3aed !important; 
        color: white !important; 
        border-radius: 12px !important; 
        padding: 18px !important; 
        font-weight: 800 !important; 
        width: 100% !important; 
        border: 1px solid white !important;
    }}
    
    h1, h2, h3, label, p, span {{ color: white !important; }}
    </style>
    
    <div class="main-header">
        {logo_html}
        <h1 style="display: inline; margin: 0; color: white;">DIDAPOD PRO</h1>
    </div>
    <p style="color: #94a3b8 !important; margin-left: 100px; margin-top: -15px;">Safe Cascade Dubbing System</p>
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

# --- 3. PROCESAMIENTO ---
target_lang = st.selectbox("Target Language:", ["English", "Spanish", "French"])
up_file = st.file_uploader("Upload podcast", type=["mp3", "wav"])

if up_file:
    st.audio(up_file)
    if st.button("🚀 START AI DUBBING"):
        try:
            with st.status("🤖 Processing...", expanded=True) as status:
                with open("temp.mp3", "wb") as f: f.write(up_file.getbuffer())
                audio = AudioSegment.from_file("temp.mp3")
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
            
            # --- RESULTADO FINAL ---
            st.markdown("<div style='background: rgba(255,255,255,0.05); padding: 25px; border-radius: 20px; border: 1px solid #7c3aed;'>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align:center;'>✅ Your Podcast is Ready</h3>", unsafe_allow_html=True)
            
            with st.expander("▶️ CLICK HERE TO LISTEN BEFORE DOWNLOADING"):
                st.audio("result.mp3")
            
            st.write("")
            with open("result.mp3", "rb") as f:
                st.download_button("📥 DOWNLOAD FINAL FILE", f, "didapod_result.mp3")
            st.markdown("</div>", unsafe_allow_html=True)

        except Exception as e: st.error(f"Error: {e}")

st.markdown("<br><hr><center><small style='color:#94a3b8;'>© 2026 DidactAI-US</small></center>", unsafe_allow_html=True)

