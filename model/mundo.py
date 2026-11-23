"""Mundo de un jugador: su nave, sus enemigos, ítems, asteroides y balas.

En 2 jugadores hay dos mundos independientes (las naves no se mezclan),
pero ambos reciben exactamente las mismas oleadas, ítems y asteroides.
"""
import random
import config
from model.distribuciones import DistribucionUniforme
from model.entidades import Jugador, Enemigo, Jefe, Item, Asteroide


class Mundo:
    def __init__(self, nombre, ancho, alto, skin=config.SKIN_DEFECTO, dificultad=config.DIFICULTAD_DEFECTO):
        self.ancho, self.alto = ancho, alto
        self.dif = config.DIFICULTADES[dificultad]
        self.jugador = Jugador(nombre, ancho, alto, skin, self.dif["vidas"])
        self.enemigos = []
        self.asteroides = []
        self.items = []
        self.balas_jugador = []
        self.balas_enemigas = []
        self.pendientes = []   # [(tiempo_restante, spec, mult_vel)]
        self.eventos = []      # para la vista y el audio
        self.tiempo = 0.0
        self.jefe = None
        self.jefe_vencido = False
        self.laser_activo = False
        self.t_chispa_laser = 0.0

        # Límites con la uniforme: [a, b] donde cada objeto puede estar
        rng = random.Random()
        jw, jh = config.JUGADOR_TAM
        self.lim_jug_x = DistribucionUniforme(0, ancho - jw, rng, "Lim-Jugador-X")
        self.lim_jug_y = DistribucionUniforme(40, alto - jh, rng, "Lim-Jugador-Y")
        self.lim_enemigo_x = {
            t: DistribucionUniforme(0, ancho - d["tam"][0], rng, f"Lim-{t}-X")
            for t, d in config.TIPOS_ENEMIGO.items()
        }
        self.lim_ast_x = {
            t: DistribucionUniforme(0, ancho - d["tam"][0], rng, f"Lim-ast-{t}-X")
            for t, d in config.ASTEROIDES.items()
        }
        self.lim_jefe_x = None

    @property
    def terminado(self):
        return not self.jugador.vivo

    # ---------- entradas desde la partida ----------
    def aparecer_jefe(self, mini=False):
        self.jefe = Jefe(self.ancho, mini=mini)
        self.jefe_vencido = False
        rng = random.Random()
        self.lim_jefe_x = DistribucionUniforme(0, self.ancho - self.jefe.w, rng, "Lim-Jefe-X")
        self.eventos.append(("jefe_aparece", self.jefe.centro, mini))

    def recibir_oleada(self, specs, mult_vel):
        for s in specs:
            self.pendientes.append([s.retraso, s, mult_vel])

    def recibir_asteroides(self, specs, mult_vel):
        for s in specs:
            self.asteroides.append(Asteroide(s, mult_vel))

    # ---------- ciclo ----------
    def actualizar(self, dt, dx, dy, disparar, bomba=False):
        self.eventos = []
        self.laser_activo = False
        if self.terminado:
            return
        self.tiempo += dt
        j = self.jugador
        # "tiempo lento" frena a todo lo enemigo
        dt_e = dt * (config.LENTO_FACTOR if j.lento else 1.0)

        # --- nave del jugador ---
        j.actualizar(dt)
        j.mover(dx, dy, dt, self.lim_jug_x, self.lim_jug_y)
        if disparar and j.arma == "laser":
            self.laser_activo = True
        elif disparar and j.puede_disparar():
            nuevas = j.disparar()
            self.balas_jugador.extend(nuevas)
            if nuevas:
                self.eventos.append(("disparo", j.centro))
        if bomba and j.usar_bomba():
            self._detonar_bomba()

        # --- aparición de enemigos programados (tiempo real, igual en ambos mundos) ---
        quedan = []
        for p in self.pendientes:
            p[0] -= dt
            if p[0] <= 0:
                self.enemigos.append(Enemigo(p[1], p[2]))
            else:
                quedan.append(p)
        self.pendientes = quedan

        # --- enemigos, jefe, asteroides ---
        objetivo = j.centro
        for e in self.enemigos:
            self.balas_enemigas.extend(e.actualizar(dt_e, self.lim_enemigo_x[e.tipo], self.alto, objetivo))
        if self.jefe:
            self.balas_enemigas.extend(self.jefe.actualizar(dt_e, self.lim_jefe_x))
        for a in self.asteroides:
            a.actualizar(dt_e, self.lim_ast_x[a.tam], self.alto)

        # --- ítems ---
        iman = j.centro if j.iman else None
        for it in self.items:
            it.actualizar(dt, self.alto, iman)

        # --- balas ---
        objetivos = self._objetivos()
        for b in self.balas_jugador:
            b.actualizar(dt, self.ancho, self.alto, objetivos)
        for b in self.balas_enemigas:
            b.actualizar(dt_e, self.ancho, self.alto)

        if self.laser_activo:
            self._laser(dt)
        self._colisiones()

        self.enemigos = [e for e in self.enemigos if e.activo]
        self.asteroides = [a for a in self.asteroides if a.activo]
        self.items = [i for i in self.items if i.activo]
        self.balas_jugador = [b for b in self.balas_jugador if b.activo]
        self.balas_enemigas = [b for b in self.balas_enemigas if b.activo]

    def _objetivos(self):
        objs = [e for e in self.enemigos if e.activo and e.y > -e.h * 0.5]
        if self.jefe and not self.jefe.entrando:
            objs.append(self.jefe)
        return objs

    # ---------- armas especiales ----------
    def rayo_laser(self):
        """(x0, x1, y_tope) del rayo láser del jugador."""
        j = self.jugador
        cx = j.x + j.w / 2
        return (cx - 9, cx + 9, j.y + 10)

    def _laser(self, dt):
        x0, x1, y_max = self.rayo_laser()
        dano = config.LASER_DPS * dt
        self.t_chispa_laser -= dt
        chispa = self.t_chispa_laser <= 0
        if chispa:
            self.t_chispa_laser = 0.08
        for e in self.enemigos:
            if e.activo and e.colisiona_franja(x0, x1, y_max):
                if e.recibir_dano(dano):
                    self._enemigo_destruido(e)
                elif chispa:
                    self.eventos.append(("impacto", (e.centro[0], e.y + e.h)))
        for a in self.asteroides:
            if a.activo and a.colisiona_franja(x0, x1, y_max):
                if a.recibir_dano(dano):
                    self._asteroide_destruido(a)
        if self.jefe and self.jefe.colisiona_franja(x0, x1, y_max):
            if self.jefe.recibir_dano(dano):
                self._jefe_destruido()
            elif chispa:
                self.eventos.append(("impacto", (self.jefe.centro[0], self.jefe.y + self.jefe.h * 0.8)))

    def _detonar_bomba(self):
        self.eventos.append(("bomba", self.jugador.centro))
        for e in self.enemigos:
            if e.activo:
                e.activo = False
                self._enemigo_destruido(e)
        for a in self.asteroides:
            if a.activo:
                a.activo = False
                self._asteroide_destruido(a)
        self.balas_enemigas = []
        if self.jefe and not self.jefe.entrando:
            if self.jefe.recibir_dano(config.BOMBA_DANO_JEFE):
                self._jefe_destruido()

    # ---------- colisiones ----------
    def _colisiones(self):
        j = self.jugador
        for b in self.balas_jugador:
            if not b.activo:
                continue
            for e in self.enemigos:
                if e.activo and b.colisiona(e):
                    b.activo = False
                    if e.recibir_dano(b.dano):
                        self._enemigo_destruido(e)
                    else:
                        self.eventos.append(("impacto", (b.x, b.y)))
                    break
            if not b.activo:
                continue
            for a in self.asteroides:
                if a.activo and b.colisiona(a):
                    b.activo = False
                    if a.recibir_dano(b.dano):
                        self._asteroide_destruido(a)
                    else:
                        self.eventos.append(("impacto", (b.x, b.y)))
                    break
            if not b.activo:
                continue
            if self.jefe and b.colisiona(self.jefe):
                b.activo = False
                if self.jefe.recibir_dano(b.dano):
                    self._jefe_destruido()
                else:
                    self.eventos.append(("impacto", (b.x, b.y)))

        # balas enemigas vs jugador
        for b in self.balas_enemigas:
            if b.activo and b.colisiona(j):
                b.activo = False
                self._jugador_golpeado()

        # choques directos
        if self.jefe and self.jefe.colisiona(j):
            self._jugador_golpeado()
        for e in self.enemigos:
            if e.activo and e.colisiona(j) and j.invulnerable <= 0:
                e.activo = False
                self.eventos.append(("explosion", e.centro, e.tipo))
                self._jugador_golpeado()
        for a in self.asteroides:
            if a.activo and a.colisiona(j) and j.invulnerable <= 0:
                a.activo = False
                self.eventos.append(("explosion", a.centro, "asteroide"))
                self._jugador_golpeado()

        # ítems
        for it in self.items:
            if it.activo and it.colisiona(j):
                it.activo = False
                nombre = j.aplicar_item(it.tipo)
                self.eventos.append(("item", it.centro, it.tipo, nombre))

    # ---------- consecuencias ----------
    def _soltar_item(self, tipo, centro):
        if tipo:
            self.items.append(Item(tipo, *centro))

    def _enemigo_destruido(self, e):
        j = self.jugador
        pts = j.ganar_puntos(e.puntos)
        j.eliminados[e.tipo] += 1
        if j.sumar_combo():
            self.eventos.append(("combo", e.centro, j.combo_mult))
        self.eventos.append(("explosion", e.centro, e.tipo))
        self.eventos.append(("puntos", e.centro, pts))
        self._soltar_item(e.item, e.centro)

    def _asteroide_destruido(self, a):
        pts = self.jugador.ganar_puntos(a.puntos)
        self.eventos.append(("explosion", a.centro, "asteroide"))
        self.eventos.append(("puntos", a.centro, pts))

    def _jefe_destruido(self):
        jefe = self.jefe
        pts = self.jugador.ganar_puntos(jefe.puntos)
        self.eventos.append(("jefe_derrotado", jefe.centro, jefe.mini))
        self.eventos.append(("puntos", jefe.centro, pts))
        self.jefe = None
        self.jefe_vencido = True
        self.balas_enemigas = []

    def soltar_items_jefe(self, tipos, centro):
        for k, t in enumerate(tipos):
            self.items.append(Item(t, centro[0] + (k - 1) * 60, centro[1]))

    def _jugador_golpeado(self):
        centro = self.jugador.centro
        resultado = self.jugador.recibir_dano()
        if resultado == "escudo":
            self.eventos.append(("escudo_roto", centro))
        elif resultado == "vida":
            self.eventos.append(("jugador_golpeado", centro))
            # limpiar balas enemigas para dar respiro al reaparecer
            self.balas_enemigas = []
            if self.terminado:
                self.eventos.append(("jugador_destruido", centro))
