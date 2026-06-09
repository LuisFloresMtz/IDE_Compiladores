"""Analizador sintáctico descendente recursivo.

Lee la lista de tokens producida por el analizador léxico
(lexical_analyzer.tokenize_with_lines → [(tipo, valor, linea, columna)]),
valida la estructura contra la gramática de la Fase 2 y construye un
Árbol Sintáctico Abstracto (AST).

A diferencia de un árbol de derivación concreto, el AST:
  * omite los terminales sin contenido semántico (main, {, }, ;, then, …);
  * no encadena nodos de un solo hijo (expresion→…→componente);
  * codifica precedencia y asociatividad en la FORMA del árbol:
    cada operador binario es un nodo «operador» con exactamente
    dos hijos (izquierdo, derecho).

Gramática (forma iterativa, recursión izquierda eliminada):

    programa            → main { lista_declaracion }
    lista_declaracion   → (declaracion_variable | sentencia)*
    declaracion_variable→ tipo identificador ;
    identificador       → id (, id)*
    tipo                → int | float | bool
    lista_sentencias    → sentencia*
    sentencia           → seleccion | iteracion | repeticion
                        | sent_in | sent_out | asignacion | incremento
    asignacion          → id = sent_expresion
    incremento          → id (++ | --) ;
    sent_expresion      → expresion ; | ;
    seleccion           → if expresion then lista_sentencias
                          [ else lista_sentencias ] end ;
    iteracion           → while expresion { lista_sentencias } ; | while expresion ;
    repeticion          → do lista_sentencias while expresion ;
    sent_in             → cin >> id ;
    sent_out            → cout << salida
    salida              → cadena [ << expresion ] | expresion [ << cadena ]

Sub-gramática de expresiones (idéntica al PDF Fase 2). La asociatividad
la fija la recursión por la izquierda de cada producción → TODOS los
operadores binarios son asociativos por la IZQUIERDA. Se implementa de
forma iterativa (bucle = plegado a la izquierda):

    expresion           → expresion logic_op relacional | relacional     (izquierda)
    logic_op            → && | ||                                        (binario)
    relacional          → expresion_simple [ rel_op expresion_simple ]   (no asociativo)
    rel_op              → < | <= | > | >= | == | !=
    expresion_simple    → expresion_simple suma_op termino | termino     (izquierda)
    suma_op             → + | -
    termino             → termino mult_op factor | factor                (izquierda)
    mult_op             → * | / | %
    factor              → factor pot_op componente | componente          (izquierda)
    pot_op              → ^
    componente          → ( expresion ) | numero | id | bool | ! componente

Precedencia (de MENOR a MAYOR): logic_op < rel_op < suma_op < mult_op < pot_op.
&& y || son BINARIOS (precedencia más baja); ! es PREFIJO sobre componente.
"""

# Conjuntos de operadores por categoría gramatical (se distinguen por valor).
REL_OP   = {'<', '<=', '>', '>=', '==', '!='}
SUMA_OP  = {'+', '-'}
MULT_OP  = {'*', '/', '%'}
POT_OP   = {'^'}
LOGIC_OP = {'&&', '||'}   # binarios, precedencia MÁS BAJA (a && b)
NOT_OP   = {'!'}          # op_logico unario PREFIJO sobre componente
INCR_OP  = {'++', '--'}   # postfijo: sentencia  (a++ ;  c-- ;)
TIPOS    = {'int', 'float', 'bool'}
# Palabras con las que puede comenzar una sentencia.
SENT_START_KW = {'if', 'while', 'do', 'cin', 'cout'}


class Node:
    """Nodo del AST. `type` es la categoría semántica; `value` el lexema
    cuando el nodo lleva contenido (operador, literal, identificador)."""

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
        self._stack = []   # nodos en construcción: el error se cuelga del actual

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

    # ── Pila de construcción (para colgar errores en su sitio del AST) ──────
    def _enter(self, node):
        """Marca `node` como construcción actual; los errores se cuelgan de él."""
        self._stack.append(node)
        return node

    def _leave(self, node):
        self._stack.pop()
        return node

    # ── Errores ─────────────────────────────────────────────────────────────
    def error(self, msg, tok=None):
        t = tok or self.peek()
        self.errors.append((msg, t[2], t[3]))
        # Cuelga un nodo «error» del nodo que se está parseando ahora mismo,
        # de modo que aparezca inline en el árbol, no agrupado al inicio.
        if self._stack:
            self._stack[-1].add(Node('error', msg, t[2], t[3]))

    def expect(self, value, context=''):
        """Consume el token si su lexema coincide; si no, registra error
        (recuperación modo pánico: NO consume). Usado solo para validar
        terminales sin valor semántico — su nodo NO entra en el AST."""
        t = self.peek()
        if not self._is_eof(t) and t[1] == value:
            self.advance()
            return True
        where = f" en {context}" if context else ''
        self.error(f"se esperaba «{value}»{where}, se encontró «{t[1]}»", t)
        return False

    def expect_type(self, ttype, descr, context=''):
        """Consume un token de cierto tipo y devuelve su nodo AST (o None)."""
        t = self.peek()
        if not self._is_eof(t) and t[0] == ttype:
            self.advance()
            return Node(descr, t[1], t[2], t[3])
        where = f" en {context}" if context else ''
        self.error(f"se esperaba {descr}{where}, se encontró «{t[1]}»", t)
        return None

    # ── Constructores AST ────────────────────────────────────────────────────
    @staticmethod
    def _binop(op_tok, left, right):
        """Nodo de operador binario: dos hijos (izquierdo, derecho).
        La forma del árbol codifica precedencia y asociatividad."""
        n = Node('operador', op_tok[1], op_tok[2], op_tok[3])
        n.add(left)    # add() ignora None (operando ausente por error sintáctico)
        n.add(right)
        return n

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
        node = self._enter(Node('programa'))
        self.expect('main', 'programa')
        self.expect('{', 'programa')
        for hijo in self.parse_lista_declaracion():
            node.add(hijo)
        self.expect('}', 'programa')
        if not self._is_eof():
            self.error(f"tokens sobrantes tras «}}»: «{self._val()}»")
        return self._leave(node)

    def parse_lista_declaracion(self):
        """Devuelve una lista de nodos (declaraciones y sentencias)."""
        hijos = []
        while True:
            t = self.peek()
            if self._is_eof(t) or t[1] == '}':
                break
            before = self.pos
            if t[0] == 'KEYWORD' and t[1] in TIPOS:
                n = self.parse_declaracion_variable()
            elif self._starts_sentencia(t):
                n = self.parse_sentencia()
            else:
                self.error(f"declaración o sentencia inesperada: «{t[1]}»", t)
                self.advance()  # recuperación: descartar token
                n = None
            if n is not None:
                hijos.append(n)
            if self.pos == before:        # guardia anti-bucle
                self.advance()
        return hijos

    def parse_declaracion_variable(self):
        tipo = self.peek()
        node = self._enter(Node('declaracion_variable', tipo[1], tipo[2], tipo[3]))
        self.advance()
        for ident in self.parse_identificador():
            node.add(ident)
        self.expect(';', 'declaracion_variable')
        return self._leave(node)

    def parse_identificador(self):
        """Devuelve la lista de nodos id declarados."""
        ids = []
        ids.append(self.expect_type('IDENTIFIER', 'id', 'identificador'))
        while self._val() == ',':
            self.advance()
            ids.append(self.expect_type('IDENTIFIER', 'id', 'identificador'))
        return [i for i in ids if i is not None]

    def parse_lista_sentencias(self, stop=()):
        """Devuelve una lista de nodos sentencia."""
        hijos = []
        while True:
            t = self.peek()
            if self._is_eof(t) or t[1] in stop:
                break
            if not self._starts_sentencia(t):
                break
            before = self.pos
            n = self.parse_sentencia(stop)
            if n is not None:
                hijos.append(n)
            if self.pos == before:
                self.advance()
        return hijos

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
            if self.tokens[self.pos + 1][1] in INCR_OP:
                return self.parse_incremento()
            return self.parse_asignacion()
        self.error(f"sentencia inesperada: «{val}»", t)
        self.advance()
        return None

    def parse_incremento(self):
        """id (++ | --) ;   → sentencia de incremento/decremento postfijo."""
        t = self.peek()
        op = self.tokens[self.pos + 1]
        node = self._enter(Node('incremento', op[1], t[2], t[3]))
        node.add(self.expect_type('IDENTIFIER', 'id', 'incremento'))
        self.advance()                      # consume ++ / --
        self.expect(';', 'incremento')
        return self._leave(node)

    def parse_asignacion(self):
        t = self.peek()
        node = self._enter(Node('asignacion', '=', t[2], t[3]))
        node.add(self.expect_type('IDENTIFIER', 'id', 'asignacion'))
        self.expect('=', 'asignacion')
        node.add(self.parse_sent_expresion())
        return self._leave(node)

    def parse_sent_expresion(self):
        """expresion ; | ;  → devuelve el nodo expresión, o None si vacía."""
        if self._val() == ';':
            self.advance()
            return None
        expr = self.parse_expresion()
        self.expect(';', 'sent_expresion')
        return expr

    def parse_seleccion(self):
        t = self.peek()
        node = self._enter(Node('if', None, t[2], t[3]))
        self.expect('if', 'seleccion')
        node.add(self.parse_expresion())
        self.expect('then', 'seleccion')
        entonces = Node('entonces')
        for s in self.parse_lista_sentencias(stop=('else', 'end')):
            entonces.add(s)
        node.add(entonces)
        if self._val() == 'else':
            self.advance()
            rama = Node('else')
            for s in self.parse_lista_sentencias(stop=('end',)):
                rama.add(s)
            node.add(rama)
        self.expect('end', 'seleccion')
        self.expect(';', 'seleccion')      # end ;
        return self._leave(node)

    def parse_iteracion(self):
        t = self.peek()
        node = self._enter(Node('while', None, t[2], t[3]))
        self.expect('while', 'iteracion')
        node.add(self.parse_expresion())        # while ( cond )
        if self._val() == ';':                  # cuerpo vacío: while(cond) ;
            self.advance()
            return self._leave(node)
        self.expect('{', 'iteracion')           # cuerpo entre llaves
        cuerpo = Node('cuerpo')
        for s in self.parse_lista_sentencias(stop=('}',)):
            cuerpo.add(s)
        node.add(cuerpo)
        self.expect('}', 'iteracion')
        if self._val() == ';':                  # ';' final opcional tras '}'
            self.advance()
        return self._leave(node)

    def parse_repeticion(self):
        t = self.peek()
        node = self._enter(Node('do_while', None, t[2], t[3]))
        self.expect('do', 'repeticion')
        cuerpo = Node('cuerpo')
        for s in self.parse_lista_sentencias(stop=('while',)):
            cuerpo.add(s)
        node.add(cuerpo)
        self.expect('while', 'repeticion')
        node.add(self.parse_expresion())
        if self._val() == ';':              # do … while ( cond ) ;
            self.advance()
        return self._leave(node)

    def parse_sent_in(self):
        t = self.peek()
        node = self._enter(Node('cin', None, t[2], t[3]))
        self.expect('cin', 'sent_in')
        self.expect('>>', 'sent_in')
        node.add(self.expect_type('IDENTIFIER', 'id', 'sent_in'))
        self.expect(';', 'sent_in')
        return self._leave(node)

    def parse_sent_out(self):
        t = self.peek()
        node = self._enter(Node('cout', None, t[2], t[3]))
        self.expect('cout', 'sent_out')
        self.expect('<<', 'sent_out')
        for parte in self.parse_salida():
            node.add(parte)
        if self._val() == ';':          # ';' final opcional (tolerancia)
            self.advance()
        return self._leave(node)

    def parse_salida(self):
        """Devuelve la lista de partes (cadena y/o expresión)."""
        partes = []
        if self._type() == 'STRING_LITERAL':
            t = self.advance()
            partes.append(Node('cadena', t[1], t[2], t[3]))
            if self._val() == '<<':
                self.advance()
                partes.append(self.parse_expresion())
        else:
            partes.append(self.parse_expresion())
            if self._val() == '<<':
                self.advance()
                t = self.peek()
                if self._type() == 'STRING_LITERAL':
                    self.advance()
                    partes.append(Node('cadena', t[1], t[2], t[3]))
                else:
                    self.error(f"se esperaba cadena tras «<<», se encontró «{t[1]}»", t)
        return [p for p in partes if p is not None]

    # ── Expresiones ─────────────────────────────────────────────────────────
    # Un nivel por escalón de precedencia (rel < suma < mult < pot < op_logico).
    # Cada producción del PDF es recursiva por la IZQUIERDA, por lo que todos
    # los operadores binarios pliegan a la izquierda (bucle while). Cada
    # operador produce un nodo binario «operador» con dos hijos → árbol no
    # ambiguo que codifica precedencia y asociatividad en su forma.

    def parse_expresion(self):
        # op_logico binario && || : precedencia más baja, asociativo izquierda.
        node = self.parse_relacional()
        while self._val() in LOGIC_OP:
            op = self.advance()
            right = self.parse_relacional()
            node = self._binop(op, node, right)
        return node

    def parse_relacional(self):
        # rel_op: no asociativo → a lo sumo una comparación.
        left = self.parse_expresion_simple()
        if self._val() in REL_OP:
            op = self.advance()
            right = self.parse_expresion_simple()
            return self._binop(op, left, right)
        return left

    def parse_expresion_simple(self):
        # suma_op: asociatividad izquierda  → ((a+b)+c)
        node = self.parse_termino()
        while self._val() in SUMA_OP:
            op = self.advance()
            right = self.parse_termino()
            node = self._binop(op, node, right)
        return node

    def parse_termino(self):
        # mult_op: asociatividad izquierda  → ((a*b)*c)
        node = self.parse_factor()
        while self._val() in MULT_OP:
            op = self.advance()
            right = self.parse_factor()
            node = self._binop(op, node, right)
        return node

    def parse_factor(self):
        # pot_op: asociatividad izquierda  → ((a^b)^c)
        # (gramática: factor → factor pot_op componente, recursión izquierda)
        node = self.parse_componente()
        while self._val() in POT_OP:
            op = self.advance()
            right = self.parse_componente()
            node = self._binop(op, node, right)
        return node

    def parse_componente(self):
        t = self.peek()
        if t[1] == '(':
            self.advance()
            expr = self.parse_expresion()
            self.expect(')', 'componente')
            return expr                    # AST: sin nodo paréntesis
        if t[0] in ('INTEGER', 'FLOAT'):
            self.advance()
            return Node('numero', t[1], t[2], t[3])
        if t[0] == 'IDENTIFIER':
            self.advance()
            return Node('id', t[1], t[2], t[3])
        if t[0] == 'KEYWORD' and t[1] in ('bool', 'true', 'false'):
            self.advance()
            return Node('bool', t[1], t[2], t[3])
        if t[1] in NOT_OP:                 # op_logico unario ! : prefijo
            self.advance()
            n = Node('operador_unario', t[1], t[2], t[3])
            n.add(self.parse_componente())
            return n
        self.error(f"se esperaba expresión, se encontró «{t[1]}»", t)
        return None


def parse_tokens(tokens):
    """Conveniencia: devuelve (ast, errores)."""
    p = Parser(tokens)
    ast = p.parse()
    return ast, p.errors
