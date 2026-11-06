"""Navegação e desenho em memória: não abrem janela ou webcam."""
import os
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch
import pygame as pg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from main import parser
from integra.catalog import EXPRESSIONS, meme_catalog
from integra.frontend import Frontend, SIZE
from integra.ui import Painter
from integra.vision import Observation, meme_paths


class FrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pg.font.init()  # Não inicializa vídeo, áudio ou câmera.

    def app(self, mode=None):
        options = ["--demo", "--windowed"] + (["--game", mode] if mode else [])
        app = Frontend(parser().parse_args(options))
        app.screen = pg.Surface(SIZE)
        app.painter = Painter(app.screen)
        return app

    def test_menu_does_not_create_camera_or_pipeline(self):
        with patch("integra.app.Pipeline") as pipeline:
            app = self.app()
            app.draw(Observation(), 100, 60)
            self.assertEqual(app.scene, "menu")
            self.assertIsNone(app.camera)
            pipeline.assert_not_called()
            play_modes = {a[1] for _, a in app.buttons if a[0] == "play"}
            self.assertEqual(play_modes, {"pong", "expressions", "fruit", "memes", "anatomy", "camera"})

    def test_click_opens_game_without_terminal(self):
        app = self.app()
        app.draw(Observation(), 100, 60)
        rect, _ = next((r, a) for r, a in app.buttons if a == ("play", "memes"))
        app.handle_event(pg.event.Event(pg.MOUSEBUTTONDOWN, button=1, pos=rect.center))
        self.assertEqual(app.scene, "game")
        self.assertEqual(app.mode, "memes")

    def test_escape_from_game_closes_pipeline_and_returns_to_menu(self):
        app = self.app("pong")
        pipeline = Mock()
        app.vision = pipeline
        self.assertTrue(app.handle_event(pg.event.Event(pg.KEYDOWN, key=pg.K_ESCAPE)))
        pipeline.close.assert_called_once()
        self.assertEqual(app.scene, "menu")
        self.assertIsNone(app.vision)

    def test_f11_toggles_without_resetting_round(self):
        app = self.app("pong")
        game = app.game
        with patch.object(app, "set_display") as display:
            app.handle_event(pg.event.Event(pg.KEYDOWN, key=pg.K_F11))
            self.assertTrue(app._fullscreen)
            app.handle_event(pg.event.Event(pg.KEYDOWN, key=pg.K_F11))
            self.assertFalse(app._fullscreen)
            self.assertEqual(display.call_count, 2)
        self.assertIs(app.game, game)

    def test_catalog_pauses_round_and_restores_scene(self):
        app = self.app("expressions")
        app.open_catalog()
        app.update(.1, app.observation(100), 100)
        self.assertEqual(app.elapsed, 0)
        self.assertEqual(app.catalog_tab, "expressions")
        app.close_catalog()
        self.assertEqual(app.scene, "game")

    def test_entire_meme_catalog_is_reachable_and_matches_original(self):
        app = self.app()
        app.open_catalog("memes")
        reachable = set()
        for page in range(3):
            app.catalog_page = page
            app.draw(Observation(), 100, 60)
            reachable.update(a[1] for _, a in app.buttons if a[0] == "focus")
        self.assertEqual(reachable, set(range(15)))
        self.assertEqual({m["key"] for m in meme_catalog()}, set(meme_paths()))
        self.assertTrue(all(m["image"].is_file() for m in meme_catalog()))

    def test_all_expression_references_and_details_render_offscreen(self):
        app = self.app()
        app.open_catalog("expressions")
        self.assertEqual(len(EXPRESSIONS), 7)
        for index in range(7):
            app.catalog_focus = index
            app.draw(Observation(), 100, 60)
        app.action(("focus_step", 1))
        self.assertEqual(app.catalog_focus, 0)

    def test_camera_is_larger_and_can_be_expanded_without_changing_capture(self):
        app = self.app("pong")
        capture_size = (app.args.width, app.args.height)
        _, small = app.layout()
        app.action(("camera_size",))
        _, large = app.layout()
        self.assertGreater(small.width * small.height, 2 * 300 * 225)
        self.assertGreater(large.width * large.height, small.width * small.height)
        self.assertEqual((app.args.width, app.args.height), capture_size)

    def test_every_mode_renders_offscreen(self):
        for mode in ("pong", "fruit", "memes", "expressions", "camera", "anatomy"):
            app = self.app(mode)
            app.draw(app.observation(100), 100, 60)
            self.assertEqual(app.screen.get_size(), SIZE)

    def test_default_fullscreen_and_explicit_windowed(self):
        self.assertTrue(parser().parse_args([]).fullscreen)
        self.assertFalse(parser().parse_args(["--windowed"]).fullscreen)

    def test_debug_overlay_is_opt_in(self):
        self.assertFalse(parser().parse_args([]).debug_overlay)
        self.assertTrue(parser().parse_args(["--debug-overlay"]).debug_overlay)
        self.assertTrue(parser().parse_args(["--show-skeleton"]).debug_overlay)
        app = self.app("pong")
        self.assertFalse(app.debug_overlay)

    def test_camera_preview_controls_are_independent(self):
        app = self.app("memes")
        self.assertTrue(app.camera_mirror)
        self.assertFalse(app.camera_fill)
        app.action(("camera_mirror",))
        app.action(("camera_fill",))
        self.assertFalse(app.camera_mirror)
        self.assertTrue(app.camera_fill)

    def test_anatomy_mode_has_configurable_layers(self):
        app = self.app("anatomy")
        self.assertTrue(app.anatomy["hands"])
        app.action(("anatomy_toggle", "indices"))
        self.assertTrue(app.anatomy["indices"])
        app.action(("anatomy_toggle", "mesh"))
        self.assertFalse(app.anatomy["mesh"])
        app.draw(app.observation(100), 100, 60)


if __name__ == "__main__":
    unittest.main()
