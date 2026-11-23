"""Partida: une distribuciones, director y mundos (1 o 2 jugadores)."""
import json
import random
import config
from model.distribuciones import (DistribucionUniforme, DistribucionExponencial,
                                  SelectorTipoExponencial, DistribucionHistorica,
                                  DistribucionBernoulli, DistribucionDiscreta,
                                  imprimir_tablas)
from model.director import DirectorOleadas
from model.mundo import Mundo

DATOS_HISTORICOS_DEFECTO = [2, 3, 1, 2, 4, 3, 2, 2, 3, 1, 4, 2, 3, 3, 2, 5, 2, 3, 1, 2]


def cargar_datos_historicos(ruta=config.HISTORICO_JSON):
    try:
        with open(ruta, encoding="utf-8") as f:
            datos = json.load(f)
        datos = [int(x) for x in datos["enemigos_por_oleada"]]
        if datos and all(x > 0 for x in datos):
            return datos
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return list(DATOS_HISTORICOS_DEFECTO)


class Distribuciones:
    """Todas las distribuciones de una partida (compartidas por ambos jugadores)."""

    def __init__(self, ancho_mundo, alto, semilla=None, consola=config.CONSOLA_TABLAS,
                 dificultad=config.DIFICULTAD_DEFECTO):
        self.rng = random.Random(semilla)
        dif = config.DIFICULTADES[dificultad]
        self.uniforme = DistribucionUniforme(0, ancho_mundo, self.rng, "Uniforme", consola)
        self.llegada = DistribucionExponencial(config.EXP_LLEGADA_MEDIA_BASE, self.rng,
                                               "Exponencial-Llegada", consola)
        self.tipo = SelectorTipoExponencial(config.EXP_TIPO_MEDIA_BASE, config.EXP_TIPO_CORTES,
                                            self.rng, "Exponencial-Tipo", consola)
        self.historica = DistribucionHistorica(cargar_datos_historicos(), self.rng,
                                               "Historica-Oleada", consola)
        self.drop = DistribucionBernoulli(min(0.9, config.BERNOULLI_DROP_P * dif["drop"]), self.rng,
                                          "Bernoulli-Item", ("NO SUELTA", "SUELTA"), consola)
        self.kamikaze = DistribucionBernoulli(config.BERNOULLI_KAMIKAZE_P, self.rng,
                                              "Bernoulli-Kamikaze", ("SIN", "CON"), consola)
        ids = list(config.ITEMS)
        self.item = DistribucionDiscreta(ids, [config.ITEMS[i]["prob"] for i in ids], self.rng,
                                         "Discreta-Item", consola)
        if consola:
            imprimir_tablas(self.tipo, self.historica, self.llegada, self.uniforme, self.drop, self.item)


class Partida:
    def __init__(self, nombres, ancho=config.ANCHO, alto=config.ALTO, semilla=None,
                 consola=config.CONSOLA_TABLAS, skins=None, dificultad=config.DIFICULTAD_DEFECTO):
        self.modo = len(nombres)
        self.ancho_mundo = ancho // self.modo
        self.alto = alto
        self.dificultad = dificultad
        self.dif = config.DIFICULTADES[dificultad]
        self.dist = Distribuciones(self.ancho_mundo, alto, semilla, consola, dificultad)
        self.director = DirectorOleadas(self.ancho_mundo, self.dist, dificultad)
        skins = skins or [config.SKIN_DEFECTO] * self.modo
        self.mundos = [Mundo(n, self.ancho_mundo, alto, s, dificultad) for n, s in zip(nombres, skins)]
        self.nivel = 1
        self.subio_nivel = False
        self.tiempo = 0.0
        # jefes
        self.minijefe_hecho = False
        self.minijefe_derrotado = False
        self.jefe_activo = False       # un jefe (mini o final) está en pantalla
        self.jefe_es_mini = False
        self.jefe_derrotado = False    # se venció al jefe final (juego ganado)
        self.esperando_decision = False  # mostrar "¿seguir jugando?"
        self.modo_infinito = False     # se eligió seguir jugando
        self.finalizada = False        # el jugador eligió terminar
        self.t_victoria = 0.0
        self._items_jefe = None
        self._items_entregados = set()

    # ---- nivel ----
    def calcular_nivel(self):
        """Nivel = 1 + puntos // 250 (en 2P se toma el mejor puntaje,
        así ambos enfrentan las mismas oleadas)."""
        mejor = max(m.jugador.puntos for m in self.mundos)
        nivel = 1 + mejor // config.PUNTOS_POR_NIVEL
        if not self.minijefe_derrotado:
            nivel = min(nivel, config.NIVEL_MINIJEFE)
        if not self.modo_infinito:  # no se pasa del nivel 10 hasta elegir seguir jugando
            nivel = min(nivel, config.NIVEL_JEFE)
        return nivel

    def puntos_siguiente_nivel(self, puntos):
        """(avance, total) hacia el siguiente nivel para la barra del HUD."""
        return puntos % config.PUNTOS_POR_NIVEL, config.PUNTOS_POR_NIVEL

    @property
    def mult_velocidad(self):
        base = min(config.VEL_MULT_MAX, 1 + config.VEL_EXTRA_POR_NIVEL * (self.nivel - 1))
        return base * self.dif["vel"]

    @property
    def terminada(self):
        return self.finalizada or all(m.terminado for m in self.mundos)

    def actualizar(self, dt, controles):
        """controles: lista (por jugador) de tuplas (dx, dy, disparar[, bomba])."""
        self.subio_nivel = False
        for m in self.mundos:   # los eventos son solo de este cuadro
            m.eventos = []
        if self.terminada or self.esperando_decision:
            return
        self.tiempo += dt

        nuevo = self.calcular_nivel()
        if nuevo > self.nivel:
            for m in self.mundos:  # logro "intocable": nivel completo sin daño
                if not m.terminado and not m.jugador.danado_en_nivel:
                    m.jugador.nivel_sin_dano = True
                m.jugador.danado_en_nivel = False
            self.nivel = nuevo
            self.director.set_nivel(nuevo)
            self.subio_nivel = True

        # durante un jefe no salen oleadas normales (los asteroides sí)
        oleadas = not self.jefe_activo and not self.victoria_pendiente
        specs, asteroides = self.director.actualizar(dt, oleadas)
        for m in self.mundos:
            if not m.terminado:
                if specs:
                    m.recibir_oleada(specs, self.mult_velocidad)
                if asteroides:
                    m.recibir_asteroides(asteroides, self.dif["vel"])

        for m, ctrl in zip(self.mundos, controles):
            dx, dy, disp = ctrl[:3]
            bomba = ctrl[3] if len(ctrl) > 3 else False
            m.actualizar(dt, dx, dy, disp, bomba)

        self._logica_jefe(dt)

    # ---- jefes ----
    @property
    def victoria_pendiente(self):
        return self.t_victoria > 0

    def _aparecer_jefe(self, vivos, mini):
        self.jefe_activo = True
        self.jefe_es_mini = mini
        self._items_jefe = None
        self._items_entregados = set()
        for m in vivos:
            m.aparecer_jefe(mini)

    def _logica_jefe(self, dt):
        vivos = [m for m in self.mundos if not m.terminado]
        if not vivos:
            return
        # ítems de recompensa: los mismos para ambos jugadores
        if self.jefe_activo:
            for i, m in enumerate(self.mundos):
                if m.jefe_vencido and i not in self._items_entregados:
                    if self._items_jefe is None:
                        self._items_jefe = self.director.oleada_jefe_drop()
                    m.soltar_items_jefe(self._items_jefe, (m.ancho / 2, 200))
                    self._items_entregados.add(i)

        if (self.nivel >= config.NIVEL_MINIJEFE and not self.minijefe_hecho):
            self.minijefe_hecho = True
            self._aparecer_jefe(vivos, mini=True)
        elif (self.nivel >= config.NIVEL_JEFE and not self.jefe_activo
              and not self.jefe_derrotado):
            self._aparecer_jefe(vivos, mini=False)
        elif self.jefe_activo and all(m.jefe_vencido for m in vivos):
            self.jefe_activo = False
            if self.jefe_es_mini:
                self.minijefe_derrotado = True
                self.director.t_siguiente = 3.0
            else:
                # todos los jugadores vivos vencieron al jefe final: ¡juego ganado!
                self.jefe_derrotado = True
                self.t_victoria = 2.5  # deja ver la explosión antes de preguntar
        elif self.victoria_pendiente:
            self.t_victoria -= dt
            if self.t_victoria <= 0:
                self.t_victoria = 0
                self.esperando_decision = True

    def seguir_jugando(self):
        """Después del jefe: el juego continúa y la dificultad sigue subiendo."""
        self.esperando_decision = False
        self.modo_infinito = True
        self.director.infinito = True
        self.nivel = self.calcular_nivel()
        self.director.set_nivel(self.nivel)
        self.director.t_siguiente = 2.0

    def terminar(self):
        self.esperando_decision = False
        self.finalizada = True

    # ---- resultados ----
    def resultados(self):
        return [{"nombre": m.jugador.nombre, "puntos": m.jugador.puntos,
                 "eliminados": dict(m.jugador.eliminados)} for m in self.mundos]

    def indice_ganador(self):
        """None si es 1 jugador, -1 si hay empate, o el índice (0/1) del ganador."""
        if self.modo == 1:
            return None
        a, b = (m.jugador.puntos for m in self.mundos)
        if a == b:
            return -1
        return 0 if a > b else 1
