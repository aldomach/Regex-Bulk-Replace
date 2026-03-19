import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
from .replacement_block import ReplacementBlock
from core.engine import apply_replacements
from core.config_manager import save_config, load_config

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title(\"Herramienta de Reemplazos - Modular\")
        self.blocks_list = []
        self.last_normal_count = 0
        self.last_regex_count = 0
        
        self.setup_ui()
        
    def setup_ui(self):
        # Configurar grid de la ventana principal
        self.root.grid_rowconfigure(6, weight=1)   # Texto Original
        self.root.grid_rowconfigure(8, weight=1)   # Texto Resultante
        self.root.grid_columnconfigure(0, weight=1)
        
        # --- Encabezado para los Bloques ---
        # No usamos anchos fijos, usamos fill o expand
        blocks_header = tk.Frame(self.root)
        blocks_header.grid(row=0, column=0, columnspan=3, padx=10, pady=2, sticky=\"w\")
        
        # Estos anchos son orientativos para alinear
        headers = [(\"#\", 4), (\"Orden\", 4), (\"Patrón\", 28), (\"\", 7), (\"Reemplazo\", 25), 
                   (\"Exp Regex\", 9), (\"Match case\", 10), (\"Palabra completa\", 15), (\"Acción\", 10)]
        for text, width in headers:
            tk.Label(blocks_header, text=text, width=width, anchor=\"w\").pack(side=tk.LEFT, padx=3)

        # --- Contenedor de Bloques con scroll ---
        blocks_frame_border = tk.Frame(self.root, bg=\"#888\")
        blocks_frame_border.grid(row=1, column=0, columnspan=3, padx=10, pady=5, sticky=\"nsew\")
        
        blocks_frame = tk.Frame(blocks_frame_border, bg=\"#f4f4f4\", padx=2, pady=2)
        blocks_frame.pack(expand=True, fill=\"both\")
        
        self.blocks_canvas = tk.Canvas(blocks_frame, height=140)
        self.blocks_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.blocks_scrollbar = tk.Scrollbar(blocks_frame, orient=\"vertical\", command=self.blocks_canvas.yview)
        self.blocks_scrollbar.pack(side=tk.RIGHT, fill=\"y\")
        
        self.blocks_canvas.configure(yscrollcommand=self.blocks_scrollbar.set)
        
        self.blocks_container_inner = tk.Frame(self.blocks_canvas)
        self.blocks_canvas.create_window((0, 0), window=self.blocks_container_inner, anchor=\"nw\")
        
        self.blocks_container_inner.bind(\"<Configure>\", 
            lambda e: self.blocks_canvas.configure(scrollregion=self.blocks_canvas.bbox(\"all\")))
        
        # --- NUEVO: Capturar mousewheel sobre el canvas ---
        self.blocks_canvas.bind_all(\"<MouseWheel>\", self._on_mousewheel)

        # --- Botones superiroes ---
        btn_agregar = tk.Button(self.root, text=\"+ Agregar Bloque\", command=self.add_block)
        btn_agregar.grid(row=2, column=0, padx=10, pady=5, sticky=\"w\")
        
        self.var_doble_salto = tk.BooleanVar(value=False)
        chk_doble_salto = tk.Checkbutton(self.root, text=\"Reemplazar doble salto de línea por uno solo\", 
                                       variable=self.var_doble_salto)
        chk_doble_salto.grid(row=3, column=0, columnspan=3, padx=10, pady=5, sticky=\"w\")

        # --- Area de botones con layout adaptativo ---
        frame_botonera = tk.Frame(self.root)
        frame_botonera.grid(row=4, column=0, columnspan=3, padx=10, pady=10, sticky=\"ew\")
        
        # Botones de configuración a la izquierda
        self.btn_abrir_config = tk.Button(frame_botonera, text=\"Abrir Config\", command=self.open_config)
        self.btn_abrir_config.pack(side=tk.LEFT, padx=5)
        self.btn_guardar_config = tk.Button(frame_botonera, text=\"Guardar Config\", command=self.save_config_action)
        self.btn_guardar_config.pack(side=tk.LEFT, padx=5)
        
        # Frame flexible para empujar el resto a la derecha
        tk.Frame(frame_botonera).pack(side=tk.LEFT, expand=True)
        
        # Botones de acción a la derecha
        self.btn_reemplazar = tk.Button(frame_botonera, text=\"REEMPLAZAR (Ctrl+Enter)\", command=self.aplicar_reemplazos, font=(\"\", 9, \"bold\"))
        self.btn_reemplazar.pack(side=tk.LEFT, padx=5)
        self.btn_copiar = tk.Button(frame_botonera, text=\"Copiar\", command=self.copiar_texto_resultante)
        self.btn_copiar.pack(side=tk.LEFT, padx=5)
        self.btn_reemplazar_y_copiar = tk.Button(frame_botonera, text=\"Reemplazar y Copiar\", command=self.reemplazar_y_copiar)
        self.btn_reemplazar_y_copiar.pack(side=tk.LEFT, padx=5)

        # --- Área de Texto Original ---
        frame_texto_original = tk.Frame(self.root)
        frame_texto_original.grid(row=5, column=0, columnspan=2, padx=10, pady=5, sticky=\"w\")
        tk.Label(frame_texto_original, text=\"Texto Original\").pack(side=tk.LEFT)
        
        tk.Button(frame_texto_original, text=\"Abrir Archivo\", command=self.abrir_archivo).pack(side=tk.LEFT, padx=10)
        tk.Button(frame_texto_original, text=\"Borrar\", command=self.limpiar).pack(side=tk.LEFT, padx=10)
        
        self.texto_entrada = scrolledtext.ScrolledText(self.root, height=15, width=80)
        self.texto_entrada.grid(row=6, column=0, columnspan=3, padx=10, pady=5, sticky=\"nsew\")

        # --- Área de Texto Resultante ---
        frame_resultado = tk.Frame(self.root)
        frame_resultado.grid(row=7, column=0, padx=10, pady=5, sticky=\"w\")
        tk.Label(frame_resultado, text=\"Texto Resultante\").pack(side=tk.LEFT, padx=(0, 10))
        tk.Button(frame_resultado, text=\"Guardar Resultado\", command=self.guardar_texto_resultante).pack(side=tk.LEFT)
        
        self.texto_salida = scrolledtext.ScrolledText(self.root, height=15, width=80, state=tk.DISABLED)
        self.texto_salida.grid(row=8, column=0, columnspan=3, padx=10, pady=5, sticky=\"nsew\")

        # --- Barra de Estado ---
        self.status_bar = tk.Label(self.root, text=\"Bloques: 0 | Resultados Normales: 0 | Resultados de Exp Regulares: 0\", 
                                  bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=9, column=0, columnspan=3, sticky=\"we\", padx=10, pady=(0,5))
        
        # Shortcuts
        self.root.bind('<Control-Return>', lambda e: self.aplicar_reemplazos())

    def _on_mousewheel(self, event):
        \"\"\"Permite el scroll del mousewheel sobre el canvas de bloques.\"\"\"
        self.blocks_canvas.yview_scroll(int(-1*(event.delta/120)), \"units\")

    def add_block(self, data=None):
        idx = len(self.blocks_list) + 1
        block = ReplacementBlock(self.blocks_container_inner, idx, self.remove_block, 
                                 on_move_up=lambda: self.move_block_up(block),
                                 on_move_down=lambda: self.move_block_down(block))
        block.pack(fill=tk.X, pady=2)
        if data:
            block.set_data(data)
        self.blocks_list.append(block)
        self.update_status_bar()
        
    def remove_block(self, block):
        block.destroy()
        if block in self.blocks_list:
            self.blocks_list.remove(block)
        self.reorder_blocks()
        self.update_status_bar()
        
    def reorder_blocks(self):
        \"\"\"Actualiza los números de bloque después de borrar o mover.\"\"\"
        for i, block in enumerate(self.blocks_list, start=1):
            block.update_index(i)
            # Volver a empaquetar en el orden correcto
            block.pack_forget()
            block.pack(fill=tk.X, pady=2)
            
    def move_block_up(self, block):
        idx = self.blocks_list.index(block)
        if idx > 0:
            self.blocks_list[idx], self.blocks_list[idx-1] = self.blocks_list[idx-1], self.blocks_list[idx]
            self.reorder_blocks()
            
    def move_block_down(self, block):
        idx = self.blocks_list.index(block)
        if idx < len(self.blocks_list) - 1:
            self.blocks_list[idx], self.blocks_list[idx+1] = self.blocks_list[idx+1], self.blocks_list[idx]
            self.reorder_blocks()

    def aplicar_reemplazos(self):
        text = self.texto_entrada.get(\"1.0\", tk.END).strip()
        if not text:
            return
            
        # Limpiar marcas de error anteriores
        for block in self.blocks_list:
            block.set_error_visual(False)
            
        blocks_data = [block.get_data() for block in self.blocks_list]
        new_text, n_count, r_count, errors = apply_replacements(
            text, blocks_data, self.var_doble_salto.get()
        )
        
        # Mostrar errores
        if errors:
            error_msg = \"Errores de Expresión Regular:\n\n\"
            for idx, msg in errors:
                error_msg += f\"Bloque #{idx}: {msg}\n\"
                # Bug fix: visual feedback in block
                self.blocks_list[idx-1].set_error_visual(True)
            messagebox.showerror(\"Error de Regex\", error_msg)
            
        self.texto_salida.config(state=tk.NORMAL)
        self.texto_salida.delete(\"1.0\", tk.END)
        self.texto_salida.insert(tk.END, new_text)
        self.texto_salida.config(state=tk.DISABLED)
        
        self.last_normal_count = n_count
        self.last_regex_count = r_count
        self.update_status_bar()

    def update_status_bar(self):
        self.status_bar.config(
            text=f\"Bloques: {len(self.blocks_list)} | Resultados Normales: {self.last_normal_count} | Resultados Regex: {self.last_regex_count} | Aldo Machado\"
        )

    def limpiar(self):
        \"\"\"Bug fix #5: Limpiar áreas de texto y resetear la barra de estado.\"\"\"
        if messagebox.askyesno(\"Confirmar limpieza\", \"¿Está seguro de que desea limpiar el contenido?\"):
            self.texto_entrada.delete(\"1.0\", tk.END)
            self.texto_salida.config(state=tk.NORMAL)
            self.texto_salida.delete(\"1.0\", tk.END)
            self.texto_salida.config(state=tk.DISABLED)
            self.last_normal_count = 0
            self.last_regex_count = 0
            self.update_status_bar()

    def copiar_texto_resultante(self):
        resultado = self.texto_salida.get(\"1.0\", tk.END).strip()
        if resultado:
            self.root.clipboard_clear()
            self.root.clipboard_append(resultado)
            
    def reemplazar_y_copiar(self):
        self.aplicar_reemplazos()
        self.copiar_texto_resultante()

    def save_config_action(self):
        save_config(self.blocks_list, self.var_doble_salto.get())
        
    def open_config(self):
        # Lógica de abrir confirmando
        if self.has_config():
            resp = messagebox.askyesnocancel(\"Configuración cargada\", 
                \"¿Desea guardar los cambios actuales antes de abrir otra?\")
            if resp is None: return
            if resp: self.save_config_action()
            
        archivo = filedialog.askopenfilename(defaultextension=\".json\", 
                                           filetypes=[(\"JSON\", \"*.json\")])
        if archivo:
            config = load_config(archivo)
            if config:
                self.var_doble_salto.set(config.get(\"reemplazar_doble_salto\", False))
                # Limpiar actuales
                for block in self.blocks_list[:]:
                    self.remove_block(block)
                # Agregar nuevos
                for item in config.get(\"reemplazos\", []):
                    self.add_block(item)

    def has_config(self):
        return any(b.get_data()['pattern'] for b in self.blocks_list) or self.var_doble_salto.get()

    def abrir_archivo(self):
        if self.texto_entrada.get(\"1.0\", tk.END).strip():
            if not messagebox.askyesno(\"Advertencia\", \"Se reemplazará el contenido. ¿Continuar?\"):
                return
        archivo = filedialog.askopenfilename(filetypes=[(\"Texto\", \"*.txt\"), (\"Todos\", \"*.*\")])
        if archivo:
            try:
                with open(archivo, \"r\", encoding=\"utf-8\") as f:
                    self.texto_entrada.delete(\"1.0\", tk.END)
                    self.texto_entrada.insert(tk.END, f.read())
            except Exception as e:
                messagebox.showerror(\"Error\", f\"No se pudo abrir: {e}\")

    def guardar_texto_resultante(self):
        resultado = self.texto_salida.get(\"1.0\", tk.END).strip()
        if not resultado:
            messagebox.showwarning(\"Advertencia\", \"No hay resultado.\")
            return
        archivo = filedialog.asksaveasfilename(defaultextension=\".txt\")
        if archivo:
            try:
                with open(archivo, \"w\", encoding=\"utf-8\") as f:
                    f.write(resultado)
                messagebox.showinfo(\"Éxito\", \"Guardado.\")
            except Exception as e:
                messagebox.showerror(\"Error\", f\"{e}\")
