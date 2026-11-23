"""Preferencias del usuario (skins, volumen, dificultad) guardadas en JSON."""
import json
import os
import config

IDS_SKINS = [s[0] for s in config.SKINS]


class RepositorioPreferencias:
    def __init__(self, ruta=config.PREFERENCIAS_JSON):
        self.ruta = ruta
        self.skins = [config.SKIN_DEFECTO, "glaciar"]
        self.vol_musica = 0.6
        self.vol_efectos = 0.8
        self.mute = False
        self.dificultad = config.DIFICULTAD_DEFECTO
        self.cargar()

    def cargar(self):
        try:
            with open(self.ruta, encoding="utf-8") as f:
                datos = json.load(f)
            skins = datos.get("skins", [])
            for i, s in enumerate(skins[:2]):
                if s in IDS_SKINS:
                    self.skins[i] = s
            self.vol_musica = min(1.0, max(0.0, float(datos.get("vol_musica", self.vol_musica))))
            self.vol_efectos = min(1.0, max(0.0, float(datos.get("vol_efectos", self.vol_efectos))))
            self.mute = bool(datos.get("mute", False))
            if datos.get("dificultad") in config.DIFICULTADES:
                self.dificultad = datos["dificultad"]
        except (OSError, ValueError, AttributeError, TypeError):
            pass

    def guardar(self):
        os.makedirs(os.path.dirname(self.ruta), exist_ok=True)
        with open(self.ruta, "w", encoding="utf-8") as f:
            json.dump({"skins": self.skins, "vol_musica": round(self.vol_musica, 2),
                       "vol_efectos": round(self.vol_efectos, 2), "mute": self.mute,
                       "dificultad": self.dificultad}, f, ensure_ascii=False, indent=2)

    def set_skin(self, jugador, skin_id):
        if skin_id in IDS_SKINS:
            self.skins[jugador] = skin_id
            self.guardar()
