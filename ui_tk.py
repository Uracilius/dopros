import tkinter as tk
import threading
import time
import sys
from tkinter import messagebox

from src.transcription.transcribe import Transcriber
from src.llm.llm import LLM
from src.enums import Language
from src.case.orchestrator import Orchestrator
import config


class RecorderThread(threading.Thread):
    """
    Thread that continuously records audio in chunks, then emits final
    transcriptions and improved transcriptions once stopped.
    """

    def __init__(
        self,
        transcriber: Transcriber,
        llm: LLM,
        chunk_length_s=5,
        language=Language.RUSSIAN.value,
        on_transcription_done=None,
        on_improved_transcription_done=None,
        on_analysis_done=None,
    ):
        super().__init__()
        self.transcriber = transcriber
        self.llm = llm
        self.chunk_length_s = chunk_length_s
        self.language = language
        self._stop_flag = False
        self.on_transcription_done = on_transcription_done
        self.on_improved_transcription_done = on_improved_transcription_done
        self.on_analysis_done = on_analysis_done
        self.orchestrator: Orchestrator = None
        self.case_id = None

    def run(self):
        while not self._stop_flag:
            text, mp3_path = self.transcriber.record_and_transcribe(
                chunk_length_s=self.chunk_length_s
            )

            if self.on_transcription_done:
                self.on_transcription_done(text)
            time.sleep(0.1)

        # Once stopped, read the collected transcription from file
        transcription = ""
        with open(config.TRANSCRIPTION_RESULT_PATH, "r", encoding="utf-8") as f:
            transcription = f.read()

        if self.on_transcription_done:
            self.on_transcription_done(transcription)

        improved = self.llm.improve_transcription(transcription)

        # Improve transcription based on current language
        # if self.language == Language.RUSSIAN.value:
        #     improved = self.llm.improve_russian_transcription(transcription)
        # else:
        #     improved = self.llm.improve_kazakh_transcription(transcription)

        if self.on_improved_transcription_done:
            self.on_improved_transcription_done(improved)

        analysis = self.llm.summarize(improved)

        analysis_points = analysis.split("\n")

        if self.on_analysis_done:
            self.on_analysis_done(analysis)

        created_transcription = None
        # Save transcription to database
        if self.orchestrator and self.case_id:
            created_transcription = self.orchestrator.create_transcription(
                {
                    "title": f"Transcription at {time.strftime('%Y-%m-%d %H:%M:%S')}",
                    "case_id": self.case_id,
                    "full_text": transcription,
                    "improved_text": improved,
                    "description": "",
                    "mp3_url": mp3_path,
                }
            )
        
        if len(analysis_points) > 0 and created_transcription:
            for text in analysis_points:
                self.orchestrator.create_info_unit(
                    case_id=self.case_id,
                    transcription_id=created_transcription.id,
                    text=text,
                    language=self.language,
                )

        # Clear the file contents
        with open(config.TRANSCRIPTION_RESULT_PATH, "w", encoding="utf-8") as f:
            f.write("")

    def stop(self):
        self._stop_flag = True
        self.transcriber.stop_recording.set()


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
        self.orchestrator = Orchestrator()

        self.recorder_thread = None
        self.language = Language.RUSSIAN.value

        self.main_screen = tk.Frame(self, bg="#2d2d30")
        self.second_screen = tk.Frame(self, bg="#2d2d30")

        self.case_selection_screen = tk.Frame(self, bg="#2d2d30")
        self.case_id_selected = None

        for frame in (self.case_selection_screen, self.main_screen, self.second_screen):
            frame.grid(row=0, column=0, sticky="nsew")

        self.build_case_selection_screen()
        self.show_frame(self.case_selection_screen)

        for frame in (self.main_screen, self.second_screen):
            frame.grid(row=0, column=0, sticky="nsew")

        self.build_main_screen()
        self.build_second_screen()

    def build_case_selection_screen(self):
        label = tk.Label(
            self.case_selection_screen,
            text="Select Case",
            fg="#ffffff",
            bg="#2d2d30",
            font=("Arial", 16),
        )
        label.pack(pady=10)

        self.case_listbox = tk.Listbox(
            self.case_selection_screen, bg="#1e1e1e", fg="#c0c0c0", font=("Arial", 12)
        )
        self.case_listbox.pack(fill="both", expand=True, padx=20, pady=10)

        proceed_button = tk.Button(
            self.case_selection_screen,
            text="Proceed",
            command=self.on_case_selected,
            bg="#3e3e42",
            fg="#ffffff",
            activebackground="#505050",
            height=2,
        )
        proceed_button.pack(pady=10)

        self.populate_case_list()

    def populate_case_list(self):
        self.case_listbox.delete(0, tk.END)
        cases = self.orchestrator.get_case_list()
        print(cases)
        self.case_map = {}  # idx -> case_id
        for idx, case in enumerate(cases):
            label = f"{case.id} ({case.status})"
            self.case_listbox.insert(tk.END, label)
            self.case_map[idx] = case.id

    def on_case_selected(self):
        sel = self.case_listbox.curselection()
        if not sel:
            messagebox.showinfo("No selection", "Please select a case.")
            return
        self.case_id_selected = self.case_map[sel[0]]
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
            command=self.show_transcriptions,  #  <-- hook it up
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

        self.analysis_textbox = tk.Text(
            textboxes_frame, bg="#1e1e1e", fg="#c0c0c0", width=35, height=15
        )
        self.analysis_textbox.pack(side="left", expand=True, fill="both", padx=5)

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

        self.recorder_thread = RecorderThread(
            self.transcriber,
            self.llm,
            chunk_length_s=5,
            language=self.language,
            on_transcription_done=self.handle_transcription,
            on_improved_transcription_done=self.handle_improved_transcription,
            on_analysis_done=self.handle_analysis,
        )
        self.recorder_thread.orchestrator = self.orchestrator
        self.recorder_thread.case_id = self.case_id_selected

        self.recorder_thread.start()

    def stop_recording(self):
        if self.recorder_thread is not None:
            self.recorder_thread.stop()

            def wait_for_thread():
                self.recorder_thread.join()
                self.recorder_thread = None

            threading.Thread(target=wait_for_thread).start()

        self.stop_button.pack_forget()
        self.record_button.pack(side="left", padx=5)

    def handle_transcription(self, transcription):
        self.transcription_textbox.delete("1.0", tk.END)
        if isinstance(transcription, str):
            self.transcription_textbox.insert(tk.END, transcription)
        else:
            self.transcription_textbox.insert(tk.END, "")

    def handle_improved_transcription(self, improved):
        self.improved_transcription_textbox.delete("1.0", tk.END)
        self.improved_transcription_textbox.insert(tk.END, improved)

    def handle_analysis(self, analysis):
        self.analysis_textbox.delete("1.0", tk.END)
        if isinstance(analysis, str):
            self.analysis_textbox.insert(tk.END, analysis)
        else:
            self.analysis_textbox.insert(tk.END, "")

    def toggle_language(self):
        if self.language == Language.RUSSIAN.value:
            self.language = Language.KAZAKH.value
            self.language_button.config(Language.KAZAKH.value)
        else:
            self.language = Language.RUSSIAN.value
            self.language_button.config(Language.RUSSIAN.value)

    def show_transcriptions(self):
        if not self.case_id_selected:
            messagebox.showinfo("No case", "No case selected.")
            return

        records = self.orchestrator.fetch_transcriptions_by_case_id(
            self.case_id_selected
        )
        if not records:
            messagebox.showinfo(
                "No data", f"No transcriptions for {self.case_id_selected}"
            )
            return

        popup = tk.Toplevel(self)
        popup.title(f"Transcriptions for {self.case_id_selected}")
        popup.geometry("500x300")
        popup.configure(bg="#2d2d30")

        listbox = tk.Listbox(popup, bg="#1e1e1e", fg="#c0c0c0")
        listbox.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        scrollbar = tk.Scrollbar(popup, command=listbox.yview)
        scrollbar.pack(side="left", fill="y")
        listbox.config(yscrollcommand=scrollbar.set)

        details = tk.Text(popup, bg="#1e1e1e", fg="#c0c0c0", state="disabled")
        details.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        # map listbox index -> record
        idx_to_rec = {}
        for idx, rec in enumerate(records):
            label = f"{rec.id}: {rec.title}"
            listbox.insert(tk.END, label)
            idx_to_rec[idx] = rec

        def on_select(event):
            sel = listbox.curselection()
            if not sel:
                return
            rec = idx_to_rec[sel[0]]

            info = (
                f"ID: {rec.id}\n"
                f"Title: {rec.title}\n"
                f"Description: {rec.description}\n"
                f"MP3 URL: {rec.mp3_url}\n"
                f"Status: {rec.status}\n"
                f"Created: {rec.create_date}\n"
                f"Updated: {rec.update_date}\n"
            )
            details.config(state="normal")
            details.delete("1.0", tk.END)
            details.insert(tk.END, info)
            details.config(state="disabled")

        listbox.bind("<<ListboxSelect>>", on_select)


def main():
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":

    import os

    main()
