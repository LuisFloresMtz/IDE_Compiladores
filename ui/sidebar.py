from PySide6.QtWidgets import QDockWidget, QTreeView, QFileSystemModel, QWidget
from PySide6.QtCore import Qt


class FileExplorer(QDockWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Quitar barra superior completamente (sin espacio)
        empty = QWidget()
        empty.setFixedHeight(0)
        self.setTitleBarWidget(empty)

        # No movible, no flotante, no cerrable
        self.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.setAllowedAreas(Qt.LeftDockWidgetArea)

        self.tree = QTreeView()
        self.model = QFileSystemModel()

        self.model.setRootPath(".")
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index("."))

        self.tree.setHeaderHidden(True)
        self.tree.setColumnHidden(1, True)
        self.tree.setColumnHidden(2, True)
        self.tree.setColumnHidden(3, True)

        self.setWidget(self.tree)
        self.tree.setStyleSheet("QTreeView { border: none; }")


    def set_directory(self, path):
        self.tree.setRootIndex(self.model.index(path))
