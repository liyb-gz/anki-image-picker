# Multi-Provider Image Support Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add Bing and DuckDuckGo as alternative image providers to reduce reliance on Google and improve reliability.

**Architecture:** Strategy pattern for scraping logic, updated configuration for per-note-type persistence, and a live switcher in the Picker UI.

**Tech Stack:** Python 3.11, PyQt6, requests, BeautifulSoup4.

---

### Task 1: Refactor Scraper to Strategy Pattern

**Files:**
- Modify: `src/scraper.py`
- Modify: `tests/test_scraper.py`

**Step 1: Add tests for new providers in `tests/test_scraper.py`**

```python
def test_fetch_bing_structure():
    from src.scraper import fetch_image_urls
    # We use a real query but limit to 1 to verify structure
    urls = fetch_image_urls("apple", limit=1, provider="bing")
    assert len(urls) > 0
    assert urls[0].startswith("http")

def test_fetch_duckduckgo_structure():
    from src.scraper import fetch_image_urls
    urls = fetch_image_urls("apple", limit=1, provider="duckduckgo")
    assert len(urls) > 0
    assert urls[0].startswith("http")
```

**Step 2: Run tests to verify they fail**
Run: `pytest tests/test_scraper.py`
Expected: FAIL (Unexpected keyword argument 'provider' or logic not implemented)

**Step 3: Refactor `src/scraper.py`**
- Rename current logic to `_fetch_google`.
- Create `_fetch_bing(query, limit, start)`.
- Create `_fetch_duckduckgo(query, limit, start)`.
- Update `fetch_image_urls` to dispatch based on `provider`.

**Step 4: Run tests to verify they pass**
Run: `pytest tests/test_scraper.py`

**Step 5: Commit**
```bash
git add src/scraper.py tests/test_scraper.py
git commit -m "feat: implement Bing and DuckDuckGo scrapers"
```

---

### Task 2: Persistent Provider Configuration

**Files:**
- Modify: `src/config.json`
- Modify: `src/anki_utils.py`
- Modify: `src/gui/config_dialog.py`

**Step 1: Update `src/config.json`**
Add `"default_provider": "google"` to the root.

**Step 2: Update `ConfigManager` in `src/anki_utils.py`**
Update `get_global_defaults` to include `default_provider`.

**Step 3: Update `ConfigDialog` in `src/gui/config_dialog.py`**
- Add `self.provider_combo = QComboBox()` to `init_ui`.
- Populate with `["google", "bing", "duckduckgo"]`.
- Update `get_config` to return the selected provider.

**Step 4: Commit**
```bash
git add src/config.json src/anki_utils.py src/gui/config_dialog.py
git commit -m "feat: add provider selection to configuration"
```

---

### Task 3: Interactive Provider Switching in Picker

**Files:**
- Modify: `src/main.py`
- Modify: `src/gui/picker_dialog.py`

**Step 1: Update `src/main.py`**
Ensure the provider is extracted from config and passed to `PickerDialog`.

**Step 2: Add Provider Dropdown to `PickerDialog`**
- Add a `QComboBox` to the `top_layout` in `init_ui`.
- Connect its `currentTextChanged` signal to `self.start_fetching`.

**Step 3: Update `_fetch_images` in `src/gui/picker_dialog.py`**
Pass the current value of the provider dropdown to `fetch_image_urls`.

**Step 4: Commit**
```bash
git add src/main.py src/gui/picker_dialog.py
git commit -m "feat: add live provider switching to picker dialog"
```
