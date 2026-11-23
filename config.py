"""Configuración global de Space Wars."""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
DATA_DIR = os.path.join(BASE_DIR, "data")
PUNTAJES_JSON = os.path.join(DATA_DIR, "puntajes.json")
PREFERENCIAS_JSON = os.path.join(DATA_DIR, "preferencias.json")
HISTORICO_JSON = os.path.join(DATA_DIR, "historico_oleadas.json")
LOGROS_JSON = os.path.join(DATA_DIR, "logros.json")
SONIDOS_DIR = os.path.join(ASSETS_DIR, "sonidos")

# Pantalla
ANCHO = 1200
ALTO = 800
FPS = 60
TITULO = "Space Wars"

# Reglas del juego
VIDAS_INICIALES = 3
PUNTOS_POR_NIVEL = 250          # cada 250 pts sube el nivel
INVULNERABLE_SEG = 2.0          # tiempo de invulnerabilidad tras recibir daño

# Jugador
JUGADOR_TAM = (64, 88)
JUGADOR_VEL = 380               # px/seg
JUGADOR_COOLDOWN = 0.22         # seg entre disparos
BALA_JUGADOR_VEL = 700

# Tipos de enemigo
TIPOS_ENEMIGO = {
    "facil": {
        "nombre": "Explorador", "tam": (50, 53), "vida": 1, "vel": 100,
        "puntos": 10, "intervalo_disparo": 3.0, "patron": "simple",
        "vel_bala": 240, "drift": 35,
    },
    "medio": {
        "nombre": "Caza", "tam": (84, 67), "vida": 3, "vel": 72,
        "puntos": 15, "intervalo_disparo": 2.4, "patron": "doble",
        "vel_bala": 250, "drift": 55,
    },
    "dificil": {
        "nombre": "Crucero", "tam": (86, 134), "vida": 6, "vel": 48,
        "puntos": 20, "intervalo_disparo": 2.0, "patron": "abanico",
        "vel_bala": 220, "drift": 20,
    },
    # kamikaze: baja y luego se lanza directo contra la nave del jugador
    "kamikaze": {
        "nombre": "Kamikaze", "tam": (44, 47), "vida": 1, "vel": 90,
        "puntos": 12, "intervalo_disparo": 999, "patron": "ninguno",
        "vel_bala": 0, "drift": 0, "vel_picada": 330,
    },
}
ORDEN_TIPOS = ["facil", "medio", "dificil"]

# ---- Parámetros de las distribuciones ----
# Exponencial para el tipo de enemigo: t = -media * ln(1 - ri)
#   t <  CORTE_1            -> fácil
#   CORTE_1 <= t < CORTE_2  -> medio
#   t >= CORTE_2            -> difícil
EXP_TIPO_MEDIA_BASE = 1.0
EXP_TIPO_MEDIA_POR_NIVEL = 0.15     # al subir de nivel aparecen más difíciles
EXP_TIPO_CORTES = (1.0, 2.0)

# Exponencial para el tiempo entre oleadas (seg)
EXP_LLEGADA_MEDIA_BASE = 4.5    # nivel 1: ~4.5 s entre oleadas
EXP_LLEGADA_MEDIA_POR_NIVEL = 0.35
EXP_LLEGADA_MEDIA_MIN = 1.2       # mínimo antes del jefe
EXP_LLEGADA_MEDIA_MIN_INFINITO = 0.7  # mínimo al seguir jugando tras el jefe
EXP_LLEGADA_MIN_SEG = 0.8           # piso para que nunca salgan 2 oleadas encimadas

# Nivel
VEL_EXTRA_POR_NIVEL = 0.15          # +15 % de velocidad enemiga por nivel
VEL_MULT_MAX = 2.4                  # tope de velocidad
NIVELES_POR_ENEMIGO_EXTRA = 2       # +1 enemigo por oleada cada 2 niveles
MAX_ENEMIGOS_OLEADA = 10

# Imprimir tablas de las distribuciones en consola
CONSOLA_TABLAS = True

# ---- Jefe final ----
NIVEL_JEFE = 10
JEFE = {
    "tam": (330, 223), "vida": 140, "puntos": 300,
    "vel_entrada": 60, "y_objetivo": 92, "vel_x": 90,
    "vel_bala": 230,
}

# ---- Skins del avión principal: (id, nombre, archivo) ----
SKINS = [
    ("rojo", "Fénix Rojo", "player.png"),
    ("dorado", "Dorado", "skin_dorado.png"),
    ("glaciar", "Glaciar", "skin_glaciar.png"),
    ("magma", "Magma", "skin_magma.png"),
    ("nebula", "Nébula", "skin_nebula.png"),
    ("neon", "Sombra Neón", "skin_neon.png"),
    ("toxico", "Tóxico", "skin_toxico.png"),
]
SKIN_DEFECTO = "rojo"

# ---- Mini-jefe (nivel 5) ----
NIVEL_MINIJEFE = 5
MINIJEFE = {
    "tam": (140, 217), "vida": 55, "puntos": 120,
    "vel_entrada": 70, "y_objetivo": 70, "vel_x": 120,
    "vel_bala": 220,
}

# ---- Dificultad ----
DIFICULTADES = {
    "facil": {"nombre": "Fácil", "vel": 0.8, "llegada": 1.3, "vidas": 5, "drop": 1.4,
              "desc": "5 vidas, enemigos lentos, más ítems"},
    "normal": {"nombre": "Normal", "vel": 1.0, "llegada": 1.0, "vidas": 3, "drop": 1.0,
               "desc": "La experiencia original"},
    "dificil": {"nombre": "Difícil", "vel": 1.25, "llegada": 0.75, "vidas": 3, "drop": 0.75,
                "desc": "Enemigos rápidos, oleadas seguidas, menos ítems"},
}
DIFICULTAD_DEFECTO = "normal"
VIDAS_MAX = 5

# ---- Ítems / power-ups ----
# ¿El enemigo suelta ítem?  -> Bernoulli(p)
# ¿Cuál ítem?               -> transformada inversa con estos porcentajes (suman 100)
BERNOULLI_DROP_P = 0.16
ITEM_VEL_CAIDA = 95
ITEM_TAM = (34, 34)
ITEMS = {
    "doble":   {"nombre": "Disparo doble", "letra": "2", "color": (255, 200, 60), "prob": 14, "dur": 12,
                "desc": "Dos balas paralelas"},
    "triple":  {"nombre": "Disparo triple", "letra": "3", "color": (255, 140, 40), "prob": 12, "dur": 12,
                "desc": "Tres balas en abanico"},
    "laser":   {"nombre": "Láser", "letra": "L", "color": (255, 60, 120), "prob": 7, "dur": 8,
                "desc": "Rayo que atraviesa todo"},
    "misiles": {"nombre": "Misiles", "letra": "M", "color": (255, 110, 70), "prob": 9, "dur": 12,
                "desc": "Misiles que persiguen enemigos"},
    "rapido":  {"nombre": "Disparo rápido", "letra": "R", "color": (255, 240, 120), "prob": 12, "dur": 10,
                "desc": "Disparas el doble de rápido"},
    "x2":      {"nombre": "Puntos x2", "letra": "x2", "color": (120, 240, 110), "prob": 10, "dur": 10,
                "desc": "Puntos dobles"},
    "x3":      {"nombre": "Puntos x3", "letra": "x3", "color": (60, 255, 200), "prob": 5, "dur": 8,
                "desc": "Puntos triples"},
    "escudo":  {"nombre": "Escudo", "letra": "S", "color": (90, 200, 255), "prob": 10, "dur": 0,
                "desc": "Absorbe un golpe"},
    "vida":    {"nombre": "Vida extra", "letra": "+", "color": (255, 80, 90), "prob": 5, "dur": 0,
                "desc": "+1 vida (máx. 5)"},
    "bomba":   {"nombre": "Bomba", "letra": "B", "color": (200, 110, 255), "prob": 8, "dur": 0,
                "desc": "Limpia la pantalla (tecla bomba)"},
    "iman":    {"nombre": "Imán", "letra": "U", "color": (200, 200, 220), "prob": 4, "dur": 12,
                "desc": "Atrae los ítems hacia ti"},
    "lento":   {"nombre": "Tiempo lento", "letra": "T", "color": (150, 160, 255), "prob": 4, "dur": 7,
                "desc": "Enemigos a media velocidad"},
}
ARMAS = ("doble", "triple", "laser", "misiles")
BOMBAS_MAX = 3
BOMBA_DANO_JEFE = 15
LASER_DPS = 9
MISIL_VEL = 520
MISIL_GIRO = 7.0            # qué tan rápido corrige el rumbo
LENTO_FACTOR = 0.5

# ---- Kamikazes (Bernoulli por oleada, desde el nivel 2) ----
KAMIKAZE_NIVEL_MIN = 2
BERNOULLI_KAMIKAZE_P = 0.25
BERNOULLI_KAMIKAZE_P_POR_NIVEL = 0.05
BERNOULLI_KAMIKAZE_P_MAX = 0.6

# ---- Asteroides obstáculo (aparecen con tiempo uniforme) ----
ASTEROIDES = {
    "grande":  {"tam": (70, 66), "vida": 5, "puntos": 8, "img": 0},
    "mediano": {"tam": (46, 44), "vida": 3, "puntos": 5, "img": 1},
    "chico":   {"tam": (28, 28), "vida": 1, "puntos": 3, "img": 2},
}
ASTEROIDE_INTERVALO = (6.0, 12.0)   # uniforme a..b segundos
ASTEROIDE_VEL = (70.0, 130.0)

# ---- Combos (matar seguido sin recibir daño) ----
COMBO_NIVELES = [(0, 1.0), (5, 1.5), (10, 2.0), (20, 2.5), (35, 3.0)]
