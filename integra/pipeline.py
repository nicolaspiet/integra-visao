"""Isola EGL/MediaPipe do contexto gráfico SDL no notebook com GPU híbrida."""
from dataclasses import replace
from multiprocessing import get_context
from queue import Empty, Full
from threading import Event
from types import SimpleNamespace
import time

from .vision import Camera, Observation, Vision


def _publish(queue, item):
    try:
        queue.put_nowait(item)
    except Full:
        try:
            queue.get_nowait()
        except Empty:
            pass
        try:
            queue.put_nowait(item)
        except Full:
            pass


def _process_main(queue, stopped, options):
    import cv2
    camera = Camera(options["camera"], options["width"], options["height"], not options["dynamic_fps"])
    worker = Vision(camera, options["mode"], options["device"])
    camera.start()
    worker.start()
    previous, last_sent = -1, 0.0
    try:
        while not stopped.is_set():
            observation = worker.latest
            now = time.monotonic()
            if observation.sequence != previous or now - last_sent >= .2:
                previous, last_sent = observation.sequence, now
                # Prévia maior e com proporção preservada, sem mudar captura/inferência.
                if observation.frame is not None:
                    height, width = observation.frame.shape[:2]
                    scale = min(1, 640 / width, 480 / height)
                    if scale < 1:
                        observation = replace(observation, frame=cv2.resize(observation.frame,
                            (round(width * scale), round(height * scale)), interpolation=cv2.INTER_AREA))
                _publish(queue, (observation, camera.fps, camera.description, camera.error,
                                 worker.backend, worker.error, worker.ready.is_set()))
            time.sleep(.002)
    except Exception as error:
        _publish(queue, (Observation(), 0, "", str(error), "Erro", str(error), True))
    finally:
        worker.close()
        camera.close()
        # O pai pode parar de consumir ao fechar; não espere o feeder da fila.
        queue.cancel_join_thread()


class Pipeline:
    def __init__(self, args):
        context = get_context("spawn")
        self.queue = context.Queue(maxsize=1)
        self.stopped = context.Event()
        options = dict(camera=args.camera, width=args.width, height=args.height,
                       dynamic_fps=args.dynamic_fps, mode=args.game, device=args.device)
        self.process = context.Process(target=_process_main, args=(self.queue, self.stopped, options),
                                       name="integra-gpu", daemon=True)
        self.latest = Observation()
        self.backend = "Inicializando…"
        self.ready = Event()
        self.error = None
        self.camera = SimpleNamespace(fps=0.0, description="", error=None)

    def start(self):
        self.process.start()

    def poll(self):
        try:
            while True:
                observation, fps, description, camera_error, backend, error, ready = self.queue.get_nowait()
                self.latest = observation
                self.camera.fps, self.camera.description, self.camera.error = fps, description, camera_error
                self.backend, self.error = backend, error
                if ready:
                    self.ready.set()
        except Empty:
            pass
        if self.process.exitcode is not None and not self.stopped.is_set():
            self.error = f"Processo de visão encerrou (código {self.process.exitcode}). Consulte logs/runtime.log."
            self.ready.set()
        return self.latest

    def close(self):
        self.stopped.set()
        self.process.join(timeout=8)
        if self.process.is_alive():
            self.process.terminate()
            self.process.join(timeout=2)
        self.queue.close()
