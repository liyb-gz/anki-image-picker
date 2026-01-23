import pytest
from unittest.mock import MagicMock
import sys

# Mock anki and aqt before importing
sys.modules['anki'] = MagicMock()
sys.modules['aqt'] = MagicMock()
sys.modules['aqt.qt'] = MagicMock()
sys.modules['aqt.utils'] = MagicMock()

try:
    from PyQt6.QtWidgets import QApplication
    from src.gui.picker_dialog import PickerDialog
except ImportError:
    QApplication = None
    PickerDialog = None

@pytest.fixture
def app():
    if QApplication:
        return QApplication.instance() or QApplication([])
    return None

@pytest.mark.skipif(PickerDialog is None or QApplication is None, reason="PyQt6 or PickerDialog not available")
def test_picker_dialog_history_navigation(app):
    notes = [{"id": 1, "term": "apple"}, {"id": 2, "term": "banana"}]
    dialog = PickerDialog(notes)
    
    # Initially back is disabled
    assert not dialog.back_button.isEnabled()
    assert not dialog.revert_button.isEnabled()
    
    # Skip one note
    dialog.on_skip()
    assert dialog.current_index == 1
    assert len(dialog.history) == 1
    assert dialog.history[0]["type"] == "skip"
    
    # Back should now be enabled
    assert dialog.back_button.isEnabled()
    assert dialog.revert_button.isEnabled()
    
    # Go back
    dialog.on_back()
    assert dialog.current_index == 0
    assert len(dialog.history) == 0
    assert not dialog.back_button.isEnabled()
    assert not dialog.revert_button.isEnabled()

@pytest.mark.skipif(PickerDialog is None or QApplication is None, reason="PyQt6 or PickerDialog not available")
def test_picker_dialog_revert(app):
    notes = [{"id": 1, "term": "apple"}, {"id": 2, "term": "banana"}]
    dialog = PickerDialog(notes)
    
    # Mocking accept/reject
    dialog.reject = MagicMock()
    
    # Skip two notes
    dialog.on_skip()
    dialog.on_skip() # This will call accept() because it's the last card
    
    # Force some history for revert test (since on_skip might have closed it if it was the last card)
    dialog.history = [{"type": "skip"}, {"type": "save", "note_id": 1, "field_name": "Front", "original_content": "old"}]
    
    dialog.on_revert()
    dialog.reject.assert_called_once()
    assert len(dialog.history) == 0
