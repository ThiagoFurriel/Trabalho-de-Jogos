from abc import ABC, abstractmethod
import pygame


BOARD_SIZE = 9
BOX_SIZE = 3

PUZZLE = [
    [5, 3, 0, 0, 7, 0, 0, 0, 0],
    [6, 0, 0, 1, 9, 5, 0, 0, 0],
    [0, 9, 8, 0, 0, 0, 0, 6, 0],
    [8, 0, 0, 0, 6, 0, 0, 0, 3],
    [4, 0, 0, 8, 0, 3, 0, 0, 1],
    [7, 0, 0, 0, 2, 0, 0, 0, 6],
    [0, 6, 0, 0, 0, 0, 2, 8, 0],
    [0, 0, 0, 4, 1, 9, 0, 0, 5],
    [0, 0, 0, 0, 8, 0, 0, 7, 9],
]

SOLUTION = [
    [5, 3, 4, 6, 7, 8, 9, 1, 2],
    [6, 7, 2, 1, 9, 5, 3, 4, 8],
    [1, 9, 8, 3, 4, 2, 5, 6, 7],
    [8, 5, 9, 7, 6, 1, 4, 2, 3],
    [4, 2, 6, 8, 5, 3, 7, 9, 1],
    [7, 1, 3, 9, 2, 4, 8, 5, 6],
    [9, 6, 1, 5, 3, 7, 2, 8, 4],
    [2, 8, 7, 4, 1, 9, 6, 3, 5],
    [3, 4, 5, 2, 8, 6, 1, 7, 9],
]

COLORS = {
    "empty": (250, 250, 250),
    "fixed": (225, 225, 225),
    "selected": (255, 246, 190),
    "correct": (214, 242, 219),
    "wrong": (250, 214, 210),
    "line": (40, 40, 40),
    "thin_line": (150, 150, 150),
    "button": (235, 235, 235),
    "button_selected": (255, 246, 190),
    "text": (30, 30, 30),
    "user_text": (35, 95, 65),
    "wrong_text": (170, 45, 40),
}


class obj(ABC):
    def __init__(self, x, y, sprites=None):
        self.x = x
        self.y = y
        self.sprites = sprites or {}

    @abstractmethod
    def draw(self, screen):
        pass

    @abstractmethod
    def update(self, dt):
        pass


def make_sprite(size, color):
    surface = pygame.Surface((size, size))
    surface.fill(color)
    pygame.draw.rect(surface, COLORS["thin_line"], (0, 0, size, size), 1)
    return surface


class Cell(obj):
    def __init__(self, grid, row, col, value):
        self.grid = grid
        self.row = row
        self.col = col
        self.size = grid.cell_size
        self.value = value
        self.fixed = value != 0
        self.flash = None
        self.flash_time = 0
        x = grid.x + col * grid.cell_size
        y = grid.y + row * grid.cell_size
        super().__init__(x, y, grid.cell_sprites)
        self.rect = pygame.Rect(x, y, self.size, self.size)

    def is_wrong(self):
        return not self.fixed and self.value != 0 and self.value != SOLUTION[self.row][self.col]

    def set_value(self, value):
        if self.fixed:
            self.flash = "wrong"
            self.flash_time = 0.25
            return False

        self.value = value
        if value == SOLUTION[self.row][self.col]:
            self.flash = "correct"
        else:
            self.flash = "wrong"
        self.flash_time = 0.25
        return True

    def clear(self):
        if not self.fixed:
            self.value = 0

    def update(self, dt):
        if self.flash_time > 0:
            self.flash_time -= dt
            if self.flash_time <= 0:
                self.flash = None

    def draw(self, screen):
        if self.flash:
            sprite_name = self.flash
        elif self.grid.selected == (self.row, self.col):
            sprite_name = "selected"
        elif self.is_wrong():
            sprite_name = "wrong"
        elif self.fixed:
            sprite_name = "fixed"
        else:
            sprite_name = "empty"

        screen.blit(self.sprites[sprite_name], (self.x, self.y))

        if self.value == 0:
            return

        color = COLORS["text"]
        if self.is_wrong():
            color = COLORS["wrong_text"]
        elif not self.fixed:
            color = COLORS["user_text"]

        font = self.grid.font
        text = font.render(str(self.value), True, color)
        screen.blit(text, text.get_rect(center=self.rect.center))


class Grid(obj):
    def __init__(self, x, y, sprites=None, grid_size=(BOARD_SIZE, BOARD_SIZE), cell_size=48):
        super().__init__(x, y, sprites)
        self.grid_size = grid_size
        self.cell_size = cell_size
        self.board_size = BOARD_SIZE * cell_size
        self.board_rect = pygame.Rect(x, y, self.board_size, self.board_size)
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.cell_sprites = self.make_cell_sprites()
        self.selected = (0, 0)
        self.score = 0
        self.errors = 0
        self.message = "Clique em uma celula e digite 1 a 9"
        self.buttons = self.make_buttons()
        self.clear_button = pygame.Rect(x + 9 * 42, y + self.board_size + 18, 58, 34)
        self.reset()

    def make_cell_sprites(self):
        return {
            "empty": make_sprite(self.cell_size, COLORS["empty"]),
            "fixed": make_sprite(self.cell_size, COLORS["fixed"]),
            "selected": make_sprite(self.cell_size, COLORS["selected"]),
            "correct": make_sprite(self.cell_size, COLORS["correct"]),
            "wrong": make_sprite(self.cell_size, COLORS["wrong"]),
        }

    def make_buttons(self):
        y = self.y + self.board_size + 18
        return [
            (number, pygame.Rect(self.x + (number - 1) * 42, y, 36, 34))
            for number in range(1, 10)
        ]

    def reset(self):
        self.cells = []
        for row in range(BOARD_SIZE):
            line = []
            for col in range(BOARD_SIZE):
                line.append(Cell(self, row, col, PUZZLE[row][col]))
            self.cells.append(line)

        self.selected = self.first_empty_cell()
        self.score = 0
        self.errors = 0
        self.message = "Clique em uma celula e digite 1 a 9"

    def first_empty_cell(self):
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if PUZZLE[row][col] == 0:
                    return row, col
        return 0, 0

    def selected_cell(self):
        row, col = self.selected
        return self.cells[row][col]

    def select(self, row, col):
        self.selected = (row % BOARD_SIZE, col % BOARD_SIZE)

    def set_selected_value(self, value):
        cell = self.selected_cell()
        changed = cell.set_value(value)

        if not changed:
            self.message = "Essa celula nao pode ser alterada"
            return

        if value == SOLUTION[cell.row][cell.col]:
            self.score += 10
            self.message = "Valor correto"
        else:
            self.errors += 1
            self.message = "Valor incorreto"

        if self.is_finished():
            self.message = "Sudoku completo"

    def clear_selected(self):
        cell = self.selected_cell()
        if cell.fixed:
            cell.flash = "wrong"
            cell.flash_time = 0.25
            self.message = "Essa celula nao pode ser alterada"
        else:
            cell.clear()
            self.message = "Celula limpa"

    def is_finished(self):
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if self.cells[row][col].value != SOLUTION[row][col]:
                    return False
        return True

    def remaining_cells(self):
        total = 0
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if self.cells[row][col].value != SOLUTION[row][col]:
                    total += 1
        return total

    def handle_mouse_down(self, pos, button=1):
        if button != 1:
            return

        if self.board_rect.collidepoint(pos):
            col = (pos[0] - self.x) // self.cell_size
            row = (pos[1] - self.y) // self.cell_size
            self.select(row, col)
            return

        for number, rect in self.buttons:
            if rect.collidepoint(pos):
                self.set_selected_value(number)
                return

        if self.clear_button.collidepoint(pos):
            self.clear_selected()

    def handle_key(self, key):
        if key == pygame.K_UP:
            self.select(self.selected[0] - 1, self.selected[1])
        elif key == pygame.K_DOWN:
            self.select(self.selected[0] + 1, self.selected[1])
        elif key == pygame.K_LEFT:
            self.select(self.selected[0], self.selected[1] - 1)
        elif key == pygame.K_RIGHT:
            self.select(self.selected[0], self.selected[1] + 1)
        elif key in (pygame.K_BACKSPACE, pygame.K_DELETE, pygame.K_0, pygame.K_KP0):
            self.clear_selected()
        elif key == pygame.K_r:
            self.reset()
        elif pygame.K_1 <= key <= pygame.K_9:
            self.set_selected_value(key - pygame.K_0)
        elif pygame.K_KP1 <= key <= pygame.K_KP9:
            self.set_selected_value(key - pygame.K_KP0)

    def update(self, dt):
        for row in self.cells:
            for cell in row:
                cell.update(dt)

    def draw_lines(self, screen):
        for i in range(BOARD_SIZE + 1):
            width = 3 if i % BOX_SIZE == 0 else 1
            color = COLORS["line"] if i % BOX_SIZE == 0 else COLORS["thin_line"]
            x = self.x + i * self.cell_size
            y = self.y + i * self.cell_size
            pygame.draw.line(screen, color, (x, self.y), (x, self.y + self.board_size), width)
            pygame.draw.line(screen, color, (self.x, y), (self.x + self.board_size, y), width)

    def draw_buttons(self, screen):
        for number, rect in self.buttons:
            color = COLORS["button_selected"] if self.selected_cell().value == number else COLORS["button"]
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, COLORS["line"], rect, 1)
            text = self.small_font.render(str(number), True, COLORS["text"])
            screen.blit(text, text.get_rect(center=rect.center))

        pygame.draw.rect(screen, COLORS["button"], self.clear_button)
        pygame.draw.rect(screen, COLORS["line"], self.clear_button, 1)
        text = self.small_font.render("Limpar", True, COLORS["text"])
        screen.blit(text, text.get_rect(center=self.clear_button.center))

    def draw(self, screen):
        for row in self.cells:
            for cell in row:
                cell.draw(screen)

        self.draw_lines(screen)
        self.draw_buttons(screen)
