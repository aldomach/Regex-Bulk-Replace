"""
ui/file_target_panel.py  (PySide6)
------------------------------------
Panel para seleccionar el objetivo de los reemplazos:
  - Modo Texto directo
  - Lista de archivos manuales
  - Carpeta recursiva
"""

from PySide6.QtWidgets import (
    QWidget, QGroupBox, QVBoxLayout, QHBoxLayout, QLabel,
    QRadioButton, QButtonGroup, QPushButton, QListWidget,
    QLineEdit, QCheckBox, QFileDialog, QFrame, QMenu,
    QAbstractItemView,
)
from PySide6.QtCore import Qt
from pathlib import Path
from core.file_scanner import ScanOptions


class ExtListWidget(QWidget):
    """Mini widget: label + listbox de extensiones + entrada para agregar."""
    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)
        lay.addWidget(QLabel(label))
        self._list = QListWidget()
        self._list.setMaximumHeight(70)
        self._list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        lay.addWidget(self._list)
        row = QHBoxLayout()
        self._entry = QLineEdit()
        self._entry.setPlaceholderText(".ext")
        self._entry.returnPressed.connect(self._add)
        row.addWidget(self._entry)
        btn_add = QPushButton("+ Agregar"); btn_add.clicked.connect(self._add)
        btn_del = QPushButton("✕ Quitar");  btn_del.clicked.connect(self._remove)
        row.addWidget(btn_add); row.addWidget(btn_del)
        lay.addLayout(row)

    def _add(self):
        v = self._entry.text().strip()
        if v:
            self._list.addItem(v)
            self._entry.clear()

    def _remove(self):
        for item in self._list.selectedItems():
            self._list.takeItem(self._list.row(item))

    def get_items(self) -> list[str]:
        return [self._list.item(i).text() for i in range(self._list.count())]

    def set_items(self, items: list[str]):
        self._list.clear()
        for i in items:
            self._list.addItem(i)


class FileTargetPanel(QGroupBox):
    MODE_TEXT   = "text"
    MODE_FILES  = "files"
    MODE_FOLDER = "folder"

    def __init__(self, parent=None):
        super().__init__("Objetivo", parent)
        self._file_list: list[str] = []
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)

        # Selector de modo
        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Modo:"))
        self._bg = QButtonGroup(self)
        for label, value in [("Texto directo", self.MODE_TEXT),
                              ("Lista de archivos", self.MODE_FILES),
                              ("Carpeta", self.MODE_FOLDER)]:
            rb = QRadioButton(label)
            rb.setProperty("mode_value", value)
            self._bg.addButton(rb)
            mode_row.addWidget(rb)
        mode_row.addStretch()
        self._bg.buttons()[0].setChecked(True)
        self._bg.buttonClicked.connect(self._on_mode_change)
        layout.addLayout(mode_row)

        # ── Página texto ──────────────────────────────────────────────────
        self._page_text = QLabel("Escribí o pegá texto en el área inferior.")
        self._page_text.setStyleSheet("color:#666")
        layout.addWidget(self._page_text)

        # ── Página archivos ───────────────────────────────────────────────
        self._page_files = QWidget()
        pf_lay = QVBoxLayout(self._page_files)
        pf_lay.setContentsMargins(0, 0, 0, 0)
        btn_row_f = QHBoxLayout()
        btn_add_f = QPushButton("Agregar archivos…")
        btn_add_f.clicked.connect(self._browse_files)
        btn_clr_f = QPushButton("✕ Limpiar lista")
        btn_clr_f.clicked.connect(self._clear_files)
        btn_row_f.addWidget(btn_add_f); btn_row_f.addWidget(btn_clr_f)
        btn_row_f.addStretch()
        pf_lay.addLayout(btn_row_f)
        self._file_listbox = QListWidget()
        self._file_listbox.setMaximumHeight(100)
        self._file_listbox.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._file_listbox.setContextMenuPolicy(Qt.CustomContextMenu)
        self._file_listbox.customContextMenuRequested.connect(self._file_ctx)
        pf_lay.addWidget(self._file_listbox)
        layout.addWidget(self._page_files)
        self._page_files.hide()

        # ── Página carpeta ────────────────────────────────────────────────
        self._page_folder = QWidget()
        pfo_lay = QVBoxLayout(self._page_folder)
        pfo_lay.setContentsMargins(0, 0, 0, 0)

        folder_row = QHBoxLayout()
        folder_row.addWidget(QLabel("Carpeta:"))
        self._folder_entry = QLineEdit()
        folder_row.addWidget(self._folder_entry, 1)
        btn_browse = QPushButton("Examinar…")
        btn_browse.clicked.connect(self._browse_folder)
        folder_row.addWidget(btn_browse)
        pfo_lay.addLayout(folder_row)

        opts_row = QHBoxLayout()
        self._chk_recursive     = QCheckBox("Recursivo");          self._chk_recursive.setChecked(True)
        self._chk_ignore_hidden = QCheckBox("Ignorar ocultos");    self._chk_ignore_hidden.setChecked(True)
        opts_row.addWidget(self._chk_recursive)
        opts_row.addWidget(self._chk_ignore_hidden)
        opts_row.addStretch()
        pfo_lay.addLayout(opts_row)

        ext_row = QHBoxLayout()
        self._include_list = ExtListWidget("✅ Incluir extensiones\n   [vacío = todo]")
        self._exclude_list = ExtListWidget("🚫 Ignorar extensiones")
        ext_row.addWidget(self._include_list, 1)
        ext_row.addWidget(self._exclude_list, 1)
        pfo_lay.addLayout(ext_row)

        layout.addWidget(self._page_folder)
        self._page_folder.hide()

    # ── Eventos ───────────────────────────────────────────────────────────

    def _on_mode_change(self, btn):
        mode = btn.property("mode_value")
        self._page_text.setVisible(mode == self.MODE_TEXT)
        self._page_files.setVisible(mode == self.MODE_FILES)
        self._page_folder.setVisible(mode in (self.MODE_FOLDER, self.MODE_FILES))

    def _browse_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta")
        if path:
            self._folder_entry.setText(path)

    def _browse_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Seleccionar archivos")
        for p in paths:
            if p not in self._file_list:
                self._file_list.append(p)
                self._file_listbox.addItem(p)

    def _clear_files(self):
        self._file_list.clear()
        self._file_listbox.clear()

    def _file_ctx(self, pos):
        menu = QMenu(self)
        menu.addAction("Quitar seleccionados", self._remove_files)
        menu.exec(self._file_listbox.mapToGlobal(pos))

    def _remove_files(self):
        for item in self._file_listbox.selectedItems():
            row = self._file_listbox.row(item)
            self._file_list.pop(row)
            self._file_listbox.takeItem(row)

    # ── API pública ───────────────────────────────────────────────────────

    @property
    def mode(self) -> str:
        for btn in self._bg.buttons():
            if btn.isChecked():
                return btn.property("mode_value")
        return self.MODE_TEXT

    @property
    def folder_path(self) -> str:
        return self._folder_entry.text().strip()

    @property
    def file_list(self) -> list[str]:
        return list(self._file_list)

    def get_scan_options(self) -> ScanOptions:
        return ScanOptions(
            include_extensions=self._include_list.get_items(),
            exclude_extensions=self._exclude_list.get_items(),
            ignore_hidden=self._chk_ignore_hidden.isChecked(),
            ignore_hidden_folders=self._chk_ignore_hidden.isChecked(),
            recursive=self._chk_recursive.isChecked(),
        )

    def get_state(self) -> dict:
        return {
            "mode": self.mode,
            "folder": self.folder_path,
            "file_list": self.file_list,
            "recursive": self._chk_recursive.isChecked(),
            "ignore_hidden": self._chk_ignore_hidden.isChecked(),
            "include_ext": self._include_list.get_items(),
            "exclude_ext": self._exclude_list.get_items(),
        }

    def set_state(self, state: dict):
        target_mode = state.get("mode", self.MODE_TEXT)
        for btn in self._bg.buttons():
            if btn.property("mode_value") == target_mode:
                btn.setChecked(True)
                self._on_mode_change(btn)
                break
        self._folder_entry.setText(state.get("folder", ""))
        self._chk_recursive.setChecked(state.get("recursive", True))
        self._chk_ignore_hidden.setChecked(state.get("ignore_hidden", True))
        self._include_list.set_items(state.get("include_ext", []))
        self._exclude_list.set_items(state.get("exclude_ext", []))
        self._clear_files()
        for p in state.get("file_list", []):
            self._file_list.append(p)
            self._file_listbox.addItem(p)
