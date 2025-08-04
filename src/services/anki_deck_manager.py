import requests

class AnkiDeckManager:
    def __init__(self, deck_name):
        self.deck_name = deck_name
        self.anki_connect_url = "http://localhost:8765"

    def add_cards(self, cards):
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
