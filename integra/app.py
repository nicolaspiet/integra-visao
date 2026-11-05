"""Estado compartilhado dos jogos e regras de atualização, sem abrir janelas."""
from pathlib import Path
from types import SimpleNamespace
import json
import math
import pygame as pg
from .games import BOTTOM, HEIGHT, LEFT, RIGHT, TOP, WIDTH, Expressions, Fruits, MemeState, Pong, clamp
from .vision import ROOT, Observation
from .pipeline import Pipeline
INK = (246, 246, 237)
TEAL = (183, 213, 164)
CORAL = (204, 157, 127)

def save_record(mode, score, demo=False):
    path = ROOT / 'data/records.json'
    try:
        records = json.loads(path.read_text()) if path.exists() else {}
        if not isinstance(records, dict):
            records = {}
    except (OSError, ValueError):
        records = {}
    previous = records.get(mode, 0)
    if not isinstance(previous, int):
        previous = 0
    best = max(previous, int(score))
    if not demo and best > previous:
        path.parent.mkdir(exist_ok=True)
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps({**records, mode: best}, ensure_ascii=False, indent=2))
        temporary.replace(path)
    return best

class App:

    def __init__(self, args):
        self.args = args
        self.mode = args.game
        self.camera = self.vision = None
        self._preview_seq = -1
        self._preview = None
        self._fullscreen = False
        self.best = save_record(self.mode, 0, demo=True)
        self.images = {}
        self.memes = MemeState()
        self.reset()

    def reset(self):
        self.game = Pong() if self.mode == 'pong' else Fruits() if self.mode == 'fruit' else Expressions()
        self.elapsed = 0.0
        self.phase = 'playing' if self.args.demo or self.mode == 'anatomy' else 'ready'
        self.paused = False
        self._expression_time = None

    def start_devices(self):
        if not self.args.demo:
            self.vision = Pipeline(self.args)
            self.camera = self.vision.camera
            self.vision.start()

    def observation(self, now):
        if self.vision:
            return self.vision.poll()
        x = 0.5 + 0.35 * math.sin(now * 1.7)
        y = 0.5 + 0.3 * math.sin(now * 2.1)
        hand = tuple((SimpleNamespace(x=x + i % 4 * 0.012, y=y + i // 4 * 0.012) for i in range(21)))
        if self.mode == 'pong':
            hand = tuple((SimpleNamespace(x=0.5, y=(self.game.y - TOP) / HEIGHT * 0.76 + 0.12) for _ in range(21)))
        expression = self.game.target if self.mode == 'expressions' else 3
        probabilities = tuple((0.94 if i == expression else 0.01 for i in range(7)))
        return Observation(int(now * 30), now, None, (hand,), (1,), expression, probabilities, 'Gato joia', 0)

    def tracking(self, observation, now):
        fresh = observation.captured > 0 and now - observation.captured < 0.35
        present = bool(observation.face) if self.mode == 'expressions' else bool(observation.hands)
        return fresh and present

    def update(self, dt, observation, now):
        tracked = self.tracking(observation, now)
        if self.mode == 'memes':
            self.memes.update(observation.gesture if now - observation.captured < 0.35 else None, now)
            return
        if self.mode == 'camera' or self.phase != 'playing' or self.paused or (not tracked):
            if self.mode == 'fruit':
                self.game.previous = None
            if self.mode == 'expressions':
                self._expression_time = None
                self.game.hold = 0
            return
        dt = min(dt, max(0, self.args.duration - self.elapsed))
        self.elapsed += dt
        tip = observation.hands[0][8] if observation.hands else None
        if self.mode == 'pong':
            self.game.update(dt, tip.y if tip else None)
        elif self.mode == 'fruit':
            cursor = (LEFT + clamp((tip.x - 0.08) / 0.84, 0, 1) * WIDTH, TOP + clamp((tip.y - 0.08) / 0.84, 0, 1) * HEIGHT) if tip else None
            self.game.update(dt, cursor)
        else:
            delta = 0.0
            if observation.sequence != self.game.last_sequence:
                delta = min(0.15, observation.captured - self._expression_time) if self._expression_time else 0
                self._expression_time = observation.captured
            confidence = max(observation.probabilities, default=0)
            self.game.update(delta, observation.expression, confidence, tracked, observation.sequence)
        if self.elapsed >= self.args.duration:
            self.phase = 'finished'
            self.best = save_record(self.mode, self.game.score, self.args.demo)

    def draw_pong(self, p):
        game = self.game
        for y in range(TOP + 12, BOTTOM - 5, 24):
            pg.draw.rect(p.screen, (47, 60, 80), (LEFT + WIDTH // 2 - 2, y, 4, 12), border_radius=2)
        p.text(str(game.score), LEFT + WIDTH // 2 - 78, TOP + 14, 48, TEAL, True)
        p.text(str(game.opponent), LEFT + WIDTH // 2 + 78, TOP + 14, 48, CORAL, True)
        for i, (x, y) in enumerate(game.trail):
            pg.draw.circle(p.screen, (35 + i * 5, 57 + i * 8, 65 + i * 8), (int(x), int(y)), max(2, i // 2))
        pg.draw.rect(p.screen, TEAL, (LEFT + 34, game.player_y - 49, 16, 98), border_radius=8)
        pg.draw.rect(p.screen, CORAL, (RIGHT - 50, game.ai_y - 49, 16, 98), border_radius=8)
        pg.draw.circle(p.screen, INK, (int(game.x), int(game.y)), 9)

    def draw_fruits(self, p):
        for fruit in self.game.items:
            pos = (int(fruit.x), int(fruit.y))
            pg.draw.circle(p.screen, (55, 64, 84) if fruit.bomb else fruit.color, pos, fruit.radius)
            if fruit.bomb:
                p.text('!', pos[0], pos[1] - 20, 28, CORAL, True)
                pg.draw.line(p.screen, CORAL, (pos[0], pos[1] - fruit.radius), (pos[0] + 10, pos[1] - fruit.radius - 12), 4)
            else:
                pg.draw.ellipse(p.screen, TEAL, (pos[0] - 1, pos[1] - fruit.radius - 9, 17, 9))
                pg.draw.circle(p.screen, INK, (pos[0] - 8, pos[1] - 9), 4)
        for x, y, _, _, life, color in self.game.particles:
            pg.draw.circle(p.screen, color, (int(x), int(y)), max(1, int(life * 9)))
        for i in range(1, len(self.game.trail)):
            pg.draw.line(p.screen, TEAL, self.game.trail[i - 1], self.game.trail[i], max(2, i))
        p.text(f'{self.game.score} frutas', LEFT + 24, TOP + 14, 32, TEAL)
