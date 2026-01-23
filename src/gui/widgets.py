from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import pyqtSignal, Qt

class ClickableImageLabel(QLabel):
    clicked = pyqtSignal(str)

    def __init__(self, url, parent=None):
        super().__init__(parent)
        self.url = url
        self.setCursor(self.cursor().shape().PointingHandCursor)
        self.setFixedWidth(150)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("border: 2px solid transparent;")

    def mousePressEvent(self, ev):
        self.clicked.emit(self.url)

    def set_selected(self, selected):
        if selected:
            self.setStyleSheet("border: 2px solid blue;")
        else:
            self.setStyleSheet("border: 2px solid transparent;")
