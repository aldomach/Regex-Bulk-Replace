import json
from tkinter import filedialog, messagebox

def save_config(blocks, remove_double_newlines):
    \"\"\"Guarda la configuración actual en un archivo JSON.\"\"\"
    config = {
        \"reemplazar_doble_salto\": remove_double_newlines,
        \"reemplazos\": []
    }
    for block in blocks:
        config[\"reemplazos\"].append({
            \"patron\": block.get_data()['pattern'],
            \"reemplazo\": block.get_data()['replacement'],
            \"usar_regex\": block.get_data()['is_regex'],
            \"match_case\": block.get_data()['match_case'],
            \"palabra_completa\": block.get_data()['whole_word']
        })
    archivo = filedialog.asksaveasfilename(
        defaultextension=\".json\",
        filetypes=[(\"JSON\", \"*.json\")],
        title=\"Guardar configuración\"
    )
    if archivo:
        try:
            with open(archivo, \"w\", encoding=\"utf-8\") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            # Bug fix: mostrar errores al guardar configuración con messagebox
            messagebox.showerror(\"Error al guardar\", f\"{e}\")
    return False

def load_config(file_path):
    \"\"\"Carga la configuración desde un archivo JSON.\"\"\"
    try:
        with open(file_path, \"r\", encoding=\"utf-8\") as f:
            config = json.load(f)
        return config
    except Exception as e:
        messagebox.showerror(\"Error al abrir\", f\"{e}\")
        return None
