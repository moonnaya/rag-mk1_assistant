# MK1 v3.100 — Notas técnicas

Lo que no hace falta saber para hacer un güego con MK1 v3.100, pero sí para
tocar el motor, el compilador de scripts o las herramientas. El manual de uso
es [`manual.md`](manual.md).

## Índice

1. [`config_derived.h`](#1-config_derivedh)
2. [Probar el motor](#2-probar-el-motor)
3. [msc4 por dentro](#3-msc4-por-dentro)
4. [Las utilidades de Windows](#4-las-utilidades-de-windows)
5. [Compilar con SDCC](#5-compilar-con-sdcc)

---

## 1. `config_derived.h`

`config.h` dice qué quiere el güego; `config_derived.h` traduce eso a lo que
necesita el motor. En lugar de repetir por todo el código condiciones como

```c
#if defined PLAYER_KILLS_ENEMIES || defined PLAYER_CAN_FIRE
```

se calculan una vez, con un nombre que dice qué necesita el motor
(`ENEMIES_CAN_DIE`) y no qué combinación de opciones lo provoca. Se incluye
justo después de `config.h`, y el usuario no tiene que tocarlo nunca.

| Bandera | Qué quiere decir |
|---|---|
| `HAS_AY_MUSIC`, `HAS_BEEPER` | Música y efectos con el WYZ player (128K, CPC) o con el beeper (48K). |
| `GAME_FRAME_TICKS` | Si `config.h` no lo pone, 2 (25 fps). |
| `JUMP_ON_FIRE`, `JUMP_ON_UP`, `JUMP_ON_KEY` | Qué tecla salta: FIRE sin disparo; ARRIBA con disparo; una tecla aparte con dos botones. |
| `REFILL_LIFE_ON_LEVEL` | El jugador recupera la vida al empezar cada nivel. |
| `SLOW_DRAIN_ON` | El jugador rebota y el daño es 4 veces más lento. |
| `CHECK_LOCKS_OR_BOXES`, `CHECK_LOCKS_OR_BOXES_VERT` | Al chocar con algo se mira si es un cerrojo o una caja (también en vertical). |
| `PUSH_BOXES_VERT` | Las cajas se empujan también en vertical (vista cenital). |
| `ENEMIES_CAN_DIE`, `SHOW_KILLS` | Los enemigos pueden morir; se cuentan en el marcador. |
| `NEEDS_INIT_MALOTES` | Hay que reiniciar los enemigos (muertos y vida) al empezar. |
| `PLAYER_STEPS_ON_ENEMIES` | Pisar enemigos hace algo (matarlos o rebotar). |
| `ENEMS_HAVE_FREE_COORDS` | Hay enemigos con coordenadas propias (fanties, tipo 6). |
| `FORCE_ENEMS_LIFE`, `MALOTE_HAS_LIFE` | La estructura de los enemigos lleva su vida (siempre con niveles; tiene que coincidir con lo que escribe `ene2h`). |
| `NEEDS_EXPLOSION_SPRITE`, `NEEDS_BULLET_SPRITE` | Hacen falta los sprites extra de la explosión y la bala. |
| `MAX_BULLETS`, `BULLETS_MOVE_VERT` | Las balas: cuántas (1 si no se dice) y si se mueven en vertical. |
| `NEEDS_CLEAR_GAMEAREA`, `NEEDS_REDRAW_SCR` | Hacen falta `clear_gamearea_tiles ()` o `redraw_scr ()`. |
| `SHOW_OBJECT_ICON`, `SHOW_TIMER` | Partes opcionales del marcador. |
| `FIRE_ZONE`, `PUSHED_SCRIPTING`, `MSC_SHOW_ITEM`, `MSC_SCRIPTS_AS_RESOURCES` | Lo que activan los scripts (salen de `msc-config.h`): la zona de fuego, la sección `TILE PUSHED`, el objeto del marcador y los scripts como recursos de nivel. |
| `SG_NFLAGS` | Cuántos flags guarda una partida guardada. |

También comprueba que el mapa no tenga más de 85 pantallas (los índices de
enemigos son de un byte: 85 * 3 = 255).

---

## 2. Probar el motor

En `tests/` hay herramientas para probar el motor sin un emulador con
pantalla. Los scripts tienen versión `.sh` (Linux) y `.bat` (Windows); los
emuladores (`zxrun.c`, `cpcrun.c`) se compilan con gcc.

| Herramienta | Qué hace |
|---|---|
| `tests/zxrun/zxrun juego.bin [-128 -page n RAMn.bin ...] -f frames -k teclas -s frames -o prefijo` | Emulador de ZX 48K/128K (con las librerías chips): ejecuta N frames pulsando teclas (`-k "130:1+,134:1-"`: tecla abajo en el frame 130, arriba en el 134) y guarda capturas png. Además: `-d dir,len` vuelca memoria, `-h` hash de pantalla, `-rt` detecta saltos a la ROM, `-prof` perfil, `-count` y `-incl` cuentan ciclos de una rutina. |
| `tests/cpcrun/cpcrun juego.sna ...` | Lo mismo para CPC (`-pc` y `-low` para depurar cuelgues). |
| `tests/build zx\|cpc salida.bin [DEF[=valor]] [-UNDEF] [@script.spt]` | Compila en una copia limpia de `src/` cambiando directivas de `config.h`. |
| `tests/matrix [zx\|cpc\|all] [filtro]` | Compila unas cien configuraciones distintas del motor. |
| `tests/bench [etiqueta]` | Mide ciclos por frame y por pintado de pantalla. |
| `tests/levels/run [nivel]` | La prueba de niveles (`SCRIPTED=1` con scripts). |
| `tests/script/` | Scripts de prueba del intérprete (`script.spt` con su `extern.h`, `full.spt` con todo). |
| `msc4/tests/matrix msc4 salida` | Pasa msc4 por los scripts de los juegos de MK1 v3.2 con varias opciones (regresión del compilador). |

En Windows:

* En `cmd` un `=` parte los argumentos de `call`, y `&` y los paréntesis son
  especiales: un valor con `&` o paréntesis va entre comillas
  (`"DEATH_COUNT_EXPRESSION=20+(rand()&15)"`). `build.bat` pasa su línea de
  comandos entera a `tests\defs.ps1`, que hace los cambios en `config.h`
  (PowerShell).
* Las configuraciones de `matrix.bat` son las líneas `::CFG nombre|defines`
  del final del archivo; usan `$FIRE`, `$SIDE_JUMP`, `$TOP`, `$TEXT`,
  `$SCRIPT` y `$REPO` como `matrix.sh` usa sus variables.
* `tests\levels\run.bat` necesita Python 3 (`crop.py`) y lee `SCRIPTED` del
  entorno (`set SCRIPTED=1`).
* `msc4\tests\matrix.bat` toma los juegos de MK1 v3.2 de la variable
  `MK1V32_GAMES`.

---

## 3. msc4 por dentro

msc4 es el mismo compilador para MK1 v3.2 (con `v=3`, genera un intérprete en
ensamblador a partir de `msc4/targets/z80.tpl` o `gb.tpl`) y para MK1 v3.100
(con `v=3_100 output=c`, genera `msc-config.h` para el intérprete en C de
`src/dev/msc.h`). El lenguaje es el mismo.

### Trampas del lenguaje

Son *por diseño* (o al menos, así funciona el lenguaje). Son las cosas que te
van a morder primero.

1. **Una letra detrás de `$` no es un nombre.** `$F` *no* es "el flag F": el
   compilador ahora lo rechaza, pero el comportamiento histórico era evaluar
   `Val("F")`, que vale `0`. Usa dígitos (`$0`, `$15`) o alias
   (`%FLAG_NAME`).

2. **`$%NOMBRE` es una indirección, no un flag.** `ALIAS %G = 3` y luego
   `$%G = 1` pone a 1 el *flag 3*. Es el idioma "dame un puntero" previsto,
   pero es fácil meter la pata.

3. **`PLAYER TOUCHES` es lo mismo que `PLAYER AT`.** Ninguno de los dos
   significa "cualquier píxel del sprite toca el tile": los dos miran el tile
   del centro del jugador.

4. **`PLAYER IN_X` / `IN_Y` van en píxeles, no en tiles.**

5. **Las minúsculas se pierden en `TEXT BOX` y `DIALOG`.** Escribe en
   mayúsculas.

6. **Las opciones de un diálogo no pueden llevar comas** (son los
   separadores). Los espacios sí valen.

7. **`NOINDEXED` en el script es sólo documental.** No cambia el binario: el
   tamaño del índice lo marca `ROOMS`.

8. **`TEXT` (el que no es caja) necesita `LINE_OF_TEXT`, `LINE_OF_TEXT_X` y
   `LINE_OF_TEXT_ATTR` en `config.h`.**

9. **`BREAK` aborta la sección entera,** no sólo la cláusula actual.

10. **El código inalcanzable tras un terminador se compila igual** (con un
    aviso): son bytes de más que nunca se ejecutan.

11. **El valor de `ROOMS` tiene que ser correcto.** El índice se dimensiona
    con él; las secciones de pantallas mayores que `ROOMS` son un error, y en
    pantallas mayores el motor no ejecuta las secciones de pantalla. Pon las directivas al *principio* del script: el tamaño del
    índice se calcula mientras se lee el script, así que una directiva
    `ROOMS` posterior a un `CALL` daría offsets inconsistentes.

### Errores corregidos en el compilador (hasta la v4.6)

Se listan porque algunos cambian el *significado* de scripts antiguos que
compilaban sin queja estando mal.

| # | Problema | Corrección |
|---|---|---|
| 1 | `PLAYER NOT FALLING` (con espacio) no producía **ningún código**: la condición se descartaba en silencio y la cláusula se ejecutaba como si no existiera. | Ahora se aceptan tanto `NOT_FALLING` como `NOT FALLING`. |
| 2 | `PLAYER FALLING` comprobaba `player.possee` y era cierto cuando valía *distinto de cero*; `PLAYER NOT FALLING` leía el offset 16 (el byte bajo del puntero `current_frame`). | `FALLING` es ahora `vy > 0 && !possee`, `NOT FALLING` es su negación exacta, usando el `vy` completo de 16 bits. |
| 3 | `PARAM = 1` escribía en `flags[$E9]` en lugar de en `script_param`: el handler de lvalue del intérprete se emitía bajo la guarda equivocada. | El handler se emite ahora siempre que `PARAM` se use como lvalue. |
| 4 | Un script que usaba `DIALOG` pero no `TEXT BOX` generaba un intérprete que no ensamblaba (faltaba el helper `read_addr`). | `read_addr` se emite siempre que pueda hacer falta. |
| 5 | `EN_N` leía `_en_it`, un símbolo que no existe en el motor. | Ahora lee `_enit` (la global C `enit`). |
| 6 | Los opcodes de condición `IF TILE AT` / `IF BEH AT` (`$30`/`$31`) eran código muerto: el codificador de expresiones los reescribía siempre. | Se han eliminado los opcodes muertos; `TILE AT` / `BEH AT` son expresiones, y nada más. |
| 7 | `IF TRUE` se codificaba como opcode `$F0` **sin handler**; funcionaba sólo porque los opcodes desconocidos caen por la rama de "no hacer nada". | `$F0` tiene ahora un handler de verdad. |
| 8 | Un comando o una condición desconocidos se **ignoraban en silencio**: el compilador no emitía nada y no decía nada. | Ahora se informa de cada comando y cada condición desconocida, con el número de línea. |
| 9 | `SET TILE (x, y), 7` (coma en vez de `=`) ponía silenciosamente el tile **0**. | Ahora el `=` es obligatorio; si falta, es un error de sintaxis. |
| 10 | Una referencia a flag inválida como `$F` se convertía silenciosamente en el flag 0. | Ahora es un error. |
| 11 | `END IF` se rechazaba con "Unexpected command" y abortaba el análisis de la sección. | `END IF` se acepta como sinónimo de `END`. |
| 12 | Un script con errores seguía produciendo un `.bin` y un intérprete. | El compilador ahora informa de todos los errores, se niega a escribir el `.bin`, se niega a escribir el intérprete y sale con un estado distinto de cero. |

Dos cosas más se han cambiado por claridad, sin alterar el comportamiento de
los scripts correctos:

* El comando `TEXT` (el que no es caja) sigue soportado (es legacy, pero
  funciona).
* `PLAYER GOT SOMETHING` es el nombre canónico de la sección (el
  `PLAYER GETS COIN` del borrador antiguo de `msc4.md` no existe).

### Corregido o añadido en la v4.7

| # | Problema / novedad | Ahora |
|---|---|---|
| 1 | Un `CALL` a una `SUB` definida más abajo se compilaba con una dirección equivocada, sin aviso. | Las direcciones de los `CALL` se resuelven al final del script. Un `CALL` a una `SUB` inexistente es un error. |
| 2 | Las `SUB` de un script seguían visibles al compilar el siguiente de `in=`. | Cada script empieza con la lista de subrutinas vacía. |
| 3 | Una cláusula de 255 bytes o más se codificaba mal (el tamaño va en un byte y `$FF` marca el fin de sección). | Error. |
| 4 | Una sección `ENTERING SCREEN n` / `PRESS FIRE AT SCREEN n` con `n >= ROOMS` caía fuera del índice. | Error. |
| 5 | `TIMER ZERO`, `TILE PUSHED` y `TILE DESTROYED` no se reconocían. | Se reconocen (índices 6, 7 y 9). |
| 6 | — | Variables `TIMER`, `MOVED_TILE`, `MOVED_X`, `MOVED_Y`; `SET FIRE ZONE [TILES]` (sólo `output=c`). |
| 7 | El intérprete estaba dentro de `msc4.bas`. | Está en plantillas (`msc4/targets/z80.tpl`, `gb.tpl`); `target=gb`, `template=`, `allopcodes`. |
| 8 | — | `v=3_100 output=c`: el intérprete en C de MK1 v3.100. |

### Diferencias con el intérprete de MK1 v3.2

* `PRINT TILE` usa coordenadas de carácter de pantalla (como en v3.2).
* `WARP TO` y escribir `PX`, `PY` colocan al jugador en coma fija 8.8; no hay
  que actualizar nada a mano.
* `RECHARGE` pone `player.life = PLAYER_LIFE`.
* `PAUSE n` espera `n` frames de 1/50 s (en CPC, 6 interrupciones por frame).
* `SHOW` llama a `sp_UpdateNow ()`.
* `HIDE_HOTSPOTS` y `DONT_MAKE_FANTIES` son de cada pantalla (vuelven a 0 al
  entrar).
* En una `SUB`, `WIN GAME`, `GAME OVER` y `RERUN` terminan también la sección
  que la llamó (en v3.2 sólo terminaban la `SUB`).
* No hay modo `jumptable`: el índice tiene siempre `16 + 2 * ROOMS` entradas.

---

## 4. Las utilidades de Windows

Los `.exe` de `src/utils` se usan tal cual. Las utilidades de FreeBASIC (y
msc4) se recompilan con `src/utils/build-windows.bat`, que necesita `fbc`
(FreeBASIC 1.10, 32 bits: `libfbpng.a` es de 32 bits) y deja los `.exe` en
`src/utils`. `pasmo`, `zx0`, `zx7`, `bas2tap`, `bin2tap`, `cpc2cdt`,
`cpctbin2sna` y `ponedor` no se compilan ahí: sus fuentes están en
`src/utils/src` (`ponedor.bas` necesita la librería de interfaz `gui.bas`).

En Linux, `src/utils/build-linux.sh` lo compila todo (también las de C) en
`src/utils/linux` (ver el apéndice A del manual).

---

## 5. Compilar con SDCC

El motor se compila con SDCC 4.4 (el de GBDK-2020 4.3.0): `sdcc`, el
ensamblador `sdasz80`, el enlazador `sdldz80` y el bibliotecario `sdar`. De
GBDK sólo se usan esas herramientas y la librería de C de Z80
(`lib/z80/z80.lib`: `memcpy`, `memset` y las rutinas de multiplicar y
dividir). `comp-zx` y `comp-cpc` buscan GBDK en `GBDK_HOME` (en Windows, por
defecto `C:\gbdk`).

### Los pasos

1. `sdcc -mz80 --no-std-crt0 -I. -c churromain.c`: todo el motor de una vez
   (`churromain.c` incluye el resto). En CPC, además, `-DCPC -DMODE_0`; en
   128K, `--codeseg MAIN --constseg MAIN` (ver más abajo).
2. `sdasz80 -g` de los módulos en ensamblador: el `crt0` de cada máquina y,
   según el caso, la música del título de 48K (`speccy/music.s`, de
   `beepola2s`), o el WYZ player de CPC, sus efectos y los instrumentos
   (`cpc/wyz_player.s`, `cpc/efectos.s`, `instrumentos.s` de
   `wyzTrackerParser`).
3. `sdldz80 -n -m -w -i -b _CODE=dirección`, con la librería gráfica
   (`speccy/splib2.lib` o `cpc/cpcrslib.lib`) y `z80.lib`.
4. `ihx2bin juego.ihx juego.bin dirección juego.map [128k]`: el binario, desde
   la dirección de carga hasta el último byte con datos, y las comprobaciones
   del mapa de memoria (abajo).

### Las áreas y el `crt0`

`crt0.s` pone la pila (`__stack_top`, que define `churromain.c` a partir de
`STACK_ADDR`), borra las variables (`_DATA`, las del motor, y `_BSS`, las de
splib2) y salta a `main`. **No copia variables con valor inicial**: no hay
ninguna (el motor usa tablas `const`, y las que cambian durante la partida
tienen una tabla `const` con su estado inicial que se copia al empezar:
`malotes_ini`, `hotspots_ini`, `cerrojos_ini`).

El orden de las áreas sale del `crt0`:

| Máquina | Orden en memoria |
|---|---|
| ZX 48K (24200) | `_CODE` (código y `const`), `_DATA`, `_BSS` |
| ZX 128K (24200) | `_CODE` (crt0 y librerías), `_DATA`, `_MAIN` (el motor), `_BSS` |
| CPC (0x400) | `_CODE`, `_DATA`, `_BSS` |

En 128K el motor se compila en el área `_MAIN` para que sus variables (entre
ellas el buffer del nivel, `level_data`) queden delante del código y por
debajo de 0xC000, aunque el código pase de esa dirección: lo que se usa con
otra página de RAM puesta tiene que estar por debajo. Las variables ocupan su
sitio en la cinta (ceros).

### Lo que comprueba `ihx2bin`

Con el `.map` (`sdldz80 -w`, nombres completos):

* que `_INITIALIZER` está vacía: si hay una variable global con valor
  inicial, error;
* que el programa y sus variables (`s__HEAP`) acaban antes de `__mem_limit`
  (`MEM_LIMIT`: en ZX, el principio de los bloques de los sprites; en CPC,
  el buffer de la canción, 0x8800);
* en 128K, que `_low_end` (una función vacía que va justo después de los
  gráficos en `churromain.c`) está por debajo de 0xC000: antes van el
  descompresor, la paginación, la ISR, el tileset y los sprites.

### Ensamblador en C

SDCC no admite ensamblador fuera de una función. Los datos y las rutinas en
ensamblador van en funciones `__naked` que no se llaman nunca (`tileset_data`,
`zx0_depack`...), con la sintaxis de `sdasz80`. Las rutinas que se llaman
desde C son `__naked` y acaban en `ret`; con `__sdcccall(1)` (la convención
por defecto) el primer argumento llega en A o HL y se devuelve en A o DE. IX
es el puntero de marco de SDCC: quien lo use lo guarda.

### Las librerías

* **splib2** (`lib/splib2`, `make.sh` o `make.bat`, salida en
  `src/dev/speccy`): los módulos en `.s`; las funciones de C llevan un
  envoltorio con la convención `__smallc` (argumentos en la pila, de
  izquierda a derecha, como en z88dk) que guarda IX en `__sp_ixsave`. Las
  funciones devuelven en L o HL. La memoria de los sprites es la de los
  bloques de splib2 (`SPBlockAlloc`). Ver [`lib-splib2.md`](lib-splib2.md).
* **cpcrslib** (`lib/cpcrslib-mt`, salida en `src/dev/cpc`): `.s`, con
  entradas `__z88dk_fastcall` (el argumento en HL o L) que guardan IX. Ver
  [`lib-cprslib.md`](lib-cprslib.md) y `lib/cpcrslib-mt/README.md`.

### Lo que generan las herramientas

| Herramienta | Salida |
|---|---|
| `mapcnv` | `mapa.h`: `const unsigned char mapa []` y `cerrojos_ini` (const) con su copia `cerrojos` en RAM. |
| `ene2h` | `enems.h`: `malotes_ini` y `hotspots_ini` (const) con sus copias en RAM, y `enoffs_index`. |
| `sprcnv` | `sprites.h`: `sprite_data` (const) y `sprite_N_x` como punteros dentro; o el `.bin`. |
| `msc4 output=c` | `msc-config.h` y `msc-scripts.h` (bytecode y textos, const). |
| `librarian` | `librarian.h`: los `RES_*`, la tabla `resources` (const) y `get_resource`. |
| `beepola2s` | `speccy/music.s` con `play_title_music`. |
| `wyzTrackerParser` | `instrumentos.s` (`TABLA_PAUTAS`, `TABLA_SONIDOS`). |
| `mkts_om mode=pals` | `cpc/pal.h`: `const unsigned char my_inks []`. |
