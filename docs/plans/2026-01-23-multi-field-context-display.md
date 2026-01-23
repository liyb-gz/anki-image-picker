# Multi-Field Context Display Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Allow users to select multiple fields to be displayed in a sidebar within the Image Picker dialog, providing context when picking images.

**Architecture:**
- **Persistent Configuration**: Store `context_fields` (list of strings) in the add-on config per note type.
- **Enhanced Config UI**: Update `ConfigDialog` to use a `QListWidget` with checkable items for multi-field selection.
- **Context Extraction**: Modify `main.py` to extract cleaned content for all selected context fields for every note.
- **Sidebar UI**: Update `PickerDialog` to include a scrollable left sidebar displaying the context fields.

**Tech Stack:** Python, PyQt6, Anki API.

---

### Task 1: Multi-Select Context Fields in Config Dialog

**Files:**
- Modify: `src/gui/config_dialog.py`
- Modify: `tests/test_config_logic.py`

**Step 1: Write the failing test**

```python
def test_config_dialog_context_fields(qapp):
    from PyQt6.QtCore import Qt
    fields = ["Front", "Back", "Meaning", "Notes"]
    dialog = ConfigDialog(fields)
    
    # Simulate selecting "Meaning" and "Notes"
    items = dialog.context_list.findItems("Meaning", Qt.MatchFlag.MatchExactly)
    if items: items[0].setCheckState(Qt.CheckState.Checked)
    
    items = dialog.context_list.findItems("Notes", Qt.MatchFlag.MatchExactly)
    if items: items[0].setCheckState(Qt.CheckState.Checked)
    
    config = dialog.get_config()
    assert "Meaning" in config["context_fields"]
    assert "Notes" in config["context_fields"]
    assert "Front" not in config["context_fields"]
```

**Step 2: Run test to verify it fails**
Run: `pytest tests/test_config_logic.py`
Expected: FAIL with `AttributeError: 'ConfigDialog' object has no attribute 'context_list'`

**Step 3: Implement multi-select UI in `ConfigDialog`**
- Import `QListWidget`, `QListWidgetItem`, `QGroupBox` from `PyQt6.QtWidgets`.
- Add a `QGroupBox` labeled "Context Fields (Show in Picker)" to `init_ui`.
- Add `self.context_list = QListWidget()` inside the group box.
- Populate with checkable `QListWidgetItem`s for each field.
- Update `get_config` to return the list of checked fields.

**Step 4: Run test to verify it passes**
Run: `pytest tests/test_config_logic.py`

**Step 5: Commit**
```bash
git add src/gui/config_dialog.py tests/test_config_logic.py
git commit -m "feat: add multi-select context fields to config dialog"
```

---

### Task 2: Fetch and Pass Context Data to Picker

**Files:**
- Modify: `src/main.py`

**Step 1: Extract context content in `on_quick_image_picker`**
- Get `context_fields` from the config.
- For each note being processed:
    - Create a `context_data` dictionary.
    - Iterate over `context_fields` and use `get_field_content(nid, field)` to fetch text.
    - Store result in `context_data[field] = content`.
    - Pass `context_data` in the `notes_data` list.

**Step 2: Commit**
```bash
git add src/main.py
git commit -m "feat: fetch and pass context field data to picker"
```

---

### Task 3: Implement Sidebar UI in PickerDialog

**Files:**
- Modify: `src/gui/picker_dialog.py`

**Step 1: Update main layout to support horizontal split**
- In `init_ui`, create `content_layout = QHBoxLayout()`.
- Move the existing `self.scroll_area` (Image Grid) into this `content_layout`.
- Add `content_layout` to the main vertical `layout`.

**Step 2: Create the Sidebar**
- Initialize `self.sidebar_scroll = QScrollArea()`.
- Set width constraints: `self.sidebar_scroll.setFixedWidth(200)`.
- Set `widgetResizable(True)`.
- Create `self.sidebar_widget = QWidget()` and `self.sidebar_layout = QVBoxLayout(self.sidebar_widget)`.
- Set `self.sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)`.
- Add `self.sidebar_scroll` to the left side of `content_layout`.

**Step 3: Update `update_current_note` to populate sidebar**
- Add a helper `clear_sidebar()`.
- For each `field, content` in `note_data["context_data"]`:
    - Add a bold `QLabel` for the field name.
    - Add a `QLabel` for the content (with word wrap enabled).
    - Add spacing between fields.
- Hide sidebar if `context_data` is empty.

**Step 4: Commit**
```bash
git add src/gui/picker_dialog.py
git commit -m "feat: display context fields in picker sidebar"
```
