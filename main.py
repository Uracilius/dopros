from transcription.transcriber import Transcriber
from llm.llm import LLM

class Orchestrator:
    def __init__(self):
        self.transcriber = Transcriber()
        self.llm = LLM()

    def orchestrate_kazakh(self):
        print("Starting transcription from microphone...")
        self.transcriber.transcribe_kazakh_from_microphone()
        
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

        print("Orchestration complete. Transcription, improved transcription, and summary saved.")

if __name__ == "__main__":
    orchestrator = Orchestrator()
    orchestrator.orchestrate_kazakh()