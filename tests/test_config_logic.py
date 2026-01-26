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
    assert config["preferred_provider"] == "google"
    assert config["mode"] == "replace"
    
    # Simulate user changes
    dialog.source_combo.setCurrentText("Back")
    dialog.width_spin.setValue(500)
    dialog.height_spin.setValue(600)
    dialog.suffix_edit.setText(" anatomical")
    dialog.provider_combo.setCurrentText("duckduckgo")
    dialog.append_radio.setChecked(True)
    
    config = dialog.get_config()
    assert config["source_field"] == "Back"
    assert config["max_width"] == 500
    assert config["max_height"] == 600
    assert config["search_suffix"] == " anatomical"
    assert config["preferred_provider"] == "duckduckgo"
    assert config["mode"] == "append"

def test_config_dialog_initial_config(qapp):
    fields = ["Front", "Back", "Image"]
    initial_config = {
        "source_field": "Back",
        "target_field": "Front",
        "search_suffix": " test",
        "max_width": 400,
        "max_height": 500,
        "preferred_provider": "bing",
        "mode": "skip"
    }
    dialog = ConfigDialog(fields, initial_config=initial_config)
    
    config = dialog.get_config()
    assert config["source_field"] == "Back"
    assert config["target_field"] == "Front"
    assert config["search_suffix"] == " test"
    assert config["max_width"] == 400
    assert config["max_height"] == 500
    assert config["preferred_provider"] == "bing"
    assert config["mode"] == "skip"

def test_config_dialog_context_fields(qapp):
    from PyQt6.QtCore import Qt
    fields = ["Front", "Back", "Meaning", "Notes"]
    dialog = ConfigDialog(fields)
    
    # Simulate selecting "Meaning" and "Notes"
    items = dialog.context_list.findItems("Meaning", Qt.MatchFlag.MatchExactly)
    if items: items[0].setCheckState(Qt.CheckState.Checked)
    
    items = dialog.context_list.findItems("Notes", Qt.MatchFlag.MatchExactly)
    if items: items[0].setCheckState(Qt.CheckState.Checked)
    
    config = dialog.get_config()
    assert "Meaning" in config["context_fields"]
    assert "Notes" in config["context_fields"]
    assert "Front" not in config["context_fields"]

def test_config_dialog_initial_context_fields(qapp):
    from PyQt6.QtCore import Qt
    fields = ["Front", "Back", "Meaning", "Notes"]
    initial_config = {
        "context_fields": ["Back", "Meaning"]
    }
    dialog = ConfigDialog(fields, initial_config=initial_config)
    
    config = dialog.get_config()
    assert "Back" in config["context_fields"]
    assert "Meaning" in config["context_fields"]
    assert "Front" not in config["context_fields"]
    assert "Notes" not in config["context_fields"]
    
    # Verify check states directly
    for i in range(dialog.context_list.count()):
        item = dialog.context_list.item(i)
        if item:
            if item.text() in ["Back", "Meaning"]:
                assert item.checkState() == Qt.CheckState.Checked
            else:
                assert item.checkState() == Qt.CheckState.Unchecked
