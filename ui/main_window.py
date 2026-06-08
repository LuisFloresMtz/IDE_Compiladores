from PySide6.QtWidgets import QMainWindow, QLabel, QFileDialog, QMessageBox
from PySide6.QtCore import Qt

from editor.tab_editor import TabEditor
from ui.panels import OutputPanels
from ui.sidebar import FileExplorer
from ui.top_bar import create_top_bar, COLORS
from ui.menu_bar import create_menu_bar
from ui.tool_bar import create_toolbar
from lexical_analyzer.lexical_analyzer import (
    tokenize_with_positions, tokenize_with_lines, operator_category,
)
from syntactic_analyzer.parser import parse_tokens
from syntactic_analyzer.tree_view import SyntaxTreeWindow

TIPO_ES = {
    'KEYWORD':        'PALABRA RESERVADA',
    'IDENTIFIER':     'IDENTIFICADOR',
    'INTEGER':        'ENTERO',
    'FLOAT':          'REAL',
    'STRING_LITERAL': 'CADENA',
    'DELIMITER':      'DELIMITADOR',
}

MAIN_STYLE = f"""
QMainWindow {{
    background-color: {COLORS['bg_dark']};
}}
QStatusBar {{
    background-color: {COLORS['bg_bar']};
    color: {COLORS['text_dim']};
    border-top: 1px solid {COLORS['border']};
    font-family: 'Segoe UI', sans-serif;
    font-size: 12px;
}}
QDockWidget {{
    background: {COLORS['bg_dark']};
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

    def _show_output(self, tab_index):
        self.output_panel.show()
        self.output_panel.raise_()
        self.output_panel.tabs.setCurrentIndex(tab_index)

    # COMPILER (usa output_panel)
    def run_lexico(self):
        import traceback
        try:
            editor = self.tabeditor.current_editor()
            if not editor:
                self.output_panel.lexico_output.setPlainText("No hay ningún archivo abierto.")
                self._show_output(0)
                return

            source = editor.toPlainText()
            tokens = tokenize_with_positions(source)

            if not tokens:
                self.output_panel.lexico_output.setPlainText("(sin tokens)")
                self._show_output(0)
                return

            lines = []
            errors = []
            for tipo, valor, start, _end in tokens:
                line_no = source.count('\n', 0, start) + 1
                if tipo == 'ERROR':
                    last_nl = source.rfind('\n', 0, start)
                    col_no = start - last_nl if last_nl != -1 else start + 1
                    errors.append(
                        f"Línea {line_no}, columna {col_no}: "
                        f"token no reconocido «{valor}»"
                    )
                    continue
                if tipo == 'COMMENT':
                    continue
                if tipo == 'OPERATOR':
                    categoria = operator_category(valor)
                else:
                    categoria = TIPO_ES.get(tipo, tipo)
                lines.append(f"Línea {line_no:<3d}  {categoria:20s}  {valor}")

            self.output_panel.lexico_output.setPlainText("\n".join(lines))

            if errors:
                self.output_panel.errores_output.setPlainText("\n".join(errors))
            else:
                self.output_panel.errores_output.setPlainText("Sin errores léxicos.")

            self._show_output(0)

        except Exception:
            self.output_panel.lexico_output.setPlainText(traceback.format_exc())
            self._show_output(0)

    def run_sintactico(self):
        import traceback
        panel = self.output_panel
        try:
            editor = self.tabeditor.current_editor()
            if not editor:
                panel.sintactico_output.setPlainText("No hay ningún archivo abierto.")
                self._show_output(1)
                return

            source = editor.toPlainText()
            tokens = tokenize_with_lines(source)

            # ── 1) Errores léxicos: deben eliminarse antes de validar sintaxis ─
            lexicos = [
                f"Léxico — Línea {ln}, columna {col}: token no reconocido «{val}»"
                for tipo, val, ln, col in tokens if tipo == 'ERROR'
            ]
            # Stream para el parser: sin comentarios ni tokens de error.
            stream = [t for t in tokens if t[0] not in ('COMMENT', 'ERROR')]

            # ── 2) Análisis sintáctico ────────────────────────────────────────
            ast, sintacticos = parse_tokens(stream)

            # ── 3) Salida en consola Sintáctico ──────────────────────────────
            panel.sintactico_output.clear()
            panel.write(panel.sintactico_output, "▶ Análisis Sintáctico", "info")
            if lexicos:
                panel.write(panel.sintactico_output,
                            f"⚠ {len(lexicos)} error(es) léxico(s): corrígelos para una validación completa.",
                            "warning")
            self._print_ast(ast, panel.sintactico_output)

            # ── 4) Consola Errores ───────────────────────────────────────────
            err_lines = list(lexicos)
            err_lines += [
                f"Sintáctico — Línea {ln}, columna {col}: {msg}"
                for msg, ln, col in sintacticos
            ]
            if err_lines:
                panel.errores_output.setPlainText("\n".join(err_lines))
            else:
                panel.errores_output.setPlainText("Sin errores léxicos ni sintácticos.")

            if sintacticos:
                panel.write(panel.sintactico_output,
                            f"✗ {len(sintacticos)} error(es) sintáctico(s). Ver pestaña Errores.",
                            "error")
            else:
                panel.write(panel.sintactico_output, "✓ Análisis sintáctico correcto.", "success")

            # ── 5) Ventana del árbol (gráfica, colapsable, auto-expandida) ────
            self.tree_window = SyntaxTreeWindow(ast, n_errores=len(sintacticos), parent=self)
            self.tree_window.show()
            self.tree_window.raise_()

            self._show_output(1)

        except Exception:
            panel.sintactico_output.setPlainText(traceback.format_exc())
            self._show_output(1)

    def _print_ast(self, node, console, depth=0):
        """Vuelca el AST en texto indentado en la consola (respaldo del árbol gráfico)."""
        if node is None:
            return
        prefix = "  " * depth
        suffix = f"  (L{node.line}, C{node.col})" if node.line is not None else ""
        self.output_panel.write(console, f"{prefix}{node.label()}{suffix}", "dim" if depth else "accent")
        for child in node.children:
            self._print_ast(child, console, depth + 1)

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