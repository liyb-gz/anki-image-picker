from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QRadioButton, QButtonGroup, 
    QDialogButtonBox
)

class ConfigDialog(QDialog):
    """
    Dialog for configuring which fields to use for image picking and how to update them.
    """
    def __init__(self, fields, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Anki Image Picker Configuration")
        self.fields = fields
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Source Field
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("Source Field (Text to search):"))
        self.source_combo = QComboBox()
        self.source_combo.addItems(self.fields)
        source_layout.addWidget(self.source_combo)
        layout.addLayout(source_layout)

        # Target Field
        target_layout = QHBoxLayout()
        target_layout.addWidget(QLabel("Target Field (Where to put image):"))
        self.target_combo = QComboBox()
        self.target_combo.addItems(self.fields)
        # Try to select a different field by default if possible (e.g. if 'Image' exists)
        image_idx = -1
        for i, f in enumerate(self.fields):
            if "image" in f.lower():
                image_idx = i
                break
        
        if image_idx != -1:
            self.target_combo.setCurrentIndex(image_idx)
        elif len(self.fields) > 1:
            self.target_combo.setCurrentIndex(1)
            
        target_layout.addWidget(self.target_combo)
        layout.addLayout(target_layout)

        # Mode
        layout.addWidget(QLabel("Update Mode:"))
        
        self.mode_button_group = QButtonGroup(self)
        self.replace_radio = QRadioButton("Replace")
        self.append_radio = QRadioButton("Append")
        self.skip_radio = QRadioButton("Skip if not empty")
        
        self.replace_radio.setChecked(True)
        
        self.mode_button_group.addButton(self.replace_radio, 0)
        self.mode_button_group.addButton(self.append_radio, 1)
        self.mode_button_group.addButton(self.skip_radio, 2)
        
        mode_layout = QVBoxLayout()
        mode_layout.addWidget(self.replace_radio)
        mode_layout.addWidget(self.append_radio)
        mode_layout.addWidget(self.skip_radio)
        layout.addLayout(mode_layout)

        # Buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def get_config(self):
        """
        Returns the user's choices as a dictionary.
        """
        mode_map = {0: "replace", 1: "append", 2: "skip"}
        return {
            "source_field": self.source_combo.currentText(),
            "target_field": self.target_combo.currentText(),
            "mode": mode_map[self.mode_button_group.checkedId()]
        }

if __name__ == "__main__":
    # Mock data for testing UI
    import sys
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    dummy_fields = ["Front", "Back", "Image", "Extra"]
    dialog = ConfigDialog(dummy_fields)
    # Since we can't show UI in this environment, we just verify it exists
    print(f"Dialog created with fields: {dialog.fields}")
    print(f"Source combo items: {[dialog.source_combo.itemText(i) for i in range(dialog.source_combo.count())]}")
    print(f"Target combo items: {[dialog.target_combo.itemText(i) for i in range(dialog.target_combo.count())]}")
    # dialog.show()
    # sys.exit(app.exec())
