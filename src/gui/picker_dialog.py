from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, 
    QPushButton, QLabel, QScrollArea, QWidget, QGridLayout, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QThreadPool, QRunnable, pyqtSlot, QObject
from PyQt6.QtGui import QPixmap, QShortcut, QKeySequence
try:
    from aqt.qt import sip
except ImportError:
    try:
        from PyQt6 import sip
    except ImportError:
        import sip
import requests
try:
    from aqt import mw
except ImportError:
    mw = None
from ..scraper import fetch_image_urls
from .widgets import ClickableImageLabel
from ..anki_utils import save_image_to_note, get_field_content, restore_field_content

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

class ImageDownloader(QThread):
    finished = pyqtSignal(bytes)
    error = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            if self.url.startswith("data:image"):
                import base64
                header, data = self.url.split(",", 1)
                image_data = base64.b64decode(data)
            else:
                response = requests.get(self.url, timeout=10)
                response.raise_for_status()
                image_data = response.content
            self.finished.emit(image_data)
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
        self.downloader = None
        self.threadpool = QThreadPool()
        self.current_note = None
        self.history = []
        self._running_threads = []
        self.setWindowTitle("Anki Image Picker")
        self.resize(800, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Top Bar: Search and Progress
        top_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.returnPressed.connect(self.start_fetching)
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.start_fetching)
        self.progress_label = QLabel()
        
        top_layout.addWidget(self.search_input)
        top_layout.addWidget(self.search_button)
        top_layout.addWidget(self.progress_label)
        layout.addLayout(top_layout)

        # Hot-swap fields row
        fields_scroll = QScrollArea()
        fields_scroll.setWidgetResizable(True)
        fields_scroll.setFixedHeight(50)
        fields_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        fields_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        fields_scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        fields_widget = QWidget()
        self.field_buttons_layout = QHBoxLayout(fields_widget)
        fields_scroll.setWidget(fields_widget)
        layout.addWidget(fields_scroll)

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
        labels = []
        for i in range(self.grid_layout.count()):
            item = self.grid_layout.itemAt(i)
            if item is None:
                continue
            
            sub_layout = item.layout()
            if sub_layout:
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
        note_data = self.notes[self.current_index]
        self.search_input.setText(note_data.get("term", ""))
        self.progress_label.setText(f"Card {self.current_index + 1} of {len(self.notes)}")
        
        self.back_button.setEnabled(len(self.history) > 0)
        self.revert_button.setEnabled(len(self.history) > 0)
        
        self.current_note = None
        if mw:
            try:
                self.current_note = mw.col.get_note(note_data["id"])
            except Exception as e:
                print(f"Error fetching note: {e}")

        self.update_field_buttons()
        self.clear_grid()
        self.start_fetching()

    def update_field_buttons(self):
        while self.field_buttons_layout.count():
            item = self.field_buttons_layout.takeAt(0)
            if item:
                widget = item.widget()
                if widget:
                    widget.deleteLater()
        
        if not self.current_note:
            return

        try:
            fields = self.current_note.keys()
            for field in fields:
                btn = QPushButton(field)
                btn.clicked.connect(lambda checked, f=field: self.on_field_clicked(f))
                self.field_buttons_layout.addWidget(btn)
        except Exception as e:
            print(f"Error getting fields: {e}")

    def on_field_clicked(self, field_name):
        if not self.current_note:
            return
        text = get_field_content(self.current_note, field_name)
        if text:
            self.search_input.setText(text)
            self.start_fetching()

    def start_fetching(self):
        query = self.search_input.text()
        if not query.strip():
            return

        # Append suffix from config if not already present in query
        note_data = self.notes[self.current_index]
        config = note_data.get("config", {})
        suffix = config.get("search_suffix", "").strip()
        
        full_query = query.strip()
        if suffix and suffix not in full_query:
            full_query += f" {suffix}"

        self.search_input.setStyleSheet("")
        self.progress_label.setText("Searching...")
        self.clear_grid()

        if mw:
            mw.taskman.run_in_background(
                lambda: fetch_image_urls(full_query),
                self.on_images_fetched
            )
        else:
            fetcher = ImageFetcher(full_query)
            self._running_threads.append(fetcher)
            fetcher.finished.connect(lambda urls: self.on_images_fetched(urls))
            fetcher.error.connect(self.on_fetch_error)
            fetcher.finished.connect(lambda: self._cleanup_thread(fetcher))
            fetcher.start()

    def on_images_fetched(self, result):
        if mw:
            try:
                urls = result.result()
            except Exception as e:
                self.on_fetch_error(str(e))
                return
        else:
            urls = result

        self.clear_grid()
        self.progress_label.setText("")
        
        if not urls:
            self.search_input.setStyleSheet("border: 2px solid red;")
            self.progress_label.setText("No results")
            return
            
        for i, url in enumerate(urls):
            label = ClickableImageLabel(url)
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

    def on_image_selected(self, url):
        self.progress_label.setText("Saving...")
        if mw:
            mw.taskman.run_in_background(
                lambda: self._download_image(url),
                self.on_image_downloaded
            )
        else:
            downloader = ImageDownloader(url)
            self._running_threads.append(downloader)
            downloader.finished.connect(self.on_image_downloaded)
            downloader.error.connect(self.on_download_error)
            downloader.finished.connect(lambda: self._cleanup_thread(downloader))
            downloader.start()

    def _download_image(self, url):
        if url.startswith("data:image"):
            import base64
            header, data = url.split(",", 1)
            return base64.b64decode(data)
        else:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.content

    def on_image_downloaded(self, result):
        if mw:
            try:
                image_data = result.result()
            except Exception as e:
                self.on_download_error(str(e))
                return
        else:
            image_data = result

        if not image_data or not isinstance(image_data, bytes):
            self.on_download_error("Invalid image data received")
            return

        note_data = self.notes[self.current_index]
        config = note_data.get("config", {})
        field_name = config.get("target_field")
        
        original_content = ""
        if self.current_note and field_name in self.current_note:
            original_content = self.current_note[field_name]
        
        success = save_image_to_note(
            note_id=note_data["id"],
            image_data=image_data,
            field_name=field_name,
            mode=config.get("mode"),
            search_term=self.search_input.text(),
            image_width=config.get("image_width"),
            max_height=config.get("max_height")
        )
        
        if success:
            self.history.append({
                "type": "save",
                "note_id": note_data["id"],
                "field_name": field_name,
                "original_content": original_content,
                "search_term": self.search_input.text()
            })
            self._navigate_forward()
        else:
            self.on_download_error("Failed to save to Anki")

    def on_download_error(self, error_msg):
        print(f"Download/Save error: {error_msg}")
        self.progress_label.setText("Error saving image")

    def on_fetch_error(self, error_msg):
        print(f"Fetch error: {error_msg}")
        self.progress_label.setText("Search failed")
        self.search_input.setStyleSheet("border: 2px solid red;")

    def _cleanup_thread(self, thread):
        if thread in self._running_threads:
            self._running_threads.remove(thread)

    def queue_thumbnail_load(self, label, url):
        worker = ThumbnailWorker(label, url)
        worker.signals.finished.connect(self.on_thumbnail_loaded)
        self.threadpool.start(worker)

    def on_thumbnail_loaded(self, label, image_data):
        if sip.isdeleted(label):
            return
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
        if not self.history:
            self.reject()
            return
        if mw:
            mw.checkpoint("Revert Images")
            mw.progress.start(max=len(self.history), label="Reverting changes...", parent=self)
        try:
            while self.history:
                last_action = self.history.pop()
                if last_action["type"] == "save":
                    success = restore_field_content(
                        last_action["note_id"], 
                        last_action["field_name"], 
                        last_action["original_content"]
                    )
                    if not success:
                        print(f"Failed to restore note {last_action['note_id']}")
                if mw:
                    mw.progress.update()
        finally:
            if mw:
                mw.progress.finish()
        self.reject()

    def clear_grid(self):
        self.threadpool.clear()
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
                sub_layout.deleteLater()
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def on_back(self):
        if not self.history:
            return
        last_action = self.history.pop()
        if last_action["type"] == "save":
            success = restore_field_content(
                last_action["note_id"], 
                last_action["field_name"], 
                last_action["original_content"]
            )
            if not success:
                print(f"Failed to restore note {last_action['note_id']}")
        self.current_index -= 1
        self.update_current_note()

    def on_skip(self):
        self.history.append({"type": "skip"})
        self._navigate_forward()

    def _navigate_forward(self):
        if self.current_index < len(self.notes) - 1:
            self.current_index += 1
            self.update_current_note()
        else:
            self.accept()

    def accept(self):
        if mw:
            mw.reset()
        super().accept()

    def reject(self):
        if mw:
            mw.reset()
        super().reject()

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
