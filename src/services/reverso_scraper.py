import os
from typing import Dict, Optional
from utils.run_cmd import run_cmd

class ReversoScraper:
    def __init__(self):
        current_dir = os.path.dirname(__file__)
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
        self.scraper_script_path = os.path.join(project_root, 'reverso_scraper', 'get_data.js')
        if not os.path.isfile(self.scraper_script_path):
            raise FileNotFoundError(f"Script do scraper não encontrado em: {self.scraper_script_path}")

    def _run(self, mode: str, text: str, source_lang: str, target_lang: str) -> Optional[Dict]:
        command = ['node', self.scraper_script_path, mode, text, source_lang, target_lang]
        print(f"Executando comando: {' '.join(command)}")
        return run_cmd(command)

    def get_context(self, text: str, source_lang: str, target_lang: str) -> Optional[Dict]:
        return self._run('context', text, source_lang, target_lang)

    def get_translation(self, text: str, source_lang: str, target_lang: str) -> Optional[Dict]:
        return self._run('translation', text, source_lang, target_lang)

    def get_synonyms(self, text: str, source_lang: str, target_lang: str) -> Optional[Dict]:
        return self._run('synonyms', text, source_lang, target_lang)

    def get_spell(self, text: str, source_lang: str, target_lang: str) -> Optional[Dict]:
        return self._run('spell', text, source_lang, target_lang)

    def get_conjugation(self, text: str, source_lang: str, target_lang: str) -> Optional[Dict]:
        return self._run('conjugation', text, source_lang, target_lang)
