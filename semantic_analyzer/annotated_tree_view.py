"""Panel del Árbol con Anotaciones Semánticas.

Muestra la copia anotada del AST en un QTreeWidget con columnas: la primera
es el mismo nodo del AST original y las demás son los atributos que agregó
el análisis semántico (tipo, valor, conversión / error). Así se puede
comparar directamente contra el panel del AST original.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QLabel, QPushButton, QDockWidget, QHeaderView,
)
from PySide6.QtGui import QColor, QBrush
from PySide6.QtCore import Qt

from symbol_table.symbol_table import formatear_valor
from semantic_analyzer.semantic import SINTETIZADO, HEREDADO

try:
    from ui.top_bar import COLORS
except ImportError:
    COLORS = {
        "bg_dark": "#1e1e2e", "bg_bar": "#181825", "bg_hover": "#313244",
        "bg_pressed": "#45475a", "accent": "#89b4fa", "accent_dim": "#585b70",
        "text": "#cdd6f4", "text_dim": "#a6adc8", "border": "#313244",
    }

_ERROR_COLOR = QColor("#f38ba8")    # errores
_TIPO_COLOR = QColor("#a6e3a1")     # atributo de tipo
_VALOR_COLOR = QColor("#f9e2af")    # atributo de valor
_CONV_COLOR = QColor("#cba6f7")     # conversiones

_STYLE = f"""
QWidget {{ background: {COLORS['bg_dark']}; }}
QLabel#titulo {{
    color: {COLORS['accent']};
    font-family: 'Segoe UI', sans-serif;
    font-size: 15px; font-weight: 600; padding: 4px 2px;
}}
QLabel#leyenda {{
    color: {COLORS['text_dim']};
    font-family: 'Segoe UI', sans-serif;
    font-size: 11px;
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
QTreeWidget::item:selected {{ background: {COLORS['bg_pressed']}; }}
QHeaderView::section {{
    background: {COLORS['bg_dark']};
    color: {COLORS['text_dim']};
    border: none;
    border-bottom: 1px solid {COLORS['border']};
    padding: 4px 6px;
    font-family: 'Segoe UI', sans-serif;
    font-size: 12px;
}}
QPushButton {{
    background: {COLORS['bg_hover']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 4px 10px;
    font-family: 'Segoe UI', sans-serif;
    font-size: 12px;
}}
QPushButton:hover {{ background: {COLORS['bg_pressed']}; }}
QScrollBar:vertical {{ background: {COLORS['bg_bar']}; width: 8px; }}
QScrollBar::handle:vertical {{ background: {COLORS['accent_dim']}; border-radius: 4px; min-height: 24px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{ background: {COLORS['bg_bar']}; height: 8px; }}
QScrollBar::handle:horizontal {{ background: {COLORS['accent_dim']}; border-radius: 4px; min-width: 24px; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
"""

_FLECHAS = {SINTETIZADO: '↑', HEREDADO: '↓'}


class AnnotatedTreePanel(QDockWidget):
    """Panel acoplable con el AST anotado. Llamar `set_arbol(raiz, errores)`."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AST anotado")
        self.setTitleBarWidget(QWidget())
        self.setAllowedAreas(
            Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea
        )
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )

        root = QWidget()
        root.setStyleSheet(_STYLE)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        titulo = QLabel("Árbol con Anotaciones Semánticas")
        titulo.setObjectName("titulo")
        layout.addWidget(titulo)

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

        leyenda = QLabel("↑ atributo sintetizado (sube de los hijos)   "
                         "↓ atributo heredado (baja de la declaración)")
        leyenda.setObjectName("leyenda")
        layout.addWidget(leyenda)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(4)
        self.tree.setHeaderLabels(["Nodo", "Tipo", "Valor", "Conversión / Error"])
        self.tree.setAnimated(True)
        self.tree.setIndentation(22)
        header = self.tree.header()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.tree)

        btn_exp.clicked.connect(self.tree.expandAll)
        btn_col.clicked.connect(self.tree.collapseAll)

        self.setWidget(root)

    def set_arbol(self, raiz, errores=None):
        """raiz: NodoSem; errores: lista de (mensaje, linea, columna) semánticos."""
        self.tree.clear()
        n = len(errores or [])
        if n:
            self.estado.setText(f"⚠ {n} error(es) semántico(s)")
            self.estado.setStyleSheet(
                "color: #f38ba8; font-family: 'Segoe UI'; font-size: 12px;")
        else:
            self.estado.setText("✓ Sin errores semánticos")
            self.estado.setStyleSheet(
                "color: #a6e3a1; font-family: 'Segoe UI'; font-size: 12px;")
        if raiz is not None:
            self._populate(raiz, self.tree.invisibleRootItem())
        self.tree.expandAll()

    def _populate(self, node, parent_item):
        if node is None:
            return
        if node.type == 'error':
            nodo_txt = f"✗ error: {node.value}"
        else:
            nodo_txt = node.label()
        if node.line is not None:
            nodo_txt += f"   (L{node.line}, C{node.col})"

        tipo_txt = ''
        if node.dtype is not None:
            flecha = _FLECHAS.get(node.origen, '')
            tipo_txt = f"{node.dtype} {flecha}".strip()
        valor_txt = formatear_valor(node.val)
        notas = []
        if node.conv:
            notas.append(node.conv)
        notas += [f"✗ {e}" for e in node.errores]

        item = QTreeWidgetItem([nodo_txt, tipo_txt, valor_txt, '   '.join(notas)])
        item.setForeground(1, QBrush(_TIPO_COLOR))
        item.setForeground(2, QBrush(_VALOR_COLOR))
        item.setForeground(3, QBrush(_CONV_COLOR))
        if node.errores or node.type == 'error':
            item.setForeground(0, QBrush(_ERROR_COLOR))
            item.setForeground(3, QBrush(_ERROR_COLOR))
        if node.dtype == 'error':
            item.setForeground(1, QBrush(_ERROR_COLOR))
        if notas:
            item.setToolTip(3, '\n'.join(notas))
        parent_item.addChild(item)
        for child in node.children:
            self._populate(child, item)
