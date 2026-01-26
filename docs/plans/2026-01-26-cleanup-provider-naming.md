# Clean up Provider Naming Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Clean up provider naming by using `default_provider` in global config and `preferred_provider` for note-type specific overrides and UI.

**Architecture:** 
- `ConfigManager.get_global_defaults` maps `default_provider` from global config to `preferred_provider` in the returned dictionary.
- The UI (ConfigDialog) and PickerDialog use `preferred_provider` exclusively.
- Note-type specific configuration in `config.json` uses the key `preferred_provider`.

**Tech Stack:** Python, PyQt6, Anki API

### Task 1: Update ConfigManager.get_global_defaults

**Files:**
- Modify: `src/anki_utils.py:162-171`
- Modify: `tests/test_config_persistence.py:38-44`

**Step 1: Write the failing test**

Modify `tests/test_config_persistence.py:38-44` to expect only `preferred_provider`.

```python
    defaults = manager.get_global_defaults()
    
    assert defaults["search_suffix"] == " test"
    assert defaults["max_width"] == 400
    assert defaults["max_height"] == 400
    assert "default_provider" not in defaults
    assert defaults["preferred_provider"] == "bing"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_config_persistence.py::test_config_manager_global_defaults -v`
Expected: FAIL (assertion error or `default_provider` still present)

**Step 3: Update `get_global_defaults` implementation**

```python
    def get_global_defaults(self):
        config = self.get_all_config()
        default_provider = config.get("default_provider", "google")
        return {
            "search_suffix": config.get("search_suffix", ""),
            "max_width": config.get("max_width", 320),
            "max_height": config.get("max_height", 320),
            "preferred_provider": default_provider
        }
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_config_persistence.py::test_config_manager_global_defaults -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/anki_utils.py tests/test_config_persistence.py
git commit -m "refactor: map default_provider to preferred_provider in get_global_defaults"
```

### Task 2: Update remaining tests in `test_config_persistence.py`

**Files:**
- Modify: `tests/test_config_persistence.py:56-59`

**Step 1: Update `test_config_manager_global_defaults_fallback`**

```python
def test_config_manager_global_defaults_fallback():
    # ...
    defaults = manager.get_global_defaults()
    assert defaults["preferred_provider"] == "google"
    assert "default_provider" not in defaults
```

**Step 2: Run tests**

Run: `pytest tests/test_config_persistence.py -v`
Expected: PASS

**Step 3: Commit**

```bash
git add tests/test_config_persistence.py
git commit -m "test: update fallback test for provider naming cleanup"
```

### Task 3: Final Verification of UI components

**Files:**
- Check: `src/gui/config_dialog.py`
- Check: `src/gui/picker_dialog.py`

**Step 1: Verify `ConfigDialog` only uses `preferred_provider`**

I already verified this in `src/gui/config_dialog.py`:
- Line 51: `provider_val = self.initial_config.get("preferred_provider", "google")`
- Line 180: `"preferred_provider": self.provider_combo.currentText(),`

**Step 2: Verify `PickerDialog` only uses `preferred_provider`**

I already verified this in `src/gui/picker_dialog.py`:
- Line 325: `provider = config.get("preferred_provider", "google")`

**Step 3: Run all tests**

Run: `pytest tests/test_config_persistence.py tests/test_config_logic.py -v`
Expected: ALL PASS

**Step 4: Commit**

```bash
git commit --allow-empty -m "chore: verify provider naming cleanup in UI components"
```
