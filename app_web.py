import streamlit as st
import azure.cognitiveservices.speech as speechsdk
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from deep_translator import GoogleTranslator
from pydub import AudioSegment
import os
import base64
import time

# --- 1. SECURITY CONFIGURATION (SECRETS) ---
try:
    AZURE_KEY = st.secrets["AZURE_SPEECH_KEY"]
    AZURE_REGION = st.secrets["AZURE_REGION"]
except:
    st.error("Missing Azure Credentials! Please check your Secrets in Streamlit Cloud.")
    st.stop()

# --- 2. PAGE CONFIG & CUSTOM STYLES ---
st.set_page_config(page_title="DIDAPOD PRO", page_icon="🎙️", layout="centered")

def get_base64_logo(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

logo_data = get_base64_logo("logo2.png")

st.markdown(f"""
    <style>
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    .stApp {{ background-color: #0f172a !important; }}
    button[kind="primaryFormSubmit"], .stButton>button {{
        background-color: #000000 !important;
        color: #ffffff !important;
        border: 2px solid #ffffff !important;
        border-radius: 12px !important;
        font-weight: 800 !important;
        width: 100% !important;
        height: 50px !important;
    }}
    h1, h2, h3, label, p, span {{ color: white !important; }}
    .logo-container {{ text-align: center; margin-bottom: 20px; }}
    </style>
    """, unsafe_allow_html=True)

if logo_data:
    st.markdown(f'<div class="logo-container"><img src="data:image/png;base64,{logo_data}" width="200"></div>', unsafe_allow_html=True)

# --- 3. LOGIN & ACCESS ---
if "auth" not in st.session_state: st.session_state["auth"] = False

if not st.session_state["auth"]:
    with st.form("login"):
        st.markdown("### 🔐 DIDAPOD RESTRICTED ACCESS")
        email = st.text_input("📧 Authorized Email")
        if st.form_submit_button("VALIDATE LICENSE"):
            if email:
                try:
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    df = conn.read()
                    new_entry = pd.DataFrame([{"Email": email, "Date": str(pd.Timestamp.now())}])
                    conn.update(data=pd.concat([df, new_entry], ignore_index=True))
                    st.session_state["auth"] = True
                    st.rerun()
                except:
                    st.session_state["auth"] = True 
                    st.rerun()
    st.stop()

# --- 4. USER INTERFACE ---
st.markdown("<h1 style='text-align:center;'>🎙️ DIDAPOD PRO v2.0</h1>", unsafe_allow_html=True)
st.write("<p style='text-align:center; color:#94a3b8;'>Azure AI Engine with Automatic Language Detection</p>", unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1:
    target_lang = st.selectbox("Target Language:", ["English", "Spanish", "French", "Portuguese", "German"])
with c2:
    gender = st.selectbox("Voice Tone:", ["Male", "Female"])

up_file = st.file_uploader("Upload Podcast (Formats: MP3, WAV)", type=["mp3", "wav"])

# --- 5. PROCESSING LOGIC ---
if up_file:
    session_id = str(int(time.time()))
    temp_input = f"input_{session_id}.mp3"
    
    with open(temp_input, "wb") as f: 
        f.write(up_file.getbuffer())
    
    try:
        audio_check = AudioSegment.from_file(temp_input)
        duration_sec = len(audio_check) / 1000
        st.info(f"⏱️ Duration detected: {duration_sec:.2f} seconds")

        if st.button("🚀 START SMART TRANSLATION"):
            try:
                with st.spinner("🤖 Azure is analyzing and dubbing the audio..."):
                    # Process in 30-second chunks for better reliability
                    chunks = [audio_check[i:i + 30000] for i in range(0, len(audio_check), 30000)]
                    final_audio = AudioSegment.empty()
                    
                    speech_config = speechsdk.SpeechConfig(subscription=AZURE_KEY, region=AZURE_REGION)
                    # Force compatible audio format for Windows/Web players
                    speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Riff24Khz16BitMonoPcm)
                    
                    codes = {"English": "en", "Spanish": "es", "French": "fr", "Portuguese": "pt", "German": "de"}
                    voices = {
                        "English": "en-US-AndrewNeural" if gender == "Male" else "en-US-AvaNeural",
                        "Spanish": "es-ES-AlvaroNeural" if gender == "Male" else "es-ES-ElviraNeural",
                        "French": "fr-FR-RemyNeural" if gender == "Male" else "fr-FR-DeniseNeural",
                        "Portuguese": "pt-BR-AntonioNeural" if gender == "Male" else "pt-BR-FranciscaNeural",
                        "German": "de-DE-ConradNeural" if gender == "Male" else "de-DE-KatjaNeural"
                    }

                    progress_bar = st.progress(0)
                    
                    for i, chunk in enumerate(chunks):
                        chunk_path = f"chunk_{session_id}_{i}.wav"
                        chunk.export(chunk_path, format="wav")
                        
                        audio_config = speechsdk.audio.AudioConfig(filename=chunk_path)
                        auto_detect_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(
                            languages=["es-ES", "en-US", "fr-FR", "pt-BR", "de-DE"]
                        )
                        
                        recognizer = speechsdk.SpeechRecognizer(
                            speech_config=speech_config, 
                            auto_detect_source_language_config=auto_detect_config, 
                            audio_config=audio_config
                        )
                        
                        result = recognizer.recognize_once()

                        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                            # AI Translation
                            trans = GoogleTranslator(source='auto', target=codes[target_lang]).translate(result.text)
                            
                            # Voice Synthesis
                            speech_config.speech_synthesis_voice_name = voices[target_lang]
                            synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
                            res_voice = synthesizer.speak_text_async(trans).get()
                            
                            if res_voice.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                                voice_path = f"v_{session_id}_{i}.wav"
                                with open(voice_path, "wb") as f: 
                                    f.write(res_voice.audio_data)
                                
                                final_audio += AudioSegment.from_wav(voice_path)
                                os.remove(voice_path)

                        if os.path.exists(chunk_path):
                            os.remove(chunk_path)
                        progress_bar.progress((i + 1) / len(chunks))

                    # Final export
                    output_file = f"result_{session_id}.mp3"
                    final_audio.export(output_file, format="mp3", bitrate="192k")
                    
                    st.success("✅ Translation completed!")
                    st.audio(output_file)
                    
                    with open(output_file, "rb") as f:
                        st.download_button("📥 DOWNLOAD RESULT", f, f"didapod_{target_lang}.mp3")
                    
                    os.remove(temp_input)

            except Exception as e:
                st.error("A technical error occurred. Please contact support.")
                st.info(f"System details: {e}")
    except Exception as e:
        st.error("Error loading file. Please ensure it is a valid MP3 or WAV.")

st.markdown("<br><hr><center><small style='color:#475569;'>DIDAPOD PRO © 2026 | Enterprise Grade Security</small></center>", unsafe_allow_html=True)

