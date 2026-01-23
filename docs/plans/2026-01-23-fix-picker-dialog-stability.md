# Picker Dialog Stability Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix stability issues, race conditions, and error handling in the PickerDialog.

**Architecture:** 
- Enhance `ImageFetcher` with error signaling.
- Implement graceful thread stopping instead of termination.
- Add safety checks for deleted UI objects during asynchronous callbacks.
- Provide visual feedback for empty search results.

**Tech Stack:** Python 3.11, PyQt6

### Task 1: Revert Button and Fetcher Error Handling

**Files:**
- Modify: `src/gui/picker_dialog.py`

**Step 1: Update ImageFetcher to handle errors**
- Add `error = pyqtSignal(str)` to `ImageFetcher`.
- Wrap `fetch_image_urls` in a try-except block.

**Step 2: Update on_revert to reject the dialog**

**Step 3: Verification**
- Manual check or mock test if possible.

**Step 4: Commit**
```bash
git add src/gui/picker_dialog.py
git commit -m "fix: implement revert and add fetcher error handling"
```

### Task 2: Fix Thumbnail Loading Race Condition

**Files:**
- Modify: `src/gui/picker_dialog.py`

**Step 1: Add sip import and check in on_thumbnail_loaded**
- Import `sip` (from `PyQt6` or top-level as found).
- Use `sip.isdeleted(label)` or `try...except RuntimeError` to ensure label is valid before `setPixmap`.

**Step 2: Commit**
```bash
git add src/gui/picker_dialog.py
git commit -m "fix: prevent race condition in thumbnail loading"
```

### Task 3: Thread Safety and No Results Feedback

**Files:**
- Modify: `src/gui/picker_dialog.py`

**Step 1: Replace terminate() with graceful stop**
- Add `is_interrupted` flag to `ImageFetcher` or just use `quit()`/`wait()`.
- Update `start_fetching` to stop previous fetcher safely.

**Step 2: Implement "No Results" visual feedback**
- If `urls` is empty in `on_images_fetched`, change `search_input` stylesheet or show a message.

**Step 3: Commit**
```bash
git add src/gui/picker_dialog.py
git commit -m "fix: improve thread safety and add no-results feedback"
```
