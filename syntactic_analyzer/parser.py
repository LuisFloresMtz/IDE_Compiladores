"""Analizador sintáctico descendente recursivo.

Lee la lista de tokens producida por el analizador léxico
(lexical_analyzer.tokenize_with_lines → [(tipo, valor, linea, columna)]),
valida la estructura contra la gramática de la Fase 2 y construye un
Árbol Sintáctico Abstracto (AST).

Gramática (con recursión por la izquierda eliminada → forma iterativa):

    programa            → main { lista_declaracion }
    lista_declaracion   → (declaracion_variable | sentencia)*
    declaracion_variable→ tipo identificador ;
    identificador       → id (, id)*
    tipo                → int | float | bool
    lista_sentencias    → sentencia*
    sentencia           → seleccion | iteracion | repeticion
                        | sent_in | sent_out | asignacion
    asignacion          → id = sent_expresion
    sent_expresion      → expresion ; | ;
    seleccion           → if expresion then lista_sentencias
                          [ else lista_sentencias ] end
    iteracion           → while expresion lista_sentencias end
    repeticion          → do lista_sentencias while expresion
    sent_in             → cin >> id ;
    sent_out            → cout << salida
    salida              → cadena [ << expresion ] | expresion [ << cadena ]
    expresion           → expresion_simple [ rel_op expresion_simple ]
    expresion_simple    → termino (suma_op termino)*
    termino             → factor (mult_op factor)*
    factor              → componente (pot_op componente)*
    componente          → ( expresion ) | numero | id | bool
                        | op_logico componente
"""

# Conjuntos de operadores por categoría gramatical (se distinguen por valor).
REL_OP   = {'<', '<=', '>', '>=', '==', '!='}
SUMA_OP  = {'+', '-', '++', '--'}
MULT_OP  = {'*', '/', '%'}
POT_OP   = {'^'}
LOG_OP   = {'&&', '||', '!'}
TIPOS    = {'int', 'float', 'bool'}
# Palabras con las que puede comenzar una sentencia.
SENT_START_KW = {'if', 'while', 'do', 'cin', 'cout'}


class Node:
    """Nodo del AST. `type` es la etiqueta gramatical; `value` el lexema
    cuando el nodo representa un terminal concreto."""

    __slots__ = ('type', 'value', 'line', 'col', 'children')

    def __init__(self, type, value=None, line=None, col=None):
        self.type = type
        self.value = value
        self.line = line
        self.col = col
        self.children = []

    def add(self, child):
        if child is not None:
            self.children.append(child)
        return child

    def label(self):
        if self.value is not None:
            return f"{self.type}  «{self.value}»"
        return self.type


class Parser:
    def __init__(self, tokens):
        # tokens: [(tipo, valor, linea, columna)] — sin COMMENT ni ERROR.
        if tokens:
            last = tokens[-1]
            eof_line, eof_col = last[2], last[3]
        else:
            eof_line, eof_col = 1, 1
        self.tokens = list(tokens) + [('EOF', 'EOF', eof_line, eof_col)]
        self.pos = 0
        self.errors = []   # [(mensaje, linea, columna)]

    # ── Acceso a tokens ────────────────────────────────────────────────────
    def peek(self):
        return self.tokens[self.pos]

    def advance(self):
        tok = self.tokens[self.pos]
        if self.peek()[0] != 'EOF':
            self.pos += 1
        return tok

    def _is_eof(self, tok=None):
        return (tok or self.peek())[0] == 'EOF'

    def _val(self):
        return self.peek()[1]

    def _type(self):
        return self.peek()[0]

    # ── Errores ─────────────────────────────────────────────────────────────
    def error(self, msg, tok=None):
        t = tok or self.peek()
        self.errors.append((msg, t[2], t[3]))

    def expect(self, value, context=''):
        """Consume el token si su lexema coincide; si no, registra error
        (recuperación modo pánico: NO consume) y devuelve None."""
        t = self.peek()
        if not self._is_eof(t) and t[1] == value:
            self.advance()
            return Node('token', value, t[2], t[3])
        where = f" en {context}" if context else ''
        self.error(f"se esperaba «{value}»{where}, se encontró «{t[1]}»", t)
        return None

    def expect_type(self, ttype, descr, context=''):
        t = self.peek()
        if not self._is_eof(t) and t[0] == ttype:
            self.advance()
            return Node(descr, t[1], t[2], t[3])
        where = f" en {context}" if context else ''
        self.error(f"se esperaba {descr}{where}, se encontró «{t[1]}»", t)
        return None

    # ── Predicados ────────────────────────────────────────────────────────
    def _starts_sentencia(self, tok):
        typ, val = tok[0], tok[1]
        if typ == 'IDENTIFIER':
            return True
        return typ == 'KEYWORD' and val in SENT_START_KW

    # ════════════════════════════════════════════════════════════════════════
    # Reglas de la gramática
    # ════════════════════════════════════════════════════════════════════════
    def parse(self):
        return self.parse_programa()

    def parse_programa(self):
        node = Node('programa')
        node.add(self.expect('main', 'programa'))
        node.add(self.expect('{', 'programa'))
        node.add(self.parse_lista_declaracion())
        node.add(self.expect('}', 'programa'))
        if not self._is_eof():
            self.error(f"tokens sobrantes tras «}}»: «{self._val()}»")
        return node

    def parse_lista_declaracion(self):
        node = Node('lista_declaracion')
        while True:
            t = self.peek()
            if self._is_eof(t) or t[1] == '}':
                break
            before = self.pos
            if t[0] == 'KEYWORD' and t[1] in TIPOS:
                node.add(self.parse_declaracion_variable())
            elif self._starts_sentencia(t):
                node.add(self.parse_sentencia())
            else:
                self.error(f"declaración o sentencia inesperada: «{t[1]}»", t)
                self.advance()  # recuperación: descartar token
            if self.pos == before:        # guardia anti-bucle
                self.advance()
        return node

    def parse_declaracion_variable(self):
        node = Node('declaracion_variable')
        tipo = self.peek()
        node.add(Node('tipo', tipo[1], tipo[2], tipo[3]))
        self.advance()
        node.add(self.parse_identificador())
        node.add(self.expect(';', 'declaracion_variable'))
        return node

    def parse_identificador(self):
        node = Node('identificador')
        node.add(self.expect_type('IDENTIFIER', 'id', 'identificador'))
        while self._val() == ',':
            self.advance()
            node.add(self.expect_type('IDENTIFIER', 'id', 'identificador'))
        return node

    def parse_lista_sentencias(self, stop=()):
        node = Node('lista_sentencias')
        while True:
            t = self.peek()
            if self._is_eof(t) or t[1] in stop:
                break
            if not self._starts_sentencia(t):
                break
            before = self.pos
            node.add(self.parse_sentencia(stop))
            if self.pos == before:
                self.advance()
        return node

    def parse_sentencia(self, stop=()):
        t = self.peek()
        val = t[1]
        if val == 'if':
            return self.parse_seleccion()
        if val == 'while':
            return self.parse_iteracion()
        if val == 'do':
            return self.parse_repeticion()
        if val == 'cin':
            return self.parse_sent_in()
        if val == 'cout':
            return self.parse_sent_out()
        if t[0] == 'IDENTIFIER':
            return self.parse_asignacion()
        self.error(f"sentencia inesperada: «{val}»", t)
        self.advance()
        return None

    def parse_asignacion(self):
        node = Node('asignacion')
        node.add(self.expect_type('IDENTIFIER', 'id', 'asignacion'))
        node.add(self.expect('=', 'asignacion'))
        node.add(self.parse_sent_expresion())
        return node

    def parse_sent_expresion(self):
        node = Node('sent_expresion')
        if self._val() == ';':
            self.advance()
            return node
        node.add(self.parse_expresion())
        node.add(self.expect(';', 'sent_expresion'))
        return node

    def parse_seleccion(self):
        node = Node('seleccion')
        node.add(self.expect('if', 'seleccion'))
        node.add(self.parse_expresion())
        node.add(self.expect('then', 'seleccion'))
        node.add(self.parse_lista_sentencias(stop=('else', 'end')))
        if self._val() == 'else':
            self.advance()
            rama = Node('else')
            rama.add(self.parse_lista_sentencias(stop=('end',)))
            node.add(rama)
        node.add(self.expect('end', 'seleccion'))
        return node

    def parse_iteracion(self):
        node = Node('iteracion')
        node.add(self.expect('while', 'iteracion'))
        node.add(self.parse_expresion())
        node.add(self.parse_lista_sentencias(stop=('end',)))
        node.add(self.expect('end', 'iteracion'))
        return node

    def parse_repeticion(self):
        node = Node('repeticion')
        node.add(self.expect('do', 'repeticion'))
        node.add(self.parse_lista_sentencias(stop=('while',)))
        node.add(self.expect('while', 'repeticion'))
        node.add(self.parse_expresion())
        return node

    def parse_sent_in(self):
        node = Node('sent_in')
        node.add(self.expect('cin', 'sent_in'))
        node.add(self.expect('>>', 'sent_in'))
        node.add(self.expect_type('IDENTIFIER', 'id', 'sent_in'))
        node.add(self.expect(';', 'sent_in'))
        return node

    def parse_sent_out(self):
        node = Node('sent_out')
        node.add(self.expect('cout', 'sent_out'))
        node.add(self.expect('<<', 'sent_out'))
        node.add(self.parse_salida())
        if self._val() == ';':          # ';' final opcional (tolerancia)
            self.advance()
        return node

    def parse_salida(self):
        node = Node('salida')
        if self._type() == 'STRING_LITERAL':
            t = self.advance()
            node.add(Node('cadena', t[1], t[2], t[3]))
            if self._val() == '<<':
                self.advance()
                node.add(self.parse_expresion())
        else:
            node.add(self.parse_expresion())
            if self._val() == '<<':
                self.advance()
                t = self.peek()
                if self._type() == 'STRING_LITERAL':
                    self.advance()
                    node.add(Node('cadena', t[1], t[2], t[3]))
                else:
                    self.error(f"se esperaba cadena tras «<<», se encontró «{t[1]}»", t)
        return node

    # ── Expresiones ─────────────────────────────────────────────────────────
    def parse_expresion(self):
        node = Node('expresion')
        node.add(self.parse_expresion_simple())
        if self._val() in REL_OP:
            op = self.advance()
            node.add(Node('rel_op', op[1], op[2], op[3]))
            node.add(self.parse_expresion_simple())
        return node

    def parse_expresion_simple(self):
        node = Node('expresion_simple')
        node.add(self.parse_termino())
        while self._val() in SUMA_OP:
            op = self.advance()
            node.add(Node('suma_op', op[1], op[2], op[3]))
            node.add(self.parse_termino())
        return node

    def parse_termino(self):
        node = Node('termino')
        node.add(self.parse_factor())
        while self._val() in MULT_OP:
            op = self.advance()
            node.add(Node('mult_op', op[1], op[2], op[3]))
            node.add(self.parse_factor())
        return node

    def parse_factor(self):
        node = Node('factor')
        node.add(self.parse_componente())
        while self._val() in POT_OP:
            op = self.advance()
            node.add(Node('pot_op', op[1], op[2], op[3]))
            node.add(self.parse_componente())
        return node

    def parse_componente(self):
        t = self.peek()
        node = Node('componente')
        if t[1] == '(':
            self.advance()
            node.add(self.parse_expresion())
            node.add(self.expect(')', 'componente'))
            return node
        if t[0] in ('INTEGER', 'FLOAT'):
            self.advance()
            node.add(Node('numero', t[1], t[2], t[3]))
            return node
        if t[0] == 'IDENTIFIER':
            self.advance()
            node.add(Node('id', t[1], t[2], t[3]))
            return node
        if t[0] == 'KEYWORD' and t[1] in ('bool', 'true', 'false'):
            self.advance()
            node.add(Node('bool', t[1], t[2], t[3]))
            return node
        if t[1] in LOG_OP:
            self.advance()
            node.add(Node('op_logico', t[1], t[2], t[3]))
            node.add(self.parse_componente())
            return node
        self.error(f"se esperaba expresión, se encontró «{t[1]}»", t)
        return node


def parse_tokens(tokens):
    """Conveniencia: devuelve (ast, errores)."""
    p = Parser(tokens)
    ast = p.parse()
    return ast, p.errors
