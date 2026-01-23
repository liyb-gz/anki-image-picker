import sys
import pytest
from PyQt6.QtWidgets import QApplication
from src.gui.config_dialog import ConfigDialog

# Create a single QApplication instance for all tests
@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app

def test_config_dialog_data(qapp):
    fields = ["Front", "Back", "Image"]
    dialog = ConfigDialog(fields)
    
    # Check default values
    config = dialog.get_config()
    assert config["source_field"] == "Front"
    assert config["target_field"] == "Image"
    assert config["max_width"] == 320
    assert config["max_height"] == 320
    assert config["search_suffix"] == ""
    assert config["mode"] == "replace"
    
    # Simulate user changes
    dialog.source_combo.setCurrentText("Back")
    dialog.width_spin.setValue(500)
    dialog.height_spin.setValue(600)
    dialog.suffix_edit.setText(" anatomical")
    dialog.append_radio.setChecked(True)
    
    config = dialog.get_config()
    assert config["source_field"] == "Back"
    assert config["max_width"] == 500
    assert config["max_height"] == 600
    assert config["search_suffix"] == " anatomical"
    assert config["mode"] == "append"

def test_config_dialog_initial_config(qapp):
    fields = ["Front", "Back", "Image"]
    initial_config = {
        "source_field": "Back",
        "target_field": "Front",
        "search_suffix": " test",
        "max_width": 400,
        "max_height": 500,
        "mode": "skip"
    }
    dialog = ConfigDialog(fields, initial_config=initial_config)
    
    config = dialog.get_config()
    assert config["source_field"] == "Back"
    assert config["target_field"] == "Front"
    assert config["search_suffix"] == " test"
    assert config["max_width"] == 400
    assert config["max_height"] == 500
    assert config["mode"] == "skip"
