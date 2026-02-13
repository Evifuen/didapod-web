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
}
h1, h2, h3, label, p, span { color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. MOTOR DE LLAVES ---
def get_clean_secret(name):
    val = st.secrets.get(name, "")
    return "".join(str(val).split()).replace('"', '').replace("'", "").strip()

AZ_KEY = get_clean_secret("AZURE_KEY")
AZ_REG = get_clean_secret("AZURE_SPEECH_REGION")

# --- 3. LOGIN & SHEETS (INTACTO) ---
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

# --- 4. PROCESO DE DOBLAJE ---
st.title("🎙️ DIDAPOD PRO")
col1, col2 = st.columns(2)
with col1: target_lang = st.selectbox("Target Language:", ["English", "Spanish", "French", "Portuguese"])
with col2: voice_gender = st.selectbox("Voice Gender:", ["Female", "Male"])

uploaded_file = st.file_uploader("Upload Podcast Audio", type=["mp3", "wav", "m4a"])

if uploaded_file and AZ_KEY:
    st.audio(uploaded_file)
    if st.button("🚀 START FULL DUBBING PROCESS"):
        # DEFINIMOS done AQUÍ AFUERA PARA QUE LAS FUNCIONES LO VEAN
        done = False
        all_text = []
        
        try:
            with st.spinner("🤖 Processing entire audio... this may take a moment."):
                # Conversión WAV
                audio = AudioSegment.from_file(uploaded_file)
                audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
                wav_io = io.BytesIO()
                audio.export(wav_io, format="wav")
                wav_data = wav_io.getvalue()

                # Config Azure
                t_cfg = speechsdk.translation.SpeechTranslationConfig(subscription=AZ_KEY, region=AZ_REG)
                l_map = {"English": "en", "Spanish": "es", "French": "fr", "Portuguese": "pt"}
                t_cfg.add_target_language(l_map[target_lang])
                
                push_stream = speechsdk.audio.PushAudioInputStream()
                audio_config = speechsdk.audio.AudioConfig(stream=push_stream)
                auto_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(languages=["es-ES", "en-US", "fr-FR", "pt-BR"])
                
                recognizer = speechsdk.translation.TranslationRecognizer(
                    translation_config=t_cfg, 
                    audio_config=audio_config, 
                    auto_detect_source_language_config=auto_config
                )

                # FUNCIONES DE CONTROL
                def stop_handle(evt):
                    nonlocal done
                    done = True

                def translated_handle(evt):
                    if evt.result.reason == speechsdk.ResultReason.TranslatedSpeech:
                        txt = evt.result.translations[l_map[target_lang]]
                        if txt: all_text.append(txt)

                recognizer.translated.connect(translated_handle)
                recognizer.session_stopped.connect(stop_handle)
                recognizer.canceled.connect(stop_handle)

                # Ejecutar Reconocimiento Continuo
                recognizer.start_continuous_recognition_async()
                push_stream.write(wav_data)
                push_stream.close()

                # Esperar hasta que termine
                while not done:
                    time.sleep(0.5)
                
                recognizer.stop_continuous_recognition_async()

                full_script = " ".join(all_text)

                if full_script:
                    # SÍNTESIS DE VOZ
                    s_cfg = speechsdk.SpeechConfig(subscription=AZ_KEY, region=AZ_REG)
                    voices = {
                        "English": {"Female": "en-US-JennyNeural", "Male": "en-US-GuyNeural"},
                        "Spanish": {"Female": "es-ES-ElviraNeural", "Male": "es-ES-AlvaroNeural"},
                        "French": {"Female": "fr-FR-DeniseNeural", "Male": "fr-FR-HenriNeural"},
                        "Portuguese": {"Female": "pt-BR-FranciscaNeural", "Male": "pt-BR-AntonioNeural"}
                    }
                    s_cfg.speech_synthesis_voice_name = voices[target_lang][voice_gender]
                    
                    out_f = "final_dub.mp3"
                    audio_out = speechsdk.audio.AudioOutputConfig(filename=out_f)
                    syn = speechsdk.SpeechSynthesizer(s_cfg, audio_out)
                    syn.speak_text_async(full_script).get()

                    st.balloons()
                    st.success("✅ Full Dubbing Success!")
                    st.audio(out_f)
                    with open(out_f, "rb") as f:
                        st.download_button("📥 DOWNLOAD AUDIO", f, "didapod_result.mp3")
                else:
                    st.error("No speech detected.")
        except Exception as e:
            st.error(f"Error: {e}")

st.markdown("<br><hr><center><small>© 2026 DidactAI-US</small></center>", unsafe_allow_html=True)
