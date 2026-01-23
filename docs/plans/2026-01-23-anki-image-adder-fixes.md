# Anki Image Adder Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix media saving API, improve extension detection, and ensure UI refresh in Anki.

**Architecture:** 
- Update `anki_utils.py` to use `mw.col.media.write_data` for saving images.
- Implement extension detection based on image data magic bytes in `anki_utils.py`.
- Ensure `mw.reset()` is called when the `PickerDialog` finishes in all paths.

**Tech Stack:** Python, PyQt6, Anki API.

### Task 1: Update media saving and extension detection in `anki_utils.py`

**Files:**
- Modify: `src/anki_utils.py`

**Step 1: Implement extension detection and update saving logic**

Modify `save_image_to_note` in `src/anki_utils.py`:

```python
def save_image_to_note(note_id, image_data, field_name, mode, search_term):
    """
    Saves image data to Anki's media collection and updates the specified note field.
    """
    from aqt import mw
    
    # 1. Detect extension from magic bytes
    ext = ".jpg" # Default
    if image_data.startswith(b"\x89PNG\r\n\x1a\n"):
        ext = ".png"
    elif image_data.startswith(b"GIF87a") or image_data.startswith(b"GIF89a"):
        ext = ".gif"
    elif image_data.startswith(b"RIFF") and image_data[8:12] == b"WEBP":
        ext = ".webp"
    
    # 2. Generate a sanitized filename
    clean_term = re.sub(r'[^\w\-_\. ]', '_', search_term).strip()
    if not clean_term:
        clean_term = "image"
    
    clean_term = clean_term[:50]
    suggested_filename = f"image_picker_{clean_term}{ext}"
    
    # 3. Save to media collection using write_data for raw bytes
    filename = mw.col.media.write_data(suggested_filename, image_data)
    
    # 4. Construct HTML tag
    img_tag = f'<img src="{filename}">'
    
    # ... rest of the function remains same ...
```

**Step 2: Commit**

```bash
git add src/anki_utils.py
git commit -m "fix: use write_data and detect image extension from bytes"
```

### Task 2: Ensure UI refresh in `picker_dialog.py`

**Files:**
- Modify: `src/gui/picker_dialog.py`

**Step 1: Add `mw.reset()` to `accept` and `reject` overrides**

Modify `PickerDialog` class in `src/gui/picker_dialog.py`:

```python
    def accept(self):
        if mw:
            mw.reset()
        super().accept()

    def reject(self):
        if mw:
            mw.reset()
        super().reject()
```

And remove the manual `mw.reset()` from `on_skip` to avoid redundancy.

**Step 2: Commit**

```bash
git add src/gui/picker_dialog.py
git commit -m "fix: ensure mw.reset() is called on dialog close"
```
