import streamlit as st
import azure.cognitiveservices.speech as speechsdk
import os, time
from pydub import AudioSegment

st.set_page_config(page_title="DIDAPOD PRO", page_icon="🎙️")

def get_clean_secret(name):
    val = st.secrets.get(name, "")
    return "".join(str(val).split()).replace('"', '').replace("'", "").strip()

AZ_KEY = get_clean_secret("AZURE_KEY")
AZ_REG = get_clean_secret("AZURE_SPEECH_REGION")

st.title("🎙️ DIDAPOD PRO (Long Audio Support)")

target_lang = st.selectbox("Idioma Destino:", ["English", "Spanish", "French", "Portuguese"])
voice_gender = st.selectbox("Género de Voz:", ["Female", "Male"])
up_file = st.file_uploader("Sube tu podcast", type=["mp3", "wav"])

if up_file and AZ_KEY:
    st.audio(up_file)
    if st.button("🚀 START AI DUBBING"):
        all_text = []
        state = {"done": False}
        
        try:
            with st.spinner(f"⌛ Procesando {up_file.name} (22+ min). Esto puede tardar..."):
                # 1. Preparar audio largo
                audio = AudioSegment.from_file(up_file)
                audio = audio.set_frame_rate(16000).set_channels(1)
                temp_wav = "temp_long.wav"
                audio.export(temp_wav, format="wav")

                # 2. Configuración de Azure
                t_cfg = speechsdk.translation.SpeechTranslationConfig(subscription=AZ_KEY, region=AZ_REG)
                t_cfg.speech_recognition_language = "es-ES" 
                l_map = {"English": "en", "Spanish": "es", "French": "fr", "Portuguese": "pt"}
                t_cfg.add_target_language(l_map[target_lang])
                
                # Aumentar tiempos de espera para audios largos
                t_cfg.set_property(speechsdk.PropertyId.Speech_SegmentationSilenceTimeoutMs, "5000")

                audio_config = speechsdk.audio.AudioConfig(filename=temp_wav)
                recognizer = speechsdk.translation.TranslationRecognizer(translation_config=t_cfg, audio_config=audio_config)

                # 3. Manejo de eventos para audio continuo
                def handle_final_result(evt):
                    if evt.result.reason == speechsdk.ResultReason.TranslatedSpeech:
                        txt = evt.result.translations.get(l_map[target_lang], "")
                        if txt: all_text.append(txt)

                def stop_cb(evt):
                    state["done"] = True

                recognizer.recognized.connect(handle_final_result)
                recognizer.session_stopped.connect(stop_cb)
                recognizer.canceled.connect(stop_cb)

                # 4. Iniciar y esperar a que termine TODO el archivo
                recognizer.start_continuous_recognition_async()
                
                # Barra de progreso visual para el usuario
                progress_bar = st.progress(0)
                while not state["done"]:
                    time.sleep(1)
                    # Simulación de progreso para que el usuario no piense que se trabó
                    progress_bar.progress(min(len(all_text) * 2, 99)) 
                
                recognizer.stop_continuous_recognition_async()

                # 5. Unir y Generar Audio Final
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

                    st.success("✅ Doblaje de 23 min completado con éxito.")
                    st.audio(final_mp3)
                else:
                    st.error("No se pudo extraer texto del audio largo.")

                if os.path.exists(temp_wav): os.remove(temp_wav)

        except Exception as e:
            st.error(f"Error en proceso largo: {e}")
