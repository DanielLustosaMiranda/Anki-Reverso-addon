import sys
from PyQt6.QtWidgets import QApplication
from views.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Passe o caminho onde vai salvar os dados temporários
    window = MainWindow(data_dir="./data")
    window.show()
    sys.exit(app.exec())
