# Session Management (Back/Undo/Revert) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the ability to go back to previous notes (undoing changes if necessary) and revert all changes made during the session.

**Architecture:** Maintain a stack-based history in `PickerDialog`. Each entry in the history records whether a note was saved (storing its original content) or skipped. The "Back" button pops from this stack and restores content if needed. The "Revert" button processes the entire stack to undo all changes.

**Tech Stack:** Python, PyQt6, Anki API (aqt).

### Task 1: Add restore utility to anki_utils

**Files:**
- Modify: `src/anki_utils.py`

**Step 1: Implement `restore_field_content`**

Add this function to the end of `src/anki_utils.py`:

```python
def restore_field_content(note_id, field_name, content):
    """
    Restores the original content of a field and flushes the note.
    """
    from aqt import mw
    try:
        note = mw.col.get_note(note_id)
        if field_name in note:
            note[field_name] = content
            note.flush()
            return True
    except Exception as e:
        print(f"Error restoring note {note_id}: {e}")
    return False
```

**Step 2: Commit**

```bash
git add src/anki_utils.py
git commit -m "feat: add restore_field_content utility"
```

### Task 2: Initialize History and Import Utility

**Files:**
- Modify: `src/gui/picker_dialog.py`

**Step 1: Import `restore_field_content`**

```python
# Modify line 15
from src.anki_utils import save_image_to_note, get_field_content, restore_field_content
```

**Step 2: Initialize history stack**

```python
# In PickerDialog.__init__ (around line 86)
        self.threadpool = QThreadPool()
        self.current_note = None
        self.history = []  # Added
```

**Step 3: Commit**

```bash
git add src/gui/picker_dialog.py
git commit -m "refactor: initialize history stack in PickerDialog"
```

### Task 3: Update Save and Skip Logic to Record History

**Files:**
- Modify: `src/gui/picker_dialog.py`

**Step 1: Update `on_image_downloaded` to record saves**

```python
    def on_image_downloaded(self, image_data):
        note_data = self.notes[self.current_index]
        config = note_data.get("config", {})
        field_name = config.get("target_field")
        
        # Store original content before saving
        original_content = ""
        if self.current_note and field_name in self.current_note:
            original_content = self.current_note[field_name]
        
        success = save_image_to_note(
            note_id=note_data["id"],
            image_data=image_data,
            field_name=field_name,
            mode=config.get("mode"),
            search_term=self.search_input.text()
        )
        
        if success:
            # Record save in history
            self.history.append({
                "type": "save",
                "note_id": note_data["id"],
                "field_name": field_name,
                "original_content": original_content,
                "search_term": self.search_input.text()
            })
            # Navigate forward without adding a 'skip' entry
            self._navigate_forward()
        else:
            self.on_download_error("Failed to save to Anki")
```

**Step 2: Update `on_skip` and create `_navigate_forward`**

Modify `on_skip` to record skips and use a helper for navigation.

```python
    def on_skip(self):
        self.history.append({"type": "skip"})
        self._navigate_forward()

    def _navigate_forward(self):
        if self.current_index < len(self.notes) - 1:
            self.current_index += 1
            self.update_current_note()
        else:
            self.accept()
```

**Step 3: Commit**

```bash
git add src/gui/picker_dialog.py
git commit -m "feat: record saves and skips in history"
```

### Task 4: Implement Back and Revert Logic

**Files:**
- Modify: `src/gui/picker_dialog.py`

**Step 1: Implement `on_back`**

```python
    def on_back(self):
        if not self.history:
            return
            
        last_action = self.history.pop()
        
        if last_action["type"] == "save":
            restore_field_content(
                last_action["note_id"], 
                last_action["field_name"], 
                last_action["original_content"]
            )
            
        self.current_index -= 1
        self.update_current_note()
```

**Step 2: Implement `on_revert`**

```python
    def on_revert(self):
        while self.history:
            last_action = self.history.pop()
            if last_action["type"] == "save":
                restore_field_content(
                    last_action["note_id"], 
                    last_action["field_name"], 
                    last_action["original_content"]
                )
        self.reject()
```

**Step 3: Update button states in `update_current_note`**

```python
    def update_current_note(self):
        if not self.notes:
            return
        note_data = self.notes[self.current_index]
        self.search_input.setText(note_data.get("term", ""))
        self.progress_label.setText(f"Card {self.current_index + 1} of {len(self.notes)}")
        
        # Update button states
        self.back_button.setEnabled(len(self.history) > 0)
        self.revert_button.setEnabled(len(self.history) > 0)
        
        # ... rest of the function ...
```

**Step 4: Commit**

```bash
git add src/gui/picker_dialog.py
git commit -m "feat: implement Back and Revert functionality"
```

### Task 5: Manual Verification (Dry Run)

**Step 1: Run the standalone picker script**

Run: `python3 src/gui/picker_dialog.py`

**Step 2: Verify buttons**
- Check if "Back" and "Revert" are disabled initially.
- Click "Skip" and verify "Back" and "Revert" become enabled.
- Click "Back" and verify it returns to the first card and disables buttons again.

**Step 3: Commit**
(No code changes, just verification)
