from PySide6.QtWidgets import QDockWidget, QTreeView, QFileSystemModel, QWidget
from PySide6.QtCore import Qt


class FileExplorer(QDockWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        empty = QWidget()
        empty.setFixedHeight(0)
        self.setTitleBarWidget(empty)

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

        self.tree.setStyleSheet("""
        QTreeView {
            background-color: #252526;
            color: #d4d4d4;
            border: none;
        }

        QTreeView::item:selected {
            background-color: #37373d;
        }

        QTreeView::item:hover {
            background-color: #2a2d2e;
        }

        QScrollBar:vertical {
            background: #1e1e1e;
            width: 10px;
        }

        QScrollBar::handle:vertical {
            background: #3c3c3c;
            border-radius: 5px;
        }
        """)

        self.setWidget(self.tree)