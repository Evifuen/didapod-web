import streamlit as st
import azure.cognitiveservices.speech as speechsdk
import os, requests, io, time
from datetime import datetime
from pydub import AudioSegment

# --- 1. CONFIG & STYLE ---
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwLIO5CsYs-7Z2xt335yT2ZQx9Hp3sxfVY7Bzvpdmu3LsD6uHTxvpukLHb2AAjMvDk2qA/exec"
st.set_page_config(page_title="DIDAPOD PRO", page_icon="🎙️", layout="centered")

st.markdown("""
<style>
.stApp { background-color: #0f172a !important; }
.stButton>button {
    background-color: #7c3aed !important;
    color: white !important;
    border-radius: 12px !important;
    padding: 18px !important;
    font-weight: 800 !important;
    width: 100% !important;
}
h1, h2, h3, label, p, span { color: white !important; }
</style>
""", unsafe_allow_html=True)

def get_clean_secret(name):
    val = st.secrets.get(name, "")
    return "".join(str(val).split()).replace('"', '').replace("'", "").strip()

AZ_KEY = get_clean_secret("AZURE_KEY")
AZ_REG = get_clean_secret("AZURE_SPEECH_REGION")

# --- 2. LOGIN & SHEETS ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    with st.form("login"):
        st.markdown("<h2 style='text-align: center;'>🎙️ DIDAPOD ACCESS</h2>", unsafe_allow_html=True)
        user_email = st.text_input("Corporate Email")
        u = st.text_input("Username", value="admin")
        p = st.text_input("Password", type="password", value="didactai2026")
        if st.form_submit_button("LOGIN"):
            if u == "admin" and p == "didactai2026" and "@" in user_email:
                try: requests.post(APPS_SCRIPT_URL, json={"email": user_email, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
                except: pass
                st.session_state["auth"] = True
                st.session_state["user_email"] = user_email
                st.rerun()
            else: st.error("Access Denied.")
    st.stop()

# --- 3. DUBBING ENGINE (PHYSICAL FILE VERSION) ---
st.title("🎙️ DIDAPOD PRO")
col1, col2 = st.columns(2)
with col1: target_lang = st.selectbox("Target Language:", ["English", "Spanish", "French", "Portuguese"])
with col2: voice_gender = st.selectbox("Voice Gender:", ["Female", "Male"])

uploaded_file = st.file_uploader("Upload Podcast Audio", type=["mp3", "wav", "m4a"])

if uploaded_file and AZ_KEY:
    st.audio(uploaded_file)
    if st.button("🚀 START AI DUBBING"):
        all_text = []
        # Objeto de control simple para evitar errores de sintaxis
        control = {"is_done": False}

        try:
            with st.spinner("🤖 Normalizing audio and translating..."):
                # PASO 1: CONVERSIÓN FÍSICA A WAV (Aquí está la clave)
                audio = AudioSegment.from_file(uploaded_file)
                audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
                temp_wav = "temp_audio_file.wav"
                audio.export(temp_wav, format="wav")

                # PASO 2: CONFIGURACIÓN AZURE
                t_cfg = speechsdk.translation.SpeechTranslationConfig(subscription=AZ_KEY, region=AZ_REG)
                l_map = {"English": "en", "Spanish": "es", "French": "fr", "Portuguese": "pt"}
                t_cfg.add_target_language(l_map[target_lang])
                
                # Le decimos a Azure que lea del archivo que acabamos de crear
                audio_config = speechsdk.audio.AudioConfig(filename=temp_wav)
                recognizer = speechsdk.translation.TranslationRecognizer(translation_config=t_cfg, audio_config=audio_config)

                # PASO 3: GESTIÓN DE EVENTOS (Nombres oficiales de la librería)
                def on_recognized(evt):
                    if evt.result.reason == speechsdk.ResultReason.TranslatedSpeech:
                        translation = evt.result.translations.get(l_map[target_lang], "")
                        if translation:
                            all_text.append(translation)

                def on_finished(evt):
                    control["is_done"] = True

                # Conexión limpia de eventos
                recognizer.recognized.connect(on_recognized)
                recognizer.session_stopped.connect(on_finished)
                recognizer.canceled.connect(on_finished)

                # Iniciar proceso
                recognizer.start_continuous_recognition_async()
                
                # Espera activa controlada
                while not control["is_done"]:
                    time.sleep(0.5)
                
                recognizer.stop_continuous_recognition_async()

                # PASO 4: GENERAR AUDIO FINAL
                full_script = " ".join(all_text)

                if full_script:
                    s_cfg = speechsdk.SpeechConfig(subscription=AZ_KEY, region=AZ_REG)
                    voices = {
                        "English": {"Female": "en-US-JennyNeural", "Male": "en-US-GuyNeural"},
                        "Spanish": {"Female": "es-ES-ElviraNeural", "Male": "es-ES-AlvaroNeural"},
                        "French": {"Female": "fr-FR-DeniseNeural", "Male": "fr-FR-HenriNeural"},
                        "Portuguese": {"Female": "pt-BR-FranciscaNeural", "Male": "pt-BR-AntonioNeural"}
                    }
                    s_cfg.speech_synthesis_voice_name = voices[target_lang][voice_gender]
                    
                    final_mp3 = "dubbed_podcast.mp3"
                    audio_out = speechsdk.audio.AudioOutputConfig(filename=final_mp3)
                    syn = speechsdk.SpeechSynthesizer(s_cfg, audio_out)
                    syn.speak_text_async(full_script).get()

                    st.balloons()
                    st.success("✅ Success! Dubbing complete.")
                    st.audio(final_mp3)
                    with open(final_mp3, "rb") as f:
                        st.download_button("📥 DOWNLOAD DUBBED PODCAST", f, "didapod_result.mp3")
                    
                    # Limpieza del servidor
                    if os.path.exists(temp_wav): os.remove(temp_wav)
                else:
                    st.error("Azure couldn't find speech segments. Please check audio volume.")

        except Exception as e:
            st.error(f"System Error: {e}")

st.markdown("<br><hr><center><small>© 2026 DidactAI-US</small></center>", unsafe_allow_html=True)
