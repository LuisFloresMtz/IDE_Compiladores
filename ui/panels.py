from PySide6.QtWidgets import QDockWidget, QTabWidget, QTextEdit, QWidget, QLabel, QHBoxLayout, QVBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCharFormat, QColor, QTextCursor


try:
    from ui.top_bar import COLORS
except ImportError:
    COLORS = {
        "bg_dark":      "#1e1e2e",
        "bg_bar":       "#181825",
        "bg_hover":     "#313244",
        "bg_pressed":   "#45475a",
        "accent":       "#89b4fa",
        "accent_dim":   "#585b70",
        "text":         "#cdd6f4",
        "text_dim":     "#a6adc8",
        "border":       "#313244",
    }

CONSOLE_COLORS = {
    "bg":      "#11111b",
    "text":    "#cdd6f4",
    "success": "#a6e3a1",
    "warning": "#f9e2af",
    "error":   "#f38ba8",
    "info":    "#89b4fa",
    "dim":     "#585b70",
    "accent":  "#cba6f7",
}

TABS_STYLE = f"""
QTabWidget {{
    border: none;
}}

QTabWidget::pane {{
    border: none;
    background: {CONSOLE_COLORS['bg']};
    top: 0px;
}}

QTabBar::tab {{
    background: {COLORS['bg_bar']};
    color: {COLORS['text_dim']};
    font-family: 'Segoe UI', 'SF Pro Text', sans-serif;
    font-size: 12px;
    padding: 6px 16px;
    border: none;
    border-bottom: 2px solid transparent;
    margin-right: 1px;
}}

QTabBar::tab:hover {{
    background: {COLORS['bg_hover']};
    color: {COLORS['text']};
}}

QTabBar::tab:selected {{
    background: {COLORS['bg_bar']};
    color: {COLORS['accent']};
    border-bottom: 2px solid {COLORS['accent']};
}}

QTabBar::tab:!selected {{
    margin-top: 0px;
}}
"""

CONSOLE_STYLE = f"""
QTextEdit {{
    background-color: {CONSOLE_COLORS['bg']};
    color: {CONSOLE_COLORS['text']};
    border: none;
    font-family: 'JetBrains Mono', 'Cascadia Code', 'Consolas', monospace;
    font-size: 13px;
    padding: 8px 12px;
    selection-background-color: {COLORS['bg_pressed']};
    selection-color: {COLORS['text']};
}}

QScrollBar:vertical {{
    background: {CONSOLE_COLORS['bg']};
    width: 8px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {COLORS['accent_dim']};
    border-radius: 4px;
    min-height: 24px;
}}

QScrollBar::handle:vertical:hover {{
    background: {COLORS['accent']};
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background: {CONSOLE_COLORS['bg']};
    height: 8px;
}}

QScrollBar::handle:horizontal {{
    background: {COLORS['accent_dim']};
    border-radius: 4px;
    min-width: 24px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {COLORS['accent']};
}}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    width: 0;
}}
"""


class OutputPanels(QDockWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # ── Suprimir title bar nativo ─────────────────────────────────────────
        self.setTitleBarWidget(QWidget())   # widget vacío = sin title bar

        # ── Dock config ───────────────────────────────────────────────────────
        self.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)
        self.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)

        # ── Contenedor raíz ───────────────────────────────────────────────────
        # Un solo QWidget con VBox: primero la barra de título, luego los tabs.
        # Esto evita cualquier empalme porque son dos widgets en un layout secuencial.
        root = QWidget()
        root.setStyleSheet(f"background: {COLORS['bg_bar']}; border: none;")
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Barra de título (header) ──────────────────────────────────────────
        header = QWidget()
        header.setFixedHeight(26)
        header.setStyleSheet(f"""
            background-color: {COLORS['bg_bar']};
            border-top: 1px solid {COLORS['border']};
            border-bottom: none;
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 0, 10, 0)
        header_layout.setSpacing(0)

        title_label = QLabel("CONSOLA")
        title_label.setStyleSheet(f"""
            color: {COLORS['text_dim']};
            background: transparent;
            font-family: 'Segoe UI', sans-serif;
            font-size: 11px;
            letter-spacing: 1px;
            font-weight: 600;
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # ── Tabs ──────────────────────────────────────────────────────────────
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(TABS_STYLE)
        self.tabs.setDocumentMode(True)

        self.lexico_output            = self._create_console()
        self.sintactico_output        = self._create_console()
        self.semantico_output         = self._create_console()
        self.codigo_intermedio_output = self._create_console()
        self.tabla_simbolos_output    = self._create_console()
        self.errores_output           = self._create_console()
        self.ejecucion_output         = self._create_console()

        for console, label in [
            (self.lexico_output,            "Léxico"),
            (self.sintactico_output,        "Sintáctico"),
            (self.semantico_output,         "Semántico"),
            (self.codigo_intermedio_output, "Intermedio"),
            (self.tabla_simbolos_output,    "Símbolos"),
            (self.errores_output,           "Errores"),
            (self.ejecucion_output,         "Ejecución"),
        ]:
            self.tabs.addTab(console, label)

        # header primero, tabs después — en orden vertical
        root_layout.addWidget(header)
        root_layout.addWidget(self.tabs)

        self.setWidget(root)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _create_console(self) -> QTextEdit:
        console = QTextEdit()
        console.setReadOnly(True)
        console.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        console.setStyleSheet(CONSOLE_STYLE)
        return console

    def write(self, console: QTextEdit, text: str, kind: str = "text"):
        """Escribe texto coloreado. kind: 'text'|'success'|'warning'|'error'|'info'|'dim'|'accent'"""
        color = CONSOLE_COLORS.get(kind, CONSOLE_COLORS["text"])
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        cursor = console.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text + "\n", fmt)
        console.setTextCursor(cursor)
        console.ensureCursorVisible()

    def clear_all(self):
        for console in [
            self.lexico_output, self.sintactico_output, self.semantico_output,
            self.codigo_intermedio_output, self.tabla_simbolos_output,
            self.errores_output, self.ejecucion_output,
        ]:
            console.clear()