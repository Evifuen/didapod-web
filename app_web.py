import streamlit as st
import edge_tts
import asyncio
import os
import base64
import speech_recognition as sr
from deep_translator import GoogleTranslator
from pydub import AudioSegment
from datetime import datetime

# --- 1. CONFIGURATION & STYLE ---
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
    h1, h2, h3, label, p, span { color: blue !important; }
    .stSpinner > div { border-top-color: #7c3aed !important; }
    .log-box { 
        background-color: rgba(255,255,255,0.05); 
        padding: 10px; 
        border-radius: 8px; 
        margin-bottom: 5px;
        border-left: 4px solid #7c3aed;
    }
    </style>
    """, unsafe_allow_html=True)

# --- EMAIL LIMIT VALIDATION ---
def check_email_limit(email):
    if not os.path.exists("database_emails.txt"):
        return 0
    with open("database_emails.txt", "r") as f:
        lines = f.readlines()
        count = sum(1 for line in lines if email in line)
        return count

# --- 2. LOGIN (WITH LIMIT & AUTO-FILL) ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    with st.form("login"):
        st.markdown("### 🔐 ACCESS PANEL")
        user_email = st.text_input("Email Address")
        u = st.text_input("User", value="admin")
        p = st.text_input("Pass", type="password", value="didactai2026")
        
        if st.form_submit_button("Login"):
            if u == "admin" and p == "didactai2026":
                if user_email and "@" in user_email:
                    attempts = check_email_limit(user_email)
                    if attempts >= 2:
                        st.error(f"🚫 Access denied. The email {user_email} has reached the maximum limit of 2 records.")
                    else:
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        with open("database_emails.txt", "a") as f:
                            f.write(f"{timestamp} | {user_email}\n")
                        st.session_state["auth"] = True
                        st.rerun()
                else:
                    st.error("Please enter a valid email address.")
    st.stop()

# --- 3. HEADER ---
col_l, col_r = st.columns([1, 4])
with col_l:
    if logo_data:
        st.markdown(f'<img src="data:image/png;base64,{logo_data}" width="110" style="border-radius:10px;">', unsafe_allow_html=True)
    else:
        st.markdown("<h1 style='margin:0;'>🎙️</h1>", unsafe_allow_html=True)
with col_r:
    st.markdown("<h1 style='margin:0;'>DIDAPOD PRO</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94a3b8 !important; margin:0;'>Enterprise Dubbing with Auto-Language Detection</p>", unsafe_allow_html=True)

st.write("---")

# --- 4. PROCESSING ---
target_lang = st.selectbox("Select Target Language:", ["English", "Spanish", "French", "Portuguese"])
up_file = st.file_uploader("Upload podcast", type=["mp3", "wav"])

if up_file:
    st.audio(up_file)
    if st.button("🚀 START AI DUBBING"):
        try:
            log_container = st.container()
            with st.spinner("🤖 AI Dubbing in progress... detecting and processing chunks"):
                with open("temp.mp3", "wb") as f: f.write(up_file.getbuffer())
                audio = AudioSegment.from_file("temp.mp3")
                chunks = [audio[i:i + 40000] for i in range(0, len(audio), 40000)]
                
                final_audio = AudioSegment.empty()
                r = sr.Recognizer()
                
                codes = {"English": "en", "Spanish": "es", "French": "fr", "Portuguese": "pt"}
                voice_m = {
                    "English": "en-US-EmmaMultilingualNeural", 
                    "Spanish": "es-ES-ElviraNeural", 
                    "French": "fr-FR-DeniseNeural",
                    "Portuguese": "pt-BR-FranciscaNeural"
                }

                for i, chunk in enumerate(chunks):
                    chunk_path = f"c_{i}.wav"
                    chunk.export(chunk_path, format="wav")
                    with sr.AudioFile(chunk_path) as src:
                        try:
                            audio_data = r.record(src)
                            raw_response = r.recognize_google(audio_data, show_all=True)
                            
                            if raw_response and 'alternative' in raw_response:
                                text = raw_response['alternative'][0]['transcript']
                                
                                translator = GoogleTranslator(source='auto', target=codes[target_lang])
                                trans = translator.translate(text)
                                detected_lang = translator.source
                                
                                # Real-time processing log in English
                                log_container.markdown(f"""
                                <div class="log-box">
                                <b>Part {i+1}:</b> Detected Language: <code>{detected_lang.upper()}</code><br>
                                <i>Text detected: "{text[:50]}..."</i>
                                </div>
                                """, unsafe_allow_html=True)

                                voice_path = f"v_{i}.mp3"
                                asyncio.run(edge_tts.Communicate(trans, voice_m[target_lang]).save(voice_path))
                                final_audio += AudioSegment.from_file(voice_path)
                                
                                os.remove(voice_path)
                            
                        except Exception:
                            continue
                        finally:
                            if os.path.exists(chunk_path): os.remove(chunk_path)
                
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

        except Exception as e: 
            st.error(f"General Error: {e}")

# --- 5. DATA LOG VIEW (Admin Only) ---
st.write("---")
with st.expander("📊 View Registered Emails (Admin Only)"):
    if os.path.exists("database_emails.txt"):
        with open("database_emails.txt", "r") as f:
            st.text(f.read())
    else:
        st.info("No emails registered yet.")

st.markdown("<br><hr><center><small style='color:#94a3b8;'>© 2026 DidactAI-US</small></center>", unsafe_allow_html=True)
