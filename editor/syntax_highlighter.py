from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor

from lexical_analyzer.lexical_analyzer import tokenize_with_positions


# Paleta de alto contraste sobre fondo oscuro.
TOKEN_COLORS = {
    'KEYWORD':        "#ff79c6",  # rosa intenso
    'IDENTIFIER':     "#f8f8f2",  # casi blanco
    'INTEGER':        "#ffb86c",  # naranja brillante
    'FLOAT':          "#ffb86c",  # naranja brillante
    'STRING_LITERAL': "#50fa7b",  # verde neón
    'COMMENT':        "#9ca3af",  # gris claro
    'OPERATOR':       "#8be9fd",  # cian brillante
    'DELIMITER':      "#f1fa8c",  # amarillo brillante
    'ERROR':          "#ff5555",  # rojo saturado
}


class LexicalHighlighter(QSyntaxHighlighter):
    """Resaltador que usa el analizador léxico del proyecto como tokenizer."""

    def __init__(self, document):
        super().__init__(document)
        self.formats = self._build_formats()

    def _build_formats(self) -> dict[str, QTextCharFormat]:
        formats: dict[str, QTextCharFormat] = {}
        for tok_type, color in TOKEN_COLORS.items():
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color))
            if tok_type == 'COMMENT':
                fmt.setFontItalic(True)
            elif tok_type == 'KEYWORD':
                fmt.setFontWeight(700)
            elif tok_type == 'ERROR':
                fmt.setUnderlineStyle(QTextCharFormat.UnderlineStyle.WaveUnderline)
                fmt.setUnderlineColor(QColor(color))
            formats[tok_type] = fmt
        return formats

    def highlightBlock(self, text: str) -> None:
        if not text:
            return
        try:
            tokens = tokenize_with_positions(text)
        except Exception:
            return
        for tok_type, _value, start, end in tokens:
            fmt = self.formats.get(tok_type)
            if fmt is not None:
                self.setFormat(start, end - start, fmt)
