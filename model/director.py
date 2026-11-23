"""Director de oleadas: decide CUÁNDO, CUÁNTOS, QUÉ TIPO, DÓNDE y QUÉ ÍTEM.

- Cuándo:        exponencial (tiempo entre oleadas)
- Cuántos:       histórica / transformada inversa (+ extra por nivel)
- Qué tipo:      exponencial con cortes (fácil / medio / difícil)
- Dónde:         uniforme x = a + (b - a) * ri dentro de los límites de la pantalla
- ¿Suelta ítem?: Bernoulli(p)
- ¿Cuál ítem?:   discreta con porcentajes (transformada inversa)
- ¿Kamikazes?:   Bernoulli por oleada (desde el nivel 2)
- Asteroides:    tiempo entre asteroides uniforme en [6, 12] s

Hay UN solo director por partida; en 2 jugadores reparte lo mismo a los
dos mundos para que nadie tenga ventaja.
"""
import config
from model.entidades import EnemigoSpec, AsteroideSpec


class DirectorOleadas:
    def __init__(self, ancho_mundo, dist, dificultad=config.DIFICULTAD_DEFECTO):
        self.ancho = ancho_mundo
        self.dist = dist
        self.dif = config.DIFICULTADES[dificultad]
        self.nivel = 1
        self.oleadas = 0
        self.t_siguiente = 2.0      # primera oleada a los 2 s
        self.t_asteroide = self.dist.uniforme.generar(*config.ASTEROIDE_INTERVALO)
        self.infinito = False       # True al seguir jugando después del jefe
        self.set_nivel(1)

    def set_nivel(self, nivel):
        self.nivel = nivel
        extra = nivel - 1
        self.dist.tipo.set_media(config.EXP_TIPO_MEDIA_BASE + config.EXP_TIPO_MEDIA_POR_NIVEL * extra)
        minimo = config.EXP_LLEGADA_MEDIA_MIN_INFINITO if self.infinito else config.EXP_LLEGADA_MEDIA_MIN
        media = max(minimo, config.EXP_LLEGADA_MEDIA_BASE - config.EXP_LLEGADA_MEDIA_POR_NIVEL * extra)
        self.dist.llegada.media = media * self.dif["llegada"]
        p_k = min(config.BERNOULLI_KAMIKAZE_P_MAX,
                  config.BERNOULLI_KAMIKAZE_P + config.BERNOULLI_KAMIKAZE_P_POR_NIVEL * max(0, nivel - 2))
        self.dist.kamikaze.set_p(p_k)

    def actualizar(self, dt, oleadas=True):
        """Regresa (lista de EnemigoSpec, lista de AsteroideSpec)."""
        specs, asteroides = [], []
        if oleadas:
            self.t_siguiente -= dt
            if self.t_siguiente <= 0:
                self.t_siguiente = max(config.EXP_LLEGADA_MIN_SEG, self.dist.llegada.generar())
                specs = self.generar_oleada()
        self.t_asteroide -= dt
        if self.t_asteroide <= 0:
            self.t_asteroide = self.dist.uniforme.generar(*config.ASTEROIDE_INTERVALO)
            asteroides = [self.generar_asteroide()]
        return specs, asteroides

    def _item(self):
        """Bernoulli decide si suelta ítem; la discreta decide cuál."""
        if self.dist.drop.generar() == 1:
            return self.dist.item.generar()
        return None

    def generar_oleada(self):
        d = self.dist
        self.oleadas += 1
        cantidad = d.historica.generar() + (self.nivel - 1) // config.NIVELES_POR_ENEMIGO_EXTRA
        cantidad = min(cantidad, config.MAX_ENEMIGOS_OLEADA)
        specs = []
        for i in range(cantidad):
            tipo = d.tipo.elegir()
            specs.append(self._spec(tipo, i * 0.35))
        # kamikazes (Bernoulli por oleada)
        if self.nivel >= config.KAMIKAZE_NIVEL_MIN and d.kamikaze.generar() == 1:
            n = 1 if d.uniforme.generar(0, 1) < 0.6 else 2
            for k in range(n):
                specs.append(self._spec("kamikaze", cantidad * 0.35 + 0.4 + k * 0.5))
        return specs

    def _spec(self, tipo, retraso):
        d = self.dist
        w = config.TIPOS_ENEMIGO[tipo]["tam"][0]
        drift = config.TIPOS_ENEMIGO[tipo]["drift"]
        # posición: uniforme dentro de [0, ancho - w]  (nunca fuera de pantalla)
        x = d.uniforme.generar(0, self.ancho - w)
        vx = d.uniforme.generar(-drift, drift) if drift else 0.0
        fase = d.uniforme.generar(0, 1)
        return EnemigoSpec(tipo, x, vx, retraso=retraso, fase_disparo=fase, item=self._item())

    def generar_asteroide(self):
        d = self.dist
        r = d.uniforme.generar(0, 1)
        tam = "chico" if r < 0.45 else ("mediano" if r < 0.8 else "grande")
        w = config.ASTEROIDES[tam]["tam"][0]
        x = d.uniforme.generar(0, self.ancho - w)
        vel = d.uniforme.generar(*config.ASTEROIDE_VEL)
        vx = d.uniforme.generar(-30, 30)
        giro = d.uniforme.generar(-90, 90)
        return AsteroideSpec(tam, x, vel, vx, giro)

    def oleada_jefe_drop(self):
        """Ítems garantizados al vencer a un jefe (iguales para ambos jugadores)."""
        return [self.dist.item.generar() for _ in range(3)]
