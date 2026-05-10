"""
core/batch_processor.py
-----------------------
Aplica reemplazos a múltiples archivos. Sin dependencias de UI.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from core.replacer import ReplaceBlock, ReplaceResult, apply_blocks
from core.file_scanner import ScannedFile


@dataclass
class FileProcessResult:
    """Resultado del procesamiento de un archivo individual."""
    file: ScannedFile
    result: Optional[ReplaceResult] = None
    success: bool = False
    error: str = ""
    skipped: bool = False       # Sin cambios, no se escribió
    original_text: Optional[str] = None  # Guardado para el panel de diff

    @property
    def path(self) -> Path:
        return self.file.path


@dataclass
class BatchResult:
    """Resumen del procesamiento de un lote de archivos."""
    file_results: list[FileProcessResult] = field(default_factory=list)

    @property
    def total_files(self) -> int:
        return len(self.file_results)

    @property
    def processed(self) -> int:
        return sum(1 for r in self.file_results if r.success)

    @property
    def skipped(self) -> int:
        return sum(1 for r in self.file_results if r.skipped)

    @property
    def errors(self) -> int:
        return sum(1 for r in self.file_results if r.error)

    @property
    def total_replacements(self) -> int:
        return sum(
            r.result.total_count
            for r in self.file_results
            if r.result
        )


def process_files(
    files: list[ScannedFile],
    blocks: list[ReplaceBlock],
    line_break_mode: str = "none",
    encoding: str = "utf-8",
    dry_run: bool = False,
    progress_callback: Optional[Callable[[int, int, Path], None]] = None,
    cancel_check: Optional[Callable[[], bool]] = None,
) -> BatchResult:
    """
    Procesa una lista de archivos aplicando los bloques de reemplazo.
    Guarda original_text en cada FileProcessResult para permitir el diff.
    """
    batch = BatchResult()
    total = len(files)

    for idx, scanned_file in enumerate(files):
        if cancel_check and cancel_check():
            break

        if progress_callback:
            progress_callback(idx, total, scanned_file.path)

        file_result = FileProcessResult(file=scanned_file)

        if scanned_file.error:
            file_result.error = scanned_file.error
            batch.file_results.append(file_result)
            continue

        try:
            text = scanned_file.path.read_text(encoding=encoding, errors="replace")
        except Exception as e:
            file_result.error = f"Error de lectura: {e}"
            batch.file_results.append(file_result)
            continue

        # Guardar texto original para poder mostrar el diff
        file_result.original_text = text

        replace_result = apply_blocks(text, blocks, line_break_mode)
        file_result.result = replace_result

        if replace_result.errors:
            file_result.error = "; ".join(f"Bloque {i}: {e}" for i, e in replace_result.errors)

        if replace_result.text == text:
            file_result.skipped = True
            file_result.success = True
            batch.file_results.append(file_result)
            continue

        if not dry_run:
            try:
                scanned_file.path.write_text(replace_result.text, encoding=encoding)
                file_result.success = True
            except Exception as e:
                file_result.error = f"Error de escritura: {e}"
        else:
            file_result.success = True

        batch.file_results.append(file_result)

    return batch
