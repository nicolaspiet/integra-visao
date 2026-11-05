"""Integração de relógio/rastreamento, sem câmera e sem janela."""
import os
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from main import parser
from integra.app import App
from integra.vision import Observation


class RuntimeTests(unittest.TestCase):
    def app(self, mode):
        args = parser().parse_args(["--game", mode, "--duration", "1"])
        app = App(args)
        app.phase = "playing"
        return app

    def test_missing_or_stale_hand_freezes_timer(self):
        app = self.app("pong")
        tip = SimpleNamespace(x=.5, y=.5)
        app.update(.1, Observation(), 100)
        app.update(.1, Observation(captured=98, hands=((tip,) * 21,)), 100)
        self.assertEqual(app.elapsed, 0)
        app.update(.1, Observation(captured=100, hands=((tip,) * 21,)), 100)
        self.assertAlmostEqual(app.elapsed, .1)

    def test_manual_pause_freezes_timer(self):
        app = self.app("pong")
        app.paused = True
        tip = SimpleNamespace(x=.5, y=.5)
        app.update(.1, Observation(captured=100, hands=((tip,) * 21,)), 100)
        self.assertEqual(app.elapsed, 0)

    def test_losing_hand_breaks_swipe_instead_of_cutting_across_screen(self):
        app = self.app("fruit")
        app.game.previous = (200, 300)
        app.update(.1, Observation(), 100)
        self.assertIsNone(app.game.previous)

    def test_onnx_classifier_returns_seven_finite_scores(self):
        import numpy as np
        from integra.vision import ExpressionModel
        model = ExpressionModel()
        face = [SimpleNamespace(x=.5, y=.5) for _ in range(478)]
        for index, x, y in ((33, .3, .35), (133, .4, .35), (362, .6, .35),
                            (263, .7, .35), (1, .5, .5), (61, .4, .7), (291, .6, .7)):
            face[index] = SimpleNamespace(x=x, y=y)
        label, scores = model.classify(np.zeros((480, 640, 3), np.uint8), face)
        self.assertIn(label, range(7))
        self.assertEqual(len(scores), 7)
        self.assertTrue(np.isfinite(scores).all())
        self.assertAlmostEqual(sum(scores), 1, places=5)


if __name__ == "__main__":
    unittest.main()
