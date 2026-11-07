from typing import Any, Dict, List
from ..controllers.main_controller import MainController
from ..enums.languages import OPENAI_TTS_VOICES
from ..utils.async_worker import run_async
from ..utils.qt_compat import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    notify_info,
    notify_warning,
    play_audio_bytes,
)


class SettingsDialog(QDialog):
    """Diálogo de configurações de IA, Text-to-Speech e mapeamento de campos do Anki."""

    def __init__(self, controller: MainController, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.controller = controller
        self.setWindowTitle("Configurações - Reverso & AI Add-on")
        self.setMinimumWidth(520)

        self._build_ui()
        self._load_current_values()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # --- ABA 1: Inteligência Artificial (LLM) ---
        ai_tab = QWidget()
        ai_layout = QFormLayout(ai_tab)

        self.ai_provider_combo = QComboBox()
        self.ai_provider_combo.addItem("Google Gemini", "gemini")
        self.ai_provider_combo.addItem("OpenAI (GPT)", "openai")
        self.ai_provider_combo.addItem("Groq", "groq")
        self.ai_provider_combo.addItem("Ollama (Local / Custom)", "ollama")
        self.ai_provider_combo.currentIndexChanged.connect(self._on_ai_provider_changed)
        ai_layout.addRow("Provedor de IA:", self.ai_provider_combo)

        self.ai_api_key_input = QLineEdit()
        self.ai_api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.ai_api_key_input.setPlaceholderText("Cole sua chave de API aqui...")
        ai_layout.addRow("Chave de API (LLM):", self.ai_api_key_input)

        self.ai_model_input = QLineEdit()
        self.ai_model_input.setPlaceholderText("Ex: gemini-2.5-flash, gpt-4o-mini, llama-3.3-70b-versatile")
        ai_layout.addRow("Modelo da IA:", self.ai_model_input)

        self.ai_base_url_input = QLineEdit()
        self.ai_base_url_input.setPlaceholderText("Opcional (ex: http://localhost:11434/v1)")
        ai_layout.addRow("URL Base Customizada:", self.ai_base_url_input)

        self.ai_count_spin = QSpinBox()
        self.ai_count_spin.setRange(1, 15)
        self.ai_count_spin.setValue(5)
        ai_layout.addRow("Frases geradas por vez:", self.ai_count_spin)

        self.tabs.addTab(ai_tab, "Inteligência Artificial")

        # --- ABA 2: Text-to-Speech (TTS) ---
        tts_tab = QWidget()
        tts_layout = QFormLayout(tts_tab)

        self.tts_provider_combo = QComboBox()
        self.tts_provider_combo.addItem("Gratuito (Voz Neural / Sem API Key)", "free_neural")
        self.tts_provider_combo.addItem("OpenAI Audio TTS", "openai")
        self.tts_provider_combo.addItem("Google Gemini Audio TTS", "gemini")
        self.tts_provider_combo.addItem("ElevenLabs Multilingual TTS", "elevenlabs")
        tts_layout.addRow("Motor de Voz (TTS):", self.tts_provider_combo)

        self.tts_api_key_input = QLineEdit()
        self.tts_api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.tts_api_key_input.setPlaceholderText("Deixe em branco para usar a mesma chave da aba IA")
        tts_layout.addRow("Chave de API (TTS):", self.tts_api_key_input)

        self.tts_model_input = QLineEdit()
        self.tts_model_input.setPlaceholderText("Ex: gpt-4o-mini-tts ou tts-1")
        tts_layout.addRow("Modelo TTS (OpenAI):", self.tts_model_input)

        self.tts_voice_combo = QComboBox()
        self.tts_voice_combo.addItems(OPENAI_TTS_VOICES)
        tts_layout.addRow("Voz OpenAI:", self.tts_voice_combo)

        self.elevenlabs_voice_input = QLineEdit()
        self.elevenlabs_voice_input.setPlaceholderText("Ex: 21m00Tcm4TlvDq8ikWAM")
        tts_layout.addRow("Voice ID (ElevenLabs):", self.elevenlabs_voice_input)

        self.test_tts_button = QPushButton("Testar Voz")
        self.test_tts_button.clicked.connect(self._on_test_tts)
        tts_layout.addRow("", self.test_tts_button)

        self.tabs.addTab(tts_tab, "Áudio (TTS)")

        # --- ABA 3: Formato do Card no Anki ---
        anki_tab = QWidget()
        anki_layout = QVBoxLayout(anki_tab)

        self.use_custom_model_check = QCheckBox(
            "Usar modelo de nota automático 'Reverso AI Card' (Recomendado)"
        )
        self.use_custom_model_check.toggled.connect(self._on_custom_model_toggled)
        anki_layout.addWidget(self.use_custom_model_check)

        self.mapping_group = QGroupBox("Mapeamento Manual (para Note Types personalizados)")
        map_form = QFormLayout(self.mapping_group)

        self.note_type_combo = QComboBox()
        self.note_type_combo.currentTextChanged.connect(self._on_note_type_changed)
        map_form.addRow("Note Type:", self.note_type_combo)

        self.front_field_combo = QComboBox()
        map_form.addRow("Campo da Frase (Frente):", self.front_field_combo)

        self.back_field_combo = QComboBox()
        map_form.addRow("Campo da Tradução (Verso):", self.back_field_combo)

        self.exp_field_combo = QComboBox()
        map_form.addRow("Campo da Explicação:", self.exp_field_combo)

        self.audio_field_combo = QComboBox()
        map_form.addRow("Campo do Áudio:", self.audio_field_combo)

        anki_layout.addWidget(self.mapping_group)
        anki_layout.addStretch(1)

        self.tabs.addTab(anki_tab, "Campos do Anki")

        # --- Botões Inferiores ---
        btn_layout = QHBoxLayout()
        btn_layout.addStretch(1)
        self.cancel_btn = QPushButton("Cancelar")
        self.save_btn = QPushButton("Salvar Configurações")
        self.save_btn.setDefault(True)
        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        main_layout.addLayout(btn_layout)

    def _load_current_values(self) -> None:
        cfg = self.controller.config.get_all()

        ai_provider = cfg.get("ai_provider", "gemini")
        idx = self.ai_provider_combo.findData(ai_provider)
        if idx >= 0:
            self.ai_provider_combo.setCurrentIndex(idx)

        self.ai_api_key_input.setText(cfg.get("ai_api_key", ""))
        self.ai_model_input.setText(cfg.get("ai_model", "gemini-2.5-flash"))
        self.ai_base_url_input.setText(cfg.get("ai_base_url", ""))
        self.ai_count_spin.setValue(int(cfg.get("ai_examples_count", 5)))

        tts_provider = cfg.get("tts_provider", "free_neural")
        t_idx = self.tts_provider_combo.findData(tts_provider)
        if t_idx >= 0:
            self.tts_provider_combo.setCurrentIndex(t_idx)

        self.tts_api_key_input.setText(cfg.get("tts_api_key", ""))
        self.tts_model_input.setText(cfg.get("tts_model", "gpt-4o-mini-tts"))

        voice = cfg.get("tts_voice", "alloy")
        v_idx = self.tts_voice_combo.findText(voice)
        if v_idx >= 0:
            self.tts_voice_combo.setCurrentIndex(v_idx)

        self.elevenlabs_voice_input.setText(cfg.get("elevenlabs_voice_id", "21m00Tcm4TlvDq8ikWAM"))

        note_types = self.controller.listar_note_types()
        self.note_type_combo.clear()
        self.note_type_combo.addItems(note_types)

        saved_model = cfg.get("default_note_type", "")
        if saved_model and saved_model in note_types:
            self.note_type_combo.setCurrentText(saved_model)

        use_custom = bool(cfg.get("use_custom_note_type", True))
        self.use_custom_model_check.setChecked(use_custom)
        self._on_custom_model_toggled(use_custom)
        self._on_note_type_changed(self.note_type_combo.currentText())

    def _on_ai_provider_changed(self) -> None:
        provider = self.ai_provider_combo.currentData()
        defaults = {
            "gemini": "gemini-2.5-flash",
            "openai": "gpt-4o-mini",
            "groq": "llama-3.3-70b-versatile",
            "ollama": "llama3.2",
        }
        current_model = self.ai_model_input.text().strip()
        if not current_model or current_model in defaults.values():
            self.ai_model_input.setText(defaults.get(provider, "gemini-2.5-flash"))

    def _on_custom_model_toggled(self, checked: bool) -> None:
        self.mapping_group.setEnabled(not checked)

    def _on_note_type_changed(self, model_name: str) -> None:
        if not model_name:
            return
        fields: List[str] = self.controller.listar_campos_note_type(model_name)
        mapping: Dict[str, str] = self.controller.config.get("field_mapping", {}) or {}

        for combo, key, allow_empty in (
            (self.front_field_combo, "front", False),
            (self.back_field_combo, "back", False),
            (self.exp_field_combo, "explanation", True),
            (self.audio_field_combo, "audio", False),
        ):
            combo.clear()
            if allow_empty:
                combo.addItem("(Anexar ao Verso)", "")
            for f in fields:
                combo.addItem(f, f)

            desired = mapping.get(key, "")
            if desired and desired in fields:
                combo.setCurrentText(desired)
            elif not allow_empty and fields:
                default_idx = 1 if (key == "back" and len(fields) > 1) else 0
                combo.setCurrentIndex(default_idx)

    def _collect_values(self) -> Dict[str, Any]:
        return {
            "ai_provider": self.ai_provider_combo.currentData(),
            "ai_api_key": self.ai_api_key_input.text().strip(),
            "ai_model": self.ai_model_input.text().strip(),
            "ai_base_url": self.ai_base_url_input.text().strip(),
            "ai_examples_count": self.ai_count_spin.value(),
            "tts_provider": self.tts_provider_combo.currentData(),
            "tts_api_key": self.tts_api_key_input.text().strip(),
            "tts_model": self.tts_model_input.text().strip(),
            "tts_voice": self.tts_voice_combo.currentText(),
            "elevenlabs_voice_id": self.elevenlabs_voice_input.text().strip(),
            "use_custom_note_type": self.use_custom_model_check.isChecked(),
            "default_note_type": self.note_type_combo.currentText(),
            "field_mapping": {
                "front": self.front_field_combo.currentData() or self.front_field_combo.currentText(),
                "back": self.back_field_combo.currentData() or self.back_field_combo.currentText(),
                "explanation": self.exp_field_combo.currentData() or "",
                "audio": self.audio_field_combo.currentData() or self.audio_field_combo.currentText(),
            },
        }

    def _on_test_tts(self) -> None:
        self.controller.salvar_configuracoes(self._collect_values())
        self.test_tts_button.setEnabled(False)
        self.test_tts_button.setText("Gerando áudio...")

        def _task():
            return self.controller.tts.synthesize(
                "This is a voice test for your Anki flashcards.", "english"
            )

        def _on_ok(res):
            audio_bytes, filename = res
            play_audio_bytes(audio_bytes, filename)

        def _on_err(err_msg: str):
            notify_warning(f"Falha ao testar TTS:\n{err_msg.splitlines()[0]}", self)

        def _on_done():
            self.test_tts_button.setEnabled(True)
            self.test_tts_button.setText("Testar Voz")

        run_async(_task, on_result=_on_ok, on_error=_on_err, on_finished=_on_done)

    def _on_save(self) -> None:
        self.controller.salvar_configuracoes(self._collect_values())
        notify_info("Configurações salvas com sucesso.", self)
        self.accept()
