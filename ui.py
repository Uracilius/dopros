import PyQt5.sip

from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget, QStyle, QPlainTextEdit
from PyQt5.QtCore import QThread, pyqtSignal
import sys
import time

from transcription.transcribe import Transcriber
from llm.llm import LLM
from enums import Language

class RecorderThread(QThread):
    transcription_done = pyqtSignal(str)
    improved_transcription_done = pyqtSignal(str)

    def __init__(self, transcriber, llm, chunk_length_s=5, language=Language.RUSSIAN.value):
        super().__init__()
        self.transcriber = transcriber
        self.llm = llm
        self.chunk_length_s = chunk_length_s
        self.language = language
        self._stop_flag = False

    def run(self):
        while not self._stop_flag:
            transcription_text = self.transcriber.record_and_transcribe(chunk_length_s=self.chunk_length_s)
            self.transcription_done.emit(transcription_text)
            time.sleep(0.1)
        transcription = ''
        with open("transcription/transcription.txt", "r", encoding="utf-8") as f:
            transcription = f.read()
        self.transcription_done.emit(transcription)
        
        if self.language == Language.RUSSIAN.value:
            improved_transcription = self.llm.improve_russian_transcription(transcription)
        else:
            improved_transcription = self.llm.improve_kazakh_transcription(transcription)
        
        self.improved_transcription_done.emit(improved_transcription)
        with open("transcription/transcription.txt", "w", encoding="utf-8") as f:
            f.write('')

    def stop(self):
        self._stop_flag = True

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.transcriber = Transcriber()
        self.llm = LLM()
        self.recorder_thread = None
        self.language = 'rus'  # Default language
        self.setWindowTitle("6.5-inch Screen Simulation")
        self.setGeometry(100, 100, 560, 336)
        
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        # Main Screen
        self.main_screen = QWidget()
        main_layout = QHBoxLayout()
        
        self.mic_button = QPushButton()
        self.mic_button.setIcon(self.style().standardIcon(QStyle.SP_MediaVolume))
        self.mic_button.setFixedSize(280, 336)
        self.mic_button.clicked.connect(self.go_to_second_screen)
        
        self.list_button = QPushButton()
        self.list_button.setIcon(self.style().standardIcon(QStyle.SP_FileDialogListView))
        self.list_button.setFixedSize(280, 336)
        
        main_layout.addWidget(self.mic_button)
        main_layout.addWidget(self.list_button)
        self.main_screen.setLayout(main_layout)
        self.stack.addWidget(self.main_screen)
        
        # Second Screen
        self.second_screen = QWidget()
        second_layout = QVBoxLayout()
        
        # Top layout for buttons
        top_buttons_layout = QHBoxLayout()
        self.record_button = QPushButton("Record")
        self.record_button.setFixedSize(75, 50)
        self.record_button.clicked.connect(self.start_recording)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.setFixedSize(75, 50)
        self.stop_button.clicked.connect(self.stop_recording)
        self.stop_button.setVisible(False)
        
        self.back_button = QPushButton("Back")
        self.back_button.setFixedSize(50, 50)
        self.back_button.clicked.connect(self.go_to_main_screen)
        
        self.language_button = QPushButton("RUS")
        self.language_button.setFixedSize(50, 50)
        self.language_button.clicked.connect(self.toggle_language)
        
        top_buttons_layout.addWidget(self.record_button)
        top_buttons_layout.addWidget(self.stop_button)
        top_buttons_layout.addWidget(self.back_button)
        top_buttons_layout.addWidget(self.language_button)
        second_layout.addLayout(top_buttons_layout)
        
        # Layout for text boxes
        textboxes_layout = QHBoxLayout()
        self.transcription_textbox = QPlainTextEdit()
        self.transcription_textbox.setFixedSize(280, 286)
        
        self.improved_transcription_textbox = QPlainTextEdit()
        self.improved_transcription_textbox.setFixedSize(280, 286)
        
        textboxes_layout.addWidget(self.transcription_textbox)
        textboxes_layout.addWidget(self.improved_transcription_textbox)
        second_layout.addLayout(textboxes_layout)
        
        self.second_screen.setLayout(second_layout)
        self.stack.addWidget(self.second_screen)
    
    def go_to_second_screen(self):
        self.stack.setCurrentWidget(self.second_screen)
    
    def start_recording(self):
        print("Recording started...")
        self.record_button.setVisible(False)
        self.stop_button.setVisible(True)
        
        # Initialize and start the recording thread
        self.recorder_thread = RecorderThread(self.transcriber, self.llm, chunk_length_s=5)
        self.recorder_thread.transcription_done.connect(self.handle_transcription)
        self.recorder_thread.improved_transcription_done.connect(self.handle_improved_transcription)
        self.recorder_thread.start()
    
    def stop_recording(self):
        if self.recorder_thread:
            self.recorder_thread.stop()
            self.recorder_thread.wait()  # Wait for the thread to finish
        self.stop_button.setVisible(False)
        self.record_button.setVisible(True)
    
    def handle_transcription(self, transcription):
        self.transcription_textbox.setPlainText(transcription)
    
    def handle_improved_transcription(self, improved_transcription):
        self.improved_transcription_textbox.setPlainText(improved_transcription)
    
    def go_to_main_screen(self):
        self.stack.setCurrentWidget(self.main_screen)

    def toggle_language(self):
        if self.language == Language.RUSSIAN.value:
            self.language = Language.KAZAKH.value
            self.language_button.setText("KAZ")
        else:
            self.language = Language.RUSSIAN.value
            self.language_button.setText("RUS")

def main():
    app = QApplication(sys.argv)
    
    # Global theme applied via Qt style sheets
    app.setStyleSheet("""
        QMainWindow {
            background-color: #2d2d30;
        }
        QPushButton {
            background-color: #3e3e42;
            color: #ffffff;
            border: 1px solid #4a4a4a;
            border-radius: 5px;
            padding: 10px;
            font-size: 14px;
        }
        QPushButton:hover {
            background-color: #505050;
        }
        QPlainTextEdit {
            background-color: #1e1e1e;
            color: #c0c0c0;
            border: 1px solid #3e3e42;
            font-size: 14px;
        }
    """)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
