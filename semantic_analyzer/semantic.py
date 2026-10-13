"""Analizador semántico.

Recibe el AST del analizador sintáctico (syntactic_analyzer.parser.Node),
construye una COPIA anotada (NodoSem) y la recorre aplicando las reglas
semánticas del lenguaje:

  · Declaración  → el tipo se HEREDA hacia cada identificador (dtype) y se
                   inserta en la tabla de símbolos.
  · Uso de id    → búsqueda en la tabla; el tipo se obtiene de ella.
  · Expresión    → el tipo (y el valor, si es constante) se SINTETIZA de los
                   hijos hacia el padre.
  · Asignación   → se compara el tipo de la variable con el de la expresión.
  · Condiciones  → if / while / do-while exigen una expresión bool.

Reglas de tipos
  + - * / ^      numérico × numérico → int si ambos son int, float en otro caso
  %              int × int → int
  < <= > >=      numérico × numérico → bool
  == !=          numérico × numérico → bool,  bool × bool → bool
  && ||          bool × bool → bool
  !              bool → bool
Conversiones
  int → float    permitida (implícita) en operaciones mixtas y al asignar a float
  float → int    NO permitida (pérdida de información)
  bool ↔ número  NO permitida

El AST original no se modifica.
"""

from symbol_table.symbol_table import TablaSimbolos, formatear_valor

NUMERICOS = ('int', 'float')
ARIT_OP = {'+', '-', '*', '/', '^'}
MOD_OP = {'%'}
ORDEN_OP = {'<', '<=', '>', '>='}
IGUAL_OP = {'==', '!='}
LOGIC_OP = {'&&', '||'}

T_ERROR = 'error'      # tipo de una expresión inválida (evita errores en cascada)
T_CADENA = 'cadena'

SINTETIZADO = 'sintetizado'
HEREDADO = 'heredado'


class NodoSem:
    """Nodo del árbol anotado: copia de un nodo del AST más sus atributos."""

    __slots__ = ('type', 'value', 'line', 'col', 'children',
                 'dtype', 'val', 'origen', 'conv', 'errores')

    def __init__(self, type, value=None, line=None, col=None):
        self.type = type
        self.value = value
        self.line = line
        self.col = col
        self.children = []
        self.dtype = None      # atributo de tipo
        self.val = None        # atributo de valor (None = no se conoce en compilación)
        self.origen = None     # SINTETIZADO | HEREDADO
        self.conv = None       # conversión aplicada, p. ej. 'int→float'
        self.errores = []      # errores semánticos detectados en este nodo

    def label(self):
        if self.value is not None:
            return f"{self.type}  «{self.value}»"
        return self.type

    def anotacion(self):
        """Texto con los atributos semánticos del nodo ('' si no tiene)."""
        partes = []
        if self.dtype is not None:
            flecha = {SINTETIZADO: ' ↑', HEREDADO: ' ↓'}.get(self.origen, '')
            partes.append(f"tipo: {self.dtype}{flecha}")
        if self.val is not None:
            partes.append(f"valor: {formatear_valor(self.val)}")
        if self.conv:
            partes.append(f"conv: {self.conv}")
        return ' | '.join(partes)


class ResultadoSemantico:
    def __init__(self, arbol, tabla, errores, bitacora):
        self.arbol = arbol          # NodoSem raíz (AST anotado)
        self.tabla = tabla          # TablaSimbolos
        self.errores = errores      # [(mensaje, linea, columna)]
        self.bitacora = bitacora    # [(linea, texto)] recorrido semántico


def copiar_ast(nodo):
    """Copia profunda del AST a nodos anotables."""
    if nodo is None:
        return None
    copia = NodoSem(nodo.type, nodo.value, nodo.line, nodo.col)
    for hijo in nodo.children:
        c = copiar_ast(hijo)
        if c is not None:
            copia.children.append(c)
    return copia


# ── Aritmética en compilación ───────────────────────────────────────────────
def _div_entera(a, b):
    """División entera truncada hacia cero (como en C)."""
    q = abs(a) // abs(b)
    return q if (a < 0) == (b < 0) else -q


def _potencia(a, b, tipo):
    try:
        if abs(b) > 4096:
            return None
        r = a ** b
        if isinstance(r, complex):
            return None
        if tipo == 'int':
            return r if isinstance(r, int) else None
        return float(r)
    except (OverflowError, ZeroDivisionError):
        return None


class AnalizadorSemantico:
    def __init__(self):
        self.tabla = TablaSimbolos()
        self.errores = []
        self.bitacora = []

    # ── Utilidades ──────────────────────────────────────────────────────────
    def _log(self, nodo, texto):
        self.bitacora.append((nodo.line if nodo is not None else None, texto))

    def _error(self, nodo, msg, pos=None):
        ref = pos if (pos is not None and pos.line is not None) else nodo
        self.errores.append((msg, ref.line or 0, ref.col or 0))
        nodo.errores.append(msg)
        self._log(ref, f"✗ ERROR: {msg}")

    @staticmethod
    def _hijos(nodo):
        """Hijos reales (se ignoran los nodos de error sintáctico)."""
        return [c for c in nodo.children if c.type != 'error']

    # ── Propagación de valores constantes ───────────────────────────────────
    def _modificadas(self, nodo, acc=None):
        """Nombres de las variables que cambian dentro de un subárbol."""
        if acc is None:
            acc = set()
        if nodo.type in ('asignacion', 'incremento', 'cin'):
            for h in nodo.children:
                if h.type == 'id':
                    acc.add(h.value)
                    break
        for h in nodo.children:
            self._modificadas(h, acc)
        return acc

    def _olvidar(self, nombres):
        """Tras un ciclo o una bifurcación el valor ya no se conoce en compilación."""
        for nombre in nombres:
            sim = self.tabla.buscar(nombre)
            if sim is not None:
                sim.valor = None

    # ── Entrada ─────────────────────────────────────────────────────────────
    def analizar(self, ast):
        arbol = copiar_ast(ast)
        if arbol is not None:
            self._bloque(arbol)
        return ResultadoSemantico(arbol, self.tabla, self.errores, self.bitacora)

    def _bloque(self, nodo):
        for hijo in self._hijos(nodo):
            self._sentencia(hijo)

    def _sentencia(self, n):
        metodo = {
            'declaracion_variable': self._declaracion,
            'asignacion': self._asignacion,
            'incremento': self._incremento,
            'if': self._seleccion,
            'while': self._iteracion,
            'do_while': self._repeticion,
            'cin': self._entrada,
            'cout': self._salida,
        }.get(n.type)
        if metodo is not None:
            metodo(n)
        else:
            self._expr(n)

    # ── Declaraciones ───────────────────────────────────────────────────────
    def _declaracion(self, n):
        tipo = n.value
        n.dtype = tipo
        n.origen = SINTETIZADO          # proviene del token de tipo
        for ident in self._hijos(n):
            if ident.type != 'id':
                continue
            ident.dtype = tipo
            ident.origen = HEREDADO     # dtype baja de la declaración al id
            previo = self.tabla.buscar(ident.value)
            if previo is not None:
                self._error(
                    ident,
                    f"declaración duplicada: «{ident.value}» ya fue declarado "
                    f"como {previo.tipo} en la línea {previo.linea_decl}")
                continue
            sim = self.tabla.insertar(ident.value, tipo, ident.line, ident.col)
            self._log(ident, f"inserta «{sim.nombre}» en la tabla: tipo {tipo} "
                             f"(heredado), dirección {sim.direccion}")

    # ── Identificadores ─────────────────────────────────────────────────────
    def _buscar_id(self, ident, contexto):
        """Busca un identificador usado; anota su tipo. Devuelve Simbolo o None."""
        sim = self.tabla.buscar(ident.value)
        if sim is None:
            ident.dtype = T_ERROR
            self._error(ident, f"identificador no declarado: «{ident.value}»")
            return None
        self.tabla.registrar_linea(ident.value, ident.line)
        ident.dtype = sim.tipo
        ident.origen = SINTETIZADO
        self._log(ident, f"busca «{sim.nombre}» ({contexto}) → tipo {sim.tipo}, "
                         f"dirección {sim.direccion}")
        return sim

    # ── Sentencias ──────────────────────────────────────────────────────────
    def _asignacion(self, n):
        hijos = self._hijos(n)
        if not hijos or hijos[0].type != 'id':
            for h in hijos:
                self._expr(h)
            return
        ident = hijos[0]
        sim = self._buscar_id(ident, 'asignación')
        expr = hijos[1] if len(hijos) > 1 else None
        t_expr = self._expr(expr) if expr is not None else None

        if sim is None:
            n.dtype = T_ERROR
            return
        n.dtype = sim.tipo
        n.origen = SINTETIZADO
        if expr is None or t_expr == T_ERROR:
            sim.valor = None
            return

        valor = expr.val
        if t_expr == sim.tipo:
            pass
        elif sim.tipo == 'float' and t_expr == 'int':
            expr.conv = 'int→float'
            if valor is not None:
                valor = float(valor)
            self._log(expr, f"conversión int→float al asignar a «{sim.nombre}»")
        elif sim.tipo == 'int' and t_expr == 'float':
            self._error(n, f"conversión de tipos no válida: no se puede asignar "
                           f"float a «{sim.nombre}» de tipo int", pos=expr)
            sim.valor = None
            return
        else:
            self._error(n, f"incompatibilidad de tipos en asignación: «{sim.nombre}» "
                           f"es {sim.tipo} y la expresión es {t_expr}", pos=expr)
            sim.valor = None
            return

        sim.valor = valor
        n.val = valor
        self._log(n, f"asignación válida: «{sim.nombre}» ({sim.tipo}) = expresión ({t_expr})"
                     + (f", valor {formatear_valor(valor)}" if valor is not None else ''))

    def _incremento(self, n):
        hijos = self._hijos(n)
        if not hijos or hijos[0].type != 'id':
            return
        ident = hijos[0]
        sim = self._buscar_id(ident, f"operador {n.value}")
        if sim is None:
            n.dtype = T_ERROR
            return
        if sim.tipo not in NUMERICOS:
            n.dtype = T_ERROR
            self._error(n, f"uso indebido del operador «{n.value}»: no se aplica a "
                           f"«{sim.nombre}» de tipo {sim.tipo}")
            return
        n.dtype = sim.tipo
        n.origen = SINTETIZADO
        ident.val = sim.valor
        if sim.valor is not None:
            sim.valor = sim.valor + (1 if n.value == '++' else -1)
            n.val = sim.valor

    def _condicion(self, n, cond, nombre):
        if cond is None:
            return
        tipo = self._expr(cond)
        ref = cond if cond.line is not None else n
        if tipo not in ('bool', T_ERROR):
            self._error(n, f"la condición de «{nombre}» debe ser bool y se obtuvo {tipo}",
                        pos=cond)
        else:
            self._log(ref, f"condición de «{nombre}»: tipo {tipo}")

    def _seleccion(self, n):
        hijos = self._hijos(n)
        cond = next((h for h in hijos if h.type not in ('entonces', 'else')), None)
        ramas = [h for h in hijos if h.type in ('entonces', 'else')]
        self._condicion(n, cond, 'if')
        # Cada rama parte del mismo estado; al salir, lo modificado es desconocido.
        estado = {s: s.valor for s in self.tabla.simbolos()}
        modificadas = set()
        for rama in ramas:
            for sim, valor in estado.items():
                sim.valor = valor
            self._bloque(rama)
            self._modificadas(rama, modificadas)
        self._olvidar(modificadas)

    def _iteracion(self, n):
        hijos = self._hijos(n)
        cond = next((h for h in hijos if h.type != 'cuerpo'), None)
        cuerpo = next((h for h in hijos if h.type == 'cuerpo'), None)
        modificadas = self._modificadas(cuerpo) if cuerpo is not None else set()
        self._olvidar(modificadas)       # el cuerpo puede repetirse
        self._condicion(n, cond, 'while')
        if cuerpo is not None:
            self._bloque(cuerpo)
        self._olvidar(modificadas)

    def _repeticion(self, n):
        hijos = self._hijos(n)
        cuerpo = next((h for h in hijos if h.type == 'cuerpo'), None)
        cond = next((h for h in hijos if h.type != 'cuerpo'), None)
        modificadas = self._modificadas(cuerpo) if cuerpo is not None else set()
        self._olvidar(modificadas)
        if cuerpo is not None:
            self._bloque(cuerpo)
        self._olvidar(modificadas)
        self._condicion(n, cond, 'do-while')

    def _entrada(self, n):
        for h in self._hijos(n):
            if h.type == 'id':
                sim = self._buscar_id(h, 'cin')
                if sim is not None:
                    sim.valor = None      # se conoce hasta la ejecución
                    n.dtype = sim.tipo
                    n.origen = SINTETIZADO

    def _salida(self, n):
        for h in self._hijos(n):
            self._expr(h)

    # ── Expresiones (atributos sintetizados) ────────────────────────────────
    def _expr(self, n):
        """Calcula y anota el tipo (y el valor, si es constante). Devuelve el tipo."""
        if n is None:
            return T_ERROR
        n.origen = SINTETIZADO
        if n.type == 'numero':
            if '.' in n.value:
                n.dtype, n.val = 'float', float(n.value)
            else:
                n.dtype, n.val = 'int', int(n.value)
        elif n.type == 'bool':
            n.dtype = 'bool'
            if n.value in ('true', 'false'):
                n.val = (n.value == 'true')
        elif n.type == 'cadena':
            n.dtype = T_CADENA
        elif n.type == 'id':
            sim = self._buscar_id(n, 'expresión')
            if sim is not None:
                n.val = sim.valor
        elif n.type == 'operador':
            self._binario(n)
        elif n.type == 'operador_unario':
            self._unario(n)
        else:
            n.dtype = T_ERROR
            n.origen = None
        return n.dtype

    def _unario(self, n):
        hijos = self._hijos(n)
        if not hijos:
            n.dtype = T_ERROR
            return
        t = self._expr(hijos[0])
        n.dtype = 'bool'
        if t == T_ERROR:
            return
        if t != 'bool':
            self._error(n, f"uso indebido del operador «{n.value}»: requiere un "
                           f"operando bool y se obtuvo {t}")
            return
        if hijos[0].val is not None:
            n.val = not hijos[0].val

    def _binario(self, n):
        op = n.value
        hijos = self._hijos(n)
        if len(hijos) < 2:               # operando perdido por un error sintáctico
            for h in hijos:
                self._expr(h)
            n.dtype = 'bool' if op in ORDEN_OP | IGUAL_OP | LOGIC_OP else T_ERROR
            return
        izq, der = hijos[0], hijos[1]
        ti, td = self._expr(izq), self._expr(der)
        hay_error = T_ERROR in (ti, td)
        ambos_num = ti in NUMERICOS and td in NUMERICOS

        if op in LOGIC_OP:
            n.dtype = 'bool'
            if hay_error:
                return
            if ti != 'bool' or td != 'bool':
                self._error(n, f"uso indebido del operador «{op}»: requiere operandos "
                               f"bool y se obtuvo {ti} y {td}")
                return
            if izq.val is not None and der.val is not None:
                n.val = (izq.val and der.val) if op == '&&' else (izq.val or der.val)

        elif op in ORDEN_OP or op in IGUAL_OP:
            n.dtype = 'bool'
            if hay_error:
                return
            if ambos_num:
                self._promover(n, izq, der)
            elif not (op in IGUAL_OP and ti == td == 'bool'):
                self._error(n, f"incompatibilidad de tipos: el operador «{op}» no "
                               f"puede comparar {ti} con {td}")
                return
            if izq.val is not None and der.val is not None:
                a, b = izq.val, der.val
                n.val = {'<': a < b, '<=': a <= b, '>': a > b, '>=': a >= b,
                         '==': a == b, '!=': a != b}[op]

        else:                            # aritméticos: + - * / ^ %
            if hay_error:
                n.dtype = T_ERROR
                return
            if not ambos_num:
                n.dtype = T_ERROR
                self._error(n, f"uso indebido del operador «{op}»: requiere operandos "
                               f"numéricos y se obtuvo {ti} y {td}")
                return
            if op in MOD_OP and (ti != 'int' or td != 'int'):
                n.dtype = T_ERROR
                self._error(n, f"uso indebido del operador «%»: requiere operandos "
                               f"int y se obtuvo {ti} y {td}")
                return
            n.dtype = self._promover(n, izq, der)
            if izq.val is not None and der.val is not None:
                n.val = self._calcular(n, op, izq.val, der.val, n.dtype)

        self._log(n, f"«{op}»: {ti} {op} {td} → {n.dtype}"
                     + (f" = {formatear_valor(n.val)}" if n.val is not None else ''))

    def _promover(self, n, izq, der):
        """Regla de conversión: int se convierte a float si el otro operando es float."""
        if izq.dtype == der.dtype:
            return izq.dtype
        for nodo in (izq, der):
            if nodo.dtype == 'int':
                nodo.conv = 'int→float'
                self._log(nodo if nodo.line is not None else n,
                          f"conversión int→float de un operando de «{n.value}»")
        return 'float'

    def _calcular(self, n, op, a, b, tipo):
        if tipo == 'float':
            a, b = float(a), float(b)
        if op == '+':
            return a + b
        if op == '-':
            return a - b
        if op == '*':
            return a * b
        if op == '^':
            return _potencia(a, b, tipo)
        if b == 0:
            self._error(n, f"división entre cero en el operador «{op}»")
            return None
        if op == '/':
            return _div_entera(a, b) if tipo == 'int' else a / b
        return a - b * _div_entera(a, b)      # %


def analizar(ast):
    """Conveniencia: analiza un AST y devuelve un ResultadoSemantico."""
    return AnalizadorSemantico().analizar(ast)


def volcar_arbol(nodo, depth=0, salida=None):
    """Árbol anotado como lista de (texto, tiene_error) con sangría."""
    if salida is None:
        salida = []
    if nodo is None:
        return salida
    texto = "  " * depth + nodo.label()
    anot = nodo.anotacion()
    if anot:
        texto += f"   [{anot}]"
    for e in nodo.errores:
        texto += f"   ✗ {e}"
    salida.append((texto, bool(nodo.errores) or nodo.type == 'error'))
    for hijo in nodo.children:
        volcar_arbol(hijo, depth + 1, salida)
    return salida


if __name__ == '__main__':
    # Uso: python -m semantic_analyzer.semantic archivo.txt
    import sys
    from lexical_analyzer.lexical_analyzer import tokenize_with_lines
    from syntactic_analyzer.parser import parse_tokens

    sys.stdout.reconfigure(encoding='utf-8')
    with open(sys.argv[1], encoding='utf-8') as f:
        fuente = f.read()
    tokens = [t for t in tokenize_with_lines(fuente) if t[0] not in ('COMMENT', 'ERROR')]
    ast, sintacticos = parse_tokens(tokens)
    res = analizar(ast)
    print("── Árbol anotado ──")
    for texto, _ in volcar_arbol(res.arbol):
        print(texto)
    print("\n── Recorrido semántico ──")
    for linea, texto in res.bitacora:
        print(f"L{linea}: {texto}")
    print("\n── Tabla de símbolos ──")
    print(res.tabla.formatear())
    print("\n── Errores ──")
    for msg, ln, col in sintacticos:
        print(f"Sintáctico — Línea {ln}, columna {col}: {msg}")
    for msg, ln, col in res.errores:
        print(f"Semántico — Línea {ln}, columna {col}: {msg}")
    if not res.errores:
        print("Sin errores semánticos.")
