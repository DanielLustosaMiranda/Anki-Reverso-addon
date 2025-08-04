from typing import List
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QListWidget,
    QListWidgetItem, QCheckBox
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from models.exemplo import Exemplo
from controllers.main_controller import MainController

class MainWindow(QMainWindow):
    def __init__(self, data_dir: str):
        super().__init__()
        self.setWindowTitle("Anki-Reverso Addon")

        self.controller = MainController(data_dir)

        # Layout base
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout()
        central.setLayout(main_layout)

        # Deck selection
        deck_layout = QHBoxLayout()
        deck_layout.addWidget(QLabel("Deck:"))
        self.deck_combo = QComboBox()
        deck_layout.addWidget(self.deck_combo)
        main_layout.addLayout(deck_layout)

        # Language selection
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("From:"))
        self.source_lang_combo = QComboBox()
        lang_layout.addWidget(self.source_lang_combo)
        lang_layout.addWidget(QLabel("To:"))
        self.target_lang_combo = QComboBox()
        lang_layout.addWidget(self.target_lang_combo)
        main_layout.addLayout(lang_layout)

        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Digite a palavra para buscar...")
        self.search_button = QPushButton("Buscar")
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        main_layout.addLayout(search_layout)

        # List widget para exemplos
        self.examples_list = QListWidget()
        main_layout.addWidget(self.examples_list)

        # Botões ação
        buttons_layout = QHBoxLayout()
        self.clear_button = QPushButton("Apagar Sessão")
        self.send_button = QPushButton("Enviar para Anki")
        buttons_layout.addWidget(self.clear_button)
        buttons_layout.addWidget(self.send_button)
        main_layout.addLayout(buttons_layout)

        # Conectar sinais
        self.search_button.clicked.connect(self.on_search)
        self.send_button.clicked.connect(self.on_send)
        self.clear_button.clicked.connect(self.on_clear_session)

        # Popula combos
        self.populate_decks()
        self.populate_languages()

    def populate_decks(self) -> None:
        decks = self.controller.listar_decks()
        self.deck_combo.clear()
        self.deck_combo.addItems(decks)

    def populate_languages(self) -> None:
        langs = self.controller.get_languages()
        self.source_lang_combo.clear()
        self.target_lang_combo.clear()
        self.source_lang_combo.addItems(langs)
        self.target_lang_combo.addItems(langs)

    def on_search(self) -> None:
        palavra = self.search_input.text().strip()
        if not palavra:
            return
        source = self.source_lang_combo.currentText()
        target = self.target_lang_combo.currentText()
        exemplos = self.controller.buscar_exemplos(palavra, source, target)
        self.populate_examples(exemplos)

    def populate_examples(self, exemplos: List[Exemplo]) -> None:
        self.examples_list.clear()
        for ex in exemplos:
            widget = QWidget()
            layout = QHBoxLayout()
            layout.setContentsMargins(2, 2, 2, 2)
            layout.setSpacing(5)

            checkbox = QCheckBox()
            layout.addWidget(checkbox)

            text_layout = QVBoxLayout()

            label_source = QLabel(ex.source)
            label_source.setStyleSheet("font-weight: bold; font-size: 14pt;") 
            label_source.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            label_source.setWordWrap(True)

            label_target = QLabel(ex.target)
            label_target.setStyleSheet("color: gray; font-style: italic; font-size: 13pt;")
            label_target.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            label_target.setWordWrap(True)

            text_layout.addWidget(label_source)
            text_layout.addWidget(label_target)

            layout.addLayout(text_layout)
            
            # --- LINHA ADICIONADA ---
            layout.addStretch(1)
            # ------------------------

            widget.setLayout(layout)

            item = QListWidgetItem(self.examples_list)
            item.setSizeHint(widget.sizeHint())
            item.setData(Qt.ItemDataRole.UserRole, (ex, checkbox))
            self.examples_list.addItem(item)
            self.examples_list.setItemWidget(item, widget)

    def on_send(self) -> None:
        selecionados = []
        for i in range(self.examples_list.count()):
            item = self.examples_list.item(i)
            if item is None:
                continue  # evita erro se for None, mesmo que improvável
            widget = self.examples_list.itemWidget(item)
            if widget is None:
                continue
            checkbox = widget.findChild(QCheckBox)
            if checkbox is not None and checkbox.isChecked():
                ex, _ = item.data(Qt.ItemDataRole.UserRole)
                selecionados.append(ex)

        if not selecionados:
            print("Nenhum exemplo selecionado para enviar.")
            return

        deck = self.deck_combo.currentText()
        sucesso = self.controller.enviar_para_anki(selecionados, deck)
        if sucesso:
            print(f"{len(selecionados)} exemplos enviados para o deck '{deck}'")
        else:
            print("Falha ao enviar para o Anki.")

    def on_clear_session(self) -> None:
        self.controller.apagar_sessao()
        self.examples_list.clear()
        print("Sessão apagada, arquivos removidos.")
