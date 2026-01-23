# Anki Image Picker Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a native Anki add-on for rapid, interactive image selection from Google Images directly within the Anki Browser.

**Architecture:** A PyQt6-based desktop interface integrated into Anki's browser. It uses a threaded scraper to fetch image thumbnails from Google and updates Anki's SQLite database and media collection.

**Tech Stack:** Python 3.9+, PyQt6 (Anki's vendor), `requests`, `beautifulsoup4`.

---

### Task 1: Project Scaffolding & Anki Entry Point

**Files:**
- Create: `src/__init__.py`
- Create: `src/main.py`

**Step 1: Create the basic add-on structure**
Write `src/__init__.py` to import the main entry point.
Write a placeholder `src/main.py` that logs "Image Picker Loaded" to the console.

**Step 2: Commit**
```bash
git add src/
git commit -m "chore: initial project scaffolding"
```

---

### Task 2: Google Image Scraper Logic

**Files:**
- Create: `src/scraper.py`
- Create: `tests/test_scraper.py`

**Step 1: Write the failing test for scraping**
Test that `fetch_image_urls(query)` returns a list of 8 strings.
Mock the `requests.get` response with sample Google Images HTML.

**Step 2: Implement the scraper**
Use `requests` and a robust User-Agent to fetch HTML and parse image URLs.

**Step 3: Verify tests pass**
Run: `pytest tests/test_scraper.py`

**Step 4: Commit**
```bash
git add src/scraper.py tests/test_scraper.py
git commit -m "feat: add google images scraper with tests"
```

---

### Task 3: Pre-flight Configuration Dialog

**Files:**
- Create: `src/gui/config_dialog.py`

**Step 1: Implement the UI**
Create a `QDialog` with:
- Source Field (ComboBox)
- Target Field (ComboBox)
- Mode (RadioButtons: Replace, Append, Skip)
- Start Button

**Step 2: Mock data for testing UI**
Manually run the dialog with dummy field names to verify layout.

**Step 3: Commit**
```bash
git add src/gui/config_dialog.py
git commit -m "feat: add pre-flight configuration dialog"
```

---

### Task 4: Interactive Picker UI - Basic Grid

**Files:**
- Create: `src/gui/picker_dialog.py`
- Create: `src/gui/widgets.py`

**Step 1: Create the Picker Window layout**
Implement a grid that can hold 8 `QLabel` widgets for thumbnails.
Add the search bar and progress indicator.

**Step 2: Implement thumbnail loading**
Use `QNetworkAccessManager` or a separate thread to load images from URLs into `QPixmap`.

**Step 3: Commit**
```bash
git add src/gui/picker_dialog.py src/gui/widgets.py
git commit -m "feat: add interactive picker UI with image grid"
```

---

### Task 5: Anki Integration - Note Selection & Field Access

**Files:**
- Modify: `src/main.py`
- Create: `src/anki_utils.py`

**Step 1: Hook into Anki Browser**
Use `browser_menus_did_init` to add "Quick Image Picker..." to the context menu.

**Step 2: Implement field extraction logic**
Write a utility to get all fields from the selected notes' NoteType.

**Step 3: Commit**
```bash
git add src/main.py src/anki_utils.py
git commit -m "feat: integrate with anki browser context menu"
```

---

### Task 6: Image Selection & Media Saving

**Files:**
- Modify: `src/gui/picker_dialog.py`
- Modify: `src/anki_utils.py`

**Step 1: Implement selection handler**
When an image is clicked:
1. Download the full image.
2. Save to `collection.media` using `mw.col.media.add_file`.
3. Update the note's target field with the `<img>` tag.

**Step 2: Handle "Replace" vs "Append" logic**
Read existing field content and modify accordingly before saving the note.

**Step 3: Commit**
```bash
git add src/gui/picker_dialog.py src/anki_utils.py
git commit -m "feat: implement image selection and anki media saving"
```

---

### Task 7: Hot-swaps & Search Refinement

**Files:**
- Modify: `src/gui/picker_dialog.py`

**Step 1: Add Field Buttons**
Dynamically generate buttons for all fields in the note.
Clicking a button updates the search term and triggers a new scraper run.

**Step 2: Implement manual search refinement**
Ensure the search bar triggers a reload on Enter.

**Step 3: Commit**
```bash
git add src/gui/picker_dialog.py
git commit -m "feat: add field hot-swaps and manual search refinement"
```

---

### Task 8: Session Management (Back/Undo/Revert)

**Files:**
- Modify: `src/gui/picker_dialog.py`
- Modify: `src/anki_utils.py`

**Step 1: Implement "Back" button**
Store a stack of previous states (Note ID + Original Content) to allow going back.

**Step 2: Implement "Revert" button**
Iterate through the session history and restore all original field values.

**Step 3: Commit**
```bash
git add src/gui/picker_dialog.py src/anki_utils.py
git commit -m "feat: add session history for back and revert actions"
```
