"""Regras dos jogos, sem dependência de câmera ou renderização."""
from __future__ import annotations

from dataclasses import dataclass
import math
import random

LEFT, TOP, WIDTH, HEIGHT = 48, 180, 820, 430
RIGHT, BOTTOM = LEFT + WIDTH, TOP + HEIGHT


def clamp(value, low, high):
    return max(low, min(high, value))


def segment_distance(point, start, end):
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = dx * dx + dy * dy
    t = clamp(((point[0] - start[0]) * dx + (point[1] - start[1]) * dy) / length, 0, 1) if length else 0
    return math.hypot(point[0] - start[0] - t * dx, point[1] - start[1] - t * dy)


class Pong:
    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.score = self.opponent = self.hits = 0
        self.player_y = self.ai_y = TOP + HEIGHT / 2
        self.trail = []
        self.serve()

    def serve(self):
        self.x, self.y = LEFT + WIDTH / 2, TOP + HEIGHT / 2
        self.vx = self.rng.choice((-1, 1)) * 380
        self.vy = self.rng.uniform(-150, 150)
        self.wait = .65
        self.trail.clear()

    def update(self, dt, target_y):
        if target_y is not None:
            target = TOP + clamp((target_y - .12) / .76, 0, 1) * HEIGHT
            self.player_y += (target - self.player_y) * (1 - math.exp(-24 * dt))
        self.player_y = clamp(self.player_y, TOP + 49, BOTTOM - 49)
        aim = self.y if self.vx > 0 else TOP + HEIGHT / 2
        self.ai_y += clamp(aim - self.ai_y, -245 * dt, 245 * dt)
        self.ai_y = clamp(self.ai_y, TOP + 49, BOTTOM - 49)
        if self.wait > 0:
            self.wait -= dt
            return
        # Subpassos limitam avanço para impedir atravessar raquetes.
        steps = max(1, math.ceil(abs(self.vx) * dt / 8))
        for _ in range(steps):
            self.x += self.vx * dt / steps
            self.y += self.vy * dt / steps
            if self.y < TOP + 9:
                self.y, self.vy = TOP + 9, abs(self.vy)
            elif self.y > BOTTOM - 9:
                self.y, self.vy = BOTTOM - 9, -abs(self.vy)
            for x, y, outgoing in ((LEFT + 42, self.player_y, 1), (RIGHT - 42, self.ai_y, -1)):
                if self.vx * outgoing < 0 and abs(self.x - x) <= 17 and abs(self.y - y) < 58:
                    self.x = x + outgoing * 18
                    speed = min(780, math.hypot(self.vx, self.vy) * 1.055)
                    angle = clamp((self.y - y) / 49, -.95, .95) * 1.0
                    self.vx, self.vy = outgoing * speed * math.cos(angle), speed * math.sin(angle)
                    if outgoing == 1:
                        self.hits += 1
            if self.x < LEFT - 15 or self.x > RIGHT + 15:
                if self.x > RIGHT:
                    self.score += 1
                else:
                    self.opponent += 1
                self.serve()
                return
        self.trail.append((self.x, self.y))
        del self.trail[:-12]


@dataclass
class Fruit:
    x: float
    y: float
    vx: float
    vy: float
    radius: int
    color: tuple
    bomb: bool = False


class Fruits:
    COLORS = ((255, 104, 117), (255, 193, 85), (113, 226, 158), (174, 149, 255))

    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.items = []
        self.particles = []
        self.trail = []
        self.spawn = .2
        self.score, self.combo = 0, 0
        self.previous = None

    def update(self, dt, cursor):
        self.spawn -= dt
        if self.spawn <= 0:
            self.spawn = self.rng.uniform(.45, .8)
            self.items.append(Fruit(self.rng.uniform(LEFT + 100, RIGHT - 100), BOTTOM + 30,
                                    self.rng.uniform(-100, 100), -self.rng.uniform(540, 690),
                                    self.rng.randint(24, 34), self.rng.choice(self.COLORS), self.rng.random() < .15))
        if cursor:
            self.trail.append(cursor)
        else:
            self.trail.clear()
        del self.trail[:-10]
        start = self.previous if self.previous is not None else cursor
        remaining = []
        for fruit in self.items:
            fruit.x += fruit.vx * dt
            fruit.y += fruit.vy * dt
            fruit.vy += 720 * dt
            if cursor and start and segment_distance((fruit.x, fruit.y), start, cursor) <= fruit.radius + 5:
                self.score = max(0, self.score + (-5 if fruit.bomb else 1))
                self.combo = 0 if fruit.bomb else self.combo + 1
                for _ in range(14):
                    self.particles.append([fruit.x, fruit.y, self.rng.uniform(-220, 220),
                                           self.rng.uniform(-230, 120), .6, fruit.color])
            elif fruit.y < BOTTOM + 90:
                remaining.append(fruit)
        self.items = remaining
        live = []
        for particle in self.particles:
            particle[0] += particle[2] * dt
            particle[1] += particle[3] * dt
            particle[3] += 450 * dt
            particle[4] -= dt
            if particle[4] > 0:
                live.append(particle)
        self.particles = live
        self.previous = cursor


class Expressions:
    TARGETS = (3, 6, 5, 0, 4, 2, 1)

    def __init__(self):
        self.score, self.index = 0, 0
        self.hold = self.elapsed = 0.0
        self.last_sequence = -1
        self.feedback = 0.0

    @property
    def target(self):
        return self.TARGETS[self.index % len(self.TARGETS)]

    def skip(self):
        self.index += 1
        self.hold = self.elapsed = 0

    def update(self, dt, expression, confidence, fresh, sequence):
        self.elapsed += dt
        self.feedback = max(0, self.feedback - dt)
        # Integra tempo somente de resultados novos e recentes, nunca de um rosto congelado.
        if fresh and sequence != self.last_sequence:
            self.last_sequence = sequence
            if expression == self.target and confidence >= .38:
                self.hold += min(dt, .15)
            else:
                self.hold = max(0, self.hold - .12)
        elif not fresh:
            self.hold = 0
        if self.hold >= .7:
            self.score += 1
            self.feedback = .8
            self.skip()
        elif self.elapsed > 9:
            self.skip()


class MemeState:
    def __init__(self):
        self.current = self.candidate = None
        self.since = self.idle = 0.0

    def update(self, gesture, now):
        if gesture != self.candidate:
            self.candidate, self.since = gesture, now
        if now - self.since >= .15:
            self.current = gesture
        if gesture:
            self.idle = now
        return self.current
