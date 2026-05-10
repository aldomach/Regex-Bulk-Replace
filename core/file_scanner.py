"""
core/file_scanner.py
--------------------
Escaneo y filtrado de archivos. Sin dependencias de UI.
Reutilizable en cualquier herramienta de procesamiento por lotes.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator


@dataclass
class ScanOptions:
    """Opciones de filtrado para el escáner de archivos."""
    include_extensions: list[str] = field(default_factory=list)   # vacío = incluir todo
    exclude_extensions: list[str] = field(default_factory=list)
    ignore_hidden: bool = True          # ignora archivos/carpetas que empiezan con "."
    ignore_hidden_folders: bool = True
    recursive: bool = True

    def normalize_extensions(self, exts: list[str]) -> set[str]:
        """Normaliza extensiones: agrega punto si falta y pone en minúsculas."""
        result = set()
        for e in exts:
            e = e.strip().lower()
            if e and not e.startswith("."):
                e = "." + e
            if e:
                result.add(e)
        return result

    @property
    def include_set(self) -> set[str]:
        return self.normalize_extensions(self.include_extensions)

    @property
    def exclude_set(self) -> set[str]:
        return self.normalize_extensions(self.exclude_extensions)


@dataclass
class ScannedFile:
    """Representa un archivo encontrado durante el escaneo."""
    path: Path
    size: int = 0
    error: str = ""

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def extension(self) -> str:
        return self.path.suffix.lower()

    def __str__(self) -> str:
        return str(self.path)


def _is_hidden(path: Path) -> bool:
    """Detecta si un archivo o carpeta es oculto (nombre empieza con punto)."""
    return path.name.startswith(".")


def _passes_filter(file_path: Path, opts: ScanOptions) -> bool:
    """Verifica si un archivo pasa los filtros de extensión y visibilidad."""
    if opts.ignore_hidden and _is_hidden(file_path):
        return False

    ext = file_path.suffix.lower()

    if opts.exclude_set and ext in opts.exclude_set:
        return False

    if opts.include_set and ext not in opts.include_set:
        return False

    return True


def scan_folder(folder: str | Path, opts: ScanOptions) -> Iterator[ScannedFile]:
    """
    Recorre una carpeta (recursiva o no) y yield ScannedFile por cada archivo
    que pase los filtros definidos en opts.
    """
    folder = Path(folder)
    if not folder.exists() or not folder.is_dir():
        return

    if opts.recursive:
        walker = os.walk(folder)
    else:
        # Solo el nivel raíz
        walker = [(str(folder), [], [f.name for f in folder.iterdir() if f.is_file()])]

    for root, dirs, files in walker:
        root_path = Path(root)

        # Filtrar subdirectorios ocultos in-place para evitar descender
        if opts.ignore_hidden_folders:
            dirs[:] = [d for d in dirs if not d.startswith(".")]

        for filename in files:
            file_path = root_path / filename
            if _passes_filter(file_path, opts):
                try:
                    size = file_path.stat().st_size
                except OSError:
                    size = 0
                yield ScannedFile(path=file_path, size=size)


def scan_file_list(paths: list[str | Path], opts: ScanOptions) -> Iterator[ScannedFile]:
    """
    Filtra una lista explícita de archivos según opts.
    """
    for p in paths:
        file_path = Path(p)
        if not file_path.exists() or not file_path.is_file():
            yield ScannedFile(path=file_path, error="Archivo no encontrado")
            continue
        if _passes_filter(file_path, opts):
            try:
                size = file_path.stat().st_size
            except OSError:
                size = 0
            yield ScannedFile(path=file_path, size=size)
