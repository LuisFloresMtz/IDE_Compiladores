"""Ventana de visualización del Árbol Sintáctico Abstracto (AST).

Muestra el AST con un QTreeWidget: estructura tipo carpeta, colapsable
(expandir/contraer nodos) y expandido automáticamente al abrirse.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QLabel, QPushButton, QDockWidget,
)
from PySide6.QtCore import Qt

try:
    from ui.top_bar import COLORS
except ImportError:
    COLORS = {
        "bg_dark": "#1e1e2e", "bg_bar": "#181825", "bg_hover": "#313244",
        "bg_pressed": "#45475a", "accent": "#89b4fa", "accent_dim": "#585b70",
        "text": "#cdd6f4", "text_dim": "#a6adc8", "border": "#313244",
    }

_TREE_STYLE = f"""
QWidget {{ background: {COLORS['bg_dark']}; }}
QLabel#titulo {{
    color: {COLORS['accent']};
    font-family: 'Segoe UI', sans-serif;
    font-size: 15px; font-weight: 600; padding: 4px 2px;
}}
QTreeWidget {{
    background: {COLORS['bg_bar']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
    font-family: 'JetBrains Mono', 'Cascadia Code', 'Consolas', monospace;
    font-size: 13px;
    outline: 0;
}}
QTreeWidget::item {{ padding: 3px 2px; }}
QTreeWidget::item:hover {{ background: {COLORS['bg_hover']}; }}
QTreeWidget::item:selected {{ background: {COLORS['bg_pressed']}; color: {COLORS['text']}; }}
QPushButton {{
    background: {COLORS['bg_hover']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 5px 14px;
    font-family: 'Segoe UI', sans-serif;
    font-size: 12px;
}}
QPushButton:hover {{ background: {COLORS['bg_pressed']}; border-color: {COLORS['accent']}; }}
QScrollBar:vertical {{ background: {COLORS['bg_bar']}; width: 10px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {COLORS['accent_dim']}; border-radius: 5px; min-height: 24px; }}
QScrollBar::handle:vertical:hover {{ background: {COLORS['accent']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{ background: {COLORS['bg_bar']}; height: 10px; }}
QScrollBar::handle:horizontal {{ background: {COLORS['accent_dim']}; border-radius: 5px; min-width: 24px; }}
QScrollBar::handle:horizontal:hover {{ background: {COLORS['accent']}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
"""


class SyntaxTreeWindow(QWidget):
    def __init__(self, ast_root, n_errores=0, parent=None):
        # Ventana independiente (Qt.Window) para tener tamaño propio amplio.
        super().__init__(parent, Qt.WindowType.Window)
        self.setWindowTitle("Árbol Sintáctico (AST)")
        self.resize(900, 760)
        self.setStyleSheet(_TREE_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        titulo = QLabel("Árbol Sintáctico Abstracto")
        titulo.setObjectName("titulo")
        layout.addWidget(titulo)

        # ── Controles colapsar/expandir ──────────────────────────────────────
        botones = QHBoxLayout()
        botones.setSpacing(6)
        btn_exp = QPushButton("Expandir todo")
        btn_col = QPushButton("Contraer todo")
        botones.addWidget(btn_exp)
        botones.addWidget(btn_col)
        if n_errores:
            estado = QLabel(f"⚠ {n_errores} error(es) sintáctico(s) — ver pestaña Errores")
            estado.setStyleSheet("color: #f38ba8; font-family: 'Segoe UI'; font-size: 12px;")
        else:
            estado = QLabel("✓ Sin errores sintácticos")
            estado.setStyleSheet("color: #a6e3a1; font-family: 'Segoe UI'; font-size: 12px;")
        botones.addWidget(estado)
        botones.addStretch()
        layout.addLayout(botones)

        # ── Árbol ─────────────────────────────────────────────────────────────
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setAnimated(True)
        self.tree.setIndentation(22)
        layout.addWidget(self.tree)

        btn_exp.clicked.connect(self.tree.expandAll)
        btn_col.clicked.connect(self.tree.collapseAll)

        if ast_root is not None:
            self._populate(ast_root, self.tree.invisibleRootItem())
        self.tree.expandAll()   # expandido automáticamente al abrir

    def _populate(self, node, parent_item):
        text = node.label()
        if node.line is not None:
            text += f"   (L{node.line}, C{node.col})"
        item = QTreeWidgetItem([text])
        parent_item.addChild(item)
        for child in node.children:
            self._populate(child, item)


class SyntaxTreePanel(QDockWidget):
    """Panel acoplable (lado derecho del IDE) que muestra el AST.

    Reemplaza la ventana independiente: el árbol vive dentro del IDE.
    Llamar `set_ast(ast_root, n_errores)` para poblarlo tras cada análisis.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Sin title bar nativo (estética consistente con el panel inferior).
        self.setTitleBarWidget(QWidget())
        self.setAllowedAreas(
            Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea
        )
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )

        root = QWidget()
        root.setStyleSheet(_TREE_STYLE)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        titulo = QLabel("Árbol Sintáctico Abstracto")
        titulo.setObjectName("titulo")
        layout.addWidget(titulo)

        # ── Controles colapsar/expandir + estado ──────────────────────────────
        botones = QHBoxLayout()
        botones.setSpacing(6)
        btn_exp = QPushButton("Expandir todo")
        btn_col = QPushButton("Contraer todo")
        botones.addWidget(btn_exp)
        botones.addWidget(btn_col)
        botones.addStretch()
        layout.addLayout(botones)

        self.estado = QLabel("")
        layout.addWidget(self.estado)

        # ── Árbol ─────────────────────────────────────────────────────────────
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setAnimated(True)
        self.tree.setIndentation(22)
        layout.addWidget(self.tree)

        btn_exp.clicked.connect(self.tree.expandAll)
        btn_col.clicked.connect(self.tree.collapseAll)

        self.setWidget(root)

    def set_ast(self, ast_root, n_errores=0):
        self.tree.clear()

        if n_errores:
            self.estado.setText(
                f"⚠ {n_errores} error(es) sintáctico(s) — ver pestaña Errores"
            )
            self.estado.setStyleSheet(
                "color: #f38ba8; font-family: 'Segoe UI'; font-size: 12px;"
            )
        else:
            self.estado.setText("✓ Sin errores sintácticos")
            self.estado.setStyleSheet(
                "color: #a6e3a1; font-family: 'Segoe UI'; font-size: 12px;"
            )

        if ast_root is not None:
            self._populate(ast_root, self.tree.invisibleRootItem())
        self.tree.expandAll()

    def _populate(self, node, parent_item):
        text = node.label()
        if node.line is not None:
            text += f"   (L{node.line}, C{node.col})"
        item = QTreeWidgetItem([text])
        parent_item.addChild(item)
        for child in node.children:
            self._populate(child, item)
