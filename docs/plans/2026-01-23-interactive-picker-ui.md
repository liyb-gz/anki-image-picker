# Interactive Picker UI - Basic Grid Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the main interactive image selection dialog with a grid of thumbnails and navigation controls.

**Architecture:** `PickerDialog` will manage a list of notes. For each note, it triggers `scraper.fetch_image_urls` in a separate thread to avoid UI freezing. A custom `ClickableImageLabel` widget will handle image selection and visual feedback.

**Tech Stack:** PyQt6, requests, BeautifulSoup4 (via scraper.py)

### Task 1: Create Custom Widgets

**Files:**
- Create: `src/gui/widgets.py`
- Test: `tests/gui/test_widgets.py`

**Step 1: Write the failing test for ClickableImageLabel**

```python
import pytest
from PyQt6.QtWidgets import QApplication
from src.gui.widgets import ClickableImageLabel

@pytest.fixture
def app():
    return QApplication.instance() or QApplication([])

def test_clickable_image_label_emits_clicked(app):
    label = ClickableImageLabel("http://example.com/image.jpg")
    clicked_url = None
    def on_clicked(url):
        nonlocal clicked_url
        clicked_url = url
    
    label.clicked.connect(on_clicked)
    # Simulate mouse press
    label.mousePressEvent(None)
    assert clicked_url == "http://example.com/image.jpg"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/gui/test_widgets.py -v`
Expected: FAIL (ModuleNotFoundError)

**Step 3: Write minimal implementation in widgets.py**

```python
from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import pyqtSignal

class ClickableImageLabel(QLabel):
    clicked = pyqtSignal(str)

    def __init__(self, url, parent=None):
        super().__init__(parent)
        self.url = url
        self.setCursor(self.cursor().shape().PointingHandCursor)
        self.setScaledContents(True)
        self.setFixedSize(150, 150)
        self.setStyleSheet("border: 2px solid transparent;")

    def mousePressEvent(self, event):
        self.clicked.emit(self.url)

    def set_selected(self, selected):
        if selected:
            self.setStyleSheet("border: 2px solid blue;")
        else:
            self.setStyleSheet("border: 2px solid transparent;")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/gui/test_widgets.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/gui/widgets.py tests/gui/test_widgets.py
git commit -m "feat: add ClickableImageLabel widget"
```

### Task 2: Create PickerDialog Layout

**Files:**
- Create: `src/gui/picker_dialog.py`
- Test: `tests/gui/test_picker_dialog.py`

**Step 1: Write the failing test for PickerDialog layout**

```python
import pytest
from PyQt6.QtWidgets import QApplication
from src.gui.picker_dialog import PickerDialog

@pytest.fixture
def app():
    return QApplication.instance() or QApplication([])

def test_picker_dialog_initial_state(app):
    notes = [{"id": 1, "term": "apple"}, {"id": 2, "term": "banana"}]
    dialog = PickerDialog(notes)
    assert dialog.search_input.text() == "apple"
    assert "1 of 2" in dialog.progress_label.text()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/gui/test_picker_dialog.py -v`
Expected: FAIL (ModuleNotFoundError)

**Step 3: Write initial implementation of PickerDialog**

```python
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, 
    QPushButton, QLabel, QScrollArea, QWidget, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal

class PickerDialog(QDialog):
    def __init__(self, notes, parent=None):
        super().__init__(parent)
        self.notes = notes
        self.current_index = 0
        self.setWindowTitle("Anki Image Picker")
        self.resize(800, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Top Bar: Search and Progress
        top_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_button = QPushButton("Search")
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
        
        footer_layout.addWidget(self.back_button)
        footer_layout.addStretch()
        footer_layout.addWidget(self.skip_button)
        footer_layout.addWidget(self.revert_button)
        footer_layout.addWidget(self.abort_button)
        layout.addLayout(footer_layout)

        self.update_current_note()

    def update_current_note(self):
        note = self.notes[self.current_index]
        self.search_input.setText(note.get("term", ""))
        self.progress_label.setText(f"Card {self.current_index + 1} of {len(self.notes)}")
        self.back_button.setEnabled(self.current_index > 0)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/gui/test_picker_dialog.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/gui/picker_dialog.py tests/gui/test_picker_dialog.py
git commit -m "feat: implement PickerDialog basic layout"
```

### Task 3: Implement Image Fetching and Grid Population

**Files:**
- Modify: `src/gui/picker_dialog.py`

**Step 1: Implement ImageFetcher thread**

```python
from PyQt6.QtCore import QThread, pyqtSignal
from src.scraper import fetch_image_urls

class ImageFetcher(QThread):
    finished = pyqtSignal(list)

    def __init__(self, query):
        super().__init__()
        self.query = query

    def run(self):
        urls = fetch_image_urls(self.query)
        self.finished.emit(urls)
```

**Step 2: Connect Search and Update logic**

In `PickerDialog`, add methods to start fetching and populate the grid.

```python
from src.gui.widgets import ClickableImageLabel
import requests
from PyQt6.QtGui import QPixmap

    # Inside PickerDialog
    def update_current_note(self):
        # ... existing ...
        self.clear_grid()
        self.start_fetching()

    def start_fetching(self):
        query = self.search_input.text()
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
                container.addWidget(QLabel(f"[{i+1}]", alignment=Qt.AlignmentFlag.AlignCenter))
                self.grid_layout.addLayout(container, i // 4, i % 4)
            else:
                self.grid_layout.addWidget(label, i // 4, i % 4)
            
            label.clicked.connect(self.on_image_selected)
            self.load_thumbnail(label, url)

    def load_thumbnail(self, label, url):
        # In a real app, use QNetworkAccessManager or another thread
        # For simplicity in this task, we can do it here or assume a helper
        try:
            # Simple sync load for now, can be improved
            data = requests.get(url, timeout=5).content
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            label.setPixmap(pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio))
        except:
            label.setText("Failed to load")

    def clear_grid(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.layout():
                # clear sub-layout
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
            if item.widget():
                item.widget().deleteLater()
```

**Step 3: Commit**

```bash
git add src/gui/picker_dialog.py
git commit -m "feat: implement image fetching and grid population"
```

### Task 4: Navigation Logic and Shortcuts

**Files:**
- Modify: `src/gui/picker_dialog.py`

**Step 1: Implement Navigation methods**

```python
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
```

**Step 2: Add Keyboard Shortcuts**

```python
from PyQt6.QtGui import QShortcut, QKeySequence

    # Inside init_ui
    for i in range(1, 9):
        shortcut = QShortcut(QKeySequence(str(i)), self)
        shortcut.activated.connect(lambda idx=i-1: self.select_by_index(idx))

    def select_by_index(self, index):
        # Logic to find the widget at index and trigger its selection
        # Simplified:
        items = []
        for i in range(self.grid_layout.count()):
            item = self.grid_layout.itemAt(i)
            # If it's the container layout
            if item.layout():
                label = item.layout().itemAt(0).widget()
                if isinstance(label, ClickableImageLabel):
                    items.append(label)
            elif item.widget() and isinstance(item.widget(), ClickableImageLabel):
                items.append(item.widget())
        
        if 0 <= index < len(items):
            self.on_image_selected(items[index].url)
```

**Step 3: Commit**

```bash
git add src/gui/picker_dialog.py
git commit -m "feat: implement navigation and keyboard shortcuts"
```

### Task 5: Final Review and Manual Test

**Step 1: Run all tests**

Run: `pytest tests/gui/`
Expected: PASS

**Step 2: Create a small runner to verify UI**

```python
# src/gui/picker_dialog.py at the end
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
```

**Step 3: Run the runner**

Run: `python src/gui/picker_dialog.py`
Expected: Window opens, loads images for "Golden Retriever", allows skipping/back.

**Step 4: Commit**

```bash
git add src/gui/picker_dialog.py
git commit -m "test: add manual test runner to picker_dialog.py"
```
