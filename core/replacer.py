"""
core/replacer.py
----------------
Motor de reemplazos puro. Sin dependencias de UI.
Reutilizable en scripts, CLI o cualquier frontend.
"""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ReplaceBlock:
    """Define un par patrón/reemplazo con sus opciones."""
    pattern: str
    replacement: str
    use_regex: bool = True
    match_case: bool = False
    whole_word: bool = False
    dotall: bool = False        # El punto (.) captura saltos de línea — esencial para bloques multilínea
    multiline: bool = False     # ^ y $ coinciden con inicio/fin de cada línea (re.MULTILINE)
    condition: str = ""         # Solo aplicar este bloque si esta regex coincide en el contenido

    def is_valid(self) -> bool:
        return bool(self.pattern.strip())


@dataclass
class ReplaceResult:
    """Resultado de aplicar todos los bloques a un texto."""
    text: str
    normal_count: int = 0
    regex_count: int = 0
    errors: list = field(default_factory=list)
    skipped_blocks: list = field(default_factory=list)  # índices de bloques saltados por condición

    @property
    def total_count(self) -> int:
        return self.normal_count + self.regex_count


def detect_line_breaks(text: str) -> str:
    """Detecta el tipo de salto de línea predominante en el texto."""
    if "\r\n" in text:
        return "\r\n"
    elif "\r" in text:
        return "\r"
    return "\n"


def apply_line_break_normalization(text: str, mode: str, line_break: str) -> tuple[str, int]:
    """
    Normaliza saltos de línea según el modo elegido.
    Retorna (texto_modificado, cantidad_de_reemplazos).
    """
    if mode == "double_to_single":
        return re.subn(f'{re.escape(line_break)}{{2,}}', line_break, text)
    elif mode == "triple_to_double":
        return re.subn(
            f'{re.escape(line_break)}{{3,}}',
            f'{line_break}{line_break}',
            text
        )
    return text, 0


def _build_flags(block: ReplaceBlock) -> int:
    """Construye los flags de re a partir de las opciones del bloque."""
    flags = 0
    if not block.match_case:
        flags |= re.IGNORECASE
    if block.dotall:
        flags |= re.DOTALL
    if block.multiline:
        flags |= re.MULTILINE
    return flags


def apply_blocks(text: str, blocks: list[ReplaceBlock], line_break_mode: str = "none") -> ReplaceResult:
    """
    Aplica una lista de ReplaceBlock sobre el texto.
    Retorna un ReplaceResult con el texto modificado y estadísticas.

    Nuevas capacidades:
    - dotall: permite que el patrón cruce saltos de línea (bloques multilínea)
    - multiline: ^ y $ anclan a inicio/fin de línea
    - condition: el bloque sólo se aplica si la condición coincide en el contenido del archivo
    """
    result = ReplaceResult(text=text)
    line_break = detect_line_breaks(text)

    for idx, block in enumerate(blocks, start=1):
        if not block.is_valid():
            continue

        # ── Verificar condición ──────────────────────────────────────────────
        if block.condition.strip():
            try:
                cond_flags = (0 if block.match_case else re.IGNORECASE) | re.DOTALL | re.MULTILINE
                if not re.search(block.condition.strip(), result.text, flags=cond_flags):
                    result.skipped_blocks.append(idx)
                    continue
            except re.error as e:
                result.errors.append((idx, f"Condición inválida: {e}"))
                continue

        pattern = block.pattern.strip()
        replacement = block.replacement  # No strip: podría ser espacio intencional
        flags = _build_flags(block)

        if block.use_regex:
            try:
                new_text, count = re.subn(pattern, replacement, result.text, flags=flags)
                result.text = new_text
                result.regex_count += count
            except re.error as e:
                result.errors.append((idx, str(e)))
        else:
            escaped = re.escape(pattern)
            if block.whole_word:
                escaped = r"\b" + escaped + r"\b"
            new_text, count = re.subn(escaped, lambda m, r=replacement: r, result.text, flags=flags)
            result.text = new_text
            result.normal_count += count

    # Normalización de saltos de línea
    if line_break_mode != "none":
        new_text, count = apply_line_break_normalization(result.text, line_break_mode, line_break)
        result.text = new_text
        result.normal_count += count

    return result
