from PySide6.QtWidgets import QWidget, QHBoxLayout, QMenuBar, QToolBar
from PySide6.QtCore import Qt


# ── Paleta de colores centralizada ──────────────────────────────────────────
COLORS = {
    "bg_dark":      "#1e1e2e",   # fondo principal
    "bg_bar":       "#181825",   # fondo de barras
    "bg_hover":     "#313244",   # hover de ítems
    "bg_pressed":   "#45475a",   # click / activo
    "accent":       "#89b4fa",   # azul lavanda (acento)
    "accent_dim":   "#585b70",   # separador / borde
    "text":         "#cdd6f4",   # texto principal
    "text_dim":     "#a6adc8",   # texto secundario
    "border":       "#313244",   # bordes sutiles
}

MENUBAR_STYLE = f"""
QMenuBar {{
    background-color: {COLORS['bg_bar']};
    color: {COLORS['text']};
    font-family: 'Segoe UI', 'SF Pro Text', sans-serif;
    font-size: 13px;
    padding: 2px 4px;
    spacing: 2px;
    border: none;
}}

QMenuBar::item {{
    background: transparent;
    padding: 5px 12px;
    border-radius: 4px;
    color: {COLORS['text_dim']};
}}

QMenuBar::item:selected,
QMenuBar::item:hover {{
    background-color: {COLORS['bg_hover']};
    color: {COLORS['text']};
}}

QMenuBar::item:pressed {{
    background-color: {COLORS['bg_pressed']};
    color: {COLORS['accent']};
}}

QMenu {{
    background-color: {COLORS['bg_bar']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 4px 0px;
    font-size: 13px;
}}

QMenu::item {{
    padding: 6px 28px 6px 16px;
    border-radius: 4px;
    margin: 1px 4px;
}}

QMenu::item:selected {{
    background-color: {COLORS['bg_hover']};
    color: {COLORS['accent']};
}}

QMenu::separator {{
    height: 1px;
    background: {COLORS['accent_dim']};
    margin: 4px 8px;
}}

QMenu::indicator {{
    width: 14px;
    height: 14px;
    margin-left: 6px;
}}
"""

TOOLBAR_STYLE = f"""
QToolBar {{
    background-color: {COLORS['bg_bar']};
    border: none;
    padding: 3px 8px;
    spacing: 4px;
}}

QToolBar::separator {{
    width: 1px;
    background-color: {COLORS['accent_dim']};
    margin: 6px 6px;
}}

QToolButton {{
    background: transparent;
    color: {COLORS['text_dim']};
    border: none;
    border-radius: 5px;
    padding: 5px 7px;
    font-size: 13px;
}}

QToolButton:hover {{
    background-color: {COLORS['bg_hover']};
    color: {COLORS['text']};
}}

QToolButton:pressed {{
    background-color: {COLORS['bg_pressed']};
    color: {COLORS['accent']};
}}

QToolButton:checked {{
    background-color: {COLORS['bg_pressed']};
    color: {COLORS['accent']};
    border: 1px solid {COLORS['accent']};
}}
"""

TOP_WIDGET_STYLE = f"""
QWidget#topBar {{
    background-color: {COLORS['bg_bar']};
    border-bottom: 1px solid {COLORS['border']};
}}
"""


def create_top_bar(main_window):
    top_widget = QWidget()
    top_widget.setObjectName("topBar")
    top_widget.setStyleSheet(TOP_WIDGET_STYLE)
    top_widget.setFixedHeight(40)

    layout = QHBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    # MENU BAR
    menu_bar = QMenuBar()
    menu_bar.setStyleSheet(MENUBAR_STYLE)
    layout.addWidget(menu_bar)

    # TOOL BAR
    tool_bar = QToolBar()
    tool_bar.setMovable(False)
    tool_bar.setStyleSheet(TOOLBAR_STYLE)
    layout.addWidget(tool_bar)

    top_widget.setLayout(layout)
    main_window.setMenuWidget(top_widget)

    return menu_bar, tool_bar