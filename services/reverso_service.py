import json
import re
import urllib.parse
import urllib.request
from typing import Any, Dict, List
from ..enums.languages import LANGUAGE_INFO
from ..models.example import ExampleItem, LookupResult


class ReversoService:
    """Cliente HTTP em Python puro para a API do Reverso Context (sem Node.js ou Playwright)."""

    TRANSLATION_API_URL = "https://api.reverso.net/translate/v1/translation"
    CONTEXT_WEB_URL = "https://context.reverso.net/translation/"

    USER_AGENT = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )

    def get_context(self, text: str, source_lang: str, target_lang: str) -> LookupResult:
        query = text.strip()
        source_key = source_lang.lower().strip()
        target_key = target_lang.lower().strip()

        if not query:
            return LookupResult(query=query, source_lang=source_key, target_lang=target_key)

        if source_key == target_key:
            return LookupResult(
                query=query,
                source_lang=source_key,
                target_lang=target_key,
                error="Os idiomas de origem e destino devem ser diferentes.",
            )

        # 1. Tenta primeiro a API JSON oficial mobile do Reverso (rápida e estruturada)
        api_result = self._fetch_via_translation_api(query, source_key, target_key)
        if api_result.examples:
            return api_result

        # 2. Fallback: scraping leve via HTTP direto em Python puro se a API JSON não retornar exemplos
        web_result = self._fetch_via_web_html(query, source_key, target_key)
        if web_result.examples or web_result.translations:
            if not web_result.translations and api_result.translations:
                web_result.translations = api_result.translations
            return web_result

        return api_result

    def _fetch_via_translation_api(
        self, query: str, source_key: str, target_key: str
    ) -> LookupResult:
        src_info = LANGUAGE_INFO.get(source_key)
        trg_info = LANGUAGE_INFO.get(target_key)
        if not src_info or not trg_info:
            return LookupResult(
                query=query,
                source_lang=source_key,
                target_lang=target_key,
                error=f"Par de idiomas não suportado: {source_key} -> {target_key}",
            )

        payload = {
            "format": "text",
            "from": src_info["reverso_code"],
            "to": trg_info["reverso_code"],
            "input": query,
            "options": {
                "contextResults": True,
                "languageDetection": True,
                "origin": "reversomobile",
                "sentenceSplitter": False,
            },
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "User-Agent": self.USER_AGENT,
            "Origin": "https://www.reverso.net",
            "Referer": "https://www.reverso.net/",
        }

        try:
            req = urllib.request.Request(
                self.TRANSLATION_API_URL,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data: Dict[str, Any] = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            return LookupResult(
                query=query,
                source_lang=source_key,
                target_lang=target_key,
                error=f"Erro ao consultar a API do Reverso: {exc}",
            )

        raw_translations: List[str] = list(data.get("translation") or [])
        context_results = (data.get("contextResults") or {}).get("results") or []

        for item in context_results:
            tr = item.get("translation")
            if tr and tr not in raw_translations:
                raw_translations.append(tr)

        examples: List[ExampleItem] = []
        example_id = 0
        for result_block in context_results:
            src_list = result_block.get("sourceExamples") or []
            trg_list = result_block.get("targetExamples") or []
            for src_html, trg_html in zip(src_list, trg_list):
                if not src_html or not trg_html:
                    continue
                examples.append(
                    ExampleItem(
                        id=example_id,
                        source=src_html,
                        target=trg_html,
                        source_html=src_html,
                        target_html=trg_html,
                        origin="reverso",
                    )
                )
                example_id += 1

        return LookupResult(
            query=query,
            source_lang=source_key,
            target_lang=target_key,
            translations=[t for t in raw_translations if t],
            examples=examples,
        )

    def _fetch_via_web_html(
        self, query: str, source_key: str, target_key: str
    ) -> LookupResult:
        encoded_query = urllib.parse.quote(query).replace("%20", "+")
        url = f"{self.CONTEXT_WEB_URL}{source_key}-{target_key}/{encoded_query}"
        headers = {
            "User-Agent": self.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8",
        }

        try:
            req = urllib.request.Request(url, headers=headers, method="GET")
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
        except Exception as exc:
            return LookupResult(
                query=query,
                source_lang=source_key,
                target_lang=target_key,
                error=f"Falha na busca web do Reverso: {exc}",
            )

        # Extrai blocos de exemplos <div class="example">...</div>
        src_matches = re.findall(
            r'<div class="src[^"]*">\s*<span class="text">(.*?)</span>',
            html,
            flags=re.DOTALL,
        )
        trg_matches = re.findall(
            r'<div class="trg[^"]*">\s*<span class="text">(.*?)</span>',
            html,
            flags=re.DOTALL,
        )
        translations = re.findall(
            r'<span class="display-term">(.*?)</span>',
            html,
            flags=re.DOTALL,
        )

        examples: List[ExampleItem] = []
        for idx, (s_raw, t_raw) in enumerate(zip(src_matches, trg_matches)):
            s_clean_html = self._clean_reverso_span_html(s_raw)
            t_clean_html = self._clean_reverso_span_html(t_raw)
            examples.append(
                ExampleItem(
                    id=idx,
                    source=s_clean_html,
                    target=t_clean_html,
                    source_html=s_clean_html,
                    target_html=t_clean_html,
                    origin="reverso",
                )
            )

        clean_translations = [re.sub(r"<[^>]+>", "", t).strip() for t in translations if t.strip()]
        return LookupResult(
            query=query,
            source_lang=source_key,
            target_lang=target_key,
            translations=list(dict.fromkeys(clean_translations)),
            examples=examples,
        )

    @staticmethod
    def _clean_reverso_span_html(raw_html: str) -> str:
        # Preserva apenas tags <em>...</em> e remove links/spans extras
        text = re.sub(r"<a[^>]*>", "", raw_html)
        text = re.sub(r"</a>", "", text)
        text = re.sub(r"<(?!/?em\b)[^>]+>", "", text)
        return " ".join(text.split())
