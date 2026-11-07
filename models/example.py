import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ExampleItem:
    id: int
    source: str
    target: str
    source_html: str = ""
    target_html: str = ""
    explanation: str = ""
    origin: str = "reverso"  # "reverso" | "ai"
    audio_bytes: Optional[bytes] = field(default=None, repr=False)
    audio_filename: str = ""

    def __post_init__(self) -> None:
        if not self.source_html:
            self.source_html = self.source
        if not self.target_html:
            self.target_html = self.target
        # Garante que source e target contenham texto limpo sem tags HTML
        self.source = self._strip_tags(self.source)
        self.target = self._strip_tags(self.target)

    @staticmethod
    def _strip_tags(text: str) -> str:
        return re.sub(r"<[^>]+>", "", text or "").strip()

    def formatted_source_html(self) -> str:
        """Retorna a frase original com destaque estilizado para a palavra-alvo."""
        return re.sub(
            r"<em>(.*?)</em>",
            r'<b style="color: #2563eb;">\1</b>',
            self.source_html,
            flags=re.IGNORECASE,
        )

    def formatted_target_html(self) -> str:
        """Retorna a tradução com destaque estilizado para a palavra-alvo."""
        return re.sub(
            r"<em>(.*?)</em>",
            r'<b style="color: #059669;">\1</b>',
            self.target_html,
            flags=re.IGNORECASE,
        )


@dataclass
class LookupResult:
    query: str
    source_lang: str
    target_lang: str
    translations: List[str] = field(default_factory=list)
    examples: List[ExampleItem] = field(default_factory=list)
    error: Optional[str] = None
