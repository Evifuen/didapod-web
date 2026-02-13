import streamlit as st
import azure.cognitiveservices.speech as speechsdk
import os, requests
from datetime import datetime

# --- 1. CONFIG ---
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwLIO5CsYs-7Z2xt335yT2ZQx9Hp3sxfVY7Bzvpdmu3LsD6uHTxvpukLHb2AAjMvDk2qA/exec"
st.set_page_config(page_title="DIDAPOD PRO", page_icon="🎙️", layout="centered")

# --- 2. STYLE ---
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

# --- 3. CLEANER ---
def get_clean_secret(name):
    val = st.secrets.get(name, "")
    return "".join(str(val).split()).replace('"', '').replace("'", "").strip()

AZ_KEY = get_clean_secret("AZURE_KEY")
AZ_REG = get_clean_secret("AZURE_SPEECH_REGION")

# --- 4. LOGIN ---
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

# --- 5. MAIN ---
st.title("🎙️ DIDAPOD PRO")
col1, col2 = st.columns(2)
with col1: target_lang = st.selectbox("Target Language:", ["English", "Spanish", "French", "Portuguese"])
with col2: voice_gender = st.selectbox("Voice Gender:", ["Female", "Male"])

uploaded_file = st.file_uploader("Upload Audio", type=["mp3", "wav"])

if uploaded_file and AZ_KEY:
    st.audio(uploaded_file)
    if st.button("🚀 START AI DUBBING PROCESS"):
        try:
            with st.spinner("🤖 AI is analyzing and dubbing..."):
                audio_data = uploaded_file.read()

                # CONFIGURACIÓN TRADUCCIÓN
                t_cfg = speechsdk.translation.SpeechTranslationConfig(subscription=AZ_KEY, region=AZ_REG)
                
                # Definimos el formato del audio (16kHz, 16-bit, Mono es el estándar de Azure)
                # Esto ayuda a evitar el NoMatch
                stream_format = speechsdk.audio.AudioStreamFormat(samples_per_second=16000, bits_per_sample=16, channels=1)
                push_stream = speechsdk.audio.PushAudioInputStream(stream_format)
                audio_config = speechsdk.audio.AudioConfig(stream=push_stream)
                
                auto_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(languages=["es-ES", "en-US", "fr-FR", "pt-BR"])
                
                l_map = {"English": "en", "Spanish": "es", "French": "fr", "Portuguese": "pt"}
                t_cfg.add_target_language(l_map[target_lang])
                
                recognizer = speechsdk.translation.TranslationRecognizer(
                    translation_config=t_cfg, 
                    audio_config=audio_config, 
                    auto_detect_source_language_config=auto_config
                )

                # Enviamos el audio
                push_stream.write(audio_data)
                push_stream.close()
                
                result = recognizer.recognize_once_async().get()

                if result.reason == speechsdk.ResultReason.TranslatedSpeech:
                    # SÍNTESIS
                    s_cfg = speechsdk.SpeechConfig(subscription=AZ_KEY, region=AZ_REG)
                    voices = {
                        "English": {"Female": "en-US-JennyNeural", "Male": "en-US-GuyNeural"},
                        "Spanish": {"Female": "es-ES-ElviraNeural", "Male": "es-ES-AlvaroNeural"},
                        "French": {"Female": "fr-FR-DeniseNeural", "Male": "fr-FR-HenriNeural"},
                        "Portuguese": {"Female": "pt-BR-FranciscaNeural", "Male": "pt-BR-AntonioNeural"}
                    }
                    s_cfg.speech_synthesis_voice_name = voices[target_lang][voice_gender]
                    
                    output_file = "dubbed_result.mp3"
                    audio_out = speechsdk.audio.AudioOutputConfig(filename=output_file)
                    syn = speechsdk.SpeechSynthesizer(s_cfg, audio_out)
                    
                    translated_text = result.translations[l_map[target_lang]]
                    syn.speak_text_async(translated_text).get()

                    st.balloons()
                    st.success("Dubbing Finished!")
                    st.audio(output_file)
                    with open(output_file, "rb") as f: 
                        st.download_button("📥 DOWNLOAD AUDIO", f, "didapod_result.mp3")
                
                elif result.reason == speechsdk.ResultReason.NoMatch:
                    st.warning("No speech detected. Try a clearer audio or a WAV file.")
                else:
                    st.error(f"Azure Connection Error: {result.reason}")
        except Exception as e:
            st.error(f"System Failure: {e}")

st.markdown("<br><hr><center><small>© 2026 DidactAI-US</small></center>", unsafe_allow_html=True)
