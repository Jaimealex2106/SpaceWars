"""Logros: se revisan durante la partida y se guardan en JSON."""
import json
import os
from datetime import datetime
import config

# id: (nombre, descripción)
LOGROS = {
    "minijefe":      ("Calentamiento", "Derrota al mini-jefe del nivel 5"),
    "primer_jefe":   ("Cazador de jefes", "Derrota al jefe final"),
    "heroe":         ("Héroe", "Derrota al jefe final en Difícil"),
    "kills_100":     ("Centenario", "Destruye 100 enemigos (acumulado)"),
    "kills_500":     ("Leyenda", "Destruye 500 enemigos (acumulado)"),
    "intocable":     ("Intocable", "Completa un nivel sin recibir daño"),
    "combo_x3":      ("Combo maestro", "Alcanza el combo x3"),
    "pts_1000":      ("Mil puntos", "Consigue 1000 pts en una partida"),
    "pts_5000":      ("Cinco mil", "Consigue 5000 pts en una partida"),
    "coleccionista": ("Coleccionista", "Recoge 10 ítems en una partida"),
    "bombardero":    ("Bombardero", "Usa 3 bombas en una partida"),
    "superviviente": ("Superviviente", "Sobrevive 5 minutos en una partida"),
    "mas_alla":      ("Más allá", "Llega al nivel 15"),
    "duo":           ("Trabajo en equipo", "Termina una partida de 2 jugadores"),
}


class RepositorioLogros:
    def __init__(self, ruta=config.LOGROS_JSON):
        self.ruta = ruta
        self.desbloqueados = {}   # id -> fecha
        self.kills_totales = 0
        self.cargar()

    def cargar(self):
        try:
            with open(self.ruta, encoding="utf-8") as f:
                d = json.load(f)
            self.desbloqueados = {k: v for k, v in d.get("desbloqueados", {}).items() if k in LOGROS}
            self.kills_totales = int(d.get("kills_totales", 0))
        except (OSError, ValueError, AttributeError, TypeError):
            pass

    def guardar(self):
        os.makedirs(os.path.dirname(self.ruta), exist_ok=True)
        with open(self.ruta, "w", encoding="utf-8") as f:
            json.dump({"desbloqueados": self.desbloqueados, "kills_totales": self.kills_totales},
                      f, ensure_ascii=False, indent=2)

    def _condiciones(self, partida, terminada):
        jugadores = [m.jugador for m in partida.mundos]
        kills = sum(j.total_eliminados for j in jugadores)
        total = self.kills_totales + (0 if terminada else kills)
        mejor = max(j.puntos for j in jugadores)
        return {
            "minijefe": partida.minijefe_derrotado,
            "primer_jefe": partida.jefe_derrotado,
            "heroe": partida.jefe_derrotado and partida.dificultad == "dificil",
            "kills_100": total >= 100,
            "kills_500": total >= 500,
            "intocable": any(j.nivel_sin_dano for j in jugadores),
            "combo_x3": any(j.max_combo_mult >= 3.0 for j in jugadores),
            "pts_1000": mejor >= 1000,
            "pts_5000": mejor >= 5000,
            "coleccionista": any(j.items_recogidos >= 10 for j in jugadores),
            "bombardero": any(j.bombas_usadas >= 3 for j in jugadores),
            "superviviente": partida.tiempo >= 300,
            "mas_alla": partida.nivel >= 15,
            "duo": terminada and partida.modo == 2,
        }

    def revisar(self, partida, terminada=False):
        """Regresa la lista de ids recién desbloqueados (y los guarda)."""
        nuevos = []
        for lid, ok in self._condiciones(partida, terminada).items():
            if ok and lid not in self.desbloqueados:
                self.desbloqueados[lid] = datetime.now().strftime("%Y-%m-%d")
                nuevos.append(lid)
        if nuevos:
            self.guardar()
        return nuevos

    def cerrar_partida(self, partida):
        """Suma los enemigos de la partida al acumulado y revisa por última vez."""
        self.kills_totales += sum(m.jugador.total_eliminados for m in partida.mundos)
        nuevos = self.revisar(partida, terminada=True)
        self.guardar()
        return nuevos
