"""Grid dupla: cada sprite consulta os quatro cantos da grade lógica."""

from pathlib import Path

import pygame


TILE_SIZE = 40
TL, TR, BL, BR = 8, 4, 2, 1
ASSETS = Path(__file__).resolve().parent / "assets"

# Recortes de 8x8 da grama, para os cantos TL, TR, BL e BR da sprite visual.
# Em cada linha: isolado, vizinho horizontal, vertical, canto interno, cheio.
GRASS_PARTS = [
    [(40, 40), (24, 40), (40, 24), (88, 24), (24, 24)],
    [(0, 40), (16, 40), (0, 24), (96, 24), (16, 24)],
    [(40, 0), (24, 0), (40, 16), (88, 32), (24, 16)],
    [(0, 0), (16, 0), (0, 16), (96, 32), (16, 16)],
]


def make_tileset(tile_size=TILE_SIZE):
    if tile_size < 2 or tile_size % 2:
        raise ValueError("O tamanho do tile deve ser um inteiro par maior ou igual a 2.")

    grass_sheet = pygame.image.load(str(ASSETS / "grass.png"))
    water_sheet = pygame.image.load(str(ASSETS / "water.png"))
    water = water_sheet.subsurface((0, 0, 16, 16))
    bits = ((TL, TR), (BL, BR))
    sprites, masks = [], []
    for tile_id in range(16):
        grass = pygame.Surface((16, 16), pygame.SRCALPHA)
        for row in range(2):
            for col in range(2):
                if tile_id & bits[row][col]:
                    continue  # Canto de água: deixa aparecer o fundo.
                horizontal = not (tile_id & bits[row][1 - col])
                vertical = not (tile_id & bits[1 - row][col])
                part = int(horizontal) + 2 * int(vertical)
                if part == 3 and not (tile_id & bits[1 - row][1 - col]):
                    part = 4
                x, y = GRASS_PARTS[row * 2 + col][part]
                grass.blit(grass_sheet, (col * 8, row * 8), (x, y, 8, 8))
        # A máscara bloqueia somente onde a grama é transparente: a água.
        grass = pygame.transform.scale(grass, (tile_size, tile_size))
        sprite = pygame.transform.scale(water, (tile_size, tile_size))
        sprite.blit(grass, (0, 0))
        solid = pygame.mask.from_surface(grass)
        solid.invert()
        sprites.append(sprite)
        masks.append(solid)
    return sprites, masks


class DualGrid:
    def __init__(self, width=18, height=12, tile_size=TILE_SIZE):
        if width < 1 or height < 1:
            raise ValueError("A grade precisa de pelo menos uma linha e uma coluna.")
        self.width = width
        self.height = height
        self.tile_size = tile_size
        self.pixel_width = width * tile_size
        self.pixel_height = height * tile_size
        self.cells = [[0] * width for _ in range(height)]
        self.sprites, self.tile_masks = make_tileset(tile_size)
        self.render_ids = [[0] * (width + 1) for _ in range(height + 1)]
        self.surface = pygame.Surface((self.pixel_width, self.pixel_height))
        self.solid_mask = pygame.mask.Mask((self.pixel_width, self.pixel_height))
        self.rebuild()

    def get_cell(self, col, row):
        if 0 <= col < self.width and 0 <= row < self.height:
            return self.cells[row][col]
        return 0

    def mask_at(self, vx, vy):
        # Somamos os pesos dos quatro cantos para escolher a sprite.
        return (
            self.get_cell(vx - 1, vy - 1) * TL
            + self.get_cell(vx, vy - 1) * TR
            + self.get_cell(vx - 1, vy) * BL
            + self.get_cell(vx, vy) * BR
        )

    def render_position(self, vx, vy):
        # A grade visual fica deslocada meia célula em relação à lógica.
        half = self.tile_size // 2
        return vx * self.tile_size - half, vy * self.tile_size - half

    def set_cell(self, col, row, solid):
        if not (0 <= col < self.width and 0 <= row < self.height):
            return False
        value = int(bool(solid))
        if self.cells[row][col] == value:
            return False
        self.cells[row][col] = value
        self.rebuild()
        return True

    def rebuild(self):
        self.solid_mask.clear()
        for vy in range(self.height + 1):
            for vx in range(self.width + 1):
                tile_id = self.mask_at(vx, vy)
                self.render_ids[vy][vx] = tile_id
                position = self.render_position(vx, vy)
                self.surface.blit(self.sprites[tile_id], position)
                self.solid_mask.draw(self.tile_masks[tile_id], position)

    def clear(self):
        self.cells = [[0] * self.width for _ in range(self.height)]
        self.rebuild()

    def load_demo(self):
        # # = água; . = grama.
        layout = [
            "..................",
            "..###......####...",
            "..###......#..#...",
            "...##......#..#...",
            "...........####...",
            "..................",
            ".......#..........",
            "........#.........",
            "..................",
            "....##......#.....",
            ".....#.....#......",
            "..................",
        ]
        self.cells = [[0] * self.width for _ in range(self.height)]
        for row, line in enumerate(layout[:self.height]):
            for col, value in enumerate(line[:self.width]):
                self.cells[row][col] = int(value == "#")
        self.rebuild()

    def draw(self, surface, origin=(0, 0)):
        surface.blit(self.surface, origin)
