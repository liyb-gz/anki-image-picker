# Anki Image Adder Improvements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement persistent configuration per note type, search suffixes, dual dimension constraints (width/height), and "Load More" pagination.

**Architecture:** 
- Use `mw.addonManager` for persistent JSON configuration.
- Update `ConfigDialog` to show and save these persistent settings.
- Update `scraper.py` to support offset-based fetching.
- Update `PickerDialog` to append search suffixes and handle "Load More" logic.

**Tech Stack:** Python, PyQt6, Anki API.

### Task 1: Implement Configuration Persistence

**Files:**
- Modify: `src/anki_utils.py`
- Test: `tests/test_config_persistence.py`

**Step 1: Write the failing test**

```python
import sys
from unittest.mock import MagicMock
sys.modules['aqt'] = MagicMock()
sys.modules['anki'] = MagicMock()
import pytest

def test_config_manager_persistence():
    import aqt
    mock_mw = MagicMock()
    aqt.mw = mock_mw
    
    mock_addon_manager = mock_mw.addonManager
    mock_addon_manager.getConfig.return_value = {}
    
    from src.anki_utils import ConfigManager
    manager = ConfigManager()
    manager.save_note_type_config("Basic", {"source": "Front", "target": "Back"})
    
    # Verify it calls writeConfig
    assert mock_addon_manager.writeConfig.called
```

**Step 2: Run test to verify it fails**
Run: `pytest tests/test_config_persistence.py`
Expected: FAIL (ImportError: cannot import name 'ConfigManager')

**Step 3: Implement ConfigManager in `src/anki_utils.py`**

```python
class ConfigManager:
    def __init__(self):
        from aqt import mw
        self.mw = mw

    def get_all_config(self):
        # __name__ might be 'src.anki_utils' but in Anki it's the addon ID
        # For simplicity in local dev, we use a fixed string or handle None
        return self.mw.addonManager.getConfig("anki_image_adder") or {}

    def get_note_type_config(self, model_name):
        config = self.get_all_config()
        return config.get("models", {}).get(model_name, {})

    def save_note_type_config(self, model_name, model_config):
        config = self.get_all_config()
        if "models" not in config:
            config["models"] = {}
        config["models"][model_name] = model_config
        self.mw.addonManager.writeConfig("anki_image_adder", config)

    def get_global_defaults(self):
        config = self.get_all_config()
        return {
            "search_suffix": config.get("search_suffix", ""),
            "max_width": config.get("max_width", 320),
            "max_height": config.get("max_height", 320)
        }
```

**Step 4: Run test to verify it passes**
Run: `pytest tests/test_config_persistence.py`

**Step 5: Commit**
```bash
git add src/anki_utils.py tests/test_config_persistence.py
git commit -m "feat: add ConfigManager for persistent settings"
```

### Task 2: Update ConfigDialog with New Fields and Persistence

**Files:**
- Modify: `src/gui/config_dialog.py`
- Modify: `src/main.py`

**Step 1: Update `ConfigDialog` UI**
Add `search_suffix` (QLineEdit) and `max_height` (QSpinBox) to `init_ui`. 
Update `get_config` to return these values.
Accept initial values in `__init__` to pre-populate.

**Step 2: Update `on_quick_image_picker` in `src/main.py`**
1. Initialize `ConfigManager`.
2. Get note type name of the first selected note.
3. Fetch saved config for this note type.
4. Pass saved values to `ConfigDialog`.
5. If `dialog.exec()`, save the new choices via `ConfigManager.save_note_type_config`.

**Step 3: Commit**
```bash
git add src/gui/config_dialog.py src/main.py
git commit -m "feat: update ConfigDialog with height, suffix, and persistence"
```

### Task 3: Support Suffix and Dual Constraints in Saving

**Files:**
- Modify: `src/anki_utils.py`
- Modify: `src/gui/picker_dialog.py`

**Step 1: Update `save_image_to_note` signature and logic**
Accept `image_height` in `save_image_to_note`.
Update `img_tag` generation:
```python
style = []
if image_width: style.append(f"max-width: {image_width}px;")
if image_height: style.append(f"max-height: {image_height}px;")
style_str = f' style="{" ".join(style)}"' if style else ""
img_tag = f'<img src="{filename}"{style_str}>'
```

**Step 2: Update `PickerDialog` to append suffix**
In `start_fetching`, if `config.get("search_suffix")` exists, append it to the query.

**Step 3: Commit**
```bash
git add src/anki_utils.py src/gui/picker_dialog.py
git commit -m "feat: support search suffix and max_height constraints"
```

### Task 4: Implement "Load More" Pagination

**Files:**
- Modify: `src/scraper.py`
- Modify: `src/gui/picker_dialog.py`

**Step 1: Update `fetch_image_urls` for offset**
Add `start=0` parameter to `fetch_image_urls`.
URL update: `f"https://www.google.com/search?q={query}&tbm=isch&start={start}"`

**Step 2: Add "Load More" button to `PickerDialog`**
1. Add `self.current_offset = 0`.
2. Add `self.load_more_button` in `init_ui`.
3. Implement `on_load_more`: 
   - Increment `self.current_offset` by 8 (or batch size).
   - Call `fetch_image_urls` with query + offset.
   - Use `on_images_fetched` logic but **without** clearing the grid (append instead).

**Step 3: Commit**
```bash
git add src/scraper.py src/gui/picker_dialog.py
git commit -m "feat: implement Load More functionality in picker"
```
