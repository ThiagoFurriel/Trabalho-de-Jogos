from abc import ABC, abstractmethod

import pygame

from util import EventHandler


WIDTH = 800
HEIGHT = 600


class Enemy:
    def __init__(self, pos, player):
        self.pos = pygame.Vector2(pos)
        self.player = player
        self.radius = 17
        self.health = 2
        self.state = ApproachingEnemyState(self)

    def update(self, dt):
        self.state.update(dt)

    def draw(self, screen):
        self.state.draw(screen)

    def take_damage(self, amount=1, source_pos=None):
        self.health -= amount
        if self.health <= 0:
            EventHandler().notify("EnemyKilled", self)
            self.destroy()
            return
        self.change_state(StunnedEnemyState, source_pos=source_pos)

    def change_state(self, new_state, *args, **kwargs):
        self.state.delete()
        self.state = new_state(self, *args, **kwargs)

    def destroy(self):
        EventHandler().notify("DestroyObj", self)


class EnemyState(ABC):
    color = (206, 67, 67)

    def __init__(self, enemy):
        self.E = enemy

    def draw(self, screen):
        pygame.draw.circle(screen, (44, 17, 17), self.E.pos, self.E.radius + 3)
        pygame.draw.circle(screen, self.color, self.E.pos, self.E.radius)

        bar_width = 28
        health_ratio = max(0, self.E.health) / 2
        bar_rect = pygame.Rect(0, 0, bar_width, 4)
        bar_rect.center = (self.E.pos.x, self.E.pos.y - self.E.radius - 9)
        pygame.draw.rect(screen, (42, 42, 38), bar_rect)
        pygame.draw.rect(
            screen,
            (255, 232, 89),
            (bar_rect.x, bar_rect.y, bar_width * health_ratio, bar_rect.height),
        )

    def delete(self):
        pass

    @abstractmethod
    def update(self, dt):
        pass


class ApproachingEnemyState(EnemyState):
    color = (210, 72, 72)

    def update(self, dt):
        direction = self.E.player.pos - self.E.pos
        if direction.length_squared() > 0:
            self.E.pos += direction.normalize() * 1.45 * dt


class StunnedEnemyState(EnemyState):
    color = (146, 103, 220)

    def __init__(self, enemy, source_pos=None, duration=22):
        super().__init__(enemy)
        self.elapsed = 0
        self.duration = duration
        if source_pos is None:
            self.knockback = pygame.Vector2(0, 0)
        else:
            self.knockback = self.E.pos - pygame.Vector2(source_pos)
            if self.knockback.length_squared() > 0:
                self.knockback = self.knockback.normalize()

    def update(self, dt):
        self.elapsed += dt
        self.E.pos += self.knockback * 2.5 * dt
        self.E.pos.x = max(self.E.radius, min(WIDTH - self.E.radius, self.E.pos.x))
        self.E.pos.y = max(self.E.radius, min(HEIGHT - self.E.radius, self.E.pos.y))
        if self.elapsed >= self.duration:
            self.E.change_state(ApproachingEnemyState)
