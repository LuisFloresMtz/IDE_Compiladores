from PySide6.QtGui import QAction


def create_menu_bar(main_window):
    menu_bar = main_window.menuBar()

    # Archivo
    file_menu = menu_bar.addMenu("Archivo")

    new_action = QAction("Nuevo", main_window)
    new_action.triggered.connect(main_window.new_file)

    open_action = QAction("Abrir", main_window)
    open_action.triggered.connect(main_window.open_file)

    close_action = QAction("Cerrar", main_window)
    close_action.triggered.connect(main_window.close_file)

    save_action = QAction("Guardar", main_window)
    save_action.triggered.connect(main_window.save_file)

    save_as_action = QAction("Guardar como", main_window)
    save_as_action.triggered.connect(main_window.save_file_as)

    exit_action = QAction("Salir", main_window)
    exit_action.triggered.connect(main_window.close)

    file_menu.addAction(new_action)
    file_menu.addAction(open_action)
    file_menu.addAction(close_action)
    file_menu.addSeparator()
    file_menu.addAction(save_action)
    file_menu.addAction(save_as_action)
    file_menu.addSeparator()
    file_menu.addAction(exit_action)

    # Compilar
    compile_menu = menu_bar.addMenu("Compilar")

    lexico_action = QAction("Análisis Léxico", main_window)
    lexico_action.triggered.connect(main_window.run_lexico)

    sintactico_action = QAction("Análisis Sintáctico", main_window)
    sintactico_action.triggered.connect(main_window.run_sintactico)

    semantico_action = QAction("Análisis Semántico", main_window)
    semantico_action.triggered.connect(main_window.run_semantico)

    intermedio_action = QAction("Código Intermedio", main_window)
    intermedio_action.triggered.connect(main_window.run_intermedio)

    ejecutar_action = QAction("Ejecución", main_window)
    ejecutar_action.triggered.connect(main_window.run_ejecucion)

    compile_menu.addAction(lexico_action)
    compile_menu.addAction(sintactico_action)
    compile_menu.addAction(semantico_action)
    compile_menu.addAction(intermedio_action)
    compile_menu.addSeparator()
    compile_menu.addAction(ejecutar_action)
