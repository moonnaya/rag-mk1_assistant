# splib2 en MTE MK1 v3.100 (ZX Spectrum)

Copyleft 2011, 2026 The Mojon Twins

Este documento explica cómo usa el motor la librería de sprites **Sprite Pack
2.2** (`splib2`), que está en `lib/splib2/`. Está pensado para quien vaya a
escribir código propio (`dev/custom.h`, `dev/extern.h`) y necesite saber:

- qué funciones de splib2 están disponibles y qué hace cada una,
- cómo las usa el motor y por qué,
- qué formato tienen los datos (tiles, sprites) que splib2 espera,
- qué trampas hay (memoria, planos, formatos).

> **Esto sólo aplica al ZX Spectrum.** En CPC el motor usa `cpcrslib`: ver
> [`lib-cprslib.md`](lib-cprslib.md).

Todo el uso de splib2 está en `src/dev/speccy/`: `sysvars.h` (variables,
teclas, memoria de los sprites), `printer.h` (inicialización, pintado de tiles
y texto, sprites, mandos), `isr.h` (la interrupción de 48K) y `cell_arrays.h`
(las tablas de frames). Las direcciones de memoria están en
`src/dev/churromain.c`.

---

## 1. Qué es splib2 y por qué está aquí

splib2 (Sprite Pack 2.2, de Alvin Albrecht) es un motor de sprites "clásico"
para ZX Spectrum: mantiene una *display list* (la lista lógica de lo que hay
en pantalla), un mapa de celdas *sucias* y una lista de sprites; y en cada
actualización (`sp_UpdateNow`) redibuja **sólo** las celdas marcadas como
sucias, componiendo el fondo (tiles) y los sprites encima.

El motor usa splib2 para todo lo que tiene que ver con la pantalla del ZX:

- la pantalla de juego se dibuja **en la display list** de splib2, no
  directamente en la memoria de pantalla;
- los sprites (jugador, enemigos, balas) son sprites de splib2;
- el refresco de pantalla es `sp_UpdateNow`;
- el teclado y los joysticks se leen con las rutinas de splib2.

La versión que hay en el repositorio es una copia recortada de la
distribución original: `lib/splib2/sp.lst` dice qué módulos se compilan, y
**muchos módulos de splib2 no están** (hashtable, huffman, ratón, listas
enlazadas, parte del AY...). Lo que sí está es todo lo que el motor usa.

### 1.1. Cómo se instala y cómo se enlaza

La librería está en ensamblador de `sdasz80` (los `.s` de `lib/splib2`).
`lib/splib2/make.bat` (o `make.sh`) ensambla los módulos de `sp.lst` con la
configuración de `SPconfig.inc` y deja la librería, `splib2.lib`, y su
cabecera, `spritepack.h`, en `src/dev/speccy`. Así cada güego lleva su copia
y no hay que instalar nada.

`comp-zx.bat` enlaza con ella:

```
sdldz80 ... -k speccy -l splib2.lib -k %GBDK_HOME%\lib\z80 -l z80.lib
```

y `speccy/sysvars.h` incluye la cabecera:

```c
#include "spritepack.h"
```

El motor usa siempre la API en C de `spritepack.h` (las funciones `sp_*`).

#### Cómo se llama desde C

Cada función `sp_*` es un envoltorio (`lib/splib2/cwrapper`) declarado con
`__smallc` en `spritepack.h`: SDCC pone los argumentos en la pila de
izquierda a derecha, de 2 bytes cada uno (como el antiguo z88dk), y el
envoltorio los saca y llama a la rutina de la librería. Las funciones
devuelven en L (8 bits) o HL (16 bits). Como las rutinas usan IX, que SDCC
necesita intacto, cada envoltorio lo guarda al entrar (en `__sp_ixsave`) y lo
recupera al salir.

---

## 2. Mapa de memoria (ZX)

splib2 usa direcciones absolutas, así que el motor reserva la parte de arriba
de la memoria de forma fija (`churromain.c` y `speccy/sysvars.h`):

```
23300 - 23599   map_attr y map_buff  (BASE_ROOM_BUFFERS: la pantalla actual)
23600 - 23727   arrays de enemigos y balas (BASE_ARRAYS)
23728 - 23877   golpes de los muros rompibles (BASE_BRK_BUFF)
24200 - ?????   el programa y sus variables
AD_FREE - 0xEFFF  bloques para los sprites (sp_AddMemory)
0xF000 - 0xF100   tabla de vectores IM2
0xF1F0 hacia abajo  la pila, 64 bytes (en 48K)
0xF1F1            la interrupción (el GenericISR de splib2)
0xF200 - 0xFFFF   tablas de rotación horizontal de splib2
```

En 128K la pila va por debajo del programa (empieza en 24200 y crece hacia
abajo), porque entre 0xC000 y 0xFFFF se ponen otras páginas de RAM.

Las direcciones fijas de splib2 están en `lib/splib2/SPconfig.inc`:

- `IM2TABLE = 0xF000`: tabla de vectores IM2, 257 bytes (`$F000-$F100`).
- `SProtatetbl = 0xF000`, pero lo que ocupa de verdad es `$F200-$FFFF`
  (4 KB): las tablas que permiten desplazar los sprites de 0 a 7 píxeles en
  horizontal.
- El GenericISR se copia en `$F1F1` (61937).

El motor calcula la memoria de los sprites en `churromain.c`:

```c
#define NUMBLOCKS (40 + 5 * MAX_BULLETS)
#define AD_FREE   (0xF000 - (NUMBLOCKS * 15))
```

`NUMBLOCKS` es el número de bloques de memoria que se le dan al asignador de
splib2 (ver la sección 5.2): 10 por cada sprite de 16x16 (jugador y tres
enemigos) y 5 por cada bala. **Si añades sprites propios, tienes que subir
`NUMBLOCKS`** (sección 9).

---

## 3. El modelo interno de splib2 (lo mínimo que hay que saber)

### 3.1. La display list

`SPDisplayList` es un array de 4 bytes por celda de pantalla (32x24 = 768
celdas, 3072 bytes):

- byte 0: **atributo** (PAPER/INK/BRIGHT/FLASH),
- byte 1: **número de tile** (índice en `SPTileArray`),
- bytes 2-3: puntero (big endian) al primer *char struct* de sprite de esa
  celda, o 0 si no hay ninguno.

### 3.2. Las celdas sucias

`SPDirtyChars` es un mapa de bits (96 bytes: 32/8 x 24) que marca qué celdas
hay que redibujar. `sp_UpdateNow` sólo repinta esas celdas: por eso el motor
escribe en la pantalla con `sp_PrintAtInv`, que además marca la celda como
sucia.

### 3.3. `SPTileArray`: los 256 tiles

splib2 dibuja el fondo con 256 "tiles" de 8x8 (caracteres). `SPTileArray`
guarda, para cada uno, un puntero a sus 8 bytes de gráfico.

El motor los apunta al tileset del güego (`ts.bin`, que genera `ts2bin`, ver
el capítulo 1 del manual) al arrancar, en `system_init ()`:

```c
allpurposepuntero = tileset;
gpit = 0; do {
	sp_TileArray (gpit, allpurposepuntero);
	allpurposepuntero += 8;
	gpit ++;
} while (gpit);
```

`ts.bin` son 2304 bytes: los 256 gráficos de 8x8 (2048 bytes) y, detrás, 256
atributos que usa `draw_coloured_tile` para colorear cada carácter. Como
`SPTileArray` sólo guarda punteros, cambiar el contenido de `tileset` cambia
los gráficos sin volver a llamar a `sp_TileArray`: es lo que hace un nivel con
tileset propio (se descomprime encima de `tileset`).

Los caracteres 0-63 son la fuente (ASCII 32-95) y los 64-255, los 48 tiles de
16x16 (4 caracteres cada uno): el tile `t` son los caracteres `64 + 4t` a
`67 + 4t`.

### 3.4. Sprites y *char structs*

Un sprite de splib2 (`struct sp_SS`, 14 bytes) es una lista de columnas, y
cada columna es una lista de *char structs* (`struct sp_CS`, 14 bytes), uno
por cada **fila de caracteres** del sprite:

```c
struct sp_SS {
   uchar row, col, height, width, hor_rot, ver_rot;
   uchar *first, *last_col, *last;
   uchar plane, type;
};

struct sp_CS {
   uchar *next_in_spr;   /* big endian!! */
   uchar *prev;          /* big endian!! */
   uchar spr_attr;       /* tipo (bits 7-6) | plano (bits 5-0) */
   uchar *left_graphic;  /* datos de la columna izquierda */
   uchar *graphic;       /* puntero al bitdef de esta columna */
   uchar hor_rot;        /* página de la tabla de rotación */
   uchar colour;         /* atributo (no se usa en modo Spectrum) */
   uchar *next;          /* big endian!! */
   uchar unused;
};
```

- `plane` (0..63): **menor plano = más delante**. El motor crea todos sus
  sprites en el plano 1.
- `type`: `sp_MASK_SPRITE` (0x00), `sp_OR_SPRITE` (0x40), `sp_XOR_SPRITE`
  (0x80), `sp_LOAD_SPRITE` (0xC0).
- `graphic` apunta al *bitdef* de la columna: los datos de los píxeles.
- `left_graphic` apunta a los datos de la columna de la izquierda; es lo que
  permite el desplazamiento horizontal de 0..7 píxeles (los píxeles que
  "se salen" de una columna se toman de la vecina).

---

## 4. El flujo de un frame en el motor

En cada frame (`mainloop.h`), el motor:

1. mueve al jugador y a los enemigos;
2. llama a `render_sprites ()` (`speccy/printer.h`), que llama a
   `sp_MoveSprAbs` para cada sprite (enemigos, jugador, balas);
3. llama a `sp_UpdateNow ()`, que repinta las celdas sucias;
4. espera a que la interrupción haya contado `GAME_FRAME_TICKS` interrupciones
   desde el frame anterior (`isr_frames`).

Al cambiar de pantalla, `draw_scr ()` (`engine.h`) pinta todos los tiles de
la pantalla nueva en la display list.

---

## 5. La API de splib2 que usa el motor, función por función

### 5.1. Inicialización e interrupciones

Todo esto está en `system_init ()` (`speccy/printer.h`), que se llama una vez
al arrancar:

```c
__asm__ ("di");
sp_InitIM2 ((void *) 0xf1f1);
sp_CreateGenericISR ((void *) 0xf1f1);
sp_RegisterHook (255, ISR_HOOK);
__asm__ ("ei");
...
sp_Initialize (7, 0);
sp_Border (BLACK);
sp_AddMemory (0, NUMBLOCKS, 14, (void *) AD_FREE);
```

#### `sp_InitIM2 (isr)`

- **Qué hace**: prepara la tabla de vectores IM2 (257 bytes en `$F000`) con
  todos los vectores apuntando a `isr`, y pone el modo de interrupción 2.
- **Ojo**: hay que llamarla con las interrupciones deshabilitadas.

#### `sp_CreateGenericISR (dirección)`

- **Qué hace**: copia el ISR genérico de splib2 a esa dirección. Ese ISR
  ejecuta una cadena de *hooks*; si un hook deja el carry puesto, la cadena
  se corta.
- El motor lo pone en `0xF1F1`, en el hueco entre la tabla IM2 y las tablas
  de rotación.

#### `sp_RegisterHook (vector, hook)`

- **Qué hace**: añade una función a la lista de hooks del ISR genérico.
- El hook del motor es `isr_hook`, en ensamblador (una función `__naked`).
  En 48K (`speccy/isr.h`) sólo cuenta interrupciones (`isr_frames ++`), para
  la sincronía de frames. En 128K (`speccy_128/wyzplayer.h`) además llama al
  WYZ player. Acaba con el acarreo a 0 (`or a`) para que sigan los demás
  hooks.
- splib2 guarda el enlace de la lista en los 2 bytes anteriores al hook: por
  eso `isr_hook` empieza con `.dw 0` y se registra su dirección más 2
  (`ISR_HOOK`).

#### `sp_Initialize (atributo, tile)`

- **Qué hace**: (1) llena la display list con el tile y el atributo dados,
  (2) marca toda la pantalla como sucia, (3) construye las tablas de
  rotación horizontal.
- El motor la llama con atributo 7 y tile 0.

#### `sp_Border (color)`

Pone el color del borde.

### 5.2. Memoria: el asignador de bloques

#### `sp_AddMemory (cola, número, tamaño, dirección)`

- **Qué hace**: añade `número` bloques de `tamaño` bytes a la cola `cola`, a
  partir de `dirección`. Cada bloque ocupa `tamaño + 1` bytes (el byte extra
  identifica la cola).
- El motor le da `NUMBLOCKS` bloques de 14 bytes (15 con el identificador) en
  `AD_FREE`, en la cola 0.

#### `sp_BlockAlloc (cola)` / `sp_FreeBlock (bloque)`

- **Qué hacen**: reservan y liberan un bloque de una cola.
- splib2 usa este asignador **por dentro** para crear sprites: cada `sp_SS`
  y cada `sp_CS` son 14 bytes, que `sp_CreateSpr` y `sp_AddColSpr` piden a
  la cola 0 (y `sp_DeleteSpr` devuelve). En la splib2 original eso pasaba
  por dos punteros, `u_malloc` y `u_free`, que tenía que definir el
  programa; en esta copia las rutinas llaman directamente al asignador.

El motor crea sus sprites una vez, al arrancar, y no los destruye nunca.

### 5.3. El fondo

#### `sp_PrintAtInv (fila, columna, atributo, tile)`

- **Qué hace**: escribe en la display list el atributo y el número de tile
  de una celda y la marca como sucia.
- **Parámetros**: `fila` (0..23), `columna` (0..31), `atributo` (el color
  del Spectrum), `tile` (0..255, índice en `SPTileArray`).
- **Uso en el motor** (`speccy/printer.h`): es lo único con lo que el motor
  pinta en pantalla durante el juego.
  - `draw_coloured_tile (x, y, t)` pinta un tile de 16x16 con cuatro
    llamadas (los caracteres `64 + 4t` a `67 + 4t`, con sus atributos del
    tileset). Con `USE_AUTO_SHADOWS` o `USE_AUTO_TILE_SHADOWS` cambia el
    atributo o el carácter de los que quedan a la sombra.
  - `print_number2` y `print_str`: los números y textos (la fuente son los
    caracteres 0-63: el carácter es el ASCII menos 32).
  - `draw_objs`: el marcador de objetos.

#### `sp_UpdateNow ()`

- **Qué hace**: repinta todas las celdas sucias: los tiles del fondo y,
  encima, los sprites que las tocan.
- **Uso**: cada frame en `mainloop.h`; en las pantallas fijas
  (`pantallas.h`); y en lo que tiene que mostrarse en el momento, como la
  acción `SHOW` del script (`msc.h`).

### 5.4. Sprites

#### `sp_CreateSpr (tipo, filas, gráfico, plano)`

- **Qué hace**: crea un sprite. Reserva el `sp_SS` y un `sp_CS` por cada fila
  de caracteres, y pone en la primera columna el *bitdef* `gráfico`.
- **Parámetros**:
  - `tipo`: `sp_MASK_SPRITE`, `sp_OR_SPRITE`, `sp_XOR_SPRITE`,
    `sp_LOAD_SPRITE`.
  - `filas`: **número de filas de caracteres** (3 para un sprite de 16 de
    alto, porque al moverse en vertical ocupa 3 filas).
  - `gráfico`: puntero al bitdef de la primera columna.
  - `plano`: 0..63, menor = más delante.
- **Salida**: puntero al `sp_SS`, o `NULL` si no hay memoria.

#### `sp_AddColSpr (sprite, gráfico)`

- **Qué hace**: añade una columna de 8 píxeles al sprite.

El motor crea así sus sprites, en `system_init ()`:

```c
#ifdef NO_MASKS
	#define BLIT_TYPE sp_OR_SPRITE
#else
	#define BLIT_TYPE sp_MASK_SPRITE
#endif

sp_player = sp_CreateSpr (BLIT_TYPE, 3, sprite_2_a, 1);
sp_AddColSpr (sp_player, sprite_2_b);
sp_AddColSpr (sp_player, sprite_2_c);

for (gpit = 0; gpit < 3; gpit ++) {
	sp_moviles [gpit] = sp_CreateSpr (BLIT_TYPE, 3, sprite_9_a, 1);
	sp_AddColSpr (sp_moviles [gpit], sprite_9_b);
	sp_AddColSpr (sp_moviles [gpit], sprite_9_c);
}

// Con PLAYER_CAN_FIRE: las balas, de 8x8
sp_bullets [gpit] = sp_CreateSpr (sp_OR_SPRITE, 2, sprite_19_a, 1);	// o sp_MASK_SPRITE con MASKED_BULLETS
sp_AddColSpr (sp_bullets [gpit], sprite_19_b);
```

- Un sprite de 16x16 tiene **3 filas y 3 columnas**: al moverse píxel a
  píxel puede tocar 3x3 caracteres. La tercera columna (`_c`) está vacía:
  es la que recibe los píxeles que se salen por la derecha. Cuesta
  1 + 3x3 = 10 bloques.
- Una bala de 8x8 tiene 2 filas y 2 columnas: 1 + 2x2 = 5 bloques.

#### `sp_MoveSprAbs (sprite, clip, animación, fila, columna, píxel_x, píxel_y)`

- **Qué hace**: coloca un sprite en una posición absoluta.
- **Parámetros**:
  - `clip`: el rectángulo fuera del cual no se dibuja (ver más abajo).
  - `animación`: cuántos bytes hay que avanzar (o retroceder) en el bitdef
    para pasar al frame nuevo; 0 si no cambia (ver la sección 7).
  - `fila`, `columna`: la posición en caracteres.
  - `píxel_x`, `píxel_y`: el desplazamiento dentro del carácter (0..7).
- Por dentro: si la celda cambia, invalida la zona que ocupaba el sprite y
  lo pone en la lista de sprites de las celdas nuevas; recalcula los
  punteros gráficos con el desplazamiento y la animación.
- **Uso en el motor** (`speccy/printer.h`): `render_sprites ()` y
  `update_this_enemy ()` en cada frame, y `saca_a_todo_el_mundo_de_aqui ()`
  para quitarlos de en medio.

El motor trabaja en píxeles y splib2 en caracteres más resto. Así coloca al
jugador:

```c
sp_MoveSprAbs (sp_player, SPRITES_CLIP, player.next_frame - player.current_frame,
	VIEWPORT_Y + (gpy >> 3), VIEWPORT_X + (gpx >> 3), gpx & 7, gpy & 7);
player.current_frame = player.next_frame;
```

Para esconder un sprite se le manda fuera del clip (por ejemplo, a la fila y
columna 254).

`update_this_enemy ()` no llama a `sp_MoveSprAbs` si el enemigo no ha
cambiado ni de sitio ni de frame: así splib2 no repinta sus celdas sin
necesidad.

#### El rectángulo de recorte (clip)

`spritesClip` es un `struct sp_Rect` (fila, columna, alto, ancho) constante,
en `speccy/sysvars.h`; `SPRITES_CLIP` es su dirección, que es lo que se pasa
a `sp_MoveSprAbs`:

```c
const struct sp_Rect spritesClip = { VIEWPORT_Y, VIEWPORT_X, 20, 30 };
#define SPRITES_CLIP ((struct sp_Rect *) &spritesClip)
```

Es la zona de juego: 30x20 caracteres a partir de `VIEWPORT_X`,
`VIEWPORT_Y`. Lo que queda fuera no se dibuja, así que los sprites no pisan
el marcador.

### 5.5. Entrada

#### `sp_JoyKeyboard (teclas)`, `sp_JoyKempston ()`, `sp_JoySinclair1 ()`

- **Qué hacen**: leen el teclado o el joystick y devuelven un byte con los
  cinco botones, **a nivel bajo** (0 = pulsado): `sp_FIRE` = 0x80,
  `sp_RIGHT` = 0x08, `sp_LEFT` = 0x04, `sp_DOWN` = 0x02, `sp_UP` = 0x01.
- `sp_JoyKeyboard` recibe un `struct sp_UDK` con las teclas. El motor tiene
  dos juegos en `speccy/sysvars.h`: el normal (O, P, Q, A, espacio) y el de
  `USE_TWO_BUTTONS`.
- El motor guarda la función elegida en `joyfunc`. En la pantalla de título,
  `select_joyfunc ()` deja elegir con 1, 2 o 3 (teclado, Kempston,
  Sinclair).
- `pad_read ()` la llama cada frame:

```c
void pad_read (void) {
	pad_this_frame = pad1;
	pad1 = pad0 = (joyfunc) (&keys);

	// Keys held this frame
	pad_this_frame = (~pad_this_frame) | pad1;
}
```

  `pad0` tiene los botones pulsados ahora, y `pad_this_frame` tiene a **0**
  los que se acaban de pulsar *en este frame*. Por eso
  `(pad_this_frame & sp_FIRE) == 0` quiere decir "acaban de pulsar FIRE".

#### `sp_KeyPressed (código)`

- **Qué hace**: dice si una tecla está pulsada. El código es
  `(máscara << 8) | fila` del teclado del Spectrum.
- Los que usa el motor están en `speccy/sysvars.h`: `KEY_M` (la tecla de
  acción del script), `KEY_H` y `KEY_Y` (pausa y abortar), `KEY_Z`, `KEY_1`,
  `KEY_2` y `KEY_3`.

#### `sp_GetKey ()` y `sp_WaitForNoKey ()`

`sp_GetKey` devuelve el carácter de la tecla pulsada (0 si no hay ninguna);
`sp_WaitForNoKey` espera a que se suelten todas. El motor las usa en los
menús y en las esperas.

---

## 6. El formato de los datos de sprite

Este es el punto donde más gente se equivoca, así que léelo con calma.

### 6.1. El *bitdef*

Los datos de un sprite son, para cada columna de 8 píxeles de ancho, **dos
bytes por línea de píxeles**: el gráfico y la máscara.

- En un sprite `sp_MASK_SPRITE` el píxel es `(pantalla AND máscara) OR
  gráfico`: los bits a 1 de la máscara dejan ver el fondo.
- En un `sp_OR_SPRITE` (y `XOR`, `LOAD`) la máscara se ignora: sólo
  `pantalla OR gráfico`.

Para poder desplazar el sprite de 0 a 7 píxeles en vertical, splib2 mueve el
puntero al bitdef, así que cada columna necesita **8 líneas de relleno**
transparente (`0, 255`) debajo, y la primera, otras 8 encima.

### 6.2. El generador: `sprcnv`

`sprcnv` convierte el png de sprites (`gfx/speccy/sprites.png`, capítulo 3
del manual) en `speccy/sprites.h`. Lo llama `comp-zx.bat` (o tu
`convert.bat`):

```bat
"%U%\sprcnv" ..\gfx\speccy\sprites.png speccy\sprites.h > nul
```

En el png, cada gráfico ocupa 32x16 píxeles: el sprite a la izquierda y su
máscara a la derecha. Hay 16 gráficos, y para cada uno `sprcnv` genera tres
columnas:

- `sprite_N_a`: la columna izquierda (16 líneas + 8 de relleno),
- `sprite_N_b`: la columna derecha (16 + 8),
- `sprite_N_c`: la columna vacía (24 líneas de `0, 255`).

Todo va en una tabla `const`, `sprite_data`, y `sprite_N_a`, `_b` y `_c`
son punteros dentro de ella. Delante de `sprite_1_a` van las 8 líneas de
relleno de arriba. Cada gráfico ocupa lo mismo (144 bytes) y van seguidos:
esto es importante (sección 7). Si la salida acaba en `.bin`, `sprcnv`
escribe esos mismos bytes en binario (los spritesets de los niveles).

Los sprites extra están escritos a mano, en el mismo formato, en
`speccy/extrasprites.h`: una tabla `const`, `extrasprites`, con `sprite_17`
(la explosión), `sprite_18` (vacío, para los enemigos muertos) y `sprite_19`
(la bala, de 8x8), cada uno con sus columnas seguidas.

Con niveles (capítulo 10 del manual), un nivel puede traer su spriteset: se
descomprime encima de los 16 sprites, en `sprite_1_a - 16` (incluye el relleno
de arriba).

### 6.3. Las tablas de frames

El motor no guarda un número de frame: guarda **punteros al bitdef**
(`player.current_frame` / `player.next_frame`, y `en_an_current_frame []` /
`en_an_next_frame []` para los enemigos).

Los punteros salen de las tablas de `speccy/cell_arrays.h`:

- `player_frames []`: los frames del jugador. Hay una tabla por cada tipo de
  movimiento (`PLAYER_MOGGY_STYLE`, `PLAYER_BOOTEE`,
  `PLAYER_ALTERNATE_ANIMATION` o el normal), y `move ()` (`engine.h`) elige
  el índice según hacia dónde mira y qué hace.
- `enem_frames []`: los 8 frames de los enemigos (`sprite_9_a` a
  `sprite_16_a`), dos por tipo. El índice es
  `en_an_base_frame [gpit] + en_an_frame [gpit]`.

La explosión y el enemigo muerto usan directamente `sprite_17_a` y
`sprite_18_a`.

---

## 7. El truco del desplazamiento: cómo se anima un sprite

Cuando el frame de un sprite cambia, el motor **no** reconstruye el sprite:
le pasa a `sp_MoveSprAbs` un **desplazamiento** que se suma a los punteros
gráficos de todas sus columnas. Es decir: "el gráfico está N bytes más allá":

```c
player.next_frame - player.current_frame
```

**Consecuencia**: los frames de un mismo sprite tienen que estar en memoria
con el mismo "paso" entre columnas. Como cada gráfico de `sprites.h` ocupa
lo mismo y sus columnas `_a`, `_b`, `_c` van seguidas, la diferencia entre
`sprite_M_a` y `sprite_N_a` sirve **para las tres columnas a la vez**
(columna `_a` → columna `_a` del frame nuevo, etc.).

Por eso, en ZX, **cada frame de animación es un gráfico distinto del png**, y
cualquier frame nuevo tiene que tener la misma forma (`_a`, `_b`, `_c`
seguidas, del mismo tamaño).

---

## 8. Recetas: tu propio código con splib2

### 8.1. Crear un sprite propio

1. Pon el gráfico en el png de sprites (o escríbelo a mano en el mismo
   formato que `extrasprites.h`).
2. Créalo en `HOOK_GAME_INIT` (`custom.h`), que se ejecuta una vez al
   arrancar, después de `system_init ()`:

```c
// En config.h (o en custom.h, antes de los ganchos): #define HOOK_GAME_INIT
struct sp_SS *sp_mio;

void hook_game_init (void) {
	sp_mio = sp_CreateSpr (sp_MASK_SPRITE, 3, sprite_5_a, 1);
	sp_AddColSpr (sp_mio, sprite_5_b);
	sp_AddColSpr (sp_mio, sprite_5_c);
}
```

3. **Sube `NUMBLOCKS`** en `churromain.c`: 10 bloques más por cada sprite de
   16x16, 5 por cada uno de 8x8. Si faltan bloques, `sp_CreateSpr` devuelve
   `NULL` y el güego se cuelga al moverlo.
4. Muévelo cada frame con `sp_MoveSprAbs` (por ejemplo, desde
   `HOOK_ENTERING_SCREEN` o desde tu código de `custom.h`), con
   `SPRITES_CLIP` como clip.

### 8.2. Animar un sprite propio

Guarda el puntero al frame que se ve y pásale a `sp_MoveSprAbs` la diferencia
con el siguiente, como hace el motor con el jugador (sección 7).

### 8.3. Escribir en pantalla

- **`sp_PrintAtInv (fila, columna, atributo, tile)`**: escribe en la display
  list y marca la celda como sucia. Para texto, el tile es el ASCII menos 32;
  `print_str (x, y, color, texto)` lo hace con una cadena entera.
- **`draw_coloured_tile (x, y, t)`**: pinta un tile de 16x16 del tileset.

Si escribes directamente en la memoria de pantalla (16384), el siguiente
`sp_UpdateNow` lo borra en cuanto esas celdas se ensucien: la pantalla
*real* de splib2 es la display list. Para las pantallas fijas (título, final)
el motor descomprime directamente en la pantalla (`unpack_screen`) cuando no
hay sprites.

### 8.4. Entrada

Usa `sp_KeyPressed (código)` para teclas sueltas, o `pad0` y
`pad_this_frame` (sección 5.5) para el mando que haya elegido el jugador.

---

## 9. Trampas y límites

- **Memoria**: `NUMBLOCKS` da exactamente para el jugador, tres enemigos y
  las balas. Si creas más sprites, súbelo (sección 8.1).
- **El sprite no tiene color propio**: en modo Spectrum el atributo de la
  celda lo pone el tile de fondo; el sprite se dibuja con la tinta de esa
  celda. Con `FLASHASFG = 1` (en `SPconfig.inc`), splib2 no dibuja sprites
  sobre celdas con el bit 7 (FLASH) del atributo puesto: así se hacen los
  tiles que tapan a los sprites.
- **El orden de dibujo es por planos**: menor plano = delante. Todos los
  sprites del motor están en el plano 1.
- **El clip manda**: los sprites fuera de `spritesClip` no se dibujan.
- **`sp_UpdateNow` es lo único que pinta**: lo que escribas en la pantalla a
  mano sobrevive sólo hasta que se repinten esas celdas.
- **La interrupción**: el motor ya usa el ISR genérico de `0xF1F1` y su hook.
  Si añades otro, escríbelo como `isr_hook` (función `__naked` con `.dw 0`
  al principio, acabada en `or a` y `ret`) y regístralo con
  `sp_RegisterHook` pasando su dirección más 2.
- **No toques las estructuras** `sp_SS` y `sp_CS` a mano salvo que sepas lo
  que haces: la librería las recorre con desplazamientos fijos.

---

## 10. Índice rápido

| Función | Para qué | Dónde la usa el motor |
|---|---|---|
| `sp_InitIM2` | Tabla de vectores IM2 y modo 2. | `system_init ()` |
| `sp_CreateGenericISR` | Copia el ISR genérico (para encadenar hooks). | `system_init ()` |
| `sp_RegisterHook` | Añade un hook al ISR genérico. | `system_init ()` |
| `sp_Initialize` | Display list vacía, pantalla sucia, tablas de rotación. | `system_init ()` |
| `sp_Border` | Color del borde. | `system_init ()` |
| `sp_AddMemory` | Da bloques al asignador. | `system_init ()` |
| `sp_BlockAlloc`, `sp_FreeBlock` | Asignador de bloques (lo usa splib2 por dentro). | — |
| `sp_TileArray` | Apunta un tile a su gráfico. | `system_init ()` |
| `sp_PrintAtInv` | Escribe tile + atributo en una celda. | `draw_coloured_tile`, `print_number2`, `print_str`, `draw_objs`… |
| `sp_UpdateNow` | Repinta las celdas sucias. | `mainloop.h`, `pantallas.h`, `msc.h`… |
| `sp_CreateSpr`, `sp_AddColSpr` | Crea un sprite y le añade columnas. | `system_init ()` |
| `sp_MoveSprAbs` | Coloca un sprite. | `render_sprites`, `update_this_enemy`, `saca_a_todo_el_mundo_de_aqui` |
| `sp_JoyKeyboard`, `sp_JoyKempston`, `sp_JoySinclair1` | Leen el mando. | `pad_read`, `select_joyfunc` |
| `sp_KeyPressed` | Una tecla suelta. | `mainloop.h`, `engine.h`, `savegame.h` |
| `sp_GetKey`, `sp_WaitForNoKey` | Tecla pulsada; esperar a que se suelten. | menús y esperas |

### Ficheros relacionados

- `lib/splib2/` — la librería (fuente en ensamblador, `spritepack.h`,
  `sp.lst` con los módulos, `make.bat` y `make.sh`).
- `lib/splib2/SPconfig.inc` — la configuración con la que se ensambla la
  librería (`NOFLICKER = 1`, `FLASHASFG = 1`, `IM2TABLE = 0xF000`,
  `SProtatetbl = 0xF000`…).
- `src/dev/speccy/splib2.lib`, `src/dev/speccy/spritepack.h` — la librería
  compilada y su cabecera (las deja ahí `make.bat`).
- `lib/splib2/readme` — el README original de Sprite Pack 2.2.
- `src/dev/speccy/` — todo lo que usa splib2 (ver el principio).
- `src/dev/speccy/sprites.h` — los gráficos de los sprites (generado por
  `sprcnv`).
- `src/dev/speccy/extrasprites.h` — explosión, sprite vacío y bala.
- `src/utils/sprcnv.bas` — el generador de `sprites.h`.
