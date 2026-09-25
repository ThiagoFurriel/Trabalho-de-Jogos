import math
import random
from dataclasses import dataclass

import pygame

from collision import Collide
from shape import Polygon


WIDTH = 800
HEIGHT = 600
FPS = 60

BALL_RADIUS = 12
GRAVITY = 900
MAX_SPEED = 920
SUB_STEPS = 4
SLOT_TOP = 540
SLOT_BOTTOM = 584

BACKGROUND = (20, 24, 32)
BOARD = (32, 39, 50)
LINE = (228, 233, 240)
BALL = (244, 212, 91)
BALL_LINE = (255, 250, 210)
PEG = (96, 165, 250)
TRIANGLE = (130, 95, 215)
WALL = (77, 94, 118)
BOOST = (58, 186, 145)
SLOT_COLORS = [
    (207, 105, 83),
    (225, 172, 72),
    (90, 177, 120),
    (225, 172, 72),
    (207, 105, 83),
]


class BallShape:

    def __init__(self, radius, sides=14):
        self.radius = radius
        self.sides = sides
        self.points = []
        self.convex_shapes = [self]
        self.bounding_box = pygame.Rect(0, 0, radius * 2, radius * 2)

    def update(self, center):
        self.points = [
            (
                center.x + math.cos((math.tau * i) / self.sides) * self.radius,
                center.y + math.sin((math.tau * i) / self.sides) * self.radius,
            )
            for i in range(self.sides)
        ]

        self.bounding_box = pygame.Rect(
            center.x - self.radius,
            center.y - self.radius,
            self.radius * 2,
            self.radius * 2,
        )


@dataclass
class Solid:
    polygon: Polygon
    color: tuple[int, int, int]
    bounce: float = 0.78

    def draw(self, screen):
        pygame.draw.polygon(screen, self.color, self.polygon.points)
        pygame.draw.polygon(screen, LINE, self.polygon.points, 2)


@dataclass
class EffectZone:
    polygon: Polygon
    color: tuple[int, int, int]
    label: str
    score: int = 0
    speed_multiplier: float = 1.0

    def draw(self, screen, font):
        pygame.draw.polygon(screen, self.color, self.polygon.points)
        pygame.draw.polygon(screen, LINE, self.polygon.points, 2)
        text = font.render(self.label, True, (18, 22, 30))
        rect = text.get_rect(center=self.polygon.bounding_box.center)
        screen.blit(text, rect)


class BallBody:

    def __init__(self):
        self.position = pygame.Vector2(WIDTH / 2, 58)
        self.velocity = pygame.Vector2()
        self.shape = BallShape(BALL_RADIUS)
        self.active = False
        self.shape.update(self.position)

    def reset(self, launcher_x):
        self.position.update(launcher_x, 58)
        self.velocity.update(0, 0)
        self.active = False
        self.shape.update(self.position)

    def launch(self):
        self.active = True
        self.velocity.update(random.uniform(-45, 45), 55)

    def integrate(self, dt):
        self.velocity.y += GRAVITY * dt

        if self.velocity.length() > MAX_SPEED:
            self.velocity.scale_to_length(MAX_SPEED)

        self.position += self.velocity * dt
        self.shape.update(self.position)


class PachinkoGame:

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Pachinko")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 26)
        self.big_font = pygame.font.SysFont(None, 38)

        self.solids = self.create_solids()
        self.boost_zones = self.create_boost_zones()
        self.score_zones = self.create_score_zones()

        self.ball = BallBody()
        self.launcher_x = WIDTH / 2
        self.score = 0
        self.balls_left = 5
        self.message = "Mova com A/D ou setas. Espaco solta a bola."
        self.message_timer = 4.0
        self.boost_was_touching = False
        self.stuck_timer = 0.0
        self.running = True

    def create_solids(self):
        solids = [
            Solid(Polygon([(34, 82), (66, 82), (66, SLOT_TOP), (34, SLOT_TOP)]), WALL),
            Solid(Polygon([(766, 82), (734, 82), (734, SLOT_TOP), (766, SLOT_TOP)]), WALL),
            Solid(Polygon([(102, 118), (236, 138), (184, 178)]), TRIANGLE, 0.84),
            Solid(Polygon([(698, 118), (564, 138), (616, 178)]), TRIANGLE, 0.84),
            Solid(Polygon([(400, 170), (435, 205), (400, 240), (365, 205)]), TRIANGLE, 0.88),
            Solid(Polygon([(250, 315), (326, 334), (278, 388)]), TRIANGLE, 0.86),
            Solid(Polygon([(550, 315), (474, 334), (522, 388)]), TRIANGLE, 0.86),
        ]

        peg_positions = [
            (160, 205), (280, 205), (520, 205), (640, 205),
            (115, 260), (220, 260), (330, 260), (470, 260), (580, 260), (685, 260),
            (165, 315), (380, 315), (420, 315), (635, 315),
            (115, 375), (220, 375), (330, 375), (470, 375), (580, 375), (685, 375),
            (165, 435), (280, 435), (400, 435), (520, 435), (635, 435),
        ]

        for x, y in peg_positions:
            solids.append(Solid(Polygon(self.regular_polygon(x, y, 9, 6)), PEG, 0.78))

        for x in [202, 328, 454, 580]:
            solids.append(Solid(Polygon([(x, 500), (x - 14, SLOT_TOP), (x + 14, SLOT_TOP)]), WALL, 0.72))

        return solids

    def create_boost_zones(self):
        return [
            EffectZone(
                Polygon([(382, 342), (424, 342), (449, 378), (402, 418), (356, 378)]),
                BOOST,
                "BOOST",
                score=25,
                speed_multiplier=1.22,
            )
        ]

    def create_score_zones(self):
        scores = [10, 25, 100, 25, 10]
        zones = []

        for i, score in enumerate(scores):
            left = 82 + i * 126
            right = left + 112
            skew = [-8, -4, 0, 4, 8][i]

            zones.append(EffectZone(
                Polygon([
                    (left, SLOT_TOP),
                    (right, SLOT_TOP),
                    (right + skew, SLOT_BOTTOM),
                    (left + skew, SLOT_BOTTOM),
                ]),
                SLOT_COLORS[i],
                str(score),
                score=score,
            ))

        return zones

    def regular_polygon(self, x, y, radius, sides):
        return [
            (
                x + math.cos(-math.pi / 2 + math.tau * i / sides) * radius,
                y + math.sin(-math.pi / 2 + math.tau * i / sides) * radius,
            )
            for i in range(sides)
        ]

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000
            self.handle_events()
            self.update(dt)
            self.draw()

        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.try_launch()
                elif event.key == pygame.K_r:
                    self.restart()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.try_launch()
            elif event.type == pygame.MOUSEMOTION and not self.ball.active:
                self.launcher_x = max(92, min(WIDTH - 92, event.pos[0]))
                self.ball.reset(self.launcher_x)

    def try_launch(self):
        if not self.ball.active and self.balls_left > 0:
            self.ball.launch()
            self.balls_left -= 1
            self.message = "Colisoes poligonais refletem a bola."
            self.message_timer = 2.0

    def restart(self):
        self.score = 0
        self.balls_left = 5
        self.launcher_x = WIDTH / 2
        self.ball.reset(self.launcher_x)
        self.message = "Jogo reiniciado."
        self.message_timer = 2.0
        self.boost_was_touching = False
        self.stuck_timer = 0.0

    def update(self, dt):
        keys = pygame.key.get_pressed()

        if not self.ball.active:
            direction = int(keys[pygame.K_RIGHT] or keys[pygame.K_d]) - int(keys[pygame.K_LEFT] or keys[pygame.K_a])
            self.launcher_x = max(92, min(WIDTH - 92, self.launcher_x + direction * 320 * dt))
            self.ball.reset(self.launcher_x)
        else:
            step = dt / SUB_STEPS

            for _ in range(SUB_STEPS):
                self.ball.integrate(step)
                self.resolve_solid_collisions()
                self.apply_boost_zones()

            self.apply_score_zones()
            self.prevent_stuck(dt)

            if self.ball.position.y > HEIGHT + 40:
                self.end_ball("Sem ponto nessa queda.")

        if self.message_timer > 0:
            self.message_timer -= dt

    def resolve_solid_collisions(self):
        for _ in range(5):
            best_collision = None
            best_solid = None

            for solid in self.solids:
                collision = Collide.polygon(self.ball.shape, solid.polygon)

                if collision is None:
                    continue

                if best_collision is None or collision.overlap > best_collision.overlap:
                    best_collision = collision
                    best_solid = solid

            if best_collision is None:
                break

            normal_from_solid_to_ball = -pygame.Vector2(best_collision.normal)

            if normal_from_solid_to_ball.length_squared() == 0:
                break

            self.ball.position += normal_from_solid_to_ball * (best_collision.overlap + 0.5)
            self.ball.shape.update(self.ball.position)

            normal_speed = self.ball.velocity.dot(normal_from_solid_to_ball)

            if normal_speed < 0:
                normal_velocity = normal_from_solid_to_ball * normal_speed
                tangent_velocity = self.ball.velocity - normal_velocity
                self.ball.velocity = tangent_velocity * 0.985 - normal_velocity * best_solid.bounce

    def apply_boost_zones(self):
        touching = any(
            Collide.polygon(self.ball.shape, zone.polygon)
            for zone in self.boost_zones
        )

        if touching and not self.boost_was_touching:
            if self.ball.velocity.length_squared() > 0:
                self.ball.velocity *= self.boost_zones[0].speed_multiplier
            else:
                self.ball.velocity.y += 100

            self.score += self.boost_zones[0].score
            self.message = "BOOST: acelerou sem refletir (+25)."
            self.message_timer = 1.7

        self.boost_was_touching = touching

    def apply_score_zones(self):
        for zone in self.score_zones:
            if Collide.polygon(self.ball.shape, zone.polygon):
                self.score += zone.score
                self.end_ball(f"Slot {zone.score}: +{zone.score} pontos.")
                return

    def prevent_stuck(self, dt):
        if not self.ball.active:
            self.stuck_timer = 0.0
            return

        if self.ball.position.y >= SLOT_TOP - BALL_RADIUS:
            self.stuck_timer = 0.0
            return

        if self.ball.velocity.length() > 36:
            self.stuck_timer = 0.0
            return

        self.stuck_timer += dt

        if self.stuck_timer < 0.55:
            return

        self.ball.velocity.x += random.choice([-1, 1]) * 130
        self.ball.velocity.y = max(self.ball.velocity.y, 100)
        self.ball.position.y += 3
        self.ball.shape.update(self.ball.position)
        self.stuck_timer = 0.0

    def end_ball(self, message):
        self.message = message
        self.message_timer = 2.4
        self.boost_was_touching = False
        self.stuck_timer = 0.0
        self.ball.reset(self.launcher_x)

        if self.balls_left == 0:
            self.message = f"Fim de jogo. Pontuacao final: {self.score}. R reinicia."
            self.message_timer = 999

    def draw(self):
        self.screen.fill(BACKGROUND)
        pygame.draw.rect(self.screen, BOARD, (34, 48, 732, 536), border_radius=6)

        for zone in self.score_zones:
            zone.draw(self.screen, self.font)

        for zone in self.boost_zones:
            zone.draw(self.screen, self.font)

        for solid in self.solids:
            solid.draw(self.screen)

        self.draw_launcher()
        self.draw_ball()
        self.draw_ui()

        pygame.display.flip()

    def draw_launcher(self):
        y = 58
        pygame.draw.line(self.screen, (174, 185, 201), (self.launcher_x, 24), (self.launcher_x, 88), 2)
        pygame.draw.polygon(
            self.screen,
            (174, 185, 201),
            [
                (self.launcher_x - 17, y - 20),
                (self.launcher_x + 17, y - 20),
                (self.launcher_x, y - 38),
            ],
            2,
        )

    def draw_ball(self):
        pygame.draw.circle(self.screen, BALL, self.ball.position, BALL_RADIUS)
        pygame.draw.circle(self.screen, BALL_LINE, self.ball.position, BALL_RADIUS, 2)

    def draw_ui(self):
        title = self.big_font.render("Pachinko", True, LINE)
        self.screen.blit(title, (18, 12))

        score_text = self.font.render(f"Pontos: {self.score}", True, LINE)
        balls_text = self.font.render(f"Bolas: {self.balls_left}", True, LINE)
        self.screen.blit(score_text, (612, 14))
        self.screen.blit(balls_text, (612, 39))

        if self.message_timer > 0:
            message = self.font.render(self.message, True, LINE)
            if self.message.startswith("Fim de jogo"):
                rect = message.get_rect(center=(WIDTH / 2, 96))
                self.screen.blit(message, rect)
            else:
                self.screen.blit(message, (18, HEIGHT - 30))


if __name__ == "__main__":
    PachinkoGame().run()
