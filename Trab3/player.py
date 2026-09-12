import os
from abc import ABC, abstractmethod

import pygame

from bullet import PlayerBullet
from util import EventHandler, colored_sprite


WIDTH = 800
HEIGHT = 600


class Player:
    def __init__(self, pos):
        self.pos = pygame.Vector2(pos)
        self.radius = 20
        self.max_health = 3
        self.health = self.max_health
        self.score = 0
        self.kills = 0
        self.facing = pygame.Vector2(1, 0)
        self.shoot_cooldown = 0
        self.dash_cooldown = 0
        self.state = NormalPlayerState(self)

    def update(self, dt):
        self.shoot_cooldown = max(0, self.shoot_cooldown - dt)
        self.dash_cooldown = max(0, self.dash_cooldown - dt)
        self.update_aim()
        self.state.update(dt)

    def draw(self, screen):
        self.state.draw(screen)

    def action_1(self):
        self.state.action_1()

    def action_2(self):
        self.state.action_2()

    def take_damage(self, amount=1):
        self.state.take_damage(amount)

    def collect_powerup(self):
        self.change_state(PoweredPlayerState)

    def change_state(self, new_state, *args, **kwargs):
        self.state.delete()
        self.state = new_state(self, *args, **kwargs)

    def move_from_input(self, speed, dt):
        keys = pygame.key.get_pressed()
        direction = pygame.Vector2(0, 0)

        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            direction.x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            direction.x += 1
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            direction.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            direction.y += 1

        if direction.length_squared() > 0:
            self.pos += direction.normalize() * speed * dt

        self.pos.x = max(self.radius, min(WIDTH - self.radius, self.pos.x))
        self.pos.y = max(self.radius, min(HEIGHT - self.radius, self.pos.y))

    def update_aim(self):
        mouse = pygame.Vector2(pygame.mouse.get_pos())
        direction = mouse - self.pos
        if direction.length_squared() > 4:
            self.facing = direction.normalize()

    def spawn_bullet(
        self,
        speed=11,
        radius=5,
        damage=1,
        cooldown=10,
        color=(255, 232, 89),
        spread=(0,),
    ):
        if self.shoot_cooldown > 0:
            return

        self.update_aim()
        for angle in spread:
            direction = self.facing.rotate(angle)
            start = self.pos + direction * (self.radius + radius + 3)
            EventHandler().notify(
                "SpawnObj",
                PlayerBullet(
                    start,
                    direction,
                    speed=speed,
                    radius=radius,
                    damage=damage,
                    color=color,
                ),
            )
        self.shoot_cooldown = cooldown

    def dash(self):
        if self.dash_cooldown > 0:
            return
        self.update_aim()
        self.pos += self.facing * 90
        self.pos.x = max(self.radius, min(WIDTH - self.radius, self.pos.x))
        self.pos.y = max(self.radius, min(HEIGHT - self.radius, self.pos.y))
        self.dash_cooldown = 55
        self.change_state(InvinciblePlayerState, duration=24)


class PlayerState(ABC):
    sprite_name = "base.png"
    fallback_color = (70, 195, 91)
    name = "Normal"

    def __init__(self, player):
        self.P = player
        self.sprite = self.load_sprite()

    def load_sprite(self):
        path = os.path.join(os.path.dirname(__file__), "images", "duck", self.sprite_name)
        if os.path.exists(path):
            image = pygame.image.load(path).convert_alpha()
            return pygame.transform.scale(image, (48, 48))
        return colored_sprite(self.fallback_color, (48, 48))

    def draw(self, screen):
        end = self.P.pos + self.P.facing * 36
        pygame.draw.line(screen, (236, 236, 214), self.P.pos, end, 3)
        rect = self.sprite.get_rect(center=self.P.pos)
        screen.blit(self.sprite, rect)

    def delete(self):
        pass

    def take_damage(self, amount):
        self.P.health -= amount
        if self.P.health <= 0:
            EventHandler().notify("GameOver")
        else:
            self.P.change_state(InvinciblePlayerState)

    @abstractmethod
    def update(self, dt):
        pass

    @abstractmethod
    def action_1(self):
        pass

    @abstractmethod
    def action_2(self):
        pass


class NormalPlayerState(PlayerState):
    sprite_name = "base.png"
    fallback_color = (70, 195, 91)
    name = "Normal"

    def update(self, dt):
        self.P.move_from_input(speed=4.0, dt=dt)

    def action_1(self):
        self.P.spawn_bullet(cooldown=9)

    def action_2(self):
        self.P.dash()


class InvinciblePlayerState(PlayerState):
    sprite_name = "blink.png"
    fallback_color = (90, 180, 255)
    name = "Invencivel"

    def __init__(self, player, duration=90):
        super().__init__(player)
        self.duration = duration
        self.elapsed = 0

    def update(self, dt):
        self.elapsed += dt
        self.P.move_from_input(speed=4.3, dt=dt)
        if self.elapsed >= self.duration:
            self.P.change_state(NormalPlayerState)

    def draw(self, screen):
        if int(self.elapsed / 6) % 2 == 0:
            super().draw(screen)
        pygame.draw.circle(screen, (90, 180, 255), self.P.pos, self.P.radius + 6, 2)

    def action_1(self):
        self.P.spawn_bullet(cooldown=9)

    def action_2(self):
        pass

    def take_damage(self, amount):
        pass


class PoweredPlayerState(PlayerState):
    sprite_name = "wing.png"
    fallback_color = (255, 214, 72)
    name = "Power-up"

    def __init__(self, player, duration=360):
        super().__init__(player)
        self.duration = duration
        self.elapsed = 0

    def update(self, dt):
        self.elapsed += dt
        self.P.move_from_input(speed=4.6, dt=dt)
        if self.elapsed >= self.duration:
            self.P.change_state(NormalPlayerState)

    def draw(self, screen):
        pygame.draw.circle(screen, (255, 214, 72), self.P.pos, self.P.radius + 7, 2)
        super().draw(screen)

    def action_1(self):
        self.P.spawn_bullet(
            speed=12,
            radius=6,
            damage=2,
            cooldown=5,
            color=(255, 214, 72),
            spread=(-9, 0, 9),
        )

    def action_2(self):
        self.P.dash()
