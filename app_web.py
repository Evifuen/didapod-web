import pandas as pd
from streamlit_gsheets import GSheetsConnection
import streamlit as st
import azure.cognitiveservices.speech as speechsdk
from deep_translator import GoogleTranslator
from pydub import AudioSegment
import speech_recognition as sr
import os
import base64

# --- 0. AUTOMATIC CREDENTIALS ---
AZURE_KEY = st.secrets["AZURE_SPEECH_KEY"]
AZURE_REGION = st.secrets["AZURE_SPEECH_REGION"]

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="DIDAPOD PRO", page_icon="🎙️", layout="centered")

def get_base64_logo(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

logo_data = get_base64_logo("logo2.png.png")

# --- 2. PROFESSIONAL DESIGN ---
st.markdown("""
    <style>
    .stApp { background-color: #0f172a !important; }
    
    /* LOGIN BUTTON IN BLACK */
    .stButton>button { 
        background-color: #000000 !important; 
        color: white !important; 
        border-radius: 12px !important; 
        font-weight: 800 !important; 
        width: 100% !important; 
        border: 2px solid #334155 !important;
    }
    
    .stButton>button:hover {
        background-color: #1e293b !important;
        border-color: #7c3aed !important;
    }

    h1, h2, h3, label, p, span { color: white !important; }
    </style>
    """, unsafe_allow_html=True)


# --- 3. LOGIN & PERMANENT REGISTRATION ---
if "auth" not in st.session_state: 
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    with st.form("login"):
        st.markdown("### 📝 DIDAPOD PRO ACCESS")
        email_cliente = st.text_input("📧 Your Email for registration")
        
        # Automatic credential fill
        u = st.text_input("Username", value="admin")
        p = st.text_input("Password", type="password", value="didactai2026")
        
        if st.form_submit_button("Enter DIDAPOD"):
            if email_cliente and u == "admin" and p == "didactai2026":
                try:
                    # Permanent connection to Google Sheets
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    
                    # Try to read data; if it fails (empty sheet), create structure
                    try:
                        df_existente = conn.read()
                    except:
                        df_existente = pd.DataFrame(columns=["Email", "Date"])
                    
                    # Add new client
                    nuevo_registro = pd.DataFrame([{"Email": email_cliente, "Date": str(pd.Timestamp.now())}])
                    df_final = pd.concat([df_existente, nuevo_registro], ignore_index=True)
                    
                    # Save to cloud (Google Sheets)
                    conn.update(data=df_final)
                    
                    st.session_state["auth"] = True
                    st.session_state["user_email"] = email_cliente # Store email for greeting
                    st.rerun()
                except Exception as e:
                    st.error(f"Database connection error: {e}")
            else:
                st.error("Please enter a valid email and the correct credentials.")
    st.stop() # Blocks the rest of the app until login

# --- 4. HEADER ---
st.markdown("<h1 style='text-align:center;'>🎙️ DIDAPOD PRO</h1>", unsafe_allow_html=True)
st.write("---")

# --- 5. PROCESSING ---
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
                            # Transcription & Translation
                            text = r.recognize_google(r.record(src), language="es-ES")
                            trans = GoogleTranslator(source='auto', target=codes[target_lang]).translate(text)
                            
                            # AZURE ENGINE
                            speech_config = speechsdk.SpeechConfig(subscription=AZURE_KEY, region=AZURE_REGION)
                            speech_config.speech_synthesis_voice_name = voice_m[target_lang]
                            
                            nombre_v = f"v{i}.mp3"
                            audio_out = speechsdk.audio.AudioOutputConfig(filename=nombre_v)
                            syn = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_out)
                            
                            syn.speak_text_async(trans).get() 
                            
                            final_audio += AudioSegment.from_file(nombre_v)
                            os.remove(nombre_v)
                        except Exception as e:
                            st.write(f"Fragment {i} skipped: {e}")
                            continue
                
                final_audio.export("result.mp3", format="mp3")
                st.balloons()
                st.audio("result.mp3")
                with open("result.mp3", "rb") as f:
                    st.download_button("📥 DOWNLOAD FINAL PODCAST", f, "didapod_pro.mp3")

        except Exception as e: st.error(f"Critical error: {e}")

st.markdown("<br><hr><center><small style='color:#94a3b8;'>© 2026 DidactAI-US</small></center>", unsafe_allow_html=True)

# --- 6. SECRET ADMIN PANEL ---
st.write("---")
with st.expander("🛠️ Admin Panel (Internal use only)"):
    admin_key = st.text_input("Enter Master Key to view clients:", type="password")
    
    if admin_key == "didactai2026": 
        try:
            conn = st.connection("gsheets", type=GSheetsConnection)
            df_clientes = conn.read()
            st.write("### 👥 Registered Client List:")
            st.dataframe(df_clientes)
            
            csv = df_clientes.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Email Database (CSV)",
                data=csv,
                file_name="client_database.csv",
                mime="text/csv"
            )
        except:
            st.warning("No clients registered yet or database connection failed.")
    elif admin_key:
        st.error("Incorrect Master Key")
