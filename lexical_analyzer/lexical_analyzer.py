tokenTypes = {
    'KEYWORD': 1,
    'IDENTIFIER': 2,
    'INTEGER': 3,
    'FLOAT': 4,
    'STRING_LITERAL': 5,
    'COMMENT': 6,
    'WHITESPACE': 7,
    'ERROR': 8
}

line = ""
linepos = 0
EOF_flag = False

_source = None
_source_pos = 0


def getNextChar():
    global line, linepos, EOF_flag, _source, _source_pos
    if EOF_flag:
        return None
    if _source is not None:
        if _source_pos >= len(_source):
            EOF_flag = True
            return None
        char = _source[_source_pos]
        _source_pos += 1
        return char
    if linepos >= len(line):
        try:
            line = input() + '\n'   # '\n' permite detectar salto de línea
            linepos = 0
        except EOFError:
            EOF_flag = True
            return None
    char = line[linepos]
    linepos += 1
    return char


def ungetChar():
    global linepos, _source_pos
    if _source is not None:
        if _source_pos > 0:
            _source_pos -= 1
        return
    if linepos > 0:
        linepos -= 1


def tokenize(source):
    global _source, _source_pos, EOF_flag
    _source = source
    _source_pos = 0
    EOF_flag = False
    tokens = []
    while not EOF_flag:
        tok = getToken()
        if tok is None:
            break
        tokens.append(tok)
    _source = None
    return tokens


def tokenize_with_positions(source):
    """Como tokenize(), pero devuelve (tipo, valor, start, end) con los
    offsets (en caracteres) de cada token dentro de `source`. Útil para
    resaltar sintaxis en el editor."""
    global _source, _source_pos, EOF_flag
    _source = source
    _source_pos = 0
    EOF_flag = False
    tokens = []
    while True:
        # Saltar whitespace aquí para poder capturar el offset inicial
        # del siguiente token antes de que getToken consuma caracteres.
        while _source_pos < len(_source) and _source[_source_pos].isspace():
            _source_pos += 1
        if _source_pos >= len(_source):
            break
        EOF_flag = False
        start = _source_pos
        tok = getToken()
        if tok is None:
            break
        end = _source_pos
        tokens.append((tok[0], tok[1], start, end))
    _source = None
    return tokens


def getToken():
    token = ""
    char = getNextChar()

    while char is not None and char.isspace():
        char = getNextChar()

    if char is None:
        return None

    # Entrada ID
    if char.isalpha() or char == '_':
        while char is not None and (char.isalnum() or char == '_'):
            token += char
            char = getNextChar()
        if char is not None:
            ungetChar()
        if token in ['if', 'else', 'while', 'for', 'return']:
            return ('KEYWORD', token)
        return ('IDENTIFIER', token)

    # Entrada INT / FLOAT
    elif char.isdigit():
        while char is not None and char.isdigit():
            token += char
            char = getNextChar()
        if char == '.':
            char = getNextChar()
            if char is not None and char.isdigit():
                token += '.'
                while char is not None and char.isdigit():
                    token += char
                    char = getNextChar()
                if char is not None:
                    ungetChar()
                return ('FLOAT', token)
            else:
                # Longest match: se consumió el punto pero no hay dígitos
                # después → toda la subcadena "NN." es un token inválido.
                if char is not None:
                    ungetChar()  # retrocede el char leído tras el punto
                token += '.'
                return ('ERROR', token)
        if char is not None:
            ungetChar()
        return ('INTEGER', token)

    # Entrada CADENA
    elif char == '"':
        token += char
        char = getNextChar()
        while char is not None and char != '"':
            token += char
            char = getNextChar()
        if char == '"':
            token += char
            return ('STRING_LITERAL', token)
        return ('ERROR', token)   # cadena sin cerrar

    # Entrada IGUAL (= / ==)
    elif char == '=':
        token += char
        char = getNextChar()
        if char == '=':
            token += char
            return ('OPERATOR', token)
        if char is not None:
            ungetChar()
        return ('OPERATOR', token)

    # Entrada DELIMITADORES
    elif char in [';', '(', ')', '{', '}', '[', ']', ':']:
        return ('DELIMITER', char)

    # Entrada MENOS (- / --)
    elif char == '-':
        token += char
        char = getNextChar()
        if char == '-':
            token += char
            return ('OPERATOR', token)
        if char is not None:
            ungetChar()
        return ('OPERATOR', token)

    # Entrada MÁS (+ / ++)
    elif char == '+':
        token += char
        char = getNextChar()
        if char == '+':
            token += char
            return ('OPERATOR', token)
        if char is not None:
            ungetChar()
        return ('OPERATOR', token)

    # Entrada MENOR (< / <=)
    elif char == '<':
        token += char
        char = getNextChar()
        if char == '=':
            token += char
            return ('OPERATOR', token)
        if char is not None:
            ungetChar()
        return ('OPERATOR', token)

    # Entrada MAYOR (> / >=)
    elif char == '>':
        token += char
        char = getNextChar()
        if char == '=':
            token += char
            return ('OPERATOR', token)
        if char is not None:
            ungetChar()
        return ('OPERATOR', token)

    # Entrada OPERADORES
    elif char in ['*', '%', '^']:
        return ('OPERATOR', char)

    # Entrada NEGACION (! / !=)
    elif char == '!':
        token += char
        char = getNextChar()
        if char == '=':
            token += char
            return ('OPERATOR', token)
        if char is not None:
            ungetChar()
        return ('OPERATOR', token)

    # Entrada DIVISION / COMENTARIOS
    elif char == '/':
        token += char
        char = getNextChar()
        if char == '/':                         # comentario unilínea
            token += char
            char = getNextChar()
            while char is not None and char != '\n':
                token += char
                char = getNextChar()
            return ('COMMENT', token)
        elif char == '*':                       # comentario multilínea
            token += char
            char = getNextChar()
            while True:
                if char is None:
                    return ('ERROR', token)   # comentario sin cerrar
                if char == '*':
                    token += char
                    char = getNextChar()
                    if char == '/':
                        token += char
                        return ('COMMENT', token)
                else:
                    token += char
                    char = getNextChar()
        else:
            if char is not None:
                ungetChar()
            return ('OPERATOR', token)

    else:
        return ('ERROR', char)


if __name__ == '__main__':
    print("Ingrese código (Ctrl+D o Ctrl+Z para terminar):")
    while not EOF_flag:
        tok = getToken()
        if tok is None:
            break
        print(f"  {tok[0]:20s} → {tok[1]!r}")
