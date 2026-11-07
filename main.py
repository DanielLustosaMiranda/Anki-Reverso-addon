import importlib
import os
import sys

# Permite importar o diretório atual como um pacote Python quando executado em modo standalone
PARENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PACKAGE_NAME = os.path.basename(os.path.abspath(os.path.dirname(__file__)))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)


def main() -> None:
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    main_dialog_mod = importlib.import_module(f"{PACKAGE_NAME}.views.main_dialog")
    dialog = main_dialog_mod.ReversoMainDialog()
    dialog.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
