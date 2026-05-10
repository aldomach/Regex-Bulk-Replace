"""
utils/template_manager.py
--------------------------
Carga, guarda y gestiona plantillas desde un archivo JSON externo.
Las plantillas son grupos de ReplaceBlock con nombre y descripción.
"""

import json
from pathlib import Path
from dataclasses import dataclass, field
from core.replacer import ReplaceBlock
from utils.config_manager import blocks_to_dict, blocks_from_dict

# Archivo de plantillas por defecto, junto al ejecutable/script
DEFAULT_TEMPLATES_FILE = Path(__file__).parent.parent / "templates.json"


@dataclass
class Template:
    name: str
    description: str
    blocks: list[ReplaceBlock] = field(default_factory=list)


def load_templates(path: Path | str | None = None) -> list[Template]:
    """Carga plantillas desde archivo JSON. Devuelve lista vacía si no existe."""
    p = Path(path) if path else DEFAULT_TEMPLATES_FILE
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        result = []
        for item in data:
            blocks = blocks_from_dict(item.get("blocks", []))
            result.append(Template(
                name=item.get("name", "Sin nombre"),
                description=item.get("description", ""),
                blocks=blocks,
            ))
        return result
    except Exception:
        return []


def save_templates(templates: list[Template], path: Path | str | None = None) -> None:
    """Guarda plantillas en archivo JSON."""
    p = Path(path) if path else DEFAULT_TEMPLATES_FILE
    data = [
        {
            "name": t.name,
            "description": t.description,
            "blocks": blocks_to_dict(t.blocks),
        }
        for t in templates
    ]
    p.write_text(json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8")
