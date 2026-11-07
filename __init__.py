import re
from typing import Any, List, Optional
from .utils.qt_compat import QAction, QKeySequence, is_running_in_anki, mw

_active_dialog: Optional[Any] = None


def open_reverso_dialog(initial_query: str = "") -> None:
    """Abre (ou traz para frente) a janela principal do Add-on dentro do Anki."""
    global _active_dialog
    from .views.main_dialog import ReversoMainDialog

    if _active_dialog is not None:
        _active_dialog.refresh_decks()
        if initial_query:
            _active_dialog.search_input.setText(initial_query)
            _active_dialog.on_search_reverso()
        _active_dialog.show()
        _active_dialog.raise_()
        _active_dialog.activateWindow()
        return

    _active_dialog = ReversoMainDialog(parent=mw, initial_query=initial_query)
    _active_dialog.show()


def open_addon_settings() -> None:
    """Abre a janela de configurações quando o usuário clica em 'Config' em Ferramentas -> Add-ons."""
    global _active_dialog
    from .controllers.main_controller import MainController
    from .views.settings_dialog import SettingsDialog

    if _active_dialog is not None:
        dlg = SettingsDialog(_active_dialog.controller, parent=_active_dialog)
    else:
        dlg = SettingsDialog(MainController(), parent=mw)
    dlg.exec()


def _on_editor_button_clicked(editor: Any) -> None:
    selected_text = ""
    try:
        if editor and editor.web:
            selected_text = editor.web.selectedText().strip()
        if not selected_text and editor and editor.note and editor.currentField is not None:
            raw_field = editor.note.fields[editor.currentField]
            selected_text = re.sub(r"<[^>]+>", "", raw_field).strip()
    except Exception:
        selected_text = ""

    open_reverso_dialog(initial_query=selected_text)


def _setup_editor_button(buttons: List[str], editor: Any) -> None:
    btn = editor.addButton(
        icon=None,
        cmd="reverso_ai_lookup",
        func=lambda ed=editor: _on_editor_button_clicked(ed),
        tip="Abrir Reverso & AI Lookup (Ctrl+Shift+R)",
        label="Reverso AI",
    )
    buttons.append(btn)


def init_anki_addon() -> None:
    if mw is None:
        return

    # 1. Item no menu Ferramentas (Tools)
    shortcut = "Ctrl+Shift+R"
    try:
        cfg = mw.addonManager.getConfig(__name__) or {}
        shortcut = cfg.get("shortcut") or shortcut
    except Exception:
        pass

    action = QAction("Reverso Context && AI Lookup...", mw)
    action.setShortcut(QKeySequence(shortcut))
    action.triggered.connect(lambda: open_reverso_dialog())
    mw.form.menuTools.addAction(action)

    # 2. Botão de configuração na tela de Add-ons do Anki
    try:
        mw.addonManager.setConfigAction(__name__, open_addon_settings)
    except Exception:
        pass

    # 3. Botão na barra do Editor de Cards do Anki
    try:
        from aqt import gui_hooks  # type: ignore

        gui_hooks.editor_did_init_buttons.append(_setup_editor_button)
    except Exception:
        pass


if is_running_in_anki() or mw is not None:
    init_anki_addon()
