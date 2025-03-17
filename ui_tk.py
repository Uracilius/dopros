import tkinter as tk
import threading
import time
import sys

from src.transcription.transcribe import Transcriber
from src.llm.llm import LLM
from src.enums import Language


class RecorderThread(threading.Thread):
    """
    Thread that continuously records audio in chunks, then emits final
    transcriptions and improved transcriptions once stopped.
    """

    def __init__(
        self,
        transcriber,
        llm,
        chunk_length_s=5,
        language=Language.RUSSIAN.value,
        on_transcription_done=None,
        on_improved_transcription_done=None,
    ):
        super().__init__()
        self.transcriber = transcriber
        self.llm = llm
        self.chunk_length_s = chunk_length_s
        self.language = language
        self._stop_flag = False
        self.on_transcription_done = on_transcription_done
        self.on_improved_transcription_done = on_improved_transcription_done

    def run(self):
        while not self._stop_flag:
            text = self.transcriber.record_and_transcribe(
                chunk_length_s=self.chunk_length_s
            )
            if self.on_transcription_done:
                self.on_transcription_done(text)
            time.sleep(0.1)

        # Once stopped, read the collected transcription from file
        transcription = ""
        with open("results/transcription.txt", "r", encoding="utf-8") as f:
            transcription = f.read()

        if self.on_transcription_done:
            self.on_transcription_done(transcription)

        # Improve transcription based on current language
        if self.language == Language.RUSSIAN.value:
            improved = self.llm.improve_russian_transcription(transcription)
        else:
            improved = self.llm.improve_kazakh_transcription(transcription)

        if self.on_improved_transcription_done:
            self.on_improved_transcription_done(improved)

        # Clear the file contents
        with open("results/transcription.txt", "w", encoding="utf-8") as f:
            f.write("")

    def stop(self):
        self._stop_flag = True


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("6.5-inch Screen Simulation")
        self.geometry("560x336")

        # If you want a dark background overall:
        self.configure(bg="#2d2d30")

        # Keep track of transcriber & LLM
        self.transcriber = Transcriber()
        self.llm = LLM()
        self.recorder_thread = None
        self.language = Language.RUSSIAN.value  # default

        # --- Create two "screens" (Frames) and raise one or the other ---
        self.main_screen = tk.Frame(self, bg="#2d2d30")
        self.second_screen = tk.Frame(self, bg="#2d2d30")
        # Use grid to stack them in the same space
        for frame in (self.main_screen, self.second_screen):
            frame.grid(row=0, column=0, sticky="nsew")

        self.build_main_screen()
        self.build_second_screen()

        # Show the main screen at startup
        self.show_frame(self.main_screen)

    def build_main_screen(self):
        """
        Main screen with two large side-by-side buttons: mic and list.
        """
        # A horizontal container
        container = tk.Frame(self.main_screen, bg="#2d2d30")
        container.pack(expand=True, fill="both")

        # "Microphone" button (navigates to second screen)
        self.mic_button = tk.Button(
            container,
            text="Mic",
            command=self.go_to_second_screen,
            bg="#3e3e42",
            fg="#ffffff",
            activebackground="#505050",
            width=20,
            height=10,  # approximate “big” button
        )
        self.mic_button.pack(side="left", expand=True, fill="both")

        # "List" button (no action assigned in original code)
        self.list_button = tk.Button(
            container,
            text="List",
            bg="#3e3e42",
            fg="#ffffff",
            activebackground="#505050",
            width=20,
            height=10,
        )
        self.list_button.pack(side="left", expand=True, fill="both")

    def build_second_screen(self):
        """
        Second screen with top row of buttons (Record, Stop, Back, Language)
        and two text boxes side by side for transcription and improved text.
        """
        # Top row for buttons
        top_frame = tk.Frame(self.second_screen, bg="#2d2d30")
        top_frame.pack(side="top", fill="x", pady=5)

        self.record_button = tk.Button(
            top_frame,
            text="Record",
            command=self.start_recording,
            bg="#3e3e42",
            fg="#ffffff",
            activebackground="#505050",
            width=8,
            height=2,
        )
        self.record_button.pack(side="left", padx=5)

        self.stop_button = tk.Button(
            top_frame,
            text="Stop",
            command=self.stop_recording,
            bg="#3e3e42",
            fg="#ffffff",
            activebackground="#505050",
            width=8,
            height=2,
        )
        self.stop_button.pack(side="left", padx=5)
        self.stop_button.pack_forget()  # hidden by default

        self.back_button = tk.Button(
            top_frame,
            text="Back",
            command=self.go_to_main_screen,
            bg="#3e3e42",
            fg="#ffffff",
            activebackground="#505050",
            width=5,
            height=2,
        )
        self.back_button.pack(side="left", padx=5)

        self.language_button = tk.Button(
            top_frame,
            text="RUS",
            command=self.toggle_language,
            bg="#3e3e42",
            fg="#ffffff",
            activebackground="#505050",
            width=5,
            height=2,
        )
        self.language_button.pack(side="left", padx=5)

        # Middle frame for the two text boxes
        textboxes_frame = tk.Frame(self.second_screen, bg="#2d2d30")
        textboxes_frame.pack(expand=True, fill="both")

        self.transcription_textbox = tk.Text(
            textboxes_frame, bg="#1e1e1e", fg="#c0c0c0", width=35, height=15
        )
        self.transcription_textbox.pack(side="left", expand=True, fill="both", padx=5)

        self.improved_transcription_textbox = tk.Text(
            textboxes_frame, bg="#1e1e1e", fg="#c0c0c0", width=35, height=15
        )
        self.improved_transcription_textbox.pack(
            side="left", expand=True, fill="both", padx=5
        )

    def show_frame(self, frame):
        frame.tkraise()

    def go_to_second_screen(self):
        self.show_frame(self.second_screen)

    def go_to_main_screen(self):
        self.show_frame(self.main_screen)

    def start_recording(self):
        print("Recording started...")
        self.record_button.pack_forget()
        self.stop_button.pack(side="left", padx=5)

        # Create & start the thread
        self.recorder_thread = RecorderThread(
            self.transcriber,
            self.llm,
            chunk_length_s=5,
            language=self.language,
            on_transcription_done=self.handle_transcription,
            on_improved_transcription_done=self.handle_improved_transcription,
        )
        self.recorder_thread.start()

    def stop_recording(self):
        if self.recorder_thread is not None:
            self.recorder_thread.stop()
            self.recorder_thread.join()
            self.recorder_thread = None

        self.stop_button.pack_forget()
        self.record_button.pack(side="left", padx=5)

    def handle_transcription(self, transcription):
        # Update the transcription box in the Tk thread
        self.transcription_textbox.delete("1.0", tk.END)
        self.transcription_textbox.insert(tk.END, transcription)

    def handle_improved_transcription(self, improved):
        self.improved_transcription_textbox.delete("1.0", tk.END)
        self.improved_transcription_textbox.insert(tk.END, improved)

    def toggle_language(self):
        if self.language == Language.RUSSIAN.value:
            self.language = Language.KAZAKH.value
            self.language_button.config(text="KAZ")
        else:
            self.language = Language.RUSSIAN.value
            self.language_button.config(text="RUS")


def main():
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
