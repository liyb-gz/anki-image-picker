import sys
from unittest.mock import MagicMock

# Mock anki and aqt before importing anki_utils
sys.modules['anki'] = MagicMock()
sys.modules['aqt'] = MagicMock()
sys.modules['aqt.qt'] = MagicMock()

import pytest

def test_get_field_names():
    # Setup mocks
    mock_mw = MagicMock()
    import aqt
    aqt.mw = mock_mw
    
    # Mock note 1
    note1 = MagicMock()
    mock_model1 = {'flds': [{'name': 'Front'}, {'name': 'Back'}]}
    note1.model.return_value = mock_model1
    
    # Mock note 2
    note2 = MagicMock()
    mock_model2 = {'flds': [{'name': 'Front'}, {'name': 'Back'}, {'name': 'Image'}]}
    note2.model.return_value = mock_model2
    
    mock_mw.col.get_note.side_effect = lambda id: note1 if id == 1 else note2
    
    from src.anki_utils import get_field_names
    fields = get_field_names([1, 2])
    
    assert "Front" in fields
    assert "Back" in fields
    assert "Image" in fields
    assert len(fields) == 3

def test_get_field_content():
    # Setup mocks
    mock_mw = MagicMock()
    import aqt
    aqt.mw = mock_mw
    
    note = MagicMock()
    # Ensure note[field_name] returns a real string, not a mock
    note.__getitem__.side_effect = lambda key: "<b>Some</b> content {{c1::cloze}}" if key == "Front" else ""
    mock_mw.col.get_note.return_value = note
    
    from src.anki_utils import get_field_content
    # Test cleaning HTML and cloze
    content = get_field_content(1, "Front")
    
    assert "Some content cloze" in content
    assert "<b>" not in content
    assert "{{" not in content

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
