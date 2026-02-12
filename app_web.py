import streamlit as st
import azure.cognitiveservices.speech as speechsdk
import os, base64, requests, io

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="DIDAPOD PRO", page_icon="🎙️", layout="centered")

st.markdown("""
<style>
.stApp { background-color: #0f172a !important; }
.stButton>button {
    background-color: #7c3aed !important;
    color: white !important;
    border-radius: 12px !important;
    padding: 15px !important;
    font-weight: bold; width: 100%;
}
h1, h2, h3, label, p, span { color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. THE ULTIMATE CLEANER ---
def get_clean_secret(name):
    raw_val = st.secrets.get(name, "")
    # Eliminamos espacios, saltos de línea y cualquier tipo de comilla accidental
    clean_val = "".join(raw_val.split()).replace('"', '').replace("'", "").strip()
    return clean_val

AZ_KEY = get_clean_secret("AZURE_KEY")
AZ_REG = get_clean_secret("AZURE_SPEECH_REGION")

# --- 3. LOGIN ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    with st.form("login"):
        st.markdown("### 🔐 DIDAPOD ACCESS")
        u = st.text_input("Username", value="admin")
        p = st.text_input("Password", type="password", value="didactai2026")
        if st.form_submit_button("LOGIN"):
            if u == "admin" and p == "didactai2026":
                st.session_state["auth"] = True
                st.rerun()
            else: st.error("Access Denied.")
    st.stop()

# --- 4. APP INTERFACE ---
st.title("🎙️ DIDAPOD PRO")
st.write("Professional AI Dubbing Engine")

# Pequeño diagnóstico para ti (se puede borrar luego)
if not AZ_KEY:
    st.warning("⚠️ AZURE_KEY not found in Secrets!")

c1, c2 = st.columns(2)
with c1: lang = st.selectbox("Target Language:", ["English", "Spanish", "French", "Portuguese"])
with c2: gen = st.selectbox("Voice Gender:", ["Female", "Male"])

up = st.file_uploader("Upload Audio", type=["mp3", "wav"])

if up and AZ_KEY:
    st.audio(up)
    if st.button("🚀 START AI DUBBING PROCESS"):
        try:
            with st.spinner("🤖 Connecting to Azure AI..."):
                with open("temp.wav", "wb") as f: f.write(up.getbuffer())

                # Configuración de Azure
                t_cfg = speechsdk.translation.SpeechTranslationConfig(subscription=AZ_KEY, region=AZ_REG)
                l_map = {"English": "en", "Spanish": "es", "French": "fr", "Portuguese": "pt"}
                t_cfg.add_target_language(l_map[lang])
                
                audio_cfg = speechsdk.audio.AudioConfig(filename="temp.wav")
                reco = speechsdk.translation.TranslationRecognizer(t_cfg, audio_cfg)
                res = reco.recognize_once_async().get()

                if res.reason == speechsdk.ResultReason.TranslatedSpeech:
                    # Síntesis
                    s_cfg = speechsdk.SpeechConfig(subscription=AZ_KEY, region=AZ_REG)
                    v_db = {
                        "English": {"Female": "en-US-JennyNeural", "Male": "en-US-GuyNeural"},
                        "Spanish": {"Female": "es-ES-ElviraNeural", "Male": "es-ES-AlvaroNeural"},
                        "French": {"Female": "fr-FR-DeniseNeural", "Male": "fr-FR-HenriNeural"},
                        "Portuguese": {"Female": "pt-BR-FranciscaNeural", "Male": "pt-BR-AntonioNeural"}
                    }
                    s_cfg.speech_synthesis_voice_name = v_db[lang][gen]
                    
                    out_f = "dubbed.mp3"
                    audio_out = speechsdk.audio.AudioOutputConfig(filename=out_f)
                    syn = speechsdk.SpeechSynthesizer(s_cfg, audio_out)
                    syn.speak_text_async(res.translations[l_map[lang]]).get()

                    st.balloons()
                    st.success("Success!")
                    st.audio(out_f)
                    with open(out_f, "rb") as f:
                        st.download_button("📥 DOWNLOAD", f, "result.mp3")
                else:
                    # Si falla, mostramos el error detallado de Azure
                    st.error(f"Azure Rejected Access. Reason: {res.reason}")
                    st.info("Tip: If you see 'AuthenticationFailure', your Key might be expired or copied incorrectly.")
        except Exception as e:
            st.error(f"System Error: {e}")

st.markdown("<br><hr><center><small>© 2026 DidactAI-US</small></center>", unsafe_allow_html=True)
