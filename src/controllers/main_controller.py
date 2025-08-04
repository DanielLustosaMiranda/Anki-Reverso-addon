from typing import List
from models.exemplo import Exemplo
from models.cards import Card
from services.exemple_manager import ExemploManager
from services.anki_deck_manager import AnkiDeckManager
from enums.languages import LANGUAGES  # Supondo que LANGUAGES é List[str] ou dict

class MainController:
    def __init__(self, data_dir: str):
        self.exemplo_manager = ExemploManager(data_dir)
        self.anki_manager = None  # Vai inicializar depois que escolher deck

    def listar_decks(self) -> List[str]:
        # Usa um deck temporário só pra listar decks no AnkiConnect
        temp_manager = AnkiDeckManager("TempDeck")
        return temp_manager.listar_decks()

    def get_languages(self) -> List[str]:
        # Supondo que LANGUAGES é um dicionário ou lista com códigos ou nomes
        return list(LANGUAGES.keys()) if isinstance(LANGUAGES, dict) else LANGUAGES

    def buscar_exemplos(self, palavra: str, source: str, target: str) -> List[Exemplo]:
        exemplos = self.exemplo_manager.buscar_exemplos(palavra, source, target)
        return exemplos

    def enviar_para_anki(self, exemplos: List[Exemplo], deck_name: str) -> bool:
        self.anki_manager = AnkiDeckManager(deck_name)
        cards = [Card(Front=ex.source, Back=ex.target) for ex in exemplos]
        return self.anki_manager.add_cards(cards)

    def apagar_sessao(self) -> None:
        self.exemplo_manager.apagar_sessao()
