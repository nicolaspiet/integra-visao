import math
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from integra.games import BOTTOM, LEFT, RIGHT, TOP, Expressions, Fruit, Fruits, MemeState, Pong, segment_distance


class GameTests(unittest.TestCase):
    def test_fast_ball_bounces_instead_of_tunneling_through_paddle(self):
        game = Pong(random.Random(1))
        game.wait = 0
        game.x, game.y = LEFT + 90, game.player_y
        game.vx, game.vy = -780, 0
        game.update(.1, .5)
        self.assertGreater(game.vx, 0)
        self.assertEqual(game.hits, 1)
        self.assertEqual(game.opponent, 0)

    def test_goal_counts_once_and_resets_ball(self):
        game = Pong(random.Random(1))
        game.wait = 0
        game.x, game.y = RIGHT + 14, TOP + 10
        game.vx, game.vy = 400, 0
        game.update(.02, None)
        self.assertEqual(game.score, 1)
        game.update(.02, None)
        self.assertEqual(game.score, 1)
        self.assertGreater(game.wait, 0)

    def test_frame_independent_paddle_smoothing(self):
        slow, fast = Pong(), Pong()
        for _ in range(30):
            slow.update(1 / 30, .7)
        for _ in range(120):
            fast.update(1 / 120, .7)
        self.assertAlmostEqual(slow.player_y, fast.player_y, places=5)

    def test_swipe_hits_fruit_between_two_cursor_samples(self):
        game = Fruits(random.Random(1))
        game.spawn = 10
        game.items = [Fruit(300, 350, 0, 0, 25, (255, 0, 0))]
        game.previous = (200, 350)
        game.update(0, (400, 350))
        self.assertEqual(game.score, 1)
        self.assertEqual(game.items, [])

    def test_bomb_penalty_and_missing_hand_does_not_cut(self):
        game = Fruits()
        game.spawn = 10
        game.score = 8
        game.items = [Fruit(300, 350, 0, 0, 25, (0, 0, 0), True)]
        game.update(0, None)
        self.assertEqual(game.score, 8)
        game.update(0, (300, 350))
        self.assertEqual(game.score, 3)

    def test_frozen_expression_result_cannot_score(self):
        game = Expressions()
        for _ in range(100):
            game.update(.05, 3, .9, True, 1)
        self.assertEqual(game.score, 0)

    def test_expression_requires_new_confident_results(self):
        game = Expressions()
        for sequence in range(25):
            game.update(1 / 30, 3, .9, True, sequence)
        self.assertEqual(game.score, 1)
        self.assertEqual(game.target, 6)

    def test_lost_face_clears_expression_hold(self):
        game = Expressions()
        game.update(.1, 3, .9, True, 1)
        game.update(.1, None, 0, False, 2)
        self.assertEqual(game.hold, 0)

    def test_meme_transition_is_stable(self):
        state = MemeState()
        state.update("Gato joia", 1)
        self.assertIsNone(state.update("Gato joia", 1.1))
        self.assertEqual(state.update("Gato joia", 1.2), "Gato joia")
        self.assertEqual(state.update("Outro", 1.21), "Gato joia")

    def test_meme_short_detection_gap_keeps_last_result(self):
        state = MemeState()
        state.update("Gato joia", 1)
        self.assertEqual(state.update("Gato joia", 1.2), "Gato joia")
        self.assertEqual(state.update(None, 1.4), "Gato joia")
        self.assertIsNone(state.update(None, 1.9))

    def test_segment_distance_handles_stationary_cursor(self):
        self.assertEqual(segment_distance((3, 4), (0, 0), (0, 0)), 5)


if __name__ == "__main__":
    unittest.main()
