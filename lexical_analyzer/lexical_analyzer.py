tokenTypes = {
    'KEYWORD': 1,
    'IDENTIFIER': 2,
    'INTEGER': 3,
    'FLOAT': 4,
    'STRING_LITERAL': 5,
    'COMMENT': 6,
    'ERROR': 7
}

# Categoría de cada operador agrupado por tipo.
OPERATOR_CATEGORY = {
    '=':  'ASIGNACION',
    '==': 'RELACIONAL',
    '!=': 'RELACIONAL',
    '<':  'RELACIONAL',
    '<=': 'RELACIONAL',
    '>':  'RELACIONAL',
    '>=': 'RELACIONAL',
    '!':  'LOGICO',
    '&&': 'LOGICO',
    '||': 'LOGICO',
    '+':  'ARITMETICO',
    '++': 'ARITMETICO',
    '-':  'ARITMETICO',
    '--': 'ARITMETICO',
    '*':  'ARITMETICO',
    '/':  'ARITMETICO',
    '%':  'ARITMETICO',
    '^':  'ARITMETICO',
}


def operator_category(value: str) -> str:
    """Devuelve la categoría del operador (ARITMETICO, RELACIONAL, LOGICO, ASIGNACION)."""
    return OPERATOR_CATEGORY.get(value, 'OPERATOR')

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


def _try_match_next(expected):
    """Salta espacios, tabs y saltos de línea y verifica si el siguiente
    carácter coincide con `expected`. Si coincide, lo consume junto con el
    whitespace intermedio y devuelve True. Si no coincide, restaura el estado
    original y devuelve False.

    Gracias a este helper, un par como «=  =» (o incluso separado por saltos
    de línea) se reconoce como el operador «==»."""
    global _source_pos, linepos, line, EOF_flag
    if _source is not None:
        saved = _source_pos
        while (_source_pos < len(_source)
               and _source[_source_pos] in (' ', '\t', '\n', '\r')):
            _source_pos += 1
        if _source_pos < len(_source) and _source[_source_pos] == expected:
            _source_pos += 1
            return True
        _source_pos = saved
        return False
    # Modo interactivo: no intentamos restaurar estado multilínea, así que
    # sólo miramos el siguiente carácter de la línea actual.
    saved_linepos = linepos
    char = getNextChar()
    while char is not None and char in (' ', '\t', '\r'):
        char = getNextChar()
    if char == expected:
        return True
    linepos = saved_linepos
    EOF_flag = False
    return False


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
        while (_source_pos < len(_source)
               and _source[_source_pos] in (' ', '\t', '\n', '\r')):
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

    # Ignorar espacios, tabuladores y saltos de línea.
    while char is not None and (char == ' ' or char == '\t'
                                or char == '\n' or char == '\r'):
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
        if token in ['if', 'else', 'while', 'for', 'return',
                     'main', 'end', 'int', 'float', 'cin', 'cout',
                     'do', 'then', 'real', 'until', 'switch', 'case']:
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

    # Entrada CADENA (comillas dobles)
    elif char == '"':
        token += char
        char = getNextChar()
        while char is not None and char != '"' and char != '\n':
            token += char
            char = getNextChar()
        if char == '"':
            token += char
            return ('STRING_LITERAL', token)
        # Cadena sin cerrar: no consumir el salto de línea
        if char == '\n':
            ungetChar()
        return ('ERROR', token)

    # Entrada CARÁCTER (comilla simple)
    elif char == "'":
        token += char
        char = getNextChar()
        while char is not None and char != "'" and char != '\n':
            token += char
            char = getNextChar()
        if char == "'":
            token += char
            return ('STRING_LITERAL', token)
        if char == '\n':
            ungetChar()
        return ('ERROR', token)

    # Entrada IGUAL (= / ==). Acepta whitespace entre los dos «=».
    elif char == '=':
        token += char
        if _try_match_next('='):
            token += '='
            return ('OPERATOR', token)
        return ('OPERATOR', token)

    # Entrada DELIMITADORES
    elif char in [';', '(', ')', '{', '}', '[', ']', ':', ',']:
        return ('DELIMITER', char)

    # Entrada MENOS (- / --). Acepta whitespace entre los dos «-».
    elif char == '-':
        token += char
        if _try_match_next('-'):
            token += '-'
            return ('OPERATOR', token)
        return ('OPERATOR', token)

    # Entrada MÁS (+ / ++). Acepta whitespace entre los dos «+».
    elif char == '+':
        token += char
        if _try_match_next('+'):
            token += '+'
            return ('OPERATOR', token)
        return ('OPERATOR', token)

    # Entrada MENOR (< / <=). Acepta whitespace entre «<» y «=».
    elif char == '<':
        token += char
        if _try_match_next('='):
            token += '='
            return ('OPERATOR', token)
        return ('OPERATOR', token)

    # Entrada MAYOR (> / >=). Acepta whitespace entre «>» y «=».
    elif char == '>':
        token += char
        if _try_match_next('='):
            token += '='
            return ('OPERATOR', token)
        return ('OPERATOR', token)

    # Entrada OPERADORES
    elif char in ['*', '%', '^']:
        return ('OPERATOR', char)

    # Entrada NEGACION (! / !=). Acepta whitespace entre «!» y «=».
    elif char == '!':
        token += char
        if _try_match_next('='):
            token += '='
            return ('OPERATOR', token)
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

    # Entrada AND lógico (&&). Acepta whitespace entre los dos «&».
    elif char == '&':
        token += char
        if _try_match_next('&'):
            token += '&'
            return ('OPERATOR', token)
        return ('ERROR', token)

    # Entrada OR lógico (||). Acepta whitespace entre los dos «|».
    elif char == '|':
        token += char
        if _try_match_next('|'):
            token += '|'
            return ('OPERATOR', token)
        return ('ERROR', token)

    else:
        return ('ERROR', char)


if __name__ == '__main__':
    import sys
    source = sys.stdin.read()
    tokens = tokenize_with_positions(source)
    for tipo, valor, start, _end in tokens:
        line_no = source.count('\n', 0, start) + 1
        if tipo == 'OPERATOR':
            categoria = operator_category(valor)
            print(f"  L{line_no:<3d} {categoria:15s} → {valor!r}")
        else:
            print(f"  L{line_no:<3d} {tipo:15s} → {valor!r}")
