"""Distribuciones de probabilidad usadas por el juego.

- DistribucionUniforme   -> posiciones aleatorias y LÍMITES de la pantalla (a, b)
- DistribucionExponencial -> tiempo entre oleadas
- SelectorTipoExponencial -> tipo de enemigo (fácil / medio / difícil)
- DistribucionHistorica   -> enemigos por oleada (transformada inversa)
- DistribucionBernoulli   -> ¿el enemigo suelta ítem? / ¿la oleada trae kamikazes?
- DistribucionDiscreta    -> qué ítem cae (porcentajes + transformada inversa)

Todas guardan un registro de cada número generado (ri y xi) para la
pantalla de Estadísticas y, opcionalmente, lo imprimen en consola.
"""
import math
from collections import deque

MAX_REGISTRO = 300


class _Registro:
    """Guarda las últimas filas generadas y las imprime en consola."""

    def __init__(self, nombre, rng, consola=False):
        self.nombre = nombre
        self.rng = rng
        self.consola = consola
        self.filas = deque(maxlen=MAX_REGISTRO)
        self.total = 0

    def _registrar(self, fila):
        self.total += 1
        fila = {"n": self.total, **fila}
        self.filas.append(fila)
        if self.consola:
            partes = []
            for k, v in fila.items():
                partes.append(f"{k}={v:.4f}" if isinstance(v, float) else f"{k}={v}")
            print(f"[{self.nombre}] " + " | ".join(partes))
        return fila


class DistribucionUniforme(_Registro):
    """x = a + (b - a) * ri.

    Además de generar, define el intervalo válido [a, b] que se usa como
    criterio de límites: nada puede quedar fuera de [a, b].
    """

    def __init__(self, a, b, rng, nombre="Uniforme", consola=False):
        super().__init__(nombre, rng, consola)
        self.set_limites(a, b)

    def set_limites(self, a, b):
        if a > b:
            a, b = b, a
        self.a, self.b = float(a), float(b)

    def generar(self, a=None, b=None):
        a = self.a if a is None else float(a)
        b = self.b if b is None else float(b)
        ri = self.rng.random()
        xi = a + (b - a) * ri
        self._registrar({"ri": ri, "a": a, "b": b, "xi": xi})
        return xi

    # ---- criterio de límites ----
    def limitar(self, valor):
        """Regresa el valor recortado al intervalo [a, b]."""
        return min(max(valor, self.a), self.b)

    def dentro(self, valor):
        return self.a <= valor <= self.b

    def media_teorica(self):
        return (self.a + self.b) / 2


class DistribucionExponencial(_Registro):
    """x = -media * ln(1 - ri)."""

    def __init__(self, media, rng, nombre="Exponencial", consola=False):
        super().__init__(nombre, rng, consola)
        self.media = float(media)

    def transformar(self, ri):
        return -self.media * math.log(1 - ri)

    def generar(self):
        ri = self.rng.random()
        x = self.transformar(ri)
        self._registrar({"ri": ri, "media": self.media, "x": x})
        return x

    def promedio_simulado(self):
        if not self.filas:
            return 0.0
        return sum(f["x"] for f in self.filas) / len(self.filas)


class SelectorTipoExponencial(_Registro):
    """Elige el tipo de enemigo con una exponencial.

    t = -media * ln(1 - ri)
    t <  c1        -> facil     P = 1 - e^(-c1/media)
    c1 <= t < c2   -> medio     P = e^(-c1/media) - e^(-c2/media)
    t >= c2        -> dificil   P = e^(-c2/media)
    """

    TIPOS = ("facil", "medio", "dificil")

    def __init__(self, media, cortes, rng, nombre="Exponencial-Tipo", consola=False):
        super().__init__(nombre, rng, consola)
        self.media = float(media)
        self.c1, self.c2 = cortes
        self.conteo = {t: 0 for t in self.TIPOS}

    def set_media(self, media):
        self.media = float(media)

    def probabilidades(self):
        e1 = math.exp(-self.c1 / self.media)
        e2 = math.exp(-self.c2 / self.media)
        return {"facil": 1 - e1, "medio": e1 - e2, "dificil": e2}

    def tabla_limites(self):
        """Filas: tipo, rango de t, p(x), P acumulada, lim inf, lim sup (en ri)."""
        p = self.probabilidades()
        filas, acum = [], 0.0
        rangos = {
            "facil": f"[0, {self.c1:g})",
            "medio": f"[{self.c1:g}, {self.c2:g})",
            "dificil": f"[{self.c2:g}, inf)",
        }
        for t in self.TIPOS:
            inf = acum
            acum += p[t]
            filas.append({"tipo": t, "rango_t": rangos[t], "p": p[t],
                          "P": acum, "lim_inf": inf, "lim_sup": acum})
        return filas

    def elegir(self):
        ri = self.rng.random()
        t = -self.media * math.log(1 - ri)
        if t < self.c1:
            tipo = "facil"
        elif t < self.c2:
            tipo = "medio"
        else:
            tipo = "dificil"
        self.conteo[tipo] += 1
        self._registrar({"ri": ri, "media": self.media, "t": t, "tipo": tipo})
        return tipo

    def porcentajes_simulados(self):
        total = sum(self.conteo.values())
        if total == 0:
            return {t: 0.0 for t in self.TIPOS}
        return {t: self.conteo[t] / total for t in self.TIPOS}


class DistribucionHistorica(_Registro):
    """Transformada inversa a partir de datos históricos.

    Construye p(x), P(x), lim inf y lim sup igual que el script de demanda,
    y busca en qué intervalo cae cada ri.
    """

    def __init__(self, datos, rng, nombre="Historica", consola=False):
        super().__init__(nombre, rng, consola)
        if not datos:
            raise ValueError("Se necesitan datos históricos")
        self.datos = list(datos)
        self.valores = sorted(set(self.datos))
        self.p, self.P, self.lim_inf, self.lim_sup = [], [], [], []
        total = len(self.datos)
        acum = 0.0
        for x in self.valores:
            px = self.datos.count(x) / total
            self.lim_inf.append(acum)
            acum += px
            self.p.append(px)
            self.P.append(acum)
            self.lim_sup.append(acum)
        self.lim_sup[-1] = 1.0  # evitar huecos por redondeo
        self.conteo = {x: 0 for x in self.valores}

    def tabla_limites(self):
        return [{"x": x, "p": p, "P": P, "lim_inf": li, "lim_sup": ls}
                for x, p, P, li, ls in zip(self.valores, self.p, self.P,
                                           self.lim_inf, self.lim_sup)]

    def transformar(self, ri):
        for i, x in enumerate(self.valores):
            if self.lim_inf[i] <= ri < self.lim_sup[i]:
                return x
        return self.valores[-1]

    def generar(self):
        ri = self.rng.random()
        x = self.transformar(ri)
        self.conteo[x] += 1
        self._registrar({"ri": ri, "x": x})
        return x

    def media_teorica(self):
        return sum(x * p for x, p in zip(self.valores, self.p))


class DistribucionBernoulli(_Registro):
    """X = 1 (éxito) con probabilidad p, X = 0 con probabilidad 1 - p.

    Criterio: ri < 1 - p  -> 0      ri >= 1 - p -> 1   (igual que bernoulli.py)
    """

    def __init__(self, p, rng, nombre="Bernoulli", etiquetas=("NO", "SI"), consola=False):
        super().__init__(nombre, rng, consola)
        self.etiquetas = etiquetas
        self.set_p(p)
        self.exitos = 0

    def set_p(self, p):
        self.p = min(1.0, max(0.0, float(p)))

    def tabla_limites(self):
        p0 = 1 - self.p
        return [{"x": 0, "estado": self.etiquetas[0], "p": p0, "P": p0, "lim_inf": 0.0, "lim_sup": p0},
                {"x": 1, "estado": self.etiquetas[1], "p": self.p, "P": 1.0, "lim_inf": p0, "lim_sup": 1.0}]

    def generar(self):
        ri = self.rng.random()
        x = 0 if ri < 1 - self.p else 1
        self.exitos += x
        self._registrar({"ri": ri, "p": self.p, "x": x, "evento": self.etiquetas[x]})
        return x

    def porcentaje_simulado(self):
        return self.exitos / self.total if self.total else 0.0


class DistribucionDiscreta(_Registro):
    """Transformada inversa con probabilidades dadas (en %), como la
    selección de tipo de taco: se acumulan y se busca el intervalo de ri."""

    def __init__(self, valores, porcentajes, rng, nombre="Discreta", consola=False):
        super().__init__(nombre, rng, consola)
        total = float(sum(porcentajes))
        self.valores = list(valores)
        self.p = [x / total for x in porcentajes]
        self.lim_inf, self.lim_sup = [], []
        acum = 0.0
        for px in self.p:
            self.lim_inf.append(acum)
            acum += px
            self.lim_sup.append(acum)
        self.lim_sup[-1] = 1.0
        self.conteo = {v: 0 for v in self.valores}

    def tabla_limites(self):
        return [{"x": v, "p": p, "P": ls, "lim_inf": li, "lim_sup": ls}
                for v, p, li, ls in zip(self.valores, self.p, self.lim_inf, self.lim_sup)]

    def generar(self):
        ri = self.rng.random()
        x = self.valores[-1]
        for v, li, ls in zip(self.valores, self.lim_inf, self.lim_sup):
            if li <= ri < ls:
                x = v
                break
        self.conteo[x] += 1
        self._registrar({"ri": ri, "x": x})
        return x


def imprimir_tablas(dist_tipo, dist_hist, dist_llegada, dist_uniforme, dist_drop=None, dist_item=None):
    """Imprime en consola las tablas de límites (al iniciar una partida)."""
    print("\n=========== SPACE WARS - DISTRIBUCIONES ===========")
    print(f"\n--- Uniforme (límites de la pantalla) a={dist_uniforme.a:.0f} b={dist_uniforme.b:.0f}")
    print("x = a + (b - a) * ri")

    print(f"\n--- Exponencial: tipo de enemigo (media={dist_tipo.media:.2f})")
    print(f"{'Tipo':<8} | {'Rango t':<11} | {'p(x)':<7} | {'P(x)':<7} | {'lim inf':<7} | lim sup")
    for f in dist_tipo.tabla_limites():
        print(f"{f['tipo']:<8} | {f['rango_t']:<11} | {f['p']:<7.4f} | {f['P']:<7.4f} | "
              f"{f['lim_inf']:<7.4f} | {f['lim_sup']:.4f}")

    print(f"\n--- Exponencial: tiempo entre oleadas (media={dist_llegada.media:.2f} s)")
    print("t = -media * ln(1 - ri)")

    print("\n--- Histórica: enemigos por oleada (transformada inversa)")
    print(f"Datos: {dist_hist.datos}")
    print(f"{'X':<4} | {'p(x)':<7} | {'P(x)':<7} | {'lim inf':<7} | lim sup")
    for f in dist_hist.tabla_limites():
        print(f"{f['x']:<4} | {f['p']:<7.4f} | {f['P']:<7.4f} | {f['lim_inf']:<7.4f} | {f['lim_sup']:.4f}")
    if dist_drop is not None:
        print(f"\n--- Bernoulli: ¿el enemigo suelta ítem? (p={dist_drop.p:.2f})")
        print(f"{'Estado':<10} | {'X':<3} | {'p(x)':<7} | {'P(x)':<7} | {'lim inf':<7} | lim sup")
        for f in dist_drop.tabla_limites():
            print(f"{f['estado']:<10} | {f['x']:<3} | {f['p']:<7.4f} | {f['P']:<7.4f} | "
                  f"{f['lim_inf']:<7.4f} | {f['lim_sup']:.4f}")
    if dist_item is not None:
        print("\n--- Discreta (transformada inversa): ¿qué ítem cae?")
        print(f"{'Ítem':<8} | {'p(x)':<7} | {'lim inf':<7} | lim sup")
        for f in dist_item.tabla_limites():
            print(f"{f['x']:<8} | {f['p']:<7.4f} | {f['lim_inf']:<7.4f} | {f['lim_sup']:.4f}")
    print("===================================================\n")
