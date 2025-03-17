import os
import wave
import torch
import librosa
import numpy as np
import pyaudio
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC


class Transcriber:
    def __init__(
        self,
        model_path="transcription/transcription_model",
        audio_chunk_dir="./audio_chunks",
        device=None,
    ):
        self.is_continue_transcription_loop = False
        self.audio_chunk_dir = audio_chunk_dir
        self.device = (
            device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        )

        # Load Model and Processor
        self.processor = Wav2Vec2Processor.from_pretrained(model_path)
        self.model = Wav2Vec2ForCTC.from_pretrained(model_path).to(self.device)

    def transcribe_kazakh_from_microphone(self, chunk_length_s=5):
        """
        Captures audio from the microphone in real-time and transcribes it.
        """
        self.is_continue_transcription_loop = True

        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=1024,
        )

        try:
            while self.is_continue_transcription_loop:
                frames = []
                for _ in range(0, int(16000 / 1024 * chunk_length_s)):
                    data = stream.read(1024, exception_on_overflow=False)
                    frames.append(data)

                audio_data = b"".join(frames)
                audio_waveform = (
                    torch.tensor(
                        librosa.util.buf_to_float(audio_data, dtype=np.float32)
                    )
                    .unsqueeze(0)
                    .to(self.device)
                )

                text = self.transcribe_audio(audio_waveform)

                with open("transcription.txt", "a", encoding="utf-8") as f:
                    f.write(text + "\n")

            return 1

        except KeyboardInterrupt:
            print("\nStopping live transcription...")
        except Exception as e:
            print(f"Error during high-level transcription: {e}")

        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()

    def transcribe_audio(self, audio_tensor):
        """
        Transcribes an audio waveform tensor using the wav2vec2 model.
        """
        with torch.no_grad():
            logits = self.model(audio_tensor).logits
        predicted_ids = torch.argmax(logits, dim=-1)
        transcription = self.processor.batch_decode(predicted_ids)[0]
        return transcription
