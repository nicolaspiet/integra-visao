"""Interface única: início, jogos e catálogo. Nenhuma câmera é aberta no menu."""
from pathlib import Path
import math
import time
import webbrowser
import cv2
import pygame as pg
from mediapipe.tasks.python import vision as mp_vision

from .app import App, save_record
from .catalog import EXPRESSIONS as GUIDE, SOURCES, LAB, gesture_entry, meme_catalog
from .games import BOTTOM, HEIGHT, LEFT, RIGHT, TOP, WIDTH, MemeState, clamp
from .ui import ACCENT, BG, DARK, INK, LINE, MUTED, WASH, WHITE, Painter, face_drawing
from .vision import EXPRESSIONS, Observation, meme_paths

SIZE = (1280, 720)
GAMES = ("pong", "expressions", "fruit", "memes", "anatomy")
TITLES = {"pong": "Pong", "fruit": "Corte as frutas", "expressions": "Expressões", "memes": "Figurinhas", "camera": "Sua câmera", "anatomy": "Anatomia da visão"}
HELP = {"pong": "Seu indicador é a raquete. Rebata a bola e marque pontos.",
        "fruit": "Use o indicador para cortar as frutas. Cuidado com as bombas.",
        "expressions": "Faça a expressão pedida e mantenha por um instante.",
        "memes": "Faça um gesto ou uma careta para encontrar a figurinha.",
        "camera": "Ajuste seu enquadramento antes de jogar.",
        "anatomy": "Veja landmarks, conexões e medidas detectadas ao vivo."}


class Frontend(App):
    def __init__(self, args):
        super().__init__(args)
        self.scene = "game" if self.mode else "menu"
        self._fullscreen = getattr(args, "fullscreen", True)
        self._preview_key = None
        self.buttons = []
        self.diagnostics = False
        self.debug_overlay = bool(getattr(args, "debug_overlay", False))
        self.camera_large = False
        self.camera_mirror = True
        self.camera_fill = False
        self.catalog_tab = "memes"
        self.catalog_page = 0
        self.catalog_focus = None
        self.catalog_return = "menu"
        self._memes = meme_catalog()
        self.anatomy = {
            "hands": True, "face": True, "mesh": True, "indices": False,
            "blendshapes": True, "contours": True,
        }

    def stop_devices(self):
        if self.vision:
            self.vision.close()
        self.camera = self.vision = None
        self._preview_key, self._preview = None, None

    def select_game(self, mode):
        self.stop_devices()
        self.args.game = self.mode = mode
        self.scene = "game"
        self.best = save_record(mode, 0, demo=True)
        self.memes = MemeState()
        self.camera_large = False
        self.camera_mirror = True
        self.camera_fill = False
        self.reset()
        self.start_devices()

    def go_home(self):
        self.stop_devices()
        self.scene = "menu"

    def open_catalog(self, tab=None):
        self.catalog_return = self.scene
        self.catalog_tab = tab or ("memes" if self.mode == "memes" else "expressions" if self.mode == "expressions" else "games")
        self.catalog_page = 0
        self.catalog_focus = None
        self.scene = "catalog"
        if self.mode == "fruit":
            self.game.previous = None
        self._expression_time = None

    def close_catalog(self):
        self.scene = self.catalog_return
        self._expression_time = None
        if self.mode == "expressions":
            self.game.hold = 0

    def update(self, dt, observation, now):
        if self.scene == "game":
            super().update(dt, observation, now)

    def button(self, label, rect, action, primary=False, quiet=False):
        rect = pg.Rect(rect)
        hover = rect.collidepoint(pg.mouse.get_pos()) if pg.display.get_init() else False
        if primary:
            pg.draw.rect(self.screen, ACCENT, rect, border_radius=4)
        elif not quiet or hover:
            pg.draw.rect(self.screen, WASH if hover else BG, rect, border_radius=4)
            if not quiet:
                pg.draw.rect(self.screen, LINE, rect, 1, border_radius=4)
        image = self.painter.rendered(label, 16, WHITE if primary else INK)
        self.screen.blit(image, image.get_rect(center=rect.center))
        self.buttons.append((rect, action))

    def image(self, path):
        key = str(path)
        if key not in self.images:
            image = pg.image.load(str(path))
            if image.get_bitsize() < 24:
                converted = pg.Surface(image.get_size(), pg.SRCALPHA, 32)
                converted.blit(image, (0, 0))
                image = converted
            self.images[key] = image
        return self.images[key]

    def header(self):
        p = self.painter
        p.text("Integra Profissões", 32, 23, 21, INK, bold=True)
        p.text("Visão computacional", 259, 27, 15, MUTED)
        if self.scene != "menu":
            self.button("Início", (712, 18, 82, 38), ("home",), quiet=True)
        self.button("Como jogar", (804, 18, 138, 38), ("catalog",), quiet=True)
        self.button("F11 · Tela cheia", (952, 18, 174, 38), ("fullscreen",), quiet=True)
        self.button("Sair", (1150, 18, 98, 38), ("quit",), quiet=True)
        p.rule(72)

    def draw_menu(self):
        p = self.painter
        p.text("Escolha uma experiência.", 32, 112, 36, bold=True)
        p.text("Uma câmera. Cinco jeitos de brincar.", 32, 165, 19, MUTED)
        descriptions = ("Rebata a bola movendo a mão.", "Imite a expressão da vez e some pontos.",
                        "Transforme seu indicador em uma lâmina.", "Descubra os memes com gestos e caretas.",
                        "Veja mãos, rosto, pontos e conexões.")
        for index, mode in enumerate(GAMES):
            y = 208 + index * 76
            rect = pg.Rect(32, y, 704, 70)
            if pg.display.get_init() and rect.collidepoint(pg.mouse.get_pos()):
                p.panel(rect, WASH)
            p.text(str(index + 1).zfill(2), 48, y + 14, 17, MUTED)
            p.text(TITLES[mode], 99, y + 5, 22, bold=True)
            p.text(descriptions[index], 99, y + 38, 15, MUTED)
            p.text("Abrir", 658, y + 22, 16, ACCENT)
            p.rule(y + 69, 32, 736)
            self.buttons.append((rect, ("play", mode)))
        p.rule(620)
        self.button("Testar câmera", (32, 644, 159, 36), ("play", "camera"), quiet=True)
        self.button("Catálogo completo", (207, 644, 206, 36), ("catalog", "memes"), quiet=True)
        p.text("1–5 escolher · H ajuda · F11 tela cheia", 858, 653, 14, MUTED)
        pg.draw.line(self.screen, LINE, (784, 230), (784, 616))
        p.text("Antes de começar", 832, 235, 19, bold=True)
        p.wrap("Deixe rosto e mãos bem iluminados. A câmera só liga depois que você escolhe um modo.", (832, 275, 363, 110), 18, MUTED)
        p.image(self.image(self._memes[8]["image"]), (851, 384, 310, 180))
        p.text("Seu gesto vira figurinha.", 832, 585, 16, MUTED)

    def layout(self):
        if self.mode in ("expressions", "memes", "camera", "anatomy") or self.camera_large:
            return pg.Rect(824, 174, 424, 280), pg.Rect(32, 174, 760, 450)
        return pg.Rect(32, 174, 680, 450), pg.Rect(744, 174, 504, 378)

    def draw_preview(self, observation, rect):
        p = self.painter
        pg.draw.rect(self.screen, DARK, rect, border_radius=3)
        if observation.frame is not None:
            height, width = observation.frame.shape[:2]
            fitted = pg.Rect(rect) if self.camera_fill else pg.Rect(0, 0, width, height).fit(rect)
            fitted.center = rect.center
            key = (observation.sequence, fitted.size, self.diagnostics, self.debug_overlay,
                   self.camera_mirror, self.camera_fill, tuple(self.anatomy.items()))
            if self._preview_key != key:
                source = cv2.flip(observation.frame, 1) if not self.camera_mirror else observation.frame
                frame = cv2.resize(source, fitted.size, interpolation=cv2.INTER_LINEAR)
                fw, fh = fitted.size
                overlay = self.mode == "anatomy" or self.debug_overlay
                if overlay:
                    # No modo Anatomia as camadas são configuráveis; nos minigames
                    # a flag mostra tudo que os detectores usam para decidir.
                    show_hands = self.anatomy["hands"] if self.mode == "anatomy" else True
                    show_face = self.anatomy["face"] if self.mode == "anatomy" else True
                    show_mesh = self.anatomy["mesh"] if self.mode == "anatomy" else True
                    show_indices = self.anatomy["indices"] if self.mode == "anatomy" else False
                    hand_edges = mp_vision.HandLandmarksConnections.HAND_CONNECTIONS
                    face_edges = mp_vision.FaceLandmarksConnections.FACE_LANDMARKS_TESSELATION if show_mesh else []
                    for hand in observation.hands if show_hands else ():
                        for edge in hand_edges:
                            a, b = hand[edge.start], hand[edge.end]
                            cv2.line(frame, (int(a.x * fw), int(a.y * fh)), (int(b.x * fw), int(b.y * fh)), (164, 229, 148), 2)
                        for index, point in enumerate(hand):
                            px, py = int(point.x * fw), int(point.y * fh)
                            cv2.circle(frame, (px, py), 4, (236, 242, 213), -1)
                            if show_indices:
                                cv2.putText(frame, str(index), (px + 5, py - 3), cv2.FONT_HERSHEY_SIMPLEX, .34, (245, 245, 235), 1, cv2.LINE_AA)
                    if show_face and observation.face:
                        for edge in face_edges:
                            a, b = observation.face[edge.start], observation.face[edge.end]
                            cv2.line(frame, (int(a.x * fw), int(a.y * fh)), (int(b.x * fw), int(b.y * fh)), (108, 185, 224), 1)
                        for index, point in enumerate(observation.face):
                            px, py = int(point.x * fw), int(point.y * fh)
                            cv2.circle(frame, (px, py), 1 if show_mesh else 3, (194, 223, 245), -1)
                            if show_indices and index % 2 == 0:
                                cv2.putText(frame, str(index), (px + 2, py), cv2.FONT_HERSHEY_SIMPLEX, .25, (235, 235, 230), 1, cv2.LINE_AA)
                    if self.debug_overlay and self.mode != "anatomy":
                        cv2.rectangle(frame, (8, 8), (min(fw - 8, 330), 34), (28, 39, 51), -1)
                        cv2.putText(frame, "DEBUG · landmarks usados", (16, 27), cv2.FONT_HERSHEY_SIMPLEX, .52, (235, 242, 245), 1, cv2.LINE_AA)
                else:
                    for hand in observation.hands:
                        if self.diagnostics:
                            for a, b in ((0, 5), (5, 6), (6, 7), (7, 8), (0, 9), (9, 10), (10, 11), (11, 12),
                                         (0, 13), (13, 14), (14, 15), (15, 16), (0, 17), (17, 18), (18, 19), (19, 20), (0, 1), (1, 2), (2, 3), (3, 4)):
                                a, b = hand[a], hand[b]
                                cv2.line(frame, (int(a.x * fw), int(a.y * fh)), (int(b.x * fw), int(b.y * fh)), (180, 215, 177), 2)
                        if self.mode in ("pong", "fruit", "camera"):
                            tip = hand[8]
                            cv2.circle(frame, (int(tip.x * fw), int(tip.y * fh)), 7, (180, 215, 177), 2)
                self._preview = pg.image.frombuffer(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).tobytes(), fitted.size, "RGB")
                self._preview_key = key
            self.screen.blit(self._preview, fitted)
        else:
            label = "Sua imagem aparece aqui" if self.args.demo else "Preparando câmera…"
            p.text(label, rect.centerx, rect.centery - 16, 20, WHITE, True)

    def draw_sport(self, rect):
        if not hasattr(self, "_board"):
            self._board = pg.Surface((RIGHT, BOTTOM))
            self._board_painter = Painter(self._board)
        self._board.fill(DARK)
        self.draw_pong(self._board_painter) if self.mode == "pong" else self.draw_fruits(self._board_painter)
        board = self._board.subsurface((LEFT, TOP, WIDTH, HEIGHT))
        self.screen.blit(pg.transform.smoothscale(board, rect.size), rect)

    def draw_expressions(self, observation, now):
        p, target = self.painter, self.game.target
        entry = GUIDE[target]
        face_drawing(self.screen, (816, 176, 100, 100), target, ACCENT)
        p.text("Faça esta expressão", 936, 182, 15, MUTED)
        p.text(entry["name"], 936, 209, 31, bold=True)
        p.wrap(entry["how"], (824, 302, 416, 105), 20)
        p.wrap(entry["tip"], (824, 413, 416, 80), 16, MUTED)
        progress = min(1, self.game.hold / .7)
        p.panel((824, 507, 416, 6), LINE, 2)
        if progress > 0:
            p.panel((824, 507, max(1, round(416 * progress)), 6), ACCENT, 2)
        p.text("Boa! +1 ponto" if self.game.feedback else "Mantenha por 0,7 segundo", 824, 527, 17, ACCENT if self.game.feedback else MUTED)
        self.button("Pular esta (N)", (824, 577, 186, 40), ("skip",))
        self.button("Ver as 7", (1032, 577, 208, 40), ("catalog", "expressions"))
        detected = EXPRESSIONS[observation.expression] if observation.expression is not None and now - observation.captured < .35 else "nenhuma"
        p.text("Expressão estimada: " + detected, 32, 632, 15, MUTED)

    def draw_memes(self, now):
        p, gesture = self.painter, self.memes.current
        entry = gesture_entry(gesture)
        if gesture:
            path = meme_paths().get(gesture)
            if path and path.exists():
                p.image(self.image(path), (824, 174, 416, 295))
            p.text(entry["name"] if entry else gesture, 824, 488, 25, bold=True)
            p.wrap(entry["how"] if entry else "Gesto reconhecido.", (824, 531, 416, 61), 17, MUTED)
        else:
            # Não mostrar uma figurinha aleatória: deixa claro o estado do detector.
            p.panel((824, 174, 416, 295), WASH)
            if self.memes.candidate:
                p.text("Identificando…", 1032, 278, 28, ACCENT, True, True)
                p.wrap("Mantenha o gesto por um instante.", (870, 320, 324, 52), 17, MUTED, True)
            else:
                p.text("Nenhum gesto identificado", 1032, 270, 25, INK, True, True)
                p.wrap("Mostre uma mão ou faça uma expressão diante da câmera.", (870, 315, 324, 75), 17, MUTED, True)
            p.text("O detector está procurando…", 1032, 416, 15, MUTED, True, True)
        self.button("Ver as 15 figurinhas", (824, 598, 416, 40), ("catalog", "memes"))

    def status(self, observation, now):
        if self.camera and self.camera.error:
            return "Câmera indisponível", "Feche outros aplicativos que usam a câmera e volte ao início."
        if self.vision and self.vision.error:
            return "Não foi possível iniciar", "Volte ao início e tente novamente. Detalhes em logs/runtime.log."
        if self.vision and not self.vision.ready.is_set():
            return "Preparando câmera", "Aguarde um instante."
        if self.mode not in ("pong", "fruit", "expressions"):
            return None
        if self.phase == "finished":
            return f"{self.game.score} pontos", f"Recorde: {self.best}. Pressione espaço para jogar de novo."
        if self.phase == "ready":
            return "Tudo pronto?", "Mostre o rosto e pressione espaço." if self.mode == "expressions" else "Mostre a mão e pressione espaço."
        if self.paused:
            return "Pausa", "Pressione P para continuar."
        if not self.tracking(observation, now):
            return "Mostre o rosto" if self.mode == "expressions" else "Mostre a mão", "O tempo está parado enquanto você se posiciona."
        return None

    def draw_game(self, observation, now, fps):
        p = self.painter
        p.text(TITLES[self.mode], 32, 91, 31, bold=True)
        p.text(HELP[self.mode], 32, 136, 16, MUTED)
        if self.debug_overlay and self.mode != "anatomy":
            p.text("DEBUG: pontos e conexões do detector", 430, 136, 14, ACCENT)
        if self.mode in ("pong", "fruit", "expressions"):
            remaining = max(0, math.ceil(self.args.duration - self.elapsed))
            p.text(f"{remaining // 60:02d}:{remaining % 60:02d}", 1068, 93, 29, bold=True)
            p.text(f"{self.game.score} pontos", 1175, 103, 16, ACCENT)
        board, camera = self.layout()
        self.draw_preview(observation, camera)
        if self.mode in ("pong", "fruit"):
            self.draw_sport(board)
            control = (board.x, board.bottom + 18, board.width, 38) if self.camera_large else (camera.x, camera.bottom + 18, camera.width, 38)
            self.button("Câmera menor (C)" if self.camera_large else "Câmera maior (C)", control, ("camera_size",), quiet=True)
        elif self.mode == "expressions":
            self.draw_expressions(observation, now)
        elif self.mode == "memes":
            self.draw_memes(now)
        elif self.mode == "anatomy":
            self.draw_anatomy(observation)
        else:
            p.text("Antes de jogar", 824, 190, 25, bold=True)
            p.wrap("Ilumine rosto e mãos pela frente. Evite uma janela muito clara atrás de você.", (824, 250, 410, 120), 21)
            p.wrap("Afaste-se até as mãos caberem no enquadramento. A resolução da câmera não muda ao ampliar a imagem.", (824, 390, 410, 130), 18, MUTED)
            if self.camera:
                p.text(f"Recebendo {self.camera.fps:.0f} quadros por segundo", 824, 556, 17, MUTED)
        status = self.status(observation, now)
        if status:
            # O aviso não encobre a câmera: ainda é possível se posicionar.
            area = board if self.mode in ("pong", "fruit") else pg.Rect(824, 174, 416, 102)
            if self.mode in ("pong", "fruit"):
                cover = pg.Surface(area.size, pg.SRCALPHA); cover.fill((*DARK, 235))
                self.screen.blit(cover, area)
                p.text(status[0], area.centerx, area.centery - 53, 29, WHITE, True, True)
                p.wrap(status[1], (area.x + 35, area.centery + 6, area.width - 70, 80), 18, WHITE)
            else:
                p.panel(area, WASH)
                p.text(status[0], area.x + 14, area.y + 13, 21, ACCENT, bold=True)
                p.wrap(status[1], (area.x + 14, area.y + 48, area.width - 28, 50), 15, MUTED)
        # Controles de prévia: não alteram resolução nem inferência.
        self.button("Desespelhar" if self.camera_mirror else "Espelhar", (824, 612, 132, 32), ("camera_mirror",), quiet=True)
        self.button("Tamanho real" if self.camera_fill else "Preencher câmera", (966, 612, 150, 32), ("camera_fill",), quiet=True)
        p.rule(655)
        if self.mode in ("pong", "fruit", "expressions"):
            label = "Jogar de novo" if self.phase == "finished" else "Começar" if self.phase == "ready" else "Continuar" if self.paused else "Pausar"
            self.button(label, (32, 668, 158, 36), ("start_pause",), primary=True)
            p.text("Espaço iniciar · P pausar", 209, 677, 14, MUTED)
        else:
            p.text("Câmera ligada apenas neste modo", 32, 677, 14, MUTED)
        if self.diagnostics:
            backend = self.vision.backend if self.vision else "Demonstração"
            p.text(f"{backend} · {fps:.0f} FPS · {observation.inference_ms:.1f} ms", 615, 677, 13, MUTED)
        else:
            p.text("H catálogo · Esc início · F11 tela cheia", 859, 677, 14, MUTED)

    def draw_anatomy(self, observation):
        p = self.painter
        p.text("Mapa ao vivo", 824, 181, 24, bold=True)
        p.text("Mãos: 21 pontos cada · rosto: 478 pontos", 824, 220, 16, MUTED)
        p.text(f"Detectado: {len(observation.hands)} mão(s) · {'1 rosto' if observation.face else 'nenhum rosto'}", 824, 248, 16, ACCENT)
        p.text("Camadas", 824, 292, 16, MUTED, bold=True)
        options = (("hands", "Mãos e ossos"), ("face", "Rosto"), ("mesh", "Malha facial"),
                   ("contours", "Contornos"), ("indices", "Índices"), ("blendshapes", "Blendshapes"))
        for index, (key, label) in enumerate(options):
            x = 824 + (index % 2) * 205
            y = 327 + (index // 2) * 43
            self.button(("✓ " if self.anatomy[key] else "○ ") + label, (x, y, 190, 34), ("anatomy_toggle", key), quiet=True)
        p.text("Todas as conexões são desenhadas na câmera.", 824, 470, 15, MUTED)
        if self.anatomy["blendshapes"] and observation.blendshapes:
            p.text("Maiores blendshapes", 824, 510, 16, MUTED, bold=True)
            top = sorted(observation.blendshapes, key=lambda item: item[1], reverse=True)[:5]
            for index, (name, value) in enumerate(top):
                p.text(f"{name}: {value:.2f}", 824, 538 + index * 20, 14, INK)
        else:
            p.text("Blendshapes aparecem quando rosto é detectado.", 824, 510, 14, MUTED)
        p.text("Câmera é visualização 2D; profundidade não é mostrada.", 824, 635, 14, MUTED)

    def catalog_entries(self):
        return self._memes if self.catalog_tab == "memes" else GUIDE

    def draw_catalog(self):
        p = self.painter
        p.text("Como jogar", 32, 91, 31, bold=True)
        for x, label, tab in ((32, "Figurinhas · 15", "memes"), (237, "Expressões · 7", "expressions"), (442, "Jogos e fontes", "games")):
            self.button(label, (x, 143, 190, 38), ("tab", tab), primary=self.catalog_tab == tab, quiet=self.catalog_tab != tab)
        self.button("Voltar", (1128, 143, 120, 38), ("back_catalog",))
        if self.catalog_tab == "games":
            descriptions = ("Mova o indicador para cima e para baixo. Sua raquete fica à esquerda.",
                            "Deslize o indicador sobre as frutas. Cada fruta vale 1 ponto; bombas tiram 5.",
                            "São 15 gestos. As regras podem se sobrepor; o gesto de maior prioridade vence.",
                            "São 7 categorias estimadas pela aparência. Medo e nojo podem ser difíceis e confundidos.")
            for i, ((title, url), description) in enumerate(zip(SOURCES, descriptions)):
                y = 212 + i * 103
                p.text(title, 32, y, 21, bold=True)
                p.wrap(description, (32, y + 34, 930, 54), 17, MUTED)
                self.button("Abrir referência", (1040, y + 8, 208, 40), ("source", url))
                p.rule(y + 89)
            p.text("Pong e frutas têm implementação própria. As fontes mostram referências e modelos utilizados.", 32, 674, 14, MUTED)
            return
        entries = self.catalog_entries()
        if self.catalog_focus is not None:
            index = self.catalog_focus % len(entries)
            entry = entries[index]
            if self.catalog_tab == "memes":
                p.image(self.image(entry["image"]), (50, 216, 530, 362))
            else:
                face_drawing(self.screen, (160, 230, 300, 300), index, ACCENT)
                p.text("Esquema ilustrativo", 310, 556, 15, MUTED, True)
            p.text(entry["name"], 650, 224, 30, bold=True)
            p.wrap(entry["how"], (650, 283, 560, 127), 23)
            p.wrap(entry["tip"], (650, 429, 560, 118), 18, MUTED)
            if self.catalog_tab == "memes":
                p.text(entry["kind"], 650, 563, 16, ACCENT)
            else:
                p.wrap("A ilustração é uma dica, não um exemplo do conjunto de treino. O modelo pode errar. Use N para pular no jogo.", (650, 562, 560, 70), 15, MUTED)
            self.button("Anterior", (32, 664, 145, 40), ("focus_step", -1))
            p.text(f"{index + 1} de {len(entries)}", 640, 675, 16, MUTED, True)
            self.button("Próxima", (1103, 664, 145, 40), ("focus_step", 1))
            self.button("Ver todas", (894, 143, 214, 38), ("overview",))
            return
        start = self.catalog_page * 6
        for index in range(start, min(start + 6, len(entries))):
            entry = entries[index]
            slot = index - start
            x, y = 32 + (slot % 3) * 416, 212 + (slot // 3) * 211
            rect = pg.Rect(x, y, 384, 194)
            if self.catalog_tab == "memes":
                p.image(self.image(entry["image"]), (x, y, 128, 130))
            else:
                face_drawing(self.screen, (x + 4, y, 116, 116), index, ACCENT)
            p.wrap(entry["name"], (x + 146, y + 3, 234, 70), 21, bold=True)
            p.wrap(entry["how"], (x + 146, y + 71, 234, 82), 15, MUTED, 5)
            p.text("Ver como fazer", x, y + 156, 15, ACCENT)
            p.rule(y + 192, x, x + 384)
            self.buttons.append((rect, ("focus", index)))
        pages = math.ceil(len(entries) / 6)
        if self.catalog_page:
            self.button("Anterior", (32, 664, 145, 40), ("page", -1))
        if self.catalog_page < pages - 1:
            self.button("Próxima", (1103, 664, 145, 40), ("page", 1))
        p.text(f"Página {self.catalog_page + 1} de {pages} · clique para ver instruções", 640, 675, 15, MUTED, True)

    def draw(self, observation, now, fps):
        self.screen.fill(BG)
        self.buttons = []
        self.header()
        if self.scene == "menu":
            self.draw_menu()
        elif self.scene == "catalog":
            self.draw_catalog()
        else:
            self.draw_game(observation, now, fps)

    def toggle_fullscreen(self):
        self._fullscreen = not self._fullscreen
        self.set_display()

    def set_display(self):
        flags = pg.SCALED | (pg.FULLSCREEN if self._fullscreen else pg.RESIZABLE)
        self.screen = pg.display.set_mode(SIZE, flags)
        self.painter = Painter(self.screen)

    def action(self, action):
        name, *values = action
        if name == "quit":
            return False
        if name == "home":
            self.go_home()
        elif name == "play":
            self.select_game(values[0])
        elif name == "fullscreen":
            self.toggle_fullscreen()
        elif name == "catalog":
            if self.scene != "catalog":
                self.open_catalog(values[0] if values else None)
        elif name == "back_catalog":
            self.close_catalog()
        elif name == "tab":
            self.catalog_tab, self.catalog_page, self.catalog_focus = values[0], 0, None
        elif name == "focus":
            self.catalog_focus = values[0]
        elif name == "overview":
            self.catalog_focus = None
        elif name == "focus_step":
            self.catalog_focus = (self.catalog_focus + values[0]) % len(self.catalog_entries())
        elif name == "page":
            self.catalog_page = int(clamp(self.catalog_page + values[0], 0, math.ceil(len(self.catalog_entries()) / 6) - 1))
        elif name == "source":
            webbrowser.open(values[0], new=2)
        elif name == "camera_size":
            self.camera_large = not self.camera_large
            self._preview_key = None
        elif name == "camera_mirror":
            self.camera_mirror = not self.camera_mirror
            self._preview_key = None
        elif name == "camera_fill":
            self.camera_fill = not self.camera_fill
            self._preview_key = None
        elif name == "anatomy_toggle" and self.mode == "anatomy":
            self.anatomy[values[0]] = not self.anatomy[values[0]]
            self._preview_key = None
        elif name == "skip" and self.mode == "expressions":
            self.game.skip()
            self._expression_time = None
        elif name == "start_pause" and self.mode in ("pong", "fruit", "expressions"):
            if self.phase in ("ready", "finished"):
                self.reset()
                self.phase = "playing"
            else:
                self.paused = not self.paused
                self._expression_time = None
        return True

    def handle_event(self, event):
        if event.type == pg.QUIT:
            return False
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            for rect, action in reversed(self.buttons):
                if rect.collidepoint(event.pos):
                    return self.action(action)
        if event.type == pg.MOUSEWHEEL and self.scene == "catalog" and self.catalog_tab != "games":
            return self.action(("focus_step", -event.y)) if self.catalog_focus is not None else self.action(("page", -event.y))
        if event.type != pg.KEYDOWN:
            return True
        key = event.key
        if key in (pg.K_F11, pg.K_f):
            return self.action(("fullscreen",))
        if key in (pg.K_ESCAPE, pg.K_q):
            if self.scene == "catalog":
                self.close_catalog()
            elif self.scene == "game":
                self.go_home()
            else:
                return False
        elif key == pg.K_h:
            self.close_catalog() if self.scene == "catalog" else self.open_catalog()
        elif self.scene == "menu":
            if pg.K_1 <= key <= pg.K_5:
                self.select_game(GAMES[key - pg.K_1])
            elif key == pg.K_6:
                self.select_game("camera")
        elif self.scene == "catalog" and self.catalog_tab != "games":
            if key in (pg.K_LEFT, pg.K_RIGHT):
                step = -1 if key == pg.K_LEFT else 1
                return self.action(("focus_step", step) if self.catalog_focus is not None else ("page", step))
            if key == pg.K_BACKSPACE:
                self.catalog_focus = None
        elif self.scene == "game":
            if key in (pg.K_SPACE, pg.K_RETURN):
                return self.action(("start_pause",))
            if key == pg.K_p and self.phase == "playing":
                return self.action(("start_pause",))
            if key == pg.K_n:
                return self.action(("skip",))
            if key == pg.K_c:
                return self.action(("camera_size",))
            if key == pg.K_m:
                return self.action(("camera_mirror",))
            if key == pg.K_v:
                return self.action(("camera_fill",))
            if key == pg.K_d:
                self.diagnostics = not self.diagnostics
            if key in (pg.K_1, pg.K_2, pg.K_3, pg.K_4, pg.K_5, pg.K_6) and self.mode == "anatomy":
                keymap = {pg.K_1: "hands", pg.K_2: "face", pg.K_3: "mesh", pg.K_4: "contours", pg.K_5: "indices", pg.K_6: "blendshapes"}
                return self.action(("anatomy_toggle", keymap[key]))
        return True

    def run(self):
        pg.display.init()
        pg.font.init()
        self.set_display()
        pg.display.set_caption("Integra Profissões")
        clock = pg.time.Clock()
        started = time.monotonic()
        running = True
        try:
            if self.scene == "game":
                self.start_devices()
            while running:
                dt = min(clock.tick(self.args.fps) / 1000, .05)
                now = time.monotonic()
                for event in pg.event.get():
                    if not self.handle_event(event):
                        running = False
                        break
                observation = self.observation(now) if self.vision or self.scene == "game" else Observation()
                self.update(dt, observation, now)
                self.draw(observation, now, clock.get_fps())
                pg.display.flip()
                if self.args.seconds and now - started >= self.args.seconds:
                    running = False
            if self.args.screenshot:
                path = Path(self.args.screenshot)
                path.parent.mkdir(parents=True, exist_ok=True)
                pg.image.save(self.screen, str(path))
            return 1 if (self.camera and self.camera.error) or (self.vision and self.vision.error) else 0
        finally:
            self.stop_devices()
            pg.quit()
