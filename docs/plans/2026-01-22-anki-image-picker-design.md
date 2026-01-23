# Design: Anki Image Picker

## Overview
A native Anki add-on (Python/PyQt6) designed for rapid, interactive image addition to flashcards. Unlike batch downloaders that add images blindly, this tool allows users to select from a grid of search results for each card in a batch, with on-the-fly search refinement and "hot-swapping" search terms from other fields.

## User Experience (UX)

### 1. Initiation
- **Trigger:** Select multiple notes in the Anki Browser -> Right-click -> "Quick Image Picker...".

### 2. Pre-flight Setup (Modal)
- **Source Field:** Dropdown to select the primary search term field (e.g., "Word").
- **Target Field:** Dropdown to select the image destination field (e.g., "Picture").
- **Mode:** Radio buttons for [Replace (Default), Append, Skip].
- **Clean Search:** Checkbox to strip HTML and Cloze markers (e.g., `{{c1::apple}}` -> `apple`).

### 3. Interactive Picker (Main Window)
- **Header:**
    - Progress indicator (e.g., "3 / 10").
    - Editable search box.
    - "Search" button to manual refresh.
    - **Field Hot-swaps:** A row of buttons for all other fields in the current note. Clicking one instantly searches for that field's content.
- **Image Grid:**
    - 6-8 thumbnails fetched from Google Images (Scraping).
    - **Selection:** Single click on an image selects it and moves to the next card.
    - **Keyboard Shortcuts:** Keys `1-8` for instant selection.
- **Footer Buttons:**
    - **Back:** Return to the previous card to re-pick or correct.
    - **Skip:** Move to the next card without changes.
    - **Abort:** Stop the session but keep changes made so far.
    - **Revert:** Undo all changes made during this session and close.

## Technical Architecture

### Component Breakdown
- **Backend:** Python 3.9+ with `requests` for fetching and `BeautifulSoup` for HTML parsing.
- **Frontend:** PyQt6 (Anki's native UI framework).
- **Media Management:** Uses `mw.col.media.add_file()` to save images with sanitized, unique filenames to the `collection.media` folder.
- **Concurrency:** Threading for image scraping and thumbnail loading to prevent UI freezing.

### Data Flow
1. **Search:** Add-on fetches Google Search results HTML.
2. **Parsing:** Extracts the first 8 image source URLs.
3. **Thumbnail Loading:** Loads low-res versions into memory for the grid.
4. **Final Selection:** Downloads the original image only when the user selects it.
5. **DB Update:** Updates the note's field with `<img src="...">` tag.

## Error Handling
- **Rate Limiting:** Detects HTTP 429 and prompts the user to wait or change IP.
- **No Results:** UI turns search bar red and displays a "No results" message.
- **Network Issues:** Graceful failure for individual thumbnails with placeholder icons.

## Success Criteria
- User can process 10 cards in under 60 seconds.
- No "blind" image additions; every image is human-verified.
- Seamless integration with the Anki Browser.
