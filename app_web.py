import azure.cognitiveservices.speech as speechsdk
import os
import streamlit as st

# Si usas Streamlit Cloud, usa st.secrets
AZURE_KEY = st.secrets["AZURE_SPEECH_KEY"]
AZURE_REGION = st.secrets["AZURE_SPEECH_REGION"]

# --- 5. LÓGICA DE DOBLAJE PROFESIONAL CON AZURE ---
col1, col2 = st.columns(2)
with col1:
    target_lang_name = st.selectbox("Select Target Language:", ["English", "Spanish", "French", "Portuguese"])
with col2:
    voice_gender = st.selectbox("Select Voice Gender:", ["Female", "Male"])

up_file = st.file_uploader("Upload podcast", type=["mp3", "wav"])

if up_file:
    st.audio(up_file)
    if st.button("🚀 START AZURE AI DUBBING"):
        try:
            with st.spinner("🤖 Azure is detecting language and dubbing..."):
                # 1. Guardar archivo para Azure
                input_filename = "temp_input.wav"
                with open(input_filename, "wb") as f:
                    f.write(up_file.getbuffer())

                # 2. Configuración de Azure Speech
                translation_config = speechsdk.translation.SpeechTranslationConfig(
                    subscription=AZURE_KEY, 
                    region=AZURE_REGION
                )
                
                # Mapeo de idiomas
                lang_map = {"English": "en", "Spanish": "es", "French": "fr", "Portuguese": "pt"}
                target_code = lang_map[target_lang_name]
                
                # Configuramos para que Azure DETECTE automáticamente la entrada (Auto-detect)
                # Y traduzca al idioma destino elegido
                translation_config.add_target_language(target_code)
                
                # Configuración de audio de entrada
                audio_config = speechsdk.audio.AudioConfig(filename=input_filename)
                
                # 3. Traductor de Azure
                translator = speechsdk.translation.TranslationRecognizer(
                    translation_config=translation_config, 
                    audio_config=audio_config
                )

                # Ejecutar el proceso
                result = translator.recognize_once_async().get()

                if result.reason == speechsdk.ResultReason.TranslatedSpeech:
                    # Azure detecta qué idioma se habló originalmente
                    detected_src_lang = result.language
                    texto_traducido = result.translations[target_code]
                    
                    st.success(f"✅ Detected Source: {detected_src_lang.upper()}")
                    st.info(f"📝 Translated Text: {texto_traducido}")

                    # 4. Síntesis de Voz (Text-to-Speech Azure)
                    speech_config = speechsdk.SpeechConfig(subscription=AZURE_KEY, region=AZURE_REGION)
                    
                    # Voces Neurales PRO de Azure
                    azure_voices = {
                        "English": {"Female": "en-US-JennyNeural", "Male": "en-US-GuyNeural"},
                        "Spanish": {"Female": "es-ES-ElviraNeural", "Male": "es-ES-AlvaroNeural"},
                        "French": {"Female": "fr-FR-DeniseNeural", "Male": "fr-FR-HenriNeural"},
                        "Portuguese": {"Female": "pt-BR-FranciscaNeural", "Male": "pt-BR-AntonioNeural"}
                    }
                    
                    selected_voice = azure_voices[target_lang_name][voice_gender]
                    speech_config.speech_synthesis_voice_name = selected_voice
                    
                    output_filename = "result_azure.mp3"
                    audio_output = speechsdk.audio.AudioOutputConfig(filename=output_filename)
                    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_output)
                    
                    # Generar el audio final traducido
                    synthesizer.speak_text_async(texto_traducido).get()

                    # 5. Mostrar y descargar
                    st.balloons()
                    st.audio(output_filename)
                    with open(output_filename, "rb") as f:
                        st.download_button("📥 DOWNLOAD DUBBED PODCAST", f, "didapod_azure.mp3")
                
                elif result.reason == speechsdk.ResultReason.NoMatch:
                    st.error("Azure could not hear any speech. Check the audio quality.")
                else:
                    st.error(f"Azure Error: {result.reason}")

        except Exception as e:
            st.error(f"Critical System Error: {e}")
