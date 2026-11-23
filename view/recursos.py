"""Carga de imágenes y fuentes."""
import os
import pygame
import config


def _cargar(nombre, tam=None):
    ruta = os.path.join(config.ASSETS_DIR, nombre)
    img = pygame.image.load(ruta).convert_alpha()
    if tam:
        img = pygame.transform.smoothscale(img, tam)
    return img


def _escalar_ancho(img, ancho):
    alto = round(img.get_height() * ancho / img.get_width())
    return pygame.transform.smoothscale(img, (ancho, alto))


class Recursos:
    def __init__(self):
        jw, jh = config.JUGADOR_TAM
        # skins del avión principal
        self.skins, self.iconos_vida, self.skins_vitrina = {}, {}, {}
        for sid, _, archivo in config.SKINS:
            base = _cargar(archivo)
            self.skins[sid] = pygame.transform.smoothscale(base, (jw, jh))
            self.iconos_vida[sid] = pygame.transform.smoothscale(base, (22, 30))
            self.skins_vitrina[sid] = pygame.transform.smoothscale(base, (110, 151))
        # jefe final
        self.jefe = _cargar("boss.png", config.JEFE["tam"])
        self.jefe_golpe = self._silueta(self.jefe)
        self.jefe_vitrina = _escalar_ancho(_cargar("boss.png"), 260)
        # mini-jefe: el crucero pesado en grande
        self.minijefe = _cargar("enemy_hard.png", config.MINIJEFE["tam"])
        self.minijefe_golpe = self._silueta(self.minijefe)
        self.enemigos = {
            "kamikaze": self._tenir(_cargar("enemy_easy.png", config.TIPOS_ENEMIGO["kamikaze"]["tam"])),
            "facil": _cargar("enemy_easy.png", config.TIPOS_ENEMIGO["facil"]["tam"]),
            "medio": _cargar("enemy_medium.png", config.TIPOS_ENEMIGO["medio"]["tam"]),
            "dificil": _cargar("enemy_hard.png", config.TIPOS_ENEMIGO["dificil"]["tam"]),
        }
        # versiones blancas para el destello al recibir un impacto
        self.enemigos_golpe = {k: self._silueta(v) for k, v in self.enemigos.items()}

        # vitrina para menús (más grandes)
        self.vitrina = {
            "facil": _escalar_ancho(_cargar("enemy_easy.png"), 80),
            "medio": _escalar_ancho(_cargar("enemy_medium.png"), 120),
            "dificil": _escalar_ancho(_cargar("enemy_hard.png"), 100),
            "kamikaze": self._tenir(_escalar_ancho(_cargar("enemy_easy.png"), 70)),
        }

        # decoración del fondo
        self.planeta = _escalar_ancho(_cargar("planet_ringed.png"), 420)
        self.luna = _escalar_ancho(_cargar("moon.png"), 200)
        self.nebulosa = _escalar_ancho(_cargar("nebula.png"), 700)
        self.galaxia = _escalar_ancho(_cargar("galaxy.png"), 300)
        archivos_ast = ["asteroid_big.png", "asteroid_med.png", "asteroid_small.png"]
        self.asteroides = {t: _cargar(archivos_ast[d["img"]], d["tam"]) for t, d in config.ASTEROIDES.items()}
        self.asteroides_golpe = {t: self._silueta(v) for t, v in self.asteroides.items()}
        self.asteroide_vitrina = _escalar_ancho(_cargar("asteroid_big.png"), 60)

        # imagen de fondo opcional (tu bg.jpeg anterior, si existe)
        self.bg = None
        for nombre in ("bg.jpeg", "bg.jpg", "bg.png"):
            ruta = os.path.join(config.ASSETS_DIR, nombre)
            if os.path.exists(ruta):
                self.bg = pygame.image.load(ruta).convert()
                break

        # fuentes
        self.f_titulo = pygame.font.Font(None, 120)
        self.f_grande = pygame.font.Font(None, 72)
        self.f_media = pygame.font.Font(None, 44)
        self.f_normal = pygame.font.Font(None, 32)
        self.f_chica = pygame.font.Font(None, 24)
        mono = "consolas,dejavusansmono,couriernew,liberationmono,monospace"
        self.f_mono = pygame.font.SysFont(mono, 17)
        self.f_mono_b = pygame.font.SysFont(mono, 17, bold=True)

        # íconos de ítems (cápsulas dibujadas por código)
        self.items = {t: self._icono_item(d, config.ITEM_TAM[0]) for t, d in config.ITEMS.items()}
        self.items_hud = {t: self._icono_item(d, 26) for t, d in config.ITEMS.items()}
        self.items_grandes = {t: self._icono_item(d, 44) for t, d in config.ITEMS.items()}

    def _icono_item(self, datos, tam):
        s = pygame.Surface((tam, tam), pygame.SRCALPHA)
        c = datos["color"]
        r = tam // 2
        pygame.draw.circle(s, (*c, 90), (r, r), r)
        pygame.draw.circle(s, (20, 16, 40, 255), (r, r), r - 3)
        pygame.draw.circle(s, c, (r, r), r - 3, 2)
        fuente = pygame.font.Font(None, int(tam * (0.62 if len(datos["letra"]) > 1 else 0.8)))
        txt = fuente.render(datos["letra"], True, (255, 255, 255))
        s.blit(txt, txt.get_rect(center=(r, r + 1)))
        return s

    @staticmethod
    def _tenir(img):
        """Versión rojiza del explorador para el kamikaze."""
        img = img.copy()
        img.fill((255, 120, 100), special_flags=pygame.BLEND_RGB_MULT)
        img.fill((70, 0, 0), special_flags=pygame.BLEND_RGB_ADD)
        return img

    @staticmethod
    def _silueta(img):
        blanco = img.copy()
        blanco.fill((255, 255, 255), special_flags=pygame.BLEND_RGB_MAX)
        return blanco
