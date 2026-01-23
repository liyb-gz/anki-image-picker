import pytest
from src.gui.widgets import ClickableImageLabel

def test_clickable_image_label_emits_clicked(qtbot):
    label = ClickableImageLabel("http://example.com/image.jpg")
    qtbot.addWidget(label)
    
    with qtbot.waitSignal(label.clicked) as blocker:
        qtbot.mouseClick(label, Qt.MouseButton.LeftButton)
    
    assert blocker.args == ["http://example.com/image.jpg"]

from PyQt6.QtCore import Qt
