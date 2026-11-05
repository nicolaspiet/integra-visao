"""Baixa dependências de seus autores; não inicia câmera ou interface."""
from pathlib import Path, PurePosixPath
import hashlib
import io
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
LAB_COMMIT = "0602ac047eebc959c44caa8c769b2bd4f1a13ea5"
ZOO_COMMIT = "48b10fa505aeb51fbd127fc60a5c660040e823b7"


def download(url):
    print(f"Baixando {url}", flush=True)
    with urllib.request.urlopen(url, timeout=120) as response:
        return response.read()


def prepare(root=ROOT):
    lab = root / "vendor/expression-lab"
    if not (lab / "models/face_landmarker.task").exists():
        archive = download(f"https://codeload.github.com/CaioScura/expression-lab/zip/{LAB_COMMIT}")
        with zipfile.ZipFile(io.BytesIO(archive)) as source:
            for entry in source.infolist():
                parts = PurePosixPath(entry.filename).parts[1:]
                if not parts or entry.is_dir():
                    continue
                if ".." in parts:
                    raise ValueError("Caminho inválido no arquivo baixado")
                target = lab.joinpath(*parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source.read(entry))
    zoo = root / "vendor/opencv-zoo"
    for name in ("LICENSE", "models/facial_expression_recognition/facial_fer_model.py"):
        target = zoo / name
        if not target.exists():
            content = download(f"https://raw.githubusercontent.com/opencv/opencv_zoo/{ZOO_COMMIT}/{name}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
    model = root / "models/facial_expression.onnx"
    expected = "4f61307602fc089ce20488a31d4e4614e3c9753a7d6c41578c854858b183e1a9"
    if not model.exists() or hashlib.sha256(model.read_bytes()).hexdigest() != expected:
        content = download(f"https://media.githubusercontent.com/media/opencv/opencv_zoo/{ZOO_COMMIT}/models/facial_expression_recognition/facial_expression_recognition_mobilefacenet_2022july.onnx")
        if hashlib.sha256(content).hexdigest() != expected:
            raise ValueError("Checksum do modelo não confere")
        model.parent.mkdir(parents=True, exist_ok=True)
        model.write_bytes(content)
    print("Modelos e referências preparados.")


if __name__ == "__main__":
    prepare()
