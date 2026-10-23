"""Testes essenciais do grid duplo e da colisão, sem abrir janela."""

import os
import unittest

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

if __package__:
    from .dual_grid import DualGrid, TILE_SIZE
    from .main import App
    from .player import Player
else:
    from dual_grid import DualGrid, TILE_SIZE
    from main import App
    from player import Player


class GridTests(unittest.TestCase):
    def setUp(self):
        self.world = DualGrid(width=5, height=4)

    def test_sixteen_corner_combinations(self):
        corners = ((1, 1, 8), (2, 1, 4), (1, 2, 2), (2, 2, 1))
        for combination in range(16):
            with self.subTest(combination=combination):
                self.world.clear()
                for col, row, bit in corners:
                    self.world.set_cell(col, row, bool(combination & bit))
                self.assertEqual(self.world.mask_at(2, 2), combination)
                self.assertEqual(self.world.render_ids[2][2], combination)

    def test_visual_grid_dimensions_and_half_cell_offset(self):
        self.assertEqual(len(self.world.render_ids), 5)
        self.assertTrue(all(len(row) == 6 for row in self.world.render_ids))
        self.assertEqual(self.world.render_position(0, 0), (-20, -20))
        self.assertEqual(self.world.render_position(1, 1), (20, 20))

    def test_sprites_are_distinct_and_masks_match_the_corners(self):
        world = self.world
        self.assertEqual(len({pygame.image.tostring(s, "RGB") for s in world.sprites}), 16)
        self.assertEqual(world.tile_masks[0].count(), 0)
        self.assertEqual(world.tile_masks[15].count(), TILE_SIZE ** 2)
        corners = ((1, 1, 8), (38, 1, 4), (1, 38, 2), (38, 38, 1))
        for combination, mask in enumerate(world.tile_masks):
            for x, y, bit in corners:
                self.assertEqual(bool(mask.get_at((x, y))), bool(combination & bit))

    def test_diagonal_water_is_separate(self):
        for combination in (6, 9):
            mask = self.world.tile_masks[combination]
            self.assertEqual(len(mask.connected_components()), 2)
            self.assertFalse(mask.get_at((20, 20)))

    def test_map_edges_and_outside_cells(self):
        world = self.world
        self.assertEqual(world.get_cell(-1, 0), 0)
        self.assertFalse(world.set_cell(5, 4, True))
        world.set_cell(0, 0, True)
        world.set_cell(4, 3, True)
        self.assertEqual(world.render_ids[0][0], 1)
        self.assertEqual(world.render_ids[-1][-1], 8)
        expected = pygame.mask.Mask((world.pixel_width, world.pixel_height))
        for vy, row in enumerate(world.render_ids):
            for vx, tile in enumerate(row):
                expected.draw(world.tile_masks[tile], world.render_position(vx, vy))
        self.assertEqual(world.solid_mask.count(), expected.count())
        self.assertEqual(world.solid_mask.overlap_area(expected, (0, 0)), expected.count())

    def test_edit_and_erase_update_the_four_tiles_and_collision(self):
        world = self.world
        self.assertTrue(world.set_cell(2, 1, True))
        changed = {(x, y): value for y, row in enumerate(world.render_ids)
                   for x, value in enumerate(row) if value}
        self.assertEqual(changed, {(2, 1): 1, (3, 1): 2, (2, 2): 4, (3, 2): 8})
        self.assertTrue(world.solid_mask.get_at((100, 60)))
        self.assertTrue(world.set_cell(2, 1, False))
        self.assertEqual(world.solid_mask.count(), 0)
        self.assertFalse(any(map(any, world.render_ids)))

    def test_player_walks_on_grass_without_crossing_water(self):
        world = self.world
        player = Player((60, 100), radius=10, speed=190)
        self.assertFalse(player.move(world, (1, 0), 0.25))
        self.assertAlmostEqual(player.position.x, 107.5)
        for row in range(world.height):
            world.set_cell(3, row, True)
        self.assertTrue(player.move(world, (1, 0), 2.0))
        self.assertLess(player.position.x, 3 * TILE_SIZE)
        self.assertFalse(player.collides(world, player.position))
        self.assertTrue(player.collides(world, (0, 100)))


class AppTests(unittest.TestCase):
    def setUp(self):
        self.app = App()
        self.app.action("clear")

    def tearDown(self):
        pygame.quit()

    def emit(self, *events):
        for event in events:
            pygame.event.post(event)
        for event in pygame.event.get():
            self.app.handle_event(event)

    def point(self, col, row):
        return (self.app.map_rect.x + col * TILE_SIZE + 20,
                self.app.map_rect.y + row * TILE_SIZE + 20)

    def drag(self, start, end, button):
        self.emit(
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=start, button=button),
            pygame.event.Event(pygame.MOUSEMOTION, pos=end, rel=(0, 0),
                               buttons=(button == 1, False, button == 3)),
            pygame.event.Event(pygame.MOUSEBUTTONUP, pos=end, button=button),
        )

    def test_mouse_drag_paints_and_erases_every_intermediate_cell(self):
        start, end = self.point(4, 4), self.point(10, 4)
        self.drag(start, end, 1)
        self.assertTrue(all(self.app.world.get_cell(x, 4) for x in range(4, 11)))
        self.assertGreater(self.app.world.solid_mask.count(), 0)
        self.drag(end, start, 3)
        self.assertFalse(any(map(any, self.app.world.cells)))
        self.assertEqual(self.app.world.solid_mask.count(), 0)

    def test_painting_over_player_is_reverted(self):
        world = self.app.world
        before = pygame.image.tostring(world.surface, "RGB")
        player = self.app.player
        point = self.point(int(player.position.x // TILE_SIZE),
                           int(player.position.y // TILE_SIZE))
        self.drag(point, point, 1)
        self.assertFalse(any(map(any, world.cells)))
        self.assertFalse(any(map(any, world.render_ids)))
        self.assertEqual(world.solid_mask.count(), 0)
        self.assertEqual(pygame.image.tostring(world.surface, "RGB"), before)
        self.assertFalse(player.collides(world, player.position))


if __name__ == "__main__":
    unittest.main()
