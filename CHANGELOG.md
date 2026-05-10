# CHANGELOG — Regex Bulk Replace

Herramienta de reemplazos de texto mediante expresiones regulares (o literales), con interfaz gráfica en Python/Tkinter (y port experimental a PySide6/Qt).

---

## [qt] — Port experimental a PySide6/Qt
_2026-04-24_

### Nuevo
- Interfaz completamente portada a **PySide6** (`QApplication`, estilo Fusion).
- Mantiene la misma arquitectura modular (`core/`, `ui/`, `utils/`) de la serie v2+.
- Incluye `template_manager` y `templates.json`.
- Punto de entrada con `sys.exit(app.exec())`.

---

## [v6] — Encoding-aware en DiffPanel
_2026-04-24_

### Cambiado
- `DiffPanel` acepta el parámetro `encoding_getter` (callback) para conocer la codificación activa al momento de mostrar el diff.
- Corrección menor en la instanciación de `DiffPanel` desde `MainWindow`.

---

## [v5] — Sistema de plantillas
_2026-04-23_

### Nuevo
- Nuevo módulo `utils/template_manager.py`: carga, guarda y gestiona **plantillas** desde un archivo JSON externo (`templates.json`).
- Una plantilla es un grupo de `ReplaceBlock` con nombre y descripción, reutilizable entre sesiones.
- `templates.json` incluido junto al ejecutable como archivo de plantillas por defecto.

---

## [v4] — Panel de diff (comparación antes/después)
_2026-04-23_

### Nuevo
- Nuevo módulo `ui/diff_panel.py`: panel de previsualización del modo simulación.
  - Lista de archivos con cambios a la izquierda.
  - Comparador lado a lado (antes / después) con resaltado de diferencias en color (verde = líneas nuevas, rojo = líneas eliminadas).
  - Estadística rápida por archivo.
- `FileProcessResult` ahora almacena `original_text` para alimentar el diff panel.

### Cambiado
- `BatchResult` y `FileProcessResult` actualizados para soportar el flujo de simulación con diff.

---

## [v3] — Menú, encodings y cancelación
_2026-04-23_

### Nuevo
- Barra de menú (`_build_menu`) con accesos rápidos a acciones principales.
- Selector de **codificación de archivos**: `utf-8`, `utf-8-sig`, `latin-1`, `cp1252`, `ascii`.
- Soporte para **cancelar** tareas en segundo plano (`_cancel_flag`).

### Cambiado
- Ventana principal redimensionada a 980×800 px con tamaño mínimo de 820×600 px.

---

## [v2] — Refactorización modular y procesamiento por lotes
_2026-04-20_

### Nuevo — Arquitectura
- El proyecto deja de ser un script único y adopta **estructura modular**:
  ```
  regex_bulk_replace/
  ├── main.py
  ├── core/
  │   ├── replacer.py        ← Motor de reemplazos (ReplaceBlock, apply_blocks)
  │   ├── file_scanner.py    ← Escaneo y filtrado de archivos (ScanOptions)
  │   └── batch_processor.py ← Procesamiento por lotes
  ├── ui/
  │   ├── main_window.py     ← Ventana principal
  │   ├── blocks_panel.py    ← Panel de patrones/reemplazos
  │   ├── file_target_panel.py ← Selector de objetivo (texto/archivos/carpeta)
  │   ├── log_panel.py       ← Panel de log de resultados
  │   └── widgets.py         ← Widgets reutilizables
  └── utils/
      ├── config_manager.py  ← Serialización JSON (compatible con v1)
      └── thread_worker.py   ← Worker genérico para tareas en hilo secundario
  ```

### Nuevo — Funcionalidades
- **Procesamiento por lotes**: aplicar reemplazos sobre listas de archivos o carpetas completas (además del modo texto directo).
- Procesamiento en **hilo secundario** (`thread_worker.py`) para no bloquear la UI.
- `core/` totalmente desacoplado de la interfaz gráfica (sin imports de tkinter).
- Config JSON de v1 compatible con v2 (`config_manager.py`).
- README completo con estructura del proyecto y requisitos.

---

## [1.2.0] — Políticas de escritura y directorio de salida
_2026-04-14_

### Nuevo
- **Políticas de escritura** en `batch_processor.py`:
  - `WRITE_OVERWRITE`: sobreescribir el archivo en su misma ubicación (comportamiento anterior).
  - `WRITE_SKIP`: no tocar el archivo si ya existe en destino.
  - `WRITE_OUTPUT_DIR`: escribir en una carpeta de destino replicando la estructura de directorios.
- Función `_resolve_output_path()` para calcular la ruta de destino según la política activa.
- `FileProcessResult` almacena `output_path` (la ruta real donde se escribió, que puede diferir del origen) y `original_text`.
- Propiedad `has_changes` en `FileProcessResult` para detectar si el resultado difiere del original.
- Propiedad `results_with_changes` en `BatchResult` para filtrar solo los archivos modificados.
- Corrección de `errors` en `BatchResult`: ya no cuenta como error archivos que tuvieron `success=True`.

---

## [1.1.2.r6] — Corrección en reemplazo literal
_2025-03-17_

### Corregido
- En modo literal con "Palabra completa" activada, el texto de reemplazo se aplica ahora mediante una función lambda, evitando que secuencias como `\1` en el texto de reemplazo sean interpretadas como grupos de captura de regex.

---

## [1.1.2.r5] — Documentación del código
_2025-03-17_

### Cambiado
- Se agregaron comentarios explicativos en todos los métodos de `CustomScrolledText`.
- Sin cambios funcionales respecto a r4.

---

## [1.1.2.r4] — Atajos de teclado y menú contextual
_2025-02-11_

### Nuevo
- Nueva clase `CustomScrolledText` (subclase de `ScrolledText`):
  - Soporte de atajos de teclado: `Ctrl+C`, `Ctrl+X`, `Ctrl+V`, `Ctrl+A`, `Ctrl+Z` (deshacer), `Ctrl+Y` / `Ctrl+Shift+Z` (rehacer), `Delete`.
  - Menú contextual con clic derecho: Cortar, Copiar, Pegar, Seleccionar todo, Deshacer, Rehacer, Eliminar.
  - Historial de deshacer habilitado (`undo=True`).
- Ambas áreas de texto (original y resultante) usan `CustomScrolledText`.

---

## [1.1.2.r3] — Botonera unificada
_2025-02-10_

### Cambiado
- Los controles "Agregar Bloque" y el ComboBox de saltos de línea se integraron en la misma fila que "Abrir Config" / "Guardar Config", eliminando la fila separada del ComboBox y unificando toda la botonera del panel de bloques en una sola barra.

---

## [1.1.2.r2] — Botón "Copiar Original"
_2025-02-10_

### Nuevo
- Botón **"Copiar Original"** junto al área de texto de entrada para copiar el texto de entrada al portapapeles sin necesidad de seleccionarlo manualmente.
- Se agregó `root.update()` para asegurar que el portapapeles se actualice correctamente en todos los sistemas.

### Cambiado
- El botón "Copiar" junto al resultado fue renombrado a **"Copiar Resultado"**.
- El botón "Copiar Resultado" se alineó a la derecha del área de resultado (con espaciador).
- Se eliminó el botón "Copiar" redundante de la barra de acciones superior.

---

## [1.1.2] — Corrección de duplicación de reemplazos
_2025-03-17_

### Corregido
- Se eliminó el bloque de reemplazo de saltos de línea duplicado que había quedado en `aplicar_reemplazos()` en la versión 1.1.0, lo que causaba que los saltos de línea se procesaran dos veces.
- La barra de estado muestra ahora `www.aldo.net.ar` en lugar del nombre del autor.

---

## [1.1.0] — Detección automática de saltos de línea
_2025-03-17_

### Nuevo
- Función `detect_line_breaks()`: detecta automáticamente el tipo de salto de línea del texto de entrada (`\n`, `\r\n` o `\r`).
- La barra de estado muestra el **tipo de salto detectado** tras cada reemplazo.
- El reemplazo de saltos de línea respeta ahora el tipo detectado en lugar de asumir siempre `\n`.

### Mejorado
- Los errores de regex se muestran en un cuadro de diálogo (`messagebox.showerror`) en lugar de imprimirse en la consola.
- Las filas de las áreas de texto son redimensionables (`grid_rowconfigure` con `weight=1`).

---

## [1.0.2] — ComboBox de saltos de línea y rediseño del layout
_2025-02-09_

### Nuevo
- El checkbox "Reemplazar doble salto de línea por uno solo" fue reemplazado por un **ComboBox** con tres opciones:
  - `Ninguno`
  - `Doble salto de línea → Uno`
  - `Triple salto de línea → Doble`
- Los bloques de reemplazo y controles agrupados dentro de un `frame_encuadre` con borde `groove`.
- Los botones de acción (Reemplazar, Copiar, Reemplazar y Copiar) se movieron al área del texto original.

### Cambiado
- Tamaño de ventana ajustado a 880×682 px con tamaño mínimo fijo.
- El config JSON guarda/carga la opción de salto de línea seleccionada (`salto_opcion`).

---

## [1.0.1] — Área de resultado editable y botón Copiar junto al resultado
_2025-02-09_

### Nuevo
- Se agregó un botón **"Copiar"** directamente junto a la etiqueta "Texto Resultante".

### Cambiado
- El área de texto resultante es ahora **editable** (se eliminó `state=tk.DISABLED`): el usuario puede modificar el resultado antes de copiarlo o guardarlo.
- Tamaño mínimo de ventana reducido de 700 a 480 px de alto.

---

## [1.0.0] — Versión inicial
_2025-02-09_

### Funcionalidades
- Interfaz gráfica con **Tkinter** (script único).
- Bloques dinámicos de reemplazo: patrón + reemplazo, con opciones por bloque:
  - **Regex** (activado por defecto) o búsqueda literal.
  - **Match case** (distinción de mayúsculas/minúsculas).
  - **Palabra completa** (agrega `\b` en modo literal).
  - Botón **Invertir** para intercambiar patrón y reemplazo.
- Añadir y eliminar bloques dinámicamente; 4 bloques creados por defecto al inicio.
- Opción global: **reemplazar doble salto de línea por uno solo**.
- Botones: Reemplazar, Copiar resultado, Reemplazar y Copiar.
- Guardar y abrir configuración en formato **JSON**.
  - Al abrir una config con datos existentes, pregunta si desea guardar la actual primero.
- Abrir archivo `.txt` como texto de entrada.
- Guardar texto resultante en archivo `.txt`.
- **Barra de estado** con conteo de bloques y resultados (normales y de expresiones regulares).
- Área de texto de entrada y resultado con scroll, redimensionables.