#!/usr/bin/env python3
"""Menu e diagnóstico do Integra Visão."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parent
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
# GLVND deve selecionar NVIDIA antes de importar MediaPipe/OpenCV/SDL.
if Path("/usr/share/glvnd/egl_vendor.d/10_nvidia.json").exists():
    os.environ.setdefault("__NV_PRIME_RENDER_OFFLOAD", "1")
    os.environ.setdefault("__GLX_VENDOR_LIBRARY_NAME", "nvidia")
    os.environ.setdefault("__EGL_VENDOR_LIBRARY_FILENAMES", "/usr/share/glvnd/egl_vendor.d/10_nvidia.json")


def parser():
    p = argparse.ArgumentParser(description="Minigames de visão computacional — Integra Profissões")
    p.add_argument("--game", choices=("pong", "expressions", "fruit", "memes", "camera", "anatomy"))
    p.add_argument("--device", choices=("auto", "gpu", "cpu"), default="auto", help="auto tenta GPU e avisa se precisar de CPU")
    p.add_argument("--camera", type=int, default=0)
    p.add_argument("--width", type=int, choices=(640, 1280), default=640)
    p.add_argument("--height", type=int, choices=(360, 480, 720), default=480)
    p.add_argument("--fps", type=int, choices=(30, 60, 120), default=60, help="FPS da interface, independente da webcam")
    p.add_argument("--duration", type=float, default=45, help="duração de cada partida em segundos")
    p.add_argument("--dynamic-fps", action="store_true", help="não modificar temporariamente o controle de FPS da câmera")
    p.add_argument("--demo", action="store_true", help="demonstração automática sem acessar webcam")
    p.add_argument("--fullscreen", action=argparse.BooleanOptionalAction, default=True, help="iniciar em tela cheia (F11 alterna)")
    p.add_argument("--windowed", dest="fullscreen", action="store_false", help="iniciar em janela")
    p.add_argument("--seconds", type=float, default=0, help="fechar janela automaticamente após N segundos")
    p.add_argument("--screenshot", help="salvar imagem da janela ao sair; só quando solicitado")
    p.add_argument("--benchmark", type=float, metavar="SEGUNDOS", help="medir captura/inferência reais sem abrir janela")
    p.add_argument("--debug-overlay", "--show-skeleton", dest="debug_overlay", action="store_true", help="mostrar landmarks, ossos e malha usados pelos minigames")
    return p


def benchmark(args):
    import numpy as np
    from integra.vision import Camera, Vision
    camera = Camera(args.camera, args.width, args.height, not args.dynamic_fps)
    worker = Vision(camera, args.game or "pong", args.device)
    times, ages = [], []
    camera.start()
    worker.start()
    previous = -1
    try:
        if not worker.ready.wait(30):
            raise RuntimeError("Tempo esgotado ao inicializar modelos.")
        if worker.error:
            raise RuntimeError(worker.error)
        # Descarta aquecimento e negociação inicial da exposição.
        time.sleep(1)
        start = time.monotonic()
        while time.monotonic() - start < args.benchmark:
            if camera.error or worker.error:
                raise RuntimeError(camera.error or worker.error)
            obs = worker.latest
            if obs.sequence != previous and obs.sequence >= 0:
                previous = obs.sequence
                times.append(obs.inference_ms)
                ages.append((time.monotonic() - obs.captured) * 1000)
            time.sleep(.001)
        if not times:
            raise RuntimeError("Nenhum quadro processado.")
        result = {"game": args.game or "pong", "backend": worker.backend, "camera": camera.description,
                  "camera_fps": round(camera.fps, 1), "inference_fps": round(len(times) / (time.monotonic() - start), 1),
                  "inference_p50_ms": round(float(np.median(times)), 2), "inference_p95_ms": round(float(np.percentile(times, 95)), 2),
                  "capture_to_result_p50_ms": round(float(np.median(ages)), 2), "samples": len(times),
                  "note": "Medição desde retorno da captura; não inclui exposição/sensor nem latência do monitor."}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return result
    finally:
        worker.close()
        camera.close()


def main():
    p = parser()
    args = p.parse_args()
    if args.duration <= 0 or args.seconds < 0 or (args.benchmark is not None and args.benchmark <= 0):
        p.error("Tempos devem ser positivos (ou zero para --seconds).")
    if (args.width, args.height) not in ((640, 360), (640, 480), (1280, 720)):
        p.error("Use 640×360, 640×480 ou 1280×720.")
    (ROOT / "logs").mkdir(exist_ok=True)
    # Logs nativos do MediaPipe vão para arquivo, mantendo menu legível.
    with (ROOT / "logs/runtime.log").open("a") as log:
        os.dup2(log.fileno(), 2)
    try:
        if args.benchmark:
            benchmark(args)
            return 0
        from integra.frontend import Frontend
        return Frontend(args).run()
    except (KeyboardInterrupt, EOFError):
        return 0
    except Exception as error:
        print(f"Não foi possível iniciar: {error}\nDetalhes: {ROOT / 'logs/runtime.log'}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
