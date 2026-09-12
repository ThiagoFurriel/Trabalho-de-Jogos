import random

import pygame

from bullet import PlayerBullet
from enemy import Enemy
from player import Player
from powerup import PowerUp
from util import EventHandler, circle_collision


WIDTH = 800
HEIGHT = 600
FPS = 60


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Trab3 - Run and Gun")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 28)
        self.big_font = pygame.font.Font(None, 72)
        self.running = True
        self.configure_events()
        self.reset()

    def configure_events(self):
        handler = EventHandler()
        handler.clear()
        handler.subscribe("SpawnObj", self.add_obj)
        handler.subscribe("DestroyObj", self.remove_obj)
        handler.subscribe("BulletHitEnemy", self.on_bullet_hit_enemy)
        handler.subscribe("EnemyHitPlayer", self.on_enemy_hit_player)
        handler.subscribe("PowerUpCollected", self.on_powerup_collected)
        handler.subscribe("EnemyKilled", self.on_enemy_killed)
        handler.subscribe("GameOver", self.on_game_over)

    def reset(self):
        self.objects = []
        self.player = Player((WIDTH // 2, HEIGHT // 2))
        self.objects.append(self.player)
        self.spawn_timer = 0
        self.game_over = False

    def add_obj(self, obj):
        self.objects.append(obj)

    def remove_obj(self, obj):
        if obj in self.objects:
            self.objects.remove(obj)

    def on_bullet_hit_enemy(self, data):
        bullet = data["bullet"]
        enemy = data["enemy"]
        enemy.take_damage(bullet.damage, source_pos=bullet.pos)
        bullet.destroy()

    def on_enemy_hit_player(self, enemy):
        self.player.take_damage(1)

    def on_powerup_collected(self, powerup):
        self.player.collect_powerup()
        powerup.destroy()

    def on_enemy_killed(self, enemy):
        self.player.kills += 1
        self.player.score += 10
        if self.player.kills % 4 == 0:
            EventHandler().notify("SpawnObj", PowerUp(enemy.pos))

    def on_game_over(self, data=None):
        self.game_over = True

    def spawn_enemy(self):
        side = random.choice(("top", "right", "bottom", "left"))
        if side == "top":
            pos = (random.randint(20, WIDTH - 20), -20)
        elif side == "right":
            pos = (WIDTH + 20, random.randint(20, HEIGHT - 20))
        elif side == "bottom":
            pos = (random.randint(20, WIDTH - 20), HEIGHT + 20)
        else:
            pos = (-20, random.randint(20, HEIGHT - 20))
        EventHandler().notify("SpawnObj", Enemy(pos, self.player))

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_r and self.game_over:
                    self.reset()
                elif not self.game_over and event.key in (
                    pygame.K_TAB,
                    pygame.K_LSHIFT,
                    pygame.K_RSHIFT,
                ):
                    self.player.action_2()

        if self.game_over:
            return

        keys = pygame.key.get_pressed()
        mouse = pygame.mouse.get_pressed()
        if keys[pygame.K_SPACE] or mouse[0]:
            self.player.action_1()

    def update(self, dt):
        if self.game_over:
            return

        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_enemy()
            self.spawn_timer = max(25, 80 - self.player.kills * 2)

        for obj in list(self.objects):
            obj.update(dt)

        self.check_collisions()

    def check_collisions(self):
        bullets = [obj for obj in self.objects if isinstance(obj, PlayerBullet)]
        enemies = [obj for obj in self.objects if isinstance(obj, Enemy)]
        powerups = [obj for obj in self.objects if isinstance(obj, PowerUp)]

        for bullet in bullets:
            for enemy in enemies:
                if bullet not in self.objects or enemy not in self.objects:
                    continue
                if circle_collision(bullet.pos, bullet.radius, enemy.pos, enemy.radius):
                    EventHandler().notify(
                        "BulletHitEnemy",
                        {"bullet": bullet, "enemy": enemy},
                    )

        for enemy in enemies:
            if enemy not in self.objects:
                continue
            if circle_collision(self.player.pos, self.player.radius, enemy.pos, enemy.radius):
                EventHandler().notify("EnemyHitPlayer", enemy)

        for powerup in powerups:
            if circle_collision(self.player.pos, self.player.radius, powerup.pos, powerup.radius):
                EventHandler().notify("PowerUpCollected", powerup)

    def draw_background(self):
        self.screen.fill((31, 34, 34))
        for x in range(0, WIDTH, 40):
            pygame.draw.line(self.screen, (38, 43, 43), (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, 40):
            pygame.draw.line(self.screen, (38, 43, 43), (0, y), (WIDTH, y))

    def draw_hud(self):
        health_text = self.font.render(f"Vida: {self.player.health}", True, (235, 235, 220))
        score_text = self.font.render(f"Pontos: {self.player.score}", True, (235, 235, 220))
        state_text = self.font.render(f"Estado: {self.player.state.name}", True, (235, 235, 220))
        self.screen.blit(health_text, (18, 14))
        self.screen.blit(score_text, (18, 42))
        self.screen.blit(state_text, (18, 70))

        dash_width = 120
        ratio = 1 - min(1, self.player.dash_cooldown / 55)
        pygame.draw.rect(self.screen, (50, 52, 48), (WIDTH - 150, 18, dash_width, 10))
        pygame.draw.rect(self.screen, (90, 180, 255), (WIDTH - 150, 18, dash_width * ratio, 10))

    def draw_game_over(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        title = self.big_font.render("FIM DE JOGO", True, (255, 232, 89))
        subtitle = self.font.render("Aperte R para Reiniciar", True, (235, 235, 220))
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30)))
        self.screen.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 28)))

    def draw(self):
        self.draw_background()
        for obj in self.objects:
            obj.draw(self.screen)
        self.draw_hud()
        if self.game_over:
            self.draw_game_over()
        pygame.display.flip()

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / (1000 / FPS)
            self.handle_input()
            self.update(dt)
            self.draw()
        pygame.quit()


if __name__ == "__main__":
    Game().run()
