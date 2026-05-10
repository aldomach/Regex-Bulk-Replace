"""
utils/config_manager.py
-----------------------
Serialización/deserialización de configuración a JSON.
Reutilizable en cualquier app que use ReplaceBlock.
"""

import json
from pathlib import Path
from core.replacer import ReplaceBlock


CONFIG_VERSION = 3


def blocks_to_dict(blocks: list[ReplaceBlock]) -> list[dict]:
    return [
        {
            "pattern": b.pattern,
            "replacement": b.replacement,
            "use_regex": b.use_regex,
            "match_case": b.match_case,
            "whole_word": b.whole_word,
            "dotall": b.dotall,
            "multiline": b.multiline,
            "condition": b.condition,
        }
        for b in blocks
    ]


def blocks_from_dict(data: list[dict]) -> list[ReplaceBlock]:
    result = []
    for item in data:
        result.append(ReplaceBlock(
            pattern=item.get("pattern", item.get("patron", "")),
            replacement=item.get("replacement", item.get("reemplazo", "")),
            use_regex=item.get("use_regex", item.get("usar_regex", True)),
            match_case=item.get("match_case", False),
            whole_word=item.get("whole_word", item.get("palabra_completa", False)),
            dotall=item.get("dotall", False),
            multiline=item.get("multiline", False),
            condition=item.get("condition", ""),
        ))
    return result


def save_config(path: str | Path, blocks: list[ReplaceBlock], extra: dict | None = None) -> None:
    """Guarda bloques y datos extra en un archivo JSON."""
    config = {
        "_version": CONFIG_VERSION,
        "replacements": blocks_to_dict(blocks),
    }
    if extra:
        config.update(extra)
    Path(path).write_text(
        json.dumps(config, indent=4, ensure_ascii=False),
        encoding="utf-8"
    )


def load_config(path: str | Path) -> tuple[list[ReplaceBlock], dict]:
    """
    Carga bloques y datos extra desde un archivo JSON.
    Retorna (blocks, extra_dict).
    Compatible con configs de v1 y v2 (campos nuevos usan valores por defecto).
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))

    # Compatibilidad con formato v1/v2
    raw_blocks = data.get("replacements", data.get("reemplazos", []))
    blocks = blocks_from_dict(raw_blocks)

    # Todo lo que no sea campos internos va al dict extra
    extra = {k: v for k, v in data.items() if k not in ("_version", "replacements", "reemplazos")}
    return blocks, extra
