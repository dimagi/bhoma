def safe_index(object, keys):
    """Safely index a document, returning None if the value isn't found."""
    if len(keys) == 1:
        if hasattr(object, keys[0]): return getattr(object, keys[0])
        else:                        return None
    else:
        return safe_index(safe_index(object, [keys[0]]), keys[1:])
    
