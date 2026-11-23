"""Genera la música chiptune y los efectos de sonido del juego (WAV).

Uso:  python herramientas/generar_audio.py
Requiere numpy. Los archivos quedan en assets/sonidos/.
Puedes reemplazar cualquier .wav por tu propio archivo con el mismo nombre
(para la música también sirve .ogg o .mp3 con el mismo nombre).
"""
import os
import wave
import numpy as np

SR = 22050
SALIDA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "sonidos")
rng = np.random.default_rng(7)


# ------------------------------------------------------------ utilidades
def freq(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def t_de(dur):
    return np.arange(int(SR * dur)) / SR


def cuadrada(f, dur, duty=0.5):
    t = t_de(dur)
    fase = (t * f) % 1.0
    return np.where(fase < duty, 1.0, -1.0)


def triangulo(f, dur):
    t = t_de(dur)
    fase = (t * f) % 1.0
    return 4 * np.abs(fase - 0.5) - 1


def ruido(dur):
    return rng.uniform(-1, 1, int(SR * dur))


def envolvente(n, ataque=0.005, caida=0.1, sostener=0.6, soltar=0.05, dur=None):
    """ADSR sencillo sobre n muestras."""
    env = np.ones(n) * sostener
    a = min(n, int(ataque * SR))
    d = min(n - a, int(caida * SR))
    r = min(n, int(soltar * SR))
    if a:
        env[:a] = np.linspace(0, 1, a)
    if d:
        env[a:a + d] = np.linspace(1, sostener, d)
    if r:
        env[n - r:] *= np.linspace(1, 0, r)
    return env


def decaer(n, k=8.0):
    return np.exp(-np.linspace(0, k, n))


def barrido(f0, f1, dur, forma="cuadrada", duty=0.5):
    t = t_de(dur)
    f = np.geomspace(max(f0, 1), max(f1, 1), len(t))
    fase = np.cumsum(f) / SR % 1.0
    if forma == "seno":
        return np.sin(2 * np.pi * fase)
    if forma == "triangulo":
        return 4 * np.abs(fase - 0.5) - 1
    return np.where(fase < duty, 1.0, -1.0)


def pasa_bajos(x, k=0.15):
    y = np.zeros_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc += k * (v - acc)
        y[i] = acc
    return y


def guardar(nombre, x, vol=0.8):
    x = np.asarray(x, dtype=np.float64)
    pico = np.max(np.abs(x)) or 1.0
    x = x / pico * vol
    datos = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    os.makedirs(SALIDA, exist_ok=True)
    with wave.open(os.path.join(SALIDA, nombre + ".wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(datos.tobytes())


def concat(*partes):
    return np.concatenate(partes)


# ------------------------------------------------------------ música
ACORDES = {"m": (0, 3, 7), "M": (0, 4, 7)}


def cancion(bpm, progresion, compases_por_acorde, estilo, repeticiones=2):
    """progresion: lista de (raiz_midi, 'm'|'M'). Devuelve un loop."""
    paso = 60 / bpm / 4                     # semicorchea
    pasos_compas = 16
    total_pasos = len(progresion) * compases_por_acorde * pasos_compas * repeticiones
    n_paso = int(SR * paso)
    pista = np.zeros(total_pasos * n_paso + SR)
    mel_rng = np.random.default_rng(estilo["semilla"])

    def poner(i_paso, sonido, vol):
        ini = i_paso * n_paso
        fin = min(len(pista), ini + len(sonido))
        pista[ini:fin] += sonido[:fin - ini] * vol

    # melodía: motivos de 2 compases que se repiten con variación
    motivos = []
    for _ in range(4):
        motivo = []
        for s in range(32):
            if s % estilo["densidad"] == 0 or mel_rng.random() < 0.15:
                motivo.append(int(mel_rng.integers(0, 6)))
            else:
                motivo.append(None)
        motivos.append(motivo)

    paso_global = 0
    for rep in range(repeticiones):
        for ia, (raiz, cal) in enumerate(progresion):
            tonos = [raiz + i for i in ACORDES[cal]]
            escala_acorde = tonos + [t + 12 for t in tonos]
            for compas in range(compases_por_acorde):
                motivo = motivos[(ia + rep) % len(motivos)]
                for s in range(pasos_compas):
                    i = paso_global + s
                    pos = compas * 16 + s
                    # bajo
                    if s % estilo["bajo_cada"] == 0:
                        nota = raiz - 12 if (s // estilo["bajo_cada"]) % 2 == 0 else raiz - 5
                        snd = triangulo(freq(nota), paso * estilo["bajo_cada"] * 0.95)
                        poner(i, snd * envolvente(len(snd), caida=0.05, sostener=0.8), 0.55)
                    # arpegio
                    if estilo["arpegio"]:
                        nota = escala_acorde[s % len(escala_acorde)] + 12
                        snd = cuadrada(freq(nota), paso * 0.9, duty=0.125)
                        poner(i, snd * envolvente(len(snd), caida=0.04, sostener=0.3), 0.10)
                    # melodía
                    m = motivo[pos % 32]
                    if m is not None:
                        nota = escala_acorde[m] + 12 + estilo["octava"]
                        dur = paso * estilo["densidad"] * 0.9
                        snd = cuadrada(freq(nota), dur, duty=0.25)
                        vib = 1 + 0.004 * np.sin(2 * np.pi * 6 * t_de(dur))
                        snd = cuadrada(freq(nota) * 1.0, dur, duty=0.25) * vib
                        poner(i, snd * envolvente(len(snd), caida=0.08, sostener=0.5, soltar=0.03), 0.22)
                    # batería
                    if estilo["bateria"]:
                        if s % 8 == 0:
                            k = barrido(150, 40, 0.12, "seno") * decaer(int(0.12 * SR), 6)
                            poner(i, k, 0.7)
                        if s % 8 == 4:
                            sn = ruido(0.1) * decaer(int(0.1 * SR), 7)
                            poner(i, sn, 0.30)
                        if s % 2 == 0:
                            hh = np.diff(ruido(0.031), prepend=0) * decaer(int(0.031 * SR), 9)
                            poner(i, hh, 0.12)
                paso_global += pasos_compas
    return pista[:total_pasos * n_paso]


def musica():
    menu = cancion(108, [(57, "m"), (53, "M"), (48, "M"), (55, "M")], 2,
                   {"semilla": 3, "densidad": 4, "bajo_cada": 8, "arpegio": True,
                    "octava": 0, "bateria": False})
    guardar("musica_menu", menu, 0.7)
    juego = cancion(140, [(52, "m"), (48, "M"), (55, "M"), (50, "M")], 2,
                    {"semilla": 11, "densidad": 2, "bajo_cada": 2, "arpegio": True,
                     "octava": 0, "bateria": True})
    guardar("musica_juego", juego, 0.7)
    jefe = cancion(165, [(50, "m"), (46, "M"), (43, "m"), (45, "M")], 2,
                   {"semilla": 23, "densidad": 2, "bajo_cada": 1, "arpegio": True,
                    "octava": 0, "bateria": True})
    guardar("musica_jefe", jefe, 0.75)


# ------------------------------------------------------------ efectos
def efectos():
    guardar("disparo", barrido(1400, 500, 0.08, duty=0.25) * decaer(int(0.08 * SR), 4), 0.35)
    guardar("misil", ruido(0.25) * decaer(int(0.25 * SR), 5) * 0.5
            + barrido(300, 900, 0.25, "triangulo") * 0.3, 0.4)
    # zumbido del láser (se usa en loop)
    t = t_de(0.5)
    laser = (np.sin(2 * np.pi * 220 * t) + 0.5 * cuadrada(440, 0.5, 0.3) * (0.6 + 0.4 * np.sin(2 * np.pi * 30 * t)))
    guardar("laser", laser, 0.3)
    exp = pasa_bajos(ruido(0.45), 0.25) * decaer(int(0.45 * SR), 5)
    guardar("explosion", exp + barrido(120, 30, 0.45, "seno") * decaer(int(0.45 * SR), 6) * 0.6, 0.6)
    expg = pasa_bajos(ruido(1.2), 0.12) * decaer(int(1.2 * SR), 4)
    guardar("explosion_grande", expg + barrido(90, 25, 1.2, "seno") * decaer(int(1.2 * SR), 3), 0.85)
    golpe = barrido(300, 60, 0.3, duty=0.5) * decaer(int(0.3 * SR), 5) + ruido(0.3) * decaer(int(0.3 * SR), 9) * 0.5
    guardar("golpe", golpe, 0.7)
    guardar("escudo_roto", barrido(2000, 300, 0.35, "triangulo") * decaer(int(0.35 * SR), 4)
            + ruido(0.35) * decaer(int(0.35 * SR), 10) * 0.3, 0.55)
    notas = [72, 76, 79, 84]
    item = concat(*[cuadrada(freq(n), 0.05, 0.25) * decaer(int(0.05 * SR), 2) for n in notas])
    guardar("item", item, 0.45)
    vida = concat(*[cuadrada(freq(n), 0.08, 0.5) * decaer(int(0.08 * SR), 1.5) for n in (72, 76, 79, 84, 88)])
    guardar("vida", vida, 0.5)
    bomba = pasa_bajos(ruido(1.6), 0.08) * decaer(int(1.6 * SR), 3) + barrido(60, 20, 1.6, "seno") * decaer(int(1.6 * SR), 2)
    guardar("bomba", concat(barrido(200, 1800, 0.25, "triangulo") * 0.4, bomba), 0.9)
    fanfarria = concat(*[cuadrada(freq(n), d, 0.25) * envolvente(int(d * SR), caida=0.05, sostener=0.7)
                         for n, d in ((67, 0.1), (72, 0.1), (76, 0.1), (79, 0.35))])
    guardar("nivel", fanfarria, 0.5)
    sirena = concat(*[barrido(500, 900, 0.3, duty=0.5) if i % 2 == 0 else barrido(900, 500, 0.3, duty=0.5)
                      for i in range(6)])
    guardar("alerta", sirena * 0.6, 0.5)
    guardar("combo", concat(cuadrada(freq(84), 0.05, 0.25), cuadrada(freq(91), 0.09, 0.25)) , 0.35)
    campana = sum(np.sin(2 * np.pi * freq(n) * t_de(0.9)) * decaer(int(0.9 * SR), 4) for n in (84, 88, 91))
    guardar("logro", concat(cuadrada(freq(79), 0.08, 0.25) * 0.5, campana), 0.5)
    guardar("menu_mover", cuadrada(freq(84), 0.03, 0.5) * decaer(int(0.03 * SR), 3), 0.25)
    guardar("menu_ok", concat(cuadrada(freq(79), 0.05, 0.25), cuadrada(freq(86), 0.09, 0.25)), 0.35)
    caida = concat(*[cuadrada(freq(n), 0.22, 0.5) * envolvente(int(0.22 * SR), caida=0.1, sostener=0.6)
                     for n in (67, 63, 60, 55)])
    guardar("game_over", caida, 0.5)
    victoria = concat(*[cuadrada(freq(n), d, 0.25) * envolvente(int(d * SR), caida=0.05, sostener=0.7)
                        for n, d in ((72, 0.12), (72, 0.12), (72, 0.12), (79, 0.4), (77, 0.12), (79, 0.12),
                                     (84, 0.7))])
    guardar("victoria", victoria, 0.55)


if __name__ == "__main__":
    musica()
    efectos()
    print("Audio generado en", SALIDA)
    for f in sorted(os.listdir(SALIDA)):
        print("  ", f, os.path.getsize(os.path.join(SALIDA, f)) // 1024, "KB")
