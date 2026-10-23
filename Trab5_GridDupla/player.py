import math

import pygame


class Player:
    def __init__(self, position, radius=10, speed=190):
        self.position = pygame.Vector2(position)
        self.radius = radius
        self.speed = speed
        body = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(body, "white", (radius, radius), radius)
        self.mask = pygame.mask.from_surface(body)
        self.blocked = False

    def rect_at(self, position):
        return pygame.Rect(
            round(position[0]) - self.radius,
            round(position[1]) - self.radius,
            self.radius * 2,
            self.radius * 2,
        )

    def collides(self, world, position):
        rect = self.rect_at(position)
        if (rect.left < 0 or rect.top < 0
                or rect.right > world.pixel_width or rect.bottom > world.pixel_height):
            return True
        return world.solid_mask.overlap(self.mask, rect.topleft) is not None

    def move(self, world, direction, dt):
        direction = pygame.Vector2(direction)
        if direction.length_squared() > 1:
            direction.normalize_ip()
        displacement = direction * self.speed * max(0.0, dt)
        # Passos de até um pixel impedem atravessar uma borda mesmo com dt alto.
        steps = max(1, math.ceil(max(abs(displacement.x), abs(displacement.y))))
        step = displacement / steps
        self.blocked = False
        for _ in range(steps):
            # Resolver os eixos separadamente permite deslizar junto às paredes.
            for axis in (0, 1):
                if not step[axis]:
                    continue
                candidate = self.position.copy()
                candidate[axis] += step[axis]
                if self.collides(world, candidate):
                    self.blocked = True
                else:
                    self.position = candidate
        return self.blocked

    def respawn(self, world, preferred=None):
        if preferred is None:
            preferred = (2.5 * world.tile_size, 7.5 * world.tile_size)
        if not self.collides(world, preferred):
            self.position.update(preferred)
            self.blocked = False
            return True
        for row in range(world.height):
            for col in range(world.width):
                point = ((col + 0.5) * world.tile_size, (row + 0.5) * world.tile_size)
                if not self.collides(world, point):
                    self.position.update(point)
                    self.blocked = False
                    return True
        return False

    def draw(self, surface, origin=(0, 0)):
        center = (round(self.position.x + origin[0]), round(self.position.y + origin[1]))
        pygame.draw.circle(surface, (240, 200, 40), center, self.radius)
        pygame.draw.circle(surface, (30, 30, 30), center, self.radius, 1)
