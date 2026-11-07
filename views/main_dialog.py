from typing import Callable, List, Optional
from ..controllers.main_controller import MainController
from ..enums.languages import AI_LEVELS, AI_STYLES
from ..models.example import ExampleItem, LookupResult
from ..models.note_config import NoteExportConfig
from ..utils.async_worker import run_async
from ..utils.qt_compat import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPixmap,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    Qt,
    QVBoxLayout,
    QWidget,
    notify_info,
    notify_warning,
    play_audio_bytes,
)
from .image_dialog import ImagePickerDialog
from .settings_dialog import SettingsDialog


class EditExampleDialog(QDialog):
    """Permite ao usuário editar a frase, a tradução ou a nota explicativa antes de enviar ao Anki."""

    def __init__(self, example: ExampleItem, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.example = example
        self.setWindowTitle("Editar Exemplo")
        self.setMinimumWidth(480)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.source_edit = QLineEdit(example.source_html or example.source)
        self.target_edit = QLineEdit(example.target_html or example.target)
        self.explanation_edit = QPlainTextEdit(example.explanation)
        self.explanation_edit.setFixedHeight(90)

        form.addRow("Frase (use <em>...</em> p/ grifar):", self.source_edit)
        form.addRow("Tradução:", self.target_edit)
        form.addRow("Explicação / Notas:", self.explanation_edit)
        layout.addLayout(form)

        btns = QHBoxLayout()
        btns.addStretch(1)
        cancel_btn = QPushButton("Cancelar")
        save_btn = QPushButton("Salvar")
        save_btn.setDefault(True)
        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self._on_save)
        btns.addWidget(cancel_btn)
        btns.addWidget(save_btn)
        layout.addLayout(btns)

    def _on_save(self) -> None:
        src_html = self.source_edit.text().strip()
        trg_html = self.target_edit.text().strip()
        if src_html:
            self.example.source_html = src_html
            self.example.source = ExampleItem._strip_tags(src_html)
            self.example.audio_bytes = None
            self.example.audio_filename = ""
        if trg_html:
            self.example.target_html = trg_html
            self.example.target = ExampleItem._strip_tags(trg_html)
        self.example.explanation = self.explanation_edit.toPlainText().strip()
        self.accept()


class ExampleRowWidget(QFrame):
    """Widget customizado para exibir uma frase, sua tradução, explicação, imagem e botões de ação."""

    def __init__(
        self,
        example: ExampleItem,
        on_listen: Callable[["ExampleRowWidget"], None],
        on_explain: Callable[["ExampleRowWidget"], None],
        on_image: Callable[["ExampleRowWidget"], None],
        on_edit: Callable[["ExampleRowWidget"], None],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.example = example
        self.on_listen = on_listen
        self.on_explain = on_explain
        self.on_image = on_image
        self.on_edit = on_edit

        self.setFrameShape(QFrame.Shape.StyledPanel)
        self._build_ui()
        self.refresh_display()

    def _build_ui(self) -> None:
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(10, 8, 10, 8)
        root_layout.setSpacing(10)

        self.checkbox = QCheckBox()
        root_layout.addWidget(self.checkbox, alignment=Qt.AlignmentFlag.AlignTop)

        # Miniatura da imagem anexada (visível apenas quando há imagem)
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(88, 66)
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_label.setStyleSheet(
            "border: 1px solid #d1d5db; border-radius: 6px; background-color: #f3f4f6;"
        )
        self.thumb_label.setVisible(False)
        root_layout.addWidget(self.thumb_label, alignment=Qt.AlignmentFlag.AlignTop)

        # Coluna central com textos
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)

        header_layout = QHBoxLayout()
        self.origin_badge = QLabel()
        self.origin_badge.setStyleSheet(
            "font-size: 9pt; font-weight: bold; color: #4b5563; "
            "background-color: #e5e7eb; padding: 1px 6px; border-radius: 4px;"
        )
        header_layout.addWidget(self.origin_badge)
        header_layout.addStretch(1)
        text_layout.addLayout(header_layout)

        self.source_label = QLabel()
        self.source_label.setTextFormat(Qt.TextFormat.RichText)
        self.source_label.setWordWrap(True)
        self.source_label.setStyleSheet("font-size: 12pt; font-weight: 600;")
        self.source_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self.target_label = QLabel()
        self.target_label.setTextFormat(Qt.TextFormat.RichText)
        self.target_label.setWordWrap(True)
        self.target_label.setStyleSheet("font-size: 11pt; color: #4b5563; font-style: italic;")
        self.target_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self.explanation_label = QLabel()
        self.explanation_label.setWordWrap(True)
        self.explanation_label.setStyleSheet(
            "font-size: 10pt; color: #1e40af; background-color: #eff6ff; "
            "padding: 6px; border-radius: 4px; border-left: 3px solid #3b82f6;"
        )
        self.explanation_label.setVisible(False)

        text_layout.addWidget(self.source_label)
        text_layout.addWidget(self.target_label)
        text_layout.addWidget(self.explanation_label)
        root_layout.addLayout(text_layout, stretch=1)

        # Coluna direita com botões de ação (sem emojis)
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(4)

        self.listen_btn = QPushButton("Ouvir")
        self.listen_btn.setFixedWidth(115)
        self.listen_btn.clicked.connect(lambda: self.on_listen(self))

        self.explain_btn = QPushButton("Explicar com IA")
        self.explain_btn.setFixedWidth(115)
        self.explain_btn.clicked.connect(lambda: self.on_explain(self))

        self.image_btn = QPushButton("Imagem")
        self.image_btn.setFixedWidth(115)
        self.image_btn.clicked.connect(lambda: self.on_image(self))

        self.edit_btn = QPushButton("Editar")
        self.edit_btn.setFixedWidth(115)
        self.edit_btn.clicked.connect(lambda: self.on_edit(self))

        actions_layout.addWidget(self.listen_btn)
        actions_layout.addWidget(self.explain_btn)
        actions_layout.addWidget(self.image_btn)
        actions_layout.addWidget(self.edit_btn)
        actions_layout.addStretch(1)

        root_layout.addLayout(actions_layout)

    def refresh_display(self) -> None:
        badge_parts = ["IA" if self.example.origin == "ai" else "Reverso"]
        if self.example.audio_bytes:
            badge_parts.append("Áudio Pronto")
        if self.example.image_bytes:
            badge_parts.append("Com Imagem")
        self.origin_badge.setText(" | ".join(badge_parts))
        self.source_label.setText(self.example.formatted_source_html())
        self.target_label.setText(self.example.formatted_target_html())

        if self.example.explanation:
            self.explanation_label.setText(f"Nota: {self.example.explanation}")
            self.explanation_label.setVisible(True)
        else:
            self.explanation_label.setVisible(False)

        if self.example.image_bytes:
            pix = QPixmap()
            if pix.loadFromData(self.example.image_bytes):
                self.thumb_label.setPixmap(
                    pix.scaled(
                        84,
                        62,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
                self.thumb_label.setVisible(True)
            else:
                self.thumb_label.setVisible(False)
        else:
            self.thumb_label.clear()
            self.thumb_label.setVisible(False)


class ReversoMainDialog(QDialog):
    """Janela principal do Add-on Reverso Context + IA + TTS + Imagens para o Anki."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        initial_query: str = "",
    ) -> None:
        super().__init__(parent)
        self.controller = MainController()
        self.current_examples: List[ExampleItem] = []
        self.current_query: str = initial_query.strip()

        self.setWindowTitle("Reverso Context & AI Lookup - Anki Add-on")
        self.resize(900, 700)

        self._build_ui()
        self._populate_initial_data()

        if self.current_query:
            self.search_input.setText(self.current_query)
            self.on_search_reverso()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)

        # --- Linha 1: Deck, Idiomas e Configurações ---
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("Deck:"))
        self.deck_combo = QComboBox()
        self.deck_combo.setMinimumWidth(180)
        top_bar.addWidget(self.deck_combo, stretch=1)

        top_bar.addWidget(QLabel("De:"))
        self.source_lang_combo = QComboBox()
        top_bar.addWidget(self.source_lang_combo)

        self.swap_lang_btn = QPushButton("Inverter")
        self.swap_lang_btn.setToolTip("Inverter idiomas de origem e destino")
        self.swap_lang_btn.clicked.connect(self._on_swap_languages)
        top_bar.addWidget(self.swap_lang_btn)

        top_bar.addWidget(QLabel("Para:"))
        self.target_lang_combo = QComboBox()
        top_bar.addWidget(self.target_lang_combo)

        self.settings_btn = QPushButton("Configurações")
        self.settings_btn.clicked.connect(self._on_open_settings)
        top_bar.addWidget(self.settings_btn)

        main_layout.addLayout(top_bar)

        # --- Linha 2: Barra de Busca e Geração por IA ---
        search_bar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Digite uma palavra ou expressão para buscar ou gerar frases...")
        self.search_input.returnPressed.connect(self.on_search_reverso)
        search_bar.addWidget(self.search_input, stretch=1)

        self.search_reverso_btn = QPushButton("Buscar no Reverso")
        self.search_reverso_btn.clicked.connect(self.on_search_reverso)
        search_bar.addWidget(self.search_reverso_btn)

        search_bar.addWidget(QLabel("Nível:"))
        self.level_combo = QComboBox()
        self.level_combo.addItems(AI_LEVELS)
        search_bar.addWidget(self.level_combo)

        self.style_combo = QComboBox()
        self.style_combo.addItems(AI_STYLES)
        search_bar.addWidget(self.style_combo)

        self.generate_ai_btn = QPushButton("Gerar com IA")
        self.generate_ai_btn.clicked.connect(self.on_generate_ai)
        search_bar.addWidget(self.generate_ai_btn)

        main_layout.addLayout(search_bar)

        # --- Linha 3: Traduções / Sinônimos Diretos ---
        self.translations_label = QLabel("Traduções: (faça uma busca para ver os significados)")
        self.translations_label.setWordWrap(True)
        self.translations_label.setStyleSheet(
            "padding: 6px 10px; background-color: #f3f4f6; color: #1f2937; "
            "border-radius: 6px; font-size: 10.5pt;"
        )
        main_layout.addWidget(self.translations_label)

        # --- Linha 4: Lista de Exemplos ---
        self.examples_list = QListWidget()
        self.examples_list.setSpacing(4)
        self.examples_list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        main_layout.addWidget(self.examples_list, stretch=1)

        # --- Linha 5: Opções de Exportação e Botões Finais ---
        options_bar = QHBoxLayout()
        self.include_audio_check = QCheckBox("Gerar e anexar áudio (TTS) ao enviar")
        self.include_audio_check.setChecked(
            bool(self.controller.config.get("auto_generate_tts_on_send", True))
        )
        self.include_explanation_check = QCheckBox("Incluir explicação no verso")
        self.include_explanation_check.setChecked(True)
        self.include_image_check = QCheckBox("Incluir imagens anexadas")
        self.include_image_check.setChecked(True)

        options_bar.addWidget(self.include_audio_check)
        options_bar.addWidget(self.include_explanation_check)
        options_bar.addWidget(self.include_image_check)
        options_bar.addStretch(1)

        self.select_all_btn = QPushButton("Selecionar Todos")
        self.select_all_btn.clicked.connect(self._on_toggle_select_all)
        self.clear_btn = QPushButton("Limpar Lista")
        self.clear_btn.clicked.connect(self.on_clear_list)
        self.send_btn = QPushButton("Enviar Selecionados para o Anki")
        self.send_btn.setStyleSheet("font-weight: bold; padding: 6px 14px;")
        self.send_btn.clicked.connect(self.on_send_to_anki)

        options_bar.addWidget(self.select_all_btn)
        options_bar.addWidget(self.clear_btn)
        options_bar.addWidget(self.send_btn)
        main_layout.addLayout(options_bar)

        # --- Linha 6: Status e Barra de Progresso ---
        status_bar = QHBoxLayout()
        self.status_label = QLabel("Pronto.")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedWidth(180)
        self.progress_bar.setVisible(False)
        status_bar.addWidget(self.status_label, stretch=1)
        status_bar.addWidget(self.progress_bar)
        main_layout.addLayout(status_bar)

    def _populate_initial_data(self) -> None:
        decks = self.controller.listar_decks()
        self.deck_combo.clear()
        self.deck_combo.addItems(decks)

        default_deck = self.controller.config.get("default_deck", "")
        if default_deck and default_deck in decks:
            self.deck_combo.setCurrentText(default_deck)

        langs = self.controller.get_languages()
        self.source_lang_combo.clear()
        self.target_lang_combo.clear()
        for code, label in langs:
            self.source_lang_combo.addItem(label, code)
            self.target_lang_combo.addItem(label, code)

        src_default = self.controller.config.get("default_source_lang", "english")
        trg_default = self.controller.config.get("default_target_lang", "portuguese")
        s_idx = self.source_lang_combo.findData(src_default)
        t_idx = self.target_lang_combo.findData(trg_default)
        if s_idx >= 0:
            self.source_lang_combo.setCurrentIndex(s_idx)
        if t_idx >= 0:
            self.target_lang_combo.setCurrentIndex(t_idx)

        lvl = self.controller.config.get("ai_level", "B1")
        l_idx = self.level_combo.findText(lvl)
        if l_idx >= 0:
            self.level_combo.setCurrentIndex(l_idx)

        style = self.controller.config.get("ai_style", "Conversação natural")
        st_idx = self.style_combo.findText(style)
        if st_idx >= 0:
            self.style_combo.setCurrentIndex(st_idx)

    def refresh_decks(self) -> None:
        current = self.deck_combo.currentText()
        decks = self.controller.listar_decks()
        self.deck_combo.clear()
        self.deck_combo.addItems(decks)
        if current and current in decks:
            self.deck_combo.setCurrentText(current)

    def _set_busy(self, busy: bool, message: str = "Pronto.") -> None:
        self.status_label.setText(message)
        self.progress_bar.setVisible(busy)
        self.search_reverso_btn.setEnabled(not busy)
        self.generate_ai_btn.setEnabled(not busy)
        self.send_btn.setEnabled(not busy)

    def _save_session_preferences(self) -> None:
        self.controller.salvar_configuracoes(
            {
                "default_deck": self.deck_combo.currentText(),
                "default_source_lang": self.source_lang_combo.currentData(),
                "default_target_lang": self.target_lang_combo.currentData(),
                "ai_level": self.level_combo.currentText(),
                "ai_style": self.style_combo.currentText(),
                "auto_generate_tts_on_send": self.include_audio_check.isChecked(),
            }
        )

    def _on_swap_languages(self) -> None:
        s_idx = self.source_lang_combo.currentIndex()
        t_idx = self.target_lang_combo.currentIndex()
        self.source_lang_combo.setCurrentIndex(t_idx)
        self.target_lang_combo.setCurrentIndex(s_idx)

    def _on_open_settings(self) -> None:
        dlg = SettingsDialog(self.controller, self)
        dlg.exec()

    def on_search_reverso(self) -> None:
        query = self.search_input.text().strip()
        if not query:
            notify_warning("Digite uma palavra ou expressão para buscar.", self)
            return

        self.current_query = query
        source_lang = self.source_lang_combo.currentData()
        target_lang = self.target_lang_combo.currentData()
        self._save_session_preferences()

        self._set_busy(True, f"Buscando '{query}' no Reverso Context...")

        def _task() -> LookupResult:
            return self.controller.buscar_reverso(query, source_lang, target_lang)

        def _on_result(result: LookupResult) -> None:
            if result.error:
                notify_warning(result.error, self)
                self._set_busy(False, "Erro na busca do Reverso.")
                return
            self._display_lookup_result(result, append=False)
            self._set_busy(False, f"{len(result.examples)} exemplos carregados do Reverso.")

        def _on_error(err: str) -> None:
            notify_warning(f"Erro ao buscar no Reverso:\n{err.splitlines()[0]}", self)
            self._set_busy(False, "Falha na busca.")

        run_async(_task, on_result=_on_result, on_error=_on_error)

    def on_generate_ai(self) -> None:
        query = self.search_input.text().strip()
        if not query:
            notify_warning("Digite uma palavra ou expressão para gerar frases com IA.", self)
            return

        self.current_query = query
        source_lang = self.source_lang_combo.currentData()
        target_lang = self.target_lang_combo.currentData()
        level = self.level_combo.currentText()
        style = self.style_combo.currentText()
        count = int(self.controller.config.get("ai_examples_count", 5))
        self._save_session_preferences()

        self._set_busy(True, f"Gerando {count} frases com IA ({level} - {style})...")

        def _task() -> LookupResult:
            return self.controller.gerar_exemplos_ia(
                palavra=query,
                source_lang=source_lang,
                target_lang=target_lang,
                level=level,
                style=style,
                count=count,
            )

        def _on_result(result: LookupResult) -> None:
            if result.error:
                notify_warning(result.error, self)
                self._set_busy(False, "Falha ao gerar frases com IA.")
                return
            self._display_lookup_result(result, append=bool(self.current_examples))
            self._set_busy(False, f"{len(result.examples)} frases geradas com IA.")

        def _on_error(err: str) -> None:
            notify_warning(f"Erro na geração com IA:\n{err.splitlines()[0]}", self)
            self._set_busy(False, "Erro ao chamar IA.")

        run_async(_task, on_result=_on_result, on_error=_on_error)

    def _display_lookup_result(self, result: LookupResult, append: bool = False) -> None:
        if result.translations:
            joined = " • ".join(result.translations[:10])
            self.translations_label.setText(f"<b>Traduções para '{result.query}':</b> {joined}")

        if not append:
            self.examples_list.clear()
            self.current_examples = []

        for ex in result.examples:
            self.current_examples.append(ex)
            self._add_example_row(ex, prepend=append)

    def _add_example_row(self, ex: ExampleItem, prepend: bool = False) -> None:
        row_widget = ExampleRowWidget(
            example=ex,
            on_listen=self._on_row_listen,
            on_explain=self._on_row_explain,
            on_image=self._on_row_image,
            on_edit=self._on_row_edit,
            parent=self.examples_list,
        )
        item = QListWidgetItem()
        item.setSizeHint(row_widget.sizeHint())
        if prepend:
            self.examples_list.insertItem(0, item)
        else:
            self.examples_list.addItem(item)
        self.examples_list.setItemWidget(item, row_widget)

    def _update_row_size(self, row_widget: ExampleRowWidget) -> None:
        row_widget.refresh_display()
        row_widget.adjustSize()
        for i in range(self.examples_list.count()):
            item = self.examples_list.item(i)
            if item and self.examples_list.itemWidget(item) is row_widget:
                item.setSizeHint(row_widget.sizeHint())
                break

    def _on_row_listen(self, row_widget: ExampleRowWidget) -> None:
        source_lang = self.source_lang_combo.currentData()
        row_widget.listen_btn.setEnabled(False)
        row_widget.listen_btn.setText("Carregando...")
        self.status_label.setText("Sintetizando voz (TTS)...")

        def _task():
            return self.controller.gerar_audio_exemplo(row_widget.example, source_lang)

        def _on_ok(res):
            audio_bytes, filename = res
            row_widget.refresh_display()
            play_audio_bytes(audio_bytes, filename)
            self.status_label.setText("Reproduzindo áudio.")

        def _on_err(err: str):
            notify_warning(f"Erro ao gerar áudio (TTS):\n{err.splitlines()[0]}", self)
            self.status_label.setText("Falha no TTS.")

        def _on_done():
            row_widget.listen_btn.setEnabled(True)
            row_widget.listen_btn.setText("Ouvir")

        run_async(_task, on_result=_on_ok, on_error=_on_err, on_finished=_on_done)

    def _on_row_explain(self, row_widget: ExampleRowWidget) -> None:
        source_lang = self.source_lang_combo.currentData()
        target_lang = self.target_lang_combo.currentData()
        query = self.current_query or self.search_input.text().strip()

        row_widget.explain_btn.setEnabled(False)
        row_widget.explain_btn.setText("Explicando...")
        self.status_label.setText("Gerando explicação contextual com IA...")

        def _task() -> str:
            return self.controller.explicar_exemplo_ia(
                palavra=query,
                example=row_widget.example,
                source_lang=source_lang,
                target_lang=target_lang,
            )

        def _on_ok(_explanation: str) -> None:
            self._update_row_size(row_widget)
            self.status_label.setText("Explicação gerada com sucesso.")

        def _on_err(err: str) -> None:
            notify_warning(f"Não foi possível gerar a explicação:\n{err.splitlines()[0]}", self)
            self.status_label.setText("Erro ao gerar explicação.")

        def _on_done() -> None:
            row_widget.explain_btn.setEnabled(True)
            row_widget.explain_btn.setText("Explicar com IA")

        run_async(_task, on_result=_on_ok, on_error=_on_err, on_finished=_on_done)

    def _on_row_image(self, row_widget: ExampleRowWidget) -> None:
        query = self.current_query or self.search_input.text().strip()
        dlg = ImagePickerDialog(
            controller=self.controller,
            example=row_widget.example,
            default_query=query,
            parent=self,
        )
        if dlg.exec():
            self._update_row_size(row_widget)

    def _on_row_edit(self, row_widget: ExampleRowWidget) -> None:
        dlg = EditExampleDialog(row_widget.example, self)
        if dlg.exec():
            self._update_row_size(row_widget)

    def _on_toggle_select_all(self) -> None:
        widgets: List[ExampleRowWidget] = []
        for i in range(self.examples_list.count()):
            item = self.examples_list.item(i)
            w = self.examples_list.itemWidget(item) if item else None
            if isinstance(w, ExampleRowWidget):
                widgets.append(w)

        if not widgets:
            return

        all_checked = all(w.checkbox.isChecked() for w in widgets)
        for w in widgets:
            w.checkbox.setChecked(not all_checked)

    def on_clear_list(self) -> None:
        self.examples_list.clear()
        self.current_examples = []
        self.translations_label.setText("Traduções: (lista limpa)")
        self.status_label.setText("Lista de exemplos limpa.")

    def on_send_to_anki(self) -> None:
        selected: List[ExampleItem] = []
        for i in range(self.examples_list.count()):
            item = self.examples_list.item(i)
            w = self.examples_list.itemWidget(item) if item else None
            if isinstance(w, ExampleRowWidget) and w.checkbox.isChecked():
                selected.append(w.example)

        if not selected:
            notify_warning("Selecione pelo menos uma frase antes de enviar para o Anki.", self)
            return

        deck_name = self.deck_combo.currentText().strip() or "Default"
        source_lang = self.source_lang_combo.currentData()
        query = self.current_query or self.search_input.text().strip()
        self._save_session_preferences()

        cfg = self.controller.config.get_all()
        export_config = NoteExportConfig(
            deck_name=deck_name,
            note_type_name=cfg.get("default_note_type") or "Reverso AI Card",
            use_custom_note_type=bool(cfg.get("use_custom_note_type", True)),
            include_audio=self.include_audio_check.isChecked(),
            include_explanation=self.include_explanation_check.isChecked(),
            include_image=self.include_image_check.isChecked(),
            tags=["reverso-ai", source_lang, deck_name.replace(" ", "_")],
            field_mapping=cfg.get("field_mapping") or {},
        )

        self._set_busy(True, f"Enviando {len(selected)} card(s) para o deck '{deck_name}'...")

        def _task():
            return self.controller.enviar_para_anki(
                exemplos=selected,
                source_lang=source_lang,
                export_config=export_config,
                query=query,
            )

        def _on_ok(res):
            added_count, warnings = res
            for i in range(self.examples_list.count()):
                item = self.examples_list.item(i)
                w = self.examples_list.itemWidget(item) if item else None
                if isinstance(w, ExampleRowWidget) and w.checkbox.isChecked():
                    w.checkbox.setChecked(False)
                    w.refresh_display()

            msg = f"{added_count} card(s) adicionado(s) ao deck '{deck_name}'!"
            if warnings:
                msg += "\n\nAvisos:\n- " + "\n- ".join(warnings[:3])
                notify_warning(msg, self)
            else:
                notify_info(msg, self)
            self._set_busy(False, f"{added_count} card(s) enviado(s) com sucesso.")

        def _on_err(err: str):
            notify_warning(f"Falha ao criar cards no Anki:\n{err.splitlines()[0]}", self)
            self._set_busy(False, "Erro ao enviar para o Anki.")

        run_async(_task, on_result=_on_ok, on_error=_on_err)
