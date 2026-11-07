import asyncio
import base64
import hashlib
import io
import json
import os
import urllib.error
import urllib.parse
import urllib.request
import wave
from typing import Dict, Tuple
from ..enums.languages import LANGUAGE_INFO
from .config_service import ConfigService


class TTSService:
    """Serviço de Text-to-Speech (TTS) por IA com cache em memória e suporte a múltiplos motores."""

    REVERSO_VOICE_URL = (
        "https://voice.reverso.net/RestPronunciation.svc/v1/output=json/GetVoiceStream/"
    )
    USER_AGENT = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )

    def __init__(self, config_service: ConfigService) -> None:
        self.config = config_service
        self._cache: Dict[str, Tuple[bytes, str]] = {}

    def synthesize(self, text: str, language: str) -> Tuple[bytes, str]:
        """Gera os bytes de áudio e o nome de arquivo determinístico para a frase."""
        clean_text = " ".join(text.strip().split())
        if not clean_text:
            raise ValueError("Texto vazio para síntese de voz.")

        provider = (self.config.get("tts_provider") or "free_neural").lower().strip()
        voice = (self.config.get("tts_voice") or "alloy").strip()
        cache_key = hashlib.sha256(f"{provider}:{language}:{voice}:{clean_text}".encode("utf-8")).hexdigest()[:16]

        if cache_key in self._cache:
            return self._cache[cache_key]

        if provider == "openai":
            audio_bytes, ext = self._synthesize_openai(clean_text)
        elif provider == "gemini":
            audio_bytes, ext = self._synthesize_gemini(clean_text, language)
        elif provider == "elevenlabs":
            audio_bytes, ext = self._synthesize_elevenlabs(clean_text)
        else:
            audio_bytes, ext = self._synthesize_free_neural(clean_text, language)

        iso = LANGUAGE_INFO.get(language.lower(), {}).get("iso_code", "lang")
        filename = f"reverso_ai_{iso}_{cache_key}{ext}"
        self._cache[cache_key] = (audio_bytes, filename)
        return audio_bytes, filename

    def _get_tts_api_key(self, provider: str) -> str:
        tts_key = (self.config.get("tts_api_key") or "").strip()
        if tts_key:
            return tts_key

        # Se usar o mesmo provedor da IA (ex: OpenAI ou Gemini), reaproveita a ai_api_key
        ai_provider = (self.config.get("ai_provider") or "").lower().strip()
        ai_key = (self.config.get("ai_api_key") or "").strip()
        if ai_key and ai_provider == provider:
            return ai_key

        if provider == "openai":
            return os.environ.get("OPENAI_API_KEY") or ""
        if provider == "gemini":
            return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""
        if provider == "elevenlabs":
            return os.environ.get("ELEVENLABS_API_KEY") or ""
        return ""

    def _synthesize_free_neural(self, text: str, language: str) -> Tuple[bytes, str]:
        lang_info = LANGUAGE_INFO.get(language.lower(), LANGUAGE_INFO["english"])

        # 1. Se o pacote edge_tts estiver disponível no ambiente, usa voz Neural da Microsoft
        try:
            import edge_tts  # type: ignore

            edge_voice = lang_info.get("edge_voice", "en-US-AriaNeural")

            async def _run_edge() -> bytes:
                communicate = edge_tts.Communicate(text, edge_voice)
                chunks = []
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        chunks.append(chunk["data"])
                return b"".join(chunks)

            data = asyncio.run(_run_edge())
            if data:
                return data, ".mp3"
        except Exception:
            pass

        # 2. Tenta a API de voz nativa do Reverso (retorna MP3 direto via HTTPS sem API key)
        reverso_voice = lang_info.get("reverso_voice", "")
        if reverso_voice:
            try:
                b64_text = base64.b64encode(text.encode("utf-8")).decode("ascii")
                url = (
                    f"{self.REVERSO_VOICE_URL}voiceName={urllib.parse.quote(reverso_voice)}"
                    f"?inputText={urllib.parse.quote(b64_text)}"
                )
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": self.USER_AGENT, "Accept": "audio/mpeg, */*"},
                    method="GET",
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    audio = resp.read()
                    if len(audio) > 256:
                        return audio, ".mp3"
            except Exception:
                pass

        # 3. Fallback universal Google Translate TTS (MP3 via HTTPS sem chave de API)
        iso_code = lang_info.get("iso_code", "en")
        params = urllib.parse.urlencode(
            {
                "ie": "UTF-8",
                "client": "tw-ob",
                "tl": iso_code,
                "q": text,
            }
        )
        g_url = f"https://translate.googleapis.com/translate_tts?{params}"
        req = urllib.request.Request(
            g_url,
            headers={"User-Agent": self.USER_AGENT},
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                audio = resp.read()
                if audio:
                    return audio, ".mp3"
        except Exception as exc:
            raise RuntimeError(f"Falha ao gerar áudio gratuito (TTS): {exc}") from exc

        raise RuntimeError("Não foi possível sintetizar o áudio para a frase.")

    def _synthesize_openai(self, text: str) -> Tuple[bytes, str]:
        api_key = self._get_tts_api_key("openai")
        if not api_key:
            raise ValueError(
                "Chave de API da OpenAI não configurada para o TTS. "
                "Configure em 'Configurações' ou altere o provedor de TTS para 'Gratuito (Voz Neural)'."
            )

        model = (self.config.get("tts_model") or "gpt-4o-mini-tts").strip()
        voice = (self.config.get("tts_voice") or "alloy").strip()
        payload = {
            "model": model,
            "input": text,
            "voice": voice,
            "response_format": "mp3",
        }

        req = urllib.request.Request(
            "https://api.openai.com/v1/audio/speech",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                return resp.read(), ".mp3"
        except urllib.error.HTTPError as err:
            err_body = err.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Erro no OpenAI TTS ({err.code}): {err_body}") from err

    def _synthesize_gemini(self, text: str, language: str) -> Tuple[bytes, str]:
        api_key = self._get_tts_api_key("gemini")
        if not api_key:
            raise ValueError(
                "Chave de API do Gemini não configurada para o TTS. "
                "Configure em 'Configurações' ou altere o provedor de TTS para 'Gratuito (Voz Neural)'."
            )

        model = "gemini-2.5-flash-preview-tts"
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={urllib.parse.quote(api_key)}"
        )
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": f"Read the following {language} sentence naturally and clearly: {text}"
                        }
                    ]
                }
            ],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {
                            "voiceName": "Kore",
                        }
                    }
                },
            },
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
            raise RuntimeError(f"Erro no Gemini TTS ({err.code}): {err_body}") from err

        candidates = data.get("candidates") or []
        if not candidates:
            raise RuntimeError(f"Resposta vazia do Gemini TTS: {data}")

        parts = (candidates[0].get("content") or {}).get("parts") or []
        for part in parts:
            inline = part.get("inlineData") or {}
            b64_audio = inline.get("data")
            mime = inline.get("mimeType", "")
            if b64_audio:
                raw_bytes = base64.b64decode(b64_audio)
                if "pcm" in mime.lower() or not raw_bytes.startswith(b"RIFF"):
                    return self._pcm24k_to_wav(raw_bytes), ".wav"
                return raw_bytes, ".wav"

        raise RuntimeError("A resposta do Gemini não retornou dados de áudio.")

    def _synthesize_elevenlabs(self, text: str) -> Tuple[bytes, str]:
        api_key = self._get_tts_api_key("elevenlabs")
        if not api_key:
            raise ValueError(
                "Chave de API da ElevenLabs não configurada. "
                "Informe sua chave nas Configurações ou use o modo Gratuito."
            )

        voice_id = (self.config.get("elevenlabs_voice_id") or "21m00Tcm4TlvDq8ikWAM").strip()
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{urllib.parse.quote(voice_id)}"
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "xi-api-key": api_key,
                "Accept": "audio/mpeg",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                return resp.read(), ".mp3"
        except urllib.error.HTTPError as err:
            err_body = err.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Erro no ElevenLabs TTS ({err.code}): {err_body}") from err

    @staticmethod
    def _pcm24k_to_wav(pcm_bytes: bytes, sample_rate: int = 24000) -> bytes:
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(pcm_bytes)
        return buf.getvalue()
