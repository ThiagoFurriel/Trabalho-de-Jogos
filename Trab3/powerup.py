import math

import pygame

from util import EventHandler


class PowerUp:
    def __init__(self, pos):
        self.pos = pygame.Vector2(pos)
        self.radius = 13
        self.elapsed = 0
        self.life_time = 520

    def update(self, dt):
        self.elapsed += dt
        if self.elapsed >= self.life_time:
            self.destroy()

    def draw(self, screen):
        pulse = math.sin(self.elapsed / 8) * 2
        radius = self.radius + pulse
        points = [
            (self.pos.x, self.pos.y - radius),
            (self.pos.x + radius, self.pos.y),
            (self.pos.x, self.pos.y + radius),
            (self.pos.x - radius, self.pos.y),
        ]
        pygame.draw.polygon(screen, (69, 47, 11), points)
        pygame.draw.polygon(screen, (255, 214, 72), points, 0)
        pygame.draw.circle(screen, (255, 246, 160), self.pos, 4)

    def destroy(self):
        EventHandler().notify("DestroyObj", self)
