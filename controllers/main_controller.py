from typing import Dict, List, Tuple
from ..enums.languages import LANGUAGE_INFO, LANGUAGES
from ..models.example import ExampleItem, LookupResult, WebImageResult
from ..models.note_config import NoteExportConfig
from ..services.ai_service import AIService
from ..services.anki_service import AnkiService
from ..services.config_service import ConfigService
from ..services.image_service import ImageService
from ..services.reverso_service import ReversoService
from ..services.tts_service import TTSService


class MainController:
    """Orquestrador principal entre a interface gráfica e os serviços de Reverso, IA, TTS, Imagens e Anki."""

    def __init__(self) -> None:
        self.config = ConfigService()
        self.reverso = ReversoService()
        self.ai = AIService(self.config)
        self.tts = TTSService(self.config)
        self.images = ImageService(self.config)
        self.anki = AnkiService()

    def get_languages(self) -> List[Tuple[str, str]]:
        """Retorna lista de tuplas (codigo_idioma, rotulo_exibicao)."""
        return [(code, LANGUAGE_INFO[code]["label"]) for code in LANGUAGES]

    def listar_decks(self) -> List[str]:
        decks = self.anki.listar_decks()
        return decks if decks else ["Default"]

    def listar_note_types(self) -> List[str]:
        return self.anki.listar_note_types()

    def listar_campos_note_type(self, model_name: str) -> List[str]:
        return self.anki.listar_campos_note_type(model_name)

    def buscar_reverso(self, palavra: str, source_lang: str, target_lang: str) -> LookupResult:
        return self.reverso.get_context(palavra, source_lang, target_lang)

    def gerar_exemplos_ia(
        self,
        palavra: str,
        source_lang: str,
        target_lang: str,
        level: str,
        style: str,
        count: int = 5,
    ) -> LookupResult:
        return self.ai.generate_examples(
            query=palavra,
            source_lang=source_lang,
            target_lang=target_lang,
            level=level,
            style=style,
            count=count,
        )

    def explicar_exemplo_ia(
        self,
        palavra: str,
        example: ExampleItem,
        source_lang: str,
        target_lang: str,
    ) -> str:
        explanation = self.ai.explain_example(
            query=palavra,
            sentence_source=example.source,
            sentence_target=example.target,
            source_lang=source_lang,
            target_lang=target_lang,
        )
        example.explanation = explanation
        return explanation

    def gerar_audio_exemplo(self, example: ExampleItem, source_lang: str) -> Tuple[bytes, str]:
        """Gera (ou recupera do cache) os bytes de áudio para o exemplo."""
        if example.audio_bytes and example.audio_filename:
            return example.audio_bytes, example.audio_filename

        audio_bytes, filename = self.tts.synthesize(example.source, source_lang)
        example.audio_bytes = audio_bytes
        example.audio_filename = filename
        return audio_bytes, filename

    def buscar_imagens_web(self, termo: str, limit: int = 6) -> List[WebImageResult]:
        return self.images.search_web_images(termo, limit=limit)

    def gerar_imagem_ia(self, prompt: str) -> Tuple[bytes, str]:
        return self.images.generate_ai_image(prompt)

    def carregar_imagem_arquivo(self, file_path: str) -> Tuple[bytes, str]:
        return self.images.load_from_file(file_path)

    def enviar_para_anki(
        self,
        exemplos: List[ExampleItem],
        source_lang: str,
        export_config: NoteExportConfig,
        query: str = "",
    ) -> Tuple[int, List[str]]:
        """
        Gera o áudio (se habilitado), salva áudios e imagens na pasta collection.media do Anki
        e cria os flashcards no deck selecionado.
        Retorna (quantidade_criada, lista_de_avisos).
        """
        warnings: List[str] = []

        for ex in exemplos:
            if export_config.include_audio:
                try:
                    audio_bytes, filename = self.gerar_audio_exemplo(ex, source_lang)
                    saved_name = self.anki.salvar_midia(filename, audio_bytes)
                    ex.audio_filename = saved_name
                except Exception as exc:
                    warnings.append(f"Áudio não gerado para '{ex.source[:25]}...': {exc}")

            if export_config.include_image and ex.image_bytes:
                try:
                    img_filename = ex.image_filename or self.images.make_filename(ex.image_bytes, ".jpg")
                    saved_img = self.anki.salvar_midia(img_filename, ex.image_bytes)
                    ex.image_filename = saved_img
                except Exception as exc:
                    warnings.append(f"Imagem não salva para '{ex.source[:25]}...': {exc}")

        added = self.anki.adicionar_exemplos(exemplos, export_config, query=query)
        return added, warnings

    def salvar_configuracoes(self, novos_valores: Dict) -> None:
        self.config.update(novos_valores)
