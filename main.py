from transcription.transcribe import Transcriber
from llm.llm import LLM
import keyboard
import time


class Orchestrator:
    def __init__(self):
        self.transcriber = Transcriber()
        self.llm = LLM()
        self.stop_flag = False

        # Register the keyboard event correctly
        keyboard.on_press_key("q", self.stop_recording)

    def stop_recording(self, event):  # Accepts event argument
        print("Stopping recording...")  # Feedback when key is pressed
        self.stop_flag = True

    def orchestrate_kazakh(self):
        print("Starting transcription from microphone...")
        print("Press 'q' to stop recording.")

        while not self.stop_flag:
            self.transcriber.record_and_transcribe(chunk_length_s=5)
            time.sleep(0.1)

        with open("transcription.txt", "r", encoding="utf-8") as f:
            transcription = f.read()

        print("Improving transcription...")
        improved_transcription = self.llm.improve_kazakh_transcription(transcription)
        print(improved_transcription)
        with open("improved_transcription.txt", "w", encoding="utf-8") as f:
            f.write(improved_transcription)

        print("Summarizing transcription...")
        summary = self.llm.summarize(improved_transcription)
        with open("summary.txt", "w", encoding="utf-8") as f:
            f.write(summary)

        print(
            "Orchestration complete. Transcription, improved transcription, and summary saved."
        )


if __name__ == "__main__":
    orchestrator = Orchestrator()
    orchestrator.orchestrate_kazakh()
