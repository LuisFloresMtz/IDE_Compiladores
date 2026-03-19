from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTabBar, QToolButton
from PySide6.QtCore import Qt
from editor.code_editor import CodeEditor


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


TABBAR_STYLE = f"""
QTabBar {{
    background: {COLORS['bg_bar']};
    border-bottom: 1px solid {COLORS['border']};
}}

QTabBar::tab {{
    background: {COLORS['bg_bar']};
    color: {COLORS['text_dim']};
    font-family: 'Segoe UI', 'SF Pro Text', sans-serif;
    font-size: 13px;
    padding: 7px 8px 7px 14px;
    border: none;
    border-right: 1px solid {COLORS['border']};
    border-bottom: 2px solid transparent;
    min-width: 100px;
    max-width: 220px;
}}

QTabBar::tab:selected {{
    background: {COLORS['bg_dark']};
    color: {COLORS['text']};
    border-bottom: 2px solid {COLORS['accent']};
}}

QTabBar::tab:hover:!selected {{
    background: {COLORS['bg_hover']};
    color: {COLORS['text']};
}}

"""

CLOSE_BTN_STYLE = f"""
QToolButton {{
    background: transparent;
    color: {COLORS['text_dim']};
    border: none;
    border-radius: 3px;
    font-size: 16px;
    padding: 0px 0px 2px 0px;
}}
QToolButton:hover {{
    background: {COLORS['bg_pressed']};
    color: {COLORS['text']};
}}
"""

EDITOR_CONTAINER_STYLE = f"""
QWidget#editorContainer {{
    background: {COLORS['bg_dark']};
    border: none;
}}
"""


class TabEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("editorContainer")
        self.setStyleSheet(EDITOR_CONTAINER_STYLE)

        self.editors: list[CodeEditor] = []

        # ── Tab bar ───────────────────────────────────────────────────────────
        self.tabs = QTabBar()
        self.tabs.setMovable(True)
        self.tabs.setTabsClosable(False)
        self.tabs.setExpanding(False)           # tabs con ancho fijo, no se estiran
        self.tabs.setDrawBase(False)            # sin línea extra debajo del tabbar
        self.tabs.setStyleSheet(TABBAR_STYLE)

        # ── Layouts ───────────────────────────────────────────────────────────
        self.editor_layout = QVBoxLayout()
        self.editor_layout.setContentsMargins(0, 0, 0, 0)
        self.editor_layout.setSpacing(0)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.tabs)
        main_layout.addLayout(self.editor_layout)

        # ── Señales ───────────────────────────────────────────────────────────
        self.tabs.currentChanged.connect(self.change_tab)
        self.tabs.tabCloseRequested.connect(self.close_tab)

        # ── Tab inicial ───────────────────────────────────────────────────────
        self.add_tab("Nuevo.txt")

    # ── API pública ───────────────────────────────────────────────────────────

    def _make_close_btn(self) -> QWidget:
        btn = QToolButton()
        btn.setText("×")
        btn.setFixedSize(20, 20)
        btn.setStyleSheet(CLOSE_BTN_STYLE)

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 6, 0)
        layout.setSpacing(0)
        layout.addWidget(btn)
        container.setFixedSize(26, 20)

        btn.clicked.connect(lambda checked=False, c=container: self._close_tab_by_button(c))
        return container

    def _close_tab_by_button(self, container: QWidget):
        for i in range(self.tabs.count()):
            if self.tabs.tabButton(i, QTabBar.ButtonPosition.RightSide) is container:
                self.close_tab(i)
                break

    def add_tab(self, filename: str):
        editor = CodeEditor()
        self.editors.append(editor)

        index = self.tabs.addTab(filename)
        self.tabs.setTabButton(index, QTabBar.ButtonPosition.RightSide, self._make_close_btn())
        self.tabs.setCurrentIndex(index)

        self.editor_layout.addWidget(editor)
        editor.show()

    def change_tab(self, index: int):
        for i, editor in enumerate(self.editors):
            editor.setVisible(i == index)

    def close_tab(self, index: int):
        if len(self.editors) == 1:
            # No cerrar la última pestaña — limpiar en su lugar
            self.editors[0].clear()
            self.tabs.setTabText(0, "Nuevo.txt")
            return

        editor = self.editors.pop(index)
        editor.deleteLater()
        self.tabs.removeTab(index)

    def current_editor(self) -> CodeEditor | None:
        index = self.tabs.currentIndex()
        if 0 <= index < len(self.editors):
            return self.editors[index]
        return None

    def set_tab_title(self, title: str, index: int | None = None):
        """Actualiza el título de la pestaña actual o de la indicada."""
        idx = index if index is not None else self.tabs.currentIndex()
        if 0 <= idx < self.tabs.count():
            self.tabs.setTabText(idx, title)