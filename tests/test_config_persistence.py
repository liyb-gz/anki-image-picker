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

def test_config_manager_global_defaults():
    import aqt
    mock_mw = MagicMock()
    aqt.mw = mock_mw
    
    mock_addon_manager = mock_mw.addonManager
    mock_addon_manager.getConfig.return_value = {
        "search_suffix": " test",
        "max_width": 400,
        "max_height": 400,
        "default_provider": "bing"
    }
    
    from src.anki_utils import ConfigManager
    manager = ConfigManager()
    defaults = manager.get_global_defaults()
    
    assert defaults["search_suffix"] == " test"
    assert defaults["max_width"] == 400
    assert defaults["max_height"] == 400
    assert "default_provider" not in defaults
    assert defaults["preferred_provider"] == "bing"

def test_config_manager_global_defaults_fallback():
    import aqt
    mock_mw = MagicMock()
    aqt.mw = mock_mw
    
    mock_addon_manager = mock_mw.addonManager
    mock_addon_manager.getConfig.return_value = {} # Empty config
    
    from src.anki_utils import ConfigManager
    manager = ConfigManager()
    defaults = manager.get_global_defaults()
    
    assert defaults["preferred_provider"] == "google" # Default fallback
    assert "default_provider" not in defaults

def test_config_manager_note_type_provider():
    import aqt
    mock_mw = MagicMock()
    aqt.mw = mock_mw
    
    mock_addon_manager = mock_mw.addonManager
    mock_addon_manager.getConfig.return_value = {
        "models": {
            "Basic": {
                "preferred_provider": "duckduckgo"
            }
        }
    }
    
    from src.anki_utils import ConfigManager
    manager = ConfigManager()
    
    # Test get
    model_config = manager.get_note_type_config("Basic")
    assert model_config["preferred_provider"] == "duckduckgo"
    
    # Test save
    manager.save_note_type_config("Basic", {"preferred_provider": "bing"})
    args, _ = mock_addon_manager.writeConfig.call_args
    assert args[1]["models"]["Basic"]["preferred_provider"] == "bing"
