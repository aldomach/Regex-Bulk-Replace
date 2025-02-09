import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox, ttk
import re
import json

# Lista global donde se almacenan los bloques dinámicos.
blocks_list = []

# Variables globales para almacenar los contadores del último reemplazo.
last_normal_count = 0
last_regex_count = 0

# Identifica saltos de linea
def detect_line_breaks(text):
    if "\r\n" in text:
        return "\r\n"
    elif "\r" in text:
        return "\r"
    else:
        return "\n"
def update_status_bar(normal, regex, line_break_type="\\n"):
    """Update the status bar with the number of blocks, replacements, and line break type."""
    status_bar.config(
        text=f"Bloques: {len(blocks_list)} | Resultados Normales: {normal} | Resultados de Exp Regulares: {regex} | Tipo de salto: {repr(line_break_type)} | Aldo Machado"
    )

def invert_texts(pattern_entry, replacement_entry):
    """Intercambia el contenido de los campos patrón y reemplazo."""
    pat = pattern_entry.get()
    rep = replacement_entry.get()
    pattern_entry.delete(0, tk.END)
    pattern_entry.insert(0, rep)
    replacement_entry.delete(0, tk.END)
    replacement_entry.insert(0, pat)

def add_block():
    """Crea un nuevo bloque (módulo) y lo agrega al contenedor scrollable."""
    block_frame = tk.Frame(blocks_container_inner)
    block_frame.pack(fill=tk.X, pady=2)

    # Campo para el patrón.
    entry_pattern = tk.Entry(block_frame, width=30)
    entry_pattern.pack(side=tk.LEFT, padx=5)
    
    # Campo para el reemplazo.
    entry_replacement = tk.Entry(block_frame, width=30)
    # Botón para invertir el contenido de patrón y reemplazo.
    btn_invert = tk.Button(block_frame, text="Invertir", command=lambda: invert_texts(entry_pattern, entry_replacement))
    btn_invert.pack(side=tk.LEFT, padx=5)
    entry_replacement.pack(side=tk.LEFT, padx=5)
    
    # Checkbutton para modo Regex.
    var_regex = tk.BooleanVar(value=True)
    chk_regex = tk.Checkbutton(block_frame, text="Regex", variable=var_regex)
    chk_regex.pack(side=tk.LEFT, padx=5)
    
    # Checkbutton para la distinción de mayúsculas.
    var_match_case = tk.BooleanVar(value=False)
    chk_match_case = tk.Checkbutton(block_frame, text="Match case", variable=var_match_case)
    chk_match_case.pack(side=tk.LEFT, padx=5)
    
    # Checkbutton para trabajar con palabra completa.
    var_whole = tk.BooleanVar(value=False)
    chk_whole = tk.Checkbutton(block_frame, text="Palabra completa", variable=var_whole)
    chk_whole.pack(side=tk.LEFT, padx=5)
    
    # Diccionario que define el bloque.
    block = {
        "frame": block_frame,
        "pattern": entry_pattern,
        "replacement": entry_replacement,
        "var": var_regex,
        "var_match_case": var_match_case,
        "var_whole": var_whole
    }
    
    # Botón para eliminar el bloque.
    btn_remove = tk.Button(block_frame, text="Eliminar", command=lambda b=block: remove_block(b))
    btn_remove.pack(side=tk.LEFT, padx=5)
    
    blocks_list.append(block)
    update_status_bar(last_normal_count, last_regex_count)

def remove_block(block):
    """Elimina el bloque recibido y lo quita de la lista."""
    block["frame"].destroy()
    if block in blocks_list:
        blocks_list.remove(block)
    update_status_bar(last_normal_count, last_regex_count)

def aplicar_reemplazos():
    """Apply replacements to the input text."""
    global last_normal_count, last_regex_count
    texto = texto_entrada.get("1.0", tk.END).strip()
    normal_count = 0
    regex_count = 0

    # Detect line break type
    line_break = detect_line_breaks(texto)

    for idx, block in enumerate(blocks_list, start=1):
        patron = block["pattern"].get().strip()
        reemplazo = block["replacement"].get().strip()
        usar_regex = block["var"].get()
        match_case = block["var_match_case"].get()
        whole_word = block["var_whole"].get()

        if patron:
            flags = 0
            if not match_case:
                flags |= re.IGNORECASE

            if usar_regex:
                try:
                    texto, count = re.subn(patron, reemplazo, texto, flags=flags)
                    regex_count += count
                except re.error as e:
                    messagebox.showerror("Error de Regex", f"Error en el bloque {idx} (regex): {e}")
            else:
                if whole_word:
                    patron_mod = r"\b" + re.escape(patron) + r"\b"
                else:
                    patron_mod = re.escape(patron)
                texto, count = re.subn(patron_mod, reemplazo, texto, flags=flags)
                normal_count += count

    # Replace line breaks
    opcion_salto = var_salto.get()
    if opcion_salto == "Doble salto de línea → Uno":
        texto, count2 = re.subn(f'{line_break}{{2,}}', line_break, texto)
        normal_count += count2
    elif opcion_salto == "Triple salto de línea → Doble":
        texto, count2 = re.subn(f'{line_break}{{3,}}', f'{line_break}{line_break}', texto)
        normal_count += count2

    texto_salida.delete("1.0", tk.END)
    texto_salida.insert(tk.END, texto)

    last_normal_count = normal_count
    last_regex_count = regex_count
    update_status_bar(last_normal_count, last_regex_count, line_break)
    

    # Reemplazo de saltos de línea según la opción elegida en el ComboBox
    opcion_salto = var_salto.get()
    if opcion_salto == "Doble salto de línea → Uno":
        texto, count2 = re.subn(r'\n{2,}', '\n', texto)
        normal_count += count2
    elif opcion_salto == "Triple salto de línea → Doble":
        texto, count2 = re.subn(r'\n{3,}', '\n\n', texto)
        normal_count += count2

    texto_salida.delete("1.0", tk.END)
    texto_salida.insert(tk.END, texto)

    last_normal_count = normal_count
    last_regex_count = regex_count
    update_status_bar(last_normal_count, last_regex_count)

def limpiar():
    """Borra el contenido de las áreas de texto (original y resultante) luego de confirmar."""
    if messagebox.askyesno("Confirmar limpieza", "¿Está seguro de que desea limpiar el contenido?"):
        texto_entrada.delete("1.0", tk.END)
        texto_salida.config(state=tk.NORMAL)
        texto_salida.delete("1.0", tk.END)
        texto_salida.config(state=tk.NORMAL)

def copiar_texto_resultante():
    """Copia el contenido del área de texto resultante al portapapeles."""
    resultado = texto_salida.get("1.0", tk.END).strip()
    if resultado:
        root.clipboard_clear()
        root.clipboard_append(resultado)

def reemplazar_y_copiar():
    """Aplica los reemplazos y luego copia el resultado."""
    aplicar_reemplazos()
    copiar_texto_resultante()

def guardar_config():
    """Guarda la configuración actual en un archivo JSON."""
    config = {
        "salto_opcion": var_salto.get(),
        "reemplazos": []
    }
    for block in blocks_list:
        config["reemplazos"].append({
            "patron": block["pattern"].get(),
            "reemplazo": block["replacement"].get(),
            "usar_regex": block["var"].get(),
            "match_case": block["var_match_case"].get(),
            "palabra_completa": block["var_whole"].get()
        })
    archivo = filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("JSON", "*.json")],
        title="Guardar configuración"
    )
    if archivo:
        try:
            with open(archivo, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error al guardar: {e}")

def has_configuration():
    """Retorna True si existe alguna configuración cargada."""
    if var_salto.get() != "Ninguno":
        return True
    for block in blocks_list:
        if block["pattern"].get().strip() or block["replacement"].get().strip():
            return True
    return False

def abrir_config():
    """
    Carga la configuración desde un archivo JSON.
    Si ya existe una configuración cargada, pregunta al usuario con tres opciones:
      - Sí: Guardar la configuración actual y continuar.
      - No: Descartar los cambios actuales y continuar.
      - Cancelar: Cancelar la operación.
    """
    if has_configuration():
        respuesta = messagebox.askyesnocancel(
            "Guardar configuración",
            "Ya tiene configuraciones cargadas. ¿Desea guardarlas antes de abrir otra?\n\n"
            "Sí: Guardar la configuración actual y continuar.\n"
            "No: No guardar y continuar.\n"
            "Cancelar: Cancelar la operación."
        )
        if respuesta is None:
            return
        elif respuesta:
            guardar_config()
    archivo = filedialog.askopenfilename(
        defaultextension=".json",
        filetypes=[("JSON", "*.json")],
        title="Abrir configuración"
    )
    if archivo:
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                config = json.load(f)
            var_salto.set(config.get("salto_opcion", "Ninguno"))
            for block in blocks_list[:]:
                remove_block(block)
            reemplazos = config.get("reemplazos", [])
            for item in reemplazos:
                add_block()
                block = blocks_list[-1]
                block["pattern"].delete(0, tk.END)
                block["pattern"].insert(0, item.get("patron", ""))
                block["replacement"].delete(0, tk.END)
                block["replacement"].insert(0, item.get("reemplazo", ""))
                block["var"].set(item.get("usar_regex", True))
                block["var_match_case"].set(item.get("match_case", True))
                block["var_whole"].set(item.get("palabra_completa", False))
        except Exception as e:
            print(f"Error al abrir: {e}")

# --- NUEVAS FUNCIONES PARA ARCHIVOS DE TEXTO ---

def abrir_archivo():
    """
    Abre un archivo de texto plano y carga su contenido en el campo de texto original.
    Si ya hay contenido en el área de texto, se advierte al usuario que se reemplazará.
    """
    if texto_entrada.get("1.0", tk.END).strip():
        respuesta = messagebox.askyesno("Advertencia", 
            "Abrir un archivo reemplazará el contenido actual. ¿Desea continuar?")
        if not respuesta:
            return
    archivo = filedialog.askopenfilename(
        defaultextension=".txt",
        filetypes=[("Archivos de texto", "*.txt")],
        title="Abrir archivo de texto"
    )
    if archivo:
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                contenido = f.read()
            texto_entrada.delete("1.0", tk.END)
            texto_entrada.insert(tk.END, contenido)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el archivo: {e}")

def guardar_texto_resultante():
    """
    Guarda el contenido del área de texto resultante en un archivo de texto (.txt).
    Se advierte si no hay contenido para guardar.
    """
    resultado = texto_salida.get("1.0", tk.END).strip()
    if not resultado:
        messagebox.showwarning("Advertencia", "No hay texto resultante para guardar.")
        return
    archivo = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Archivos de texto", "*.txt")],
        title="Guardar texto resultante"
    )
    if archivo:
        try:
            with open(archivo, "w", encoding="utf-8") as f:
                f.write(resultado)
            messagebox.showinfo("Éxito", "El archivo se guardó correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el archivo: {e}")

# --------------------
# INTERFAZ GRÁFICA
# --------------------
root = tk.Tk()
root.title("Regex Bulk Replace")
root.geometry("880x682")
root.minsize(880, 682)

root.grid_columnconfigure(0, weight=1)

# --- Frame que enmarca desde "Encabezado para los Bloques" hasta el ComboBox ---
frame_encuadre = tk.Frame(root, bd=2, relief="groove")
frame_encuadre.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
frame_encuadre.grid_columnconfigure(0, weight=1)

# Encabezado para los Bloques (dentro de frame_encuadre)
blocks_header = tk.Frame(frame_encuadre)
blocks_header.grid(row=0, column=0, padx=10, pady=2, sticky="w")
label_patron = tk.Label(blocks_header, text="Patrón", width=35, anchor="w")
label_patron.pack(side=tk.LEFT, padx=5)
label_reemplazo = tk.Label(blocks_header, text="Reemplazo", width=25, anchor="w")
label_reemplazo.pack(side=tk.LEFT, padx=5)
label_regex = tk.Label(blocks_header, text="Exp Regex", width=9, anchor="w")
label_regex.pack(side=tk.LEFT, padx=5)
label_match_case = tk.Label(blocks_header, text="Match case", width=10, anchor="w")
label_match_case.pack(side=tk.LEFT, padx=5)
label_whole = tk.Label(blocks_header, text="Palabra completa", width=15, anchor="w")
label_whole.pack(side=tk.LEFT, padx=5)
label_accion = tk.Label(blocks_header, text="Acción", width=10, anchor="w")
label_accion.pack(side=tk.LEFT, padx=5)

# Frame que contiene la lista dinámica de bloques (dentro de frame_encuadre)
blocks_frame_border = tk.Frame(frame_encuadre, bg="#888")
blocks_frame_border.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
blocks_frame = tk.Frame(blocks_frame_border, bg="#f4f4f4", padx=2, pady=2)
blocks_frame.pack(expand=True, fill="both")
blocks_canvas = tk.Canvas(blocks_frame, height=120)
blocks_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
blocks_scrollbar = tk.Scrollbar(blocks_frame, orient="vertical", command=blocks_canvas.yview)
blocks_scrollbar.pack(side=tk.RIGHT, fill="y")
blocks_canvas.configure(yscrollcommand=blocks_scrollbar.set)
blocks_container_inner = tk.Frame(blocks_canvas)
blocks_canvas.create_window((0, 0), window=blocks_container_inner, anchor="nw")
def on_configure(event):
    blocks_canvas.configure(scrollregion=blocks_canvas.bbox("all"))
blocks_container_inner.bind("<Configure>", on_configure)


# Botón Agregar Bloque (dentro de frame_encuadre)
btn_agregar = tk.Button(frame_encuadre, text="Agregar Bloque", command=add_block)
btn_agregar.grid(row=2, column=0, padx=10, pady=5, sticky="w")

# ComboBox para selección de reemplazo de saltos de línea (dentro de frame_encuadre)
frame_salto = tk.Frame(frame_encuadre)
frame_salto.grid(row=3, column=0, columnspan=3, padx=10, pady=5, sticky="w")
label_salto = tk.Label(frame_salto, text="Reemplazar saltos de línea:")
label_salto.pack(side=tk.LEFT)
var_salto = tk.StringVar(value="Ninguno")
opciones_salto = ["Ninguno", "Doble salto de línea → Uno", "Triple salto de línea → Doble"]
combo_salto = ttk.Combobox(frame_salto, textvariable=var_salto, values=opciones_salto, state="readonly", width=30)
combo_salto.pack(side=tk.LEFT, padx=5)

# --- Botones de Configuración (fuera de frame_encuadre, en fila siguiente) ---
frame_botonera = tk.Frame(frame_encuadre)
frame_botonera.grid(row=4, column=0, columnspan=3, padx=10, pady=10, sticky="w")
btn_abrir = tk.Button(frame_botonera, text="Abrir Config", command=abrir_config)
btn_abrir.pack(side=tk.LEFT, padx=5)
btn_guardar = tk.Button(frame_botonera, text="Guardar Config", command=guardar_config)
btn_guardar.pack(side=tk.LEFT, padx=5)

# --- Área de Texto Original y botones (fila 2) ---
frame_texto_original = tk.Frame(root)
frame_texto_original.grid(row=2, column=0, columnspan=3, padx=10, pady=5, sticky="w")
etiqueta_entrada = tk.Label(frame_texto_original, text="Texto Original")
etiqueta_entrada.pack(side=tk.LEFT)
btn_abrir_archivo = tk.Button(frame_texto_original, text="Abrir Archivo", command=abrir_archivo)
btn_abrir_archivo.pack(side=tk.LEFT, padx=10)
btn_limpiar = tk.Button(frame_texto_original, text="Borrar", command=limpiar)
btn_limpiar.pack(side=tk.LEFT, padx=10)

# Espacio de 280px entre "Abrir Archivo" y "Reemplazar"
espacio = tk.Frame(frame_texto_original, width=280)
espacio.pack(side=tk.LEFT)
espacio.pack_propagate(False)

btn_reemplazar = tk.Button(frame_texto_original, text="Reemplazar", command=aplicar_reemplazos)
btn_reemplazar.pack(side=tk.LEFT, padx=10)
btn_copiar = tk.Button(frame_texto_original, text="Copiar", command=copiar_texto_resultante)
btn_copiar.pack(side=tk.LEFT, padx=10)
btn_reemplazar_y_copiar = tk.Button(frame_texto_original, text="Reemplazar y Copiar", command=reemplazar_y_copiar)
btn_reemplazar_y_copiar.pack(side=tk.LEFT, padx=10)

# --- Área de Texto Original ---
texto_entrada = scrolledtext.ScrolledText(root, height=8, width=20)
texto_entrada.grid(row=3, column=0, columnspan=3, padx=10, pady=5, sticky="nsew")

# --- Contenedor para la etiqueta y los botones del Resultado ---
frame_resultado = tk.Frame(root)
frame_resultado.grid(row=4, column=0, padx=10, pady=5, sticky="w")
etiqueta_salida = tk.Label(frame_resultado, text="Texto Resultante")
etiqueta_salida.pack(side=tk.LEFT, padx=(0, 10))
btn_copiar_resultado = tk.Button(frame_resultado, text="Copiar", command=copiar_texto_resultante)
btn_copiar_resultado.pack(side=tk.LEFT, padx=(0, 10))
btn_guardar_resultado = tk.Button(frame_resultado, text="Guardar Resultado", command=guardar_texto_resultante)
btn_guardar_resultado.pack(side=tk.LEFT)

# --- Área de Texto Resultante ---
texto_salida = scrolledtext.ScrolledText(root, height=8, width=80)
texto_salida.grid(row=5, column=0, columnspan=3, padx=10, pady=5, sticky="nsew")

# --- Barra de Estado ---
status_bar = tk.Label(root, text="Bloques: 0 | Resultados Normales: 0 | Resultados de Exp Regulares: 0", bd=1, relief=tk.SUNKEN, anchor=tk.W)
status_bar.grid(row=6, column=0, columnspan=3, padx=10, pady=5, sticky="ew")

# --- Crear 4 bloques por defecto ---
for i in range(4):
    add_block()

root.mainloop()
