"""Vista de la partida: dibuja uno o dos mundos (pantalla dividida),
efectos visuales, HUD y reproduce los sonidos de los eventos del modelo."""
import math
import random
import pygame
import config
from view import ui
from view.fondo import FondoParallax

COLORES_EXPLOSION = {
    "facil": [(150, 255, 120), (255, 240, 140), (255, 255, 255)],
    "medio": [(90, 210, 255), (255, 240, 140), (255, 255, 255)],
    "dificil": [(220, 100, 255), (255, 120, 60), (255, 230, 120)],
    "kamikaze": [(255, 80, 60), (255, 200, 80), (255, 255, 255)],
    "asteroide": [(150, 140, 160), (110, 100, 120), (200, 190, 200)],
    "jugador": [(255, 120, 40), (255, 220, 80), (255, 255, 255)],
}
# color de las llamas del motor según la skin
LLAMA_SKIN = {
    "rojo": ((255, 200, 60), (255, 110, 30)), "dorado": ((255, 240, 170), (255, 170, 40)),
    "magma": ((255, 240, 90), (255, 120, 20)), "glaciar": ((200, 245, 255), (90, 190, 255)),
    "neon": ((170, 250, 255), (40, 200, 255)), "toxico": ((200, 255, 120), (60, 220, 40)),
    "nebula": ((255, 190, 250), (220, 80, 230)),
}


class Efectos:
    """Partículas, anillos y textos flotantes (solo visual)."""

    def __init__(self):
        self.particulas = []
        self.anillos = []
        self.textos = []
        self.flash = 0.0
        self.rng = random.Random()

    def explosion(self, pos, tipo, grande=False):
        n = 46 if grande else {"facil": 18, "medio": 26, "dificil": 38, "kamikaze": 20}.get(tipo, 16)
        colores = COLORES_EXPLOSION.get(tipo, COLORES_EXPLOSION["jugador"])
        for _ in range(n):
            ang = self.rng.uniform(0, math.tau)
            vel = self.rng.uniform(60, 320 if grande else 240)
            vida = self.rng.uniform(0.35, 0.9)
            self.particulas.append([pos[0], pos[1], math.cos(ang) * vel, math.sin(ang) * vel,
                                    vida, vida, self.rng.choice(colores), self.rng.randint(2, 5)])
        self.anillos.append([pos[0], pos[1], 0.0, 0.4, 90 if grande else 55, (255, 230, 160)])

    def onda(self, pos, radio, color, dur=0.6):
        self.anillos.append([pos[0], pos[1], 0.0, dur, radio, color])

    def chispa(self, pos, color=(255, 240, 180)):
        for _ in range(6):
            ang = self.rng.uniform(math.pi, math.tau)
            vel = self.rng.uniform(60, 160)
            self.particulas.append([pos[0], pos[1], math.cos(ang) * vel, math.sin(ang) * vel,
                                    0.2, 0.2, color, 2])

    def estela(self, pos, color):
        vida = self.rng.uniform(0.15, 0.3)
        self.particulas.append([pos[0] + self.rng.uniform(-3, 3), pos[1], self.rng.uniform(-15, 15),
                                self.rng.uniform(120, 220), vida, vida, color, 3])

    def texto_flotante(self, pos, txt, color, dur=0.9):
        self.textos.append([pos[0], pos[1], dur, txt, color])

    def actualizar(self, dt):
        self.flash = max(0.0, self.flash - dt)
        for p in self.particulas:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[2] *= 0.96
            p[3] *= 0.96
            p[4] -= dt
        self.particulas = [p for p in self.particulas if p[4] > 0]
        for a in self.anillos:
            a[2] += dt
        self.anillos = [a for a in self.anillos if a[2] < a[3]]
        for t in self.textos:
            t[1] -= 40 * dt
            t[2] -= dt
        self.textos = [t for t in self.textos if t[2] > 0]

    def dibujar(self, sup, fuente):
        for x, y, t, dur, r_max, color in self.anillos:
            k = t / dur
            radio = int(8 + r_max * k)
            s = pygame.Surface((radio * 2 + 6, radio * 2 + 6), pygame.SRCALPHA)
            pygame.draw.circle(s, (*color, int(200 * (1 - k))), (radio + 3, radio + 3), radio, 4)
            sup.blit(s, (x - radio - 3, y - radio - 3))
        for x, y, _, _, vida, vida0, color, tam in self.particulas:
            k = vida / vida0
            t = max(1, int(tam * k + 1))
            pygame.draw.rect(sup, color, (int(x), int(y), t, t))
        for x, y, vida, txt, color in self.textos:
            ui.texto(sup, txt, fuente, color, centro=(int(x), int(y)), alpha=int(255 * min(1, vida * 2)))
        if self.flash > 0:
            s = pygame.Surface(sup.get_size(), pygame.SRCALPHA)
            s.fill((255, 255, 255, int(200 * min(1, self.flash / 0.4))))
            sup.blit(s, (0, 0))


class VistaJuego:
    def __init__(self, pantalla, recursos, partida, audio=None):
        self.pantalla = pantalla
        self.r = recursos
        self.partida = partida
        self.audio = audio
        ancho = partida.ancho_mundo
        alto = partida.alto
        self.viewports = []
        for i in range(partida.modo):
            rect = pygame.Rect(i * ancho, 0, ancho, alto)
            self.viewports.append({
                "rect": rect,
                "sup": pygame.Surface((ancho, alto)),
                "fondo": FondoParallax(ancho, alto, recursos, semilla=2026),  # mismo fondo
                "efectos": Efectos(),
                "temblor": 0.0,
            })
        self.banner_nivel = 0.0
        self.banner_jefe = 0.0
        self.banner_mini = False
        self.tiempo = 0.0
        self.sel_decision = 0
        self.toasts = []        # logros desbloqueados: [texto, tiempo]

    def _sonido(self, nombre):
        if self.audio:
            self.audio.efecto(nombre)

    def mostrar_logro(self, nombre):
        self.toasts.append([nombre, 3.5])
        self._sonido("logro")

    # ---------- eventos del modelo -> efectos y sonidos ----------
    def procesar_eventos(self):
        if self.partida.subio_nivel:
            self.banner_nivel = 2.2
            self._sonido("nivel")
            for vp in self.viewports:
                vp["fondo"].set_nivel(self.partida.nivel)
        laser = False
        for vp, mundo in zip(self.viewports, self.partida.mundos):
            ef = vp["efectos"]
            laser = laser or mundo.laser_activo
            for ev in mundo.eventos:
                tipo = ev[0]
                if tipo == "disparo":
                    self._sonido("misil" if mundo.jugador.arma == "misiles" else "disparo")
                elif tipo == "explosion":
                    ef.explosion(ev[1], ev[2])
                    self._sonido("explosion")
                elif tipo == "impacto":
                    ef.chispa(ev[1])
                elif tipo == "puntos":
                    ef.texto_flotante(ev[1], f"+{ev[2]}", ui.AMARILLO)
                elif tipo == "combo":
                    ef.texto_flotante((ev[1][0], ev[1][1] - 25), f"COMBO x{ev[2]:g}", ui.NARANJA, 1.2)
                    self._sonido("combo")
                elif tipo == "item":
                    color = config.ITEMS[ev[2]]["color"]
                    ef.texto_flotante(ev[1], ev[3], color, 1.3)
                    ef.onda(ev[1], 40, color, 0.35)
                    self._sonido("vida" if ev[2] == "vida" else "item")
                elif tipo == "escudo_roto":
                    ef.onda(ev[1], 70, (90, 200, 255), 0.4)
                    self._sonido("escudo_roto")
                elif tipo == "bomba":
                    ef.flash = 0.45
                    ef.onda(ev[1], max(mundo.ancho, mundo.alto), (200, 110, 255), 0.7)
                    vp["temblor"] = 0.7
                    self._sonido("bomba")
                elif tipo == "jugador_golpeado":
                    ef.explosion(ev[1], "jugador", grande=True)
                    vp["temblor"] = 0.35
                    self._sonido("golpe")
                elif tipo == "jugador_destruido":
                    ef.explosion(ev[1], "jugador", grande=True)
                    vp["temblor"] = 0.6
                    self._sonido("explosion_grande")
                elif tipo == "jefe_aparece":
                    self.banner_jefe = 3.0
                    self.banner_mini = ev[2]
                    vp["temblor"] = 0.5
                    self._sonido("alerta")
                elif tipo == "jefe_derrotado":
                    x, y = ev[1]
                    tiros = ((0, 0), (-40, -20), (40, 20)) if ev[2] else \
                        ((0, 0), (-90, -30), (90, -20), (-50, 50), (60, 45))
                    for dx, dy in tiros:
                        ef.explosion((x + dx, y + dy), "dificil", grande=True)
                    ef.explosion((x, y), "jugador", grande=True)
                    vp["temblor"] = 1.0
                    self._sonido("explosion_grande")
        if self.audio:
            self.audio.laser(laser and not self.partida.terminada)

    def actualizar(self, dt):
        self.tiempo += dt
        self.banner_nivel = max(0.0, self.banner_nivel - dt)
        self.banner_jefe = max(0.0, self.banner_jefe - dt)
        for t in self.toasts:
            t[1] -= dt
        self.toasts = [t for t in self.toasts if t[1] > 0]
        for vp, mundo in zip(self.viewports, self.partida.mundos):
            if not mundo.terminado:
                lento = config.LENTO_FACTOR if mundo.jugador.lento else 1.0
                vp["fondo"].actualizar(dt * lento, self.partida.mult_velocidad)
                j = mundo.jugador
                if j.vivo:  # estela de los motores
                    c = LLAMA_SKIN.get(j.skin, LLAMA_SKIN["rojo"])[1]
                    for fx in (0.33, 0.67):
                        if random.random() < 0.6:
                            vp["efectos"].estela((j.x + j.w * fx, j.y + j.h * 0.92), c)
            vp["efectos"].actualizar(dt)
            vp["temblor"] = max(0.0, vp["temblor"] - dt)

    # ---------- pantalla de victoria ----------
    def rects_decision(self):
        cx, cy = self.pantalla.get_width() // 2, self.pantalla.get_height() // 2
        return [pygame.Rect(cx - 290, cy + 120, 270, 60), pygame.Rect(cx + 20, cy + 120, 270, 60)]

    def _dibujar_decision(self):
        ui.oscurecer(self.pantalla, 180)
        cx, cy = self.pantalla.get_width() // 2, self.pantalla.get_height() // 2
        ui.titulo_brillante(self.pantalla, "¡GANASTE!", self.r.f_titulo, (cx, cy - 230), color=ui.AMARILLO)
        ui.texto(self.pantalla, "Derrotaste al JEFE FINAL", self.r.f_media, ui.VERDE, centro=(cx, cy - 160))
        img = self.r.jefe_vitrina
        self.pantalla.blit(img, img.get_rect(center=(cx, cy - 50)))
        pts = "   ·   ".join(f"{m.jugador.nombre}: {m.jugador.puntos} pts" for m in self.partida.mundos)
        ui.texto(self.pantalla, pts, self.r.f_media, ui.BLANCO, centro=(cx, cy + 70))
        for i, (r, txt) in enumerate(zip(self.rects_decision(), ("SEGUIR JUGANDO", "TERMINAR"))):
            ui.boton(self.pantalla, r, txt, self.r.f_media, i == self.sel_decision)
        ui.texto(self.pantalla, "Si sigues, las naves enemigas aparecerán cada vez más rápido",
                 self.r.f_normal, ui.GRIS, centro=(cx, cy + 225))

    # ---------- dibujo ----------
    def dibujar(self, pausa=False):
        for i, (vp, mundo) in enumerate(zip(self.viewports, self.partida.mundos)):
            sup = vp["sup"]
            vp["fondo"].dibujar(sup)
            if mundo.jugador.lento:
                tinte = pygame.Surface(sup.get_size(), pygame.SRCALPHA)
                tinte.fill((60, 80, 255, 35))
                sup.blit(tinte, (0, 0))
            self._dibujar_mundo(sup, mundo)
            vp["efectos"].dibujar(sup, self.r.f_normal)
            self._dibujar_hud(sup, mundo, i)
            if mundo.terminado and self.partida.modo == 2 and not self.partida.terminada:
                ui.oscurecer(sup, 150)
                ui.texto(sup, "DERRIBADO", self.r.f_grande, ui.ROJO,
                         centro=(sup.get_width() // 2, sup.get_height() // 2 - 30))
                ui.texto(sup, f"{mundo.jugador.puntos} pts - esperando al rival...",
                         self.r.f_normal, ui.BLANCO,
                         centro=(sup.get_width() // 2, sup.get_height() // 2 + 25))
            off = (0, 0)
            if vp["temblor"] > 0:
                k = vp["temblor"] * 18
                off = (random.uniform(-k, k), random.uniform(-k, k))
            self.pantalla.blit(sup, vp["rect"].move(off))

        if self.partida.modo == 2:
            x = self.viewports[0]["rect"].right
            pygame.draw.rect(self.pantalla, (20, 20, 40), (x - 3, 0, 6, self.partida.alto))
            pygame.draw.line(self.pantalla, ui.CIAN, (x, 0), (x, self.partida.alto), 2)

        cx, cy = self.pantalla.get_width() // 2, self.pantalla.get_height() // 2
        if self.banner_jefe > 0:
            a = int(255 * min(1, self.banner_jefe))
            if int(self.tiempo * 6) % 2 == 0:
                ui.texto(self.pantalla, "¡ALERTA!", self.r.f_grande, ui.ROJO, centro=(cx, cy - 40), alpha=a)
            ui.texto(self.pantalla, "MINI-JEFE" if self.banner_mini else "JEFE FINAL", self.r.f_titulo,
                     ui.NARANJA, centro=(cx, cy + 30), alpha=a)
        elif self.banner_nivel > 0:
            a = int(255 * min(1, self.banner_nivel))
            ui.texto(self.pantalla, f"NIVEL {self.partida.nivel}", self.r.f_titulo, ui.AMARILLO,
                     centro=(cx, cy - 80), alpha=a)
            ui.texto(self.pantalla, "¡Más enemigos y más rápidos!", self.r.f_media, ui.BLANCO,
                     centro=(cx, cy - 10), alpha=a)

        # logros desbloqueados
        for k, (nombre, t) in enumerate(self.toasts):
            a = int(255 * min(1, t))
            rect = pygame.Rect(0, 0, 420, 64)
            rect.midtop = (cx, 110 + k * 72)
            ui.panel(self.pantalla, rect, alpha=int(220 * a / 255), borde=ui.AMARILLO)
            ui.texto(self.pantalla, "¡LOGRO DESBLOQUEADO!", self.r.f_chica, ui.AMARILLO,
                     centro=(rect.centerx, rect.y + 18), alpha=a)
            ui.texto(self.pantalla, nombre, self.r.f_media, ui.BLANCO, centro=(rect.centerx, rect.y + 44), alpha=a)

        if self.partida.esperando_decision:
            self._dibujar_decision()

        if pausa:
            ui.oscurecer(self.pantalla, 170)
            ui.texto(self.pantalla, "PAUSA", self.r.f_titulo, ui.AMARILLO, centro=(cx, cy - 60))
            ui.texto(self.pantalla, "P / ESC  continuar        Q  salir al menú        M  silenciar",
                     self.r.f_normal, ui.BLANCO, centro=(cx, cy + 30))

    def _dibujar_mundo(self, sup, mundo):
        j = mundo.jugador
        t = self.tiempo
        # ítems (cápsulas que brillan)
        for it in mundo.items:
            img = self.r.items[it.tipo]
            brillo = 0.5 + 0.5 * math.sin(t * 8 + it.x)
            c = config.ITEMS[it.tipo]["color"]
            halo = pygame.Surface((it.w + 20, it.h + 20), pygame.SRCALPHA)
            pygame.draw.circle(halo, (*c, int(40 + 60 * brillo)), (halo.get_width() // 2,) * 2, it.w // 2 + 9)
            sup.blit(halo, (int(it.x) - 10, int(it.y) - 10))
            sup.blit(img, (int(it.x), int(it.y)))
        # asteroides
        for a in mundo.asteroides:
            base = self.r.asteroides_golpe[a.tam] if a.golpe > 0 else self.r.asteroides[a.tam]
            img = pygame.transform.rotate(base, a.angulo)
            sup.blit(img, img.get_rect(center=(int(a.centro[0]), int(a.centro[1]))))
        # balas enemigas
        for b in mundo.balas_enemigas:
            c = (int(b.x + b.w / 2), int(b.y + b.h / 2))
            pygame.draw.circle(sup, (255, 60, 90), c, 6)
            pygame.draw.circle(sup, (255, 200, 210), c, 3)
        # enemigos
        for e in mundo.enemigos:
            img = self.r.enemigos_golpe[e.tipo] if e.golpe > 0 else self.r.enemigos[e.tipo]
            sup.blit(img, (int(e.x), int(e.y)))
            if e.tipo == "kamikaze" and e.picando and int(t * 20) % 2 == 0:
                pygame.draw.circle(sup, (255, 80, 60), (int(e.centro[0]), int(e.y) - 4), 5)
            if e.item and int(t * 4) % 2 == 0:  # pista: este enemigo lleva ítem
                c = config.ITEMS[e.item]["color"]
                pygame.draw.circle(sup, c, (int(e.x + e.w - 4), int(e.y + 4)), 4)
            if e.vida_max > 1 and e.vida < e.vida_max:
                w = e.w * max(0, e.vida) / e.vida_max
                pygame.draw.rect(sup, (60, 0, 0), (int(e.x), int(e.y) - 8, e.w, 4))
                pygame.draw.rect(sup, ui.COLOR_TIPO.get(e.tipo, ui.ROJO), (int(e.x), int(e.y) - 8, int(w), 4))
        # jefe / mini-jefe
        jefe = mundo.jefe
        if jefe:
            if jefe.mini:
                img = self.r.minijefe_golpe if jefe.golpe > 0 else self.r.minijefe
            else:
                img = self.r.jefe_golpe if jefe.golpe > 0 else self.r.jefe
            sup.blit(img, (int(jefe.x), int(jefe.y)))
        # láser
        if mundo.laser_activo:
            x0, x1, y_max = mundo.rayo_laser()
            cx = int((x0 + x1) / 2)
            ancho = int(x1 - x0) + int(4 * math.sin(t * 40))
            glow = pygame.Surface((ancho * 3, int(y_max)), pygame.SRCALPHA)
            glow.fill((255, 60, 120, 70))
            sup.blit(glow, (cx - ancho * 3 // 2, 0))
            pygame.draw.rect(sup, (255, 90, 150), (cx - ancho // 2, 0, ancho, int(y_max)))
            pygame.draw.rect(sup, (255, 230, 240), (cx - ancho // 4, 0, max(2, ancho // 2), int(y_max)))
        # balas del jugador y misiles
        for b in mundo.balas_jugador:
            if b.dano == 2:  # misil
                ang = math.atan2(b.vy, b.vx)
                cx, cy = b.centro
                cola = (cx - math.cos(ang) * 14, cy - math.sin(ang) * 14)
                pygame.draw.line(sup, (255, 150, 60), (int(cx), int(cy)), (int(cola[0]), int(cola[1])), 4)
                pygame.draw.circle(sup, (255, 240, 200), (int(cx), int(cy)), 4)
                continue
            r = pygame.Rect(int(b.x), int(b.y), b.w, b.h)
            pygame.draw.rect(sup, (255, 170, 40), r.inflate(4, 4), border_radius=3)
            pygame.draw.rect(sup, (255, 255, 200), r, border_radius=3)
        # jugador (parpadea si es invulnerable)
        if j.vivo and (j.invulnerable <= 0 or int(t * 14) % 2 == 0):
            self._dibujar_llamas(sup, j)
            sup.blit(self.r.skins[j.skin], (int(j.x), int(j.y)))
        if j.vivo and j.escudo:
            cx, cy = j.centro
            radio = int(max(j.w, j.h) * 0.62 + 3 * math.sin(t * 6))
            s = pygame.Surface((radio * 2 + 4, radio * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(s, (90, 200, 255, 45), (radio + 2, radio + 2), radio)
            pygame.draw.circle(s, (150, 230, 255, 180), (radio + 2, radio + 2), radio, 3)
            sup.blit(s, (int(cx) - radio - 2, int(cy) - radio - 2))

    def _dibujar_llamas(self, sup, j):
        """Llamas animadas de los motores."""
        claro, oscuro = LLAMA_SKIN.get(j.skin, LLAMA_SKIN["rojo"])
        base_y = j.y + j.h * 0.86
        for fx in (0.33, 0.67):
            x = j.x + j.w * fx
            largo = 14 + 9 * abs(math.sin(self.tiempo * 30 + fx * 10)) + random.uniform(0, 5)
            ancho = 6
            pygame.draw.polygon(sup, oscuro, [(x - ancho, base_y), (x + ancho, base_y), (x, base_y + largo)])
            pygame.draw.polygon(sup, claro, [(x - ancho / 2, base_y), (x + ancho / 2, base_y),
                                             (x, base_y + largo * 0.6)])

    def _dibujar_hud(self, sup, mundo, indice):
        j = mundo.jugador
        w, h = sup.get_size()
        p = self.partida
        pygame.draw.rect(sup, (0, 0, 0), (0, 0, w, 40))
        pygame.draw.line(sup, (60, 60, 110), (0, 40), (w, 40))
        etiqueta = f"P{indice + 1} " if p.modo == 2 else ""
        f_nombre = self.r.f_chica if p.modo == 2 else self.r.f_normal
        ui.texto(sup, f"{etiqueta}{j.nombre}", f_nombre, ui.CIAN, topleft=(12, 11))
        ui.texto(sup, f"{j.puntos:05d}", self.r.f_media, ui.AMARILLO, centro=(int(w * 0.42), 21))
        # nivel actual + barra de avance hacia el siguiente nivel (cada 250 pts)
        xn = int(w * 0.64)
        ui.texto(sup, f"NIVEL {p.nivel}", self.r.f_normal, ui.CIAN, centro=(xn, 14))
        barra = pygame.Rect(xn - 45, 28, 90, 7)
        pygame.draw.rect(sup, (40, 40, 70), barra, border_radius=3)
        tope = (p.nivel >= config.NIVEL_JEFE and not p.modo_infinito) or \
               (p.nivel >= config.NIVEL_MINIJEFE and not p.minijefe_derrotado)
        if p.jefe_activo or tope:
            pygame.draw.rect(sup, ui.ROJO, barra, border_radius=3)
        else:
            avance, total = p.puntos_siguiente_nivel(j.puntos)
            pygame.draw.rect(sup, ui.CIAN, (barra.x, barra.y, int(barra.w * avance / total), barra.h),
                             border_radius=3)
        for v in range(j.vidas):
            sup.blit(self.r.iconos_vida[j.skin], (w - 32 - v * 26, 5))

        # barra de vida del jefe
        jefe = mundo.jefe
        if jefe:
            r = pygame.Rect(40, 52, w - 80, 14)
            pygame.draw.rect(sup, (50, 0, 20), r, border_radius=4)
            pygame.draw.rect(sup, (220, 60, 255) if jefe.fase == 1 else ui.ROJO,
                             (r.x, r.y, int(r.w * max(0, jefe.vida) / jefe.vida_max), r.h), border_radius=4)
            pygame.draw.rect(sup, ui.BLANCO, r, 1, border_radius=4)
            ui.texto(sup, "MINI-JEFE" if jefe.mini else "JEFE FINAL", self.r.f_chica, ui.BLANCO,
                     centro=(w // 2, r.bottom + 12))
        elif mundo.jefe_vencido and p.jefe_activo:
            ui.texto(sup, "¡JEFE DERROTADO! Esperando al rival...", self.r.f_normal, ui.VERDE,
                     centro=(w // 2, 70))

        # power-ups activos (abajo a la izquierda): ícono + barra de tiempo
        x, y = 10, h - 38
        activos = list(j.timers.items())
        if j.escudo:
            activos.append(("escudo", None))
        for tipo, restante in activos:
            sup.blit(self.r.items_hud[tipo], (x, y))
            if restante is not None:
                dur = config.ITEMS[tipo]["dur"] or 1
                pygame.draw.rect(sup, (40, 40, 70), (x, y + 29, 26, 4))
                pygame.draw.rect(sup, config.ITEMS[tipo]["color"], (x, y + 29, int(26 * restante / dur), 4))
            x += 32

        # combo y bombas (abajo a la derecha)
        x = w - 12
        for _ in range(j.bombas):
            img = self.r.items_hud["bomba"]
            x -= 30
            sup.blit(img, (x, h - 38))
        if j.bombas:
            tecla = "B" if p.modo == 1 else ("E" if indice == 0 else "Shift der.")
            ui.texto(sup, f"Bomba: {tecla}", self.r.f_chica, ui.GRIS, topright=(w - 12, h - 60))
        mult = j.mult_items * j.combo_mult
        if j.combo >= 3 or mult > 1:
            color = ui.NARANJA if j.combo_mult > 1 else ui.BLANCO
            ui.texto(sup, f"COMBO {j.combo}", self.r.f_normal, color, topright=(w - 12, h - 110))
            if mult > 1:
                ui.texto(sup, f"PUNTOS x{mult:g}", self.r.f_normal, ui.VERDE, topright=(w - 12, h - 85))
