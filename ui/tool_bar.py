from PySide6.QtWidgets import QToolBar


def create_tool_bar(main_window):
    toolbar = QToolBar("Acceso rápido")
    main_window.addToolBar(toolbar)

    toolbar.addAction("Léxico", main_window.run_lexico)
    toolbar.addAction("Sintáctico", main_window.run_sintactico)
    toolbar.addAction("Semántico", main_window.run_semantico)
    toolbar.addAction("Intermedio", main_window.run_intermedio)
    toolbar.addAction("Ejecutar", main_window.run_ejecucion)

    return toolbar
