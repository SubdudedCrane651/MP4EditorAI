import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
)

from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget

from moviepy import VideoFileClip, AudioFileClip
from moviepy.audio.AudioClip import CompositeAudioClip


class ExportWorker(QThread):
    progress = pyqtSignal(str)
    finished_ok = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, video_file, narration_file, output_file):
        super().__init__()

        self.video_file = video_file
        self.narration_file = narration_file
        self.output_file = output_file

    def run(self):
        try:
            self.progress.emit("Loading video...")

            video = VideoFileClip(self.video_file)
            narration = AudioFileClip(self.narration_file)

            self.progress.emit("Building audio mix...")

            if video.audio:
                mixed_audio = CompositeAudioClip(
                    [video.audio, narration]
                )
            else:
                mixed_audio = narration

            final_video = video.with_audio(mixed_audio)

            self.progress.emit("Exporting MP4...")

            final_video.write_videofile(
                self.output_file,
                codec="libx264",
                audio_codec="aac"
            )

            video.close()
            narration.close()

            self.finished_ok.emit(self.output_file)

        except Exception as e:
            self.failed.emit(str(e))


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("MP4 Narration Editor")
        self.resize(1000, 700)

        self.worker = None

        self.video_file = ""
        self.narration_file = ""
        self.output_file = ""

        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()

        self.player.setAudioOutput(self.audio_output)

        self.build_ui()

    def build_ui(self):

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout()

        self.video_widget = QVideoWidget()
        self.player.setVideoOutput(self.video_widget)

        layout.addWidget(self.video_widget, 1)

        # Video file
        row1 = QHBoxLayout()

        self.video_edit = QLineEdit()
        self.video_edit.setReadOnly(True)

        btn_video = QPushButton("Select MP4")
        btn_video.clicked.connect(self.select_video)

        row1.addWidget(QLabel("Video"))
        row1.addWidget(self.video_edit)
        row1.addWidget(btn_video)

        layout.addLayout(row1)

        # Narration
        row2 = QHBoxLayout()

        self.narration_edit = QLineEdit()
        self.narration_edit.setReadOnly(True)

        btn_narration = QPushButton("Select Narration")
        btn_narration.clicked.connect(self.select_narration)

        row2.addWidget(QLabel("Narration"))
        row2.addWidget(self.narration_edit)
        row2.addWidget(btn_narration)

        layout.addLayout(row2)

        # Output
        row3 = QHBoxLayout()

        self.output_edit = QLineEdit()
        self.output_edit.setReadOnly(True)

        btn_output = QPushButton("Output MP4")
        btn_output.clicked.connect(self.select_output)

        row3.addWidget(QLabel("Output"))
        row3.addWidget(self.output_edit)
        row3.addWidget(btn_output)

        layout.addLayout(row3)

        # Controls
        controls = QHBoxLayout()

        self.btn_preview = QPushButton("Preview Video")
        self.btn_preview.clicked.connect(self.preview_video)

        self.btn_export = QPushButton("Export MP4")
        self.btn_export.clicked.connect(self.export_video)

        controls.addWidget(self.btn_preview)
        controls.addWidget(self.btn_export)

        layout.addLayout(controls)

        self.status_label = QLabel("Ready")

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()

        layout.addWidget(self.status_label)
        layout.addWidget(self.progress)

        central.setLayout(layout)

    def select_video(self):

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select MP4",
            "",
            "Video Files (*.mp4 *.mkv *.avi)"
        )

        if filename:
            self.video_file = filename
            self.video_edit.setText(filename)

    def select_narration(self):

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select Narration",
            "",
            "Audio Files (*.wav *.mp3)"
        )

        if filename:
            self.narration_file = filename
            self.narration_edit.setText(filename)

    def select_output(self):

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save MP4",
            str(Path.home() / "output.mp4"),
            "MP4 Files (*.mp4)"
        )

        if filename:
            self.output_file = filename
            self.output_edit.setText(filename)

    def preview_video(self):

        if not self.video_file:
            QMessageBox.warning(
                self,
                "Warning",
                "Select a video first."
            )
            return

        self.player.setSource(
            QUrl.fromLocalFile(self.video_file)
        )

        self.player.play()

    def export_video(self):

        if not self.video_file:
            QMessageBox.warning(
                self,
                "Warning",
                "Select an MP4 file."
            )
            return

        if not self.narration_file:
            QMessageBox.warning(
                self,
                "Warning",
                "Select narration audio."
            )
            return

        if not self.output_file:
            QMessageBox.warning(
                self,
                "Warning",
                "Select output location."
            )
            return

        self.progress.show()

        self.worker = ExportWorker(
            self.video_file,
            self.narration_file,
            self.output_file
        )

        self.worker.progress.connect(
            self.status_label.setText
        )

        self.worker.finished_ok.connect(
            self.export_finished
        )

        self.worker.failed.connect(
            self.export_failed
        )

        self.worker.start()

    def export_finished(self, filename):

        self.progress.hide()

        self.status_label.setText("Finished")

        QMessageBox.information(
            self,
            "Success",
            f"Saved:\n{filename}"
        )

    def export_failed(self, error):

        self.progress.hide()

        QMessageBox.critical(
            self,
            "Error",
            error
        )


if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())