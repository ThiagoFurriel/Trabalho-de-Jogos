import math

import pygame

from util import EventHandler


WIDTH = 800
HEIGHT = 600


def rotate(pos, angle, axis=(0, 0)):
    angle = math.radians(angle)
    x, y = pos
    ax, ay = axis
    x -= ax
    y -= ay

    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    rx = x * cos_a - y * sin_a
    ry = x * sin_a + y * cos_a
    return rx + ax, ry + ay


class Bullet:
    def __init__(
        self,
        pos,
        velocity,
        radius=6,
        life_time=70,
        damage=1,
        color=(255, 232, 89),
        owner="player",
    ):
        self.pos = pygame.Vector2(pos)
        self.velocity = pygame.Vector2(velocity)
        self.radius = radius
        self.life_time = life_time
        self.damage = damage
        self.color = color
        self.owner = owner
        self.elapsed = 0

    def update(self, dt):
        self.elapsed += dt
        self.move(dt)

        margin = self.radius + 30
        outside = (
            self.pos.x < -margin
            or self.pos.x > WIDTH + margin
            or self.pos.y < -margin
            or self.pos.y > HEIGHT + margin
        )
        if self.elapsed >= self.life_time or outside:
            self.destroy()

    def move(self, dt):
        self.pos += self.velocity * dt

    def draw(self, screen):
        pygame.draw.circle(screen, (64, 38, 9), self.pos, self.radius + 2)
        pygame.draw.circle(screen, self.color, self.pos, self.radius)

    def destroy(self):
        EventHandler().notify("DestroyObj", self)


class PlayerBullet(Bullet):
    def __init__(self, pos, direction, speed=11, radius=5, damage=1, color=(255, 232, 89)):
        direction = pygame.Vector2(direction)
        if direction.length_squared() == 0:
            direction = pygame.Vector2(1, 0)
        super().__init__(
            pos=pos,
            velocity=direction.normalize() * speed,
            radius=radius,
            damage=damage,
            color=color,
            owner="player",
        )


class sinBullet(Bullet):
    def __init__(self, pos, angle=0, radius=16, life_time=240):
        self.origin = pygame.Vector2(pos)
        self.angle = angle
        super().__init__(
            pos=pos,
            velocity=(0, 0),
            radius=radius,
            life_time=life_time,
            color=(255, 89, 89),
            owner="enemy",
        )

    def move(self, dt):
        offset = pygame.Vector2(self.elapsed * 4, math.sin(self.elapsed / 8) * 50)
        self.pos = self.origin + pygame.Vector2(rotate(offset, self.angle))
