import tkinter as tk
from tkinter import scrolledtext, messagebox
from main import Orchestrator

class OrchestratorUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Kazakh Speech Transcription UI")
        
        self.orchestrator = Orchestrator()
        
        self.start_button = tk.Button(root, text="Start Transcription", command=self.start_transcription)
        self.start_button.pack(pady=10)
        
        self.text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=20)
        self.text_area.pack(pady=10)
        
        self.save_button = tk.Button(root, text="Save Results", command=self.save_results)
        self.save_button.pack(pady=10)
    
    def start_transcription(self):
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, "Starting transcription...\n")
        
        self.orchestrator.orchestrate_kazakh()
        
        with open("improved_transcription.txt", "r", encoding="utf-8") as f:
            improved_transcription = f.read()
        
        with open("summary.txt", "r", encoding="utf-8") as f:
            summary = f.read()
        
        result_text = f"Improved Transcription:\n{improved_transcription}\n\nSummary:\n{summary}"
        self.text_area.insert(tk.END, result_text)
    
    def save_results(self):
        try:
            with open("final_transcription.txt", "w", encoding="utf-8") as f:
                f.write(self.text_area.get(1.0, tk.END))
            messagebox.showinfo("Success", "Results saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save results: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = OrchestratorUI(root)
    root.mainloop()