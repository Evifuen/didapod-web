import streamlit as st
import azure.cognitiveservices.speech as speechsdk
import os, time, base64, requests
from datetime import datetime
from pydub import AudioSegment
import smtplib 
from email.mime.text import MIMEText 

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
    /* Ajuste para que el footer no tape contenido */
    .block-container { padding-bottom: 5rem; }
    </style>
    """, unsafe_allow_html=True)

def get_clean_secret(name):
    val = st.secrets.get(name, "")
    return "".join(str(val).split()).replace('"', '').replace("'", "").strip()


AZ_KEY = os.getenv("AZURE_SPEECH_KEY", "")
AZ_REG = os.getenv("AZURE_REGION", "")

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
                try:
                    requests.post(APPS_SCRIPT_URL, json={"email": user_email, "timestamp": timestamp}, timeout=1)
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
    st.markdown("<p style='color:#94a3b8 !important; margin:0;'>Global Language Support</p>", unsafe_allow_html=True)

# --- 4. MOTOR CON DETECCIÓN AUTOMÁTICA REFORZADA ---
target_lang = st.selectbox("Target Language:", ["English", "Spanish", "French", "Portuguese"])
voice_gender = st.selectbox("Voice Gender Selection:", ["Female", "Male"])
up_file = st.file_uploader("Upload your Podcast", type=["mp3", "wav"])

if up_file and AZ_KEY:
    st.audio(up_file)
    if st.button("🚀 START AI DUBBING"):
        all_text = []
        state = {"done": False}
        
        try:
            with st.spinner(f"⌛ Analizando y traduciendo..."):
                audio = AudioSegment.from_file(up_file)
                temp_wav = "temp_long.wav"
                audio.set_frame_rate(16000).set_channels(1).export(temp_wav, format="wav", bitrate="256k")

                # CONFIGURACIÓN DE TRADUCCIÓN
                t_cfg = speechsdk.translation.SpeechTranslationConfig(subscription=AZ_KEY, region=AZ_REG)
                
                # Mapeo de salida
                l_map = {"English": "en", "Spanish": "es", "French": "fr", "Portuguese": "pt"}
                target_code = l_map[target_lang]
                t_cfg.add_target_language(target_code)
                
                # DETECCIÓN AUTOMÁTICA MEJORADA
                auto_detect_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(languages=["en-US", "es-ES", "fr-FR", "pt-BR"])
                
                t_cfg.set_property(speechsdk.PropertyId.Speech_SegmentationSilenceTimeoutMs, "4000")

                audio_config = speechsdk.audio.AudioConfig(filename=temp_wav)
                
                # Recognizer con detección de lenguaje de origen
                recognizer = speechsdk.translation.TranslationRecognizer(
                    translation_config=t_cfg, 
                    audio_config=audio_config,
                    auto_detect_source_language_config=auto_detect_config
                )

                def handle_final_result(evt):
                    if evt.result.reason == speechsdk.ResultReason.TranslatedSpeech:
                        txt = evt.result.translations.get(target_code, "")
                        if txt: 
                            all_text.append(txt)

                def stop_cb(evt): state["done"] = True

                recognizer.recognized.connect(handle_final_result)
                recognizer.session_stopped.connect(stop_cb)
                recognizer.canceled.connect(stop_cb)

                recognizer.start_continuous_recognition_async()
                
                progress_bar = st.progress(0)
                while not state["done"]:
                    time.sleep(0.1) 
                    current_progress = min(len(all_text) * 2, 99)
                    progress_bar.progress(current_progress)
                
                recognizer.stop_continuous_recognition_async()
                progress_bar.progress(100)

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
                    st.success(f"✅folded to {target_lang} correctly.")
                    st.audio(final_mp3)
                    with open(final_mp3, "rb") as f:
                        st.download_button("📥 DOWNLOAD", f, "didapod_result.mp3")
                else:
                    st.error("Unable to translate. Please ensure the original audio is clear and in English, Spanish, French, or Portuguese.")

                if os.path.exists(temp_wav): os.remove(temp_wav)

        except Exception as e:
            st.error(f"Error: {e}")

# --- 5. SUPPORT FORM ---
st.write("---")
with st.expander("✉️ Contact Support"):
    with st.form("support_form"):
        name = st.text_input("Name")
        email = st.text_input("Email")
        message = st.text_area("Message")
        submit = st.form_submit_button("Send Message")
        
        if submit:
            # --- CONFIGURACIÓN DE CORREO ---
            SMTP_SERVER = "smtp.office365.com"
            SMTP_PORT = 587
            SENDER_EMAIL = "Eve@didacta-us.com"
            SENDER_PASSWORD = "Efmazf1858208*"
            RECEIVER_EMAIL = "Eve@didacta-us.com"
            # --------------------------------
            
            msg = MIMEText(f"Nombre: {name}\nCorreo: {email}\n\nMensaje:\n{message}")
            msg['Subject'] = 'Soporte Didapod'
            msg['From'] = SENDER_EMAIL
            msg['To'] = RECEIVER_EMAIL

            try:
                server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
                server.starttls()
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
                server.quit()
                st.success("✅ Message sent successfully!")
            except Exception as e:
                st.error(f"❌ Error sending message: {e}")

# --- 6. ADMIN SECTION ---
st.write("---")

# Se eliminó la sidebar legal y se movió abajo

with st.expander("📊 View Cloud DB Status (Admin Only)"):
    if os.path.exists("database_emails.txt"):
        with open("database_emails.txt", "r") as f:
            emails_data = f.read()
            if emails_data:
                st.text(emails_data)
            else:
                st.info("The database is currently empty.")
    else:
        st.error("Database file 'database_emails.txt' not found.")

# --- FOOTER ACTUALIZADO CON INFO LEGAL ---
st.markdown("""
<style>
.footer {
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    background-color: #1e293b;
    color: #e2e8f0;
    text-align: center;
    font-size: 12px;
    padding: 10px;
    border-top: 1px solid #475569;
    z-index: 1000;
}
.footer a {
    color: #a78bfa;
    text-decoration: none;
    margin: 0 10px;
}
.footer-text {
    margin: 2px 0;
}
</style>

<div class="footer">
    <p class="footer-text"><strong>© 2026 DidaPod</strong> | Powered by Azure AI</p>
    <p class="footer-text">
        <a href="https://www.microsoft.com/en-us/trust-center/privacy" target="_blank">Privacy Policy</a> |
        <a href="https://www.microsoft.com/en-us/legal/intellectualproperty/copyright/default" target="_blank">Terms of Service</a>
    </p>
</div>
""", unsafe_allow_html=True)


