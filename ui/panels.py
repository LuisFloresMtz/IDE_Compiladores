from PySide6.QtWidgets import QDockWidget, QTabWidget, QTextEdit
from PySide6.QtCore import Qt


class OutputPanels(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Consola", parent)

        self.setAllowedAreas(Qt.BottomDockWidgetArea)
        self.setFeatures(QDockWidget.NoDockWidgetFeatures)

        self.tabs = QTabWidget()

        # Crear outputs tipo consola
        self.lexico_output = self.create_console()
        self.sintactico_output = self.create_console()
        self.semantico_output = self.create_console()
        self.codigo_intermedio_output = self.create_console()
        self.tabla_simbolos_output = self.create_console()
        self.errores_output = self.create_console()
        self.ejecucion_output = self.create_console()

        self.tabs.addTab(self.lexico_output, "Léxico")
        self.tabs.addTab(self.sintactico_output, "Sintáctico")
        self.tabs.addTab(self.semantico_output, "Semántico")
        self.tabs.addTab(self.codigo_intermedio_output, "Intermedio")
        self.tabs.addTab(self.tabla_simbolos_output, "Tabla Símbolos")
        self.tabs.addTab(self.errores_output, "Errores")
        self.tabs.addTab(self.ejecucion_output, "Ejecución")

        # 🎨 Estilo tabs
        self.tabs.setStyleSheet("""
        QTabWidget::pane {
            border: none;
            background: #1e1e1e;
        }

        QTabBar::tab {
            background: #2d2d30;
            color: #d4d4d4;
            padding: 6px;
        }

        QTabBar::tab:selected {
            background: #3c3f41;
        }

        QTabBar::tab:hover {
            background: #37373d;
        }
        """)

        self.setWidget(self.tabs)

    def create_console(self):
        console = QTextEdit()
        console.setReadOnly(True)

        console.setStyleSheet("""
        QTextEdit {
            background-color: #111111;
            color: #00ff88;
            border: none;
            font-family: Consolas;
            font-size: 13px;
        }
        """)

        return console