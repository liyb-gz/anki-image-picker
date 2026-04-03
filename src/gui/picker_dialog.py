from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, 
    QPushButton, QLabel, QScrollArea, QWidget, QGridLayout, QFrame,
    QComboBox
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
    finished = pyqtSignal(list, int)
    error = pyqtSignal(str, int)

    def __init__(self, query, limit=8, start_index=0, provider="bing", api_key="", request_id=0):
        super().__init__()
        self.query = query
        self.limit = limit
        self.start_index = start_index
        self.provider = provider
        self.api_key = api_key
        self.request_id = request_id

    def run(self):
        try:
            urls = fetch_image_urls(self.query, limit=self.limit, start=self.start_index, provider=self.provider, api_key=self.api_key)
            self.finished.emit(urls, self.request_id)
        except Exception as e:
            self.error.emit(str(e), self.request_id)

class ImageDownloader(QThread):
    finished = pyqtSignal(bytes)
    error = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def run(self):
        try:
            if self.url.startswith("data:image"):
                import base64
                header, data = self.url.split(",", 1)
                image_data = base64.b64decode(data)
            else:
                response = requests.get(self.url, headers=self.headers, timeout=10)
                response.raise_for_status()
                image_data = response.content
            self.finished.emit(image_data)
        except Exception as e:
            self.error.emit(str(e))


class WorkerSignals(QObject):
    finished = pyqtSignal(object, bytes, str, str)

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
                content_type = header.split(";")[0].split(":")[1]
            else:
                # Build headers with Referer to bypass hotlink protection
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                }
                # Add Referer based on URL domain
                from urllib.parse import urlparse
                parsed = urlparse(self.url)
                headers["Referer"] = f"{parsed.scheme}://{parsed.netloc}/"
                
                response = requests.get(self.url, headers=headers, timeout=8, allow_redirects=True)
                response.raise_for_status()
                image_data = response.content
                content_type = response.headers.get('Content-Type', 'unknown')
                
                # Early check: if Content-Type is clearly not an image, skip
                if content_type and 'text/html' in content_type.lower():
                    self.signals.finished.emit(self.label, b"", "text/html", self.url)
                    return
                    
            self.signals.finished.emit(self.label, image_data, content_type, self.url)
        except Exception:
            self.signals.finished.emit(self.label, b"", "error", self.url)

class PickerDialog(QDialog):
    def __init__(self, notes, preferred_provider="bing", api_keys=None, parent=None):
        super().__init__(parent)
        self.notes = notes
        self.preferred_provider = preferred_provider
        self.api_keys = api_keys or {}
        self.current_index = 0
        self.current_offset = 0
        self.seen_urls = set()
        self._api_cache = []
        self.fetcher = None
        self.downloader = None
        self.threadpool = QThreadPool()
        self.current_note = None
        self.history = []
        self._running_threads = []
        self._current_request_id = 0
        self.setWindowTitle("Anki Image Picker")
        self.resize(1100, 750)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Top Bar: Search, Suffix and Progress
        top_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.returnPressed.connect(self.start_fetching)
        self.suffix_input = QLineEdit()
        self.suffix_input.setPlaceholderText("Suffix...")
        self.suffix_input.setFixedWidth(100)
        self.suffix_input.returnPressed.connect(self.start_fetching)
        
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.start_fetching)
        
        from ..scraper import PROVIDER_DISPLAY_NAMES
        self.provider_combo = QComboBox()
        provider_ids = ["bing", "duckduckgo"]
        if self.api_keys.get("serpapi_key"):
            provider_ids.append("serpapi")
        if self.api_keys.get("serper_key"):
            provider_ids.append("serper")
        for pid in provider_ids:
            self.provider_combo.addItem(PROVIDER_DISPLAY_NAMES.get(pid, pid), pid)
        self.provider_combo.currentIndexChanged.connect(self.on_provider_changed)
        
        self.progress_label = QLabel()
        self.status_label = QLabel()
        
        top_layout.addWidget(self.search_input)
        top_layout.addWidget(self.suffix_input)
        top_layout.addWidget(self.provider_combo)
        top_layout.addWidget(self.search_button)
        top_layout.addWidget(self.progress_label)
        top_layout.addWidget(self.status_label)
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
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.grid_widget)

        # Content area with Sidebar
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        
        # Sidebar for context data
        self.sidebar_scroll = QScrollArea()
        self.sidebar_scroll.setFixedWidth(200)
        self.sidebar_scroll.setWidgetResizable(True)
        self.sidebar_widget = QWidget()
        self.sidebar_layout = QVBoxLayout(self.sidebar_widget)
        self.sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.sidebar_scroll.setWidget(self.sidebar_widget)
        
        content_layout.addWidget(self.sidebar_scroll)
        content_layout.addWidget(self.scroll_area)
        layout.addWidget(content_widget)

        # Footer Buttons
        footer_layout = QHBoxLayout()
        self.back_button = QPushButton("Back")
        self.load_more_button = QPushButton("Load More")
        self.skip_button = QPushButton("Skip")
        self.abort_button = QPushButton("Abort")
        self.revert_button = QPushButton("Revert")
        
        self.back_button.clicked.connect(self.on_back)
        self.load_more_button.clicked.connect(self.on_load_more)
        self.skip_button.clicked.connect(self.on_skip)
        self.abort_button.clicked.connect(self.reject)
        self.revert_button.clicked.connect(self.on_revert)
        
        footer_layout.addWidget(self.back_button)
        footer_layout.addStretch()
        footer_layout.addWidget(self.load_more_button)
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
        
        config = note_data.get("config", {})
        self.suffix_input.setText(config.get("search_suffix", ""))
        
        provider = config.get("preferred_provider", self.preferred_provider)
        self.provider_combo.blockSignals(True)
        idx = self.provider_combo.findData(provider)
        if idx >= 0:
            self.provider_combo.setCurrentIndex(idx)
        self.provider_combo.blockSignals(False)
        
        self.progress_label.setText(f"Card {self.current_index + 1} of {len(self.notes)}")
        
        self.back_button.setEnabled(len(self.history) > 0)
        self.revert_button.setEnabled(len(self.history) > 0)
        
        self.current_note = None
        if mw:
            try:
                self.current_note = mw.col.get_note(note_data["id"])
            except Exception as e:
                print(f"Error fetching note: {e}")

        # Update Sidebar
        self.clear_sidebar()
        context_data = note_data.get("context_data", {})
        if not context_data:
            self.sidebar_scroll.hide()
        else:
            self.sidebar_scroll.show()
            for field, content in context_data.items():
                label = QLabel(f"<b>{field}</b>")
                content_label = QLabel(content)
                content_label.setWordWrap(True)
                self.sidebar_layout.addWidget(label)
                self.sidebar_layout.addWidget(content_label)
                self.sidebar_layout.addSpacing(10)

        self.update_field_buttons()
        self.start_fetching()

    def clear_sidebar(self):
        while self.sidebar_layout.count():
            item = self.sidebar_layout.takeAt(0)
            if item:
                widget = item.widget()
                if widget:
                    widget.deleteLater()

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

    def on_provider_changed(self, index):
        provider_id = self.provider_combo.currentData()
        if not provider_id:
            return
        self.preferred_provider = provider_id
        if self.notes and self.current_index < len(self.notes):
            config = self.notes[self.current_index].get("config", {})
            config["preferred_provider"] = provider_id
        self.start_fetching()

    def start_fetching(self):
        self._current_request_id += 1
        self.current_offset = 0
        self.seen_urls = set()
        self._api_cache = []
        self.clear_grid()
        self._fetch_images()

    def on_load_more(self):
        # Jump by the number of results we currently have to get the next page
        # Using the actual grid count ensures we don't skip results
        count = self.grid_layout.count()
        if count > 0:
            self.current_offset = count
        else:
            self.current_offset += 12
        self._fetch_images()

    def _is_api_provider(self, provider=None):
        if provider is None:
            provider = self.provider_combo.currentData()
        return provider in ("serpapi", "serper")

    def _fetch_images(self):
        query = self.search_input.text()
        suffix = self.suffix_input.text().strip()
        
        if self.notes and self.current_index < len(self.notes):
            config = self.notes[self.current_index].get("config", {})
            config["search_suffix"] = suffix

        if not query.strip():
            return

        full_query = query.strip()
        if suffix and suffix.lower() not in full_query.lower():
            full_query += f" {suffix}"

        provider = self.provider_combo.currentData()
        request_id = self._current_request_id
        is_api = self._is_api_provider(provider)

        api_key = ""
        if provider == "serpapi":
            api_key = self.api_keys.get("serpapi_key", "")
        elif provider == "serper":
            api_key = self.api_keys.get("serper_key", "")

        # For API providers, serve from cache if available
        if is_api and self.current_offset < len(self._api_cache):
            page = self._api_cache[self.current_offset:self.current_offset + 12]
            self._display_urls(page)
            return

        self.search_input.setStyleSheet("")
        self.status_label.setText("Searching...")

        # API providers: fetch large batch; scraping providers: fetch one page
        fetch_limit = 100 if is_api else 12
        fetch_start = len(self._api_cache) if is_api else self.current_offset

        if mw:
            mw.taskman.run_in_background(
                lambda: fetch_image_urls(full_query, limit=fetch_limit, start=fetch_start, provider=provider, api_key=api_key),
                lambda res: self.on_images_fetched(res, request_id)
            )
        else:
            fetcher = ImageFetcher(full_query, limit=fetch_limit, start_index=fetch_start, provider=provider, api_key=api_key, request_id=request_id)
            self._running_threads.append(fetcher)
            fetcher.finished.connect(self.on_images_fetched)
            fetcher.error.connect(self.on_fetch_error)
            fetcher.finished.connect(lambda: self._cleanup_thread(fetcher))
            fetcher.start()

    def on_images_fetched(self, result, request_id=None):
        if request_id is not None and request_id != self._current_request_id:
            return

        if mw:
            try:
                urls = result.result()
            except Exception as e:
                self.on_fetch_error(str(e), request_id)
                return
        else:
            urls = result

        self.status_label.setText("")

        if self._is_api_provider():
            self._api_cache.extend(urls)
            page = self._api_cache[self.current_offset:self.current_offset + 12]
            self._display_urls(page)
        else:
            self._display_urls(urls)

    def _display_urls(self, urls):
        new_urls = [u for u in urls if u not in self.seen_urls]
        for u in new_urls:
            self.seen_urls.add(u)

        if not new_urls:
            if self.current_offset == 0:
                self.search_input.setStyleSheet("border: 2px solid red;")
                self.status_label.setText("No results")
            else:
                self.status_label.setText("No more results")
            return
            
        current_count = self.grid_layout.count()
        for i, url in enumerate(new_urls):
            total_idx = current_count + i
            label = ClickableImageLabel(url)
            if total_idx < 8:
                container = QVBoxLayout()
                container.addWidget(label)
                shortcut_label = QLabel(f"[{total_idx+1}]")
                shortcut_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                container.addWidget(shortcut_label)
                self.grid_layout.addLayout(container, total_idx // 4, total_idx % 4)
            else:
                self.grid_layout.addWidget(label, total_idx // 4, total_idx % 4)
            
            label.clicked.connect(self.on_image_selected)
            self.queue_thumbnail_load(label, url)

    def on_image_selected(self, url):
        self.status_label.setText("Saving...")
        note_id = self.notes[self.current_index]["id"]
        if mw:
            mw.taskman.run_in_background(
                lambda: self._download_image(url),
                lambda res: self.on_image_downloaded(res, note_id)
            )
        else:
            downloader = ImageDownloader(url)
            self._running_threads.append(downloader)
            downloader.finished.connect(lambda data: self.on_image_downloaded(data, note_id))
            downloader.error.connect(self.on_download_error)
            downloader.finished.connect(lambda: self._cleanup_thread(downloader))
            downloader.start()

    def _download_image(self, url):
        if url.startswith("data:image"):
            import base64
            header, data = url.split(",", 1)
            return base64.b64decode(data)
        else:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.content

    def on_image_downloaded(self, result, note_id):
        # Ensure we are still on the same note that triggered the download
        if not self.notes or self.notes[self.current_index]["id"] != note_id:
            print("Ignoring download result: note changed")
            return

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
            max_width=config.get("max_width"),
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
        self.status_label.setText("Error saving image")

    def on_fetch_error(self, error_msg, request_id=None):
        if request_id is not None and request_id != self._current_request_id:
            return
        print(f"Fetch error: {error_msg}")
        self.status_label.setText("Search failed")
        self.search_input.setStyleSheet("border: 2px solid red;")

    def _cleanup_thread(self, thread):
        if thread in self._running_threads:
            self._running_threads.remove(thread)

    def queue_thumbnail_load(self, label, url):
        worker = ThumbnailWorker(label, url)
        worker.signals.finished.connect(self.on_thumbnail_loaded)
        self.threadpool.start(worker)

    def on_thumbnail_loaded(self, label, image_data, content_type, url):
        if sip.isdeleted(label):
            return
        if not image_data:
            # Show a less alarming message for common failures
            label.setText("...")
            label.setToolTip(f"Failed to load: {url}")
            return
            
        # Basic check to skip non-image content that returned 200 OK
        if content_type and 'text/html' in content_type.lower():
            label.setText("...")
            label.setToolTip(f"Server returned HTML instead of image")
            return
            
        # Additional check on raw bytes for HTML that might have wrong Content-Type
        if image_data.startswith(b'<!DOCTYPE') or image_data.startswith(b'<html') or image_data.startswith(b'<HTML'):
            label.setText("...")
            label.setToolTip(f"Server returned HTML instead of image")
            return

        pixmap = QPixmap()
        pixmap.loadFromData(image_data)
        if not pixmap.isNull():
            label.setPixmap(pixmap.scaledToWidth(150, Qt.TransformationMode.SmoothTransformation))
        else:
            # If QPixmap failed, try PIL as a fallback (it's better at some formats like WebP or CMYK JPEGs)
            try:
                from PIL import Image
                import io
                image = Image.open(io.BytesIO(image_data))
                # Convert to RGBA and then to QImage
                if image.mode != "RGBA":
                    image = image.convert("RGBA")
                data = image.tobytes("raw", "RGBA")
                from PyQt6.QtGui import QImage
                qimage = QImage(data, image.size[0], image.size[1], QImage.Format.Format_RGBA8888)
                pixmap = QPixmap.fromImage(qimage)
                if not pixmap.isNull():
                    label.setPixmap(pixmap.scaledToWidth(150, Qt.TransformationMode.SmoothTransformation))
                    return
            except Exception:
                pass
            
            # Final fallback - show placeholder
            label.setText("...")
            label.setToolTip(f"Unsupported format: {content_type}")

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
