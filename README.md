# Space Wars 🚀

Juego arcade de batalla de naves en 2D hecho con **pygame**, con estructura **MVC** y
generación de enemigos mediante **distribuciones de probabilidad**.

## Cómo ejecutar

```bash
pip install pygame
python main.py
```

La música y los efectos ya vienen en `assets/sonidos/`. Si quieres regenerarlos o cambiar las
melodías: `pip install numpy` y `python herramientas/generar_audio.py`. Para usar tu propia
música, pon `musica_menu.ogg` / `musica_juego.ogg` / `musica_jefe.ogg` (o .mp3) en esa carpeta.

## Controles

| Modo | Movimiento | Disparo | Pausa |
|------|-----------|---------|-------|
| 1 jugador | WASD o flechas | Espacio | P / Esc |
| 2 jugadores · J1 (izquierda) | WASD | Espacio | P / Esc |
| 2 jugadores · J2 (derecha) | Flechas | Enter (o Ctrl der.) | P / Esc |

Bomba: **B** (1P) · **E** (J1) · **Shift derecho** (J2). En pausa, **Q** regresa al menú.
**M** silencia el audio en cualquier pantalla (menos al escribir tu nombre).

## Estructura (MVC)

```
space_wars/
├── main.py                  # punto de entrada
├── config.py                # constantes y parámetros de las distribuciones
├── model/                   # MODELO: lógica pura, sin pygame
│   ├── distribuciones.py    # Uniforme, Exponencial, Selector exponencial, Histórica
│   ├── director.py          # decide cuándo / cuántos / qué tipo / dónde salen enemigos
│   ├── entidades.py         # Jugador, Enemigo, Bala, EnemigoSpec
│   ├── mundo.py             # un mundo por jugador (colisiones, puntos, vidas)
│   ├── partida.py           # une todo: 1P o 2P, niveles, ganador
│   ├── puntajes.py          # historial en JSON
│   ├── preferencias.py      # skins, volumen y dificultad (JSON)
│   └── logros.py            # logros y estadísticas acumuladas (JSON)
├── view/                    # VISTA: solo dibuja
│   ├── recursos.py          # carga de sprites, íconos de ítems y fuentes
│   ├── audio.py             # música y efectos (silencio si no hay audio)
│   ├── fondo.py             # fondo parallax (planetas, nebulosa, asteroides, estrellas)
│   ├── vista_juego.py       # partida, HUD, explosiones, pantalla dividida
│   ├── pantallas.py         # bienvenida, menú, dificultad, nombre, skins, cómo jugar,
│   │                        # logros, opciones, game over, historial, estadísticas
│   └── ui.py                # textos, botones, paneles
├── controller/              # CONTROLADOR: eventos y flujo entre pantallas
│   ├── app.py               # ciclo principal
│   └── estados.py           # un estado por pantalla
├── assets/                  # sprites (PNG) y sonidos/ (WAV)
├── herramientas/
│   └── generar_audio.py     # genera la música chiptune y los efectos
└── data/
    ├── puntajes.json        # historial de partidas (se llena solo)
    ├── preferencias.json    # skins, volumen, dificultad (se crea solo)
    ├── logros.json          # logros desbloqueados (se crea solo)
    └── historico_oleadas.json  # datos históricos editables
```

## Dónde se usa cada distribución

| Distribución | Fórmula | Uso en el juego |
|---|---|---|
| **Uniforme** | `x = a + (b − a)·ri` | Posición X donde aparece cada enemigo, su deriva lateral y la fase de disparo. Sus límites `[a, b]` son el criterio que impide que el avión y los enemigos salgan de la pantalla. |
| **Exponencial (tipo)** | `t = −media·ln(1 − ri)` | Tipo de enemigo: `t < 1` → fácil, `1 ≤ t < 2` → medio, `t ≥ 2` → difícil. La media sube con el nivel, así salen más difíciles. |
| **Exponencial (llegadas)** | `t = −media·ln(1 − ri)` | Segundos entre oleadas. La media baja con el nivel. |
| **Histórica (transformada inversa)** | `p(x)`, `P(x)`, lim inf / lim sup | Cuántos enemigos trae cada oleada, a partir de `data/historico_oleadas.json`. Se suma 1 cada 2 niveles. |
| **Bernoulli** | `X = 1 si ri ≥ 1 − p` | ¿El enemigo suelta ítem? (p = 0.16, cambia con la dificultad) y ¿la oleada trae kamikazes? (desde nivel 2, p sube con el nivel). |
| **Discreta (transformada inversa)** | porcentajes → lim inf / lim sup | Qué ítem cae (los % de cada ítem están en `config.py`). |

Los asteroides usan la uniforme para su posición, velocidad y el tiempo entre uno y otro (6–12 s).

Las tablas (ri, xi, límites) se imprimen en **consola** y también se ven en la pantalla
**ESTADÍSTICAS** del menú. Para desactivar la consola: `CONSOLA_TABLAS = False` en `config.py`.

## Reglas

- Fácil = 10 pts · Medio = 15 pts · Difícil = 20 pts
- Cada 250 pts sube el nivel (se muestra en el HUD con una barra de avance y un aviso grande):
  las oleadas salen más seguido, los enemigos van más rápido y cada 2 niveles traen uno más.
  El nivel 1 es lento a propósito (~4.5 s entre oleadas).
- **Nivel 10: JEFE FINAL.** Dejan de salir oleadas y aparece el jefe (140 de vida, 2 fases de
  ataque). Vencerlo da 300 pts y **ganas el juego**: puedes **terminar** o **seguir jugando**; si
  sigues, los niveles continúan y las naves enemigas aparecen cada vez más rápido.
- **Skins:** 7 diseños para el avión, se eligen en el menú SKINS (uno por jugador) y se guardan.
- **Nivel 5: MINI-JEFE** (crucero gigante). Hay que vencerlo para seguir subiendo de nivel.
- **Ítems:** disparo doble, triple, láser, misiles teledirigidos, disparo rápido, puntos x2 / x3,
  escudo, vida extra, bomba, imán y tiempo lento. Los enemigos que llevan uno parpadean con un
  punto del color del ítem. Al recibir daño pierdes el arma especial. Los jefes sueltan 3 ítems.
- **Combos:** matar seguido sin recibir daño multiplica los puntos (x1.5 → x3); se combina con x2/x3.
- **Kamikazes** (12 pts) se lanzan contra tu nave; **asteroides** (3–8 pts) te dañan si chocas.
- **Dificultad:** Fácil (5 vidas, más lento, más ítems), Normal, Difícil.
- **Logros:** 14 logros guardados entre partidas; aparece un aviso al desbloquear uno.
- **Opciones:** volumen de música y efectos por separado, y silencio.
- 3 vidas; después, Game Over
- **2 jugadores:** pantalla dividida, las naves no se cruzan y ambos reciben **exactamente las
  mismas oleadas** (mismo tipo, posición y momento). La partida termina cuando los dos pierden
  sus 3 vidas y gana el de más puntos. El nivel se basa en el mejor puntaje para que las oleadas
  sigan siendo idénticas.
- El fondo usa `assets/bg.jpeg` con planetas, nebulosa, galaxia, asteroides y estrellas encima.
