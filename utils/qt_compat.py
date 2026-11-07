import os
import subprocess
import sys
import tempfile
from typing import Any, Optional

mw: Any = None
av_player: Any = None
tooltip: Any = None
showWarning: Any = None
IN_ANKI: bool = False
HAS_QT: bool = False

try:
    from aqt import mw as _mw  # type: ignore
    from aqt.qt import (  # type: ignore
        QAction,
        QApplication,
        QCheckBox,
        QComboBox,
        QDialog,
        QFormLayout,
        QFrame,
        QGroupBox,
        QHBoxLayout,
        QKeySequence,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QMessageBox,
        QObject,
        QPlainTextEdit,
        QProgressBar,
        QPushButton,
        QRunnable,
        QScrollArea,
        QSizePolicy,
        QSpinBox,
        QSplitter,
        QTabWidget,
        Qt,
        QThreadPool,
        QVBoxLayout,
        QWidget,
        pyqtSignal,
        pyqtSlot,
    )
    from aqt.sound import av_player as _av_player  # type: ignore
    from aqt.utils import showWarning as _showWarning, tooltip as _tooltip  # type: ignore

    mw = _mw
    av_player = _av_player
    tooltip = _tooltip
    showWarning = _showWarning
    IN_ANKI = mw is not None
    HAS_QT = True
except ImportError:
    try:
        from PyQt6.QtCore import (
            QObject,
            QRunnable,
            Qt,
            QThreadPool,
            pyqtSignal,
            pyqtSlot,
        )
        from PyQt6.QtGui import QAction, QKeySequence
        from PyQt6.QtWidgets import (
            QApplication,
            QCheckBox,
            QComboBox,
            QDialog,
            QFormLayout,
            QFrame,
            QGroupBox,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QListWidget,
            QListWidgetItem,
            QMessageBox,
            QPlainTextEdit,
            QProgressBar,
            QPushButton,
            QScrollArea,
            QSizePolicy,
            QSpinBox,
            QSplitter,
            QTabWidget,
            QVBoxLayout,
            QWidget,
        )

        HAS_QT = True
    except ImportError:
        # Stubs leves para ambientes de teste headless sem PyQt6/aqt instalados
        class _Stub:
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                pass

        QAction = QApplication = QCheckBox = QComboBox = QDialog = _Stub  # type: ignore
        QFormLayout = QFrame = QGroupBox = QHBoxLayout = QKeySequence = _Stub  # type: ignore
        QLabel = QLineEdit = QListWidget = QListWidgetItem = QMessageBox = _Stub  # type: ignore
        QObject = QPlainTextEdit = QProgressBar = QPushButton = QRunnable = _Stub  # type: ignore
        QScrollArea = QSizePolicy = QSpinBox = QSplitter = QTabWidget = _Stub  # type: ignore
        Qt = QThreadPool = QVBoxLayout = QWidget = _Stub  # type: ignore

        def pyqtSignal(*args: Any, **kwargs: Any) -> Any:  # type: ignore
            return None

        def pyqtSlot(*args: Any, **kwargs: Any) -> Any:  # type: ignore
            def _decorator(fn: Any) -> Any:
                return fn

            return _decorator


def is_running_in_anki() -> bool:
    """Retorna True se o código estiver executando dentro de uma instância ativa do Anki."""
    return mw is not None and getattr(mw, "col", None) is not None


def notify_info(message: str, parent: Optional[Any] = None) -> None:
    """Exibe uma notificação leve (tooltip no Anki ou caixa de diálogo no modo standalone)."""
    if is_running_in_anki() and tooltip is not None:
        tooltip(message, parent=parent or mw)
    elif HAS_QT and parent is not None:
        QMessageBox.information(parent, "Reverso & AI Add-on", message)


def notify_warning(message: str, parent: Optional[Any] = None) -> None:
    """Exibe um alerta de erro ou aviso."""
    if is_running_in_anki() and showWarning is not None:
        showWarning(message, parent=parent or mw, title="Reverso & AI Add-on")
    elif HAS_QT and parent is not None:
        QMessageBox.warning(parent, "Reverso & AI Add-on", message)


def play_audio_bytes(audio_bytes: bytes, filename_hint: str = "preview.mp3") -> str:
    """Salva temporariamente os bytes de áudio e reproduz usando o player nativo do Anki ou do sistema."""
    suffix = os.path.splitext(filename_hint)[1] or ".mp3"
    temp_dir = os.path.join(tempfile.gettempdir(), "anki_reverso_ai_tts")
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, filename_hint if filename_hint else f"preview{suffix}")

    with open(temp_path, "wb") as f:
        f.write(audio_bytes)

    if is_running_in_anki() and av_player is not None:
        av_player.play_file(temp_path)
        return temp_path

    # Fallback para modo standalone fora do Anki
    if sys.platform.startswith("linux"):
        for player_cmd in (
            ["mpv", "--no-video", temp_path],
            ["ffplay", "-nodisp", "-autoexit", temp_path],
            ["xdg-open", temp_path],
        ):
            try:
                subprocess.Popen(player_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                break
            except FileNotFoundError:
                continue
    elif sys.platform == "darwin":
        subprocess.Popen(["afplay", temp_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif sys.platform == "win32":
        os.startfile(temp_path)  # type: ignore[attr-defined]

    return temp_path
