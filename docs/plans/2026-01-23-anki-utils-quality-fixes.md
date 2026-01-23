# Anki Utils Quality Improvements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Modernize Anki API usage, improve performance via caching, refine Cloze regex to handle hints, and add error handling for note retrieval.

**Architecture:** 
- Update `get_field_names` to use `note.note_type()` and a local cache for model fields.
- Update `get_field_content` with a more precise regex for Cloze deletions and wrap `get_note` in a `try...except` block.
- Update tests to reflect API changes and verify new regex behavior.

**Tech Stack:** Python, Anki (aqt/anki), pytest, BeautifulSoup4.

### Task 1: Update regex and error handling in `get_field_content`

**Files:**
- Modify: `src/anki_utils.py:16-38`
- Test: `tests/test_anki_utils.py:37-55`

**Step 1: Write a failing test for Cloze hints**

Update `test_get_field_content` to include a Cloze with a hint.

```python
def test_get_field_content_with_hint():
    # Setup mocks
    mock_mw = MagicMock()
    import aqt
    aqt.mw = mock_mw
    
    note = MagicMock()
    # Test with hint: {{c1::actual::hint}}
    note.__getitem__.side_effect = lambda key: "{{c1::actual::hint}}" if key == "Front" else ""
    mock_mw.col.get_note.return_value = note
    
    from src.anki_utils import get_field_content
    content = get_field_content(1, "Front")
    
    assert content == "actual"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_anki_utils.py -k test_get_field_content_with_hint -v`
Expected: FAIL (it will likely return `actual::hint` with the current regex)

**Step 3: Update `get_field_content` implementation**

Update regex and add error handling for `get_note`.

```python
def get_field_content(note_id, field_name):
    """
    Returns the cleaned text content of a field from a note ID.
    Cleans HTML tags and Cloze markers.
    """
    from aqt import mw
    try:
        note = mw.col.get_note(note_id)
    except Exception:
        return ""
        
    try:
        content = note[field_name]
    except KeyError:
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

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_anki_utils.py -v`
Expected: ALL PASS (including existing tests and the new hint test)

**Step 5: Commit**

```bash
git add src/anki_utils.py tests/test_anki_utils.py
git commit -m "fix(anki_utils): improve Cloze regex and add error handling for note retrieval"
```

### Task 2: Modernize API and add caching to `get_field_names`

**Files:**
- Modify: `src/anki_utils.py:3-14`
- Test: `tests/test_anki_utils.py:11-36`

**Step 1: Update `test_get_field_names` to use `note_type()`**

Update the test to mock `note_type()` instead of `model()`.

```python
def test_get_field_names():
    # Setup mocks
    mock_mw = MagicMock()
    import aqt
    aqt.mw = mock_mw
    
    # Mock note 1
    note1 = MagicMock()
    mock_model1 = {'flds': [{'name': 'Front'}, {'name': 'Back'}]}
    # Modernize mock
    note1.note_type.return_value = mock_model1
    note1.mid = 101 # Model ID
    
    # Mock note 2
    note2 = MagicMock()
    mock_model2 = {'flds': [{'name': 'Front'}, {'name': 'Back'}, {'name': 'Image'}]}
    # Modernize mock
    note2.note_type.return_value = mock_model2
    note2.mid = 102
    
    mock_mw.col.get_note.side_effect = lambda id: note1 if id == 1 else note2
    
    from src.anki_utils import get_field_names
    fields = get_field_names([1, 2])
    
    assert "Front" in fields
    assert "Back" in fields
    assert "Image" in fields
    assert len(fields) == 3
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_anki_utils.py::test_get_field_names -v`
Expected: FAIL (it still calls `note.model()`)

**Step 3: Update `get_field_names` implementation**

Add caching and use `note_type()`.

```python
def get_field_names(note_ids):
    """
    Returns a list of unique field names for the given note IDs.
    """
    from aqt import mw
    field_names = set()
    model_cache = {}
    
    for nid in note_ids:
        try:
            note = mw.col.get_note(nid)
        except Exception:
            continue
            
        mid = note.mid
        if mid not in model_cache:
            model = note.note_type()
            model_cache[mid] = [f['name'] for f in model['flds']]
            
        for name in model_cache[mid]:
            field_names.add(name)
            
    return sorted(list(field_names))
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_anki_utils.py -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add src/anki_utils.py tests/test_anki_utils.py
git commit -m "refactor(anki_utils): modernize API usage and add caching to get_field_names"
```
