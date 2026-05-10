"""
ui/main_window.py  (PySide6)
-----------------------------
Ventana principal. Orquesta todos los paneles.
"""

import threading
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QComboBox, QCheckBox, QPushButton,
    QStatusBar, QGroupBox, QTextEdit, QFileDialog, QMessageBox,
    QSplitter, QToolBar, QSizePolicy,
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, QThread, Signal, QObject

from core.replacer import apply_blocks, ReplaceBlock
from core.file_scanner import scan_folder, scan_file_list
from core.batch_processor import process_files, BatchResult
from utils.config_manager import save_config, load_config

from ui.blocks_panel import BlocksPanel
from ui.file_target_panel import FileTargetPanel
from ui.log_panel import LogPanel
from ui.diff_panel import DiffPanel


LINE_BREAK_MODES = {
    "Ninguno": "none",
    "Doble → Uno": "double_to_single",
    "Triple → Doble": "triple_to_double",
}
ENCODINGS = ["utf-8", "utf-8-sig", "latin-1", "cp1252", "ascii"]


# ── Worker thread ─────────────────────────────────────────────────────────────

class _WorkerSignals(QObject):
    progress = Signal(int, int, str)   # current, total, path_name
    finished = Signal(object)          # BatchResult
    error    = Signal(str)


class _BatchWorker(QThread):
    def __init__(self, fn, parent=None):
        super().__init__(parent)
        self.fn = fn
        self.signals = _WorkerSignals()
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def is_cancelled(self):
        return self._cancel

    def run(self):
        try:
            result = self.fn()
            self.signals.finished.emit(result)
        except Exception as e:
            self.signals.error.emit(str(e))


# ── MainWindow ────────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Regex Bulk Replace")
        self.resize(1050, 820)
        self.setMinimumSize(820, 600)

        self._worker: _BatchWorker | None = None
        self._cancel_flag = False

        self._build_menu()
        self._build_ui()
        self._add_default_blocks()

    # ── Menú ──────────────────────────────────────────────────────────────

    def _build_menu(self):
        mb = self.menuBar()

        m_file = mb.addMenu("Archivo")
        m_file.addAction("Abrir config…",   self._load_config)
        m_file.addAction("Guardar config…", self._save_config)
        m_file.addSeparator()
        m_file.addAction("Salir", self.close)

        m_help = mb.addMenu("Ayuda")
        m_help.addAction("Acerca de…", self._show_about)

    # ── UI principal ──────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(8, 6, 8, 4)
        root.setSpacing(4)

        self._tabs = QTabWidget()
        root.addWidget(self._tabs, 1)

        # Pestaña Reemplazos
        tab_main = QWidget()
        self._tabs.addTab(tab_main, "  Reemplazos  ")
        self._build_main_tab(tab_main)

        # Pestaña Log
        tab_log = QWidget()
        self._tabs.addTab(tab_log, "  Log  ")
        lay_log = QVBoxLayout(tab_log)
        lay_log.setContentsMargins(6, 6, 6, 6)
        self._log_panel = LogPanel()
        lay_log.addWidget(self._log_panel)

        # Pestaña Diferencias
        tab_diff = QWidget()
        self._tabs.addTab(tab_diff, "  Diferencias  ")
        lay_diff = QVBoxLayout(tab_diff)
        lay_diff.setContentsMargins(6, 6, 6, 6)
        self._diff_panel = DiffPanel(encoding_getter=lambda: self._cmb_encoding.currentText())
        lay_diff.addWidget(self._diff_panel)

        # Status bar
        self.statusBar().showMessage("Listo")

    def _build_main_tab(self, parent):
        layout = QVBoxLayout(parent)
        layout.setSpacing(6)
        layout.setContentsMargins(4, 4, 4, 4)

        # Splitter vertical: bloques arriba, texto abajo
        splitter = QSplitter(Qt.Vertical)

        # ── Parte superior ─────────────────────────────────────────────
        top = QWidget()
        top_lay = QVBoxLayout(top)
        top_lay.setContentsMargins(0, 0, 0, 0)
        top_lay.setSpacing(4)

        self._blocks_panel = BlocksPanel()
        top_lay.addWidget(self._blocks_panel)

        self._target_panel = FileTargetPanel()
        top_lay.addWidget(self._target_panel)

        # Opciones globales
        opts_box = QGroupBox("Opciones")
        opts_lay = QVBoxLayout(opts_box)
        opts_lay.setSpacing(4)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Saltos de línea:"))
        self._cmb_linebreak = QComboBox()
        self._cmb_linebreak.addItems(list(LINE_BREAK_MODES.keys()))
        row1.addWidget(self._cmb_linebreak)
        row1.addSpacing(20)

        row1.addWidget(QLabel("Encoding:"))
        self._cmb_encoding = QComboBox()
        self._cmb_encoding.addItems(ENCODINGS)
        self._cmb_encoding.setEditable(True)
        row1.addWidget(self._cmb_encoding)
        row1.addSpacing(20)

        self._chk_dry = QCheckBox("Modo simulación (activa pestaña Diferencias)")
        row1.addWidget(self._chk_dry)
        row1.addStretch()
        opts_lay.addLayout(row1)

        row2 = QHBoxLayout()
        self._btn_run = QPushButton("▶  Ejecutar")
        self._btn_run.setStyleSheet(
            "background:#2a7a2a; color:white; font-weight:bold; padding:6px 16px")
        self._btn_run.clicked.connect(self._run)
        row2.addWidget(self._btn_run)

        self._btn_cancel = QPushButton("⏹  Cancelar")
        self._btn_cancel.setEnabled(False)
        self._btn_cancel.clicked.connect(self._cancel)
        row2.addWidget(self._btn_cancel)

        row2.addSpacing(20)
        btn_open_cfg = QPushButton("Abrir config")
        btn_open_cfg.clicked.connect(self._load_config)
        row2.addWidget(btn_open_cfg)

        btn_save_cfg = QPushButton("Guardar config")
        btn_save_cfg.clicked.connect(self._save_config)
        row2.addWidget(btn_save_cfg)
        row2.addStretch()
        opts_lay.addLayout(row2)

        top_lay.addWidget(opts_box)
        splitter.addWidget(top)

        # ── Parte inferior: área de texto ──────────────────────────────
        self._text_area_widget = QWidget()
        ta_lay = QVBoxLayout(self._text_area_widget)
        ta_lay.setContentsMargins(0, 0, 0, 0)
        ta_lay.setSpacing(2)

        # Texto entrada
        hdr_in = QHBoxLayout()
        hdr_in.addWidget(QLabel("<b>Texto Original</b>"))
        btn_open_f = QPushButton("Abrir archivo…"); btn_open_f.clicked.connect(self._open_text_file)
        btn_copy_in = QPushButton("Copiar"); btn_copy_in.clicked.connect(lambda: self._copy_text(self._text_in))
        btn_clear = QPushButton("Borrar"); btn_clear.clicked.connect(self._clear_texts)
        for b in [btn_open_f, btn_copy_in, btn_clear]:
            hdr_in.addWidget(b)
        hdr_in.addStretch()
        ta_lay.addLayout(hdr_in)

        self._text_in = QTextEdit()
        self._text_in.setPlaceholderText("Pegá texto aquí para probar los reemplazos…")
        self._text_in.setMinimumHeight(80)
        ta_lay.addWidget(self._text_in, 1)

        mid_row = QHBoxLayout()
        btn_run_t = QPushButton("▶ Reemplazar")
        btn_run_t.setStyleSheet("background:#2a7a2a; color:white")
        btn_run_t.clicked.connect(self._run)
        btn_run_copy = QPushButton("▶ Reemplazar y Copiar")
        btn_run_copy.clicked.connect(self._run_and_copy)
        mid_row.addWidget(btn_run_t)
        mid_row.addWidget(btn_run_copy)
        mid_row.addStretch()
        btn_copy_out = QPushButton("Copiar resultado")
        btn_copy_out.clicked.connect(lambda: self._copy_text(self._text_out))
        btn_save_out = QPushButton("Guardar resultado…")
        btn_save_out.clicked.connect(self._save_text_result)
        mid_row.addWidget(btn_copy_out); mid_row.addWidget(btn_save_out)
        ta_lay.addLayout(mid_row)

        self._text_out = QTextEdit()
        self._text_out.setReadOnly(True)
        self._text_out.setPlaceholderText("El resultado aparecerá aquí…")
        self._text_out.setMinimumHeight(80)
        ta_lay.addWidget(self._text_out, 1)

        splitter.addWidget(self._text_area_widget)
        splitter.setSizes([600, 300])
        layout.addWidget(splitter, 1)

        # Ocultar área de texto según modo
        self._target_panel._bg.buttonClicked.connect(self._on_mode_change)
        self._on_mode_change()

    # ── Mode switch ───────────────────────────────────────────────────────

    def _on_mode_change(self, btn=None):
        mode = self._target_panel.mode
        self._text_area_widget.setVisible(mode == FileTargetPanel.MODE_TEXT)

    # ── Run ───────────────────────────────────────────────────────────────

    def _run(self):
        blocks = self._blocks_panel.get_blocks()
        active = [b for b in blocks if b.is_valid()]
        if not active:
            QMessageBox.warning(self, "Sin bloques",
                                "Agregá al menos un patrón antes de ejecutar.")
            return

        mode = self._target_panel.mode
        lb_mode = LINE_BREAK_MODES[self._cmb_linebreak.currentText()]

        if mode == FileTargetPanel.MODE_TEXT:
            self._run_text_mode(active, lb_mode)
        else:
            self._run_batch_mode(active, lb_mode)

    def _run_text_mode(self, blocks, lb_mode):
        text = self._text_in.toPlainText()
        result = apply_blocks(text, blocks, lb_mode)
        self._text_out.setPlainText(result.text)

        if result.errors:
            msg = "\n".join(f"Bloque {i}: {e}" for i, e in result.errors)
            QMessageBox.critical(self, "Error regex", msg)

        self.statusBar().showMessage(
            f"Normal: {result.normal_count}  |  Regex: {result.regex_count}  |  "
            f"Total: {result.total_count} reemplazos"
        )

    def _run_batch_mode(self, blocks, lb_mode):
        encoding = self._cmb_encoding.currentText()
        dry_run  = self._chk_dry.isChecked()
        mode     = self._target_panel.mode

        if mode == FileTargetPanel.MODE_FOLDER:
            folder = self._target_panel.folder_path
            if not folder:
                QMessageBox.warning(self, "Sin carpeta", "Seleccioná una carpeta primero.")
                return
            files = list(scan_folder(folder, self._target_panel.get_scan_options()))
        else:
            manual = self._target_panel.file_list
            if not manual:
                QMessageBox.warning(self, "Sin archivos", "Agregá archivos a la lista primero.")
                return
            files = list(scan_file_list(manual, self._target_panel.get_scan_options()))

        if not files:
            QMessageBox.information(self, "Sin archivos",
                                    "No se encontraron archivos con los filtros aplicados.")
            return

        msg = (
            f"Se procesarán {len(files)} archivo(s).\n"
            f"{'⚠ MODO SIMULACIÓN: no se escribirán cambios.' if dry_run else '⚠ Los archivos serán modificados en disco.'}\n\n"
            "¿Continuar?"
        )
        if QMessageBox.question(self, "Confirmar", msg) != QMessageBox.Yes:
            return

        self._log_panel.clear()
        self._tabs.setCurrentIndex(1)
        self.statusBar().showMessage("Procesando…")
        self._btn_run.setEnabled(False)
        self._btn_cancel.setEnabled(True)
        self._cancel_flag = False

        def do_work():
            return process_files(
                files, blocks, lb_mode, encoding, dry_run,
                progress_callback=lambda cur, tot, p: self._worker.signals.progress.emit(cur, tot, str(p)),
                cancel_check=lambda: self._cancel_flag,
            )

        self._worker = _BatchWorker(do_work)
        self._worker.signals.progress.connect(self._on_progress)
        self._worker.signals.finished.connect(lambda r: self._on_batch_done(r, dry_run))
        self._worker.signals.error.connect(self._on_batch_error)
        self._worker.start()

    def _on_progress(self, current: int, total: int, path_name: str):
        pct = (current / total * 100) if total else 0
        self._log_panel.set_progress(pct, f"{current}/{total}")
        self.statusBar().showMessage(f"Procesando {current}/{total}: {path_name}")

    def _on_batch_done(self, batch: BatchResult, dry_run: bool):
        for fr in batch.file_results:
            self._log_panel.log_file_result(fr)
        self._log_panel.log_batch_summary(batch)
        self._log_panel.set_progress(100, "Completado")
        self.statusBar().showMessage(
            f"Completado — {batch.processed} archivos, "
            f"{batch.total_replacements} reemplazos, {batch.errors} errores"
        )
        self._reset_buttons()
        if dry_run:
            self._diff_panel.load_results(batch)
            self._tabs.setCurrentIndex(2)

    def _on_batch_error(self, msg: str):
        QMessageBox.critical(self, "Error", msg)
        self._reset_buttons()

    def _cancel(self):
        self._cancel_flag = True
        self.statusBar().showMessage("Cancelando…")
        self._btn_cancel.setEnabled(False)

    def _reset_buttons(self):
        self._btn_run.setEnabled(True)
        self._btn_cancel.setEnabled(False)

    def _run_and_copy(self):
        self._run()
        self._copy_text(self._text_out)

    # ── Text helpers ──────────────────────────────────────────────────────

    def _copy_text(self, widget: QTextEdit):
        from PySide6.QtWidgets import QApplication
        text = widget.toPlainText().strip()
        if text:
            QApplication.clipboard().setText(text)

    def _clear_texts(self):
        if QMessageBox.question(self, "Confirmar", "¿Limpiar ambas áreas de texto?") == QMessageBox.Yes:
            self._text_in.clear()
            self._text_out.clear()

    def _open_text_file(self):
        if self._text_in.toPlainText().strip():
            if QMessageBox.question(self, "Advertencia",
                                    "Se reemplazará el contenido actual. ¿Continuar?") != QMessageBox.Yes:
                return
        path, _ = QFileDialog.getOpenFileName(self, "Abrir archivo de texto")
        if path:
            try:
                content = Path(path).read_text(
                    encoding=self._cmb_encoding.currentText(), errors="replace")
                self._text_in.setPlainText(content)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo abrir: {e}")

    def _save_text_result(self):
        text = self._text_out.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Sin contenido", "No hay texto resultante para guardar.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Guardar resultado",
                                              filter="Archivos de texto (*.txt);;Todos (*.*)")
        if path:
            try:
                Path(path).write_text(text, encoding=self._cmb_encoding.currentText())
                QMessageBox.information(self, "Guardado", "Archivo guardado correctamente.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo guardar: {e}")

    # ── Config ────────────────────────────────────────────────────────────

    def _save_config(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar configuración", filter="JSON (*.json)")
        if not path:
            return
        extra = {
            "linebreak_mode": self._cmb_linebreak.currentText(),
            "encoding": self._cmb_encoding.currentText(),
            "target": self._target_panel.get_state(),
        }
        try:
            save_config(path, self._blocks_panel.get_blocks(), extra)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar: {e}")

    def _load_config(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir configuración", filter="JSON (*.json)")
        if not path:
            return
        try:
            blocks, extra = load_config(path)
            self._blocks_panel.load_blocks(blocks)
            if "linebreak_mode" in extra:
                idx = self._cmb_linebreak.findText(extra["linebreak_mode"])
                if idx >= 0:
                    self._cmb_linebreak.setCurrentIndex(idx)
            if "encoding" in extra:
                idx = self._cmb_encoding.findText(extra["encoding"])
                if idx >= 0:
                    self._cmb_encoding.setCurrentIndex(idx)
                else:
                    self._cmb_encoding.setCurrentText(extra["encoding"])
            if "target" in extra:
                self._target_panel.set_state(extra["target"])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar: {e}")

    # ── Misc ──────────────────────────────────────────────────────────────

    def _add_default_blocks(self):
        for _ in range(3):
            self._blocks_panel.add_row()

    def _show_about(self):
        QMessageBox.about(
            self, "Acerca de",
            "Regex Bulk Replace\n\n"
            "Herramienta para aplicar reemplazos de texto (regex y literales)\n"
            "sobre texto directo, listas de archivos o carpetas completas.\n\n"
            "www.aldo.net.ar"
        )
