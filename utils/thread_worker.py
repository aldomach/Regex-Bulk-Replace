"""
utils/thread_worker.py
----------------------
Ejecuta tareas pesadas en un hilo secundario para no bloquear la UI.
Reutilizable con cualquier función de larga duración.
"""

import threading
from typing import Callable, Any


class Worker(threading.Thread):
    """
    Hilo de trabajo genérico.
    Ejecuta fn(*args, **kwargs) en segundo plano.
    Notifica progreso, finalización y errores mediante callbacks.
    """

    def __init__(
        self,
        fn: Callable,
        args: tuple = (),
        kwargs: dict = None,
        on_progress: Callable[[int, int, Any], None] | None = None,
        on_done: Callable[[Any], None] | None = None,
        on_error: Callable[[Exception], None] | None = None,
    ):
        super().__init__(daemon=True)
        self._fn = fn
        self._args = args
        self._kwargs = kwargs or {}
        self.on_progress = on_progress
        self.on_done = on_done
        self.on_error = on_error
        self._cancel_flag = False

    def cancel(self):
        self._cancel_flag = True

    def is_cancelled(self) -> bool:
        return self._cancel_flag

    def run(self):
        try:
            result = self._fn(*self._args, **self._kwargs)
            if self.on_done and not self._cancel_flag:
                self.on_done(result)
        except Exception as e:
            if self.on_error:
                self.on_error(e)
