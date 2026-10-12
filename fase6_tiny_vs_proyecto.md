# Fase 6 — TINY frente al lenguaje del proyecto

Compiladores II · comparación completa: código TINY → árbol sintáctico → tabla de símbolos → tipos anotados → resultado semántico → error semántico → comparación con la gramática del proyecto.

---

## 1. Código fuente: el programa TINY (factorial)

Ejemplo clásico de Louden — el mismo con que se introduce `analyze.c` en el compilador de referencia de TINY. Sin declaraciones: la variable nace en su primer uso.

```
1  { calcula el factorial de x }
2  read x;
3  if 0 < x then
4    fact := 1;
5    repeat
6      fact := fact * x;
7      x := x - 1
8    until x = 0;
9    write fact
10 end
```

10 líneas · 2 identificadores (`x`, `fact`) · sin sentencia de declaración.

---

## 2. Árbol sintáctico (AST)

TINY encadena las sentencias de un bloque con un puntero "hermano" (sin nodo contenedor). Aquí se agrupan como `entonces` / `cuerpo` para leerse igual que el AST del proyecto.

```
programa
├─ read(x)                              L2
└─ if                                   L3
    ├─ test: <                          L3
    │    ├─ 0
    │    └─ x
    └─ entonces
         ├─ fact := 1                   L4
         ├─ repeat                      L5
         │    ├─ cuerpo
         │    │    ├─ fact := fact * x  L6
         │    │    └─ x := x - 1        L7
         │    └─ until: x = 0           L8
         └─ write(fact)                 L9
```

---

## 3. Tabla de símbolos

`symtab.c` es una tabla hash: la clave es el nombre; el valor, un contador de **ubicación de memoria** asignado en el orden de primera aparición, más la lista de líneas donde el nombre vuelve a aparecer.

| Identificador | Ubicación | Primera aparición       | Líneas donde aparece |
|----------------|-----------|--------------------------|------------------------|
| `x`            | 0         | L2 (`read x`)            | 2, 3, 6, 7, 8          |
| `fact`         | 1         | L4 (`fact := 1`)         | 4, 6, 9                |

La ubicación es un contador global que solo avanza al insertar un nombre nuevo. No hay columna de "tipo declarado" porque TINY no declara.

---

## 4. Tipos anotados: `checkNode()`

TINY solo conoce dos tipos: **Integer** (identificadores, constantes, `+ - * /`) y **Boolean** (únicamente el resultado de `<` o `=`). El recorrido postorden anota cada nodo y valida en el mismo paso.

| Línea | Expresión            | Tipo inferido | Regla semántica                | Resultado |
|-------|-----------------------|----------------|----------------------------------|-----------|
| 3     | `0 < x`               | Boolean        | test de `if` ≠ Integer           | ✓ cumple  |
| 4     | `fact := 1`           | Integer        | valor de assign = Integer        | ✓ cumple  |
| 6     | `fact * x`            | Integer        | operandos aritméticos = Integer  | ✓ cumple  |
| 6     | `fact := fact*x`      | Integer        | valor de assign = Integer        | ✓ cumple  |
| 7     | `x - 1`               | Integer        | operandos aritméticos = Integer  | ✓ cumple  |
| 7     | `x := x-1`            | Integer        | valor de assign = Integer        | ✓ cumple  |
| 8     | `x = 0`               | Boolean        | test de `until` ≠ Integer        | ✓ cumple  |
| 9     | `write fact`          | Integer        | expresión de write = Integer     | ✓ cumple  |

---

## 5. Resultado del análisis semántico

Con las 8 verificaciones satisfechas, `typeCheck()` termina sin invocar `typeError()` ni una vez.

- **0** errores de tipo reportados
- **2** identificadores registrados
- **2** ubicaciones de memoria asignadas (0 y 1)
- **8** chequeos de tipo pasados

La fase de generación de código puede arrancar con esta tabla de símbolos.

---

## 6. Ejemplo semánticamente incorrecto

Variante de 3 líneas: se prueba directamente un identificador entero, sin operador relacional de por medio.

```
1  { variante con error semántico }
2  read x;
3  if x then
4    write x
5  end
```

- **Dónde ocurre:** nodo `IfK` en L3, al revisar el hijo test.
- **Regla violada:** el test de un `if` (y de un `repeat`) debe ser **Boolean** — y Boolean en TINY solo lo produce `<` o `=`. `x` por sí solo es Integer, nunca Boolean, así que no hay forma correcta de escribir `if x then`.
- **`typeError()` genera:**

```
Type error at line 3: if test is not Boolean
```

---

## 7. Comparación: TINY vs. la gramática del proyecto

La gramática del equipo (`syntactic_analyzer/parser.py`) ya resuelve precedencia y asociatividad; falta la capa semántica. Fragmento real del proyecto (tomado de `tests/test.txt`) al lado del equivalente TINY:

**TINY**
```
if 0 < x then
  fact := 1
end
```

**Proyecto**
```
if(2>3 && a!=7)then
    y=a+3;
end;
```

Nótese el `;` obligatorio tras `end` y los operadores `&&` / `!=` que TINY no tiene.

| Aspecto                      | TINY                                              | Proyecto                                                |
|-------------------------------|----------------------------------------------------|-----------------------------------------------------------|
| Declaración de variables      | no existe — nace en el primer uso                  | `tipo id(,id)*;` explícita, antes de usar                 |
| Tipos declarables             | ninguno (todo Integer implícito)                   | `int`, `float`, `bool`                                     |
| Boolean                       | efímero: solo resultado de `<` / `=`, no se guarda en variables | tipo de primera clase, con literales `true`/`false` |
| Relacionales                  | `<` `=` (2)                                        | `< <= > >= == !=` (6)                                      |
| Lógicos                       | ninguno                                            | `&& \|\| !`                                                |
| Aritméticos                   | `+ - * /`                                          | `+ - * / % ^`, más `++ --`                                 |
| Control de flujo              | `if`, `repeat…until`                               | `if…then…else…end`, `while`, `do…while`                    |
| E/S                           | `read` / `write` — una expresión Integer           | `cin>>id`, `cout<<` mezcla cadena + expresión               |
| "test debe ser Boolean"       | solo `if` y `repeat` la exigen                     | debe generalizarse a `if`, `while` y `do…while`             |
| Tabla de símbolos             | nombre → ubicación + líneas (sin tipo)             | necesita columna de tipo declarado                          |
| Nodo de bloque                | lista enlazada por hermano, sin nodo               | nodos explícitos `entonces` / `cuerpo` / `else`              |

---

## 8. Qué reutilizar del modelo TINY vs. qué extender

El diseño de `analyze.c` no es específico de TINY: la mitad es arquitectura general de un analizador semántico y sirve tal cual; la otra mitad asume "un solo tipo Integer" y hay que ampliarla.

### ✓ Reutilizar tal cual

- Un único recorrido del AST que construye la tabla de símbolos y verifica tipos a la vez (preProc / postProc).
- Tabla de símbolos: nombre → contador de ubicación + lista de líneas de aparición.
- `typeError(nodo, mensaje)` que acumula errores sin abortar — el mismo patrón que ya usa `Parser.error()` en `parser.py` (cuelga el error del nodo actual y sigue).
- Anotar el tipo inferido directamente sobre el nodo del AST, para que el generador de código lo consuma después — encaja con el atributo `Node.type` que ya existe.

### ⚠ Extender o modificar

- Agregar chequeo de **declarado antes de usar** y de **declaración duplicada** — TINY no los necesita porque declara implícito.
- Tabla de tipos ampliada: `int`/`float` con reglas de promoción, y `bool` de primera clase con literales.
- Generalizar "el test debe ser Boolean" de `if`/`repeat` a `if`, `while` y `do…while`.
- Verificar que el operando de `++` / `--` sea un identificador numérico ya declarado (TINY no tiene estos operadores).
- En `cout`, chequear solo las partes-expresión y saltar las partes-cadena — TINY nunca mezcla texto y expresión en `write`.
- Guardar el tipo declarado en la tabla de símbolos (columna nueva), no solo la ubicación.

---

## 9. Dónde está el proyecto hoy

El repositorio ya tiene analizador léxico y sintáctico funcionando (AST con `entonces`/`cuerpo`/`else`, precedencia y asociatividad resueltas). La fase semántica es el siguiente paso, y TINY da el plano de arquitectura.

1. Extender `Node` con un campo de tipo inferido, poblado en un recorrido postorden como el de `checkNode()`.
2. Construir la tabla de símbolos sobre las declaraciones ya parseadas (`declaracion_variable`), agregando la columna de tipo.
3. Portar el patrón `typeError()` para acumular errores semánticos junto a los sintácticos que ya recolecta `Parser.errors`.
4. Escribir la tabla de tipos para `int/float/bool` antes de tocar el generador de código intermedio.
