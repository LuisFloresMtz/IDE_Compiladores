from PySide6.QtWidgets import QPlainTextEdit, QWidget, QTextEdit
from PySide6.QtGui import QColor, QPainter, QTextFormat, QTextCursor
from PySide6.QtCore import Qt, QRect, QSize, Signal


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.editor.lineNumberAreaPaintEvent(event)


class CodeEditor(QPlainTextEdit):

    cursorPositionInfo = Signal(int, int)  # (linea, columna)

    def __init__(self):
        super().__init__()

        self.lineNumberArea = LineNumberArea(self)

        self.document().blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.verticalScrollBar().valueChanged.connect(self.updateLineNumberArea)
        self.textChanged.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.onCursorPositionChanged)

        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()

        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * 4)

        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: white;
                font-family: Consolas;
                font-size: 16px;
                border: none;
            }
        """)

    def lineNumberAreaWidth(self):
        digits = len(str(max(1, self.blockCount())))
        space = 12 + self.fontMetrics().horizontalAdvance("9") * digits
        return space

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
        painter.fillRect(event.rect(), QColor("#2b2b2b"))

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()

        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.setPen(QColor("#aaaaaa"))

                painter.drawText(
                    0,
                    top,
                    self.lineNumberArea.width() - 5,
                    self.fontMetrics().height(),
                    Qt.AlignRight,
                    number
                )

            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            blockNumber += 1

    def highlightCurrentLine(self):
        extraSelections = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()

            lineColor = QColor("#333333")
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)

            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()

            extraSelections.append(selection)

        self.setExtraSelections(extraSelections)

    def onCursorPositionChanged(self):
        cursor = self.textCursor()

        line = cursor.blockNumber() + 1
        col = cursor.positionInBlock() + 1

        self.cursorPositionInfo.emit(line, col)
        self.highlightCurrentLine()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Tab:
            self.insertPlainText(" " * 4)
            return

        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.StartOfBlock)
            current_line = cursor.block().text()

            indent = len(current_line) - len(current_line.lstrip(" "))

            super().keyPressEvent(event)
            self.insertPlainText(" " * indent)
            return

        super().keyPressEvent(event)
