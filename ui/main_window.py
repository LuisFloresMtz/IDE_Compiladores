from PySide6.QtWidgets import QMainWindow, QLabel, QFileDialog, QMessageBox
from PySide6.QtCore import Qt

from editor.tab_editor import TabEditor
from ui.panels import OutputPanels
from ui.sidebar import FileExplorer
from ui.top_bar import create_top_bar, COLORS
from ui.menu_bar import create_menu_bar
from ui.tool_bar import create_toolbar


# ── Estilo global de la ventana principal ─────────────────────────────────────
MAIN_STYLE = f"""
QMainWindow {{
    background-color: {COLORS['bg_dark']};
}}

/* Status bar */
QStatusBar {{
    background-color: {COLORS['bg_bar']};
    color: {COLORS['text_dim']};
    font-family: 'Segoe UI', 'SF Pro Text', sans-serif;
    font-size: 12px;
    border-top: 1px solid {COLORS['border']};
}}

QStatusBar QLabel {{
    color: {COLORS['text_dim']};
    padding: 0 8px;
}}

/* Splitter entre paneles */
QSplitter::handle {{
    background: {COLORS['border']};
    width: 1px;
    height: 1px;
}}

/* Dock widgets */
QDockWidget {{
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
}}

/* Tooltip global */
QToolTip {{
    background-color: {COLORS['bg_bar']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 4px 8px;
    font-family: 'Segoe UI', sans-serif;
    font-size: 12px;
}}

/* Diálogos (open/save) */
QFileDialog {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text']};
}}

QMessageBox {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text']};
}}
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("IDE Compiladores")
        self.resize(1280, 760)
        self.setMinimumSize(800, 500)

        self.current_file: str | None = None

        # ── Estilos globales ──────────────────────────────────────────────────
        self.setStyleSheet(MAIN_STYLE)

        # ── Editor central (tabs) ─────────────────────────────────────────────
        self.tabeditor = TabEditor()
        self.setCentralWidget(self.tabeditor)

        editor = self.tabeditor.current_editor()
        if editor:
            editor.cursorPositionInfo.connect(self.update_cursor_position)

        # ── Panel inferior (consola) ──────────────────────────────────────────
        self.output_panel = OutputPanels(self)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.output_panel)
        self.resizeDocks([self.output_panel], [200], Qt.Orientation.Vertical)

        # ── Sidebar (explorador de archivos) ──────────────────────────────────
        self.sidebar = FileExplorer(self)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.sidebar)
        self.resizeDocks([self.sidebar], [220], Qt.Orientation.Horizontal)
        self.sidebar.tree.doubleClicked.connect(self.open_file_from_sidebar)

        # ── Status bar ────────────────────────────────────────────────────────
        self.cursor_label = QLabel("Ln 1, Col 1")
        self.statusBar().addPermanentWidget(self.cursor_label)
        self.statusBar().showMessage("Listo")

        # ── Menú y barra de herramientas ──────────────────────────────────────
        menu_bar, tool_bar = create_top_bar(self)
        create_menu_bar(self, menu_bar)
        create_toolbar(self, tool_bar)

    # ── Status bar ────────────────────────────────────────────────────────────

    def update_cursor_position(self, line: int, col: int):
        self.cursor_label.setText(f"Ln {line}, Col {col}")

    # ── Gestión de archivos ───────────────────────────────────────────────────

    def new_file(self):
        self.tabeditor.add_tab("Nuevo.txt")
        self.current_file = None
        self.statusBar().showMessage("Nuevo archivo creado")

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Abrir archivo", "",
            "Archivos de código (*.txt *.py *.c *.h *.cpp *.java);;Todos (*.*)"
        )
        if not file_path:
            return

        filename = file_path.split("/")[-1]
        self.tabeditor.add_tab(filename)

        editor = self.tabeditor.current_editor()
        if editor:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    editor.setPlainText(f.read())
                editor.cursorPositionInfo.connect(self.update_cursor_position)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo abrir el archivo:\n{e}")
                return

        self.current_file = file_path
        self.statusBar().showMessage(f"Abierto: {filename}")

    def save_file(self):
        editor = self.tabeditor.current_editor()
        if not editor:
            return

        if not self.current_file:
            self.save_file_as()
            return

        try:
            with open(self.current_file, "w", encoding="utf-8") as f:
                f.write(editor.toPlainText())
            self.statusBar().showMessage(f"Guardado: {self.current_file.split('/')[-1]}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar:\n{e}")

    def save_file_as(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar como", "",
            "Archivos de código (*.txt *.py *.c *.h *.cpp *.java);;Todos (*.*)"
        )
        if not file_path:
            return

        self.current_file = file_path
        self.tabeditor.set_tab_title(file_path.split("/")[-1])
        self.save_file()

    def close_file(self):
        self.tabeditor.close_tab(self.tabeditor.tabs.currentIndex())
        self.current_file = None

    # ── Análisis / Compilación ────────────────────────────────────────────────

    def _get_source(self) -> str | None:
        editor = self.tabeditor.current_editor()
        return editor.toPlainText() if editor else None

    def run_lexico(self):
        src = self._get_source()
        if src is not None:
            self.output_panel.write(self.output_panel.lexico_output, "▶ Análisis Léxico iniciado…", "info")
            # TODO: conectar al analizador léxico real y usar write() con kind apropiado

    def run_sintactico(self):
        self.output_panel.write(self.output_panel.sintactico_output, "▶ Análisis Sintáctico iniciado…", "info")

    def run_semantico(self):
        self.output_panel.write(self.output_panel.semantico_output, "▶ Análisis Semántico iniciado…", "info")

    def run_intermedio(self):
        self.output_panel.write(self.output_panel.codigo_intermedio_output, "▶ Generando código intermedio…", "info")

    def run_ejecucion(self):
        self.output_panel.write(self.output_panel.ejecucion_output, "▶ Ejecutando…", "success")

    # ── Sidebar ───────────────────────────────────────────────────────────────

    def open_file_from_sidebar(self, index):
        file_path = self.sidebar.model.filePath(index)
        if self.sidebar.model.isDir(index):
            return

        filename = file_path.split("/")[-1]
        self.tabeditor.add_tab(filename)

        editor = self.tabeditor.current_editor()
        if editor:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    editor.setPlainText(f.read())
                editor.cursorPositionInfo.connect(self.update_cursor_position)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo abrir:\n{e}")
                return

        self.current_file = file_path
        self.statusBar().showMessage(f"Abierto: {filename}")