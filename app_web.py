import streamlit as st
import azure.cognitiveservices.speech as speechsdk
import os, time, base64, requests
from datetime import datetime
from pydub import AudioSegment

# --- 0. CONFIGURACIÓN CLOUD (Google Sheets) ---
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwLIO5CsYs-7Z2xt335yT2ZQx9Hp3sxfVY7Bzvpdmu3LsD6uHTxvpukLHb2AAjMvDk2qA/exec"

# --- 1. CONFIGURATION & STYLE ---
st.set_page_config(page_title="DIDAPOD PRO", page_icon="🎙️", layout="centered")

def get_base64_logo(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

logo_data = get_base64_logo("logo2.png")

st.markdown("""
    <style>
    .stApp { background-color: #0f172a !important; }
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
    .stProgress > div > div > div > div { background-color: #7c3aed !important; }
    </style>
    """, unsafe_allow_html=True)

def get_clean_secret(name):
    val = st.secrets.get(name, "")
    return "".join(str(val).split()).replace('"', '').replace("'", "").strip()

AZ_KEY = get_clean_secret("AZURE_KEY")
AZ_REG = get_clean_secret("AZURE_SPEECH_REGION")

# --- 2. LOGIN OBLIGATORIO ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    with st.form("login"):
        st.markdown("### 🔐 ACCESS PANEL")
        user_email = st.text_input("Email Address")
        u = st.text_input("User", value="admin")
        p = st.text_input("Pass", type="password", value="didactai2026")
        if st.form_submit_button("Login"):
            if u == "admin" and p == "didactai2026" and "@" in user_email:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # REGISTRO EN GOOGLE SHEETS
                try:
                    requests.post(APPS_SCRIPT_URL, json={"email": user_email, "timestamp": timestamp})
                    # También guardamos local por respaldo
                    with open("database_emails.txt", "a") as f:
                        f.write(f"{timestamp} | {user_email}\n")
                except: pass
                st.session_state["auth"] = True
                st.rerun()
            else: st.error("Invalid credentials.")
    st.stop()

# --- 3. HEADER ---
col_l, col_r = st.columns([1, 4])
with col_l:
    if logo_data:
        st.markdown(f'<img src="data:image/png;base64,{logo_data}" width="110" style="border-radius:10px;">', unsafe_allow_html=True)
with col_r:
    st.markdown("<h1 style='margin:0;'>🎙️ DIDAPOD PRO</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94a3b8 !important; margin:0;'>Long Audio Enterprise Support</p>", unsafe_allow_html=True)

# --- 4. MOTOR ORIGINAL (SIN TOCAR LÓGICA) ---
target_lang = st.selectbox("Idioma Destino:", ["English", "Spanish", "French", "Portuguese"])
voice_gender = st.selectbox("Género de Voz:", ["Female", "Male"])
up_file = st.file_uploader("Sube tu podcast", type=["mp3", "wav"])

if up_file and AZ_KEY:
    st.audio(up_file)
    if st.button("🚀 START AI DUBBING"):
        all_text = []
        state = {"done": False}
        
        try:
            with st.spinner(f"⌛ Procesando {up_file.name} (22+ min). Esto puede tardar..."):
                # 1. Preparar audio largo
                audio = AudioSegment.from_file(up_file)
                audio = audio.set_frame_rate(16000).set_channels(1)
                temp_wav = "temp_long.wav"
                audio.export(temp_wav, format="wav")

                # 2. Configuración de Azure
                t_cfg = speechsdk.translation.SpeechTranslationConfig(subscription=AZ_KEY, region=AZ_REG)
                t_cfg.speech_recognition_language = "es-ES" 
                l_map = {"English": "en", "Spanish": "es", "French": "fr", "Portuguese": "pt"}
                t_cfg.add_target_language(l_map[target_lang])
                
                t_cfg.set_property(speechsdk.PropertyId.Speech_SegmentationSilenceTimeoutMs, "5000")

                audio_config = speechsdk.audio.AudioConfig(filename=temp_wav)
                recognizer = speechsdk.translation.TranslationRecognizer(translation_config=t_cfg, audio_config=audio_config)

                # 3. Manejo de eventos
                def handle_final_result(evt):
                    if evt.result.reason == speechsdk.ResultReason.TranslatedSpeech:
                        txt = evt.result.translations.get(l_map[target_lang], "")
                        if txt: all_text.append(txt)

                def stop_cb(evt):
                    state["done"] = True

                recognizer.recognized.connect(handle_final_result)
                recognizer.session_stopped.connect(stop_cb)
                recognizer.canceled.connect(stop_cb)

                # 4. Iniciar proceso continuo
                recognizer.start_continuous_recognition_async()
                
                progress_bar = st.progress(0)
                while not state["done"]:
                    time.sleep(1)
                    # Progreso visual basado en fragmentos detectados
                    progress_bar.progress(min(len(all_text) * 2, 99)) 
                
                recognizer.stop_continuous_recognition_async()
                progress_bar.progress(100)

                # 5. Unir y Generar Audio Final
                full_script = " ".join(all_text).strip()
                if full_script:
                    s_cfg = speechsdk.SpeechConfig(subscription=AZ_KEY, region=AZ_REG)
                    voices = {
                        "English": {"Female": "en-US-JennyNeural", "Male": "en-US-GuyNeural"},
                        "Spanish": {"Female": "es-ES-ElviraNeural", "Male": "es-ES-AlvaroNeural"},
                        "French": {"Female": "fr-FR-DeniseNeural", "Male": "fr-FR-HenriNeural"},
                        "Portuguese": {"Female": "pt-BR-FranciscaNeural", "Male": "pt-BR-AntonioNeural"}
                    }
                    s_cfg.speech_synthesis_voice_name = voices[target_lang][voice_gender]
                    
                    final_mp3 = "result_long.mp3"
                    syn = speechsdk.SpeechSynthesizer(s_cfg, speechsdk.audio.AudioOutputConfig(filename=final_mp3))
                    syn.speak_text_async(full_script).get()

                    st.balloons()
                    st.success("✅ Doblaje completado con éxito.")
                    st.audio(final_mp3)
                    with open(final_mp3, "rb") as f:
                        st.download_button("📥 DOWNLOAD FINAL DUB", f, "didapod_result.mp3")
                else:
                    st.error("No se pudo extraer texto del audio largo.")

                if os.path.exists(temp_wav): os.remove(temp_wav)

        except Exception as e:
            st.error(f"Error en proceso largo: {e}")

# --- 5. DATA LOG VIEW (Para el Administrador) ---
st.write("---")
with st.expander("📊 View Cloud DB Status (Admin Only)"):
    st.info(f"Los datos se están sincronizando con la Google Sheet en la nube.")
    if os.path.exists("database_emails.txt"):
        with open("database_emails.txt", "r") as f:
            st.text(f.read())
    else:
        st.write("No hay registros locales aún.")

st.markdown("<br><hr><center><small>© 2026 DidactAI-US</small></center>", unsafe_allow_html=True)
