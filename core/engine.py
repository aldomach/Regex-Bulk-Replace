import re

def apply_replacements(text, blocks, remove_double_newlines=False):
    """
    Aplica todos los reemplazamientos al texto dado.
    
    :param text: El texto original
    :param blocks: Una lista de diccionarios o objetos que contengan:
        - pattern: str
        - replacement: str
        - is_regex: bool
        - match_case: bool
        - whole_word: bool
    :param remove_double_newlines: bool
    :return: (new_text, normal_count, regex_count, errors)
        - errors: lista de tuplas (idx, error_msg)
    """
    normal_count = 0
    regex_count = 0
    errors = []
    
    current_text = text
    
    for idx, block in enumerate(blocks, start=1):
        pattern = block['pattern']
        replacement = block['replacement'] # No usar .strip() aquí por requerimiento
        is_regex = block['is_regex']
        match_case = block['match_case']
        whole_word = block['whole_word']
        
        if not pattern:
            continue
            
        flags = 0
        if not match_case:
            flags |= re.IGNORECASE
            
        try:
            if is_regex:
                # En modo regex, se permite que re.subn interprete el reemplazo (ej. \1)
                new_text, count = re.subn(pattern, replacement, current_text, flags=flags)
                regex_count += count
                current_text = new_text
            else:
                # En modo normal, usamos un lambda para tratar el reemplazo como literal
                # Bug fix #2: Usar lambda para evitar interpretación de backslashes
                if whole_word:
                    pattern_mod = r"\b" + re.escape(pattern) + r"\b"
                else:
                    pattern_mod = re.escape(pattern)
                
                new_text, count = re.subn(pattern_mod, lambda m: replacement, current_text, flags=flags)
                normal_count += count
                current_text = new_text
        except re.error as e:
            errors.append((idx, str(e)))
            
    if remove_double_newlines:
        current_text, count = re.subn(r'\n{2,}', '\n', current_text)
        normal_count += count
        
    return current_text, normal_count, regex_count, errors
