from PySide6.QtWidgets import QPlainTextEdit, QWidget, QTextEdit
from PySide6.QtGui import QColor, QPainter, QTextFormat, QTextCursor, QFont
from PySide6.QtCore import Qt, QRect, QSize, Signal


try:
    from ui.top_bar import COLORS
except ImportError:
    COLORS = {
        "bg_dark":      "#1e1e2e",
        "bg_bar":       "#181825",
        "bg_hover":     "#313244",
        "bg_pressed":   "#45475a",
        "accent":       "#89b4fa",
        "accent_dim":   "#585b70",
        "text":         "#cdd6f4",
        "text_dim":     "#a6adc8",
        "border":       "#313244",
    }

# ── Colores internos del editor ───────────────────────────────────────────────
EDITOR = {
    "bg":           "#1e1e2e",   # fondo del editor
    "bg_gutter":    "#181825",   # fondo del gutter (números de línea)
    "line_hl":      "#2a2a3d",   # resaltado de línea actual
    "gutter_text":  "#585b70",   # números de línea (inactivos)
    "gutter_active":"#89b4fa",   # número de línea activo
    "caret":        "#f5c2e7",   # cursor
    "selection":    "#45475a",   # selección
    "text":         "#cdd6f4",   # texto principal
    "scrollbar":    "#313244",   # handle scrollbar
    "scrollbar_hl": "#89b4fa",   # handle scrollbar hover
}

EDITOR_QSS = f"""
QPlainTextEdit {{
    background-color: {EDITOR['bg']};
    color: {EDITOR['text']};
    font-family: 'JetBrains Mono', 'Cascadia Code', 'Consolas', monospace;
    font-size: 14px;
    border: none;
    selection-background-color: {EDITOR['selection']};
    selection-color: {EDITOR['text']};
}}

QScrollBar:vertical {{
    background: {EDITOR['bg_gutter']};
    width: 10px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {EDITOR['scrollbar']};
    border-radius: 5px;
    min-height: 24px;
}}

QScrollBar::handle:vertical:hover {{
    background: {EDITOR['scrollbar_hl']};
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background: {EDITOR['bg_gutter']};
    height: 10px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background: {EDITOR['scrollbar']};
    border-radius: 5px;
    min-width: 24px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {EDITOR['scrollbar_hl']};
}}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    width: 0;
}}
"""


class LineNumberArea(QWidget):
    def __init__(self, editor: "CodeEditor"):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self.editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.editor.lineNumberAreaPaintEvent(event)


class CodeEditor(QPlainTextEdit):

    cursorPositionInfo = Signal(int, int)   # (línea, columna)

    def __init__(self):
        super().__init__()

        self.lineNumberArea = LineNumberArea(self)

        # ── Señales ───────────────────────────────────────────────────────────
        self.document().blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.verticalScrollBar().valueChanged.connect(self.updateLineNumberArea)
        self.textChanged.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.onCursorPositionChanged)

        # ── Setup inicial ─────────────────────────────────────────────────────
        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()

        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * 4)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.setStyleSheet(EDITOR_QSS)

    # ── Gutter / números de línea ─────────────────────────────────────────────

    def lineNumberAreaWidth(self) -> int:
        digits = len(str(max(1, self.blockCount())))
        padding = 24  # margen izq + der
        return padding + self.fontMetrics().horizontalAdvance("9") * digits

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, *args):
        self.lineNumberArea.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(
            QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height())
        )

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), QColor(EDITOR["bg_gutter"]))

        # Línea separadora sutil entre gutter y editor
        sep_x = self.lineNumberArea.width() - 1
        painter.setPen(QColor(COLORS["border"]))
        painter.drawLine(sep_x, event.rect().top(), sep_x, event.rect().bottom())

        current_block_number = self.textCursor().blockNumber()

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)

                # Número activo más brillante
                if block_number == current_block_number:
                    painter.setPen(QColor(EDITOR["gutter_active"]))
                    font = painter.font()
                    font.setBold(True)
                    painter.setFont(font)
                else:
                    painter.setPen(QColor(EDITOR["gutter_text"]))
                    font = painter.font()
                    font.setBold(False)
                    painter.setFont(font)

                painter.drawText(
                    0, top,
                    self.lineNumberArea.width() - 8,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    number,
                )

            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    # ── Resaltado de línea actual ─────────────────────────────────────────────

    def highlightCurrentLine(self):
        extra_selections = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(QColor(EDITOR["line_hl"]))
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)

        self.setExtraSelections(extra_selections)

    # ── Eventos ───────────────────────────────────────────────────────────────

    def onCursorPositionChanged(self):
        cursor = self.textCursor()
        self.cursorPositionInfo.emit(
            cursor.blockNumber() + 1,
            cursor.positionInBlock() + 1,
        )
        self.highlightCurrentLine()
        self.lineNumberArea.update()   # refrescar gutter para el número activo

    def keyPressEvent(self, event):
        # Tab → 4 espacios
        if event.key() == Qt.Key.Key_Tab:
            self.insertPlainText(" " * 4)
            return

        # Enter → preservar indentación
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
            current_line = cursor.block().text()
            indent = len(current_line) - len(current_line.lstrip(" "))
            super().keyPressEvent(event)
            self.insertPlainText(" " * indent)
            return

        # Backspace inteligente — borra 4 espacios si son indentación
        if event.key() == Qt.Key.Key_Backspace:
            cursor = self.textCursor()
            if not cursor.hasSelection():
                pos = cursor.positionInBlock()
                line = cursor.block().text()
                # Si los caracteres anteriores son todos espacios y múltiplo de 4
                if pos > 0 and line[:pos].strip() == "":
                    spaces = pos % 4 or 4
                    for _ in range(spaces):
                        cursor.deletePreviousChar()
                    return

        super().keyPressEvent(event)