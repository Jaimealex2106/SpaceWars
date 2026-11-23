"""Utilidades de dibujo compartidas por las pantallas."""
import pygame

BLANCO = (240, 240, 255)
GRIS = (150, 150, 175)
AMARILLO = (255, 214, 70)
ROJO = (255, 80, 70)
CIAN = (90, 220, 255)
VERDE = (120, 240, 110)
MORADO = (200, 110, 255)
NARANJA = (255, 150, 50)
PANEL = (12, 10, 32)

COLOR_TIPO = {"facil": VERDE, "medio": CIAN, "dificil": MORADO, "kamikaze": ROJO}
NOMBRE_TIPO = {"facil": "Fácil", "medio": "Medio", "dificil": "Difícil", "kamikaze": "Kamikaze"}


def texto(sup, txt, fuente, color=BLANCO, centro=None, topleft=None, topright=None,
          sombra=True, alpha=255):
    img = fuente.render(str(txt), True, color)
    rect = img.get_rect()
    if centro is not None:
        rect.center = centro
    elif topright is not None:
        rect.topright = topright
    else:
        rect.topleft = topleft or (0, 0)
    if sombra:
        s = fuente.render(str(txt), True, (0, 0, 0))
        if alpha < 255:
            s.set_alpha(alpha)
        sup.blit(s, rect.move(2, 3))
    if alpha < 255:
        img.set_alpha(alpha)
    sup.blit(img, rect)
    return rect


def titulo_brillante(sup, txt, fuente, centro, color=NARANJA, brillo=(255, 60, 40)):
    """Título con halo de color (estilo arcade)."""
    base = fuente.render(txt, True, brillo)
    for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, 2), (2, -2), (-2, 2)):
        r = base.get_rect(center=(centro[0] + dx, centro[1] + dy))
        base.set_alpha(90)
        sup.blit(base, r)
    texto(sup, txt, fuente, color, centro=centro)


def panel(sup, rect, alpha=200, borde=CIAN, radio=12):
    s = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(s, (*PANEL, alpha), s.get_rect(), border_radius=radio)
    sup.blit(s, rect.topleft)
    if borde:
        pygame.draw.rect(sup, borde, rect, 2, border_radius=radio)


def oscurecer(sup, alpha=150):
    s = pygame.Surface(sup.get_size(), pygame.SRCALPHA)
    s.fill((0, 0, 0, alpha))
    sup.blit(s, (0, 0))


def boton(sup, rect, txt, fuente, activo):
    color_borde = AMARILLO if activo else (90, 90, 140)
    panel(sup, rect, alpha=230 if activo else 170, borde=color_borde, radio=10)
    if activo:
        pygame.draw.polygon(sup, AMARILLO, [(rect.left - 26, rect.centery - 10),
                                            (rect.left - 26, rect.centery + 10),
                                            (rect.left - 10, rect.centery)])
    texto(sup, txt, fuente, AMARILLO if activo else BLANCO, centro=rect.center)


def estrella(sup, centro, radio, color):
    import math
    pts = []
    for i in range(10):
        r = radio if i % 2 == 0 else radio * 0.45
        ang = -math.pi / 2 + i * math.pi / 5
        pts.append((centro[0] + math.cos(ang) * r, centro[1] + math.sin(ang) * r))
    pygame.draw.polygon(sup, color, pts)
