from PySide6.QtWidgets import (
    QMainWindow, QLabel, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt

from editor.tab_editor import TabEditor
from ui.panels import OutputPanels   # Debe heredar de QDockWidget
from ui.sidebar import FileExplorer
# from ui.tool_bar import create_toolbar
from ui.menu_bar import create_menu_bar


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("IDE - Proyecto Compiladores")
        self.resize(1200, 700)

        self.current_file = None

        # EDITOR CENTRAL
        self.tabeditor = TabEditor()
        self.setCentralWidget(self.tabeditor)

        editor = self.tabeditor.current_editor()
        if editor:
            editor.cursorPositionInfo.connect(self.update_cursor_position)

        # PANEL INFERIOR (CONSOLA)
        self.output_panel = OutputPanels(self)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.output_panel)

        self.resizeDocks(
            [self.output_panel],
            [200],
            Qt.Vertical
        )

        # SIDEBAR
        self.sidebar = FileExplorer(self)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.sidebar)
        self.sidebar.tree.doubleClicked.connect(self.open_file_from_sidebar)

        # STATUS BAR
        self.cursor_label = QLabel("Ln 1, Col 1")
        self.statusBar().addPermanentWidget(self.cursor_label)

        # MENU Y TOOLBAR
        create_menu_bar(self)
        # create_toolbar(self)

        # ESTILO OSCURO
        self.setStyleSheet("""
        QMainWindow { background-color: #2b2b2b; }

        QMenuBar {
            background-color: #2b2b2b;
            color: white;
        }

        QMenuBar::item:selected {
            background-color: #3c3f41;
        }

        QMenu {
            background-color: #2b2b2b;
            color: white;
        }

        QToolBar {
            background-color: #313335;
        }

        QToolButton {
            background-color: #3c3f41;
            color: white;
            padding: 5px;
        }

        QToolButton:hover {
            background-color: #505354;
        }

        QDockWidget {
            background-color: #2b2b2b;
            color: white;
        }

        QTabWidget::pane {
            background: #1e1e1e;
        }

        QTabBar::tab {
            background: #2d2d2d;
            color: white;
            padding: 6px;
        }

        QTabBar::tab:selected {
            background: #3c3f41;
        }
        """)

    # STATUS
    def update_cursor_position(self, line, col):
        self.cursor_label.setText(f"Ln {line}, Col {col}")

    # FILES
    def new_file(self):
        self.tabeditor.add_tab("Nuevo.txt")
        self.current_file = None

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Abrir archivo", "", "Archivos (*.txt *.py *.c);;Todos (*.*)"
        )
        if file_path:
            self.tabeditor.add_tab(file_path.split("/")[-1])
            editor = self.tabeditor.current_editor()
            if editor:
                with open(file_path, "r", encoding="utf-8") as f:
                    editor.setPlainText(f.read())
            self.current_file = file_path

    def save_file(self):
        editor = self.tabeditor.current_editor()
        if editor and self.current_file:
            with open(self.current_file, "w", encoding="utf-8") as f:
                f.write(editor.toPlainText())
            QMessageBox.information(self, "Guardar", "Archivo guardado.")

    def save_file_as(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar como", "", "Archivos (*.txt *.py *.c);;Todos (*.*)"
        )
        if file_path:
            self.current_file = file_path
            self.save_file()

    def close_file(self):
        self.tabeditor.close_current_tab()
        self.current_file = None

    # COMPILER (usa output_panel)
    def run_lexico(self):
        self.output_panel.lexico_output.setPlainText("Análisis Léxico...")

    def run_sintactico(self):
        self.output_panel.sintactico_output.setPlainText("Análisis Sintáctico...")

    def run_semantico(self):
        self.output_panel.semantico_output.setPlainText("Análisis Semántico...")

    def run_intermedio(self):
        self.output_panel.codigo_intermedio_output.setPlainText("Código Intermedio...")

    def run_ejecucion(self):
        self.output_panel.ejecucion_output.setPlainText("Ejecución...")

    # SIDEBAR
    def open_file_from_sidebar(self, index):
        file_path = self.sidebar.model.filePath(index)
        if self.sidebar.model.isDir(index):
            return

        self.tabeditor.add_tab(file_path.split("/")[-1])
        editor = self.tabeditor.current_editor()
        if editor:
            with open(file_path, "r", encoding="utf-8") as f:
                editor.setPlainText(f.read())

        self.current_file = file_path