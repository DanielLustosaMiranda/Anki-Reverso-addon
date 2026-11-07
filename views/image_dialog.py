from typing import List, Optional
from ..controllers.main_controller import MainController
from ..models.example import ExampleItem, WebImageResult
from ..utils.async_worker import run_async
from ..utils.qt_compat import (
    QApplication,
    QBuffer,
    QByteArray,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QIODevice,
    QLabel,
    QLineEdit,
    QPixmap,
    QProgressBar,
    QPushButton,
    QScrollArea,
    Qt,
    QVBoxLayout,
    QWidget,
    notify_warning,
)


class ImagePickerDialog(QDialog):
    """Diálogo para anexar imagem ao card (Busca Web, Geração por IA, Área de Transferência ou Arquivo)."""

    def __init__(
        self,
        controller: MainController,
        example: ExampleItem,
        default_query: str = "",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.controller = controller
        self.example = example
        self.selected_bytes: Optional[bytes] = example.image_bytes
        self.selected_filename: str = example.image_filename

        self.setWindowTitle("Adicionar Imagem ao Card")
        self.resize(680, 560)

        self._build_ui(default_query)
        self._refresh_preview()

    def _build_ui(self, default_query: str) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setSpacing(10)

        # --- Seção 1: Pré-visualização da Imagem Selecionada + Ações Locais ---
        preview_group = QGroupBox("Imagem Atual do Card")
        preview_layout = QHBoxLayout(preview_group)

        self.preview_label = QLabel("Nenhuma imagem selecionada")
        self.preview_label.setFixedSize(160, 120)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet(
            "border: 1px dashed #9ca3af; border-radius: 6px; background-color: #f9fafb; color: #6b7280;"
        )
        preview_layout.addWidget(self.preview_label)

        local_btns_layout = QVBoxLayout()
        self.paste_btn = QPushButton("Colar da Área de Transferência")
        self.paste_btn.clicked.connect(self._on_paste_clipboard)

        self.file_btn = QPushButton("Escolher Arquivo do Computador...")
        self.file_btn.clicked.connect(self._on_choose_file)

        self.remove_btn = QPushButton("Remover Imagem")
        self.remove_btn.clicked.connect(self._on_remove_image)

        local_btns_layout.addWidget(self.paste_btn)
        local_btns_layout.addWidget(self.file_btn)
        local_btns_layout.addWidget(self.remove_btn)
        local_btns_layout.addStretch(1)
        preview_layout.addLayout(local_btns_layout, stretch=1)

        root_layout.addWidget(preview_group)

        # --- Seção 2: Busca na Web e Geração com IA ---
        search_group = QGroupBox("Buscar na Web ou Gerar com IA")
        search_vlayout = QVBoxLayout(search_group)

        web_row = QHBoxLayout()
        self.web_search_input = QLineEdit(default_query or self.example.source)
        self.web_search_input.setPlaceholderText("Digite um termo para buscar fotos/ilustrações...")
        self.web_search_input.returnPressed.connect(self._on_search_web)
        self.web_search_btn = QPushButton("Buscar Imagens na Web")
        self.web_search_btn.clicked.connect(self._on_search_web)
        web_row.addWidget(self.web_search_input, stretch=1)
        web_row.addWidget(self.web_search_btn)
        search_vlayout.addLayout(web_row)

        ai_row = QHBoxLayout()
        self.ai_prompt_input = QLineEdit(self.example.source)
        self.ai_prompt_input.setPlaceholderText("Descreva a cena ou frase para gerar com IA...")
        self.ai_generate_btn = QPushButton("Gerar Imagem com IA")
        self.ai_generate_btn.clicked.connect(self._on_generate_ai_image)
        ai_row.addWidget(self.ai_prompt_input, stretch=1)
        ai_row.addWidget(self.ai_generate_btn)
        search_vlayout.addLayout(ai_row)

        root_layout.addWidget(search_group)

        # --- Seção 3: Grade de Resultados de Imagens ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(10)
        self.scroll_area.setWidget(self.grid_container)
        root_layout.addWidget(self.scroll_area, stretch=1)

        # --- Seção 4: Status e Botões de Confirmação ---
        bottom_bar = QHBoxLayout()
        self.status_label = QLabel("Pronto.")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedWidth(140)
        self.progress_bar.setVisible(False)

        self.cancel_btn = QPushButton("Cancelar")
        self.confirm_btn = QPushButton("Confirmar Imagem")
        self.confirm_btn.setDefault(True)
        self.cancel_btn.clicked.connect(self.reject)
        self.confirm_btn.clicked.connect(self._on_confirm)

        bottom_bar.addWidget(self.status_label, stretch=1)
        bottom_bar.addWidget(self.progress_bar)
        bottom_bar.addWidget(self.cancel_btn)
        bottom_bar.addWidget(self.confirm_btn)
        root_layout.addLayout(bottom_bar)

    def _set_busy(self, busy: bool, text: str) -> None:
        self.status_label.setText(text)
        self.progress_bar.setVisible(busy)
        self.web_search_btn.setEnabled(not busy)
        self.ai_generate_btn.setEnabled(not busy)

    def _refresh_preview(self) -> None:
        if self.selected_bytes:
            pixmap = QPixmap()
            if pixmap.loadFromData(self.selected_bytes):
                scaled = pixmap.scaled(
                    154,
                    114,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.preview_label.setPixmap(scaled)
                self.remove_btn.setEnabled(True)
                return

        self.preview_label.clear()
        self.preview_label.setText("Sem imagem")
        self.remove_btn.setEnabled(False)

    def _on_paste_clipboard(self) -> None:
        clipboard = QApplication.clipboard()
        if clipboard is None:
            return
        image = clipboard.image()
        if image is None or image.isNull():
            notify_warning("Nenhuma imagem encontrada na área de transferência.", self)
            return

        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        image.save(buffer, "PNG")
        raw_bytes = bytes(byte_array.data())
        if raw_bytes:
            self.selected_bytes = raw_bytes
            self.selected_filename = self.controller.images.make_filename(raw_bytes, ".png")
            self._refresh_preview()
            self.status_label.setText("Imagem colada da área de transferência.")

    def _on_choose_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Escolher Imagem",
            "",
            "Imagens (*.png *.jpg *.jpeg *.webp *.gif)",
        )
        if not file_path:
            return
        try:
            img_bytes, filename = self.controller.carregar_imagem_arquivo(file_path)
            self.selected_bytes = img_bytes
            self.selected_filename = filename
            self._refresh_preview()
            self.status_label.setText(f"Arquivo carregado: {filename}")
        except Exception as exc:
            notify_warning(f"Erro ao carregar imagem:\n{exc}", self)

    def _on_remove_image(self) -> None:
        self.selected_bytes = None
        self.selected_filename = ""
        self._refresh_preview()
        self.status_label.setText("Imagem removida.")

    def _clear_grid(self) -> None:
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child and child.widget():
                child.widget().deleteLater()

    def _on_search_web(self) -> None:
        query = self.web_search_input.text().strip()
        if not query:
            notify_warning("Digite uma palavra para buscar imagens.", self)
            return

        self._clear_grid()
        self._set_busy(True, f"Buscando imagens para '{query}'...")

        def _task() -> List[WebImageResult]:
            return self.controller.buscar_imagens_web(query, limit=6)

        def _on_ok(results: List[WebImageResult]) -> None:
            if not results:
                self._set_busy(False, "Nenhuma imagem encontrada para este termo.")
                return
            self._populate_grid(results)
            self._set_busy(False, f"{len(results)} imagens encontradas. Clique em 'Usar esta' para selecionar.")

        def _on_err(err: str) -> None:
            notify_warning(f"Erro ao buscar imagens:\n{err.splitlines()[0]}", self)
            self._set_busy(False, "Falha na busca de imagens.")

        run_async(_task, on_result=_on_ok, on_error=_on_err)

    def _populate_grid(self, results: List[WebImageResult]) -> None:
        self._clear_grid()
        cols = 3
        for idx, item in enumerate(results):
            if not item.image_bytes:
                continue
            card = QFrame()
            card.setFrameShape(QFrame.Shape.StyledPanel)
            vlayout = QVBoxLayout(card)
            vlayout.setContentsMargins(6, 6, 6, 6)

            img_lbl = QLabel()
            img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            img_lbl.setFixedSize(180, 120)
            pix = QPixmap()
            if pix.loadFromData(item.image_bytes):
                img_lbl.setPixmap(
                    pix.scaled(
                        176,
                        116,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
            vlayout.addWidget(img_lbl)

            select_btn = QPushButton("Usar esta")
            select_btn.clicked.connect(lambda _checked=False, r=item: self._select_web_result(r))
            vlayout.addWidget(select_btn)

            self.grid_layout.addWidget(card, idx // cols, idx % cols)

    def _select_web_result(self, result: WebImageResult) -> None:
        if not result.image_bytes:
            return
        self.selected_bytes = result.image_bytes
        self.selected_filename = self.controller.images.make_filename(
            result.image_bytes, result.extension
        )
        self._refresh_preview()
        self.status_label.setText("Imagem selecionada da busca web.")

    def _on_generate_ai_image(self) -> None:
        prompt = self.ai_prompt_input.text().strip()
        if not prompt:
            notify_warning("Digite uma descrição ou frase para gerar a imagem.", self)
            return

        self._set_busy(True, "Gerando ilustração com IA (pode levar alguns segundos)...")

        def _task():
            return self.controller.gerar_imagem_ia(prompt)

        def _on_ok(res):
            img_bytes, filename = res
            self.selected_bytes = img_bytes
            self.selected_filename = filename
            self._refresh_preview()
            self._set_busy(False, "Imagem gerada com IA e selecionada!")

        def _on_err(err: str):
            notify_warning(f"Erro ao gerar imagem com IA:\n{err.splitlines()[0]}", self)
            self._set_busy(False, "Falha ao gerar imagem.")

        run_async(_task, on_result=_on_ok, on_error=_on_err)

    def _on_confirm(self) -> None:
        self.example.image_bytes = self.selected_bytes
        self.example.image_filename = self.selected_filename if self.selected_bytes else ""
        self.accept()
