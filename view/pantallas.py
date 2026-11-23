"""Pantallas fuera de la partida: bienvenida, menú, nombre, skins, game over,
historial y estadísticas."""
import math
import pygame
import config
from view import ui
from view.fondo import FondoParallax

OPCIONES_MENU = ["1 PLAYER", "2 PLAYERS", "SKINS", "CÓMO JUGAR", "LOGROS", "HISTORIAL",
                 "ESTADÍSTICAS", "OPCIONES", "SALIR"]
PESTANAS_STATS = ["Uniforme", "Exp: tipo", "Exp: oleadas", "Histórica", "Bernoulli", "Ítems"]
PAGINAS_AYUDA = ["Controles", "Enemigos", "Ítems"]
OPCIONES_AJUSTES = ["Música", "Efectos", "Silencio (M)", "Regresar"]


class VistaPantallas:
    def __init__(self, pantalla, recursos, prefs):
        self.p = pantalla
        self.r = recursos
        self.prefs = prefs
        self.W, self.H = pantalla.get_size()
        self.fondo = FondoParallax(self.W, self.H, recursos, semilla=7)
        self.t = 0.0

    def actualizar(self, dt):
        self.t += dt
        self.fondo.actualizar(dt)

    def _fondo(self, oscuro=60):
        self.fondo.dibujar(self.p)
        if oscuro:
            ui.oscurecer(self.p, oscuro)

    def _ayuda(self, txt):
        ui.texto(self.p, txt, self.r.f_chica, ui.GRIS, centro=(self.W // 2, self.H - 24))

    # ---------------- Bienvenida ----------------
    def bienvenida(self):
        self._fondo(30)
        cx = self.W // 2
        y = 210 + int(math.sin(self.t * 2) * 6)
        ui.titulo_brillante(self.p, "SPACE WARS", self.r.f_titulo, (cx, y))
        ui.texto(self.p, "BATALLA DE NAVES  ·  ARCADE", self.r.f_media, ui.CIAN, centro=(cx, y + 75))

        v = self.r.vitrina
        base = 470
        nave = self.r.skins_vitrina[self.prefs.skins[0]]
        self.p.blit(nave, nave.get_rect(center=(cx, base + 10 + math.sin(self.t * 3) * 8)))
        for k, dx in (("facil", -380), ("medio", -230), ("dificil", 260)):
            img = v[k]
            self.p.blit(img, img.get_rect(center=(cx + dx, base - 20 + math.sin(self.t * 2 + dx) * 6)))

        if int(self.t * 2) % 2 == 0:
            ui.texto(self.p, "PRESS ANY KEY FOR START", self.r.f_media, ui.AMARILLO,
                     centro=(cx, self.H - 140))
        self._ayuda("Simulación con distribuciones Uniforme, Exponencial e Histórica (transformada inversa)")

    # ---------------- Menú ----------------
    def rects_menu(self):
        rects = []
        w, h, gap = 340, 44, 8
        y0 = 238
        for i in range(len(OPCIONES_MENU)):
            rects.append(pygame.Rect(self.W // 2 - w // 2, y0 + i * (h + gap), w, h))
        return rects

    def menu(self, seleccion):
        self._fondo(80)
        cx = self.W // 2
        ui.titulo_brillante(self.p, "SPACE WARS", self.r.f_titulo, (cx, 130))
        for i, (rect, op) in enumerate(zip(self.rects_menu(), OPCIONES_MENU)):
            ui.boton(self.p, rect, op, self.r.f_normal, i == seleccion)
        # vitrina de enemigos y puntos
        x0 = 70
        for k, y in (("facil", 290), ("medio", 400), ("dificil", 525), ("kamikaze", 650)):
            img = self.r.vitrina[k]
            img = pygame.transform.smoothscale(img, (img.get_width() * 2 // 3, img.get_height() * 2 // 3))
            self.p.blit(img, img.get_rect(center=(x0 + 60, y)))
            ui.texto(self.p, ui.NOMBRE_TIPO[k], self.r.f_normal, ui.COLOR_TIPO[k], topleft=(x0 + 130, y - 22))
            ui.texto(self.p, f"{config.TIPOS_ENEMIGO[k]['puntos']} pts", self.r.f_normal, ui.AMARILLO,
                     topleft=(x0 + 130, y + 4))
        # controles
        rect = pygame.Rect(self.W - 330, 245, 300, 345)
        ui.panel(self.p, rect, borde=(70, 70, 120))
        lineas = [("CONTROLES", ui.AMARILLO), ("1P: WASD / Flechas", ui.BLANCO), ("     Espacio = disparar", ui.GRIS),
                  ("2P  J1: WASD + Espacio", ui.BLANCO), ("     J2: Flechas + Enter", ui.BLANCO),
                  ("B = bomba (1P)", ui.GRIS), ("2P bomba: E / Shift der.", ui.GRIS),
                  ("P / ESC = pausa   ·   M = silencio", ui.GRIS), (f"Cada {config.PUNTOS_POR_NIVEL} pts sube el nivel", ui.CIAN),
                  (f"Nivel {config.NIVEL_MINIJEFE}: MINI-JEFE", ui.NARANJA),
                  (f"Nivel {config.NIVEL_JEFE}: JEFE FINAL", ui.ROJO)]
        for i, (txt, c) in enumerate(lineas):
            ui.texto(self.p, txt, self.r.f_chica, c, topleft=(rect.x + 18, rect.y + 14 + i * 29))
        nombre_dif = config.DIFICULTADES[self.prefs.dificultad]["nombre"]
        ui.texto(self.p, f"Última dificultad: {nombre_dif}", self.r.f_chica, ui.GRIS, topleft=(rect.x + 18, rect.bottom + 12))
        self._ayuda("Clic o  flechas + Enter para elegir")

    # ---------------- Nombre ----------------
    def nombre(self, indice_jugador, modo, texto, error=""):
        self._fondo(110)
        cx = self.W // 2
        ui.texto(self.p, "1 PLAYER" if modo == 1 else "2 PLAYERS", self.r.f_media, ui.CIAN, centro=(cx, 170))
        etiqueta = f"JUGADOR {indice_jugador + 1}" if modo == 2 else "PILOTO"
        ui.titulo_brillante(self.p, f"{etiqueta}: INGRESA TU NOMBRE", self.r.f_grande, (cx, 260))
        if modo == 2:
            ctrl = "WASD + Espacio" if indice_jugador == 0 else "Flechas + Enter"
            ui.texto(self.p, f"Controles: {ctrl}   ·   Pantalla {'izquierda' if indice_jugador == 0 else 'derecha'}",
                     self.r.f_normal, ui.GRIS, centro=(cx, 320))
        caja = pygame.Rect(cx - 260, 370, 520, 80)
        ui.panel(self.p, caja, borde=ui.AMARILLO)
        cursor = "_" if int(self.t * 2.5) % 2 == 0 else " "
        ui.texto(self.p, texto + cursor, self.r.f_grande, ui.BLANCO, centro=caja.center)
        if error:
            ui.texto(self.p, error, self.r.f_normal, ui.ROJO, centro=(cx, 490))
        nave = self.r.skins_vitrina[self.prefs.skins[indice_jugador]]
        self.p.blit(nave, nave.get_rect(center=(cx, 610)))
        nombre_skin = dict((s[0], s[1]) for s in config.SKINS)[self.prefs.skins[indice_jugador]]
        ui.texto(self.p, f"Skin: {nombre_skin}  (cámbiala en el menú SKINS)", self.r.f_chica, ui.GRIS,
                 centro=(cx, 705))
        self._ayuda("Enter = confirmar   ·   Esc = regresar   ·   máx. 12 caracteres")

    # ---------------- Skins ----------------
    def rects_skins(self):
        n = len(config.SKINS)
        w, h, gap = 140, 190, 14
        x0 = self.W // 2 - (n * w + (n - 1) * gap) // 2
        return [pygame.Rect(x0 + i * (w + gap), 430, w, h) for i in range(n)]

    def rects_jugador_skins(self):
        cx = self.W // 2
        return [pygame.Rect(cx - 230, 120, 220, 44), pygame.Rect(cx + 10, 120, 220, 44)]

    def skins(self, jugador, seleccion):
        self._fondo(120)
        cx = self.W // 2
        ui.titulo_brillante(self.p, "SKINS", self.r.f_grande, (cx, 60))
        for i, r in enumerate(self.rects_jugador_skins()):
            ui.boton(self.p, r, f"JUGADOR {i + 1}", self.r.f_normal, i == jugador)
        equipada = self.prefs.skins[jugador]
        sid, nombre, _ = config.SKINS[seleccion]
        # vista previa grande
        nave = self.r.skins_vitrina[sid]
        grande = pygame.transform.smoothscale(nave, (130, 179))
        self.p.blit(grande, grande.get_rect(center=(cx, 290 + math.sin(self.t * 3) * 6)))
        ui.texto(self.p, nombre, self.r.f_media, ui.AMARILLO, centro=(cx, 395))
        for i, (rect, (s_id, s_nombre, _)) in enumerate(zip(self.rects_skins(), config.SKINS)):
            borde = ui.AMARILLO if i == seleccion else (ui.VERDE if s_id == equipada else (70, 70, 120))
            ui.panel(self.p, rect, alpha=220 if i == seleccion else 160, borde=borde)
            img = self.r.skins_vitrina[s_id]
            img = pygame.transform.smoothscale(img, (80, 110))
            self.p.blit(img, img.get_rect(center=(rect.centerx, rect.y + 75)))
            ui.texto(self.p, s_nombre, self.r.f_chica, ui.BLANCO, centro=(rect.centerx, rect.bottom - 42))
            if s_id == equipada:
                ui.texto(self.p, "EQUIPADA", self.r.f_chica, ui.VERDE, centro=(rect.centerx, rect.bottom - 18))
            if s_id == self.prefs.skins[1 - jugador]:
                ui.texto(self.p, f"J{2 - jugador}", self.r.f_chica, ui.CIAN, topright=(rect.right - 8, rect.y + 6))
        self._ayuda("Flechas / clic = elegir   ·   Enter = equipar   ·   Tab = cambiar jugador   ·   Esc = regresar")

    # ---------------- Dificultad ----------------
    def rects_dificultad(self):
        cx = self.W // 2
        return [pygame.Rect(cx - 400 + i * 275, 300, 250, 300) for i in range(len(config.DIFICULTADES))]

    def dificultad(self, modo, seleccion):
        self._fondo(110)
        cx = self.W // 2
        ui.texto(self.p, "1 PLAYER" if modo == 1 else "2 PLAYERS", self.r.f_media, ui.CIAN, centro=(cx, 150))
        ui.titulo_brillante(self.p, "ELIGE LA DIFICULTAD", self.r.f_grande, (cx, 220))
        colores = {"facil": ui.VERDE, "normal": ui.AMARILLO, "dificil": ui.ROJO}
        for i, (rect, (k, d)) in enumerate(zip(self.rects_dificultad(), config.DIFICULTADES.items())):
            activo = i == seleccion
            ui.panel(self.p, rect, alpha=230 if activo else 160, borde=colores[k] if activo else (70, 70, 120))
            ui.texto(self.p, d["nombre"], self.r.f_grande, colores[k], centro=(rect.centerx, rect.y + 50))
            lineas = [f"Vidas: {d['vidas']}", f"Velocidad: x{d['vel']:g}",
                      f"Oleadas: x{1 / d['llegada']:.2f}", f"Ítems: x{d['drop']:g}"]
            for j, txt in enumerate(lineas):
                ui.texto(self.p, txt, self.r.f_normal, ui.BLANCO, centro=(rect.centerx, rect.y + 115 + j * 34))
            ui.texto(self.p, d["desc"], self.r.f_chica, ui.GRIS, centro=(rect.centerx, rect.bottom - 30)) \
                if len(d["desc"]) < 28 else self._texto_partido(d["desc"], rect.centerx, rect.bottom - 48)
        self._ayuda("Flechas / clic = elegir   ·   Enter = continuar   ·   Esc = regresar")

    def _texto_partido(self, txt, cx, y):
        palabras = txt.split()
        mitad = len(palabras) // 2
        for k, linea in enumerate((" ".join(palabras[:mitad]), " ".join(palabras[mitad:]))):
            ui.texto(self.p, linea, self.r.f_chica, ui.GRIS, centro=(cx, y + k * 22))

    # ---------------- Cómo jugar ----------------
    def como_jugar(self, pagina):
        self._fondo(160)
        cx = self.W // 2
        ui.titulo_brillante(self.p, "CÓMO JUGAR", self.r.f_grande, (cx, 60))
        for i, nombre in enumerate(PAGINAS_AYUDA):
            r = pygame.Rect(0, 0, 200, 40)
            r.center = (cx - 220 + i * 220, 125)
            ui.boton(self.p, r, f"{i + 1}. {nombre}", self.r.f_normal, i == pagina)
        area = pygame.Rect(80, 165, self.W - 160, 570)
        ui.panel(self.p, area)
        x, y = area.x + 40, area.y + 30
        if pagina == 0:
            filas = [
                ("Objetivo", "Destruye enemigos, sobrevive y vence al jefe final del nivel 10.", ui.AMARILLO),
                ("1 jugador", "Mover: WASD o flechas · Disparar: Espacio · Bomba: B", ui.BLANCO),
                ("2 jugadores", "J1: WASD+Espacio, bomba E · J2: flechas+Enter, bomba Shift der.", ui.BLANCO),
                ("Pausa", "P o Esc (Q en pausa = menú) · M silencia el audio", ui.BLANCO),
                ("Vidas", "3 vidas (5 en Fácil). Si te dañan pierdes el arma especial.", ui.ROJO),
                ("Niveles", f"Cada {config.PUNTOS_POR_NIVEL} pts: más enemigos, más rápidos y más seguido.", ui.CIAN),
                ("Jefes", f"Nivel {config.NIVEL_MINIJEFE}: mini-jefe · Nivel {config.NIVEL_JEFE}: jefe final (vencerlo = ganar).", ui.NARANJA),
                ("Combos", "Mata sin recibir daño: 5 = x1.5, 10 = x2, 20 = x2.5, 35 = x3", ui.VERDE),
                ("Asteroides", "Obstáculos: te dañan si chocas, pero puedes destruirlos.", ui.GRIS),
                ("Pantalla 2P", "Dividida, mismos enemigos e ítems. Gana quien tenga más puntos.", ui.BLANCO),
            ]
            for i, (titulo, txt, c) in enumerate(filas):
                ui.texto(self.p, titulo, self.r.f_normal, c, topleft=(x, y + i * 52))
                ui.texto(self.p, txt, self.r.f_chica, ui.BLANCO, topleft=(x + 165, y + 4 + i * 52))
        elif pagina == 1:
            filas = [("facil", "Explorador. 1 impacto, dispara recto."),
                     ("medio", "Caza. 3 impactos, disparo doble."),
                     ("dificil", "Crucero. 6 impactos, disparo en abanico."),
                     ("kamikaze", "Se lanza directo contra tu nave. ¡Esquívalo! (nivel 2+)")]
            for i, (k, txt) in enumerate(filas):
                yy = y + 40 + i * 105
                img = self.r.vitrina[k]
                esc = min(1, 85 / img.get_height())
                img = pygame.transform.smoothscale(img, (int(img.get_width() * esc), int(img.get_height() * esc)))
                self.p.blit(img, img.get_rect(center=(x + 60, yy)))
                ui.texto(self.p, ui.NOMBRE_TIPO[k], self.r.f_media, ui.COLOR_TIPO[k], topleft=(x + 140, yy - 30))
                ui.texto(self.p, f"{config.TIPOS_ENEMIGO[k]['puntos']} pts", self.r.f_normal, ui.AMARILLO,
                         topleft=(x + 330, yy - 26))
                ui.texto(self.p, txt, self.r.f_normal, ui.BLANCO, topleft=(x + 140, yy + 8))
            xj = area.right - 330
            ui.texto(self.p, "Mini-jefe (nivel 5)", self.r.f_normal, ui.NARANJA, topleft=(xj, y + 10))
            ui.texto(self.p, f"{config.MINIJEFE['puntos']} pts", self.r.f_normal, ui.AMARILLO, topleft=(xj, y + 40))
            img = pygame.transform.smoothscale(self.r.minijefe, (70, 108))
            self.p.blit(img, (xj + 180, y))
            ui.texto(self.p, "Jefe final (nivel 10)", self.r.f_normal, ui.ROJO, topleft=(xj, y + 150))
            ui.texto(self.p, f"{config.JEFE['puntos']} pts", self.r.f_normal, ui.AMARILLO, topleft=(xj, y + 180))
            self.p.blit(self.r.jefe_vitrina, (xj, y + 215))
            ui.texto(self.p, "Asteroide: 3-8 pts", self.r.f_normal, ui.GRIS, topleft=(xj, y + 420))
            self.p.blit(self.r.asteroide_vitrina, (xj + 220, y + 400))
        else:
            ui.texto(self.p, "Algunos enemigos sueltan ítems (Bernoulli). Los que llevan uno parpadean con un punto de color.",
                     self.r.f_chica, ui.GRIS, topleft=(x, y - 10))
            items = list(config.ITEMS.items())
            for i, (k, d) in enumerate(items):
                col, fila = i // 6, i % 6
                xx, yy = x + col * 520, y + 30 + fila * 85
                self.p.blit(self.r.items_grandes[k], (xx, yy))
                dur = f" ({d['dur']} s)" if d["dur"] else ""
                ui.texto(self.p, f"{d['nombre']}{dur} · {d['prob']}%", self.r.f_normal, d["color"], topleft=(xx + 60, yy))
                ui.texto(self.p, d["desc"], self.r.f_chica, ui.BLANCO, topleft=(xx + 60, yy + 27))
        self._ayuda("1-3 / flechas / clic = cambiar página   ·   Esc / Enter = regresar")

    def rects_paginas_ayuda(self):
        cx = self.W // 2
        rects = []
        for i in range(len(PAGINAS_AYUDA)):
            r = pygame.Rect(0, 0, 200, 40)
            r.center = (cx - 220 + i * 220, 125)
            rects.append(r)
        return rects

    # ---------------- Logros ----------------
    def logros(self, repo, definiciones):
        self._fondo(160)
        cx = self.W // 2
        ui.titulo_brillante(self.p, "LOGROS", self.r.f_grande, (cx, 60))
        n_ok = len(repo.desbloqueados)
        ui.texto(self.p, f"{n_ok} / {len(definiciones)} desbloqueados   ·   Enemigos destruidos (total): {repo.kills_totales}",
                 self.r.f_normal, ui.CIAN, centro=(cx, 115))
        for i, (lid, (nombre, desc)) in enumerate(definiciones.items()):
            col, fila = i % 2, i // 2
            rect = pygame.Rect(80 + col * 530, 150 + fila * 82, 510, 72)
            ok = lid in repo.desbloqueados
            ui.panel(self.p, rect, alpha=210 if ok else 140, borde=ui.AMARILLO if ok else (60, 60, 90))
            icono = pygame.Rect(rect.x + 14, rect.y + 14, 44, 44)
            pygame.draw.circle(self.p, ui.AMARILLO if ok else (70, 70, 100), icono.center, 22)
            if ok:
                ui.estrella(self.p, icono.center, 15, (60, 40, 10))
            else:
                ui.texto(self.p, "?", self.r.f_media, ui.GRIS, centro=icono.center, sombra=False)
            ui.texto(self.p, nombre, self.r.f_normal, ui.BLANCO if ok else ui.GRIS, topleft=(rect.x + 75, rect.y + 12))
            ui.texto(self.p, desc, self.r.f_chica, ui.GRIS, topleft=(rect.x + 75, rect.y + 42))
            if ok:
                ui.texto(self.p, repo.desbloqueados[lid], self.r.f_chica, ui.AMARILLO,
                         topright=(rect.right - 12, rect.y + 12))
        self._ayuda("Esc / Enter = regresar")

    # ---------------- Opciones ----------------
    def rects_opciones(self):
        cx = self.W // 2
        return [pygame.Rect(cx - 300, 260 + i * 95, 600, 70) for i in range(len(OPCIONES_AJUSTES))]

    def opciones(self, seleccion, prefs, audio_ok):
        self._fondo(140)
        cx = self.W // 2
        ui.titulo_brillante(self.p, "OPCIONES", self.r.f_grande, (cx, 130))
        if not audio_ok:
            ui.texto(self.p, "No se detectó dispositivo de audio: el juego funcionará en silencio",
                     self.r.f_normal, ui.ROJO, centro=(cx, 200))
        valores = [prefs.vol_musica, prefs.vol_efectos]
        for i, (rect, nombre) in enumerate(zip(self.rects_opciones(), OPCIONES_AJUSTES)):
            activo = i == seleccion
            ui.panel(self.p, rect, alpha=230 if activo else 160, borde=ui.AMARILLO if activo else (70, 70, 120))
            ui.texto(self.p, nombre, self.r.f_media, ui.AMARILLO if activo else ui.BLANCO,
                     topleft=(rect.x + 25, rect.centery - 16))
            if i < 2:
                barra = pygame.Rect(rect.x + 250, rect.centery - 9, 260, 18)
                pygame.draw.rect(self.p, (40, 40, 70), barra, border_radius=6)
                pygame.draw.rect(self.p, ui.CIAN, (barra.x, barra.y, int(barra.w * valores[i]), barra.h),
                                 border_radius=6)
                ui.texto(self.p, f"{int(valores[i] * 100)}%", self.r.f_normal, ui.BLANCO,
                         topleft=(barra.right + 15, barra.y - 3))
            elif i == 2:
                ui.texto(self.p, "SÍ" if prefs.mute else "NO", self.r.f_media,
                         ui.ROJO if prefs.mute else ui.VERDE, topleft=(rect.x + 250, rect.centery - 16))
        self._ayuda("Arriba/abajo = elegir   ·   Izq/der = ajustar volumen   ·   Enter = cambiar   ·   Esc = regresar")

    # ---------------- Game over ----------------
    def game_over(self, partida, nuevo_record, logros_nuevos=()):
        self._fondo(140)
        cx = self.W // 2
        res = partida.resultados()
        if partida.modo == 1:
            r = res[0]
            if partida.jefe_derrotado:
                ui.titulo_brillante(self.p, "¡VICTORIA!", self.r.f_titulo, (cx, 150), color=ui.AMARILLO)
                ui.texto(self.p, "Derrotaste al jefe final", self.r.f_normal, ui.VERDE, centro=(cx, 212))
            else:
                ui.titulo_brillante(self.p, "GAME OVER", self.r.f_titulo, (cx, 150), color=ui.ROJO)
            ui.texto(self.p, r["nombre"], self.r.f_grande, ui.CIAN, centro=(cx, 260))
            ui.texto(self.p, f"{r['puntos']} pts", self.r.f_titulo, ui.AMARILLO, centro=(cx, 350))
            ui.texto(self.p, f"Nivel alcanzado: {partida.nivel}", self.r.f_media, ui.BLANCO, centro=(cx, 430))
            self._eliminados(r["eliminados"], cx, 500)
            if nuevo_record and int(self.t * 3) % 2 == 0:
                ui.texto(self.p, "¡NUEVO RÉCORD!", self.r.f_grande, ui.NARANJA, centro=(cx, 620))
        else:
            g = partida.indice_ganador()
            if g == -1:
                ui.titulo_brillante(self.p, "¡EMPATE!", self.r.f_titulo, (cx, 150))
                ui.texto(self.p, f"{res[0]['nombre']}  y  {res[1]['nombre']}", self.r.f_grande,
                         ui.CIAN, centro=(cx, 260))
            else:
                sub = "GANADOR  ·  ¡JEFE FINAL DERROTADO!" if partida.jefe_derrotado else "GANADOR"
                ui.texto(self.p, sub, self.r.f_media, ui.BLANCO, centro=(cx, 110))
                ui.titulo_brillante(self.p, res[g]["nombre"], self.r.f_titulo, (cx, 185), color=ui.AMARILLO)
                img = self.r.skins_vitrina[partida.mundos[g].jugador.skin]
                self.p.blit(img, img.get_rect(center=(cx, 330 + math.sin(self.t * 3) * 8)))
            # puntos de ambos
            for i, r in enumerate(res):
                x = cx - 230 if i == 0 else cx + 230
                gano = (g == i)
                rect = pygame.Rect(0, 0, 340, 150)
                rect.center = (x, 520)
                ui.panel(self.p, rect, borde=ui.AMARILLO if gano else (80, 80, 120))
                ui.texto(self.p, f"P{i + 1}  {r['nombre']}", self.r.f_media,
                         ui.AMARILLO if gano else ui.BLANCO, centro=(x, rect.y + 35))
                ui.texto(self.p, f"{r['puntos']} pts", self.r.f_grande, ui.AMARILLO if gano else ui.GRIS,
                         centro=(x, rect.y + 90))
                e = r["eliminados"]
                ui.texto(self.p, f"F:{e['facil']}  M:{e['medio']}  D:{e['dificil']}  K:{e['kamikaze']}", self.r.f_chica,
                         ui.GRIS, centro=(x, rect.y + 130))
        ui.texto(self.p, f"Dificultad: {config.DIFICULTADES[partida.dificultad]['nombre']}", self.r.f_chica,
                 ui.GRIS, topleft=(20, 20))
        if logros_nuevos:
            ui.texto(self.p, "Logros nuevos: " + ", ".join(logros_nuevos), self.r.f_normal, ui.AMARILLO,
                     centro=(self.W // 2, self.H - 70))
        self._ayuda("Enter = menú    ·    H = ver historial")

    def _eliminados(self, elim, cx, y):
        xs = (cx - 300, cx - 100, cx + 100, cx + 300)
        for x, k in zip(xs, ("facil", "medio", "dificil", "kamikaze")):
            img = self.r.vitrina[k]
            img = pygame.transform.smoothscale(img, (img.get_width() // 2, img.get_height() // 2))
            self.p.blit(img, img.get_rect(midright=(x - 10, y)))
            ui.texto(self.p, f"x {elim[k]}", self.r.f_media, ui.COLOR_TIPO[k], topleft=(x + 5, y - 15))

    # ---------------- Historial ----------------
    def historial(self, registros, pestana):
        self._fondo(150)
        cx = self.W // 2
        ui.titulo_brillante(self.p, "HISTORIAL DE PUNTAJES", self.r.f_grande, (cx, 70))
        for i, nombre in enumerate(("MEJORES", "RECIENTES")):
            r = pygame.Rect(0, 0, 200, 40)
            r.center = (cx - 110 + i * 220, 135)
            ui.boton(self.p, r, nombre, self.r.f_normal, i == pestana)
        tabla = pygame.Rect(90, 170, self.W - 180, 560)
        ui.panel(self.p, tabla)
        cols = [("#", 40), ("Nombre", 210), ("Puntos", 110), ("Nivel", 80), ("Modo", 80),
                ("Resultado", 260), ("Fecha", 200)]
        x = tabla.x + 20
        for nombre, w in cols:
            ui.texto(self.p, nombre, self.r.f_normal, ui.AMARILLO, topleft=(x, tabla.y + 15))
            x += w
        if not registros:
            ui.texto(self.p, "Aún no hay partidas guardadas", self.r.f_media, ui.GRIS, centro=tabla.center)
        for n, reg in enumerate(registros[:12]):
            y = tabla.y + 58 + n * 40
            if n % 2 == 0:
                pygame.draw.rect(self.p, (30, 28, 60), (tabla.x + 8, y - 6, tabla.w - 16, 36), border_radius=6)
            if reg.get("modo") == "2P":
                res = {"gano": "Ganó", "perdio": "Perdió", "empate": "Empate"}.get(reg.get("resultado"), "")
                res = f"{res} vs {reg.get('rival', '?')} ({reg.get('puntos_rival', '?')})"
            else:
                res = "-"
            if reg.get("jefe_derrotado"):
                res = "Venció al jefe" if res == "-" else res + " · Jefe"
            vals = [n + 1, reg.get("nombre", "?"), reg.get("puntos", 0), reg.get("nivel", 1),
                    reg.get("modo", "1P"), res, reg.get("fecha", "")]
            x = tabla.x + 20
            for (col, w), v in zip(cols, vals):
                color = ui.AMARILLO if col == "Puntos" else ui.BLANCO
                ui.texto(self.p, v, self.r.f_chica if col in ("Resultado", "Fecha") else self.r.f_normal,
                         color, topleft=(x, y + (3 if col in ("Resultado", "Fecha") else 0)), sombra=False)
                x += w
        self._ayuda("Tab / flechas = cambiar pestaña    ·    Esc / Enter = regresar")

    # ---------------- Estadísticas ----------------
    def _tabla(self, x, y, encabezados, filas, anchos, max_filas=None):
        f, fb = self.r.f_mono, self.r.f_mono_b
        cx = x
        for h, w in zip(encabezados, anchos):
            self.p.blit(fb.render(h, True, ui.AMARILLO), (cx, y))
            cx += w
        y += 22
        pygame.draw.line(self.p, (90, 90, 140), (x, y - 2), (x + sum(anchos) - 10, y - 2))
        for fila in filas[-max_filas:] if max_filas else filas:
            cx = x
            for v, w in zip(fila, anchos):
                txt = f"{v:.4f}" if isinstance(v, float) else str(v)
                self.p.blit(f.render(txt, True, ui.BLANCO), (cx, y))
                cx += w
            y += 20
        return y

    def estadisticas(self, dist, pestana, origen):
        self._fondo(170)
        cx = self.W // 2
        ui.titulo_brillante(self.p, "ESTADÍSTICAS", self.r.f_grande, (cx, 55))
        ui.texto(self.p, origen, self.r.f_chica, ui.GRIS, centro=(cx, 100))
        for i, (r, nombre) in enumerate(zip(self.rects_pestanas_stats(), PESTANAS_STATS)):
            ui.boton(self.p, r, f"{i + 1}. {nombre}", self.r.f_chica, i == pestana)
        area = pygame.Rect(60, 175, self.W - 120, 570)
        ui.panel(self.p, area)
        x, y = area.x + 25, area.y + 18
        f = self.r.f_normal

        if pestana == 0:
            u = dist.uniforme
            ui.texto(self.p, "x = a + (b - a) · ri", f, ui.CIAN, topleft=(x, y))
            ui.texto(self.p, "Se usa para: posición X de cada enemigo, su deriva lateral y la fase de disparo.",
                     self.r.f_chica, ui.GRIS, topleft=(x, y + 32))
            ui.texto(self.p, "Los mismos límites [a, b] impiden que naves y enemigos salgan de la pantalla.",
                     self.r.f_chica, ui.GRIS, topleft=(x, y + 54))
            filas = [(r["n"], r["ri"], r["a"], r["b"], r["xi"]) for r in u.filas]
            self._tabla(x, y + 90, ["Iter", "ri", "a", "b", "xi = a+(b-a)ri"],
                        filas, [80, 120, 120, 120, 160], max_filas=20)
            if u.filas:
                # promedio de ri (debe tender a 0.5)
                prom_ri = sum(r["ri"] for r in u.filas) / len(u.filas)
                ui.texto(self.p, f"Total generados: {u.total}", f, ui.BLANCO, topleft=(x + 680, y + 120))
                ui.texto(self.p, f"Promedio ri: {prom_ri:.4f}", f, ui.AMARILLO, topleft=(x + 680, y + 160))
                ui.texto(self.p, "Teórico: 0.5000", f, ui.GRIS, topleft=(x + 680, y + 195))

        elif pestana == 1:
            s = dist.tipo
            ui.texto(self.p, f"t = -media · ln(1 - ri)     media = {s.media:.2f}", f, ui.CIAN, topleft=(x, y))
            ui.texto(self.p, "Fácil si t < 1   ·   Medio si 1 <= t < 2   ·   Difícil si t >= 2   (la media sube con el nivel)",
                     self.r.f_chica, ui.GRIS, topleft=(x, y + 32))
            lim = [(ui.NOMBRE_TIPO[r["tipo"]], r["rango_t"], r["p"], r["P"], r["lim_inf"], r["lim_sup"])
                   for r in s.tabla_limites()]
            yy = self._tabla(x, y + 65, ["Tipo", "Rango t", "p(x)", "P(x)", "lim inf", "lim sup"],
                             lim, [90, 110, 90, 90, 90, 90])
            sim = s.porcentajes_simulados()
            teo = s.probabilidades()
            comp = [(ui.NOMBRE_TIPO[k], f"{teo[k] * 100:.2f}%", f"{sim[k] * 100:.2f}%", s.conteo[k])
                    for k in s.TIPOS]
            self._tabla(x, yy + 20, ["Tipo", "Teórico", "Simulado", "Veces"], comp, [90, 110, 110, 80])
            filas = [(r["n"], r["ri"], r["media"], r["t"], ui.NOMBRE_TIPO[r["tipo"]]) for r in s.filas]
            self._tabla(x + 600, y + 65, ["#", "ri", "media", "t", "Tipo"], filas,
                        [55, 85, 75, 85, 80], max_filas=22)

        elif pestana == 2:
            e = dist.llegada
            ui.texto(self.p, f"t = -media · ln(1 - ri)     media actual = {e.media:.2f} s", f, ui.CIAN,
                     topleft=(x, y))
            ui.texto(self.p, f"Tiempo entre oleadas de enemigos (la media baja {config.EXP_LLEGADA_MEDIA_POR_NIVEL} s por nivel, "
                     f"mínimo {config.EXP_LLEGADA_MEDIA_MIN} s).", self.r.f_chica, ui.GRIS, topleft=(x, y + 32))
            filas = [(r["n"], r["ri"], r["media"], r["x"]) for r in e.filas]
            self._tabla(x, y + 70, ["Oleada", "ri", "media", "Tiempo (s)"], filas, [90, 120, 100, 120],
                        max_filas=21)
            if e.filas:
                ui.texto(self.p, f"Oleadas generadas: {e.total}", f, ui.BLANCO, topleft=(x + 560, y + 100))
                ui.texto(self.p, f"Promedio simulado: {e.promedio_simulado():.4f} s", f, ui.AMARILLO,
                         topleft=(x + 560, y + 140))
                medias = [r["media"] for r in e.filas]
                ui.texto(self.p, f"Media teórica (promedio): {sum(medias) / len(medias):.4f} s", f, ui.GRIS,
                         topleft=(x + 560, y + 175))

        elif pestana == 4:
            self._tab_bernoulli(dist.drop, x, y, "¿El enemigo suelta ítem?")
            self._tab_bernoulli(dist.kamikaze, x + 560, y, "¿La oleada trae kamikazes? (nivel 2+)")
        elif pestana == 5:
            it = dist.item
            ui.texto(self.p, "Transformada inversa con porcentajes: ¿qué ítem cae?", f, ui.CIAN, topleft=(x, y))
            ui.texto(self.p, "Solo se usa cuando la Bernoulli dice SUELTA.", self.r.f_chica, ui.GRIS,
                     topleft=(x, y + 32))
            total = sum(it.conteo.values()) or 1
            lim = [(config.ITEMS[r["x"]]["nombre"][:14], r["p"], r["lim_inf"], r["lim_sup"],
                    f"{it.conteo[r['x']] * 100 / total:.1f}%") for r in it.tabla_limites()]
            self._tabla(x, y + 65, ["Ítem", "p(x)", "lim inf", "lim sup", "Simulado"], lim,
                        [160, 90, 90, 90, 90])
            filas = [(r["n"], r["ri"], config.ITEMS[r["x"]]["nombre"][:14]) for r in it.filas]
            self._tabla(x + 620, y + 65, ["#", "ri", "Ítem"], filas, [60, 100, 170], max_filas=22)
        else:
            h = dist.historica
            ui.texto(self.p, "Transformada inversa con datos históricos: enemigos por oleada", f, ui.CIAN,
                     topleft=(x, y))
            ui.texto(self.p, f"Datos ({len(h.datos)}): {h.datos}", self.r.f_chica, ui.GRIS, topleft=(x, y + 32))
            ui.texto(self.p, f"Se suma 1 enemigo extra por oleada cada {config.NIVELES_POR_ENEMIGO_EXTRA} niveles.",
                     self.r.f_chica, ui.GRIS, topleft=(x, y + 54))
            lim = [(r["x"], r["p"], r["P"], r["lim_inf"], r["lim_sup"], h.conteo[r["x"]]) for r in h.tabla_limites()]
            yy = self._tabla(x, y + 85, ["X", "p(x)", "P(x)", "lim inf", "lim sup", "Veces"],
                             lim, [50, 90, 90, 90, 90, 70])
            ui.texto(self.p, f"Media teórica: {h.media_teorica():.4f}", f, ui.AMARILLO, topleft=(x, yy + 20))
            if h.filas:
                prom = sum(r["x"] for r in h.filas) / len(h.filas)
                ui.texto(self.p, f"Media simulada: {prom:.4f}", f, ui.AMARILLO, topleft=(x, yy + 55))
            filas = [(r["n"], r["ri"], r["x"]) for r in h.filas]
            self._tabla(x + 620, y + 85, ["Oleada", "ri", "Enemigos"], filas, [90, 110, 100], max_filas=21)

        self._ayuda("1-6 / flechas / clic = cambiar pestaña    ·    Esc / Enter = regresar")

    def _tab_bernoulli(self, b, x, y, titulo):
        f = self.r.f_normal
        ui.texto(self.p, titulo, f, ui.CIAN, topleft=(x, y))
        ui.texto(self.p, f"p = {b.p:.2f}   ·   X = 0 si ri < 1 - p,  X = 1 si ri >= 1 - p", self.r.f_chica,
                 ui.GRIS, topleft=(x, y + 32))
        lim = [(r["estado"], r["x"], r["p"], r["P"], r["lim_inf"], r["lim_sup"]) for r in b.tabla_limites()]
        yy = self._tabla(x, y + 62, ["Estado", "X", "p(x)", "P(x)", "inf", "sup"], lim, [110, 30, 75, 75, 75, 75])
        ui.texto(self.p, f"Simulado: {b.porcentaje_simulado() * 100:.2f}%  de {b.total}  (teórico {b.p * 100:.0f}%)",
                 self.r.f_chica, ui.AMARILLO, topleft=(x, yy + 8))
        filas = [(r["n"], r["ri"], r["x"], r["evento"]) for r in b.filas]
        self._tabla(x, yy + 40, ["#", "ri", "X", "Evento"], filas, [60, 90, 40, 120], max_filas=15)

    def rects_pestanas_stats(self):
        n, w = len(PESTANAS_STATS), 180
        x0 = self.W // 2 - n * w // 2
        return [pygame.Rect(x0 + i * w + 6, 120, w - 12, 40) for i in range(n)]
