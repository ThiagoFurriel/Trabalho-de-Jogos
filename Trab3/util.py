import pygame


def singleton(class_):
    instances = {}

    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]

    return getinstance


@singleton
class EventHandler:
    def __init__(self):
        self.observers = {}

    def clear(self):
        self.observers.clear()

    def subscribe(self, event_type, callback):
        if event_type not in self.observers:
            self.observers[event_type] = []
        self.observers[event_type].append(callback)

    def notify(self, event_type, data=None):
        if event_type in self.observers:
            for observer in list(self.observers[event_type]):
                observer(data)


def colored_sprite(color, size=(32, 32), circle=True):
    sprite = pygame.Surface(size, pygame.SRCALPHA)
    if circle:
        pygame.draw.circle(sprite, color, (size[0] // 2, size[1] // 2), size[0] // 2)
    else:
        sprite.fill(color)
    return sprite


def circle_collision(p1, r1, p2, r2):
    p1 = pygame.Vector2(p1)
    p2 = pygame.Vector2(p2)
    return p1.distance_squared_to(p2) <= (r1 + r2) ** 2


# Nome antigo mantido para nao quebrar exercicios que importem a funcao.
circle_collistiion = circle_collision
