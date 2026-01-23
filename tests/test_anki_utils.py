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

def test_save_image_to_note():
    # Setup mocks
    mock_mw = MagicMock()
    import aqt
    aqt.mw = mock_mw
    
    note = MagicMock()
    note.__getitem__.side_effect = lambda key: "old content"
    note.__contains__.side_effect = lambda key: True
    note.__setitem__ = MagicMock()
    mock_mw.col.get_note.return_value = note
    
    # Mock media.write_data
    mock_mw.col.media.write_data.return_value = "saved_filename.jpg"
    
    from src.anki_utils import save_image_to_note
    
    # Test Replace
    success = save_image_to_note(1, b"fake_data", "Field", "replace", "term")
    assert success is True
    note.__setitem__.assert_called_with("Field", '<img src="saved_filename.jpg">')
    
    # Test Append
    note.__setitem__.reset_mock()
    success = save_image_to_note(1, b"fake_data", "Field", "append", "term")
    assert success is True
    note.__setitem__.assert_called_with("Field", 'old content<br><img src="saved_filename.jpg">')
    
    # Test Skip (not empty)
    note.__setitem__.reset_mock()
    success = save_image_to_note(1, b"fake_data", "Field", "skip", "term")
    assert success is True
    note.__setitem__.assert_not_called()
    
    # Test Skip (empty)
    note.__getitem__.side_effect = lambda key: ""
    note.__setitem__.reset_mock()
    success = save_image_to_note(1, b"fake_data", "Field", "skip", "term")
    assert success is True
    note.__setitem__.assert_called_with("Field", '<img src="saved_filename.jpg">')
    
    # Verify flush
    assert note.flush.called

def test_filename_sanitization():
    from src.anki_utils import save_image_to_note
    mock_mw = MagicMock()
    import aqt
    aqt.mw = mock_mw
    
    note = MagicMock()
    note.__contains__.return_value = True
    mock_mw.col.get_note.return_value = note
    
    # Complex term
    save_image_to_note(1, b"data", "Field", "replace", "Golden Retriever (Dog) & Cat!")
    
    # Check what was passed to write_data
    args, kwargs = mock_mw.col.media.write_data.call_args
    filename = args[0]
    assert "Golden Retriever _Dog_ _ Cat_" in filename
    assert filename.endswith(".jpg")
    assert " " in filename # Current regex allows spaces

def test_extension_detection():
    from src.anki_utils import save_image_to_note
    mock_mw = MagicMock()
    import aqt
    aqt.mw = mock_mw
    
    note = MagicMock()
    note.__contains__.return_value = True
    mock_mw.col.get_note.return_value = note
    
    # PNG
    save_image_to_note(1, b"\x89PNG\r\n\x1a\nfake_png", "Field", "replace", "term")
    args, _ = mock_mw.col.media.write_data.call_args
    assert args[0].endswith(".png")
    
    # GIF
    save_image_to_note(1, b"GIF89afake_gif", "Field", "replace", "term")
    args, _ = mock_mw.col.media.write_data.call_args
    assert args[0].endswith(".gif")
    
    # WEBP
    save_image_to_note(1, b"RIFF\x00\x00\x00\x00WEBPfake_webp", "Field", "replace", "term")
    args, _ = mock_mw.col.media.write_data.call_args
    assert args[0].endswith(".webp")
    
    # Default (JPG)
    save_image_to_note(1, b"random_data", "Field", "replace", "term")
    args, _ = mock_mw.col.media.write_data.call_args
    assert args[0].endswith(".jpg")

def test_save_image_with_dimensions():
    from src.anki_utils import save_image_to_note
    mock_mw = MagicMock()
    import aqt
    aqt.mw = mock_mw
    
    note = MagicMock()
    note.__contains__.return_value = True
    note.__getitem__.return_value = ""
    mock_mw.col.get_note.return_value = note
    mock_mw.col.media.write_data.return_value = "saved_filename.jpg"
    
    # Width and Height
    save_image_to_note(1, b"data", "Field", "replace", "term", max_width=400, max_height=500)
    note.__setitem__.assert_called()
    call_args = note.__setitem__.call_args[0]
    img_tag = call_args[1]
    assert 'style="max-width: 400px; max-height: 500px;"' in img_tag
    
    # Only Width
    note.__setitem__.reset_mock()
    save_image_to_note(1, b"data", "Field", "replace", "term", max_width=400)
    img_tag = note.__setitem__.call_args[0][1]
    assert 'style="max-width: 400px;"' in img_tag
    
    # Only Height
    note.__setitem__.reset_mock()
    save_image_to_note(1, b"data", "Field", "replace", "term", max_height=500)
    img_tag = note.__setitem__.call_args[0][1]
    assert 'style="max-height: 500px;"' in img_tag
