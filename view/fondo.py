"""Fondo con scroll vertical en capas (parallax).

Capas, de la más lejana a la más cercana:
  1. imagen base (bg.jpeg si existe, si no un degradado espacial)
  2. nebulosa / galaxia (cambian según el nivel)
  3. estrellas lejanas
  4. planeta con anillos y luna
  5. estrellas cercanas
"""
import math
import random
import pygame


class FondoParallax:
    def __init__(self, ancho, alto, recursos, semilla=42):
        self.ancho, self.alto = ancho, alto
        self.r = recursos
        self.rng = random.Random(semilla)
        self.base = self._crear_base()
        # copia volteada: al alternarlas el scroll no muestra costura
        self.base_volteada = pygame.transform.flip(self.base, False, True)
        self.scroll_base = 0.0
        self.capas_estrellas = [
            self._crear_estrellas(110, 12, (1, 1), (90, 150)),
            self._crear_estrellas(60, 30, (1, 2), (150, 210)),
            self._crear_estrellas(28, 70, (2, 3), (210, 255)),
        ]
        self.nivel = 1
        self.atmosfera = self._nueva_atmosfera(primera=True)
        self.planetas = [
            self._nuevo_objeto(self.r.planeta, 14, primera=True, x_rel=0.72, y=-120),
            self._nuevo_objeto(self.r.luna, 22, primera=True, x_rel=0.12, y=self.alto * 0.45),
        ]

    # ---------- construcción ----------
    def _crear_base(self):
        if self.r.bg is not None:
            # escalar para cubrir la vista y recortar al centro (sin deformar)
            bw, bh = self.r.bg.get_size()
            k = max(self.ancho / bw, self.alto / bh)
            img = pygame.transform.smoothscale(self.r.bg, (round(bw * k), round(bh * k)))
            x = (img.get_width() - self.ancho) // 2
            y = (img.get_height() - self.alto) // 2
            base = pygame.Surface((self.ancho, self.alto))
            base.blit(img, (-x, -y))
            return base
        base = pygame.Surface((self.ancho, self.alto))
        for y in range(self.alto):
            t = y / self.alto
            color = (int(6 + 14 * t), int(4 + 6 * t), int(20 + 26 * t))
            pygame.draw.line(base, color, (0, y), (self.ancho, y))
        for _ in range(self.ancho * self.alto // 900):
            x, y = self.rng.randrange(self.ancho), self.rng.randrange(self.alto)
            c = self.rng.randint(30, 70)
            base.set_at((x, y), (c, c, c + 20))
        return base

    def _crear_estrellas(self, cantidad, velocidad, tam, brillo):
        return {
            "vel": velocidad,
            "puntos": [[self.rng.uniform(0, self.ancho), self.rng.uniform(0, self.alto),
                        self.rng.randint(*tam), self.rng.randint(*brillo),
                        self.rng.uniform(0, math.tau)] for _ in range(cantidad)],
        }

    def _nueva_atmosfera(self, primera=False):
        img = self.r.nebulosa if self.nivel % 2 == 1 else self.r.galaxia
        img = img.copy()
        img.set_alpha(150)
        y = self.alto * 0.15 if primera else -img.get_height()
        x = self.rng.uniform(-img.get_width() * 0.3, self.ancho - img.get_width() * 0.7)
        return {"img": img, "x": x, "y": y, "vel": 8}

    def _nuevo_objeto(self, img, vel, primera=False, x_rel=None, y=None):
        x_rel = self.rng.uniform(0.0, 0.85) if x_rel is None else x_rel
        x = x_rel * self.ancho - img.get_width() / 2
        if y is None:
            y = -img.get_height() - self.rng.uniform(100, 900)
        return {"img": img, "x": x, "y": y, "vel": vel}

    # ---------- actualización ----------
    def set_nivel(self, nivel):
        if nivel != self.nivel:
            self.nivel = nivel
            self.atmosfera = self._nueva_atmosfera()

    def actualizar(self, dt, mult=1.0):
        self.scroll_base = (self.scroll_base + 10 * dt) % (2 * self.alto)
        for capa in self.capas_estrellas:
            for p in capa["puntos"]:
                p[1] += capa["vel"] * mult * dt
                p[4] += dt * 3
                if p[1] > self.alto:
                    p[1] -= self.alto
                    p[0] = self.rng.uniform(0, self.ancho)

        a = self.atmosfera
        a["y"] += a["vel"] * dt
        if a["y"] > self.alto:
            self.atmosfera = self._nueva_atmosfera()

        for i, o in enumerate(self.planetas):
            o["y"] += o["vel"] * dt
            if o["y"] > self.alto:
                self.planetas[i] = self._nuevo_objeto(o["img"], o["vel"])

    # ---------- dibujo ----------
    def dibujar(self, sup):
        y = int(self.scroll_base)
        # ciclo de 2 pantallas: normal -> volteada -> normal ...
        sup.blit(self.base, (0, y))
        sup.blit(self.base_volteada, (0, y - self.alto))
        sup.blit(self.base_volteada, (0, y + self.alto))
        sup.blit(self.base, (0, y - 2 * self.alto))

        a = self.atmosfera
        sup.blit(a["img"], (int(a["x"]), int(a["y"])))
        self._dibujar_estrellas(sup, self.capas_estrellas[0])
        for o in self.planetas:
            sup.blit(o["img"], (int(o["x"]), int(o["y"])))
        self._dibujar_estrellas(sup, self.capas_estrellas[1])
        self._dibujar_estrellas(sup, self.capas_estrellas[2])

    @staticmethod
    def _dibujar_estrellas(sup, capa):
        for x, y, tam, brillo, fase in capa["puntos"]:
            b = int(brillo * (0.75 + 0.25 * math.sin(fase)))
            color = (b, b, min(255, b + 25))
            if tam <= 1:
                sup.set_at((int(x), int(y)), color)
            else:
                pygame.draw.rect(sup, color, (int(x), int(y), tam, tam))
