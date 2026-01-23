from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import pyqtSignal

class ClickableImageLabel(QLabel):
    clicked = pyqtSignal(str)

    def __init__(self, url, parent=None):
        super().__init__(parent)
        self.url = url
        self.setCursor(self.cursor().shape().PointingHandCursor)
        self.setScaledContents(True)
        self.setFixedSize(150, 150)
        self.setStyleSheet("border: 2px solid transparent;")

    def mousePressEvent(self, ev):
        self.clicked.emit(self.url)

    def set_selected(self, selected):
        if selected:
            self.setStyleSheet("border: 2px solid blue;")
        else:
            self.setStyleSheet("border: 2px solid transparent;")
