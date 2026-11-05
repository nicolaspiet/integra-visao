"""Elementos visuais simples e independentes de câmera."""
from functools import lru_cache
import math
import pygame as pg

BG = (244, 243, 238)
PAPER = (255, 254, 250)
INK = (35, 39, 34)
MUTED = (105, 110, 102)
LINE = (216, 219, 209)
ACCENT = (65, 91, 66)
WASH = (232, 236, 225)
DARK = (30, 36, 32)
WHITE = (251, 251, 245)
CORAL = (185, 91, 67)


class Painter:
    def __init__(self, screen):
        self.screen = screen

    @lru_cache(maxsize=32)
    def font(self, size, bold=False):
        return pg.font.SysFont("DejaVu Sans", size, bold=bold)

    @lru_cache(maxsize=512)
    def rendered(self, text, size, color, bold=False):
        return self.font(size, bold).render(str(text), True, color)

    def text(self, text, x, y, size=20, color=INK, center=False, bold=False):
        image = self.rendered(str(text), size, color, bold)
        rect = image.get_rect(midtop=(x, y)) if center else image.get_rect(topleft=(x, y))
        self.screen.blit(image, rect)
        return rect

    def wrap(self, text, rect, size=18, color=INK, spacing=7, bold=False):
        rect = pg.Rect(rect)
        words, lines, current = str(text).split(), [], ""
        for word in words:
            candidate = (current + " " + word).strip()
            if current and self.font(size, bold).size(candidate)[0] > rect.width:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
        y = rect.y
        for line in lines:
            if y + size > rect.bottom:
                break
            self.text(line, rect.x, y, size, color, bold=bold)
            y += size + spacing
        return y

    def rule(self, y, x=32, right=1248):
        pg.draw.line(self.screen, LINE, (x, y), (right, y))

    def panel(self, rect, color=PAPER, radius=4):
        pg.draw.rect(self.screen, color, rect, border_radius=radius)

    def image(self, image, rect):
        rect = pg.Rect(rect)
        fitted = image.get_rect().fit(rect)
        fitted.center = rect.center
        scaled = pg.transform.smoothscale(image, fitted.size)
        self.screen.blit(scaled, fitted)
        return fitted


def face_drawing(surface, rect, expression, color=INK):
    """Esquema didático; não representa exemplos ou limiares do modelo."""
    rect = pg.Rect(rect)
    unit = min(rect.width, rect.height) / 120
    cx, cy = rect.center
    def point(x, y):
        return (round(cx + x * unit), round(cy + y * unit))
    def line(a, b, width=2):
        pg.draw.line(surface, color, point(*a), point(*b), max(1, round(width * unit)))
    pg.draw.circle(surface, color, (cx, cy), round(49 * unit), max(1, round(2 * unit)))
    wide = expression in (2, 6)
    for sign in (-1, 1):
        eye = pg.Rect(0, 0, round(10 * unit), round((14 if wide else 7) * unit))
        eye.center = point(sign * 18, -8)
        pg.draw.ellipse(surface, color, eye, max(1, round(2 * unit)))
        pg.draw.circle(surface, color, point(sign * 18, -8), max(1, round(2 * unit)))
    if expression == 0:
        line((-29, -25), (-10, -17), 3); line((10, -17), (29, -25), 3)
    elif expression in (2, 5):
        line((-29, -22), (-10, -29), 3); line((10, -29), (29, -22), 3)
    elif expression == 6:
        line((-29, -30), (-10, -31), 3); line((10, -31), (29, -30), 3)
    elif expression == 1:
        line((-29, -20), (-10, -18), 3); line((10, -24), (29, -21), 3)
        line((-5, 4), (0, 0)); line((0, 0), (5, 4))
    else:
        line((-29, -23), (-10, -25)); line((10, -25), (29, -23))
    if expression == 6:
        mouth = pg.Rect(0, 0, round(19 * unit), round(24 * unit)); mouth.center = point(0, 24)
        pg.draw.ellipse(surface, color, mouth, max(1, round(2 * unit)))
    elif expression == 3:
        points = [point(x, 18 + 12 * (1 - (x / 23) ** 2)) for x in range(-23, 24, 2)]
        pg.draw.lines(surface, color, False, points, max(1, round(3 * unit)))
    elif expression == 5:
        points = [point(x, 28 - 10 * (1 - (x / 22) ** 2)) for x in range(-22, 23, 2)]
        pg.draw.lines(surface, color, False, points, max(1, round(3 * unit)))
    elif expression == 2:
        mouth = pg.Rect(0, 0, round(37 * unit), round(10 * unit)); mouth.center = point(0, 24)
        pg.draw.ellipse(surface, color, mouth, max(1, round(2 * unit)))
    elif expression == 1:
        line((-21, 25), (0, 16), 3); line((0, 16), (21, 20), 3)
    else:
        line((-20, 24), (20, 24), 3)
