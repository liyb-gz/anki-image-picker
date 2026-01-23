from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, 
    QPushButton, QLabel, QScrollArea, QWidget, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QThreadPool, QRunnable, pyqtSlot, QObject
from PyQt6.QtGui import QPixmap, QShortcut, QKeySequence
import requests
from src.scraper import fetch_image_urls
from src.gui.widgets import ClickableImageLabel

class ImageFetcher(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, query):
        super().__init__()
        self.query = query

    def run(self):
        try:
            urls = fetch_image_urls(self.query)
            self.finished.emit(urls)
        except Exception as e:
            self.error.emit(str(e))

class WorkerSignals(QObject):
    finished = pyqtSignal(object, bytes)

class ThumbnailWorker(QRunnable):
    def __init__(self, label, url):
        super().__init__()
        self.label = label
        self.url = url
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            if self.url.startswith("data:image"):
                import base64
                header, data = self.url.split(",", 1)
                image_data = base64.b64decode(data)
            else:
                response = requests.get(self.url, timeout=5)
                response.raise_for_status()
                image_data = response.content
            self.signals.finished.emit(self.label, image_data)
        except Exception:
            self.signals.finished.emit(self.label, b"")

class PickerDialog(QDialog):
    def __init__(self, notes, parent=None):
        super().__init__(parent)
        self.notes = notes
        self.current_index = 0
        self.fetcher = None
        self.threadpool = QThreadPool()
        self.setWindowTitle("Anki Image Picker")
        self.resize(800, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Top Bar: Search and Progress
        top_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.start_fetching)
        self.progress_label = QLabel()
        
        top_layout.addWidget(self.search_input)
        top_layout.addWidget(self.search_button)
        top_layout.addWidget(self.progress_label)
        layout.addLayout(top_layout)

        # Image Grid Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.scroll_area.setWidget(self.grid_widget)
        layout.addWidget(self.scroll_area)

        # Footer Buttons
        footer_layout = QHBoxLayout()
        self.back_button = QPushButton("Back")
        self.skip_button = QPushButton("Skip")
        self.abort_button = QPushButton("Abort")
        self.revert_button = QPushButton("Revert")
        
        self.back_button.clicked.connect(self.on_back)
        self.skip_button.clicked.connect(self.on_skip)
        self.abort_button.clicked.connect(self.reject)
        self.revert_button.clicked.connect(self.on_revert)
        
        footer_layout.addWidget(self.back_button)
        footer_layout.addStretch()
        footer_layout.addWidget(self.skip_button)
        footer_layout.addWidget(self.revert_button)
        footer_layout.addWidget(self.abort_button)
        layout.addLayout(footer_layout)

        # Keyboard Shortcuts
        for i in range(1, 9):
            shortcut = QShortcut(QKeySequence(str(i)), self)
            shortcut.activated.connect(lambda idx=i-1: self.select_by_index(idx))

        self.update_current_note()

    def select_by_index(self, index):
        # Logic to find the widget at index and trigger its selection
        labels = []
        for i in range(self.grid_layout.count()):
            item = self.grid_layout.itemAt(i)
            if item is None:
                continue
            
            # Check if it's the container layout (for first 8 images)
            sub_layout = item.layout()
            if sub_layout:
                # The label is the first item in the container layout
                child = sub_layout.itemAt(0)
                if child:
                    w = child.widget()
                    if isinstance(w, ClickableImageLabel):
                        labels.append(w)
            else:
                w = item.widget()
                if isinstance(w, ClickableImageLabel):
                    labels.append(w)
        
        if 0 <= index < len(labels):
            self.on_image_selected(labels[index].url)

    def update_current_note(self):
        if not self.notes:
            return
        note = self.notes[self.current_index]
        self.search_input.setText(note.get("term", ""))
        self.progress_label.setText(f"Card {self.current_index + 1} of {len(self.notes)}")
        self.back_button.setEnabled(self.current_index > 0)
        self.clear_grid()
        self.start_fetching()

    def start_fetching(self):
        query = self.search_input.text()
        if self.fetcher and self.fetcher.isRunning():
            self.fetcher.terminate()
            self.fetcher.wait()
        
        self.fetcher = ImageFetcher(query)
        self.fetcher.finished.connect(self.on_images_fetched)
        self.fetcher.start()

    def on_images_fetched(self, urls):
        self.clear_grid()
        for i, url in enumerate(urls):
            label = ClickableImageLabel(url)
            # Shortcut visual aid
            if i < 8:
                container = QVBoxLayout()
                container.addWidget(label)
                shortcut_label = QLabel(f"[{i+1}]")
                shortcut_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                container.addWidget(shortcut_label)
                self.grid_layout.addLayout(container, i // 4, i % 4)
            else:
                self.grid_layout.addWidget(label, i // 4, i % 4)
            
            label.clicked.connect(self.on_image_selected)
            self.queue_thumbnail_load(label, url)

    def queue_thumbnail_load(self, label, url):
        worker = ThumbnailWorker(label, url)
        worker.signals.finished.connect(self.on_thumbnail_loaded)
        self.threadpool.start(worker)

    def on_thumbnail_loaded(self, label, image_data):
        if not image_data:
            label.setText("Error")
            return
        
        pixmap = QPixmap()
        pixmap.loadFromData(image_data)
        if not pixmap.isNull():
            label.setPixmap(pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio))
        else:
            label.setText("Invalid Image")

    def on_revert(self):
        self.reject()

    def clear_grid(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item is None:
                continue
            
            sub_layout = item.layout()
            if sub_layout:
                while sub_layout.count():
                    child = sub_layout.takeAt(0)
                    if child:
                        w = child.widget()
                        if w:
                            w.deleteLater()
            
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def on_back(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.update_current_note()

    def on_skip(self):
        if self.current_index < len(self.notes) - 1:
            self.current_index += 1
            self.update_current_note()
        else:
            self.accept()

    def on_image_selected(self, url):
        print(f"Selected: {url}")
        # Logic to save and go to next will be in next task
        self.on_skip()

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    notes = [
        {"id": 1, "term": "Golden Retriever"},
        {"id": 2, "term": "Siamese Cat"},
        {"id": 3, "term": "Red Fox"}
    ]
    dialog = PickerDialog(notes)
    dialog.show()
    sys.exit(app.exec())

