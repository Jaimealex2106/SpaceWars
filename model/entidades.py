"""Entidades del juego (sin dependencias de pygame)."""
import math
import config


class Entidad:
    HITBOX = 0.75  # porcentaje del sprite que cuenta para colisiones

    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = float(x), float(y), w, h
        self.activo = True

    @property
    def centro(self):
        return (self.x + self.w / 2, self.y + self.h / 2)

    def caja(self):
        mx = self.w * (1 - self.HITBOX) / 2
        my = self.h * (1 - self.HITBOX) / 2
        return (self.x + mx, self.y + my, self.w - 2 * mx, self.h - 2 * my)

    def colisiona(self, otra):
        ax, ay, aw, ah = self.caja()
        bx, by, bw, bh = otra.caja()
        return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah

    def colisiona_franja(self, x0, x1, y_max):
        """¿Toca la franja vertical [x0, x1] por encima de y_max? (láser)"""
        ax, ay, aw, ah = self.caja()
        return ax < x1 and x0 < ax + aw and ay < y_max and ay + ah > 0


# ---------------------------------------------------------------- balas
class Bala(Entidad):
    HITBOX = 1.0

    def __init__(self, x, y, vx, vy, amiga, dano=1):
        w, h = (6, 18) if amiga else (8, 14)
        super().__init__(x - w / 2, y, w, h)
        self.vx, self.vy = vx, vy
        self.amiga = amiga
        self.dano = dano

    def actualizar(self, dt, ancho, alto, objetivos=None):
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.y + self.h < -20 or self.y > alto + 20 or self.x + self.w < -20 or self.x > ancho + 20:
            self.activo = False


class Misil(Bala):
    """Bala que persigue al objetivo más cercano."""

    def __init__(self, x, y, vx):
        super().__init__(x, y, vx, -config.MISIL_VEL * 0.6, amiga=True, dano=2)
        self.w, self.h = 10, 10
        self.vida = 3.0

    @property
    def angulo(self):
        return math.atan2(self.vy, self.vx)

    def actualizar(self, dt, ancho, alto, objetivos=None):
        self.vida -= dt
        if objetivos:
            cx, cy = self.centro
            obj = min(objetivos, key=lambda o: (o.centro[0] - cx) ** 2 + (o.centro[1] - cy) ** 2)
            ox, oy = obj.centro
            deseado = math.atan2(oy - cy, ox - cx)
            actual = self.angulo
            dif = (deseado - actual + math.pi) % math.tau - math.pi
            actual += max(-1, min(1, dif)) * config.MISIL_GIRO * dt
        else:
            actual = self.angulo
        self.vx = math.cos(actual) * config.MISIL_VEL
        self.vy = math.sin(actual) * config.MISIL_VEL
        super().actualizar(dt, ancho, alto)
        if self.vida <= 0:
            self.activo = False


# ---------------------------------------------------------------- jugador
class Jugador(Entidad):
    HITBOX = 0.6

    def __init__(self, nombre, ancho_mundo, alto_mundo, skin=config.SKIN_DEFECTO,
                 vidas=config.VIDAS_INICIALES):
        w, h = config.JUGADOR_TAM
        super().__init__(0, 0, w, h)
        self.nombre = nombre
        self.skin = skin
        self.vidas = vidas
        self.puntos = 0
        self.eliminados = {t: 0 for t in config.TIPOS_ENEMIGO}
        self.cooldown = 0.0
        self.t_misil = 0.0
        self.invulnerable = 0.0
        self.ancho_mundo, self.alto_mundo = ancho_mundo, alto_mundo
        # power-ups
        self.arma = "normal"
        self.timers = {}           # item -> segundos restantes (rápido, x2, x3, imán, lento, arma)
        self.escudo = False
        self.bombas = 0
        # combo y estadísticas (para logros)
        self.combo = 0
        self.max_combo_mult = 1.0
        self.items_recogidos = 0
        self.bombas_usadas = 0
        self.danado_en_nivel = False
        self.nivel_sin_dano = False
        self.reaparecer()

    @property
    def vivo(self):
        return self.vidas > 0

    @property
    def total_eliminados(self):
        return sum(self.eliminados.values())

    def reaparecer(self):
        # El avión se sitúa en medio de su pantalla
        self.x = self.ancho_mundo / 2 - self.w / 2
        self.y = self.alto_mundo / 2 - self.h / 2
        self.invulnerable = config.INVULNERABLE_SEG

    def mover(self, dx, dy, dt, lim_x, lim_y):
        """dx, dy en {-1,0,1}. lim_x / lim_y son DistribucionUniforme con [a, b]."""
        if dx and dy:  # diagonal con la misma rapidez
            dx *= 0.7071
            dy *= 0.7071
        self.x = lim_x.limitar(self.x + dx * config.JUGADOR_VEL * dt)
        self.y = lim_y.limitar(self.y + dy * config.JUGADOR_VEL * dt)

    # ---------- multiplicadores ----------
    @property
    def combo_mult(self):
        mult = 1.0
        for minimo, m in config.COMBO_NIVELES:
            if self.combo >= minimo:
                mult = m
        return mult

    @property
    def mult_items(self):
        if "x3" in self.timers:
            return 3
        if "x2" in self.timers:
            return 2
        return 1

    def ganar_puntos(self, base):
        pts = int(round(base * self.mult_items * self.combo_mult))
        self.puntos += pts
        return pts

    def sumar_combo(self):
        antes = self.combo_mult
        self.combo += 1
        self.max_combo_mult = max(self.max_combo_mult, self.combo_mult)
        return self.combo_mult > antes  # True si subió de multiplicador

    # ---------- power-ups ----------
    def aplicar_item(self, tipo):
        """Aplica el ítem y regresa un texto corto para mostrar."""
        datos = config.ITEMS[tipo]
        self.items_recogidos += 1
        if tipo in config.ARMAS:
            for a in config.ARMAS:
                self.timers.pop(a, None)
            self.arma = tipo
            self.timers[tipo] = datos["dur"]
        elif tipo == "escudo":
            self.escudo = True
        elif tipo == "vida":
            self.vidas = min(config.VIDAS_MAX, self.vidas + 1)
        elif tipo == "bomba":
            self.bombas = min(config.BOMBAS_MAX, self.bombas + 1)
        else:
            if tipo == "x3":
                self.timers.pop("x2", None)
            elif tipo == "x2" and "x3" in self.timers:
                return datos["nombre"]
            self.timers[tipo] = datos["dur"]
        return datos["nombre"]

    def usar_bomba(self):
        if self.bombas > 0 and self.vivo:
            self.bombas -= 1
            self.bombas_usadas += 1
            return True
        return False

    @property
    def lento(self):
        return "lento" in self.timers

    @property
    def iman(self):
        return "iman" in self.timers

    # ---------- disparo ----------
    def puede_disparar(self):
        return self.cooldown <= 0

    def disparar(self):
        cd = config.JUGADOR_COOLDOWN * (0.5 if "rapido" in self.timers else 1.0)
        self.cooldown = cd
        cx = self.x + self.w / 2
        y = self.y - 10
        v = config.BALA_JUGADOR_VEL
        if self.arma == "doble":
            return [Bala(cx - 14, y, 0, -v, True), Bala(cx + 14, y, 0, -v, True)]
        if self.arma == "triple":
            return [Bala(cx, y, 0, -v, True), Bala(cx - 8, y, -v * 0.22, -v, True),
                    Bala(cx + 8, y, v * 0.22, -v, True)]
        if self.arma == "laser":
            return []  # el láser lo maneja el mundo como un rayo continuo
        balas = [Bala(cx, y, 0, -v, True)]
        if self.arma == "misiles" and self.t_misil <= 0:
            self.t_misil = 0.55
            balas += [Misil(self.x + 6, self.y + 30, -260), Misil(self.x + self.w - 6, self.y + 30, 260)]
        return balas

    def recibir_dano(self):
        """Regresa 'escudo', 'vida' o None (si no le pasó nada)."""
        if self.invulnerable > 0 or not self.vivo:
            return None
        self.combo = 0
        self.danado_en_nivel = True
        if self.escudo:
            self.escudo = False
            self.invulnerable = 1.0
            return "escudo"
        self.vidas -= 1
        # al perder vida se pierde el arma especial
        self.arma = "normal"
        for a in config.ARMAS:
            self.timers.pop(a, None)
        if self.vivo:
            self.reaparecer()
        return "vida"

    def actualizar(self, dt):
        self.cooldown = max(0.0, self.cooldown - dt)
        self.t_misil = max(0.0, self.t_misil - dt)
        self.invulnerable = max(0.0, self.invulnerable - dt)
        for k in list(self.timers):
            self.timers[k] -= dt
            if self.timers[k] <= 0:
                del self.timers[k]
                if k == self.arma:
                    self.arma = "normal"


# ---------------------------------------------------------------- ítems
class Item(Entidad):
    HITBOX = 1.2  # un poco más fácil de agarrar

    def __init__(self, tipo, cx, cy):
        w, h = config.ITEM_TAM
        super().__init__(cx - w / 2, cy - h / 2, w, h)
        self.tipo = tipo
        self.t = 0.0

    def actualizar(self, dt, alto, iman_hacia=None):
        self.t += dt
        if iman_hacia is not None:
            tx, ty = iman_hacia
            cx, cy = self.centro
            d = math.hypot(tx - cx, ty - cy) or 1
            vel = 420
            self.x += (tx - cx) / d * vel * dt
            self.y += (ty - cy) / d * vel * dt
        else:
            self.y += config.ITEM_VEL_CAIDA * dt
            self.x += math.sin(self.t * 3) * 25 * dt
        if self.y > alto:
            self.activo = False


# ---------------------------------------------------------------- enemigos
class EnemigoSpec:
    """Descripción de un enemigo generado por el director.

    En 2 jugadores la MISMA spec se entrega a ambos mundos, así los
    enemigos salen en el mismo lugar, tiempo, tipo y con el mismo ítem.
    """

    def __init__(self, tipo, x, vx, retraso, fase_disparo, item=None):
        self.tipo = tipo
        self.x = x
        self.vx = vx
        self.retraso = retraso
        self.fase_disparo = fase_disparo
        self.item = item

    def __repr__(self):
        return f"EnemigoSpec({self.tipo}, x={self.x:.1f}, vx={self.vx:.1f}, item={self.item})"


class Enemigo(Entidad):
    HITBOX = 0.8

    def __init__(self, spec, mult_vel):
        datos = config.TIPOS_ENEMIGO[spec.tipo]
        w, h = datos["tam"]
        super().__init__(spec.x, -h, w, h)
        self.tipo = spec.tipo
        self.item = spec.item
        self.vida = datos["vida"]
        self.vida_max = datos["vida"]
        self.puntos = datos["puntos"]
        self.vel = datos["vel"] * mult_vel
        self.vx = spec.vx * mult_vel
        self.intervalo = datos["intervalo_disparo"] / mult_vel
        self.vel_bala = datos["vel_bala"] * mult_vel
        self.patron = datos["patron"]
        self.t_disparo = spec.fase_disparo * self.intervalo
        self.golpe = 0.0  # destello al recibir impacto (para la vista)
        # kamikaze
        self.picando = False
        self.vel_picada = datos.get("vel_picada", 0) * mult_vel
        self.dir = (0.0, 1.0)

    def actualizar(self, dt, lim_x, alto, objetivo=None):
        self.golpe = max(0.0, self.golpe - dt)
        if self.tipo == "kamikaze":
            self._actualizar_kamikaze(dt, lim_x, alto, objetivo)
            return []
        self.y += self.vel * dt
        self.x += self.vx * dt
        # rebota dentro de los límites [a, b] de la uniforme
        if not lim_x.dentro(self.x):
            self.x = lim_x.limitar(self.x)
            self.vx = -self.vx
        if self.y > alto:
            self.activo = False

        balas = []
        if self.y > 0:  # solo dispara cuando ya está visible
            self.t_disparo += dt
            if self.t_disparo >= self.intervalo:
                self.t_disparo -= self.intervalo
                balas = self._disparar()
        return balas

    def _actualizar_kamikaze(self, dt, lim_x, alto, objetivo):
        if not self.picando:
            self.y += self.vel * dt
            if self.y >= alto * 0.12:
                self.picando = True
                if objetivo:
                    cx, cy = self.centro
                    d = math.hypot(objetivo[0] - cx, objetivo[1] - cy) or 1
                    self.dir = ((objetivo[0] - cx) / d, max(0.35, (objetivo[1] - cy) / d))
                    n = math.hypot(*self.dir)
                    self.dir = (self.dir[0] / n, self.dir[1] / n)
        else:
            self.x += self.dir[0] * self.vel_picada * dt
            self.y += self.dir[1] * self.vel_picada * dt
            self.x = lim_x.limitar(self.x)
        if self.y > alto:
            self.activo = False

    def _disparar(self):
        cx = self.x + self.w / 2
        by = self.y + self.h - 6
        v = self.vel_bala
        if self.patron == "simple":
            return [Bala(cx, by, 0, v, amiga=False)]
        if self.patron == "doble":
            return [Bala(self.x + self.w * 0.25, by, 0, v, amiga=False),
                    Bala(self.x + self.w * 0.75, by, 0, v, amiga=False)]
        if self.patron == "abanico":
            return [Bala(cx, by, -v * 0.3, v, amiga=False),
                    Bala(cx, by, 0, v, amiga=False),
                    Bala(cx, by, v * 0.3, v, amiga=False)]
        return []

    def recibir_dano(self, dano):
        if not self.activo:
            return False
        self.vida -= dano
        self.golpe = 0.08
        if self.vida <= 0:
            self.activo = False
            return True
        return False


# ---------------------------------------------------------------- asteroides
class AsteroideSpec:
    def __init__(self, tam, x, vel, vx, giro):
        self.tam, self.x, self.vel, self.vx, self.giro = tam, x, vel, vx, giro


class Asteroide(Entidad):
    HITBOX = 0.7

    def __init__(self, spec, mult_vel):
        d = config.ASTEROIDES[spec.tam]
        w, h = d["tam"]
        super().__init__(spec.x, -h, w, h)
        self.tam = spec.tam
        self.vida = self.vida_max = d["vida"]
        self.puntos = d["puntos"]
        self.vel = spec.vel * mult_vel
        self.vx = spec.vx
        self.giro = spec.giro
        self.angulo = 0.0
        self.golpe = 0.0

    def actualizar(self, dt, lim_x, alto):
        self.y += self.vel * dt
        self.x += self.vx * dt
        if not lim_x.dentro(self.x):
            self.x = lim_x.limitar(self.x)
            self.vx = -self.vx
        self.angulo = (self.angulo + self.giro * dt) % 360
        self.golpe = max(0.0, self.golpe - dt)
        if self.y > alto:
            self.activo = False

    def recibir_dano(self, dano):
        if not self.activo:
            return False
        self.vida -= dano
        self.golpe = 0.06
        if self.vida <= 0:
            self.activo = False
            return True
        return False


# ---------------------------------------------------------------- jefes
class Jefe(Entidad):
    """Jefe final (nivel 10) o mini-jefe (nivel 5). Sus patrones de disparo
    dependen solo del tiempo, así en 2 jugadores ambos enfrentan el mismo jefe."""
    HITBOX = 0.7

    def __init__(self, ancho_mundo, mini=False, mult_vida=1.0):
        d = config.MINIJEFE if mini else config.JEFE
        self.datos = d
        self.mini = mini
        w, h = d["tam"]
        super().__init__(ancho_mundo / 2 - w / 2, -h, w, h)
        self.vida = self.vida_max = d["vida"] * mult_vida
        self.puntos = d["puntos"]
        self.vx = d["vel_x"]
        self.vel_bala = d["vel_bala"]
        self.entrando = True
        self.t_abanico = 0.0
        self.t_especial = 0.0
        self.golpe = 0.0

    @property
    def fase(self):
        return 1 if self.vida > self.vida_max / 2 else 2

    def actualizar(self, dt, lim_x):
        d = self.datos
        self.golpe = max(0.0, self.golpe - dt)
        if self.entrando:
            self.y += d["vel_entrada"] * dt
            if self.y >= d["y_objetivo"]:
                self.y = d["y_objetivo"]
                self.entrando = False
            return []
        vel = self.vx * (1.5 if self.fase == 2 else 1.0)
        self.x += vel * dt
        if not lim_x.dentro(self.x):
            self.x = lim_x.limitar(self.x)
            self.vx = -self.vx

        balas = []
        self.t_abanico += dt
        self.t_especial += dt
        if self.mini:
            if self.t_abanico >= (1.8 if self.fase == 1 else 1.3):
                self.t_abanico = 0.0
                balas += self._abanico(3 if self.fase == 1 else 5)
            if self.fase == 2 and self.t_especial >= 2.5:
                self.t_especial = 0.0
                balas += self._canones()
            return balas

        int_abanico = 1.4 if self.fase == 1 else 1.0
        if self.t_abanico >= int_abanico:
            self.t_abanico -= int_abanico
            balas += self._abanico(5 if self.fase == 1 else 7)
        int_especial = 2.2 if self.fase == 1 else 2.6
        if self.t_especial >= int_especial:
            self.t_especial -= int_especial
            balas += self._canones() if self.fase == 1 else self._anillo(16)
        return balas

    def _abanico(self, n):
        cx, by = self.x + self.w / 2, self.y + self.h * 0.85
        apertura = math.radians(70)
        balas = []
        for i in range(n):
            ang = math.pi / 2 - apertura / 2 + apertura * i / (n - 1)
            balas.append(Bala(cx, by, math.cos(ang) * self.vel_bala, math.sin(ang) * self.vel_bala, False))
        return balas

    def _canones(self):
        by = self.y + self.h * 0.7
        v = self.vel_bala * 1.3
        return [Bala(self.x + self.w * f, by, 0, v, False) for f in (0.22, 0.32, 0.68, 0.78)]

    def _anillo(self, n):
        cx, cy = self.centro
        return [Bala(cx, cy, math.cos(math.tau * i / n) * self.vel_bala * 0.8,
                     math.sin(math.tau * i / n) * self.vel_bala * 0.8, False) for i in range(n)]

    def recibir_dano(self, dano):
        if self.entrando or not self.activo:
            return False
        self.vida -= dano
        self.golpe = 0.06
        if self.vida <= 0:
            self.activo = False
            return True
        return False
