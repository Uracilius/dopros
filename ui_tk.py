import tkinter as tk
import threading
import time
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
        # accumulator for live transcript
        self._accumulated = ""

    def run(self):
        self._accumulated = ""
        last_known_transcription = ""

        def background_record():
            self._final_text, self._final_mp3 = self.transcriber.record_and_transcribe()

        # Start recording in background
        recording_thread = threading.Thread(target=background_record)
        recording_thread.start()

        # Poll the result file for updates
        while not self._stop_flag and recording_thread.is_alive():
            time.sleep(0.5)

            try:
                with open(config.TRANSCRIPTION_RESULT_PATH, "r", encoding="utf-8") as f:
                    current = f.read().strip()
            except FileNotFoundError:
                current = ""

            if current and current != last_known_transcription:
                new_content = current[len(last_known_transcription):].strip()
                last_known_transcription = current
                self._accumulated = current
                if new_content and self.on_transcription_done:
                    self.on_transcription_done(current)

        # Wait for the recording thread to finish
        recording_thread.join()

        # Final update (just in case)
        final_text = self._accumulated.strip() or getattr(self, "_final_text", "")
        mp3_path = getattr(self, "_final_mp3", "")

        if self.on_transcription_done:
            self.on_transcription_done(final_text)

        improved = self.llm.improve_transcription(final_text)

        if self.on_improved_transcription_done:
            self.on_improved_transcription_done(improved)

        info_units_unprocessed = self.llm.summarize(improved)
        info_units = info_units_unprocessed.split("\n")

        if self.on_analysis_done:
            self.on_analysis_done(info_units_unprocessed)

        created_transcription = None
        if self.orchestrator and self.case_id:
            created_transcription = self.orchestrator.create_transcription(
                {
                    "title": f"Transcription at {time.strftime('%Y-%m-%d %H:%M:%S')}",
                    "case_id": self.case_id,
                    "full_text": final_text,
                    "improved_text": improved,
                    "description": "",
                    "mp3_url": mp3_path,
                }
            )

        if len(info_units) > 0 and created_transcription:
            for text_unit in info_units:
                self.orchestrator.create_info_unit(
                    case_id=self.case_id,
                    transcription_id=created_transcription.id,
                    text=text_unit,
                    language=self.language,
                )

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
        self.configure(bg="#2d2d30")

        self.start_time = time.time()
        print("Initializing transcriber...")
        self.transcriber = Transcriber()
        print("Transcriber initialized, time taken is ", time.time() - self.start_time)

        self.start_time = time.time()
        print("Initializing LLM...")
        self.llm = LLM()
        print("LLM initialized, time taken is ", time.time() - self.start_time)

        self.start_time = time.time()
        print("Initializing Orchestrator...")
        self.orchestrator = Orchestrator()
        print("Orchestrator initialized, time taken is ", time.time() - self.start_time)

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

        self.build_main_screen()
        self.build_second_screen()

    def build_case_selection_screen(self):
        label = tk.Label(
            self.case_selection_screen,
            text="Select Case",
            fg="#ffffff",
            bg="#2d2d30",
            font=("Arial", 10),
        )
        label.pack(pady=10)

        self.case_listbox = tk.Listbox(
            self.case_selection_screen, bg="#1e1e1e", fg="#c0c0c0", font=("Arial", 8)
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
        self.case_map = {}
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
        container = tk.Frame(self.main_screen, bg="#2d2d30")
        container.pack(expand=True, fill="both")

        self.mic_button = tk.Button(
            container,
            text="Mic",
            command=self.go_to_second_screen,
            bg="#3e3e42",
            fg="#ffffff",
            activebackground="#505050",
            width=10,
            height=5,
        )
        self.mic_button.pack(side="left", expand=True, fill="both")

        self.list_button = tk.Button(
            container,
            text="List",
            command=self.show_transcriptions,
            bg="#3e3e42",
            fg="#ffffff",
            activebackground="#505050",
            width=10,
            height=5,
        )
        self.list_button.pack(side="left", expand=True, fill="both")

    def build_second_screen(self):
        top_frame = tk.Frame(self.second_screen, bg="#2d2d30")
        top_frame.pack(side="top", fill="x", pady=5)

        self.record_button = tk.Button(
            top_frame,
            text="Record",
            command=self.start_recording,
            bg="#3e3e42",
            fg="#ffffff",
            activebackground="#505050",
            width=4,
            height=1,
        )
        self.record_button.pack(side="left", padx=5)

        self.stop_button = tk.Button(
            top_frame,
            text="Stop",
            command=self.stop_recording,
            bg="#3e3e42",
            fg="#ffffff",
            activebackground="#505050",
            width=4,
            height=1,
        )
        self.stop_button.pack(side="left", padx=5)
        self.stop_button.pack_forget()

        self.back_button = tk.Button(
            top_frame,
            text="Back",
            command=self.go_to_main_screen,
            bg="#3e3e42",
            fg="#ffffff",
            activebackground="#505050",
            width=2,
            height=1,
        )
        self.back_button.pack(side="left", padx=5)

        self.language_button = tk.Button(
            top_frame,
            text="RUS",
            command=self.toggle_language,
            bg="#3e3e42",
            fg="#ffffff",
            activebackground="#505050",
            width=2,
            height=1,
        )
        self.language_button.pack(side="left", padx=5)

        textboxes_frame = tk.Frame(self.second_screen, bg="#2d2d30")
        textboxes_frame.pack(expand=True, fill="both")

        self.transcription_textbox = tk.Text(
            textboxes_frame, bg="#1e1e1e", fg="#c0c0c0", width=17, height=7
        )
        self.transcription_textbox.pack(side="left", expand=True, fill="both", padx=5)

        self.improved_transcription_textbox = tk.Text(
            textboxes_frame, bg="#1e1e1e", fg="#c0c0c0", width=17, height=7
        )
        self.improved_transcription_textbox.pack(
            side="left", expand=True, fill="both", padx=5
        )

        self.analysis_textbox = tk.Text(
            textboxes_frame, bg="#1e1e1e", fg="#c0c0c0", width=17, height=7
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
                threading.Thread(target=self.post_analysis).start()

            threading.Thread(target=wait_for_thread).start()

        self.stop_button.pack_forget()
        self.record_button.pack(side="left", padx=5)

    def post_analysis(self):
        if not self.case_id_selected:
            return

        info_units = self.orchestrator.get_info_unit_list(self.case_id_selected)
        if not info_units:
            print("No info units found for analysis.")
            return

        all_text = "\n".join([unit.text for unit in info_units])
        try:
            result = self.llm.analyze(all_text, all_facts=info_units)
        except Exception as e:
            result = f"Error during analysis: {e}"

        self.analysis_textbox.after(0, lambda: self.update_analysis_box(result))

    def update_analysis_box(self, content):
        self.analysis_textbox.delete("1.0", tk.END)
        self.analysis_textbox.insert(tk.END, content)

    def handle_transcription(self, transcription):
        self.transcription_textbox.delete("1.0", tk.END)
        self.transcription_textbox.insert(
            tk.END, transcription if isinstance(transcription, str) else ""
        )

    def handle_improved_transcription(self, improved):
        self.improved_transcription_textbox.delete("1.0", tk.END)
        self.improved_transcription_textbox.insert(tk.END, improved)

    def handle_analysis(self, analysis):
        self.analysis_textbox.delete("1.0", tk.END)
        self.analysis_textbox.insert(
            tk.END, analysis if isinstance(analysis, str) else ""
        )

    def toggle_language(self):
        if self.language == Language.RUSSIAN.value:
            self.language = Language.KAZAKH.value
            self.language_button.config(text=Language.KAZAKH.value)
        else:
            self.language = Language.RUSSIAN.value
            self.language_button.config(text=Language.RUSSIAN.value)

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
                f"Full Text: {rec.full_text}\n"
                f"Improved Text: {rec.improved_text}\n"
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
    main()
