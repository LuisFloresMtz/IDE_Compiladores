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
        comment_fmt = self.formats['COMMENT']
        in_comment = self.previousBlockState() == 1
        offset = 0

        # Si venimos de un /* abierto en un bloque anterior, pintar
        # hasta el cierre */ (o toda la línea si sigue sin cerrar).
        if in_comment:
            close = text.find('*/')
            if close == -1:
                self.setFormat(0, len(text), comment_fmt)
                self.setCurrentBlockState(1)
                return
            close_end = close + 2
            self.setFormat(0, close_end, comment_fmt)
            offset = close_end

        remainder = text[offset:]
        if not remainder:
            self.setCurrentBlockState(0)
            return

        try:
            tokens = tokenize_with_positions(remainder)
        except Exception:
            self.setCurrentBlockState(0)
            return

        carry = False
        for tok_type, value, start, end in tokens:
            # Un ERROR al final de la línea que empieza con "/*" es un
            # comentario multilínea que no cerró en esta línea → lo
            # pintamos como COMMENT y mantenemos el estado para la
            # siguiente línea.
            if (tok_type == 'ERROR'
                    and value.startswith('/*')
                    and end == len(remainder)):
                self.setFormat(offset + start, end - start, comment_fmt)
                carry = True
                continue
            fmt = self.formats.get(tok_type)
            if fmt is not None:
                self.setFormat(offset + start, end - start, fmt)

        self.setCurrentBlockState(1 if carry else 0)
