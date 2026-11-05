"""Catálogo compartilhado pela interface e pelo guia HTML offline."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "vendor/expression-lab"

EXPRESSIONS = (
    dict(name="Raiva", how="Junte e abaixe as sobrancelhas. Aperte os lábios, sem cobrir o rosto.",
         tip="Só fechar a boca pode parecer neutro. O desenho das sobrancelhas ajuda a diferenciar."),
    dict(name="Nojo", how="Franza o nariz e levante um pouco o lábio superior, como ao sentir um cheiro ruim.",
         tip="É uma das categorias mais difíceis. Língua para fora não garante reconhecimento."),
    dict(name="Medo", how="Erga e aproxime as sobrancelhas. Abra os olhos e estique a boca na horizontal.",
         tip="Pode confundir com surpresa. Na surpresa, a boca tende a ficar mais arredondada."),
    dict(name="Alegria", how="Sorria, levantando os cantos da boca. Deixe as bochechas acompanharem o sorriso.",
         tip="Olhe para a câmera. Um sorriso claro costuma ser mais fácil que um sorriso discreto."),
    dict(name="Neutra", how="Relaxe a boca e as sobrancelhas. Olhe de frente sem fazer careta.",
         tip="Evite manter um sorriso pequeno. Respire e solte a tensão do rosto."),
    dict(name="Tristeza", how="Deixe os cantos da boca caírem e levante a parte interna das sobrancelhas.",
         tip="Olhar para baixo ou fechar os olhos não basta. Mantenha o rosto visível."),
    dict(name="Surpresa", how="Erga as sobrancelhas, abra os olhos e faça um O com a boca.",
         tip="Afaste um pouco a mão do rosto. O modelo precisa ver olhos, nariz e boca."),
)

# Nomes correspondem exatamente às chaves do gestos.json original.
MEMES = (
    dict(key="Macaco maos na cabeca", name="Mãos na cabeça", how="Coloque as duas mãos em cima da cabeça.", tip="Deixe as duas mãos dentro do enquadramento e visíveis.", kind="Duas mãos"),
    dict(key="Maos pra cima", name="Mãos para cima", how="Levante as duas mãos acima do queixo e abra a boca.", tip="Com a boca fechada, outro gesto pode ter prioridade.", kind="Mãos + rosto"),
    dict(key="Kojima cinema", name="Cinema", how="Levante as duas mãos abertas ao lado da cabeça e mantenha a boca fechada.", tip="As palmas e os dedos precisam aparecer. Evite colocar as mãos sobre a cabeça.", kind="Duas mãos"),
    dict(key="Nao grita", name="Não grita", how="Encoste o indicador levantado perto da boca, fazendo shhh.", tip="Não esconda toda a boca nem vire o rosto de lado.", kind="Mão + rosto"),
    dict(key="Pensativo", name="Pensativo", how="Apoie uma mão logo abaixo do queixo.", tip="Mostre a mão inteira perto do queixo. Não cubra a boca.", kind="Mão + rosto"),
    dict(key="Gato mao na boca", name="Mão na boca", how="Leve a palma da mão à frente da boca.", tip="Se o rosto sumir, afaste um pouco a mão: a oclusão pode prejudicar a detecção.", kind="Mão + rosto"),
    dict(key="Hang loose", name="Hang loose", how="Estique o polegar e o dedo mínimo. Dobre os outros três dedos.", tip="Mostre a palma à câmera, sem sobrepor os dedos.", kind="Uma mão"),
    dict(key="Faz o L", name="Faz o L", how="Estique polegar e indicador em L. Dobre os outros dedos.", tip="Mantenha a mão de frente e separe bem os dois dedos.", kind="Uma mão"),
    dict(key="Gato joia", name="Joia", how="Aponte o polegar para cima e feche os outros dedos.", tip="Deixe espaço entre a mão e o rosto.", kind="Uma mão"),
    dict(key="Mario dedo do meio", name="Dedo do meio", how="Estique apenas o dedo médio. Mantenha os outros dobrados.", tip="Este item faz parte do catálogo original. Não é necessário usá-lo na demonstração.", kind="Uma mão"),
    dict(key="Gato apontando", name="Apontando", how="Estique apenas o indicador e aponte para o lado.", tip="Aponte na horizontal, não para a lente. Para cima pode ativar Indicador levantado.", kind="Uma mão"),
    dict(key="Indicador levantado", name="Indicador levantado", how="Estique apenas o indicador, apontando para cima.", tip="Afaste o indicador da boca para não ativar Não grita.", kind="Uma mão"),
    dict(key="Gato nojo", name="Nariz franzido", how="Franza o nariz, como ao sentir um cheiro ruim.", tip="Língua para fora não é detectada. A regra usa o movimento do nariz.", kind="Rosto"),
    dict(key="Olhar assustado", name="Olhar assustado", how="Arregale os olhos, olhando para a câmera.", tip="Não precisa abrir a boca. Deixe os olhos bem visíveis.", kind="Rosto"),
    dict(key="Olhando de lado", name="Olhando de lado", how="Olhe para o lado movendo só os olhos.", tip="Mantenha a cabeça voltada para a câmera. Girar a cabeça não é o mesmo gesto.", kind="Rosto"),
)

SOURCES = (
    ("Pong: referência de controle pela mão", "https://github.com/ekagansahin/hand-controlled-pong"),
    ("Frutas: referência de jogo pela mão", "https://github.com/devnickverma/Fruite_Ninja_Using_OpenCV"),
    ("Figurinhas: Expression Lab original e catálogo", "https://github.com/CaioScura/expression-lab#gestos-reconhecidos"),
    ("Expressões: modelo Progressive Teacher / OpenCV Zoo", "https://github.com/opencv/opencv_zoo/tree/main/models/facial_expression_recognition"),
)


def meme_catalog():
    paths = json.loads((LAB / "gestos.json").read_text())
    return tuple({**item, "image": LAB / paths[item["key"]]["imagem"]} for item in MEMES)


def gesture_entry(key):
    return next((item for item in MEMES if item["key"] == key), None)
