import streamlit as st
import azure.cognitiveservices.speech as speechsdk
import os, requests, io, time, base64
from datetime import datetime
from pydub import AudioSegment

# --- 1. CONFIGURATION & STYLE (Tu estilo original) ---
st.set_page_config(page_title="DIDAPOD - DidactAI", page_icon="🎙️", layout="centered")

def get_base64_logo(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            data = f.read()
            return base64.b64encode(data).decode()
    return None

logo_data = get_base64_logo("logo2.png")

st.markdown("""
    <style>
    .stApp { background-color: #0f172a !important; }
    .stExpander { 
        background-color: #7c3aed !important; 
        border: 2px solid white !important; 
        border-radius: 12px !important;
    }
    .stExpander summary, .stExpander summary * { 
        color: #ffffff !important; 
        font-weight: 800 !important; 
        font-size: 19px !important;
        text-transform: uppercase !important;
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
    </style>
    """, unsafe_allow_html=True)

def get_clean_secret(name):
    val = st.secrets.get(name, "")
    return "".join(str(val).split()).replace('"', '').replace("'", "").strip()

AZ_KEY = get_clean_secret("AZURE_KEY")
AZ_REG = get_clean_secret("AZURE_SPEECH_REGION")

# --- 2. LOGIN (Tu lógica original) ---
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
                with open("database_emails.txt", "a") as f:
                    f.write(f"{timestamp} | {user_email}\n")
                st.session_state["auth"] = True
                st.rerun()
            else: st.error("Access Denied.")
    st.stop()

# --- 3. HEADER ---
col_l, col_r = st.columns([1, 4])
with col_l:
    if logo_data:
        st.markdown(f'<img src="data:image/png;base64,{logo_data}" width="110" style="border-radius:10px;">', unsafe_allow_html=True)
with col_r:
    st.markdown("<h1 style='margin:0;'>DIDAPOD PRO</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94a3b8 !important; margin:0;'>Enterprise Dubbing by DidactAI-US</p>", unsafe_allow_html=True)

# --- 4. NEW AZURE ENGINE (Reemplaza a Google/Edge) ---
col1, col2 = st.columns(2)
with col1: target_lang = st.selectbox("Select Target Language:", ["English", "Spanish", "French", "Portuguese"])
with col2: voice_gender = st.selectbox("Select Voice Gender:", ["Female", "Male"])

up_file = st.file_uploader("Upload podcast", type=["mp3", "wav"])

if up_file and AZ_KEY:
    st.audio(up_file)
    if st.button("🚀 START AI DUBBING"):
        all_text = []
        state = {"done": False}
        
        try:
            with st.spinner("🤖 Azure is listening and translating your podcast..."):
                # Convert to WAV for Azure
                audio = AudioSegment.from_file(up_file)
                audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
                temp_wav = "process_file.wav"
                audio.export(temp_wav, format="wav")

                # Translation Config
                t_cfg = speechsdk.translation.SpeechTranslationConfig(subscription=AZ_KEY, region=AZ_REG)
                l_map = {"English": "en", "Spanish": "es", "French": "fr", "Portuguese": "pt"}
                t_cfg.add_target_language(l_map[target_lang])
                
                audio_config = speechsdk.audio.AudioConfig(filename=temp_wav)
                recognizer = speechsdk.translation.TranslationRecognizer(translation_config=t_cfg, audio_config=audio_config)

                def on_recognized(evt):
                    if evt.result.reason == speechsdk.ResultReason.TranslatedSpeech:
                        txt = evt.result.translations.get(l_map[target_lang], "")
                        if txt: all_text.append(txt)

                def on_stop(evt): state["done"] = True

                recognizer.recognized.connect(on_recognized)
                recognizer.session_stopped.connect(on_stop)
                recognizer.canceled.connect(on_stop)

                recognizer.start_continuous_recognition_async()
                while not state["done"]: time.sleep(0.5)
                recognizer.stop_continuous_recognition_async()

                # Build final dubbing
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
                    
                    audio_out = speechsdk.audio.AudioOutputConfig(filename="result.mp3")
                    syn = speechsdk.SpeechSynthesizer(s_cfg, audio_out)
                    syn.speak_text_async(full_script).get()

                    st.balloons()
                    st.success("✅ PODCAST READY")
                    st.audio("result.mp3")
                    with open("result.mp3", "rb") as f:
                        st.download_button("📥 DOWNLOAD FINAL FILE", f, "didapod_result.mp3")
                else:
                    st.error("Azure couldn't find speech. Please check your audio quality.")
                
                if os.path.exists(temp_wav): os.remove(temp_wav)

        except Exception as e: st.error(f"Error: {e}")

st.markdown("<br><hr><center><small style='color:#94a3b8;'>© 2026 DidactAI-US</small></center>", unsafe_allow_html=True)
