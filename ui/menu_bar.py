from PySide6.QtGui import QAction, QKeySequence


def create_menu_bar(main_window, menu_bar):
    """
    Construye el menú completo: Archivo y Compilar.
    Los estilos visuales (QSS) están definidos en top_bar.py (MENUBAR_STYLE).
    """

    # ════════════════════════════════════════════════════════════════════════
    # MENÚ: ARCHIVO
    # ════════════════════════════════════════════════════════════════════════
    file_menu = menu_bar.addMenu("Archivo")

    main_window.action_new = _action(
        main_window,
        text="Nuevo",
        shortcut=QKeySequence.StandardKey.New,
        tip="Crear un nuevo archivo",
        slot=main_window.new_file,
    )

    main_window.action_open = _action(
        main_window,
        text="Abrir…",
        shortcut=QKeySequence.StandardKey.Open,
        tip="Abrir un archivo existente",
        slot=main_window.open_file,
    )

    main_window.action_save = _action(
        main_window,
        text="Guardar",
        shortcut=QKeySequence.StandardKey.Save,
        tip="Guardar el archivo actual",
        slot=main_window.save_file,
    )

    main_window.action_save_as = _action(
        main_window,
        text="Guardar como…",
        shortcut=QKeySequence.StandardKey.SaveAs,
        tip="Guardar con un nombre diferente",
        slot=main_window.save_file_as,
    )

    main_window.action_close = _action(
        main_window,
        text="Cerrar",
        shortcut="Ctrl+W",
        tip="Cerrar el archivo actual",
        slot=main_window.close_file,
    )

    main_window.action_exit = _action(
        main_window,
        text="Salir",
        shortcut="Alt+F4",
        tip="Salir de la aplicación",
        slot=main_window.close,
    )

    file_menu.addAction(main_window.action_new)
    file_menu.addAction(main_window.action_open)
    file_menu.addAction(main_window.action_close)
    file_menu.addSeparator()
    file_menu.addAction(main_window.action_save)
    file_menu.addAction(main_window.action_save_as)
    file_menu.addSeparator()
    file_menu.addAction(main_window.action_exit)

    # ════════════════════════════════════════════════════════════════════════
    # MENÚ: COMPILAR
    # ════════════════════════════════════════════════════════════════════════
    compile_menu = menu_bar.addMenu("Compilar")

    main_window.action_lexico = _action(
        main_window,
        text="Análisis Léxico",
        shortcut="F9",
        tip="Ejecutar el análisis léxico (F9)",
        slot=main_window.run_lexico,
    )

    main_window.action_sintactico = _action(
        main_window,
        text="Análisis Sintáctico",
        tip="Ejecutar el análisis sintáctico",
        slot=main_window.run_sintactico,
    )

    main_window.action_semantico = _action(
        main_window,
        text="Análisis Semántico",
        tip="Ejecutar el análisis semántico",
        slot=main_window.run_semantico,
    )

    main_window.action_intermedio = _action(
        main_window,
        text="Código Intermedio",
        tip="Generar código intermedio",
        slot=main_window.run_intermedio,
    )

    main_window.action_run = _action(
        main_window,
        text="Ejecutar",
        shortcut="F10",
        tip="Ejecutar el programa (F10)",
        slot=main_window.run_ejecucion,
    )

    compile_menu.addAction(main_window.action_lexico)
    compile_menu.addAction(main_window.action_sintactico)
    compile_menu.addAction(main_window.action_semantico)
    compile_menu.addAction(main_window.action_intermedio)
    compile_menu.addSeparator()
    compile_menu.addAction(main_window.action_run)


# ── Helper ────────────────────────────────────────────────────────────────────
def _action(parent, *, text: str, slot, shortcut=None, tip: str = "") -> QAction:
    """Crea un QAction con texto, atajo, tooltip y conexión de señal."""
    act = QAction(text, parent)
    if shortcut:
        act.setShortcut(shortcut)
    if tip:
        act.setStatusTip(tip)
        act.setToolTip(tip)
    act.triggered.connect(slot)
    return act