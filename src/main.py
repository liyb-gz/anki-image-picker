from aqt import mw, gui_hooks
from aqt.qt import QAction
from .anki_utils import get_field_names, get_field_content, ConfigManager
from .gui.config_dialog import ConfigDialog
from .gui.picker_dialog import PickerDialog

def on_quick_image_picker(browser):
    selected_notes = browser.selected_notes()
    if not selected_notes:
        return

    # 1. Get unique fields from selected notes
    fields = get_field_names(selected_notes)
    
    # 2. Get saved config for this note type
    config_manager = ConfigManager()
    note = mw.col.get_note(selected_notes[0])
    model_name = note.note_type()["name"]
    
    saved_config = config_manager.get_note_type_config(model_name)
    global_defaults = config_manager.get_global_defaults()
    
    # Merge: saved_config takes precedence, then global_defaults
    initial_config = {**global_defaults, **saved_config}
    
    # 3. Open Config Dialog
    dialog = ConfigDialog(fields, initial_config=initial_config, parent=browser)
    if not dialog.exec():
        return
        
    config = dialog.get_config()
    
    # 4. Save the config for this note type
    config_manager.save_note_type_config(model_name, config)
    
    source_field = config["source_field"]
    search_suffix = config.get("search_suffix", "")
    
    # 5. Prepare note data for Picker
    notes_data = []
    for nid in selected_notes:
        term = get_field_content(nid, source_field)
        if term:
            # Apply suffix if present
            full_term = term
            if search_suffix:
                full_term += f" {search_suffix.strip()}"
                
            notes_data.append({
                "id": nid,
                "term": full_term,
                "config": config  # Pass config so picker knows where to save
            })
            
    if not notes_data:
        from aqt.utils import showInfo
        showInfo("No search terms found in the selected notes' source field.")
        return
        
    # 4. Open Picker Dialog
    picker = PickerDialog(notes_data, parent=browser)
    picker.exec()

def setup_menu(browser):
    action = QAction("Quick Image Picker...", browser)
    action.triggered.connect(lambda: on_quick_image_picker(browser))
    browser.form.menuEdit.addAction(action)

def on_browser_context_menu(browser, menu):
    selected_notes = browser.selected_notes()
    if not selected_notes:
        return
        
    action = menu.addAction("Quick Image Picker...")
    action.triggered.connect(lambda: on_quick_image_picker(browser))

def init():
    gui_hooks.browser_menus_did_init.append(setup_menu)
    gui_hooks.browser_will_show_context_menu.append(on_browser_context_menu)

init()
print("Image Picker Loaded")
