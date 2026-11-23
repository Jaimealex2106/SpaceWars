"""Música y efectos de sonido. Si no hay tarjeta de audio, todo queda en silencio."""
import os
import time
import pygame
import config

EFECTOS = ["disparo", "misil", "laser", "explosion", "explosion_grande", "golpe", "escudo_roto",
           "item", "vida", "bomba", "nivel", "alerta", "combo", "logro", "menu_mover", "menu_ok",
           "game_over", "victoria"]
# volumen relativo de cada efecto
VOL_EFECTO = {"disparo": 0.35, "laser": 0.5, "explosion": 0.7, "menu_mover": 0.6}
MIN_INTERVALO = {"disparo": 0.05, "explosion": 0.04, "misil": 0.1, "combo": 0.1, "item": 0.05}


class Audio:
    def __init__(self, prefs):
        self.prefs = prefs
        self.ok = False
        self.efectos = {}
        self.pista_actual = None
        self.ultimo = {}
        self.canal_laser = None
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            pygame.mixer.set_num_channels(24)
            for nombre in EFECTOS:
                ruta = os.path.join(config.SONIDOS_DIR, nombre + ".wav")
                if os.path.exists(ruta):
                    self.efectos[nombre] = pygame.mixer.Sound(ruta)
            self.canal_laser = pygame.mixer.Channel(23)
            pygame.mixer.set_reserved(1)
            self.ok = True
        except (pygame.error, NotImplementedError, AttributeError):
            self.ok = False
        self.aplicar_volumen()

    # ---------- volumen ----------
    def aplicar_volumen(self):
        if not self.ok:
            return
        vm = 0 if self.prefs.mute else self.prefs.vol_musica
        try:
            pygame.mixer.music.set_volume(vm)
        except pygame.error:
            pass
        ve = 0 if self.prefs.mute else self.prefs.vol_efectos
        for nombre, snd in self.efectos.items():
            snd.set_volume(ve * VOL_EFECTO.get(nombre, 1.0))

    def alternar_mute(self):
        self.prefs.mute = not self.prefs.mute
        self.prefs.guardar()
        self.aplicar_volumen()

    # ---------- efectos ----------
    def efecto(self, nombre):
        if not self.ok or self.prefs.mute or nombre not in self.efectos:
            return
        ahora = time.monotonic()
        if ahora - self.ultimo.get(nombre, 0) < MIN_INTERVALO.get(nombre, 0.0):
            return
        self.ultimo[nombre] = ahora
        self.efectos[nombre].play()

    def laser(self, activo):
        if not self.ok or "laser" not in self.efectos:
            return
        if activo and not self.prefs.mute:
            if not self.canal_laser.get_busy():
                self.canal_laser.play(self.efectos["laser"], loops=-1)
        elif self.canal_laser.get_busy():
            self.canal_laser.stop()

    # ---------- música ----------
    def musica(self, pista):
        """pista: 'menu', 'juego', 'jefe' o None para detener."""
        if not self.ok or pista == self.pista_actual:
            return
        self.pista_actual = pista
        try:
            if pista is None:
                pygame.mixer.music.fadeout(400)
                return
            ruta = None
            for ext in (".ogg", ".mp3", ".wav"):  # tu propio archivo tiene prioridad
                r = os.path.join(config.SONIDOS_DIR, f"musica_{pista}{ext}")
                if os.path.exists(r):
                    ruta = r
                    break
            if ruta:
                pygame.mixer.music.load(ruta)
                pygame.mixer.music.play(-1, fade_ms=600)
                self.aplicar_volumen()
        except pygame.error:
            pass

    def detener_todo(self):
        if self.ok:
            self.laser(False)
            pygame.mixer.stop()
