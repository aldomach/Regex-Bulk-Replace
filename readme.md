# Regex Bulk Replace

Herramienta de escritorio para aplicar múltiples reemplazos de texto —por expresiones regulares o literales— de forma encadenada, sobre texto directo, archivos individuales o carpetas completas.

Compatible con **Windows** y **Linux**. Requiere **Python 3.10+**.

---

## Características

- **Bloques de reemplazo encadenados**: definí tantos patrones como necesités; se aplican en orden, uno sobre el resultado del anterior.
- **Modos por bloque**: Regex o búsqueda literal, con opciones de Match case y Palabra completa independientes por bloque.
- **Procesamiento por lotes**: aplicá los reemplazos sobre texto directo, una lista de archivos o una carpeta completa (con filtros por extensión).
- **Panel de diff**: previsualización antes/después con resaltado de cambios en color, antes de escribir nada al disco.
- **Plantillas**: guardá grupos de bloques con nombre para reutilizarlos entre sesiones.
- **Políticas de escritura**: sobreescribir en el mismo lugar, omitir archivos sin cambios, o escribir en una carpeta de destino replicando la estructura de directorios.
- **Detección automática del tipo de salto de línea** (`\n`, `\r\n`, `\r`) por archivo.
- **Soporte de encodings**: UTF-8, UTF-8-BOM, Latin-1, CP1252, ASCII.
- **Config exportable**: guardá y cargá configuraciones de bloques en formato JSON.

---

## Requisitos

```
Python 3.10+
tkinter (incluido en la mayoría de instalaciones de Python)
```

Para el port experimental de Qt:

```
PySide6
```

---

## Instalación

```bash
git clone https://github.com/tu-usuario/regex-bulk-replace.git
cd regex-bulk-replace/regex_bulk_replace
python main.py
```

No requiere instalación de dependencias externas para la versión Tkinter.

---

## Uso rápido

1. **Definí los bloques de reemplazo** en el panel superior: escribí el patrón y el texto de reemplazo en cada fila.
2. Activá o desactivá **Regex**, **Match case** y **Palabra completa** por bloque según necesites.
3. Elegí el **objetivo**:
   - *Texto directo*: pegá o escribí el texto en el área de entrada y presioná **Reemplazar**.
   - *Archivos / carpeta*: seleccioná los archivos o la carpeta desde el panel lateral.
4. Usá **Simulación** para ver el diff antes de escribir al disco.
5. Presioná **Aplicar** para confirmar los cambios.

---

## Estructura del proyecto

```
regex_bulk_replace/
│
├── main.py                      ← Punto de entrada
│
├── core/                        ← Lógica pura, sin dependencias de UI
│   ├── replacer.py              ← Motor de reemplazos (ReplaceBlock, apply_blocks)
│   ├── file_scanner.py          ← Escaneo y filtrado de archivos (ScanOptions)
│   └── batch_processor.py       ← Procesamiento por lotes sobre archivos
│
├── ui/                          ← Interfaz gráfica (Tkinter)
│   ├── main_window.py           ← Ventana principal, orquestación
│   ├── blocks_panel.py          ← Panel de patrones/reemplazos
│   ├── file_target_panel.py     ← Panel de selección de objetivo
│   ├── diff_panel.py            ← Panel de previsualización antes/después
│   ├── log_panel.py             ← Panel de log de resultados
│   └── widgets.py               ← Widgets reutilizables
│
├── utils/                       ← Utilidades
│   ├── config_manager.py        ← Serialización de config a JSON
│   ├── template_manager.py      ← Gestión de plantillas
│   └── thread_worker.py         ← Worker para tareas en hilo secundario
│
└── templates.json               ← Plantillas predefinidas (opcional)
```

---

## Panel de bloques

Cada bloque de reemplazo tiene los siguientes campos:

| Campo | Descripción |
|---|---|
| **Patrón** | Texto a buscar (expresión regular o literal). |
| **Reemplazo** | Texto con el que se reemplaza. En modo Regex, se pueden usar grupos de captura (`\1`, `\2`, etc.). |
| **Invertir** | Intercambia patrón y reemplazo con un clic. |
| **Regex** | Si está activo, el patrón se interpreta como expresión regular. |
| **Match case** | Si está activo, distingue mayúsculas de minúsculas. |
| **Palabra completa** | En modo literal, agrega `\b` alrededor del patrón para buscar solo palabras completas. |
| **Eliminar** | Elimina el bloque. |

Los bloques se aplican **en orden**, de arriba hacia abajo. El resultado de cada bloque es la entrada del siguiente.

---

## Opciones globales

- **Reemplazar saltos de línea**: normalizá los saltos antes o después de aplicar los bloques.
  - `Ninguno`: sin modificación.
  - `Doble → Uno`: elimina líneas en blanco múltiples.
  - `Triple → Doble`: reduce tres o más saltos a dos.
- **Encoding**: seleccioná la codificación para leer y escribir archivos (`utf-8`, `utf-8-sig`, `latin-1`, `cp1252`, `ascii`).

---

## Configuración (JSON)

Las configuraciones se guardan en archivos `.json` con el siguiente formato:

```json
{
  "salto_opcion": "Ninguno",
  "reemplazos": [
    {
      "patron": "\\bcolor\\b",
      "reemplazo": "colour",
      "usar_regex": true,
      "match_case": false,
      "palabra_completa": false
    }
  ]
}
```

Los archivos de config de la versión 1.x son **compatibles** con la versión 2.x.

---

## Plantillas

Las plantillas son grupos de bloques de reemplazo con nombre y descripción, almacenadas en `templates.json` junto al ejecutable.

```json
[
  {
    "name": "Limpiar HTML básico",
    "description": "Elimina etiquetas HTML comunes",
    "blocks": [
      { "patron": "<[^>]+>", "reemplazo": "", "usar_regex": true, "match_case": false, "palabra_completa": false }
    ]
  }
]
```

---

## Procesamiento por lotes

El modo de archivos permite aplicar los reemplazos sobre múltiples archivos de forma simultánea, con las siguientes políticas de escritura:

| Política | Comportamiento |
|---|---|
| `overwrite` | Sobreescribe el archivo en su ubicación original. |
| `skip` | Omite el archivo si no hubo cambios. |
| `output_dir` | Escribe el resultado en una carpeta de destino, replicando la estructura de directorios original. |

El procesamiento corre en un **hilo secundario** para no bloquear la interfaz, con opción de cancelar a mitad de proceso.

---

## Atajos de teclado

Las áreas de texto admiten los siguientes atajos:

| Atajo | Acción |
|---|---|
| `Ctrl+Z` | Deshacer |
| `Ctrl+Y` / `Ctrl+Shift+Z` | Rehacer |
| `Ctrl+A` | Seleccionar todo |
| `Ctrl+C` | Copiar |
| `Ctrl+X` | Cortar |
| `Ctrl+V` | Pegar |
| `Delete` | Eliminar selección |
| `Clic derecho` | Menú contextual |

---

## Versiones

| Versión | UI | Notas |
|---|---|---|
| 1.x | Tkinter (script único) | Serie original, script autocontenido. |
| 2.x / v2–v6 | Tkinter (modular) | Arquitectura modular, procesamiento por lotes, diff, plantillas. |
| qt | PySide6 | Port experimental con estilo Fusion. |

Consultar el [CHANGELOG](CHANGELOG.md) para el historial completo de cambios.

---

## Autor

Aldo Machado — [www.aldo.net.ar](https://www.aldo.net.ar)