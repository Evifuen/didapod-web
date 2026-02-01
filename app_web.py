import streamlit as st
import azure.cognitiveservices.speech as speechsdk
from deep_translator import GoogleTranslator
from pydub import AudioSegment
import speech_recognition as sr
import os
import base64

# --- 0. CREDENCIALES AUTOMÁTICAS ---
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
    .stButton>button { background-color: #7c3aed !important; color: white !important; border-radius: 12px !important; font-weight: 800 !important; width: 100% !important; border: 1px solid white !important; }
    h1, h2, h3, label, p, span { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIN & REGISTRO DE EMAIL ---
if "auth" not in st.session_state: st.session_state["auth"] = False

if not st.session_state["auth"]:
    with st.form("login"):
        st.markdown("### 📝 Acceso Clientes")
        email_cliente = st.text_input("📧 Tu Email para registro")
        # Relleno automático de User y Pass para que no tengas que escribirlos
        u = st.text_input("User", value="admin")
        p = st.text_input("Pass", type="password", value="didactai2026")
        
        if st.form_submit_button("Entrar a DIDAPOD"):
            if email_cliente and u == "admin" and p == "didactai2026":
                # GUARDAR EMAIL (Para tu base de datos de clientes)
                with open("clientes.txt", "a") as f:
                    f.write(f"{email_cliente}\n")
                st.session_state["auth"] = True
                st.rerun()
            else:
                st.error("Por favor rellena el email y usa las credenciales correctas.")
    st.stop()

# --- 4. ENCABEZADO ---
st.markdown("<h1 style='text-align:center;'>🎙️ DIDAPOD PRO</h1>", unsafe_allow_html=True)
st.write("---")

# --- 5. PROCESAMIENTO ---
target_lang = st.selectbox("Select Target Language:", ["English", "Spanish", "French", "Portuguese"])
up_file = st.file_uploader("Upload podcast", type=["mp3", "wav"])

if up_file:
    st.audio(up_file)
    if st.button("🚀 START AI DUBBING"):
        try:
            with st.spinner("🤖 AI Dubbing in progress..."):
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
                            # Traducción
                            text = r.recognize_google(r.record(src), language="es-ES")
                            trans = GoogleTranslator(source='auto', target=codes[target_lang]).translate(text)
                            
                            # MOTOR AZURE (Aquí es donde ocurre la magia)
                            speech_config = speechsdk.SpeechConfig(subscription=AZURE_KEY, region=AZURE_REGION)
                            speech_config.speech_synthesis_voice_name = voice_m[target_lang]
                            
                            nombre_v = f"v{i}.mp3"
                            audio_out = speechsdk.audio.AudioOutputConfig(filename=nombre_v)
                            syn = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_out)
                            
                            # El .get() es lo que hace que el contador de Azure suba
                            syn.speak_text_async(trans).get() 
                            
                            final_audio += AudioSegment.from_file(nombre_v)
                            os.remove(nombre_v)
                        except Exception as e:
                            st.write(f"Fragmento {i} saltado: {e}")
                            continue
                
                final_audio.export("result.mp3", format="mp3")
                st.balloons()
                st.audio("result.mp3")
                with open("result.mp3", "rb") as f:
                    st.download_button("📥 DOWNLOAD FINAL PODCAST", f, "didapod_pro.mp3")

        except Exception as e: st.error(f"Error crítico: {e}")

st.markdown("<br><hr><center><small style='color:#94a3b8;'>© 2026 DidactAI-US</small></center>", unsafe_allow_html=True)



















