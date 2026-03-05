from PySide6.QtWidgets import QDockWidget, QTreeView, QFileSystemModel, QWidget, QLabel, QHBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


# ── Importar paleta desde top_bar (o redefinir aquí si el módulo no está disponible)
try:
    from top_bar import COLORS
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


EXPLORER_STYLE = f"""
/* ── Panel contenedor ─────────────────────────────────────────────────────── */
QDockWidget {{
    background-color: {COLORS['bg_bar']};
    border: none;
}}

/* ── Árbol ────────────────────────────────────────────────────────────────── */
QTreeView {{
    background-color: {COLORS['bg_bar']};
    color: {COLORS['text_dim']};
    border: none;
    font-family: 'Segoe UI', 'SF Pro Text', sans-serif;
    font-size: 13px;
    padding-top: 4px;
    outline: 0;
}}

QTreeView::item {{
    padding: 3px 6px;
    border-radius: 4px;
    margin: 1px 4px;
}}

QTreeView::item:hover {{
    background-color: {COLORS['bg_hover']};
    color: {COLORS['text']};
}}

QTreeView::item:selected {{
    background-color: {COLORS['bg_pressed']};
    color: {COLORS['accent']};
    border-left: 2px solid {COLORS['accent']};
}}

QTreeView::item:selected:hover {{
    background-color: {COLORS['bg_pressed']};
    color: {COLORS['accent']};
}}

QTreeView::branch {{
    background: transparent;
}}

QTreeView::branch:has-children:!has-siblings:closed,
QTreeView::branch:closed:has-children:has-siblings {{
    image: none;
    border: none;
}}

QTreeView::branch:open:has-children:!has-siblings,
QTreeView::branch:open:has-children:has-siblings {{
    image: none;
    border: none;
}}

/* ── Scrollbar vertical ───────────────────────────────────────────────────── */
QScrollBar:vertical {{
    background: {COLORS['bg_bar']};
    width: 8px;
    margin: 0;
    border-radius: 4px;
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
    background: none;
}}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {{
    background: none;
}}

/* ── Scrollbar horizontal ─────────────────────────────────────────────────── */
QScrollBar:horizontal {{
    background: {COLORS['bg_bar']};
    height: 8px;
    margin: 0;
    border-radius: 4px;
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
    background: none;
}}
"""

class FileExplorer(QDockWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # ── Barra de título personalizada ────────────────────────────────────
        title_bar = QWidget()
        title_bar.setFixedHeight(28)
        title_bar.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['bg_bar']};
                border-bottom: 1px solid {COLORS['border']};
            }}
        """)

        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 8, 0)
        title_layout.setSpacing(0)

        title_label = QLabel("EXPLORADOR")
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_dim']};
                background: transparent;
                font-family: 'Segoe UI', sans-serif;
                font-size: 11px;
                letter-spacing: 1px;
                font-weight: 600;
                border: none;
                padding: 0;
            }}
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        self.setTitleBarWidget(title_bar)

        # ── Configuración del dock ───────────────────────────────────────────
        self.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea)

        # ── Árbol de archivos ────────────────────────────────────────────────
        self.tree = QTreeView()
        self.model = QFileSystemModel()

        self.model.setRootPath(".")
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index("."))

        self.tree.setHeaderHidden(True)
        self.tree.setColumnHidden(1, True)
        self.tree.setColumnHidden(2, True)
        self.tree.setColumnHidden(3, True)

        self.tree.setAnimated(True)
        self.tree.setIndentation(16)
        self.tree.setUniformRowHeights(True)
        self.tree.setExpandsOnDoubleClick(True)

        self.tree.setStyleSheet(EXPLORER_STYLE)
        self.setWidget(self.tree)