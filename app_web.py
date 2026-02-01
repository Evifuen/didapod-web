import azure.cognitiveservices.speech as speechsdk
import streamlit as st
import azure.cognitiveservices.speech
import asyncio
import os
import base64
import speech_recognition as sr
from deep_translator import GoogleTranslator
from pydub import AudioSegment
AZURE_KEY = st.secrets["AZURE_SPEECH_KEY"]
AZURE_REGION = st.secrets["AZURE_SPEECH_REGION"]

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="DIDAPOD PRO", page_icon="🎙️", layout="centered")

def get_base64_logo(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

logo_data = get_base64_logo("logo2.png.png")

# --- 2. DISEÑO PROFESIONAL ---
st.markdown("""
    <style>
    .stApp { background-color: #0f172a !important; }
    .stExpander { 
        background-color: #7c3aed !important; 
        border: 2px solid white !important; 
        border-radius: 12px !important;
    }
    .stExpander summary p { 
        color: white !important; 
        font-weight: 800 !important; 
        font-size: 1.1rem !important;
    }
    .stButton>button, .stDownloadButton>button { 
        background-color: #7c3aed !important; 
        color: white !important; 
        border-radius: 12px !important; 
        padding: 18px !important; 
        font-weight: 800 !important; 
        width: 100% !important; 
        border: 1px solid white !important;
    }
    h1, h2, h3, label, p, span { color: white !important; }
    .stSpinner > div { border-top-color: #7c3aed !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIN ---
# --- 3. LOGIN & REGISTRO DE CLIENTES ---
if "auth" not in st.session_state: st.session_state["auth"] = False

if not st.session_state["auth"]:
    with st.form("login"):
        st.markdown("### 📝 Register & Access")
        # Capturamos el email del cliente
        email_cliente = st.text_input("📧 Your Email")
        
        # Relleno automático para facilitar la entrada del admin
        u = st.text_input("User", value="admin") 
        p = st.text_input("Pass", type="password", value="didactai2026")
        
        if st.form_submit_button("Access DIDAPOD"):
            if email_cliente and u == "admin" and p == "didactai2026":
                # GUARDAR EMAIL: Lo guardamos en un archivo de texto
                with open("clientes.txt", "a") as f:
                    f.write(f"{email_cliente}\n")
                
                st.session_state["auth"] = True
                st.session_state["user_email"] = email_cliente
                st.rerun()
            else:
                st.error("Please provide a valid email and credentials.")
    st.stop()

# --- 4. ENCABEZADO ---
col_l, col_r = st.columns([1, 4])
with col_l:
    if logo_data:
        st.markdown(f'<img src="data:image/png;base64,{logo_data}" width="100" style="border-radius:10px;">', unsafe_allow_html=True)
with col_r:
    st.markdown("<h1 style='margin:0;'>DIDAPOD PRO</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94a3b8 !important; margin:0;'>AI Powered Cascade Dubbing</p>", unsafe_allow_html=True)

st.write("---")

# --- 5. PROCESAMIENTO ---
target_lang = st.selectbox("Select Target Language:", ["English", "Spanish", "French", "Portuguese"])
up_file = st.file_uploader("Upload podcast", type=["mp3", "wav"])

if up_file:
    st.audio(up_file)
    if st.button("🚀 START AI DUBBING"):
        try:
            with st.spinner("🤖 AI Dubbing in progress... please wait"):
                with open("temp.mp3", "wb") as f: f.write(up_file.getbuffer())
                audio = AudioSegment.from_file("temp.mp3")
                chunks = [audio[i:i + 40000] for i in range(0, len(audio), 40000)]
                final_audio = AudioSegment.empty()
                r = sr.Recognizer()
                codes = {"English": "en", "Spanish": "es", "French": "fr", "Portuguese": "pt"}
                voice_m = {"English": "en-US-EmmaMultilingualNeural", "Spanish": "es-ES-ElviraNeural", "French": "fr-FR-DeniseNeural", "Portuguese": "pt-BR-FranciscaNeural"}

                for i, chunk in enumerate(chunks):
                    chunk.export("c.wav", format="wav")
                    with sr.AudioFile("c.wav") as src:
                        try:
                            # 1. Transcripción y Traducción
                            text = r.recognize_google(r.record(src), language="es-ES")
                            trans = GoogleTranslator(source='auto', target=codes[target_lang]).translate(text)
                            
                            # 2. Configuración de Azure (Alineado con el texto de arriba)
                            speech_config = speechsdk.SpeechConfig(
                                subscription=st.secrets["AZURE_SPEECH_KEY"], 
                                region=st.secrets["AZURE_SPEECH_REGION"]
                            )
                            speech_config.speech_synthesis_voice_name = voice_m[target_lang]
                            
                            # 3. Generación del audio profesional
                            nombre_archivo = f"v{i}.mp3"
                            audio_output = speechsdk.audio.AudioOutputConfig(filename=nombre_archivo)
                            synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_output)
                            
                            # El .get() asegura que el archivo no pese 261 bytes
                            synthesizer.speak_text_async(trans).get() 
                            
                            # 4. Unión del audio
                            final_audio += AudioSegment.from_file(nombre_archivo)
                            os.remove(nombre_archivo)
                            # --- CONFIGURACIÓN DE AZURE (Fuera del bucle para mayor velocidad) ---
                speech_config = speechsdk.SpeechConfig(
                    subscription=AZURE_KEY, 
                    region=AZURE_REGION
                )
                        except Exception as e:
                            st.write(f"Error en fragmento {i}: {e}")
                            continue 
                   
                final_audio.export("result.mp3", format="mp3")
            
            st.balloons()
            st.markdown("<div style='background: rgba(255,255,255,0.05); padding: 25px; border-radius: 20px; border: 1px solid #7c3aed;'>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align:center;'>✅ PODCAST READY</h3>", unsafe_allow_html=True)
            with st.expander("▶️ CLICK HERE TO LISTEN BEFORE DOWNLOADING"):
                st.audio("result.mp3")
            st.write("")
            with open("result.mp3", "rb") as f:
                st.download_button("📥 DOWNLOAD FINAL FILE", f, "didapod_result.mp3")
            st.markdown("</div>", unsafe_allow_html=True)

        except Exception as e: st.error(f"Error: {e}")

st.markdown("<br><hr><center><small style='color:#94a3b8;'>© 2026 DidactAI-US</small></center>", unsafe_allow_html=True)


















