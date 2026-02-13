import streamlit as st
import azure.cognitiveservices.speech as speechsdk
import os, requests, io, time, base64
from datetime import datetime
from pydub import AudioSegment, effects

# --- 1. CONFIG & STYLE (Your Branding) ---
st.set_page_config(page_title="DIDAPOD - DidactAI", page_icon="🎙️", layout="centered")

def get_base64_logo(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

logo_data = get_base64_logo("logo2.png")

st.markdown("""
    <style>
    .stApp { background-color: #0f172a !important; }
    .stButton>button { 
        background-color: #7c3aed !important; color: white !important; 
        border-radius: 12px !important; padding: 18px !important; 
        font-weight: 800 !important; width: 100% !important; border: 1px solid white !important;
    }
    h1, h2, h3, label, p, span { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

def get_clean_secret(name):
    val = st.secrets.get(name, "")
    return "".join(str(val).split()).replace('"', '').replace("'", "").strip()

AZ_KEY = get_clean_secret("AZURE_KEY")
AZ_REG = get_clean_secret("AZURE_SPEECH_REGION")

# --- 2. LOGIN (Your Logic) ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    with st.form("login"):
        user_email = st.text_input("Email Address")
        if st.form_submit_button("Login"):
            if "@" in user_email:
                st.session_state["auth"] = True
                st.rerun()
    st.stop()

# --- 3. DUBBING ENGINE WITH AUDIO BOOSTER ---
st.title("🎙️ DIDAPOD PRO")
col1, col2 = st.columns(2)
with col1: target_lang = st.selectbox("Target Language:", ["English", "Spanish", "French", "Portuguese"])
with col2: voice_gender = st.selectbox("Voice Gender:", ["Female", "Male"])

up_file = st.file_uploader("Upload podcast", type=["mp3", "wav"])

if up_file and AZ_KEY:
    st.audio(up_file)
    if st.button("🚀 START AI DUBBING"):
        all_text = []
        state = {"done": False}
        
        try:
            with st.spinner("🔊 Boosting audio & Analyzing..."):
                # STEP 1: LOAD & NORMALIZE (The fix for "No Speech Detected")
                audio = AudioSegment.from_file(up_file)
                # This makes the voices as loud as possible without distortion
                audio = effects.normalize(audio) 
                audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
                
                temp_wav = "boosted_audio.wav"
                audio.export(temp_wav, format="wav")

                # STEP 2: AZURE SETUP
                t_cfg = speechsdk.translation.SpeechTranslationConfig(subscription=AZ_KEY, region=AZ_REG)
                l_map = {"English": "en", "Spanish": "es", "French": "fr", "Portuguese": "pt"}
                t_cfg.add_target_language(l_map[target_lang])
                
                # Critical: Set profanity to raw and increase timeout
                t_cfg.set_profanity(speechsdk.ProfanityOption.Raw)
                
                audio_config = speechsdk.audio.AudioConfig(filename=temp_wav)
                recognizer = speechsdk.translation.TranslationRecognizer(translation_config=t_cfg, audio_config=audio_config)

                # STEP 3: RECOGNITION LOOP
                def on_recognized(evt):
                    if evt.result.reason == speechsdk.ResultReason.TranslatedSpeech:
                        txt = evt.result.translations.get(l_map[target_lang], "")
                        if txt: all_text.append(txt)

                recognizer.recognized.connect(on_recognized)
                recognizer.session_stopped.connect(lambda evt: state.update({"done": True}))
                recognizer.canceled.connect(lambda evt: state.update({"done": True}))

                recognizer.start_continuous_recognition_async()
                while not state["done"]:
                    time.sleep(0.5)
                recognizer.stop_continuous_recognition_async()

                # STEP 4: GENERATE OUTPUT
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
                    
                    syn = speechsdk.SpeechSynthesizer(s_cfg, speechsdk.audio.AudioOutputConfig(filename="result.mp3"))
                    syn.speak_text_async(full_script).get()

                    st.success("✅ DONE!")
                    st.audio("result.mp3")
                else:
                    st.error("Azure still reports no speech. Check your API Key/Region in Secrets.")
                
                if os.path.exists(temp_wav): os.remove(temp_wav)

        except Exception as e:
            st.error(f"Error: {e}")
