"""Tabla de símbolos del compilador.

Implementada como una tabla hash con encadenamiento separado (misma idea que
la tabla de TINY de Louden): cada cubeta guarda la lista de símbolos cuyo
nombre produce el mismo valor hash.

Por cada identificador se registra:
  · nombre (lexema)
  · tipo de dato (int, float, bool)
  · dirección de memoria (localidad consecutiva: 0, 1, 2, …)
  · números de línea donde aparece (declaración y usos)
  · valor conocido en compilación (None si sólo se sabe en ejecución)
  · si ya recibió un valor (para detectar variables sin valor asignado)

El analizador semántico la usa de verdad durante el recorrido del AST:
`insertar` al procesar declaraciones y `buscar` en cada uso de identificador.
"""

SIZE = 211    # número de cubetas (primo)
SHIFT = 4     # potencia de dos usada como multiplicador en la función hash


class Simbolo:
    """Registro de un identificador dentro de la tabla."""

    __slots__ = ('nombre', 'tipo', 'direccion', 'lineas',
                 'linea_decl', 'col_decl', 'valor', 'inicializada')

    def __init__(self, nombre, tipo, direccion, linea=None, col=None):
        self.nombre = nombre
        self.tipo = tipo
        self.direccion = direccion
        self.linea_decl = linea
        self.col_decl = col
        self.lineas = [linea] if linea is not None else []
        self.valor = None          # valor conocido en compilación
        self.inicializada = False  # ¿ya recibió un valor (asignación o cin)?

    def __repr__(self):
        return (f"Simbolo({self.nombre!r}, {self.tipo!r}, "
                f"dir={self.direccion}, lineas={self.lineas})")


class TablaSimbolos:
    def __init__(self):
        self._cubetas = [[] for _ in range(SIZE)]
        self._siguiente_dir = 0    # siguiente localidad de memoria libre

    # ── Función hash ────────────────────────────────────────────────────────
    @staticmethod
    def hash(nombre):
        temp = 0
        for ch in nombre:
            temp = ((temp << SHIFT) + ord(ch)) % SIZE
        return temp

    # ── Operaciones ─────────────────────────────────────────────────────────
    def buscar(self, nombre):
        """Devuelve el Simbolo asociado a `nombre`, o None si no está declarado."""
        for sim in self._cubetas[self.hash(nombre)]:
            if sim.nombre == nombre:
                return sim
        return None

    def insertar(self, nombre, tipo, linea=None, col=None):
        """Inserta un identificador recién declarado y le asigna dirección.
        Devuelve el Simbolo creado, o None si el nombre ya existía (la
        declaración duplicada no modifica la tabla)."""
        if self.buscar(nombre) is not None:
            return None
        sim = Simbolo(nombre, tipo, self._siguiente_dir, linea, col)
        self._siguiente_dir += 1
        self._cubetas[self.hash(nombre)].append(sim)
        return sim

    def eliminar(self, nombre):
        """Elimina un identificador. Devuelve True si existía."""
        cubeta = self._cubetas[self.hash(nombre)]
        for i, sim in enumerate(cubeta):
            if sim.nombre == nombre:
                del cubeta[i]
                return True
        return False

    def existe(self, nombre):
        return self.buscar(nombre) is not None

    __contains__ = existe

    def tipo_de(self, nombre):
        """Tipo asociado al identificador, o None si no está declarado."""
        sim = self.buscar(nombre)
        return sim.tipo if sim else None

    def registrar_linea(self, nombre, linea):
        """Agrega una línea de uso (sin repetir) al identificador."""
        sim = self.buscar(nombre)
        if sim is not None and linea is not None and linea not in sim.lineas:
            sim.lineas.append(linea)
        return sim

    # ── Consulta global ─────────────────────────────────────────────────────
    def simbolos(self):
        """Todos los símbolos, ordenados por dirección de memoria."""
        todos = [s for cubeta in self._cubetas for s in cubeta]
        return sorted(todos, key=lambda s: s.direccion)

    def __len__(self):
        return sum(len(c) for c in self._cubetas)

    # ── Presentación ────────────────────────────────────────────────────────
    def filas(self):
        """Filas listas para mostrar: (nombre, tipo, dirección, hash, valor,
        asignada, líneas)."""
        filas = []
        for s in self.simbolos():
            filas.append((
                s.nombre,
                s.tipo,
                str(s.direccion),
                str(self.hash(s.nombre)),
                formatear_valor(s.valor) if s.valor is not None else '—',
                'sí' if s.inicializada else 'no',
                ', '.join(str(l) for l in s.lineas),
            ))
        return filas

    def formatear(self):
        """Tabla en texto de ancho fijo para la pestaña «Símbolos»."""
        encabezados = ('Nombre', 'Tipo', 'Dirección', 'Hash', 'Valor', 'Asignada', 'Líneas')
        filas = self.filas()
        if not filas:
            return "(tabla de símbolos vacía)"
        anchos = [
            max(len(encabezados[i]), *(len(f[i]) for f in filas))
            for i in range(len(encabezados))
        ]

        def linea(celdas):
            return '  '.join(c.ljust(anchos[i]) for i, c in enumerate(celdas)).rstrip()

        salida = [linea(encabezados), '  '.join('─' * a for a in anchos)]
        salida += [linea(f) for f in filas]
        salida.append('')
        salida.append(f"{len(filas)} identificador(es) · tabla hash de {SIZE} cubetas")
        return '\n'.join(salida)


def formatear_valor(valor):
    """Texto de un valor calculado en compilación."""
    if valor is None:
        return ''
    if isinstance(valor, bool):
        return 'true' if valor else 'false'
    if isinstance(valor, float):
        return repr(round(valor, 6))
    return str(valor)
