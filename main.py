import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox,
    QTabWidget, QTextEdit, QSplitter, QWidget, QVBoxLayout,
    QLabel, QToolBar
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt

from editor.code_editor import CodeEditor


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("IDE - Proyecto Compiladores")
        self.resize(1200, 700)

        self.current_file = None

        # EDITOR PRINCIPAL
        self.editor = CodeEditor()
        self.editor.cursorPositionInfo.connect(self.update_cursor_position)

        # PANELES DE RESULTADOS (Tabs)
        self.tabs = QTabWidget()

        self.lexico_output = QTextEdit()
        self.lexico_output.setReadOnly(True)

        self.sintactico_output = QTextEdit()
        self.sintactico_output.setReadOnly(True)

        self.semantico_output = QTextEdit()
        self.semantico_output.setReadOnly(True)

        self.codigo_intermedio_output = QTextEdit()
        self.codigo_intermedio_output.setReadOnly(True)

        self.tabla_simbolos_output = QTextEdit()
        self.tabla_simbolos_output.setReadOnly(True)

        self.errores_output = QTextEdit()
        self.errores_output.setReadOnly(True)

        self.ejecucion_output = QTextEdit()
        self.ejecucion_output.setReadOnly(True)

        self.tabs.addTab(self.lexico_output, "Léxico (Tokens)")
        self.tabs.addTab(self.sintactico_output, "Sintáctico")
        self.tabs.addTab(self.semantico_output, "Semántico")
        self.tabs.addTab(self.codigo_intermedio_output, "Código Intermedio")
        self.tabs.addTab(self.tabla_simbolos_output, "Tabla de Símbolos")
        self.tabs.addTab(self.errores_output, "Errores")
        self.tabs.addTab(self.ejecucion_output, "Ejecución")

        # SPLITTER PRINCIPAL
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.editor)
        splitter.addWidget(self.tabs)
        splitter.setSizes([700, 500])

        container = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(splitter)
        container.setLayout(layout)

        self.setCentralWidget(container)

        # STATUS BAR (línea/columna)
        self.cursor_label = QLabel("Ln 1, Col 1")
        self.statusBar().addPermanentWidget(self.cursor_label)

        # MENUS Y TOOLBAR
        self.create_menus()
        self.create_toolbar()

    # MENÚS
    def create_menus(self):
        menu_bar = self.menuBar()

        # ---- Archivo
        file_menu = menu_bar.addMenu("Archivo")

        new_action = QAction("Nuevo", self)
        new_action.triggered.connect(self.new_file)

        open_action = QAction("Abrir", self)
        open_action.triggered.connect(self.open_file)

        close_action = QAction("Cerrar", self)
        close_action.triggered.connect(self.close_file)

        save_action = QAction("Guardar", self)
        save_action.triggered.connect(self.save_file)

        save_as_action = QAction("Guardar como", self)
        save_as_action.triggered.connect(self.save_file_as)

        exit_action = QAction("Salir", self)
        exit_action.triggered.connect(self.close)

        file_menu.addAction(new_action)
        file_menu.addAction(open_action)
        file_menu.addAction(close_action)
        file_menu.addSeparator()
        file_menu.addAction(save_action)
        file_menu.addAction(save_as_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        # ---- Compilar
        compile_menu = menu_bar.addMenu("Compilar")

        lexico_action = QAction("Análisis Léxico", self)
        lexico_action.triggered.connect(self.run_lexico)

        sintactico_action = QAction("Análisis Sintáctico", self)
        sintactico_action.triggered.connect(self.run_sintactico)

        semantico_action = QAction("Análisis Semántico", self)
        semantico_action.triggered.connect(self.run_semantico)

        intermedio_action = QAction("Código Intermedio", self)
        intermedio_action.triggered.connect(self.run_intermedio)

        ejecutar_action = QAction("Ejecución", self)
        ejecutar_action.triggered.connect(self.run_ejecucion)

        compile_menu.addAction(lexico_action)
        compile_menu.addAction(sintactico_action)
        compile_menu.addAction(semantico_action)
        compile_menu.addAction(intermedio_action)
        compile_menu.addSeparator()
        compile_menu.addAction(ejecutar_action)

    # TOOLBAR (BOTONES RÁPIDOS)
    def create_toolbar(self):
        toolbar = QToolBar("Acceso rápido")
        self.addToolBar(toolbar)

        toolbar.addAction("Léxico", self.run_lexico)
        toolbar.addAction("Sintáctico", self.run_sintactico)
        toolbar.addAction("Semántico", self.run_semantico)
        toolbar.addAction("Intermedio", self.run_intermedio)
        toolbar.addAction("Ejecutar", self.run_ejecucion)

    # ARCHIVOS
    def new_file(self):
        self.editor.clear()
        self.current_file = None
        self.setWindowTitle("IDE - Proyecto Compiladores (Nuevo archivo)")

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Abrir archivo", "", "Archivos (*.txt *.py *.c);;Todos (*.*)")
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                self.editor.setPlainText(f.read())
            self.current_file = file_path
            self.setWindowTitle(f"IDE - {file_path}")

    def save_file(self):
        if self.current_file is None:
            self.save_file_as()
            return

        with open(self.current_file, "w", encoding="utf-8") as f:
            f.write(self.editor.toPlainText())

        QMessageBox.information(self, "Guardar", "Archivo guardado correctamente.")

    def save_file_as(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Guardar como", "", "Archivos (*.txt *.py *.c);;Todos (*.*)")
        if file_path:
            self.current_file = file_path
            self.save_file()

    def close_file(self):
        self.editor.clear()
        self.current_file = None
        self.setWindowTitle("IDE - Proyecto Compiladores")

    # COMPILACIÓN (POR AHORA PLACEHOLDER)
    # Aquí después vas a meter system calls al compilador real
    def run_lexico(self):
        self.lexico_output.setPlainText("Ejecutando análisis léxico...\n\n(Aquí irán los tokens)")
        self.tabs.setCurrentWidget(self.lexico_output)

    def run_sintactico(self):
        self.sintactico_output.setPlainText("Ejecutando análisis sintáctico...\n\n(Aquí irá el árbol o salida estructurada)")
        self.tabs.setCurrentWidget(self.sintactico_output)

    def run_semantico(self):
        self.semantico_output.setPlainText("Ejecutando análisis semántico...\n\n(Aquí irán validaciones y tipos)")
        self.tabs.setCurrentWidget(self.semantico_output)

    def run_intermedio(self):
        self.codigo_intermedio_output.setPlainText("Generando código intermedio...\n\n(Aquí irá el código de tres direcciones)")
        self.tabs.setCurrentWidget(self.codigo_intermedio_output)

    def run_ejecucion(self):
        self.ejecucion_output.setPlainText("Ejecutando programa...\n\n(Aquí irá la salida del ejecutable)")
        self.tabs.setCurrentWidget(self.ejecucion_output)

    # STATUS BAR (línea/columna)
    def update_cursor_position(self, line, col):
        self.cursor_label.setText(f"Ln {line}, Col {col}")
        
    def open_file_from_sidebar(self, index):
        file_path = self.sidebar.model.filePath(index)
    
        # Si es carpeta, no hacer nada
        if self.sidebar.model.isDir(index):
            return
    
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                self.editor.setPlainText(f.read())
    
            self.current_file = file_path
            self.setWindowTitle(f"IDE - {file_path}")
    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir el archivo:\n{str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
