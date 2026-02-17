from PySide6.QtWidgets import QDockWidget, QTreeView
from PySide6.QtGui import QFileSystemModel
from PySide6.QtCore import Qt


class FileExplorer(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Explorador", parent)

        self.tree = QTreeView()
        self.model = QFileSystemModel()

        # Cargar desde carpeta raíz del proyecto
        self.model.setRootPath(".")

        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index("."))

        # Ocultar columnas innecesarias (tamaño, tipo, fecha)
        self.tree.setColumnHidden(1, True)
        self.tree.setColumnHidden(2, True)
        self.tree.setColumnHidden(3, True)

        self.tree.setHeaderHidden(True)

        self.setWidget(self.tree)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

    def set_directory(self, path):
        self.tree.setRootIndex(self.model.index(path))
