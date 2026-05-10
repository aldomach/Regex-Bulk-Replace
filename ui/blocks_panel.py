"""
ui/blocks_panel.py  (PySide6)
------------------------------
Panel de bloques patrón/reemplazo.
- Campos multilínea con scroll nativo de Qt
- Checkboxes en grilla 2 columnas
- Condición expandible por bloque
- Contador de módulos
- Plantillas desde templates.json
- Guardar como plantilla nueva
"""

from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QCheckBox, QScrollArea, QSizePolicy,
    QGroupBox, QDialog, QListWidget, QTextEdit, QSplitter,
    QLineEdit, QMessageBox, QInputDialog, QDialogButtonBox,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from core.replacer import ReplaceBlock
from utils.template_manager import load_templates, save_templates, Template


# ── BlockRow ──────────────────────────────────────────────────────────────────

class BlockRow(QFrame):
    """Una fila visual que representa un ReplaceBlock."""

    removed  = Signal(object)   # emite self cuando se presiona ✕
    changed  = Signal()         # emite cuando el contenido cambia

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setObjectName("BlockRow")
        self._cond_visible = False
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(2)

        # ── Fila principal ────────────────────────────────────────────────
        main_row = QHBoxLayout()
        main_row.setSpacing(4)
        root.addLayout(main_row)

        # Patrón
        pat_box = QVBoxLayout()
        pat_box.setSpacing(1)
        pat_box.addWidget(QLabel("Patrón:"))
        self._txt_pattern = QTextEdit()
        self._txt_pattern.setFixedHeight(64)
        self._txt_pattern.setLineWrapMode(QTextEdit.NoWrap)
        self._txt_pattern.setPlaceholderText("patrón a buscar…")
        self._txt_pattern.setFont(self._mono_font())
        self._txt_pattern.textChanged.connect(self.changed)
        pat_box.addWidget(self._txt_pattern)
        main_row.addLayout(pat_box, 3)

        # Botón invertir
        btn_inv = QPushButton("⇄")
        btn_inv.setFixedWidth(28)
        btn_inv.setToolTip("Intercambiar patrón y reemplazo")
        btn_inv.clicked.connect(self._invert)
        main_row.addWidget(btn_inv, 0, Qt.AlignVCenter)

        # Reemplazo
        rep_box = QVBoxLayout()
        rep_box.setSpacing(1)
        rep_box.addWidget(QLabel("Reemplazo:"))
        self._txt_replacement = QTextEdit()
        self._txt_replacement.setFixedHeight(64)
        self._txt_replacement.setLineWrapMode(QTextEdit.NoWrap)
        self._txt_replacement.setPlaceholderText("texto de reemplazo…")
        self._txt_replacement.setFont(self._mono_font())
        rep_box.addWidget(self._txt_replacement)
        main_row.addLayout(rep_box, 3)

        # Checkboxes en grilla 2 col
        chk_grid = QGridLayout()
        chk_grid.setSpacing(2)
        chk_grid.setContentsMargins(4, 0, 4, 0)

        self._chk_regex = QCheckBox("Regex");     self._chk_regex.setChecked(True)
        self._chk_case  = QCheckBox("Case")
        self._chk_whole = QCheckBox("Pal.")
        self._chk_dot   = QCheckBox("Dot");       self._chk_dot.setStyleSheet("color:#0055aa")
        self._chk_multi = QCheckBox("Multi");     self._chk_multi.setStyleSheet("color:#0055aa")

        chk_grid.addWidget(self._chk_regex, 0, 0)
        chk_grid.addWidget(self._chk_case,  0, 1)
        chk_grid.addWidget(self._chk_whole, 1, 0)
        chk_grid.addWidget(self._chk_dot,   1, 1)
        chk_grid.addWidget(self._chk_multi, 2, 0)

        main_row.addLayout(chk_grid, 0)

        # Botones ⚙ y ✕
        btn_col = QVBoxLayout()
        btn_col.setSpacing(4)
        self._btn_cond = QPushButton("⚙▾")
        self._btn_cond.setFixedWidth(36)
        self._btn_cond.setToolTip("Mostrar/ocultar condición")
        self._btn_cond.setCheckable(True)
        self._btn_cond.clicked.connect(self._toggle_cond)
        btn_col.addWidget(self._btn_cond)

        btn_del = QPushButton("✕")
        btn_del.setFixedWidth(36)
        btn_del.setStyleSheet("color:red")
        btn_del.clicked.connect(lambda: self.removed.emit(self))
        btn_col.addWidget(btn_del)
        btn_col.addStretch()
        main_row.addLayout(btn_col, 0)

        # ── Fila condición (oculta) ───────────────────────────────────────
        self._cond_frame = QFrame()
        self._cond_frame.setStyleSheet("background:#fffbe6; border:1px solid #e0d080; border-radius:3px")
        cond_row = QHBoxLayout(self._cond_frame)
        cond_row.setContentsMargins(6, 4, 6, 4)
        cond_row.addWidget(QLabel("Solo aplicar si el archivo contiene (regex):"))
        self._cond_entry = QLineEdit()
        self._cond_entry.setPlaceholderText("regex de condición…")
        cond_row.addWidget(self._cond_entry, 1)
        self._cond_frame.hide()
        root.addWidget(self._cond_frame)

    @staticmethod
    def _mono_font():
        from PySide6.QtGui import QFont
        f = QFont("Courier New")
        f.setPointSize(9)
        return f

    # ── Slots ─────────────────────────────────────────────────────────────

    def _toggle_cond(self, checked):
        self._cond_frame.setVisible(checked)
        self._btn_cond.setText("⚙▴" if checked else "⚙▾")

    def _invert(self):
        pat = self._txt_pattern.toPlainText()
        rep = self._txt_replacement.toPlainText()
        self._txt_pattern.setPlainText(rep)
        self._txt_replacement.setPlainText(pat)

    def has_content(self) -> bool:
        return bool(self._txt_pattern.toPlainText().strip())

    # ── API pública ───────────────────────────────────────────────────────

    def to_block(self) -> ReplaceBlock:
        return ReplaceBlock(
            pattern=self._txt_pattern.toPlainText(),
            replacement=self._txt_replacement.toPlainText(),
            use_regex=self._chk_regex.isChecked(),
            match_case=self._chk_case.isChecked(),
            whole_word=self._chk_whole.isChecked(),
            dotall=self._chk_dot.isChecked(),
            multiline=self._chk_multi.isChecked(),
            condition=self._cond_entry.text(),
        )

    def load_block(self, block: ReplaceBlock):
        self._txt_pattern.setPlainText(block.pattern)
        self._txt_replacement.setPlainText(block.replacement)
        self._chk_regex.setChecked(block.use_regex)
        self._chk_case.setChecked(block.match_case)
        self._chk_whole.setChecked(block.whole_word)
        self._chk_dot.setChecked(block.dotall)
        self._chk_multi.setChecked(block.multiline)
        self._cond_entry.setText(block.condition)
        if block.condition.strip():
            self._btn_cond.setChecked(True)
            self._toggle_cond(True)


# ── BlocksPanel ───────────────────────────────────────────────────────────────

class BlocksPanel(QGroupBox):
    """Panel completo: encabezado con contador, área scrollable, botonera."""

    def __init__(self, parent=None):
        super().__init__("Patrones y Reemplazos", parent)
        self._rows: list[BlockRow] = []
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(4)

        # ── Leyenda + contador ────────────────────────────────────────────
        legend_row = QHBoxLayout()
        legend = QLabel(
            "  <span style='color:#0055aa'>Dot</span> = punto captura saltos   |   "
            "<span style='color:#0055aa'>Multi</span> = ^ y $ por línea   |   "
            "⚙ = condición"
        )
        legend.setTextFormat(Qt.RichText)
        legend.setStyleSheet("color:#888; font-size:8pt")
        legend_row.addWidget(legend, 1)

        self._lbl_count = QLabel("0 módulos")
        self._lbl_count.setStyleSheet("font-weight:bold; color:#555")
        legend_row.addWidget(self._lbl_count)
        layout.addLayout(legend_row)

        # ── Área scrollable ───────────────────────────────────────────────
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setMinimumHeight(180)

        self._inner = QWidget()
        self._inner_layout = QVBoxLayout(self._inner)
        self._inner_layout.setSpacing(4)
        self._inner_layout.setContentsMargins(2, 2, 2, 2)
        self._inner_layout.addStretch()  # empuja filas hacia arriba
        self._scroll.setWidget(self._inner)
        layout.addWidget(self._scroll, 1)

        # ── Botonera ──────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_add = QPushButton("+ Agregar bloque")
        btn_add.clicked.connect(self.add_row)
        btn_row.addWidget(btn_add)

        btn_clear = QPushButton("✕ Limpiar todo")
        btn_clear.clicked.connect(self.clear_all)
        btn_row.addWidget(btn_clear)

        btn_row.addSpacing(20)

        btn_tpl = QPushButton("📋 Plantillas…")
        btn_tpl.setStyleSheet("color:#005599")
        btn_tpl.clicked.connect(self._show_templates)
        btn_row.addWidget(btn_tpl)

        btn_save_tpl = QPushButton("💾 Guardar como plantilla")
        btn_save_tpl.setStyleSheet("color:#006633")
        btn_save_tpl.clicked.connect(self._save_as_template)
        btn_row.addWidget(btn_save_tpl)

        btn_row.addStretch()
        layout.addLayout(btn_row)

    # ── Gestión de filas ──────────────────────────────────────────────────

    def add_row(self, block: ReplaceBlock | None = None) -> BlockRow:
        row = BlockRow()
        row.removed.connect(self._remove_row)
        row.changed.connect(self._update_counter)
        # Insertar antes del stretch
        idx = self._inner_layout.count() - 1
        self._inner_layout.insertWidget(idx, row)
        self._rows.append(row)
        if block:
            row.load_block(block)
        self._update_counter()
        # Scroll al fondo al agregar
        self._scroll.verticalScrollBar().setValue(
            self._scroll.verticalScrollBar().maximum()
        )
        return row

    def _remove_row(self, row: BlockRow):
        self._inner_layout.removeWidget(row)
        row.deleteLater()
        self._rows.remove(row)
        self._update_counter()

    def clear_all(self):
        for row in list(self._rows):
            self._inner_layout.removeWidget(row)
            row.deleteLater()
        self._rows.clear()
        self._update_counter()

    def get_blocks(self) -> list[ReplaceBlock]:
        return [r.to_block() for r in self._rows]

    def load_blocks(self, blocks: list[ReplaceBlock]):
        self.clear_all()
        for b in blocks:
            self.add_row(b)

    def block_count(self) -> int:
        return len(self._rows)

    def _update_counter(self):
        total = len(self._rows)
        active = sum(1 for r in self._rows if r.has_content())
        if total == 0:
            text = "0 módulos"
        elif active == total:
            text = f"{total} módulo{'s' if total != 1 else ''}"
        else:
            text = f"{active}/{total} con patrón"
        self._lbl_count.setText(text)

    # ── Plantillas ────────────────────────────────────────────────────────

    def _show_templates(self):
        templates = load_templates()
        dlg = TemplateDialog(templates, parent=self)
        result = dlg.exec()
        if result == QDialog.Accepted and dlg.selected_template:
            action = dlg.action
            if action == "add":
                for b in dlg.selected_template.blocks:
                    self.add_row(b)
            elif action == "replace":
                self.load_blocks(dlg.selected_template.blocks)
            elif action == "delete":
                templates.remove(dlg.selected_template)
                save_templates(templates)
                QMessageBox.information(self, "Listo", "Plantilla eliminada.")

    def _save_as_template(self):
        blocks = [r.to_block() for r in self._rows if r.has_content()]
        if not blocks:
            QMessageBox.warning(self, "Sin bloques",
                                "Agregá al menos un bloque con patrón antes de guardar.")
            return

        name, ok = QInputDialog.getText(self, "Guardar plantilla",
                                        "Nombre para la nueva plantilla:")
        if not ok or not name.strip():
            return

        desc, ok2 = QInputDialog.getText(self, "Descripción (opcional)",
                                         "Descripción breve (podés dejarlo vacío):")
        if not ok2:
            desc = ""

        templates = load_templates()
        existing = next((i for i, t in enumerate(templates) if t.name == name.strip()), None)
        if existing is not None:
            ans = QMessageBox.question(self, "Plantilla existente",
                                       f"Ya existe «{name.strip()}». ¿Reemplazarla?")
            if ans != QMessageBox.Yes:
                return
            templates[existing] = Template(name=name.strip(), description=desc.strip(), blocks=blocks)
        else:
            templates.append(Template(name=name.strip(), description=desc.strip(), blocks=blocks))

        save_templates(templates)
        QMessageBox.information(self, "Guardado",
                                f"Plantilla «{name.strip()}» guardada en templates.json.")


# ── TemplateDialog ────────────────────────────────────────────────────────────

class TemplateDialog(QDialog):
    def __init__(self, templates: list[Template], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Plantillas")
        self.resize(720, 500)
        self._templates = templates
        self.selected_template: Template | None = None
        self.action = ""
        self._build(templates)

    def _build(self, templates):
        layout = QVBoxLayout(self)

        if not templates:
            layout.addWidget(QLabel(
                "No se encontró templates.json junto al programa.\n"
                "Guardá la configuración actual como plantilla para crearlo."
            ))
            bb = QDialogButtonBox(QDialogButtonBox.Close)
            bb.rejected.connect(self.reject)
            layout.addWidget(bb)
            return

        splitter = QSplitter(Qt.Horizontal)

        # Lista
        self._list = QListWidget()
        for t in templates:
            n = len(t.blocks)
            self._list.addItem(f"{t.name}  ({n} bloque{'s' if n!=1 else ''})")
        self._list.currentRowChanged.connect(self._on_select)
        splitter.addWidget(self._list)

        # Detalle
        self._detail = QTextEdit()
        self._detail.setReadOnly(True)
        self._detail.setStyleSheet("background:#f7f7f7")
        splitter.addWidget(self._detail)
        splitter.setSizes([280, 420])
        layout.addWidget(splitter, 1)

        # Botones
        btn_row = QHBoxLayout()
        self._btn_add = QPushButton("➕ Agregar bloques al panel")
        self._btn_add.setStyleSheet("background:#2a7a2a; color:white")
        self._btn_add.clicked.connect(self._accept_add)
        btn_row.addWidget(self._btn_add)

        self._btn_replace = QPushButton("↩ Reemplazar panel completo")
        self._btn_replace.clicked.connect(self._accept_replace)
        btn_row.addWidget(self._btn_replace)

        self._btn_delete = QPushButton("🗑 Eliminar plantilla")
        self._btn_delete.setStyleSheet("color:#aa0000")
        self._btn_delete.clicked.connect(self._accept_delete)
        btn_row.addWidget(self._btn_delete)

        btn_row.addStretch()
        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(self.reject)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

        if templates:
            self._list.setCurrentRow(0)

    def _on_select(self, row):
        if row < 0 or row >= len(self._templates):
            return
        t = self._templates[row]
        lines = [f"<b>{t.name}</b>"]
        if t.description:
            lines.append(f"<i>{t.description}</i>")
        lines.append(f"<br>── {len(t.blocks)} bloque(s) ──<br>")
        for i, b in enumerate(t.blocks, 1):
            flags = []
            if b.use_regex:   flags.append("Regex")
            if b.dotall:      flags.append("Dot")
            if b.multiline:   flags.append("Multi")
            if b.match_case:  flags.append("Case")
            if b.whole_word:  flags.append("Pal.")
            pat_esc = b.pattern.replace("<","&lt;").replace(">","&gt;")
            rep_esc = repr(b.replacement).replace("<","&lt;").replace(">","&gt;")
            lines.append(
                f"<b>[{i}]</b> Patrón: <code>{pat_esc}</code><br>"
                f"&nbsp;&nbsp;&nbsp;&nbsp; Reemplazo: <code>{rep_esc}</code><br>"
                f"&nbsp;&nbsp;&nbsp;&nbsp; Flags: {', '.join(flags) or '—'}"
            )
            if b.condition:
                lines.append(f"&nbsp;&nbsp;&nbsp;&nbsp; Condición: <code>{b.condition}</code>")
            lines.append("")
        self._detail.setHtml("<br>".join(lines))

    def _current_template(self) -> Template | None:
        row = self._list.currentRow()
        if 0 <= row < len(self._templates):
            return self._templates[row]
        return None

    def _accept_add(self):
        self.selected_template = self._current_template()
        self.action = "add"
        self.accept()

    def _accept_replace(self):
        self.selected_template = self._current_template()
        self.action = "replace"
        self.accept()

    def _accept_delete(self):
        t = self._current_template()
        if not t:
            return
        ans = QMessageBox.question(self, "Eliminar",
                                   f"¿Eliminar la plantilla «{t.name}»?")
        if ans == QMessageBox.Yes:
            self.selected_template = t
            self.action = "delete"
            self.accept()
