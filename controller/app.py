"""Controlador principal: inicializa pygame y corre el ciclo del juego."""
import os
import pygame
import config
from model.puntajes import RepositorioPuntajes
from model.preferencias import RepositorioPreferencias
from model.logros import RepositorioLogros
from view.audio import Audio
from view.recursos import Recursos
from view.pantallas import VistaPantallas


class App:
    def __init__(self):
        try:
            pygame.mixer.pre_init(22050, -16, 1, 512)
        except (pygame.error, AttributeError):
            pass
        pygame.init()
        self.pantalla = pygame.display.set_mode((config.ANCHO, config.ALTO))
        pygame.display.set_caption(config.TITULO)
        icono = os.path.join(config.ASSETS_DIR, "player.png")
        if os.path.exists(icono):
            pygame.display.set_icon(pygame.image.load(icono))
        self.reloj = pygame.time.Clock()
        self.recursos = Recursos()
        self.prefs = RepositorioPreferencias()
        self.logros = RepositorioLogros()
        self.audio = Audio(self.prefs)
        self.vista_pantallas = VistaPantallas(self.pantalla, self.recursos, self.prefs)
        self.repo = RepositorioPuntajes()
        self.ultima_partida = None
        self.corriendo = True

        from controller.estados import EstadoBienvenida
        self.estado = EstadoBienvenida(self)

    def cambiar(self, nuevo_estado):
        self.estado = nuevo_estado

    def salir(self):
        self.corriendo = False

    def run(self):
        while self.corriendo:
            dt = min(self.reloj.tick(config.FPS) / 1000.0, 1 / 20)
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.corriendo = False
                elif (e.type == pygame.KEYDOWN and e.key == pygame.K_m
                      and getattr(self.estado, "permite_mute", True)):
                    self.audio.alternar_mute()
                else:
                    self.estado.manejar_evento(e)
            self.estado.actualizar(dt)
            self.estado.dibujar()
            pygame.display.flip()
        pygame.quit()
