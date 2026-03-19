from PySide6.QtWidgets import QToolBar
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon


# Tamaño de iconos uniforme
ICON_SIZE = QSize(18, 18)

# Tooltips descriptivos para cada acción
ACTION_TOOLTIPS = {
    "action_new":    "Nuevo archivo  (Ctrl+N)",
    "action_open":   "Abrir archivo  (Ctrl+O)",
    "action_save":   "Guardar        (Ctrl+S)",
    "action_lexico": "Análisis Léxico (F9)",
    "action_run":    "Ejecutar       (F10)",
}

# Iconos de tema del sistema — reemplaza con rutas a .png si los tienes
ACTION_ICONS = {
    "action_new":    "document-new",
    "action_open":   "document-open",
    "action_save":   "document-save",
    "action_lexico": "system-run",
    "action_run":    "media-playback-start",
}


def create_toolbar(main_window, tool_bar: QToolBar) -> QToolBar:
    """
    Configura iconos, tooltips y acciones en el QToolBar recibido.
    El estilo visual ya fue aplicado en top_bar.py (TOOLBAR_STYLE).
    """
    tool_bar.setMovable(False)
    tool_bar.setIconSize(ICON_SIZE)
    tool_bar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)

    # ── Asignar iconos y tooltips ────────────────────────────────────────────
    for attr, theme_name in ACTION_ICONS.items():
        action = getattr(main_window, attr, None)
        if action is None:
            continue
        action.setIcon(QIcon.fromTheme(theme_name))
        action.setToolTip(ACTION_TOOLTIPS.get(attr, ""))

    # ── Grupo 1: Archivo ─────────────────────────────────────────────────────
    tool_bar.addAction(main_window.action_new)
    tool_bar.addAction(main_window.action_open)
    tool_bar.addAction(main_window.action_save)

    # ── Separador visual ─────────────────────────────────────────────────────
    tool_bar.addSeparator()

    # ── Grupo 2: Compilar / Ejecutar ─────────────────────────────────────────
    tool_bar.addAction(main_window.action_lexico)
    tool_bar.addAction(main_window.action_run)

    return tool_bar