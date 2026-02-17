from PySide6.QtWidgets import QTabWidget, QTextEdit


class OutputPanels(QTabWidget):
    def __init__(self):
        super().__init__()

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

        self.addTab(self.lexico_output, "Léxico (Tokens)")
        self.addTab(self.sintactico_output, "Sintáctico")
        self.addTab(self.semantico_output, "Semántico")
        self.addTab(self.codigo_intermedio_output, "Código Intermedio")
        self.addTab(self.tabla_simbolos_output, "Tabla de Símbolos")
        self.addTab(self.errores_output, "Errores")
        self.addTab(self.ejecucion_output, "Ejecución")
