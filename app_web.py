import streamlit as st
import edge_tts
import asyncio
import os
import base64
import speech_recognition as sr
from deep_translator import GoogleTranslator
from pydub import AudioSegment

# 1. Configuración de página
st.set_page_config(page_title="DIDAPOD PRO", page_icon="🎙️")

# 2. Estilos Visuales
st.markdown("""
    <style>
    .stApp { background-color: #0f172a !important; color: white !important; }
    h1, h2, h3, p, label { color: white !important; }
    .stButton>button { background-color: #7c3aed !important; color: white !important; border-radius: 10px; width: 100%; }
    /* Estilo para la barra de progreso */
    .stProgress > div > div > div > div { background-color: #7c3aed !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. Encabezado
st.title("🎙️ DIDAPOD PRO")

# 4. Lógica de Procesamiento Optimizada
target_lang = st.selectbox("Select Target Language:", ["English", "Spanish", "French", "Portuguese"])
up_file = st.file_uploader("Upload podcast", type=["mp3", "wav"])

if up_file:
    st.audio(up_file)
    if st.button("🚀 START AI DUBBING"):
        try:
            # Creamos contenedores para la información de progreso
            status_text = st.empty()
            progress_bar = st.progress(0)
            
            with st.spinner("🤖 AI is preparing the engine..."):
                with open("temp.mp3", "wb") as f: f.write(up_file.getbuffer())
                audio = AudioSegment.from_file("temp.mp3")
                
                # Reducimos a 25 segundos para que procese más rápido cada bloque
                chunk_length = 25000 
                chunks = [audio[i:i + chunk_length] for i in range(0, len(audio), chunk_length)]
                total_chunks = len(chunks)
                
                final_audio = AudioSegment.empty()
                r = sr.Recognizer()
                
                codes = {"English": "en", "Spanish": "es", "French": "fr", "Portuguese": "pt"}
                voice_m = {"English": "en-US-EmmaMultilingualNeural", "Spanish": "es-ES-ElviraNeural", "French": "fr-FR-DeniseNeural", "Portuguese": "pt-BR-FranciscaNeural"}

                for i, chunk in enumerate(chunks):
                    # Actualizamos barra y texto
                    percent = (i + 1) / total_chunks
                    progress_bar.progress(percent)
                    status_text.text(f"Processing segment {i+1} of {total_chunks}...")
                    
                    chunk.export("c.wav", format="wav")
                    with sr.AudioFile("c.wav") as src:
                        try:
                            # Reconocimiento y traducción rápida
                            text = r.recognize_google(r.record(src), language="es-ES")
                            trans = GoogleTranslator(source='auto', target=codes[target_lang]).translate(text)
                            asyncio.run(edge_tts.Communicate(trans, voice_m[target_lang]).save(f"v{i}.mp3"))
                            final_audio += AudioSegment.from_file(f"v{i}.mp3")
                            os.remove(f"v{i}.mp3")
                        except: continue
                
                final_audio.export("result.mp3", format="mp3")
            
            st.balloons()
            status_text.success("✅ Dubbing Complete!")
            st.audio("result.mp3")
            with open("result.mp3", "rb") as f:
                st.download_button("📥 DOWNLOAD", f, "result.mp3")

        except Exception as e: 
            st.error(f"Error: {e}")
