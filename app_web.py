import streamlit as st
import azure.cognitiveservices.speech as speechsdk
import os
import base64
from deep_translator import GoogleTranslator
from pydub import AudioSegment

# --- 1. CONFIGURACIÓN DE SEGURIDAD (No expone tu llave) ---
# Estos nombres deben coincidir con lo que escribiste en Streamlit Secrets
AZURE_KEY = st.secrets["AZURE_SPEECH_KEY"]
AZURE_REGION = st.secrets["AZURE_SPEECH_REGION"]

# Configuración de la página
st.set_page_config(page_title="DIDAPOD PRO", page_icon="🎙️", layout="centered")

# --- 2. FUNCIÓN MAESTRA DE AZURE ---
def generar_audio_azure(texto, archivo_salida):
    """
    Conecta con el recurso 'didapod' y genera el audio profesional.
    El uso de .get() evita que el archivo pese solo 261 bytes.
    """
    # Configuración del servicio
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_KEY, region=AZURE_REGION)
    
    # Seleccionamos la voz neural (profesional)
    speech_config.speech_synthesis_voice_name = "es-ES-ElviraNeural" 
    
    # Configuramos la salida hacia el archivo físico
    audio_config = speechsdk.audio.AudioOutputConfig(filename=archivo_salida)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    # Esta línea hace que el contador de Azure suba de 0 a 1
    resultado = synthesizer.speak_text_async(texto).get()
    
    return resultado

# --- 3. INTERFAZ DE USUARIO ---
st.title("🎙️ Doblaje Profesional con Azure AI")
st.write("Escribe el texto que deseas convertir en voz profesional.")

texto_usuario = st.text_area("Texto a doblar:", placeholder="Hola, esto es una prueba de voz profesional...")

if st.button("Generar Doblaje"):
    if texto_usuario:
        with st.spinner("Procesando con Azure AI..."):
            nombre_archivo = "doblaje_final.mp3"
            
            # Llamada a la función
            resultado = generar_audio_azure(texto_usuario, nombre_archivo)
            
            if resultado.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                st.success("¡Audio generado con éxito!")
                
                # Reproductor de audio
                with open(nombre_archivo, "rb") as audio_file:
                    st.audio(audio_file.read(), format="audio/mp3")
                
                # Botón de descarga
                with open(nombre_archivo, "rb") as f:
                    st.download_button("Descargar Archivo MP3", f, file_name=nombre_archivo)
                
                st.info("Revisa tu portal de Azure en 5 minutos; el contador debería marcar '1'.")
            else:
                st.error("Error en la síntesis. Revisa los Secrets y la región 'eastus'.")
    else:
        st.warning("Por favor, introduce algún texto.")


