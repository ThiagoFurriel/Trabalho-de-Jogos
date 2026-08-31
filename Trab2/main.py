import sys
import pygame
from grid import Grid


WIDTH = 800
HEIGHT = 600
FPS = 60


def draw_text(screen, font, text, x, y, color=(30, 30, 30)):
    image = font.render(text, True, color)
    screen.blit(image, (x, y))


def main():
    pygame.init()
    pygame.font.init()
    pygame.display.set_caption("Trab2 - Sudoku")

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    title_font = pygame.font.Font(None, 48)
    text_font = pygame.font.Font(None, 26)

    grid = Grid(35, 90, cell_size=48)
    objects = [grid]

    while True:
        dt = clock.tick(FPS) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                grid.handle_mouse_down(event.pos, event.button)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                grid.handle_key(event.key)

        for obj in objects:
            obj.update(dt)

        screen.fill((245, 245, 245))
        draw_text(screen, title_font, "Sudoku", 35, 25)
        draw_text(screen, text_font, grid.message, 190, 38)
        draw_text(screen, text_font, f"Pontos: {grid.score}", 520, 120)
        draw_text(screen, text_font, f"Erros: {grid.errors}", 520, 155)
        draw_text(screen, text_font, f"Restantes: {grid.remaining_cells()}", 520, 190)
        draw_text(screen, text_font, "Mouse: seleciona celula/botao", 520, 270)
        draw_text(screen, text_font, "Teclado: setas e 1 a 9", 520, 305)
        draw_text(screen, text_font, "Backspace limpa | R reinicia", 520, 340)

        for obj in objects:
            obj.draw(screen)

        pygame.display.flip()


if __name__ == "__main__":
    main()
