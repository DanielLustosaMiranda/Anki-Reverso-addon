import base64
import json
import urllib.request
from typing import Any, Dict, List, Optional
from ..models.example import ExampleItem
from ..models.note_config import NoteExportConfig
from ..utils.qt_compat import is_running_in_anki, mw


class AnkiService:
    """Serviço de integração nativa com a coleção do Anki (mw.col) e fallback para AnkiConnect."""

    CUSTOM_MODEL_NAME = "Reverso AI Card"
    CUSTOM_FIELDS = ["Front", "Back", "Explanation", "Image", "Audio", "Word"]

    CARD_CSS = """
.card {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    font-size: 20px;
    text-align: center;
    color: #1f2937;
    background-color: #f9fafb;
    padding: 24px;
}
.nightMode .card {
    color: #f3f4f6;
    background-color: #111827;
}
.sentence-front {
    font-size: 24px;
    line-height: 1.5;
    margin-bottom: 16px;
}
.sentence-back {
    font-size: 20px;
    color: #059669;
    margin-top: 14px;
}
.nightMode .sentence-back {
    color: #34d399;
}
.card-image {
    margin: 16px auto;
}
.card-image img {
    max-width: 340px;
    max-height: 240px;
    border-radius: 10px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
}
.explanation-box {
    margin-top: 18px;
    padding: 12px 16px;
    border-radius: 8px;
    background-color: #eff6ff;
    color: #1e3a8a;
    font-size: 15px;
    text-align: left;
    border-left: 4px solid #3b82f6;
}
.nightMode .explanation-box {
    background-color: #1e293b;
    color: #bfdbfe;
}
.word-badge {
    display: inline-block;
    font-size: 13px;
    color: #6b7280;
    margin-bottom: 8px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
"""

    FRONT_TEMPLATE = """
{{#Word}}<div class="word-badge">{{Word}}</div>{{/Word}}
<div class="sentence-front">{{Front}}</div>
{{#Audio}}<div>{{Audio}}</div>{{/Audio}}
"""

    BACK_TEMPLATE = """
{{FrontSide}}
<hr id="answer">
<div class="sentence-back">{{Back}}</div>
{{#Image}}
<div class="card-image">{{Image}}</div>
{{/Image}}
{{#Explanation}}
<div class="explanation-box">
    <b>Nota Contextual:</b><br>{{Explanation}}
</div>
{{/Explanation}}
"""

    def __init__(self) -> None:
        self.anki_connect_url = "http://localhost:8765"

    def listar_decks(self) -> List[str]:
        if is_running_in_anki() and mw is not None and mw.col is not None:
            try:
                decks = mw.col.decks.all_names_and_ids()
                return [d.name for d in decks]
            except Exception:
                return mw.col.decks.allNames()

        # Fallback AnkiConnect (modo standalone)
        res = self._anki_connect_invoke("deckNames")
        if isinstance(res, list):
            return [str(d) for d in res]
        return ["Default"]

    def listar_note_types(self) -> List[str]:
        if is_running_in_anki() and mw is not None and mw.col is not None:
            try:
                models = mw.col.models.all_names_and_ids()
                return [m.name for m in models]
            except Exception:
                return mw.col.models.allNames()

        res = self._anki_connect_invoke("modelNames")
        if isinstance(res, list):
            return [str(m) for m in res]
        return [self.CUSTOM_MODEL_NAME, "Basic"]

    def listar_campos_note_type(self, model_name: str) -> List[str]:
        if model_name == self.CUSTOM_MODEL_NAME:
            return list(self.CUSTOM_FIELDS)

        if is_running_in_anki() and mw is not None and mw.col is not None:
            model = mw.col.models.by_name(model_name)
            if model:
                return [f["name"] for f in model.get("flds", [])]

        res = self._anki_connect_invoke("modelFieldNames", {"modelName": model_name})
        if isinstance(res, list) and res:
            return [str(f) for f in res]
        return ["Front", "Back"]

    def ensure_custom_note_type(self) -> Optional[Dict[str, Any]]:
        """Garante que o modelo de nota 'Reverso AI Card' exista e possua todos os campos atuais."""
        if is_running_in_anki() and mw is not None and mw.col is not None:
            mm = mw.col.models
            existing = mm.by_name(self.CUSTOM_MODEL_NAME)
            if existing is not None:
                # Atualiza campos caso o usuário tinha versão anterior sem o campo Image
                existing_fields = [f["name"] for f in existing.get("flds", [])]
                updated = False
                for field_name in self.CUSTOM_FIELDS:
                    if field_name not in existing_fields:
                        mm.add_field(existing, mm.new_field(field_name))
                        updated = True
                if updated:
                    existing["css"] = self.CARD_CSS.strip()
                    if existing.get("tmpls"):
                        existing["tmpls"][0]["qfmt"] = self.FRONT_TEMPLATE.strip()
                        existing["tmpls"][0]["afmt"] = self.BACK_TEMPLATE.strip()
                    mm.save(existing)
                return existing

            model = mm.new(self.CUSTOM_MODEL_NAME)
            for field_name in self.CUSTOM_FIELDS:
                fld = mm.new_field(field_name)
                mm.add_field(model, fld)

            tmpl = mm.new_template("Card 1")
            tmpl["qfmt"] = self.FRONT_TEMPLATE.strip()
            tmpl["afmt"] = self.BACK_TEMPLATE.strip()
            mm.add_template(model, tmpl)
            model["css"] = self.CARD_CSS.strip()
            mm.add(model)
            return model

        # Fallback AnkiConnect
        existing_models = self.listar_note_types()
        if self.CUSTOM_MODEL_NAME not in existing_models:
            self._anki_connect_invoke(
                "createModel",
                {
                    "modelName": self.CUSTOM_MODEL_NAME,
                    "inOrderFields": self.CUSTOM_FIELDS,
                    "css": self.CARD_CSS.strip(),
                    "cardTemplates": [
                        {
                            "Name": "Card 1",
                            "Front": self.FRONT_TEMPLATE.strip(),
                            "Back": self.BACK_TEMPLATE.strip(),
                        }
                    ],
                },
            )
        return None

    def salvar_midia(self, filename: str, media_bytes: bytes) -> str:
        """Grava arquivo de mídia (áudio ou imagem) na pasta collection.media do Anki."""
        if is_running_in_anki() and mw is not None and mw.col is not None:
            return mw.col.media.write_data(filename, media_bytes)

        # Fallback AnkiConnect
        b64_data = base64.b64encode(media_bytes).decode("ascii")
        res = self._anki_connect_invoke(
            "storeMediaFile",
            {"filename": filename, "data": b64_data},
        )
        return str(res) if res else filename

    def adicionar_exemplos(
        self,
        exemplos: List[ExampleItem],
        export_config: NoteExportConfig,
        query: str = "",
    ) -> int:
        """Cria notas no Anki para cada exemplo selecionado. Retorna a quantidade adicionada."""
        if not exemplos:
            return 0

        if export_config.use_custom_note_type:
            self.ensure_custom_note_type()
            target_model_name = self.CUSTOM_MODEL_NAME
        else:
            target_model_name = export_config.note_type_name

        added_count = 0

        if is_running_in_anki() and mw is not None and mw.col is not None:
            col = mw.col
            deck_id = col.decks.id(export_config.deck_name)
            model = col.models.by_name(target_model_name)
            if model is None:
                all_models = col.models.all()
                if not all_models:
                    raise RuntimeError("Nenhum Note Type encontrado na coleção do Anki.")
                model = all_models[0]

            for ex in exemplos:
                note = col.new_note(model)
                fields_dict = self._build_note_fields(ex, export_config, query, model_fields=list(note.keys()))
                for f_name, f_val in fields_dict.items():
                    if f_name in note:
                        note[f_name] = f_val

                for tag in export_config.tags:
                    clean_tag = tag.strip().replace(" ", "_")
                    if clean_tag:
                        note.add_tag(clean_tag)

                col.add_note(note, deck_id)
                added_count += 1

            mw.reset()
            return added_count

        # Fallback AnkiConnect (modo standalone)
        available_fields = self.listar_campos_note_type(target_model_name)
        for ex in exemplos:
            fields_dict = self._build_note_fields(ex, export_config, query, model_fields=available_fields)
            note_payload = {
                "deckName": export_config.deck_name,
                "modelName": target_model_name,
                "fields": fields_dict,
                "options": {"allowDuplicate": True},
                "tags": [t.strip().replace(" ", "_") for t in export_config.tags if t.strip()],
            }
            res = self._anki_connect_invoke("addNote", {"note": note_payload})
            if res is not None:
                added_count += 1

        return added_count

    def _build_note_fields(
        self,
        ex: ExampleItem,
        export_config: NoteExportConfig,
        query: str,
        model_fields: List[str],
    ) -> Dict[str, str]:
        sound_tag = f"[sound:{ex.audio_filename}]" if (export_config.include_audio and ex.audio_filename) else ""
        img_tag = f'<img src="{ex.image_filename}">' if (export_config.include_image and ex.image_filename) else ""
        front_html = ex.formatted_source_html()
        back_html = ex.formatted_target_html()
        explanation_html = (
            ex.explanation.replace("\n", "<br>")
            if (export_config.include_explanation and ex.explanation)
            else ""
        )

        if export_config.use_custom_note_type and set(self.CUSTOM_FIELDS).issubset(set(model_fields)):
            return {
                "Front": front_html,
                "Back": back_html,
                "Explanation": explanation_html,
                "Image": img_tag,
                "Audio": sound_tag,
                "Word": query,
            }

        # Mapeamento dinâmico para Note Types personalizados
        result: Dict[str, str] = {f: "" for f in model_fields}
        front_field = export_config.field_mapping.get("front") or (model_fields[0] if model_fields else "Front")
        back_field = export_config.field_mapping.get("back") or (
            model_fields[1] if len(model_fields) > 1 else front_field
        )
        exp_field = export_config.field_mapping.get("explanation") or ""
        img_field = export_config.field_mapping.get("image") or ""
        audio_field = export_config.field_mapping.get("audio") or front_field

        if front_field not in result and model_fields:
            front_field = model_fields[0]
        if back_field not in result and len(model_fields) > 1:
            back_field = model_fields[1]

        result[front_field] = front_html
        if back_field == front_field:
            result[back_field] = f"{front_html}<br><hr>{back_html}"
        else:
            result[back_field] = back_html

        if img_tag:
            if img_field and img_field in result:
                sep = "<br>" if result[img_field] else ""
                result[img_field] = f"{result[img_field]}{sep}{img_tag}"
            else:
                result[back_field] = f"{result[back_field]}<br><br>{img_tag}"

        if explanation_html:
            if exp_field and exp_field in result:
                sep = "<br><br>" if result[exp_field] else ""
                result[exp_field] = f"{result[exp_field]}{sep}{explanation_html}"
            else:
                result[back_field] = f"{result[back_field]}<br><br><small><i>{explanation_html}</i></small>"

        if sound_tag:
            target_audio_field = audio_field if audio_field in result else front_field
            sep = " " if result[target_audio_field] else ""
            result[target_audio_field] = f"{result[target_audio_field]}{sep}{sound_tag}"

        return result

    def _anki_connect_invoke(self, action: str, params: Optional[Dict[str, Any]] = None) -> Any:
        payload: Dict[str, Any] = {"action": action, "version": 6}
        if params is not None:
            payload["params"] = params
        try:
            req = urllib.request.Request(
                self.anki_connect_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                if body.get("error"):
                    print(f"Aviso AnkiConnect ({action}): {body['error']}")
                    return None
                return body.get("result")
        except Exception:
            return None
