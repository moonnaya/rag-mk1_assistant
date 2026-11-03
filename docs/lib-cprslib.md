# cpcrslib-mt en MTE MK1 v3.100 (Amstrad CPC)

Copyleft 2011, 2026 The Mojon Twins

Este documento explica cómo usa el motor la librería **CPCRSLIB "Mojon
Tilemap"** (`cpcrslib-mt`), que está en `lib/cpcrslib-mt/`. Está pensado para
quien vaya a escribir código propio (`dev/custom.h`, `dev/extern.h`) y
necesite saber:

- qué hace la librería y cómo está recortada,
- qué contrato tiene con el motor (qué pone cada lado),
- cómo se dibuja una pantalla, cómo se actualiza y qué son las "celdas
  tocadas",
- cómo son los sprites y en qué unidades van sus coordenadas,
- cómo se leen las teclas,
- qué trampas hay.

> El equivalente para ZX Spectrum es [`lib-splib2.md`](lib-splib2.md). Los
> dos backends son **completamente distintos** por dentro (el ZX usa splib2:
> display list y sprites con máscaras; el CPC usa cpcrslib-mt: nametable,
> superbuffer y celdas sucias), pero el motor les da **los mismos nombres**:
> en CPC también hay un `sp_UpdateNow ()`, un `sp_PrintAtInv ()`, un
> `sp_KeyPressed ()`… escritos con cpcrslib-mt. Así el resto del motor es el
> mismo para las dos máquinas.

Todo el uso de cpcrslib-mt está en `src/dev/cpc/`: `sysvars.h` (direcciones,
teclas, estructura de los sprites), `printer.h` (inicialización, pintado,
sprites, mandos) y `cell_arrays.h` (las tablas de frames). La librería
compilada y su cabecera están en el mismo sitio (`cpcrslib.lib`,
`cpcrslib_fg.lib`, `cpcrslib_mt.h`).

---

## 1. Qué es cpcrslib-mt

`cpcrslib-mt` es una versión **recortada** de la CPCRSLIB original (Raúl
Simarro / Artaburu, 2007), modificada por na_th_an para el modelo del motor:

- **Lo que se ha quitado**: todo lo que no es tilemap ni *dirty cells*. No
  hay gestión de teclado completa (`cpc_AssignKey`, `cpc_ScanKeyboard`...),
  ni impresión, ni gráficos genéricos, ni el gestor de tilemap completo, ni
  actualizadores alternativos de pantalla.
- **Lo que se ha cambiado**: la "lista de tiles tocados" (pares X,Y) se ha
  sustituido por un **bitfield** de 96 bytes (1 bit por celda de 32x24),
  igual que hace splib2 con su `SPDirtyChars`. Los sprites no llevan
  "cabecera": sus datos se ponen en una estructura propia (sección 6).
- **Lo que se ha añadido**: rutinas de sprite que dibujan con una LUT de
  píxeles transparentes (de CPCTelera) y rutinas al píxel.

La lista de módulos está en `lib/cpcrslib-mt/cpcrslib.lst`. Además del
núcleo (`cpc_ShowTileMap`, `cpc_UpdScr`, `cpc_ShowTouchedTiles`,
`cpc_ResetTouchedTiles`, `cpc_UpdTileTable`, `cpc_InvalidateRect`,
`cpc_KeysData`, `cpc_TestKeyboard`, `cpc_TestKey`, `cpc_SetMode`, y las
tablas del tilemap, `cpc_TileMapConf`), hay una
colección de rutinas de sprite de varios tamaños y formatos. El motor usa
sólo dos parejas (sección 6.3); las demás están por si un güego las
necesita.

### 1.1. Las dos variantes

- `cpcrslib.lib`: la variante normal, la que usa el motor.
- `cpcrslib_fg.lib`: la variante **fg** ("foreground"), compilada con
  `PASARPORDETRAS = 1`, que permite que los sprites **pasen por detrás** de
  ciertos tiles del fondo. Necesita que el güego defina una tabla
  `behindtilemasks` (256 bytes, uno por tile: 1 = el sprite queda detrás).
  Se elige al compilar (cambiando `-l cpcrslib.lib` por
  `-l cpcrslib_fg.lib` en `comp-cpc.bat`), no durante el juego.

La configuración con la que se ensambla está en
`lib/cpcrslib-mt/CPCconfig.inc`; `make.bat` la copia con `PASARPORDETRAS`
a 0 o a 1 para cada variante.

### 1.2. Construcción y enlazado

`lib/cpcrslib-mt/make.bat` (o `make.sh`) ensambla los módulos `.s` con
`sdasz80`, hace las dos librerías con `sdar` y las deja, con
`cpcrslib_mt.h`, en `src/dev/cpc`.

`comp-cpc.bat` enlaza así:

```
sdldz80 -n -m -w -i -b _CODE=0x400 %game%.ihx crt0.rel churromain.rel wyz_player.rel efectos.rel instrumentos.rel -k cpc -l cpcrslib.lib -k %GBDK_HOME%\lib\z80 -l z80.lib
```

y `cpc/sysvars.h` incluye la cabecera:

```c
#include "cpcrslib_mt.h"
```

#### Cómo se llama desde C

Las funciones que reciben un argumento lo toman en HL (o L, si es de 8 bits):
están declaradas `__z88dk_fastcall`. `cpc_TestKey` devuelve en L
(`__sdcccall(0)`). Cada función de C tiene una entrada `_nombre`; si la
rutina usa IX, esa entrada lo guarda (SDCC lo usa como puntero de marco). Las
rutinas internas (`cpc_UpdTileTable`, `cpc_InvalidateRect`,
`cpc_TestKeyboard`…) se llaman desde ensamblador con su nombre.

---

## 2. El contrato entre el motor y la librería

La librería **no** es autónoma: usa símbolos que pone el güego.

### 2.1. Lo que pone el motor

- `tiles`: los gráficos de los tiles. Los define `cpc/tileset.h`: la fuente,
  `font.bin`, y los tiles, `work.bin`, que genera `mkts_om`.
- `viewport_x` / `viewport_y` (`cpc/sysvars.h`, a partir de `VIEWPORT_X` y
  `VIEWPORT_Y`): la librería los usa para recortar las marcas de celdas a la
  zona de juego (opción `CHURRERA_CLIPPING`).

```c
void viewport_symbols (void) __naked {
	__asm
		viewport_x == VIEWPORT_X
		viewport_y == VIEWPORT_Y
	__endasm;
}
```

### 2.2. Lo que la librería tiene fijo

La geometría de la pantalla es la misma en todos los güegos (32x24 tiles), así
que lo que antes ponía cada güego en un `tilemap_conf.asm` está en la
librería: las constantes en `CPCconfig.inc` y las tablas en
`cpc_TileMapConf.s`.

- `pantalla_juego` = `$100`: la nametable, 32x24 bytes, uno por celda, con
  el número de tile. En C es `nametable` (`cpc/sysvars.h`).
- `tiles_tocados` = `$CE00`: el bitfield de celdas sucias (96 bytes).
- `posiciones_pantalla`, `posiciones_super_buffer`: la dirección del principio
  de cada fila de caracteres en la pantalla y en el superbuffer.
- `posicion_inicial_area_visible` = `$C000` y
  `posicion_inicial_superbuffer` = `$9000`.
- `ancho_pantalla_bytes` = 64, `alto_pantalla_bytes` = 192,
  `ancho_pantalla_bytes_visible` = 64.
- `mascara1`, `mascara2` = 0: máscaras para los píxeles "mezclados" del
  modo 0. La librería actual no las usa.

### 2.3. Lo que usa el motor de la librería

- Desde C: `cpc_SetMode`, `cpc_ShowTileMap`, `cpc_UpdScr`,
  `cpc_ShowTouchedTiles`, `cpc_ResetTouchedTiles` y las rutinas de sprite
  (`cpc_PutSPTileMap4Bx16`, `cpc_PutTrSp4Bx16TileMap`, y con disparos
  `cpc_PutSPTileMap2Bx8`, `cpc_PutTrSp2Bx8TileMap`).
- Desde dos funciones puente en ensamblador (`cpc/printer.h`):
  `cpc_InvalidateRect` (`invalidate_rect ()`) y `cpc_TestKeyboard`
  (`key_line ()`).

---

## 3. Mapa de memoria (CPC)

Las direcciones están en `src/dev/cpc/sysvars.h` y en
`lib/cpcrslib-mt/CPCconfig.inc`:

```
$0100   la nametable          (BASE_TILEMAP, nametable)
$0400   el programa y sus variables (hasta $8800; ihx2bin lo comprueba)
$8800   la canción descomprimida (WYZ_SONG_BUFFER)
$9000   el superbuffer        (BASE_SUPERBUFF)
$C000   la pantalla visible   (en los huecos, lo que sigue)
$C600   la pantalla actual    (BASE_ROOM_BUFFERS: map_attr, map_buff)
$CE00   las celdas sucias     (BASE_DIRTY_CELLS, tiles_tocados)
$D600   arrays de enemigos y balas (BASE_ARRAYS)
$D680   golpes de los muros rompibles (BASE_BRK_BUFF)
$DF80   buffers del WYZ player (BASE_WYZ)
$E600   las estructuras de los sprites (BASE_SPRITES)
$F600   libre para el güego (BASE_CUSTOM)
$FE00   la LUT de píxeles transparentes (BASE_LUT)
$FFFF   la pila, hacia abajo  (STACK_ADDR)
```

Con la geometría de 32x24 caracteres que pone el motor, la pantalla visible
no ocupa los 16 KB de `$C000`: los huecos al final de cada bloque de 2 KB
(`$C600`, `$CE00`, `$D600`…) quedan libres, y el motor los aprovecha.

Las direcciones **no** son negociables: la librería las tiene fijadas en
`CPCconfig.inc` y en sus rutinas (la LUT, en `$FE00`). Si las cambias, hay
que cambiarlas en los dos sitios y volver a construir la librería.

---

## 4. El modelo: nametable, superbuffer y celdas sucias

A diferencia de splib2, el CPC trabaja con **tres** buffers:

1. **La nametable** (`$100`): 32x24 bytes con el número de tile de cada
   celda. Es el "estado lógico" de la pantalla. El motor escribe aquí, nunca
   en la memoria de pantalla.
2. **El superbuffer** (`$9000`): el buffer de píxeles donde se compone todo
   (fondo y sprites), en el formato de píxeles del modo de vídeo.
3. **La pantalla visible** (`$C000`): lo que se ve.

Y un **bitfield de celdas sucias** (`tiles_tocados`, 96 bytes en `$CE00`): 1
bit por celda, "esta celda hay que recomponerla".

### 4.1. `sp_UpdateNow ()` en CPC

El motor llama a `sp_UpdateNow ()` cada frame, igual que en ZX. En CPC está
en `cpc/printer.h` y hace esto:

1. Para cada sprite, llama a su rutina de **marcado**
   (`cpc_PutSPTileMap4Bx16`, o `cpc_PutSPTileMap2Bx8` para las balas), que
   marca en el bitfield las celdas que ocupa el sprite **en su posición
   anterior y en la nueva**.
2. `cpc_UpdScr`: para cada celda marcada, copia al superbuffer el gráfico del
   tile que dice la nametable. Esto **borra** los sprites que hubiera.
3. Para cada sprite, llama a su rutina de **dibujo**
   (`cpc_PutTrSp4Bx16TileMap`, o `cpc_PutTrSp2Bx8TileMap`), que lo pinta en
   el superbuffer.
4. Espera a que hayan pasado `MIN_FAPS_PER_FRAME` interrupciones (sale de
   `GAME_FRAME_TICKS`): es la sincronía de frames.
5. `cpc_ShowTouchedTiles`: copia del superbuffer a la pantalla **sólo** las
   celdas marcadas.
6. `cpc_ResetTouchedTiles`: limpia el bitfield.

El paso 5 es lo que hace que el CPC no parpadee: sólo se tocan las celdas que
han cambiado.

### 4.2. Escribir en la nametable

La celda (x, y) es `nametable [(y << 5) + x]`. Después de escribir hay que
marcar las celdas: `invalidate_rect ()` (`cpc/printer.h`) marca el
rectángulo de `px`, `py` a `pxx`, `pyy` con `cpc_InvalidateRect`. Lo hacen:

- `draw_coloured_tile (x, y, t)`: escribe los 4 caracteres del tile de 16x16
  (`64 + 4t` a `67 + 4t`) y marca las 4 celdas.
- `sp_PrintAtInv (y, x, color, tile)`: escribe un carácter y marca su celda.
  Es la misma función que en ZX, pero en CPC el color no se usa (el color va
  en los gráficos).
- `print_number2 (x, y, número)`: escribe dos dígitos y marca dos celdas.
- `print_str (x, y, color, texto)`: escribe un texto (el ASCII menos 32) y
  marca sus celdas.

---

## 5. La API usada, función por función

### 5.1. `cpc_SetMode (modo)`

- **Qué hace**: cambia el modo de vídeo (0: 16 colores, 1: 4 colores)
  escribiendo en el Gate Array.
- **Uso**: `system_init ()`, según `MODE_0` / `MODE_1` (que pone
  `comp-cpc.bat` a partir de `set mode=`).
- `cpc_SetMode` **no** toca el CRTC. El motor lo hace después, a mano, con la
  geometría de 32x24 caracteres (registro 1 = 32 columnas, 2 = 42, 6 = 24
  filas; y registro 5 = 4 con `MODE_1` y `AUTO_SPLIT`).

### 5.2. `cpc_Border (color)`

El motor tiene la suya, en `cpc/printer.h`: escribe el color del borde en el
Gate Array. `system_init ()` la llama con `0x54` (negro). La macro
`BORDER (b)` la usa.

### 5.3. `cpc_ShowTileMap (parámetro)`

- **Qué hace**: con `0`, recompone toda la pantalla (los 768 tiles de la
  nametable al superbuffer) y la vuelca a la pantalla; con `1`, **sólo
  vuelca** el superbuffer a la pantalla.
- **Uso**: `pantallas.h`, `cpc_ShowTileMap (1)` después de descomprimir una
  pantalla fija en el superbuffer (`unpack_screen ()` descomprime en
  `BASE_SUPERBUFF`).

### 5.4. `cpc_UpdScr ()`

Para cada celda marcada, copia al superbuffer el gráfico de su tile. Lo
llama `sp_UpdateNow ()`.

### 5.5. `cpc_ShowTouchedTiles ()` / `cpc_ResetTouchedTiles ()`

Copian a la pantalla las celdas marcadas y limpian el bitfield. Las llama
`sp_UpdateNow ()`, al final.

### 5.6. `cpc_UpdTileTable` (en ensamblador)

- **Qué hace**: marca una celda como sucia.
- **Parámetros**: `E` = columna, `D` = fila, en **coordenadas de pantalla**
  (0..31, 0..23), no de la zona de juego.
- **Uso**: la usan por dentro las rutinas de la librería.

### 5.7. `cpc_InvalidateRect` (en ensamblador)

- **Qué hace**: marca un rectángulo de celdas.
- **Parámetros**: `B` = fila de arriba, `C` = columna izquierda, `D` = fila
  de abajo, `E` = columna derecha (todo incluido).
- **Uso**: `invalidate_rect ()`, que toma el rectángulo de `px`, `py`,
  `pxx`, `pyy`.

### 5.8. `cpc_TestKeyboard` (en ensamblador)

- **Qué hace**: lee una línea de la matriz del teclado.
- **Parámetro**: `A` = línea (con el bit 6 puesto: `$40 | línea`).
- **Salida**: `A` con un bit a 1 por cada tecla pulsada de esa línea.
- **Uso**: `key_line (línea)` en C, que usan `pad_read ()` y
  `sp_KeyPressed ()`.

### 5.9. La tabla de teclas

- Es `keys [12]` (`cpc/sysvars.h`), 12 entradas de 2 bytes,
  `(($40 | línea) << 8) | bit`. El orden es izquierda, derecha, arriba,
  abajo, botón A, botón B, AUX3, AUX4, AUX1, AUX2, ENTER y ESC
  (`KEY_LEFT` = 0 … `KEY_ESC` = 11). `system_init ()` la llena con las del
  teclado. (La librería tiene su propia tabla, `cpc_KeysData`, para
  `cpc_TestKey`; el motor no la usa.)
- `pad_read ()` recorre las 8 primeras y monta `pad0` con los bits
  `sp_LEFT` (0x01), `sp_RIGHT` (0x02), `sp_UP` (0x04), `sp_DOWN` (0x08),
  `sp_FIRE` (0x10), `sp_FIRE2` (0x20), `sp_AUX3` (0x40) y `sp_AUX4` (0x80).
  Como en ZX, **a nivel bajo**: 0 = pulsado. `pad_this_frame` tiene a 0 los
  que se acaban de pulsar en este frame.
- En la pantalla de título, `select_joyfunc ()` copia sobre `keys` una de
  las dos tablas `const` de `cpc/sysvars.h`: `def_keys` (teclado: O, P, Q,
  A, espacio…) si se pulsa 1, o `def_keys_joy` (joystick) si se pulsa 2.

### 5.10. `sp_KeyPressed (código)` y `sp_WaitForNoKey ()`

Están escritas en `cpc/printer.h` para que el resto del motor funcione igual
que en ZX. El código de tecla es `(($40 | línea) << 8) | bit`; los que usa el
motor (`KEY_M`, `KEY_H`, `KEY_Y`, `KEY_Z`, `KEY_1`…) están en
`cpc/sysvars.h`.

---

## 6. Los sprites en el CPC

### 6.1. La estructura `SPR`

El motor no usa los sprites de la CPCRSLIB original: tiene su propia
estructura de 16 bytes (`cpc/sysvars.h`):

```c
typedef struct sprite {
	unsigned int sp0;			// 0   puntero al gráfico del frame
	unsigned int sp1; 			// 2   (no se usa)
	unsigned int coord0;		// 4   (no se usa)
	signed char cox, coy;		// 6 7 (no se usa)
	unsigned char cx, cy; 		// 8 9 posición actual
	unsigned char ox, oy;		// 10 11 posición anterior
	void *invfunc;				// 12 (no se usa)
	void *updfunc;				// 14 (no se usa)
} SPR;

AT (BASE_SPRITES) SPR sp_sw [SW_SPRITES_ALL];
```

- `cx`, `cy`: la posición **actual**. `cx` va en **bytes** de la pantalla
  (0..63) y `cy` en **líneas** (0..191).
- `ox`, `oy`: la posición **anterior**. La rutina de marcado marca las
  celdas de las dos posiciones, para que el sprite no deje rastro, y luego
  copia `cx`, `cy` en `ox`, `oy`.
- `sp0`: el gráfico del frame que se ve.

`sp_sw` está en `BASE_SPRITES` (`$E600`), y los índices son:

- `SP_PLAYER` (0): el jugador,
- `SP_ENEMS_BASE` (1, 2 y 3): los enemigos,
- `SP_BULLETS_BASE` (4…): las balas.

`SW_SPRITES_ALL` = 1 + 3 + `MAX_BULLETS`.

### 6.2. Quién pone qué

- `system_init ()` coloca todos los sprites fuera de la zona de juego.
- `saca_a_todo_el_mundo_de_aqui ()` les pone a todos el gráfico vacío
  (`sprite_18_a`).
- Cada frame, `render_sprites ()` coloca a los enemigos, al jugador (o le
  pone el gráfico vacío si está parpadeando) y a las balas con
  `cpc_MoveSprAbs`.

### 6.3. `cpc_MoveSprAbs (sprite, frame, x, y)`

Es una función del motor (`cpc/printer.h`), equivalente a la `sp_MoveSprAbs`
de splib2: pone en `sp_sw [sprite]` el gráfico `frame` y la posición, pasando
de las coordenadas del motor (píxeles dentro de la zona de juego) a las de la
librería:

```
cx = x / 4 + VIEWPORT_X * 2     (bytes)
cy = y + VIEWPORT_Y * 8         (líneas)
```

Así que **en horizontal los sprites se mueven de 4 en 4 píxeles** (un byte;
en modo 0, un byte son dos píxeles anchos).

Las rutinas que usa el motor son siempre las mismas:

| Sprites | Marcar | Dibujar | Tamaño |
|---|---|---|---|
| Jugador y enemigos | `cpc_PutSPTileMap4Bx16` | `cpc_PutTrSp4Bx16TileMap` | 4 bytes x 16 líneas (64 bytes) |
| Balas | `cpc_PutSPTileMap2Bx8` | `cpc_PutTrSp2Bx8TileMap` | 2 bytes x 8 líneas (16 bytes) |

`sp_UpdateNow ()` las llama directamente para cada sprite (los campos
`invfunc` y `updfunc` no se usan).

### 6.4. Los datos de los sprites

Los gráficos vienen de los png de `gfx/cpc/`, que `comp-cpc.bat` convierte con
`mkts_om` (capítulo 11 del manual):

- `sprites.png` → `sprites.bin`: los 16 sprites del güego, 64 bytes cada uno
  (`cpc/sprites.h`). `cpc/spriteset_mappings.h` define `sprite_1_a` …
  `sprite_16_a` como `sprites + 64 * (n - 1)`, para que el resto del motor
  (`cpc/cell_arrays.h`, `engine.h`) los use con los mismos nombres que en ZX.
- `sprites_extra.png` → `sprites_extra.bin`: la explosión (`sprite_17_a`).
- `sprite_18_a`: el sprite vacío (96 bytes a 0), en `cpc/extrasprites.h`.
- `sprites_bullet.png` → `sprites_bullet.bin`: la bala (`sprite_19_a`).

Cada sprite es un bitmap de 4 bytes por línea, en el formato de píxeles del
modo de vídeo. Las tablas de frames (`player_frames []` y `enem_frames []`,
en `cpc/cell_arrays.h`) apuntan a esos gráficos, y el motor pone el que toca
en `sp0`.

### 6.5. La transparencia: la LUT

Las rutinas de dibujo mezclan el sprite con el fondo byte a byte:

```
destino = (fondo AND LUT [byte_del_sprite]) OR byte_del_sprite
```

`LUT` es la **LUT de píxeles transparentes** de `$FE00` (`BASE_LUT`). Para
cada byte posible del sprite dice qué bits del fondo se conservan: los píxeles
con el color 0 son transparentes. La genera el motor:

- `src/dev/cpc/cpc_TrPixLutM0.asm` (modo 0) y `cpc_TrPixLutM1.asm` (modo 1),
- `comp-cpc.bat` la ensambla con `pasmo` y la comprime con `zx0`
  (`trpixlutc.bin`),
- `system_init ()` la descomprime en su sitio al arrancar:

```c
unpack ((unsigned char *) trpixlutc, (unsigned char *) BASE_LUT);
```

---

## 7. La interrupción

La interrupción es del motor, no de la librería: `system_init ()`
(`cpc/printer.h`) pone un `jp _isr` en `$38`. El CPC interrumpe 300 veces por
segundo; la ISR (una función `__naked` en ensamblador) cuenta en `isr_c1` y,
cada 6, suma uno al contador de frames (`isr_c2`, el que espera
`sp_UpdateNow ()`) y, si está sonando, llama al WYZ player
(`WYZ_PLAYER_ISR`, en `cpc/wyz_player.s`).

---

## 8. Recetas: tu propio código

### 8.1. Añadir un sprite propio

1. Sube `SW_SPRITES_ALL` en `cpc/sysvars.h` (cada sprite son 16 bytes más en
   `BASE_SPRITES`) y usa los índices de después de las balas.
2. Pon el gráfico en el png de sprites (o en otro png convertido con
   `mkts_om` y metido con `.incbin` en una función `__naked`, como
   `cpc/extrasprites.h`).
3. Muévelo cada frame con `cpc_MoveSprAbs (índice, gráfico, x, y)`.
4. Como `sp_UpdateNow ()` recorre todos los sprites de `sp_sw` con las
   rutinas de 4Bx16 (salvo las balas), un sprite propio de 16x16 no necesita
   nada más. Para otro tamaño, hay que cambiar `sp_UpdateNow ()` para que use
   sus rutinas.

### 8.2. Escribir en pantalla

- **Un tile o un carácter**: `draw_coloured_tile`, `sp_PrintAtInv`,
  `print_number2` y `print_str`, igual que en ZX (sección 4.2).
- **A mano**: escribe en la nametable (`nametable [(y << 5) + x]`) y marca
  las celdas con `invalidate_rect ()` (pon antes `px`, `py`, `pxx` y
  `pyy`).

Nunca escribas en `$C000` (la pantalla visible) esperando que se quede: el
siguiente `sp_UpdateNow ()` lo pisa en cuanto esas celdas se ensucien.

### 8.3. Teclas

- `sp_KeyPressed (código)` para una tecla concreta.
- `pad0` y `pad_this_frame` para el mando del jugador (sección 5.9).

### 8.4. Forzar un repintado completo

`cpc_ShowTileMap (0)` recompone la pantalla entera desde la nametable.

---

## 9. Trampas

- **La librería no es autónoma**: si cambias las direcciones de
  `CPCconfig.inc`, `BASE_LUT` o `BASE_SPRITES`, hay que volver a construir la
  librería con las mismas.
- **El superbuffer es el protagonista**: lo que se dibuje "a mano" en
  `$C000` se pierde; hay que ir por la nametable.
- **El orden de `sp_UpdateNow ()` importa**: primero se marcan las celdas,
  luego se recarga el fondo (`cpc_UpdScr`), luego se dibujan los sprites y al
  final se vuelca a la pantalla. Si recargas el fondo después de dibujar los
  sprites, los borras.
- **Las coordenadas**: `cx` va en bytes y `cy` en líneas de la pantalla
  entera, no de la zona de juego (`cpc_MoveSprAbs` hace la conversión).
- **Modo 0 o modo 1**: cambia el número de colores, el formato de los
  píxeles (`mkts_om` con `cpcmode=`) y la LUT de transparencia
  (`cpc_TrPixLutM0` o `M1`). `comp-cpc.bat` lo elige todo con `set mode=`.
- **La tabla de teclas se reescribe**: `select_joyfunc ()` copia
  `def_keys` o `def_keys_joy` sobre `keys`.
- **La variante fg** necesita la tabla `behindtilemasks`; si falta, no
  enlaza.
- **Los sprites no tienen capas**: se dibujan en el orden de `sp_sw`, del
  primero al último, así que los de índice más alto (las balas) quedan
  delante.

---

## 10. Índice rápido

| Función | Para qué | Dónde la usa el motor |
|---|---|---|
| `cpc_SetMode` | Cambia el modo de vídeo. | `system_init ()` |
| `cpc_Border` (del motor) | Color del borde. | `system_init ()`, `BORDER ()` |
| `cpc_ShowTileMap` | Recompone y/o vuelca la pantalla. | `pantallas.h` |
| `cpc_UpdScr` | Recarga en el superbuffer las celdas sucias. | `sp_UpdateNow ()` |
| `cpc_ShowTouchedTiles`, `cpc_ResetTouchedTiles` | Vuelcan las celdas sucias y limpian la marca. | `sp_UpdateNow ()` |
| `cpc_InvalidateRect` | Marca un rectángulo. | `invalidate_rect ()`: `draw_coloured_tile`, `sp_PrintAtInv`, `print_number2`, `print_str` |
| `cpc_TestKeyboard` | Lee una línea del teclado. | `key_line ()`: `pad_read`, `sp_KeyPressed` |
| `cpc_PutSPTileMap4Bx16`, `cpc_PutTrSp4Bx16TileMap` | Marcan y dibujan un sprite de 16x16. | `sp_UpdateNow ()` |
| `cpc_PutSPTileMap2Bx8`, `cpc_PutTrSp2Bx8TileMap` | Marcan y dibujan una bala. | `sp_UpdateNow ()` |
| `cpc_MoveSprAbs` (del motor) | Coloca un sprite. | `render_sprites ()` |

### Ficheros relacionados

- `lib/cpcrslib-mt/` — la librería (fuente en ensamblador, cabecera,
  `cpcrslib.lst` con los módulos, `make.bat` y `make.sh`).
- `lib/cpcrslib-mt/README.md` — notas de la poda de la librería.
- `lib/cpcrslib-mt/cosas.md` — notas de implementación (píxeles de modo 0,
  LUTs).
- `lib/cpcrslib-mt/CPCconfig.inc` — la configuración y las constantes del
  tilemap.
- `src/dev/cpc/` — todo lo que usa la librería (ver el principio), y las
  librerías compiladas.
- `src/dev/cpc/cpc_TrPixLutM0.asm`, `cpc_TrPixLutM1.asm` — la LUT de
  píxeles transparentes.
- `src/utils/mkts_om.bas` — el conversor de gráficos de CPC.
