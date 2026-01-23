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

def get_field_content(note_id, field_name):
    """
    Returns the cleaned text content of a field from a note ID.
    Cleans HTML tags and Cloze markers.
    """
    from aqt import mw
    try:
        note = mw.col.get_note(note_id)
    except Exception:
        return ""
        
    try:
        content = note[field_name]
    except KeyError:
        return ""

    # Clean HTML
    soup = BeautifulSoup(content, "html.parser")
    text = soup.get_text()

    # Clean Cloze markers {{c1::text}} or {{c1::text::hint}} -> text
    text = re.sub(r"\{\{c\d+::(.*?)(?::.*?)?\}\}", r"\1", text)
    # Clean other brackets just in case
    text = text.replace("{{", "").replace("}}", "")
    
    return text.strip()
