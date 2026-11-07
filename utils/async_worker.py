import traceback
from typing import Any, Callable, Optional
from .qt_compat import QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot


class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    result = pyqtSignal(object)


class AsyncWorker(QRunnable):
    """Executa funções pesadas ou de rede em background sem travar a UI do Anki."""

    def __init__(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self) -> None:
        try:
            output = self.fn(*self.args, **self.kwargs)
        except Exception as exc:
            tb = traceback.format_exc()
            self.signals.error.emit(f"{exc}\n{tb}")
        else:
            self.signals.result.emit(output)
        finally:
            self.signals.finished.emit()


def run_async(
    fn: Callable[..., Any],
    on_result: Optional[Callable[[Any], None]] = None,
    on_error: Optional[Callable[[str], None]] = None,
    on_finished: Optional[Callable[[], None]] = None,
    *args: Any,
    **kwargs: Any,
) -> AsyncWorker:
    worker = AsyncWorker(fn, *args, **kwargs)
    if on_result is not None:
        worker.signals.result.connect(on_result)
    if on_error is not None:
        worker.signals.error.connect(on_error)
    if on_finished is not None:
        worker.signals.finished.connect(on_finished)
    QThreadPool.globalInstance().start(worker)
    return worker
