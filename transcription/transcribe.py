import streamlit as st
import nemo.collections.asr as nemo_asr
import torch
import pyaudio
import wave
import tempfile
import logging
import nemo.utils
import warnings

# Suppress extra logs
logging.getLogger("nemo_logger").setLevel(logging.ERROR)
nemo.utils.logging.setLevel(logging.ERROR)
warnings.filterwarnings("ignore", category=UserWarning)

class Transcriber:
    def __init__(
        self,
        model_path="transcription/transcription_model/stt_kk_ru_fastconformer_hybrid_large.nemo"
    ):

        # Restore model and move it to the chosen device
        self.model = nemo_asr.models.EncDecHybridRNNTCTCBPEModel.restore_from(model_path)

    def transcribe_audio(self, file_path):
        """
        Transcribes an audio file (.wav) using the ASR model.
        """
        output = self.model.transcribe([file_path])
        # If the model output is a tuple: (logits, processed_text)
        if isinstance(output, tuple) and len(output) == 2:
            processed_text = output[1]
            return processed_text[0] if processed_text else None
        # Otherwise, if the model returns a list of strings
        if isinstance(output, list) and len(output) > 0 and isinstance(output[0], str):
            return output[0]
        return None

    def record_and_transcribe(self, chunk_length_s=2):
        """
        Captures audio for 'chunk_length_s' seconds and transcribes it.
        Also saves the transcription to 'transcription/transcription.txt'.
        """
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=1024
        )

        frames = []
        try:
            # Record audio in chunks
            for _ in range(0, int(16000 / 1024 * chunk_length_s)):
                data = stream.read(1024, exception_on_overflow=False)
                frames.append(data)

            # Save the recorded chunk to a temporary .wav file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav:
                wav_filename = tmp_wav.name
                with wave.open(wav_filename, "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
                    wf.setframerate(16000)
                    wf.writeframes(b''.join(frames))

            # Transcribe the temporary file
            transcription = self.transcribe_audio(wav_filename)

            # Save the transcription to a file
            if transcription:
                with open("transcription/transcription.txt", "a", encoding="utf-8") as f:
                    f.write(transcription + "\n")

            return transcription

        except Exception as e:
            print(f"Error during transcription: {e}")
            return None
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()

if __name__ == "__main__":
    ### Streamlit UI ###
    st.title("Стенограмма речи, смешанная(kk/rus)")

    # Create the Transcriber once in session state
    if "transcriber" not in st.session_state:
        st.session_state.transcriber = Transcriber()

    if st.button("Начать запись"):

        all_transcriptions = []
        for i in range(1, 11):
            text = st.session_state.transcriber.record_and_transcribe(chunk_length_s=5)
            if len(text) > 1:
                all_transcriptions.append(text)
                st.write(f"*: {text}")
            else:
                all_transcriptions.append("")
                st.write(f"*: (Нет речи)")
        
