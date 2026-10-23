import pygame

if __package__:
    from .dual_grid import DualGrid, TILE_SIZE
    from .player import Player
else:
    from dual_grid import DualGrid, TILE_SIZE
    from player import Player


WIDTH = 800
HEIGHT = 600
MAP_ORIGIN = (40, 60)


def cells_on_line(start, end):
    # Preenche as células entre duas posições do mouse.
    x, y = start
    dx = end[0] - x
    dy = end[1] - y
    steps = max(abs(dx), abs(dy))
    if steps == 0:
        yield start
    else:
        for i in range(steps + 1):
            yield round(x + dx * i / steps), round(y + dy * i / steps)


class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Trabalho 5 - Grid dupla")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.world = DualGrid(width=18, height=12)
        self.world.load_demo()
        self.player = Player((100, 300))
        self.map_rect = pygame.Rect(MAP_ORIGIN, (self.world.pixel_width, self.world.pixel_height))
        self.running = True
        self.show_grid = False
        self.paint_button = None
        self.last_cell = None

    def action(self, name):
        if name == "grid":
            self.show_grid = not self.show_grid
        elif name == "reset":
            self.world.load_demo()
            self.player.respawn(self.world)
        elif name == "clear":
            self.world.clear()
        elif name == "respawn":
            self.player.respawn(self.world)
        self.paint_button = None
        self.last_cell = None

    def cell_at(self, position):
        if self.map_rect.collidepoint(position):
            return ((position[0] - self.map_rect.x) // TILE_SIZE,
                    (position[1] - self.map_rect.y) // TILE_SIZE)
        return None

    def paint(self, position):
        cell = self.cell_at(position)
        if cell is None:
            self.last_cell = None
            return
        solid = self.paint_button == 1
        for col, row in cells_on_line(self.last_cell or cell, cell):
            previous = self.world.get_cell(col, row)
            if self.world.set_cell(col, row, solid):
                # Não deixa colocar água em cima do jogador.
                if solid and self.player.collides(self.world, self.player.position):
                    self.world.set_cell(col, row, previous)
        self.last_cell = cell

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.running = False
            actions = {pygame.K_g: "grid", pygame.K_r: "reset",
                       pygame.K_DELETE: "clear", pygame.K_SPACE: "respawn"}
            if event.key in actions:
                self.action(actions[event.key])
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button in (1, 3) and self.cell_at(event.pos) is not None:
                self.paint_button = event.button
                self.last_cell = None
                self.paint(event.pos)
        elif event.type == pygame.MOUSEMOTION and self.paint_button is not None:
            self.paint(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == self.paint_button:
                self.paint_button = None
                self.last_cell = None
        elif event.type == pygame.WINDOWFOCUSLOST:
            self.paint_button = None
            self.last_cell = None

    def update(self, dt):
        keys = pygame.key.get_pressed()
        dx = int(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - int(keys[pygame.K_a] or keys[pygame.K_LEFT])
        dy = int(keys[pygame.K_s] or keys[pygame.K_DOWN]) - int(keys[pygame.K_w] or keys[pygame.K_UP])
        self.player.move(self.world, (dx, dy), dt)

    def draw(self):
        self.screen.fill((230, 230, 230))
        self.world.draw(self.screen, MAP_ORIGIN)
        if self.show_grid:
            # A segunda grade fica deslocada metade do tamanho do tile.
            for offset, color in ((0, (40, 40, 40)), (TILE_SIZE // 2, (230, 190, 60))):
                for x in range(offset, self.world.pixel_width + 1, TILE_SIZE):
                    pygame.draw.line(self.screen, color,
                                     (self.map_rect.left + x, self.map_rect.top),
                                     (self.map_rect.left + x, self.map_rect.bottom))
                for y in range(offset, self.world.pixel_height + 1, TILE_SIZE):
                    pygame.draw.line(self.screen, color,
                                     (self.map_rect.left, self.map_rect.top + y),
                                     (self.map_rect.right, self.map_rect.top + y))
        self.player.draw(self.screen, MAP_ORIGIN)
        pygame.draw.rect(self.screen, (30, 30, 30), self.map_rect, 1)
        for text, position in (
            ("Grid dupla", (40, 23)),
            ("Verde: grama livre   |   Azul: água com colisão", (330, 23)),
            ("Mouse esquerdo: água   |   Direito: grama   |   WASD/setas: mover", (40, 550)),
            ("G: grades   R: restaurar   Delete: limpar   Espaco: reposicionar   Esc: sair", (40, 575)),
        ):
            self.screen.blit(self.font.render(text, True, (30, 30, 30)), position)
        pygame.display.flip()

    def run(self):
        while self.running:
            dt = min(self.clock.tick(60) / 1000, 0.05)
            for event in pygame.event.get():
                self.handle_event(event)
            self.update(dt)
            self.draw()


def main():
    app = App()
    try:
        app.run()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
