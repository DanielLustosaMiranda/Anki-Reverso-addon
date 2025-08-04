import requests
from typing import List, TypedDict, Optional
from models.cards import Card

class AnkiDeckManager:
    def __init__(self, deck_name: str) -> None:
        self.deck_name: str = deck_name
        self.anki_connect_url: str = "http://localhost:8765"

    def add_cards(self, cards: List[Card]) -> bool:
        for card in cards:
            payload = {
                "action": "addNote",
                "version": 6,
                "params": {
                    "note": {
                        "deckName": self.deck_name,
                        "modelName": "Basic",
                        "fields": {
                            "Front": card['Front'],
                            "Back": card['Back']
                        },
                        "tags": ["automated-import", self.deck_name.replace(" ", "-")]
                    }
                }
            }
            try:
                response = requests.post(self.anki_connect_url, json=payload).json()
                if response.get('error'):
                    print(f"Erro Anki: {response['error']}")
                else:
                    print(f"Card adicionado: {card['Front'][:30]}...")
            except requests.exceptions.RequestException:
                print("Erro: não conseguiu conectar no AnkiConnect.")
                return False
        return True

    def listar_decks(self) -> List[str]:
        try:
            import urllib.request, json
            req = {
                "action": "deckNames",
                "version": 6
            }
            data = json.dumps(req).encode("utf-8")
            response = urllib.request.urlopen(
                urllib.request.Request(self.anki_connect_url, data=data)
            )
            decks = json.load(response)["result"]
            return decks
        except Exception as e:
            print("Erro ao listar decks:", e)
            return []
