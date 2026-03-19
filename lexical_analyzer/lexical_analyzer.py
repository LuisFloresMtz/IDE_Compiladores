tokenTypes = {
    'KEYWORD': 1,
    'IDENTIFIER': 2,
    'INTEGER': 3,
    'FLOAT': 4,
    'OPERATOR': 5,
    'DELIMITER': 6,
    'STRING_LITERAL': 7,
    'COMMENT': 8,
    'WHITESPACE': 9,
    'UNKNOWN': 10
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
                if char is not None:
                    ungetChar()  # retrocede el char leído tras el punto
                ungetChar()      # retrocede el punto
                return ('INTEGER', token)
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
        return ('UNKNOWN', token)   # cadena sin cerrar

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
                    return ('UNKNOWN', token)   # comentario sin cerrar
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
        return ('UNKNOWN', char)


if __name__ == '__main__':
    print("Ingrese código (Ctrl+D o Ctrl+Z para terminar):")
    while not EOF_flag:
        tok = getToken()
        if tok is None:
            break
        print(f"  {tok[0]:20s} → {tok[1]!r}")
