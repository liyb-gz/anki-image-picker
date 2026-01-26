from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QRadioButton, QButtonGroup, 
    QPushButton, QDialogButtonBox, QSpinBox, QLineEdit,
    QListWidget, QListWidgetItem, QGroupBox
)

class ConfigDialog(QDialog):
    """
    Dialog for configuring which fields to use for image picking and how to update them.
    """
    def __init__(self, fields, initial_config=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Anki Image Picker Configuration")
        self.fields = fields
        self.initial_config = initial_config or {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Source Field
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("Source Field (Text to search):"))
        self.source_combo = QComboBox()
        self.source_combo.addItems(self.fields)
        
        # Initial value
        source_val = self.initial_config.get("source_field")
        if source_val and source_val in self.fields:
            self.source_combo.setCurrentText(source_val)
            
        source_layout.addWidget(self.source_combo)
        layout.addLayout(source_layout)

        # Search Suffix
        suffix_layout = QHBoxLayout()
        suffix_layout.addWidget(QLabel("Search Suffix (e.g. ' anatomical'):"))
        self.suffix_edit = QLineEdit()
        self.suffix_edit.setText(self.initial_config.get("search_suffix", ""))
        suffix_layout.addWidget(self.suffix_edit)
        layout.addLayout(suffix_layout)

        # Preferred Provider
        provider_layout = QHBoxLayout()
        provider_layout.addWidget(QLabel("Preferred Provider:"))
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["google", "bing", "duckduckgo"])
        
        provider_val = self.initial_config.get("preferred_provider", "google")
        self.provider_combo.setCurrentText(provider_val)
        
        provider_layout.addWidget(self.provider_combo)
        layout.addLayout(provider_layout)

        # Target Field
        target_layout = QHBoxLayout()
        target_layout.addWidget(QLabel("Target Field (Where to put image):"))
        self.target_combo = QComboBox()
        self.target_combo.addItems(self.fields)
        
        # Initial value or heuristic
        target_val = self.initial_config.get("target_field")
        if target_val and target_val in self.fields:
            self.target_combo.setCurrentText(target_val)
        else:
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
            elif self.fields:
                self.target_combo.setCurrentIndex(0)
            
        target_layout.addWidget(self.target_combo)
        layout.addLayout(target_layout)

        # Context Fields
        context_group = QGroupBox("Context Fields (Show in Picker)")
        context_layout = QVBoxLayout(context_group)
        self.context_list = QListWidget()
        
        initial_context = self.initial_config.get("context_fields", [])
        for field in self.fields:
            item = QListWidgetItem(field)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            if field in initial_context:
                item.setCheckState(Qt.CheckState.Checked)
            else:
                item.setCheckState(Qt.CheckState.Unchecked)
            self.context_list.addItem(item)
            
        context_layout.addWidget(self.context_list)
        layout.addWidget(context_group)

        # Image Dimensions
        dims_layout = QHBoxLayout()
        dims_layout.addWidget(QLabel("Max Width:"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(50, 2000)
        self.width_spin.setValue(self.initial_config.get("max_width", 320))
        dims_layout.addWidget(self.width_spin)
        
        dims_layout.addWidget(QLabel("Max Height:"))
        self.height_spin = QSpinBox()
        self.height_spin.setRange(50, 2000)
        self.height_spin.setValue(self.initial_config.get("max_height", 320))
        dims_layout.addWidget(self.height_spin)
        layout.addLayout(dims_layout)

        # Mode
        layout.addWidget(QLabel("Update Mode:"))
        
        self.mode_button_group = QButtonGroup(self)
        self.replace_radio = QRadioButton("Replace")
        self.append_radio = QRadioButton("Append")
        self.skip_radio = QRadioButton("Skip if not empty")
        
        mode_val = self.initial_config.get("mode", "replace")
        if mode_val == "append":
            self.append_radio.setChecked(True)
        elif mode_val == "skip":
            self.skip_radio.setChecked(True)
        else:
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
            QDialogButtonBox.StandardButton.Cancel
        )
        self.start_button = QPushButton("Start")
        self.start_button.setDefault(True)
        if not self.fields:
            self.start_button.setEnabled(False)
            layout.addWidget(QLabel("<font color='red'>No fields found in the selected note type.</font>"))

        self.button_box.addButton(self.start_button, QDialogButtonBox.ButtonRole.AcceptRole)
        
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def get_config(self):
        """
        Returns the user's choices as a dictionary.
        """
        mode_map = {0: "replace", 1: "append", 2: "skip"}
        checked_id = self.mode_button_group.checkedId()
        
        context_fields = []
        for i in range(self.context_list.count()):
            item = self.context_list.item(i)
            if item and item.checkState() == Qt.CheckState.Checked:
                context_fields.append(item.text())

        return {
            "source_field": self.source_combo.currentText(),
            "target_field": self.target_combo.currentText(),
            "context_fields": context_fields,
            "search_suffix": self.suffix_edit.text(),
            "max_width": self.width_spin.value(),
            "max_height": self.height_spin.value(),
            "preferred_provider": self.provider_combo.currentText(),
            "mode": mode_map.get(checked_id, "replace")
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
