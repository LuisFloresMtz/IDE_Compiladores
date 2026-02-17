from PySide6.QtWidgets import QFileDialog


def new_file(editor):
    editor.clear()
    return None


def open_file(parent, editor):
    file_path, _ = QFileDialog.getOpenFileName(
        parent, "Abrir archivo", "", "Archivos (*.txt *.py *.c);;Todos (*.*)"
    )

    if file_path:
        with open(file_path, "r", encoding="utf-8") as f:
            editor.setPlainText(f.read())
        return file_path

    return None


def save_file(file_path, editor):
    if file_path:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(editor.toPlainText())
        return file_path
    return None


def save_file_as(parent, editor):
    file_path, _ = QFileDialog.getSaveFileName(
        parent, "Guardar como", "", "Archivos (*.txt *.py *.c);;Todos (*.*)"
    )

    if file_path:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(editor.toPlainText())
        return file_path

    return None
