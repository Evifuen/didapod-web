import streamlit as st
import azure.cognitiveservices.speech as speechsdk
import os
from deep_translator import GoogleTranslator
import speech_recognition as sr
from pydub import AudioSegment

# --- 1. CONFIGURACIÓN SEGURA ---
AZURE_KEY = st.secrets["AZURE_SPEECH_KEY"]
AZURE_REGION = st.secrets["AZURE_SPEECH_REGION"]

st.set_page_config(page_title="DIDAPOD PRO - Elvira Edition", page_icon="🎙️")

# --- 2. FUNCIÓN DE DOBLAJE CON ELVIRA ---
def doblaje_elvira(texto_traducido, archivo_salida):
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_KEY, region=AZURE_REGION)
    # Aquí configuramos a Elvira específicamente
    speech_config.speech_synthesis_voice_name = "es-ES-ElviraNeural" 
    
    audio_config = speechsdk.audio.AudioOutputConfig(filename=archivo_salida)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    # El .get() asegura que el audio se grabe completo
    resultado = synthesizer.speak_text_async(texto_traducido).get()
    return resultado

# --- 3. INTERFAZ DEL PODCAST ---
st.title("🎙️ Traductor de Podcast (Voz: Elvira)")
archivo_podcast = st.file_uploader("Sube tu podcast original", type=["mp3", "wav", "m4a"])

if archivo_podcast:
    st.audio(archivo_podcast, format="audio/mp3")
    
    if st.button("Traducir Podcast con Elvira"):
        with st.spinner("Escuchando, traduciendo y doblando..."):
            # Lógica de transcripción (Speech-to-Text)
            # 1. Guardar archivo temporal
            with open("temp.mp3", "wb") as f:
                f.write(archivo_podcast.getbuffer())
            
            # (Aquí va tu bloque de speech_recognition para obtener el 'texto_original')
            texto_original = "Hola, bienvenidos a mi podcast." # Ejemplo
            
            # 2. Traducción
            texto_espanol = GoogleTranslator(source='auto', target='es').translate(texto_original)
            
            # 3. Generación de Audio con Azure y Elvira
            nombre_final = "podcast_final_elvira.mp3"
            res = doblaje_elvira(texto_espanol, nombre_final)
            
            if res.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                st.success("¡Doblaje listo! Escucha a Elvira:")
                st.audio(nombre_final)
                
                with open(nombre_final, "rb") as f:
                    st.download_button("Descargar Podcast Traducido", f, file_name=nombre_final)
                
                st.info("¡Tu contador de Azure debería subir pronto!")
            else:
                st.error("Hubo un problema con la voz de Elvira.")
   


