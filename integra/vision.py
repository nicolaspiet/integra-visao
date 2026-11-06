"""Captura e inferência independentes: somente o quadro mais recente é mantido."""
from __future__ import annotations

from contextlib import ExitStack
from dataclasses import dataclass, field
from pathlib import Path
from threading import Condition, Event, Thread
import json
import subprocess
import sys
import time

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "vendor/expression-lab"
ZOO = ROOT / "vendor/opencv-zoo/models/facial_expression_recognition"
EXPRESSIONS = ("Raiva", "Nojo", "Medo", "Alegria", "Neutra", "Tristeza", "Surpresa")


@dataclass(frozen=True)
class Observation:
    sequence: int = -1
    captured: float = 0.0
    frame: object = None
    hands: tuple = ()
    face: tuple = ()
    expression: int | None = None
    probabilities: tuple = ()
    gesture: str | None = None
    inference_ms: float = 0.0
    blendshapes: tuple = ()


class Camera:
    def __init__(self, index=0, width=640, height=480, fixed_fps=True):
        self.index, self.width, self.height = index, width, height
        self.fixed_fps = fixed_fps
        self.condition = Condition()
        self.stopped = Event()
        self.latest = (-1, 0.0, None)
        self.fps = 0.0
        self.error = None
        self.description = ""
        self._restore = None
        self._cap = None
        self.thread = Thread(target=self._run, name="webcam", daemon=True)

    def start(self):
        self.thread.start()

    def _fps_control(self):
        if not self.fixed_fps or not sys.platform.startswith("linux"):
            return
        command = ["v4l2-ctl", "-d", f"/dev/video{self.index}"]
        try:
            result = subprocess.run(command + ["--get-ctrl=exposure_dynamic_framerate"],
                                    capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                previous = int(result.stdout.strip().rsplit(":", 1)[-1])
                if previous:
                    changed = subprocess.run(command + ["--set-ctrl=exposure_dynamic_framerate=0"],
                                             capture_output=True, timeout=2)
                    if changed.returncode == 0:
                        self._restore = (command, previous)
        except (OSError, ValueError, subprocess.TimeoutExpired):
            pass

    def _run(self):
        cap = None
        try:
            # DroidCam pode abrir em V4L2, mas não aceitar o formato YUYV. Tente
            # backend genérico e MJPG antes de desistir; isso também remove avisos
            # estranhos do driver quando a câmera anuncia capacidades incompletas.
            backends = [cv2.CAP_V4L2, cv2.CAP_ANY] if sys.platform.startswith("linux") else [cv2.CAP_ANY]
            codecs = ["MJPG", "YUYV"] if self.width >= 1280 else ["YUYV", "MJPG"]
            for backend in backends:
                for codec in codecs:
                    candidate = cv2.VideoCapture(self.index, backend)
                    if not candidate.isOpened():
                        candidate.release()
                        continue
                    candidate.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*codec))
                    candidate.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                    candidate.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                    candidate.set(cv2.CAP_PROP_FPS, 30)
                    candidate.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    ok, probe = candidate.read()
                    if ok and probe is not None and probe.size:
                        cap = candidate
                        break
                    candidate.release()
                if cap is not None:
                    break
            self._cap = cap
            if cap is None:
                raise RuntimeError("Webcam não entregou quadros. No DroidCam, confira se o cliente está conectado e tente --camera 1.")
            self._fps_control()
            fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
            actual_codec = "".join(chr((fourcc >> (8 * i)) & 255) for i in range(4))
            self.description = f"{int(cap.get(3))}×{int(cap.get(4))} · {actual_codec}"
            count, started, sequence = 0, time.monotonic(), 0
            while not self.stopped.is_set():
                ok, frame = cap.read()
                if not ok or frame is None or frame.size == 0:
                    raise RuntimeError("A webcam parou de enviar imagens. Tente o outro dispositivo com --camera 1.")
                captured = time.monotonic()
                frame = cv2.flip(frame, 1)
                with self.condition:
                    self.latest = (sequence, captured, frame)
                    self.condition.notify_all()
                count += 1
                sequence += 1
                if captured - started >= 1:
                    self.fps = count / (captured - started)
                    count, started = 0, captured
        except Exception as error:
            self.error = str(error)
        finally:
            self.stopped.set()
            with self.condition:
                self.condition.notify_all()
            if self._restore:
                command, value = self._restore
                try:
                    subprocess.run(command + [f"--set-ctrl=exposure_dynamic_framerate={value}"],
                                   capture_output=True, timeout=2)
                except (OSError, subprocess.TimeoutExpired):
                    pass
            if cap is not None:
                cap.release()

    def next(self, previous):
        with self.condition:
            self.condition.wait_for(lambda: self.latest[0] != previous or self.stopped.is_set(), timeout=.2)
            return self.latest

    def close(self):
        self.stopped.set()
        with self.condition:
            self.condition.notify_all()
        self.thread.join(timeout=3)


class ExpressionModel:
    """MobileFaceNet/Progressive Teacher do OpenCV Zoo, com alinhamento original."""
    def __init__(self):
        sys.path.insert(0, str(ZOO))
        from facial_fer_model import FaceAlignment
        self.align = FaceAlignment()
        self.net = cv2.dnn.readNet(str(ROOT / "models/facial_expression.onnx"))

    def classify(self, frame, face):
        height, width = frame.shape[:2]
        point = lambda i: np.array((face[i].x * width, face[i].y * height))
        eyes = sorted([(point(33) + point(133)) / 2, (point(362) + point(263)) / 2], key=lambda p: p[0])
        mouth = sorted([point(61), point(291)], key=lambda p: p[0])
        aligned = self.align.get_align_image(frame, np.array([*eyes, point(1), *mouth]))
        blob = cv2.dnn.blobFromImage(aligned, 1 / 127.5, (112, 112), (127.5,) * 3, swapRB=True)
        self.net.setInput(blob, "data")
        scores = self.net.forward("label").reshape(-1)
        probabilities = np.exp(scores - scores.max())
        probabilities /= probabilities.sum()
        return int(probabilities.argmax()), tuple(float(p) for p in probabilities)


class Vision:
    def __init__(self, camera, mode, device="auto"):
        self.camera, self.mode, self.device = camera, mode, device
        self.latest = Observation()
        self.ready, self.stopped = Event(), Event()
        self.error = None
        self.backend = "Inicializando…"
        self.thread = Thread(target=self._run, name="visao", daemon=True)

    def start(self):
        self.thread.start()

    def _detectors(self, stack, delegate):
        hand, face = None, None
        if self.mode in ("pong", "fruit", "memes", "camera", "anatomy"):
            options = vision.HandLandmarkerOptions(
                base_options=python.BaseOptions(model_asset_path=str(LAB / "models/hand_landmarker.task"), delegate=delegate),
                running_mode=vision.RunningMode.VIDEO, num_hands=2 if self.mode == "memes" else 1,
                min_hand_detection_confidence=.4, min_hand_presence_confidence=.4, min_tracking_confidence=.4)
            hand = stack.enter_context(vision.HandLandmarker.create_from_options(options))
        if self.mode in ("expressions", "memes", "anatomy"):
            options = vision.FaceLandmarkerOptions(
                base_options=python.BaseOptions(model_asset_path=str(LAB / "models/face_landmarker.task"), delegate=delegate),
                running_mode=vision.RunningMode.VIDEO, num_faces=1,
                min_face_detection_confidence=.4, min_face_presence_confidence=.4,
                min_tracking_confidence=.4,
                output_face_blendshapes=self.mode in ("memes", "anatomy"))
            face = stack.enter_context(vision.FaceLandmarker.create_from_options(options))
        return hand, face

    def _run(self):
        cv2.setNumThreads(2)
        try:
            with ExitStack() as outer:
                delegates = [python.BaseOptions.Delegate.CPU] if self.device == "cpu" else [python.BaseOptions.Delegate.GPU]
                if self.device == "auto":
                    delegates.append(python.BaseOptions.Delegate.CPU)
                for delegate in delegates:
                    try:
                        stack = ExitStack()
                        hand, face = self._detectors(stack, delegate)
                        outer.enter_context(stack)
                        self.backend = "GPU · NVIDIA / OpenGL" if delegate == python.BaseOptions.Delegate.GPU else "CPU · XNNPACK"
                        break
                    except Exception:
                        stack.close()
                        if delegate == delegates[-1]:
                            raise
                        print("GPU indisponível; usando CPU. Detalhes em logs/runtime.log.", flush=True)
                classifier = ExpressionModel() if self.mode == "expressions" else None
                if self.mode == "memes":
                    sys.path.insert(0, str(LAB))
                    # Tolerância maior a pequenas variações de ângulo/distância.
                    # Valores originais seguem intactos no checkout da referência.
                    import config as lab_config
                    lab_config.ANGULO_DEDO_ESTENDIDO = 150
                    lab_config.FATOR_POLEGAR_ESTENDIDO = 1.10
                    lab_config.DISTANCIA_MAO_ROSTO = .45
                    lab_config.DISTANCIA_MAO_CABECA = 1.20
                    from reconhecimento import reconhecer_gesto
                    from rosto import extrair_info_rosto
                self.ready.set()
                previous, last_timestamp = -1, -1
                while not self.stopped.is_set() and not self.camera.stopped.is_set():
                    sequence, captured, frame = self.camera.next(previous)
                    if sequence == previous or frame is None:
                        continue
                    previous = sequence
                    started = time.monotonic()
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                    timestamp = max(last_timestamp + 1, int(captured * 1000))
                    last_timestamp = timestamp
                    hands = hand.detect_for_video(image, timestamp).hand_landmarks if hand else []
                    face_result = face.detect_for_video(image, timestamp) if face else None
                    landmarks = face_result.face_landmarks[0] if face_result and face_result.face_landmarks else []
                    expression, probabilities, gesture, blendshapes = None, (), None, ()
                    if classifier and landmarks:
                        expression, probabilities = classifier.classify(frame, landmarks)
                    if self.mode == "memes":
                        height, width = frame.shape[:2]
                        gesture = reconhecer_gesto(hands, extrair_info_rosto(face_result, width, height), width, height)
                    if face_result and face_result.face_blendshapes:
                        blendshapes = tuple((item.category_name, float(item.score))
                                            for item in face_result.face_blendshapes[0])
                    self.latest = Observation(sequence, captured, frame, tuple(hands), tuple(landmarks),
                                              expression, probabilities, gesture, (time.monotonic() - started) * 1000,
                                              blendshapes)
        except Exception as error:
            self.error = str(error)
            import traceback
            traceback.print_exc()
        finally:
            self.ready.set()

    def close(self):
        self.stopped.set()
        self.thread.join(timeout=5)


def meme_paths():
    data = json.loads((LAB / "gestos.json").read_text())
    return {gesture: LAB / item["imagem"] for gesture, item in data.items()}
