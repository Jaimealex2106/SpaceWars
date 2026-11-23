"""Controladores de cada pantalla (estados de la aplicación).

Cada estado recibe eventos de pygame, actualiza el modelo y le pide a la
vista que dibuje. Para cambiar de pantalla llaman a app.cambiar(...).
"""
import pygame
import config
from model.partida import Partida, Distribuciones
from model.director import DirectorOleadas
from model.logros import LOGROS
from view.pantallas import OPCIONES_MENU, PESTANAS_STATS, PAGINAS_AYUDA, OPCIONES_AJUSTES
from view.vista_juego import VistaJuego

TECLAS_CONFIRMAR = (pygame.K_RETURN, pygame.K_KP_ENTER)


def _clic(e):
    return e.type == pygame.MOUSEBUTTONDOWN and e.button == 1


class Estado:
    musica = "menu"
    permite_mute = True   # la tecla M silencia (excepto al escribir nombres)

    def __init__(self, app):
        self.app = app
        self.vista = app.vista_pantallas
        app.audio.musica(self.musica)

    def sonido(self, nombre):
        self.app.audio.efecto(nombre)

    def manejar_evento(self, e):
        pass

    def actualizar(self, dt):
        self.vista.actualizar(dt)

    def dibujar(self):
        pass


class EstadoLista(Estado):
    """Estado con opciones seleccionables por teclado y mouse."""

    def __init__(self, app, seleccion=0):
        super().__init__(app)
        self.sel = seleccion

    def rects(self):
        return []

    def elegir(self, i):
        pass

    def regresar(self):
        pass

    def manejar_evento(self, e):
        n = len(self.rects())
        if e.type == pygame.KEYDOWN:
            if e.key in self.teclas_anterior:
                self.sel = (self.sel - 1) % n
                self.sonido("menu_mover")
            elif e.key in self.teclas_siguiente:
                self.sel = (self.sel + 1) % n
                self.sonido("menu_mover")
            elif e.key in TECLAS_CONFIRMAR or e.key == pygame.K_SPACE:
                self.sonido("menu_ok")
                self.elegir(self.sel)
            elif e.key == pygame.K_ESCAPE:
                self.regresar()
        elif e.type == pygame.MOUSEMOTION:
            for i, r in enumerate(self.rects()):
                if r.collidepoint(e.pos) and self.sel != i:
                    self.sel = i
                    self.sonido("menu_mover")
        elif _clic(e):
            for i, r in enumerate(self.rects()):
                if r.collidepoint(e.pos):
                    self.sel = i
                    self.sonido("menu_ok")
                    self.elegir(i)
                    break

    teclas_anterior = (pygame.K_UP, pygame.K_w)
    teclas_siguiente = (pygame.K_DOWN, pygame.K_s)


# ---------------------------------------------------------------- Bienvenida
class EstadoBienvenida(Estado):
    def __init__(self, app):
        super().__init__(app)
        self.espera = 0.4  # evita saltarse la pantalla por una tecla previa

    def manejar_evento(self, e):
        if self.espera > 0:
            return
        if (e.type == pygame.KEYDOWN and e.key != pygame.K_m) or e.type == pygame.MOUSEBUTTONDOWN:
            self.sonido("menu_ok")
            self.app.cambiar(EstadoMenu(self.app))

    def actualizar(self, dt):
        super().actualizar(dt)
        self.espera -= dt

    def dibujar(self):
        self.vista.bienvenida()


# ---------------------------------------------------------------- Menú
class EstadoMenu(EstadoLista):
    def rects(self):
        return self.vista.rects_menu()

    def elegir(self, i):
        op = OPCIONES_MENU[i]
        destinos = {
            "1 PLAYER": lambda: EstadoDificultad(self.app, modo=1),
            "2 PLAYERS": lambda: EstadoDificultad(self.app, modo=2),
            "SKINS": lambda: EstadoSkins(self.app),
            "CÓMO JUGAR": lambda: EstadoComoJugar(self.app),
            "LOGROS": lambda: EstadoLogros(self.app),
            "HISTORIAL": lambda: EstadoHistorial(self.app),
            "ESTADÍSTICAS": lambda: EstadoEstadisticas(self.app),
            "OPCIONES": lambda: EstadoOpciones(self.app),
        }
        if op in destinos:
            self.app.cambiar(destinos[op]())
        else:
            self.app.salir()

    def regresar(self):
        self.app.cambiar(EstadoBienvenida(self.app))

    def manejar_evento(self, e):
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_1, pygame.K_2):
            self.elegir(e.key - pygame.K_1)
            return
        super().manejar_evento(e)

    def dibujar(self):
        self.vista.menu(self.sel)


def volver_menu(app, opcion):
    app.cambiar(EstadoMenu(app, OPCIONES_MENU.index(opcion)))


# ---------------------------------------------------------------- Dificultad
class EstadoDificultad(EstadoLista):
    teclas_anterior = (pygame.K_LEFT, pygame.K_a)
    teclas_siguiente = (pygame.K_RIGHT, pygame.K_d)

    def __init__(self, app, modo):
        ids = list(config.DIFICULTADES)
        super().__init__(app, ids.index(app.prefs.dificultad))
        self.modo = modo

    def rects(self):
        return self.vista.rects_dificultad()

    def elegir(self, i):
        self.app.prefs.dificultad = list(config.DIFICULTADES)[i]
        self.app.prefs.guardar()
        self.app.cambiar(EstadoNombre(self.app, self.modo, self.app.prefs.dificultad))

    def regresar(self):
        volver_menu(self.app, "1 PLAYER" if self.modo == 1 else "2 PLAYERS")

    def dibujar(self):
        self.vista.dificultad(self.modo, self.sel)


# ---------------------------------------------------------------- Nombre
class EstadoNombre(Estado):
    MAX = 12
    permite_mute = False

    def __init__(self, app, modo, dificultad=config.DIFICULTAD_DEFECTO):
        super().__init__(app)
        self.modo = modo
        self.dificultad = dificultad
        self.nombres = []
        self.texto = ""
        self.error = ""

    def manejar_evento(self, e):
        if e.type != pygame.KEYDOWN:
            return
        if e.key == pygame.K_ESCAPE:
            if self.nombres:  # regresar al jugador 1
                self.texto = self.nombres.pop()
            else:
                self.app.cambiar(EstadoDificultad(self.app, self.modo))
        elif e.key in TECLAS_CONFIRMAR:
            nombre = self.texto.strip()
            if not nombre:
                self.error = "El nombre no puede estar vacío"
            elif nombre.lower() in (n.lower() for n in self.nombres):
                self.error = "Ese nombre ya lo usa el jugador 1"
            else:
                self.sonido("menu_ok")
                self.nombres.append(nombre)
                self.texto, self.error = "", ""
                if len(self.nombres) == self.modo:
                    self.app.cambiar(EstadoJuego(self.app, self.nombres, self.dificultad))
        elif e.key == pygame.K_BACKSPACE:
            self.texto = self.texto[:-1]
        elif e.unicode and e.unicode.isprintable() and len(self.texto) < self.MAX:
            self.texto += e.unicode
            self.error = ""

    def dibujar(self):
        self.vista.nombre(len(self.nombres), self.modo, self.texto, self.error)


# ---------------------------------------------------------------- Juego
class EstadoJuego(Estado):
    musica = "juego"

    def __init__(self, app, nombres, dificultad=config.DIFICULTAD_DEFECTO):
        super().__init__(app)
        self.nombres = nombres
        self.partida = Partida(nombres, skins=app.prefs.skins[:len(nombres)], dificultad=dificultad)
        app.ultima_partida = self.partida
        self.vista_juego = VistaJuego(app.pantalla, app.recursos, self.partida, app.audio)
        self.pausa = False
        self.fin = 0.0  # pequeña espera tras terminar para ver la explosión
        self.bombas = [False] * len(nombres)
        self.t_logros = 0.0
        self.logros_nuevos = []

    def manejar_evento(self, e):
        if self.partida.esperando_decision:
            self._evento_decision(e)
            return
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_p, pygame.K_ESCAPE):
                self.pausa = not self.pausa
                self.app.audio.laser(False)
            elif e.key == pygame.K_q and self.pausa:
                self.app.audio.detener_todo()
                self.app.cambiar(EstadoMenu(self.app))
            elif not self.pausa:
                # bombas (se usan al presionar, no al mantener)
                if self.partida.modo == 1 and e.key in (pygame.K_b, pygame.K_LSHIFT, pygame.K_RSHIFT):
                    self.bombas[0] = True
                elif self.partida.modo == 2:
                    if e.key in (pygame.K_e, pygame.K_LSHIFT):
                        self.bombas[0] = True
                    elif e.key in (pygame.K_RSHIFT, pygame.K_KP0):
                        self.bombas[1] = True
        elif e.type == getattr(pygame, "WINDOWFOCUSLOST", -1):
            self.pausa = True
            self.app.audio.laser(False)

    def _evento_decision(self, e):
        """Pantalla de victoria tras vencer al jefe: seguir jugando o terminar."""
        vj = self.vista_juego
        elegir = None
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_a, pygame.K_d, pygame.K_TAB):
                vj.sel_decision = 1 - vj.sel_decision
                self.sonido("menu_mover")
            elif e.key in TECLAS_CONFIRMAR:
                elegir = vj.sel_decision
            elif e.key == pygame.K_s:
                elegir = 0
            elif e.key == pygame.K_ESCAPE:
                elegir = 1
        elif e.type == pygame.MOUSEMOTION:
            for i, r in enumerate(vj.rects_decision()):
                if r.collidepoint(e.pos):
                    vj.sel_decision = i
        elif _clic(e):
            for i, r in enumerate(vj.rects_decision()):
                if r.collidepoint(e.pos):
                    elegir = i
        if elegir is not None:
            self.sonido("menu_ok")
        if elegir == 0:
            self.partida.seguir_jugando()
            self.app.audio.musica("juego")
        elif elegir == 1:
            self.partida.terminar()
            self.fin = 1.6  # ir directo a la pantalla final

    def _controles(self):
        k = pygame.key.get_pressed()
        b = self.bombas
        self.bombas = [False] * len(b)
        if self.partida.modo == 1:
            dx = (k[pygame.K_d] or k[pygame.K_RIGHT]) - (k[pygame.K_a] or k[pygame.K_LEFT])
            dy = (k[pygame.K_s] or k[pygame.K_DOWN]) - (k[pygame.K_w] or k[pygame.K_UP])
            return [(dx, dy, bool(k[pygame.K_SPACE]), b[0])]
        j1 = (k[pygame.K_d] - k[pygame.K_a], k[pygame.K_s] - k[pygame.K_w], bool(k[pygame.K_SPACE]), b[0])
        j2 = (k[pygame.K_RIGHT] - k[pygame.K_LEFT], k[pygame.K_DOWN] - k[pygame.K_UP],
              bool(k[pygame.K_RETURN] or k[pygame.K_KP_ENTER] or k[pygame.K_RCTRL]), b[1])
        return [j1, j2]

    def actualizar(self, dt):
        if self.pausa:
            return
        p = self.partida
        if p.esperando_decision:
            self.vista_juego.actualizar(dt)
            return
        estaba_victoria = p.victoria_pendiente
        p.actualizar(dt, self._controles())
        self.vista_juego.procesar_eventos()
        self.vista_juego.actualizar(dt)

        # música según la situación
        if p.jefe_activo:
            self.app.audio.musica("jefe")
        elif not p.victoria_pendiente and not p.esperando_decision:
            self.app.audio.musica("juego")
        if p.victoria_pendiente and not estaba_victoria:
            self.app.audio.musica(None)
            self.sonido("victoria")

        # logros durante la partida
        self.t_logros -= dt
        if self.t_logros <= 0:
            self.t_logros = 0.5
            for lid in self.app.logros.revisar(p):
                self.logros_nuevos.append(LOGROS[lid][0])
                self.vista_juego.mostrar_logro(LOGROS[lid][0])

        if p.terminada:
            if self.fin == 0:
                self.app.audio.laser(False)
                self.app.audio.musica(None)
                if not p.finalizada:
                    self.sonido("game_over")
            self.fin += dt
            if self.fin > 1.6:
                nuevo_record = self._es_record()
                self.app.repo.guardar_partida(p)
                for lid in self.app.logros.cerrar_partida(p):
                    self.logros_nuevos.append(LOGROS[lid][0])
                self.app.cambiar(EstadoGameOver(self.app, p, nuevo_record, self.logros_nuevos))

    def _es_record(self):
        mejores = self.app.repo.mejores(1)
        tope = mejores[0]["puntos"] if mejores else 0
        return max(m.jugador.puntos for m in self.partida.mundos) > tope

    def dibujar(self):
        self.vista_juego.dibujar(self.pausa)


# ---------------------------------------------------------------- Game over
class EstadoGameOver(Estado):
    musica = None

    def __init__(self, app, partida, nuevo_record, logros_nuevos=()):
        super().__init__(app)
        self.partida = partida
        self.nuevo_record = nuevo_record
        self.logros_nuevos = list(logros_nuevos)
        self.espera = 0.8
        if partida.jefe_derrotado:
            self.sonido("victoria")

    def manejar_evento(self, e):
        if self.espera > 0 or e.type != pygame.KEYDOWN:
            return
        if e.key == pygame.K_h:
            self.app.cambiar(EstadoHistorial(self.app, pestana=1))
        elif e.key in TECLAS_CONFIRMAR or e.key in (pygame.K_ESCAPE, pygame.K_SPACE):
            self.app.cambiar(EstadoMenu(self.app))

    def actualizar(self, dt):
        super().actualizar(dt)
        self.espera -= dt

    def dibujar(self):
        self.vista.game_over(self.partida, self.nuevo_record, self.logros_nuevos)


# ---------------------------------------------------------------- Historial
class EstadoHistorial(Estado):
    def __init__(self, app, pestana=0):
        super().__init__(app)
        self.pestana = pestana

    def manejar_evento(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_TAB, pygame.K_LEFT, pygame.K_RIGHT):
                self.pestana = 1 - self.pestana
                self.sonido("menu_mover")
            elif e.key in TECLAS_CONFIRMAR or e.key == pygame.K_ESCAPE:
                volver_menu(self.app, "HISTORIAL")
        elif _clic(e):
            cx = self.vista.W // 2
            for i in range(2):
                r = pygame.Rect(0, 0, 200, 40)
                r.center = (cx - 110 + i * 220, 135)
                if r.collidepoint(e.pos):
                    self.pestana = i

    def dibujar(self):
        repo = self.app.repo
        regs = repo.mejores(12) if self.pestana == 0 else repo.recientes(12)
        self.vista.historial(regs, self.pestana)


# ---------------------------------------------------------------- Pestañas genéricas
class EstadoPestanas(Estado):
    n_pestanas = 1
    opcion_menu = "ESTADÍSTICAS"

    def __init__(self, app):
        super().__init__(app)
        self.pestana = 0

    def rects_pestanas(self):
        return []

    def manejar_evento(self, e):
        n = self.n_pestanas
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_RIGHT, pygame.K_TAB):
                self.pestana = (self.pestana + 1) % n
                self.sonido("menu_mover")
            elif e.key == pygame.K_LEFT:
                self.pestana = (self.pestana - 1) % n
                self.sonido("menu_mover")
            elif pygame.K_1 <= e.key < pygame.K_1 + n:
                self.pestana = e.key - pygame.K_1
            elif e.key in TECLAS_CONFIRMAR or e.key == pygame.K_ESCAPE:
                volver_menu(self.app, self.opcion_menu)
        elif _clic(e):
            for i, r in enumerate(self.rects_pestanas()):
                if r.collidepoint(e.pos):
                    self.pestana = i
                    self.sonido("menu_mover")


class EstadoEstadisticas(EstadoPestanas):
    n_pestanas = len(PESTANAS_STATS)
    opcion_menu = "ESTADÍSTICAS"

    def __init__(self, app):
        super().__init__(app)
        if app.ultima_partida is not None:
            self.dist = app.ultima_partida.dist
            self.origen = "Datos generados durante tu última partida"
        else:
            # aún no se ha jugado: simulamos 40 oleadas de muestra
            self.dist = Distribuciones(app.pantalla.get_width(), app.pantalla.get_height(), consola=False)
            director = DirectorOleadas(app.pantalla.get_width(), self.dist)
            for i in range(40):
                director.set_nivel(1 + i // 5)
                self.dist.llegada.generar()
                director.generar_oleada()
            self.origen = "Simulación de muestra (40 oleadas) - juega una partida para ver tus propios datos"

    def rects_pestanas(self):
        return self.vista.rects_pestanas_stats()

    def dibujar(self):
        self.vista.estadisticas(self.dist, self.pestana, self.origen)


class EstadoComoJugar(EstadoPestanas):
    n_pestanas = len(PAGINAS_AYUDA)
    opcion_menu = "CÓMO JUGAR"

    def rects_pestanas(self):
        return self.vista.rects_paginas_ayuda()

    def dibujar(self):
        self.vista.como_jugar(self.pestana)


# ---------------------------------------------------------------- Logros
class EstadoLogros(Estado):
    def manejar_evento(self, e):
        if e.type == pygame.KEYDOWN and (e.key in TECLAS_CONFIRMAR or e.key == pygame.K_ESCAPE):
            volver_menu(self.app, "LOGROS")

    def dibujar(self):
        self.vista.logros(self.app.logros, LOGROS)


# ---------------------------------------------------------------- Opciones
class EstadoOpciones(EstadoLista):
    def rects(self):
        return self.vista.rects_opciones()

    def _ajustar(self, delta):
        prefs = self.app.prefs
        if self.sel == 0:
            prefs.vol_musica = round(min(1.0, max(0.0, prefs.vol_musica + delta)), 2)
        elif self.sel == 1:
            prefs.vol_efectos = round(min(1.0, max(0.0, prefs.vol_efectos + delta)), 2)
            self.sonido("item")
        else:
            return
        prefs.guardar()
        self.app.audio.aplicar_volumen()

    def elegir(self, i):
        op = OPCIONES_AJUSTES[i]
        if op.startswith("Silencio"):
            self.app.audio.alternar_mute()
        elif op == "Regresar":
            self.regresar()

    def regresar(self):
        volver_menu(self.app, "OPCIONES")

    def manejar_evento(self, e):
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_LEFT, pygame.K_a):
            self._ajustar(-0.1)
            return
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_RIGHT, pygame.K_d):
            self._ajustar(0.1)
            return
        if _clic(e) and self.sel < 2:
            # clic sobre la barra = fijar volumen en ese punto
            r = self.rects()[self.sel]
            barra = pygame.Rect(r.x + 250, r.centery - 15, 260, 30)
            if barra.collidepoint(e.pos):
                valor = round((e.pos[0] - barra.x) / barra.w, 2)
                self._ajustar(valor - (self.app.prefs.vol_musica if self.sel == 0 else self.app.prefs.vol_efectos))
                return
        super().manejar_evento(e)

    def dibujar(self):
        self.vista.opciones(self.sel, self.app.prefs, self.app.audio.ok)


# ---------------------------------------------------------------- Skins
class EstadoSkins(Estado):
    def __init__(self, app):
        super().__init__(app)
        self.jugador = 0
        self.sel = self._indice(app.prefs.skins[0])

    @staticmethod
    def _indice(skin_id):
        ids = [s[0] for s in config.SKINS]
        return ids.index(skin_id) if skin_id in ids else 0

    def _cambiar_jugador(self, j):
        self.jugador = j
        self.sel = self._indice(self.app.prefs.skins[j])
        self.sonido("menu_mover")

    def _equipar(self):
        self.app.prefs.set_skin(self.jugador, config.SKINS[self.sel][0])
        self.sonido("menu_ok")

    def manejar_evento(self, e):
        n = len(config.SKINS)
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_RIGHT, pygame.K_d):
                self.sel = (self.sel + 1) % n
                self.sonido("menu_mover")
            elif e.key in (pygame.K_LEFT, pygame.K_a):
                self.sel = (self.sel - 1) % n
                self.sonido("menu_mover")
            elif e.key in TECLAS_CONFIRMAR or e.key == pygame.K_SPACE:
                self._equipar()
            elif e.key in (pygame.K_TAB, pygame.K_UP, pygame.K_DOWN, pygame.K_w, pygame.K_s):
                self._cambiar_jugador(1 - self.jugador)
            elif e.key == pygame.K_1:
                self._cambiar_jugador(0)
            elif e.key == pygame.K_2:
                self._cambiar_jugador(1)
            elif e.key == pygame.K_ESCAPE:
                volver_menu(self.app, "SKINS")
        elif e.type == pygame.MOUSEMOTION:
            for i, r in enumerate(self.vista.rects_skins()):
                if r.collidepoint(e.pos):
                    self.sel = i
        elif _clic(e):
            for i, r in enumerate(self.vista.rects_skins()):
                if r.collidepoint(e.pos):
                    self.sel = i
                    self._equipar()
            for j, r in enumerate(self.vista.rects_jugador_skins()):
                if r.collidepoint(e.pos):
                    self._cambiar_jugador(j)

    def dibujar(self):
        self.vista.skins(self.jugador, self.sel)
