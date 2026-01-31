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
    context_fields = config.get("context_fields", [])
    
    # 5. Prepare note data for Picker
    notes_data = []
    for nid in selected_notes:
        note = mw.col.get_note(nid)
        term = get_field_content(note, source_field)
        if term:
            context_data = {f: get_field_content(note, f) for f in context_fields}
            notes_data.append({
                "id": nid,
                "term": term,
                "context_data": context_data,
                "config": config  # Pass config so picker knows where to save
            })
            
    if not notes_data:
        from aqt.utils import showInfo
        showInfo("No search terms found in the selected notes' source field.")
        return
        
    # 4. Open Picker Dialog
    preferred_provider = config.get("preferred_provider", "google")
    picker = PickerDialog(notes_data, preferred_provider=preferred_provider, parent=browser)
    picker.exec()

def setup_menu(browser):
    action = QAction("Anki Image Picker...", browser)
    action.triggered.connect(lambda: on_quick_image_picker(browser))
    browser.form.menuEdit.addAction(action)

def on_browser_context_menu(browser, menu):
    selected_notes = browser.selected_notes()
    if not selected_notes:
        return
        
    action = menu.addAction("Anki Image Picker...")
    action.triggered.connect(lambda: on_quick_image_picker(browser))

def init():
    gui_hooks.browser_menus_did_init.append(setup_menu)
    gui_hooks.browser_will_show_context_menu.append(on_browser_context_menu)

init()
print("Image Picker Loaded")
