"""
ui/diff_panel.py  (PySide6)
----------------------------
Panel de comparación antes/después para modo simulación.
Lista de archivos | comparador ANTES/DESPUÉS lado a lado sincronizado.
Botones: Aplicar archivo actual | Aplicar todos.
"""

import difflib
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QListWidget, QLabel, QPushButton, QTextEdit,
    QFrame, QMessageBox,
)
from PySide6.QtGui import QTextCursor, QTextCharFormat, QColor, QFont
from PySide6.QtCore import Qt, QTimer

from core.batch_processor import BatchResult, FileProcessResult

_C = {
    "add_bg":  "#d4f7d4", "add_fg":  "#006600",
    "del_bg":  "#ffd4d4", "del_fg":  "#880000",
    "eq_bg":   "#f8f8f8", "eq_fg":   "#333333",
    "hdr_bg":  "#e8e8e8", "hdr_fg":  "#555555",
    "num_fg":  "#aaaaaa",
    "applied": "#c8f0c8",
    "sel":     "#cce5ff",
}


def _fmt(bg: str, fg: str, bold=False) -> QTextCharFormat:
    f = QTextCharFormat()
    f.setBackground(QColor(bg))
    f.setForeground(QColor(fg))
    if bold:
        f.setFontWeight(QFont.Bold)
    return f


# Formatos reutilizables
FMT_ADD  = _fmt(_C["add_bg"], _C["add_fg"])
FMT_DEL  = _fmt(_C["del_bg"], _C["del_fg"])
FMT_EQ   = _fmt(_C["eq_bg"],  _C["eq_fg"])
FMT_HDR  = _fmt(_C["hdr_bg"], _C["hdr_fg"], bold=True)
FMT_NUM  = _fmt("#ffffff",    _C["num_fg"])


class SyncTextEdit(QTextEdit):
    """QTextEdit de solo lectura con scroll sincronizable."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setLineWrapMode(QTextEdit.NoWrap)
        f = QFont("Courier New", 9)
        self.setFont(f)
        self._sync_target: "SyncTextEdit | None" = None
        self._syncing = False

    def set_sync(self, other: "SyncTextEdit"):
        self._sync_target = other
        self.verticalScrollBar().valueChanged.connect(self._on_vscroll)

    def _on_vscroll(self, value):
        if self._sync_target and not self._syncing:
            self._syncing = True
            self._sync_target.verticalScrollBar().setValue(value)
            self._syncing = False

    def append_text(self, text: str, fmt: QTextCharFormat):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text, fmt)

    def clear_content(self):
        self.clear()


class DiffPanel(QWidget):

    def __init__(self, encoding_getter=None, parent=None):
        super().__init__(parent)
        self._results: list[FileProcessResult] = []
        self._applied: set[int] = set()
        self._current_idx = -1
        self._encoding_getter = encoding_getter
        self._build()

    # ── Construcción ─────────────────────────────────────────────────────

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(6)

        # ── Panel izquierdo ───────────────────────────────────────────────
        left = QWidget()
        left.setFixedWidth(300)
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(4)

        self._lbl_count = QLabel("Sin resultados")
        self._lbl_count.setStyleSheet(
            "background:#e8e8e8; padding:4px; font-weight:bold")
        left_lay.addWidget(self._lbl_count)

        self._listbox = QListWidget()
        self._listbox.currentRowChanged.connect(self._show_diff)
        left_lay.addWidget(self._listbox, 1)

        nav_row = QHBoxLayout()
        btn_prev = QPushButton("◀ Anterior"); btn_prev.clicked.connect(lambda: self._navigate(-1))
        btn_next = QPushButton("Siguiente ▶"); btn_next.clicked.connect(lambda: self._navigate(1))
        nav_row.addWidget(btn_prev); nav_row.addWidget(btn_next)
        left_lay.addLayout(nav_row)

        # Botones aplicar
        apply_frame = QFrame()
        apply_frame.setStyleSheet(
            "QFrame{background:#eef7ee; border:1px solid #aaddaa; border-radius:4px}")
        apply_lay = QVBoxLayout(apply_frame)
        apply_lay.setContentsMargins(6, 6, 6, 6)
        apply_lay.setSpacing(4)

        self._btn_apply = QPushButton("💾  Aplicar al archivo actual")
        self._btn_apply.setStyleSheet("background:#2a7a2a; color:white; font-weight:bold")
        self._btn_apply.setEnabled(False)
        self._btn_apply.clicked.connect(self._apply_current)
        apply_lay.addWidget(self._btn_apply)

        self._btn_apply_all = QPushButton("💾  Aplicar TODOS los cambios")
        self._btn_apply_all.setStyleSheet("background:#1a5a1a; color:white")
        self._btn_apply_all.setEnabled(False)
        self._btn_apply_all.clicked.connect(self._apply_all)
        apply_lay.addWidget(self._btn_apply_all)

        self._lbl_apply_status = QLabel("")
        self._lbl_apply_status.setStyleSheet("color:#226622; font-size:8pt")
        apply_lay.addWidget(self._lbl_apply_status)

        left_lay.addWidget(apply_frame)
        layout.addWidget(left)

        # ── Panel derecho: comparador ─────────────────────────────────────
        right = QWidget()
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(2)

        hdr_row = QHBoxLayout()
        lbl_b = QLabel("  ANTES")
        lbl_b.setStyleSheet(f"background:{_C['del_bg']}; color:{_C['del_fg']}; font-weight:bold; padding:3px")
        lbl_a = QLabel("  DESPUÉS")
        lbl_a.setStyleSheet(f"background:{_C['add_bg']}; color:{_C['add_fg']}; font-weight:bold; padding:3px")
        hdr_row.addWidget(lbl_b, 1); hdr_row.addWidget(lbl_a, 1)
        right_lay.addLayout(hdr_row)

        diff_splitter = QSplitter(Qt.Horizontal)
        self._txt_before = SyncTextEdit()
        self._txt_after  = SyncTextEdit()
        self._txt_before.set_sync(self._txt_after)
        self._txt_after.set_sync(self._txt_before)
        diff_splitter.addWidget(self._txt_before)
        diff_splitter.addWidget(self._txt_after)
        diff_splitter.setSizes([500, 500])
        right_lay.addWidget(diff_splitter, 1)

        self._lbl_stats = QLabel("")
        self._lbl_stats.setStyleSheet("color:#444; font-size:9pt; padding:2px")
        right_lay.addWidget(self._lbl_stats)

        layout.addWidget(right, 1)

    # ── Carga de resultados ───────────────────────────────────────────────

    def load_results(self, batch: BatchResult):
        self._results = [
            r for r in batch.file_results
            if r.original_text is not None
            and r.result is not None
            and r.result.text != r.original_text
        ]
        self._applied = set()
        self._listbox.clear()
        self._txt_before.clear_content()
        self._txt_after.clear_content()
        self._lbl_stats.setText("")
        self._current_idx = -1

        for r in self._results:
            sym = "✕" if (r.error and not r.success) else f"+{r.result.total_count if r.result else 0}"
            self._listbox.addItem(f" {sym:>6}  {r.path.name}")

        total = len(self._results)
        self._lbl_count.setText(
            f"{total} archivo{'s' if total != 1 else ''} con cambios"
        )
        self._update_apply_buttons()

        if self._results:
            self._listbox.setCurrentRow(0)

    # ── Selección y navegación ────────────────────────────────────────────

    def _navigate(self, delta: int):
        if not self._results:
            return
        new = max(0, min(len(self._results) - 1, self._current_idx + delta))
        self._listbox.setCurrentRow(new)

    def _show_diff(self, idx: int):
        if idx < 0 or idx >= len(self._results):
            return
        self._current_idx = idx
        result = self._results[idx]

        before_lines = result.original_text.splitlines(keepends=True)
        after_lines  = result.result.text.splitlines(keepends=True) if result.result else before_lines

        nr = result.result.normal_count if result.result else 0
        rr = result.result.regex_count  if result.result else 0
        applied = idx in self._applied
        prefix = "✅ APLICADO  " if applied else ""
        self._lbl_stats.setText(
            f"  {prefix}📄 {result.path}   |   "
            f"normales: {nr}   regex: {rr}   total: {nr + rr}"
        )

        self._render_diff(before_lines, after_lines)
        item = self._listbox.item(idx)
        if item:
            item.setBackground(QColor(_C["applied"] if applied else _C["sel"]))
        self._update_apply_buttons()

    # ── Renderizado del diff ──────────────────────────────────────────────

    def _render_diff(self, before: list[str], after: list[str]):
        self._txt_before.clear_content()
        self._txt_after.clear_content()

        CONTEXT = 4
        opcodes = difflib.SequenceMatcher(None, before, after).get_opcodes()

        show_before: set[int] = set()
        show_after:  set[int] = set()
        for tag, i1, i2, j1, j2 in opcodes:
            if tag != "equal":
                for i in range(max(0, i1 - CONTEXT), min(len(before), i2 + CONTEXT)):
                    show_before.add(i)
                for j in range(max(0, j1 - CONTEXT), min(len(after), j2 + CONTEXT)):
                    show_after.add(j)

        if len(before) <= 80:
            show_before = set(range(len(before)))
            show_after  = set(range(len(after)))

        last_b = last_a = -1

        for tag, i1, i2, j1, j2 in opcodes:
            if i1 > last_b + 1 and last_b >= 0:
                omit_b = i1 - last_b - 1
                omit_a = j1 - last_a - 1
                self._txt_before.append_text(f"  ··· {omit_b} líneas omitidas ···\n", FMT_HDR)
                self._txt_after.append_text( f"  ··· {omit_a} líneas omitidas ···\n", FMT_HDR)

            if tag == "equal":
                for i in [i for i in range(i1, i2) if i in show_before]:
                    j = j1 + (i - i1)
                    ln = f"{i+1:>4} │ "
                    self._txt_before.append_text(ln, FMT_NUM)
                    self._txt_before.append_text(before[i], FMT_EQ)
                    self._txt_after.append_text(ln, FMT_NUM)
                    self._txt_after.append_text(after[j] if j < len(after) else "\n", FMT_EQ)
                last_b = i2 - 1; last_a = j2 - 1

            elif tag == "replace":
                for i in range(i1, i2):
                    self._txt_before.append_text(f"{i+1:>4} │ ", FMT_NUM)
                    self._txt_before.append_text(before[i], FMT_DEL)
                for j in range(j1, j2):
                    self._txt_after.append_text(f"{j+1:>4} │ ", FMT_NUM)
                    self._txt_after.append_text(after[j], FMT_ADD)
                diff = (i2 - i1) - (j2 - j1)
                blank_fmt = _fmt("#f0f0f0", "#aaaaaa")
                for _ in range(diff):
                    self._txt_after.append_text("     │\n", blank_fmt)
                for _ in range(-diff):
                    self._txt_before.append_text("     │\n", blank_fmt)
                last_b = i2 - 1; last_a = j2 - 1

            elif tag == "delete":
                for i in range(i1, i2):
                    self._txt_before.append_text(f"{i+1:>4} │ ", FMT_NUM)
                    self._txt_before.append_text(before[i], FMT_DEL)
                    self._txt_after.append_text("     │\n", FMT_NUM)
                last_b = i2 - 1; last_a = j2 - 1

            elif tag == "insert":
                for j in range(j1, j2):
                    self._txt_after.append_text(f"{j+1:>4} │ ", FMT_NUM)
                    self._txt_after.append_text(after[j], FMT_ADD)
                    self._txt_before.append_text("     │\n", FMT_NUM)
                last_b = i2 - 1; last_a = j2 - 1

        # Scroll al inicio
        for t in (self._txt_before, self._txt_after):
            t.verticalScrollBar().setValue(0)

    # ── Aplicar cambios ───────────────────────────────────────────────────

    def _get_encoding(self) -> str:
        return self._encoding_getter() if self._encoding_getter else "utf-8"

    def _apply_current(self):
        idx = self._current_idx
        if idx < 0 or idx >= len(self._results) or idx in self._applied:
            return
        result = self._results[idx]
        if not result.result:
            return
        try:
            result.path.write_text(result.result.text, encoding=self._get_encoding())
            self._applied.add(idx)
            item = self._listbox.item(idx)
            if item:
                item.setBackground(QColor(_C["applied"]))
            self._lbl_apply_status.setText(
                f"✅ {len(self._applied)}/{len(self._results)} archivos aplicados")
            self._update_apply_buttons()
            self._show_diff(idx)
        except Exception as e:
            QMessageBox.critical(self, "Error al guardar",
                                 f"No se pudo escribir:\n{result.path}\n\n{e}")

    def _apply_all(self):
        pendientes = [i for i in range(len(self._results)) if i not in self._applied]
        if not pendientes:
            QMessageBox.information(self, "Listo", "Todos los archivos ya fueron aplicados.")
            return
        ans = QMessageBox.question(
            self, "Confirmar",
            f"Se escribirán {len(pendientes)} archivo(s) en disco.\n\n¿Continuar?"
        )
        if ans != QMessageBox.Yes:
            return
        errores = []
        for i in pendientes:
            r = self._results[i]
            if not r.result:
                continue
            try:
                r.path.write_text(r.result.text, encoding=self._get_encoding())
                self._applied.add(i)
                item = self._listbox.item(i)
                if item:
                    item.setBackground(QColor(_C["applied"]))
            except Exception as e:
                errores.append(f"{r.path.name}: {e}")
        self._lbl_apply_status.setText(
            f"✅ {len(self._applied)}/{len(self._results)} archivos aplicados")
        self._update_apply_buttons()
        if self._current_idx >= 0:
            self._show_diff(self._current_idx)
        if errores:
            QMessageBox.critical(self, "Errores",
                                 "No se pudieron escribir:\n" + "\n".join(errores))

    def _update_apply_buttons(self):
        idx = self._current_idx
        has = bool(self._results)
        cur_applied = idx in self._applied if idx >= 0 else False
        pendientes = len([i for i in range(len(self._results)) if i not in self._applied])

        self._btn_apply.setEnabled(has and not cur_applied and idx >= 0)
        self._btn_apply.setText(
            "✅ Ya aplicado" if cur_applied else "💾  Aplicar al archivo actual")

        self._btn_apply_all.setEnabled(pendientes > 0)
        self._btn_apply_all.setText(
            f"💾  Aplicar TODOS ({pendientes} pendientes)" if pendientes > 0
            else "✅ Todos aplicados")
