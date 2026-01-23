import sys
from PyQt6.QtWidgets import QApplication
from src.gui.config_dialog import ConfigDialog

def test_config_dialog_data():
    app = QApplication(sys.argv)
    fields = ["Front", "Back", "Image"]
    dialog = ConfigDialog(fields)
    
    # Check default values
    config = dialog.get_config()
    assert config["source_field"] == "Front"
    assert config["target_field"] == "Image"
    assert config["image_width"] == 320
    assert config["mode"] == "replace"
    
    # Simulate user changes
    dialog.source_combo.setCurrentText("Back")
    dialog.width_spin.setValue(500)
    dialog.append_radio.setChecked(True)
    
    config = dialog.get_config()
    assert config["source_field"] == "Back"
    assert config["image_width"] == 500
    assert config["mode"] == "append"
    
    print("ConfigDialog data test passed!")

if __name__ == "__main__":
    try:
        test_config_dialog_data()
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)
