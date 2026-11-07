import base64
import hashlib
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import List, Tuple
from ..models.example import WebImageResult
from .config_service import ConfigService


class ImageService:
    """Serviço para busca de imagens gratuitas na web, geração de imagem por IA e carregamento local."""

    WIKIMEDIA_API_URL = "https://commons.wikimedia.org/w/api.php"
    OPENVERSE_API_URL = "https://api.openverse.org/v1/images/"
    USER_AGENT = "AnkiReversoAIAddon/2.0 (https://github.com/DanielLustosaMiranda/Anki-Reverso-addon)"

    def __init__(self, config_service: ConfigService) -> None:
        self.config = config_service

    @staticmethod
    def make_filename(image_bytes: bytes, ext: str = ".jpg") -> str:
        if not ext.startswith("."):
            ext = f".{ext}"
        digest = hashlib.sha256(image_bytes).hexdigest()[:16]
        return f"reverso_img_{digest}{ext.lower()}"

    def load_from_file(self, file_path: str) -> Tuple[bytes, str]:
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
        ext = os.path.splitext(file_path)[1].lower() or ".png"
        with open(file_path, "rb") as f:
            data = f.read()
        if not data:
            raise ValueError("O arquivo de imagem selecionado está vazio.")
        return data, self.make_filename(data, ext)

    def search_web_images(self, query: str, limit: int = 6) -> List[WebImageResult]:
        clean_query = query.strip()
        if not clean_query:
            return []

        results = self._search_wikimedia(clean_query, limit=limit)
        if len(results) < limit:
            extra = self._search_openverse(clean_query, limit=limit - len(results))
            results.extend(extra)

        # Faz o download das miniaturas para exibir e anexar rapidamente
        populated: List[WebImageResult] = []
        for item in results[:limit]:
            try:
                img_bytes = self._download_bytes(item.thumb_url)
                if img_bytes and len(img_bytes) > 512:
                    item.image_bytes = img_bytes
                    populated.append(item)
            except Exception:
                continue

        return populated

    def _search_wikimedia(self, query: str, limit: int = 6) -> List[WebImageResult]:
        params = urllib.parse.urlencode(
            {
                "action": "query",
                "format": "json",
                "generator": "search",
                "gsrsearch": f"filetype:bitmap {query}",
                "gsrnamespace": 6,
                "gsrlimit": limit + 3,
                "prop": "imageinfo",
                "iiprop": "url|mime",
                "iiurlwidth": 420,
            }
        )
        url = f"{self.WIKIMEDIA_API_URL}?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": self.USER_AGENT}, method="GET")

        results: List[WebImageResult] = []
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception:
            return results

        pages = (data.get("query") or {}).get("pages") or {}
        for page in pages.values():
            title = str(page.get("title") or "").replace("File:", "").strip()
            info_list = page.get("imageinfo") or []
            if not info_list:
                continue
            info = info_list[0]
            mime = str(info.get("mime") or "").lower()
            if not any(m in mime for m in ("jpeg", "jpg", "png", "webp")):
                continue
            thumb_url = str(info.get("thumburl") or info.get("url") or "")
            full_url = str(info.get("url") or thumb_url)
            if not thumb_url:
                continue
            ext = ".png" if "png" in mime else ".jpg"
            results.append(
                WebImageResult(
                    title=title[:60],
                    thumb_url=thumb_url,
                    full_url=full_url,
                    extension=ext,
                )
            )
            if len(results) >= limit:
                break

        return results

    def _search_openverse(self, query: str, limit: int = 4) -> List[WebImageResult]:
        params = urllib.parse.urlencode({"q": query, "page_size": limit})
        url = f"{self.OPENVERSE_API_URL}?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": self.USER_AGENT}, method="GET")

        results: List[WebImageResult] = []
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception:
            return results

        for item in data.get("results") or []:
            thumb = str(item.get("thumbnail") or item.get("url") or "")
            full = str(item.get("url") or thumb)
            title = str(item.get("title") or query)[:60]
            if thumb:
                results.append(
                    WebImageResult(
                        title=title,
                        thumb_url=thumb,
                        full_url=full,
                        extension=".jpg",
                    )
                )
        return results

    def generate_ai_image(self, prompt: str) -> Tuple[bytes, str]:
        """Gera uma ilustração por IA usando OpenAI, Gemini Imagen ou motor gratuito Pollinations."""
        clean_prompt = prompt.strip()
        if not clean_prompt:
            raise ValueError("Digite uma descrição ou frase para gerar a imagem.")

        provider = (self.config.get("ai_provider") or "gemini").lower().strip()
        api_key = (self.config.get("ai_api_key") or "").strip()

        if provider == "openai" and api_key:
            try:
                img_bytes = self._generate_openai_image(clean_prompt, api_key)
                return img_bytes, self.make_filename(img_bytes, ".png")
            except Exception:
                pass

        if provider == "gemini" and api_key:
            try:
                img_bytes = self._generate_gemini_image(clean_prompt, api_key)
                return img_bytes, self.make_filename(img_bytes, ".png")
            except Exception:
                pass

        # Fallback universal gratuito (Pollinations AI Image)
        img_bytes = self._generate_free_ai_image(clean_prompt)
        return img_bytes, self.make_filename(img_bytes, ".jpg")

    def _generate_openai_image(self, prompt: str, api_key: str) -> bytes:
        payload = {
            "model": "dall-e-3",
            "prompt": f"Clear educational flashcard illustration for language learning: {prompt}",
            "n": 1,
            "size": "1024x1024",
            "response_format": "b64_json",
        }
        req = urllib.request.Request(
            "https://api.openai.com/v1/images/generations",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=40) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        b64_str = data["data"][0]["b64_json"]
        return base64.b64decode(b64_str)

    def _generate_gemini_image(self, prompt: str, api_key: str) -> bytes:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"imagen-3.0-generate-002:predict?key={urllib.parse.quote(api_key)}"
        )
        payload = {
            "instances": [
                {"prompt": f"Clean educational flashcard illustration: {prompt}"}
            ],
            "parameters": {"sampleCount": 1, "aspectRatio": "1:1"},
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=35) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        predictions = data.get("predictions") or []
        if predictions and predictions[0].get("bytesBase64Encoded"):
            return base64.b64decode(predictions[0]["bytesBase64Encoded"])
        raise RuntimeError("Imagen API não retornou bytes.")

    def _generate_free_ai_image(self, prompt: str) -> bytes:
        full_prompt = f"educational flashcard illustration, clean style, {prompt}"
        encoded = urllib.parse.quote(full_prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=512&height=512&nologo=true"
        try:
            return self._download_bytes(url, timeout=30)
        except Exception as exc:
            raise RuntimeError(f"Falha ao gerar imagem por IA: {exc}") from exc

    def _download_bytes(self, url: str, timeout: int = 15) -> bytes:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": self.USER_AGENT, "Accept": "image/*,*/*;q=0.8"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
