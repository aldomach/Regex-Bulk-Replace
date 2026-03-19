import tkinter as tk

class ReplacementBlock(tk.Frame):
    """
    Clase que representa un bloque de reemplazo individual.
    Encapsula los widgets y variables de configuración.
    """
    def __init__(self, parent, block_index, on_remove_callback, on_move_up=None, on_move_down=None):
        super().__init__(parent)
        self.block_index = block_index
        self.on_remove_callback = on_remove_callback
        self.on_move_up = on_move_up
        self.on_move_down = on_move_down
        
        # Variables de configuración
        self.var_regex = tk.BooleanVar(value=True)
        self.var_match_case = tk.BooleanVar(value=True)
        self.var_whole = tk.BooleanVar(value=False)
        
        self.setup_ui()
        
    def setup_ui(self):
        # Número de bloque
        self.lbl_index = tk.Label(self, text=f"#{self.block_index}", width=3)
        self.lbl_index.pack(side=tk.LEFT, padx=5)
        
        # Botones de orden
        self.btn_up = tk.Button(self, text="\u25b2", command=self.on_move_up)
        self.btn_up.pack(side=tk.LEFT, padx=1)
        self.btn_down = tk.Button(self, text="\u25bc", command=self.on_move_down)
        self.btn_down.pack(side=tk.LEFT, padx=1)
        
        # Campo patrón
        self.entry_pattern = tk.Entry(self, width=30)
        self.entry_pattern.pack(side=tk.LEFT, padx=5)
        
        # Botón invertir
        self.btn_invert = tk.Button(self, text="\u21c4 Invertir", command=self.invert_texts)
        self.btn_invert.pack(side=tk.LEFT, padx=2)
        
        # Campo reemplazo
        self.entry_replacement = tk.Entry(self, width=30)
        self.entry_replacement.pack(side=tk.LEFT, padx=5)
        
        # Checkbox Regex
        self.chk_regex = tk.Checkbutton(self, text="Regex", variable=self.var_regex, command=self.toggle_regex)
        self.chk_regex.pack(side=tk.LEFT, padx=5)
        
        # Checkbox Match case
        self.chk_match_case = tk.Checkbutton(self, text="Match case", variable=self.var_match_case)
        self.chk_match_case.pack(side=tk.LEFT, padx=5)
        
        # Checkbox Palabra completa
        self.chk_whole = tk.Checkbutton(self, text="Palabra completa", variable=self.var_whole)
        self.chk_whole.pack(side=tk.LEFT, padx=5)
        
        # Botón eliminar
        self.btn_remove = tk.Button(self, text="Eliminar", command=lambda: self.on_remove_callback(self))
        self.btn_remove.pack(side=tk.LEFT, padx=5)
        
        # Asegurarse de que el estado inicial de chk_whole sea consistente
        self.toggle_regex()
        
    def invert_texts(self):
        pat = self.entry_pattern.get()
        rep = self.entry_replacement.get()
        self.entry_pattern.delete(0, tk.END)
        self.entry_pattern.insert(0, rep)
        self.entry_replacement.delete(0, tk.END)
        self.entry_replacement.insert(0, pat)
        
    def toggle_regex(self):
        """Deshabilita 'Palabra completa' cuando el modo regex está activo."""
        if self.var_regex.get():
            self.chk_whole.config(state=tk.DISABLED)
            # visualmente se mantiene el valor pero se ignora en la lógica
        else:
            self.chk_whole.config(state=tk.NORMAL)
            
    def set_error_visual(self, is_error=True):
        """Marca con color de fondo las entradas de texto en caso de error."""
        color = "#fdd" if is_error else "white"
        self.entry_pattern.config(bg=color)
            
    def get_data(self):
        return {
            'pattern': self.entry_pattern.get(),
            'replacement': self.entry_replacement.get(), # Sin .strip() para permitir espacios
            'is_regex': self.var_regex.get(),
            'match_case': self.var_match_case.get(),
            'whole_word': self.var_whole.get()
        }
    
    def set_data(self, data):
        self.entry_pattern.delete(0, tk.END)
        self.entry_pattern.insert(0, data.get('patron', ''))
        self.entry_replacement.delete(0, tk.END)
        self.entry_replacement.insert(0, data.get('reemplazo', ''))
        self.var_regex.set(data.get('usar_regex', True))
        self.var_match_case.set(data.get('match_case', True))
        self.var_whole.set(data.get('palabra_completa', False))
        self.toggle_regex()
        
    def update_index(self, new_index):
        self.block_index = new_index
        self.lbl_index.config(text=f"#{self.block_index}")
