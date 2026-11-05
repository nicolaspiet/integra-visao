"""Gera catálogo HTML autossuficiente; não abre navegador, janela ou webcam."""
import base64
from html import escape
import io
import mimetypes
import os
from pathlib import Path
import sys

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from integra.catalog import EXPRESSIONS, SOURCES, meme_catalog


def data_image(path):
    media = mimetypes.guess_type(path)[0] or "image/png"
    return f"data:{media};base64," + base64.b64encode(Path(path).read_bytes()).decode()


def face_image(index):
    import pygame as pg
    from integra.ui import BG, ACCENT, face_drawing
    surface = pg.Surface((220, 180))
    surface.fill(BG)
    face_drawing(surface, (20, 0, 180, 180), index, ACCENT)
    stream = io.BytesIO()
    pg.image.save(surface, stream, "face.png")
    return "data:image/png;base64," + base64.b64encode(stream.getvalue()).decode()


def build():
    memes = []
    for item in meme_catalog():
        memes.append(f'''<article><img src="{data_image(item['image'])}" alt="Figurinha: {escape(item['name'])}" loading="lazy">
        <div><small>{escape(item['kind'])}</small><h3>{escape(item['name'])}</h3>
        <p>{escape(item['how'])}</p><p class="tip">{escape(item['tip'])}</p></div></article>''')
    expressions = []
    for index, item in enumerate(EXPRESSIONS):
        expressions.append(f'''<article><img class="face" src="{face_image(index)}" alt="Esquema ilustrativo de {escape(item['name'])}" loading="lazy">
        <div><h3>{escape(item['name'])}</h3><p>{escape(item['how'])}</p><p class="tip">{escape(item['tip'])}</p></div></article>''')
    links = "".join(f'<li><a href="{escape(url)}" target="_blank" rel="noopener noreferrer">{escape(title)}</a></li>' for title, url in SOURCES)
    html = '''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Integra — catálogo de gestos e expressões</title><style>
    :root{color-scheme:light;--ink:#232722;--muted:#696e66;--line:#d8dbd1;--accent:#415b42}
    *{box-sizing:border-box}body{margin:0;background:#f4f3ee;color:var(--ink);font:17px/1.65 system-ui,sans-serif}
    main{max-width:1180px;margin:auto;padding:35px 28px 90px}header{border-bottom:1px solid var(--line);padding-bottom:25px}
    header strong{font-size:20px}nav{display:flex;flex-wrap:wrap;gap:25px;margin-top:18px}a{color:var(--accent);text-underline-offset:5px}
    h1{font-size:clamp(30px,5vw,48px);line-height:1.15;letter-spacing:-1px;font-weight:650;margin-top:48px}
    h2{font-size:28px;margin-top:65px}h3{font-size:22px;line-height:1.2;margin:5px 0 15px}p{margin:8px 0}.intro{max-width:790px}
    .tip,small{color:var(--muted)}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0 36px}
    article{display:grid;grid-template-columns:155px 1fr;align-items:start;gap:22px;border-top:1px solid var(--line);padding:28px 0;break-inside:avoid}
    article img{width:155px;height:170px;object-fit:contain}article .face{height:145px}small{font-size:14px}
    aside{border-left:3px solid var(--accent);padding:3px 20px;margin:27px 0;max-width:850px}section{scroll-margin-top:25px}
    li{margin:12px 0}code,kbd{font-family:ui-monospace,monospace;background:#e8ece1;padding:2px 6px;border-radius:3px}
    @media(max-width:850px){.grid{grid-template-columns:1fr}}@media(max-width:450px){article{grid-template-columns:105px 1fr;gap:15px}article img{width:105px}}
    @media print{nav{display:none}body{font-size:12px}h2{margin-top:30px}.grid{grid-template-columns:1fr 1fr}article{grid-template-columns:100px 1fr}article img{width:100px;height:100px}}
    </style><main><header><strong>Integra Profissões</strong><nav><a href="#figurinhas">15 figurinhas</a><a href="#expressoes">7 expressões</a><a href="#jogos">Jogos e fontes</a></nav></header>
    <h1>Como fazer cada gesto.</h1><div class="intro"><p>Catálogo completo dos dois modos de rosto, com imagens, instruções e dicas. Este guia funciona offline e não acessa a webcam.</p>
    <p>No programa: <kbd>H</kbd> abre o catálogo, <kbd>F11</kbd> alterna tela cheia e <kbd>Esc</kbd> volta ao início.</p></div>
    <section id="figurinhas"><h2>Figurinhas · 15 gestos</h2><p class="intro">Este modo usa as regras do Expression Lab: mãos, rosto ou ambos. Não é o mesmo classificador do desafio de emoções. Quando dois gestos se encaixam, a prioridade das regras decide qual figurinha aparece.</p>
    <aside>Comece por joia, hang loose e indicador levantado. Para gestos perto do rosto, mantenha olhos e mãos visíveis. A imagem do meme mostra o resultado; a instrução ao lado explica o gesto reconhecido.</aside><div class="grid">''' + "".join(memes) + '''</div>
    <p class="tip">Também existem duas imagens de espera: macaco com olhar perdido quando não há gesto e gato de frente após 10 segundos. Não são gestos extras.</p></section>
    <section id="expressoes"><h2>Expressões · 7 categorias</h2><p class="intro">No desafio que pontua, imite a categoria pedida e mantenha por aproximadamente 0,7 segundo. A estimativa precisa coincidir com o alvo e passar o limiar de pontuação. <kbd>N</kbd> pula uma categoria difícil.</p>
    <aside>Os desenhos abaixo são esquemas didáticos, não fotos do conjunto de treino nem garantia de reconhecimento. Medo e nojo podem confundir o modelo. A estimativa descreve aparência facial, não confirma o que você sente.</aside><div class="grid">''' + "".join(expressions) + '''</div></section>
    <section id="jogos"><h2>Jogos e referências</h2><p><strong>Pong:</strong> levante e abaixe o indicador para controlar a raquete da esquerda. A bola que passa pelo adversário vale ponto. A partida dura 45 segundos.</p>
    <p><strong>Frutas:</strong> deslize o indicador sobre as frutas. Cada fruta vale 1 ponto; cortar uma bomba tira 5 pontos. A partida dura 45 segundos.</p>
    <p>Os jogos de Pong e frutas têm implementação própria. Os links abaixo mostram os projetos de referência, a origem das figurinhas e o modelo de expressões utilizado.</p><ul>''' + links + '''</ul>
    <p class="tip">Figurinhas e regras: CaioScura / Expression Lab, checkout local preservado. Classificador: OpenCV Zoo / Progressive Teacher (MobileFaceNet). Fontes locais consultadas: README, gestos.json e documentação do modelo.</p></section></main></html>'''
    path = ROOT / "docs/referencias.html"
    path.parent.mkdir(exist_ok=True)
    path.write_text(html)
    return path


if __name__ == "__main__":
    print(build())
