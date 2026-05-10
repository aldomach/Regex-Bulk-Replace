"""
ui/log_panel.py  (PySide6)
---------------------------
Panel de log con barra de progreso y colores.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit,
    QPushButton, QProgressBar, QLabel,
)
from PySide6.QtGui import QTextCursor, QColor, QTextCharFormat, QFont
from PySide6.QtCore import Qt
from core.batch_processor import FileProcessResult, BatchResult


class LogPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(4)

        # Barra de progreso
        prog_row = QHBoxLayout()
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._prog_label = QLabel("")
        self._prog_label.setMinimumWidth(80)
        self._prog_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        prog_row.addWidget(self._progress, 1)
        prog_row.addWidget(self._prog_label)
        layout.addLayout(prog_row)

        # Área de texto (modo oscuro)
        self._text = QPlainTextEdit()
        self._text.setReadOnly(True)
        self._text.setLineWrapMode(QPlainTextEdit.NoWrap)
        f = QFont("Consolas", 9)
        self._text.setFont(f)
        self._text.setStyleSheet("background:#1e1e1e; color:#d4d4d4")
        layout.addWidget(self._text, 1)

        btn_clear = QPushButton("Limpiar log")
        btn_clear.clicked.connect(self.clear)
        layout.addWidget(btn_clear, 0, Qt.AlignRight)

    # ── Colores ───────────────────────────────────────────────────────────

    def _fmt(self, hex_color: str, bold=False) -> QTextCharFormat:
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(hex_color))
        if bold:
            fmt.setFontWeight(QFont.Bold)
        return fmt

    def _append(self, text: str, color: str = "#d4d4d4", bold=False):
        cursor = self._text.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text, self._fmt(color, bold))
        self._text.setTextCursor(cursor)
        self._text.ensureCursorVisible()

    # ── API pública ───────────────────────────────────────────────────────

    def clear(self):
        self._text.clear()
        self._progress.setValue(0)
        self._prog_label.setText("")

    def set_progress(self, value: float, label: str = ""):
        self._progress.setValue(int(value))
        self._prog_label.setText(label)

    def log_file_result(self, fr: FileProcessResult):
        path_str = str(fr.path)

        if fr.error and not fr.result:
            self._append(f"✗  {path_str}\n", "#f47070")
            self._append(f"   └─ {fr.error}\n", "#f47070")
            return

        if fr.skipped:
            self._append(f"─  {path_str}  (sin cambios)\n", "#888888")
            return

        if fr.result and fr.result.total_count > 0:
            self._append(f"✔  {path_str}", "#61b0ff")
            self._append(f"  [{fr.result.total_count} reemplazo(s)]\n", "#61b0ff")
        else:
            self._append(f"─  {path_str}  (sin cambios)\n", "#888888")

        if fr.result and fr.result.skipped_blocks:
            bloques = ", ".join(str(i) for i in fr.result.skipped_blocks)
            self._append(f"   └─ Bloques saltados por condición: {bloques}\n", "#c0a030")

        if fr.result and fr.result.errors:
            for idx, err in fr.result.errors:
                self._append(f"   └─ Error bloque {idx}: {err}\n", "#f47070")

        if fr.error:
            self._append(f"   └─ {fr.error}\n", "#f47070")

    def log_batch_summary(self, batch: BatchResult):
        sep = "─" * 60
        self._append(f"\n{sep}\n", "#ffd700", bold=True)
        self._append(
            f"  Total archivos : {batch.total_files}\n"
            f"  Modificados    : {batch.processed - batch.skipped}\n"
            f"  Sin cambios    : {batch.skipped}\n"
            f"  Errores        : {batch.errors}\n"
            f"  Reemplazos     : {batch.total_replacements}\n",
            "#ffd700", bold=True
        )
        self._append(f"{sep}\n", "#ffd700", bold=True)
