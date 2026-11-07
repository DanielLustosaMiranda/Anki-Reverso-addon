import json
import os
import re
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional
from ..enums.languages import LANGUAGE_INFO
from ..models.example import ExampleItem, LookupResult
from .config_service import ConfigService


class AIService:
    """Serviço de Inteligência Artificial (LLM) para gerar frases de exemplo e explicações contextuais."""

    def __init__(self, config_service: ConfigService) -> None:
        self.config = config_service

    def _get_provider_config(self) -> Dict[str, Any]:
        provider = (self.config.get("ai_provider") or "gemini").lower().strip()
        api_key = (self.config.get("ai_api_key") or "").strip()

        # Permite ler de variáveis de ambiente caso o usuário não tenha preenchido na UI
        if not api_key:
            if provider == "gemini":
                api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""
            elif provider == "openai":
                api_key = os.environ.get("OPENAI_API_KEY") or ""
            elif provider == "groq":
                api_key = os.environ.get("GROQ_API_KEY") or ""

        model = (self.config.get("ai_model") or "").strip()
        if not model:
            default_models = {
                "gemini": "gemini-2.5-flash",
                "openai": "gpt-4o-mini",
                "groq": "llama-3.3-70b-versatile",
                "ollama": "llama3.2",
            }
            model = default_models.get(provider, "gemini-2.5-flash")

        base_url = (self.config.get("ai_base_url") or "").strip()
        return {
            "provider": provider,
            "api_key": api_key,
            "model": model,
            "base_url": base_url,
        }

    def generate_examples(
        self,
        query: str,
        source_lang: str,
        target_lang: str,
        level: str = "B1",
        style: str = "Conversação natural",
        count: int = 5,
    ) -> LookupResult:
        text = query.strip()
        src_label = LANGUAGE_INFO.get(source_lang, {}).get("label", source_lang)
        trg_label = LANGUAGE_INFO.get(target_lang, {}).get("label", target_lang)

        system_prompt = (
            "Você é um professor especialista em ensino de idiomas e criação de flashcards para o Anki. "
            "Responda ESTRITAMENTE em formato JSON válido, sem blocos markdown extras."
        )

        user_prompt = f"""Crie {count} frases de exemplo autênticas para estudar o termo/expressão "{text}".
- Idioma da frase (origem): {src_label} ({source_lang})
- Idioma da tradução/explicação (destino): {trg_label} ({target_lang})
- Nível de proficiência CEFR: {level}
- Estilo/Contexto: {style}

Regras obrigatórias:
1. Envolva a palavra ou expressão alvo com a tag <em>...</em> tanto em `source_html` quanto no termo equivalente em `target_html`.
2. Forneça uma lista `translations` com 3 a 6 traduções diretas ou sinônimos do termo buscado.
3. Em cada exemplo, inclua um campo `explanation` curto (1 a 2 frases em {trg_label}) explicando o sentido do termo naquele contexto, nuances gramaticais ou dicas de uso.

Formato JSON esperado:
{{
  "translations": ["tradução 1", "tradução 2"],
  "examples": [
    {{
      "source_html": "Frase no idioma de origem com <em>{text}</em> destacada.",
      "target_html": "Tradução natural com <em>equivalente</em> destacado.",
      "explanation": "Breve explicação gramatical/contextual da frase."
    }}
  ]
}}"""

        try:
            raw_response = self._call_llm(system_prompt, user_prompt, json_mode=True)
            parsed = self._parse_json_response(raw_response)
        except Exception as exc:
            return LookupResult(
                query=text,
                source_lang=source_lang,
                target_lang=target_lang,
                error=str(exc),
            )

        translations = [str(t).strip() for t in (parsed.get("translations") or []) if str(t).strip()]
        raw_examples = parsed.get("examples") or []

        examples: List[ExampleItem] = []
        for idx, item in enumerate(raw_examples):
            if not isinstance(item, dict):
                continue
            src_html = str(item.get("source_html") or item.get("source") or "").strip()
            trg_html = str(item.get("target_html") or item.get("target") or "").strip()
            explanation = str(item.get("explanation") or "").strip()
            if not src_html or not trg_html:
                continue
            examples.append(
                ExampleItem(
                    id=1000 + idx,
                    source=src_html,
                    target=trg_html,
                    source_html=src_html,
                    target_html=trg_html,
                    explanation=explanation,
                    origin="ai",
                )
            )

        return LookupResult(
            query=text,
            source_lang=source_lang,
            target_lang=target_lang,
            translations=translations,
            examples=examples,
        )

    def explain_example(
        self,
        query: str,
        sentence_source: str,
        sentence_target: str,
        source_lang: str,
        target_lang: str,
    ) -> str:
        src_label = LANGUAGE_INFO.get(source_lang, {}).get("label", source_lang)
        trg_label = LANGUAGE_INFO.get(target_lang, {}).get("label", target_lang)

        system_prompt = (
            "Você é um tutor conciso de idiomas. Forneça explicações curtas e diretas ideais "
            "para o verso de um flashcard do Anki (sem saudações, direto ao ponto)."
        )
        user_prompt = (
            f"Explique brevemente em {trg_label} (máximo de 3 linhas) o uso do termo '{query}' "
            f"e a estrutura chave na seguinte frase em {src_label}:\n"
            f"Frase: \"{sentence_source}\"\n"
            f"Tradução: \"{sentence_target}\""
        )

        return self._call_llm(system_prompt, user_prompt, json_mode=False).strip()

    def _call_llm(self, system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
        cfg = self._get_provider_config()
        provider = cfg["provider"]
        api_key = cfg["api_key"]
        model = cfg["model"]
        base_url = cfg["base_url"]

        if provider != "ollama" and not api_key:
            raise ValueError(
                f"Chave de API para '{provider.upper()}' não configurada. "
                "Clique em 'Configurações' no Add-on e informe sua API Key."
            )

        if provider == "gemini":
            return self._call_gemini(api_key, model, system_prompt, user_prompt, json_mode)

        # OpenAI, Groq ou Ollama (compatíveis com Chat Completions)
        if provider == "openai":
            endpoint = (base_url.rstrip("/") if base_url else "https://api.openai.com/v1") + "/chat/completions"
        elif provider == "groq":
            endpoint = (base_url.rstrip("/") if base_url else "https://api.groq.com/openai/v1") + "/chat/completions"
        elif provider == "ollama":
            endpoint = (base_url.rstrip("/") if base_url else "http://localhost:11434/v1") + "/chat/completions"
        else:
            raise ValueError(f"Provedor de IA desconhecido: {provider}")

        return self._call_openai_compatible(endpoint, api_key, model, system_prompt, user_prompt, json_mode)

    def _call_gemini(
        self,
        api_key: str,
        model: str,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool,
    ) -> str:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={urllib.parse.quote(api_key)}"
        )
        gen_config: Dict[str, Any] = {"temperature": 0.7}
        if json_mode:
            gen_config["responseMimeType"] = "application/json"

        payload = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": gen_config,
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as err:
            err_body = err.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Erro na API Gemini ({err.code}): {err_body}") from err
        except Exception as exc:
            raise RuntimeError(f"Falha ao conectar na API Gemini: {exc}") from exc

        candidates = data.get("candidates") or []
        if not candidates:
            raise RuntimeError(f"Resposta vazia do Gemini: {data}")
        parts = (candidates[0].get("content") or {}).get("parts") or []
        return "".join(p.get("text", "") for p in parts)

    def _call_openai_compatible(
        self,
        endpoint: str,
        api_key: str,
        model: str,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool,
    ) -> str:
        payload: Dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.7,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Anki-Reverso-AI-Addon/2.0",
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as err:
            err_body = err.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Erro na API LLM ({err.code}): {err_body}") from err
        except Exception as exc:
            raise RuntimeError(f"Falha ao conectar no endpoint LLM ({endpoint}): {exc}") from exc

        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError(f"Resposta inválida da API LLM: {data}")
        return str((choices[0].get("message") or {}).get("content") or "")

    @staticmethod
    def _parse_json_response(raw_text: str) -> Dict[str, Any]:
        cleaned = raw_text.strip()
        # Remove cercas markdown ```json ... ``` se o modelo as incluir
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
            if match:
                return json.loads(match.group(0))
            raise ValueError(f"Não foi possível interpretar o JSON retornado pela IA: {raw_text[:200]}")
