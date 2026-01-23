import re
from bs4 import BeautifulSoup

def get_field_names(note_ids):
    """
    Returns a list of unique field names for the given note IDs.
    """
    from aqt import mw
    field_names = set()
    model_cache = {}
    
    for nid in note_ids:
        try:
            note = mw.col.get_note(nid)
        except Exception:
            continue
            
        mid = note.mid
        if mid not in model_cache:
            model = note.note_type()
            model_cache[mid] = [f['name'] for f in model['flds']]
            
        for name in model_cache[mid]:
            field_names.add(name)
            
    return sorted(list(field_names))

def get_field_content(note_or_id, field_name):
    """
    Returns the cleaned text content of a field from a note ID or Note object.
    Cleans HTML tags and Cloze markers.
    """
    from aqt import mw
    if isinstance(note_or_id, (int, str)):
        try:
            note = mw.col.get_note(note_or_id)
        except Exception:
            return ""
    else:
        note = note_or_id
        
    try:
        content = note[field_name]
    except (KeyError, TypeError):
        return ""

    # Clean HTML
    soup = BeautifulSoup(content, "html.parser")
    text = soup.get_text()

    # Clean Cloze markers {{c1::text}} or {{c1::text::hint}} -> text
    text = re.sub(r"\{\{c\d+::(.*?)(?::.*?)?\}\}", r"\1", text)
    # Clean other brackets just in case
    text = text.replace("{{", "").replace("}}", "")
    
    return text.strip()

def save_image_to_note(note_id, image_data, field_name, mode, search_term, image_width=None, max_height=None):
    """
    Saves image data to Anki's media collection and updates the specified note field.
    """
    from aqt import mw
    
    # 1. Detect extension from magic bytes
    ext = ".jpg" # Default
    if image_data.startswith(b"\x89PNG\r\n\x1a\n"):
        ext = ".png"
    elif image_data.startswith(b"GIF87a") or image_data.startswith(b"GIF89a"):
        ext = ".gif"
    elif image_data.startswith(b"RIFF") and image_data[8:12] == b"WEBP":
        ext = ".webp"
    
    # 2. Generate a sanitized filename
    clean_term = re.sub(r'[^\w\-_\. ]', '_', search_term).strip()
    if not clean_term:
        clean_term = "image"
    
    clean_term = clean_term[:50]
    suggested_filename = f"image_picker_{clean_term}{ext}"
    
    # 3. Save to media collection using write_data for raw bytes
    filename = mw.col.media.write_data(suggested_filename, image_data)
    
    # 4. Construct HTML tag
    style_parts = []
    if image_width:
        style_parts.append(f"max-width: {image_width}px;")
    if max_height:
        style_parts.append(f"max-height: {max_height}px;")
    
    if style_parts:
        style_str = " ".join(style_parts)
        img_tag = f'<img src="{filename}" style="{style_str}">'
    else:
        img_tag = f'<img src="{filename}">'
    
    # 4. Update the note
    try:
        note = mw.col.get_note(note_id)
    except Exception:
        return False
        
    if field_name not in note:
        return False
        
    current_content = note[field_name].strip()
    
    if mode == "replace":
        note[field_name] = img_tag
    elif mode == "append":
        if current_content:
            note[field_name] = current_content + "<br>" + img_tag
        else:
            note[field_name] = img_tag
    elif mode == "skip":
        if not current_content:
            note[field_name] = img_tag
        else:
            # Field not empty, skip updating
            return True
    
    # 5. Flush changes
    note.flush()
    return True

def restore_field_content(note_id, field_name, content):
    """
    Restores the original content of a field and flushes the note.
    """
    from aqt import mw
    try:
        note = mw.col.get_note(note_id)
        if field_name in note:
            note[field_name] = content
            note.flush()
            return True
    except Exception as e:
        print(f"Error restoring note {note_id}: {e}")
    return False

class ConfigManager:
    def __init__(self):
        from aqt import mw
        self.mw = mw

    def get_all_config(self):
        return self.mw.addonManager.getConfig("anki_image_adder") or {}

    def get_note_type_config(self, model_name):
        config = self.get_all_config()
        return config.get("models", {}).get(model_name, {})

    def save_note_type_config(self, model_name, model_config):
        config = self.get_all_config()
        if "models" not in config:
            config["models"] = {}
        config["models"][model_name] = model_config
        self.mw.addonManager.writeConfig("anki_image_adder", config)

    def get_global_defaults(self):
        config = self.get_all_config()
        return {
            "search_suffix": config.get("search_suffix", ""),
            "image_width": config.get("image_width", 320),
            "max_height": config.get("max_height", 320)
        }
