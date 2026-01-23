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
def test_picker_dialog_initial_state(app):
    notes = [{"id": 1, "term": "apple"}, {"id": 2, "term": "banana"}]
    dialog = PickerDialog(notes)
    assert dialog.search_input.text() == "apple"
    assert "1 of 2" in dialog.progress_label.text()
