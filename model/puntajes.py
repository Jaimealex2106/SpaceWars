"""Historial de puntajes guardado en JSON."""
import json
import os
from datetime import datetime
import config


class RepositorioPuntajes:
    def __init__(self, ruta=config.PUNTAJES_JSON):
        self.ruta = ruta

    def cargar(self):
        try:
            with open(self.ruta, encoding="utf-8") as f:
                datos = json.load(f)
            return datos if isinstance(datos, list) else []
        except (OSError, ValueError):
            return []

    def _guardar(self, registros):
        os.makedirs(os.path.dirname(self.ruta), exist_ok=True)
        tmp = self.ruta + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(registros, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.ruta)

    def guardar_partida(self, partida):
        """Agrega un registro por jugador de la partida terminada."""
        registros = self.cargar()
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
        resultados = partida.resultados()
        ganador = partida.indice_ganador()
        for i, r in enumerate(resultados):
            reg = {
                "nombre": r["nombre"],
                "puntos": r["puntos"],
                "nivel": 1 + r["puntos"] // config.PUNTOS_POR_NIVEL,
                "modo": "1P" if partida.modo == 1 else "2P",
                "eliminados": r["eliminados"],
                "jefe_derrotado": partida.jefe_derrotado,
                "dificultad": partida.dificultad,
                "fecha": fecha,
            }
            if partida.modo == 2:
                rival = resultados[1 - i]
                reg["rival"] = rival["nombre"]
                reg["puntos_rival"] = rival["puntos"]
                if ganador == -1:
                    reg["resultado"] = "empate"
                else:
                    reg["resultado"] = "gano" if ganador == i else "perdio"
            registros.append(reg)
        self._guardar(registros)
        return registros

    def mejores(self, n=10):
        return sorted(self.cargar(), key=lambda r: r.get("puntos", 0), reverse=True)[:n]

    def recientes(self, n=10):
        return list(reversed(self.cargar()))[:n]
