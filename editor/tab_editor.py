from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabBar
from PySide6.QtCore import Qt
from editor.code_editor import CodeEditor

class TabEditor(QWidget):
    def __init__(self):
        super().__init__()

        self.tabs = QTabBar()
        self.editors = []   # 👈 lista de CodeEditor

        self.tabs.setMovable(True)
        self.tabs.setTabsClosable(True)

        self.editor_layout = QVBoxLayout()
        self.editor_layout.setContentsMargins(0, 0, 0, 0)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.tabs)
        main_layout.addLayout(self.editor_layout)

        self.add_tab("Nuevo.txt")

        self.tabs.currentChanged.connect(self.change_tab)
        self.tabs.tabCloseRequested.connect(self.close_tab)

    def add_tab(self, filename):
        editor = CodeEditor()
        self.editors.append(editor)

        index = self.tabs.addTab(filename)
        self.tabs.setCurrentIndex(index)

        self.editor_layout.addWidget(editor)
        editor.show()

    def change_tab(self, index):
        for i, editor in enumerate(self.editors):
            editor.setVisible(i == index)

    def close_tab(self, index):
        editor = self.editors.pop(index)
        editor.deleteLater()
        self.tabs.removeTab(index)

    # ✅ ESTE ES EL PASO CLAVE
    def current_editor(self):
        index = self.tabs.currentIndex()
        if index >= 0:
            return self.editors[index]
        return None