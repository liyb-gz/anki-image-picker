# Picker Dialog Improvements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Improve resource efficiency and UI robustness of the `PickerDialog`.

**Architecture:** 
- Enhance `clear_grid` with threadpool and layout cleanup.
- Refactor `field_buttons_layout` to use a `QScrollArea`.
- Add caching for the Anki `Note` object to reduce redundant database calls.

**Tech Stack:** PyQt6

### Task 1: Threadpool and Layout Cleanup in `clear_grid`

**Files:**
- Modify: `src/gui/picker_dialog.py:272-290`

**Step 1: Update `clear_grid` implementation**

```python
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
```

**Step 2: Commit**

```bash
git add src/gui/picker_dialog.py
git commit -m "fix: improve cleanup in clear_grid by clearing threadpool and deleting sub-layouts"
```

### Task 2: Layout Overflow for Field Buttons

**Files:**
- Modify: `src/gui/picker_dialog.py:107-109`

**Step 1: Wrap `field_buttons_layout` in a `QScrollArea`**

Replace:
```python
        # Hot-swap fields row
        self.field_buttons_layout = QHBoxLayout()
        layout.addLayout(self.field_buttons_layout)
```
With:
```python
        # Hot-swap fields row
        fields_scroll = QScrollArea()
        fields_scroll.setWidgetResizable(True)
        fields_scroll.setFixedHeight(50)  # Approximate height for one row of buttons
        fields_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        fields_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        fields_scroll.setFrameShape(QScrollArea.FrameShape.NoFrame)
        
        fields_widget = QWidget()
        self.field_buttons_layout = QHBoxLayout(fields_widget)
        fields_scroll.setWidget(fields_widget)
        layout.addWidget(fields_scroll)
```

**Step 2: Commit**

```bash
git add src/gui/picker_dialog.py
git commit -m "feat: wrap field buttons in a scroll area to prevent dialog overflow"
```

### Task 3: Optimization - Cache Note Object

**Files:**
- Modify: `src/gui/picker_dialog.py`
- Modify: `src/anki_utils.py`

**Step 1: Update `get_field_content` in `src/anki_utils.py` to accept note object**

```python
def get_field_content(note_or_id, field_name):
    """
    Returns the cleaned text content of a field from a note ID or Note object.
    Cleans HTML tags and Cloze markers.
    """
    from aqt import mw
    if isinstance(note_or_id, (int, str)):
        try:
            note = mw.col.get_note(note_or_id)
        except Exception:
            return ""
    else:
        note = note_or_id
        
    try:
        content = note[field_name]
    except (KeyError, TypeError):
        return ""

    # Clean HTML
    soup = BeautifulSoup(content, "html.parser")
    text = soup.get_text()

    # Clean Cloze markers {{c1::text}} or {{c1::text::hint}} -> text
    text = re.sub(r"\{\{c\d+::(.*?)(?::.*?)?\}\}", r"\1", text)
    # Clean other brackets just in case
    text = text.replace("{{", "").replace("}}", "")
    
    return text.strip()
```

**Step 2: Initialize `self.current_note = None` in `PickerDialog.__init__`**

In `src/gui/picker_dialog.py`, around line 86.

**Step 3: Update `update_current_note` to fetch and cache the note**

Modify `update_current_note` (around line 170):
```python
    def update_current_note(self):
        if not self.notes:
            return
        note_data = self.notes[self.current_index]
        self.search_input.setText(note_data.get("term", ""))
        self.progress_label.setText(f"Card {self.current_index + 1} of {len(self.notes)}")
        self.back_button.setEnabled(self.current_index > 0)
        
        self.current_note = None
        if mw:
            try:
                self.current_note = mw.col.get_note(note_data["id"])
            except Exception as e:
                print(f"Error fetching note: {e}")

        self.update_field_buttons()
        
        self.clear_grid()
        self.start_fetching()
```

**Step 4: Update `update_field_buttons` to use cached note**

Modify `update_field_buttons` (around line 183):
```python
    def update_field_buttons(self):
        # Clear existing buttons
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
```

**Step 5: Update `on_field_clicked` to use cached note**

Modify `on_field_clicked` (around line 205):
```python
    def on_field_clicked(self, field_name):
        if not self.current_note:
            return
        text = get_field_content(self.current_note, field_name)
        if text:
            self.search_input.setText(text)
            self.start_fetching()
```

**Step 6: Commit**

```bash
git add src/gui/picker_dialog.py src/anki_utils.py
git commit -m "perf: cache note object to avoid redundant database fetches"
```

**Step 3: Update `update_field_buttons` to use cached note**

Modify `update_field_buttons` (around line 183):
```python
    def update_field_buttons(self):
        # Clear existing buttons
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
```

**Step 4: Update `on_field_clicked` to use cached note**

Modify `on_field_clicked` (around line 205):
```python
    def on_field_clicked(self, field_name):
        if not self.current_note:
            return
        
        text = self.current_note[field_name]
        if text:
            # Strip HTML if present (simple regex or BeautifulSoup would be better, 
            # but get_field_content might have been doing something similar)
            import re
            clean_text = re.sub('<[^<]+?>', '', text)
            self.search_input.setText(clean_text)
            self.start_fetching()
```
*Note: I should check what `get_field_content` does.*

**Step 5: Check `src/anki_utils.py` for `get_field_content` implementation**

**Step 6: Commit**

```bash
git add src/gui/picker_dialog.py
git commit -m "perf: cache note object to avoid redundant database fetches"
```
