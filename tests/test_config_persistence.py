import sys
from unittest.mock import MagicMock
sys.modules['aqt'] = MagicMock()
sys.modules['anki'] = MagicMock()
import pytest

def test_config_manager_persistence():
    import aqt
    mock_mw = MagicMock()
    aqt.mw = mock_mw
    
    mock_addon_manager = mock_mw.addonManager
    mock_addon_manager.getConfig.return_value = {}
    
    from src.anki_utils import ConfigManager
    manager = ConfigManager()
    manager.save_note_type_config("Basic", {"source": "Front", "target": "Back"})
    
    # Verify it calls writeConfig with correct name
    args, _ = mock_addon_manager.writeConfig.call_args
    assert args[0] == "anki_image_picker"
