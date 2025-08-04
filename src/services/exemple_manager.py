# src/models/exemplo_manager.py
import os
import json
import csv
from typing import List
from models.exemplo import Exemplo
from services.reverso_scraper import ReversoScraper

class ExemploManager:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir

    def buscar_exemplos(self, palavra: str, source: str, target: str) -> List[Exemplo]:
        scraper = ReversoScraper()
        data = scraper.get_context(text=palavra, source_lang=source, target_lang=target)

        if not data or 'examples' not in data:
            return []

        self.salvar_exemplos(data)
        self.exemplos = self.carregar_exemplos()
        return self.exemplos

    def salvar_exemplos(self, data: dict) -> None:
        output_path = os.path.join(self.data_dir, 'output.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Erro ao ler output.json: {e}")
            return

        translations = data.get('translations', [])
        examples = data.get('examples', [])

        with open(os.path.join(self.data_dir, 'translation.json'), 'w', encoding='utf-8') as f:
            json.dump(translations, f, ensure_ascii=False, indent=2)
        with open(os.path.join(self.data_dir, 'examples.json'), 'w', encoding='utf-8') as f:
            json.dump(examples, f, ensure_ascii=False, indent=2)

    def carregar_exemplos(self) -> List[Exemplo]:
        path = os.path.join(self.data_dir, 'examples.json')
        with open(path, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        return [Exemplo(**ex) for ex in dados]

    def filtrar_por_ids(self, exemplos: List[Exemplo], ids: List[int]) -> List[Exemplo]:
        return [ex for ex in exemplos if ex.id in ids]

    def salvar_csv(self, exemplos_filtrados: List[Exemplo]) -> None:
        path = os.path.join(self.data_dir, 'exemplos_filtrados.csv')
        with open(path, 'a', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            writer.writerows([(ex.source, ex.target) for ex in exemplos_filtrados])

    def apagar_sessao(self) -> None:
        for nome_arquivo in os.listdir(self.data_dir):
            caminho_arquivo = os.path.join(self.data_dir, nome_arquivo)
            if os.path.isfile(caminho_arquivo):
                os.remove(caminho_arquivo)
