from PySide6.QtGui import QAction


def create_menu_bar(main_window):
    menu_bar = main_window.menuBar()

    file_menu = menu_bar.addMenu("Archivo")

    file_menu.addAction("Nuevo", main_window.new_file)
    file_menu.addAction("Abrir", main_window.open_file)
    file_menu.addAction("Cerrar", main_window.close_file)
    file_menu.addSeparator()
    file_menu.addAction("Guardar", main_window.save_file)
    file_menu.addAction("Guardar como", main_window.save_file_as)
    file_menu.addSeparator()
    file_menu.addAction("Salir", main_window.close)

    compile_menu = menu_bar.addMenu("Compilar")

    compile_menu.addAction("Análisis Léxico", main_window.run_lexico)
    compile_menu.addAction("Análisis Sintáctico", main_window.run_sintactico)
    compile_menu.addAction("Análisis Semántico", main_window.run_semantico)
    compile_menu.addAction("Código Intermedio", main_window.run_intermedio)
    compile_menu.addSeparator()
    compile_menu.addAction("Ejecución", main_window.run_ejecucion)