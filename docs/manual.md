# MTE MK1 v3.100 — Manual

Copyleft 2010-2014, 2026 by The Mojon Twins

## Qué es este documento

Es el manual de **MTE MK1 v3.100** ("la Churrera"), el motor para hacer
güegos de ZX Spectrum 48K / 128K y Amstrad CPC. Cuenta cómo hacer un güego
con él, desde instalar las herramientas hasta montar la cinta. Si algo de aquí
no coincide con `src/dev`, **manda el código**.

| Capítulo | Qué cuenta |
|---|---|
| [0](#capítulo-0---antes-de-empezar) | Instalar las herramientas, compilar el ejemplo, hacer un güego nuevo. |
| [1](#capítulo-1---el-tileset) | El tileset y el comportamiento de los tiles. |
| [2](#capítulo-2---el-mapa) | El mapa. |
| [3](#capítulo-3---los-sprites) | Los sprites. |
| [4](#capítulo-4---las-pantallas-fijas) | Título, marco, final y pantalla de carga. |
| [5](#capítulo-5---enemigos-y-hotspots) | Enemigos y *hotspots*. |
| [6](#capítulo-6---configurando-el-güego) | `config.h`, directiva por directiva. |
| [7](#capítulo-7---música-y-sonido) | Música y efectos. |
| [8](#capítulo-8---el-scripting-msc4) | El scripting (MSC4). |
| [9](#capítulo-9---código-propio-customh-y-externh) | Código propio: `custom.h` y `extern.h`. |
| [10](#capítulo-10---zx-spectrum-128k-y-juegos-con-niveles) | 128K y güegos de varios niveles. |
| [11](#capítulo-11---amstrad-cpc) | Amstrad CPC. |
| [12](#capítulo-12---tu-güego-aparte-del-motor-y-el-ejemplo-de-goku-mal) | Tu güego aparte del motor: `game.bat`, `convert.bat` y el ejemplo de Goku Mal. |
| [13](#capítulo-13---las-herramientas) | Referencia de las herramientas. |
| [14](#capítulo-14---game-boy-en-desarrollo) | Game Boy (en desarrollo). |
| [A](#apéndice-a---trabajar-en-linux) | Trabajar en Linux. |
| [B](#apéndice-b---mapa-de-memoria) | Mapa de memoria. |

Otros documentos:

* [`msc4.md`](msc4.md): el lenguaje de scripts, completo.
* [`formato-niveles.md`](formato-niveles.md): el formato de los niveles.
* [`lib-splib2.md`](lib-splib2.md), [`lib-cprslib.md`](lib-cprslib.md): las
  librerías gráficas de ZX y CPC.
* [`tecnico.md`](tecnico.md): notas técnicas, para quien quiera tocar el
  motor o probarlo.
* `examples/Goku Mal 128/README.md`: un güego de 128K con cinco niveles.

---

# Capítulo 0 - Antes de empezar

## Qué es MK1

MK1 es un *framework* para hacer juegos de habitaciones fijas (*flick
screen*) de 15x10 tiles de 16x16: plataformas (vista lateral) o aventuras
vistas desde arriba (la "vista genital"). Se compone de:

1. **El motor**, en C (SDCC, el compilador de GBDK-2020) con algo de
   ensamblador. Se gobierna con un
   archivo, `config.h`, en el que se dice qué partes del motor usa el güego y
   cómo se comportan.
2. **Las herramientas de conversión**, que convierten los gráficos (png), el
   mapa (Mappy), los enemigos (el `ponedor`) y los scripts en datos del güego.
3. **El scripting** (MSC4), para lo que no se puede hacer sólo configurando.
4. **El código propio** (`custom.h`, `extern.h`), para lo que no se puede
   hacer ni con lo anterior.

Lo que el motor sabe hacer sin tocar nada: movimiento con inercia
configurable; vista lateral (saltar, saltar siempre a lo Bootee, jetpac) o
vista genital; llaves y cerrojos; bloques empujables; disparos (en vista
lateral, también hacia arriba y en diagonal); muros rompibles; enemigos
lineales, plataformas móviles, voladores (*fanties*), perseguidores y un tipo
"custom" de ejemplo; tiles que matan y tiles que esconden; objetos
coleccionables, recargas de vida, de munición y de tiempo; temporizador;
puntos de control (*checkpoints*); tiles animados; sombras automáticas; pausa;
y, en 128K, música AY y varios niveles.

## Lo que necesitas

Todo lo necesario para trabajar en Windows está en este repositorio:

| Dónde | Qué es |
|---|---|
| `env/gbdk-win64.zip` | GBDK-2020 4.3.0: el compilador de C (SDCC), su ensamblador y su enlazador. El motor sólo usa eso (no es un güego de Game Boy). Las librerías del motor (`splib2` para ZX, `cpcrslib` para CPC) ya vienen compiladas en `src/dev/speccy` y `src/dev/cpc`. |
| `env/mappy-mojon.zip` | Mappy, el editor de mapas (capítulo 2). |
| `env/WYZTracker-0.5.0.2.zip` | WYZ Tracker 0.5.0.2, para hacer la música de **ZX Spectrum 128K** (capítulo 7). |
| `env/WYZTracker.2.0.1.2.7z` | WYZ Tracker 2.0.1.2, para hacer la música de **Amstrad CPC** (capítulo 7). |
| `env/cpc_pal.*` | La paleta del CPC para tu editor de gráficos (`.png`, `.act`, `.aco` y `.pal`). |
| `env/XVI32.zip` | Un editor hexadecimal, por si hay que mirar un binario. |
| `src/utils/` | Las herramientas de conversión (`ts2bin`, `mapcnv`, `ponedor`…) y el compilador de scripts (`msc4`), ya compiladas. |

Además te hará falta un editor de gráficos que guarde png (el que te guste),
un editor de textos y un emulador de Spectrum o de CPC para probar el güego.

## Instalar el entorno

1. Descomprime `env\gbdk-win64.zip` directamente en `C:\`. Tiene que
   quedar la carpeta `C:\gbdk`.
2. Descomprime donde quieras Mappy y el WYZ Tracker que vayas a usar.

Y ya está. Las herramientas de `src\utils` no hay que instalarlas.

Si prefieres tener GBDK-2020 en otro sitio, di dónde antes de compilar, en la
misma ventana de comandos:

```bat
set GBDK_HOME=D:\herramientas\gbdk
```

Si trabajas en Linux, mira el [apéndice A](#apéndice-a---trabajar-en-linux).

## La estructura del repositorio

```
src/                 <- el esqueleto de un güego (el ejemplo es Bootee)
  dev/               <- el motor y la configuración del güego
    config.h         <- la configuración (capítulo 6)
    custom.h         <- tu código: ganchos del motor (capítulo 9)
    extern.h         <- tu código: EXTERN, TEXT BOX y DIALOG del script
    comp-zx.bat      <- compila para ZX Spectrum
    comp-cpc.bat     <- compila para Amstrad CPC
    churromain.c     <- el programa principal (incluye todo lo demás)
    engine.h         <- el motor
    mainloop.h       <- el bucle principal
    msc.h            <- el intérprete de scripts
    levels.h         <- el sistema de niveles
    speccy/          <- lo específico de ZX (impresión, sprites, beeper...)
    speccy_128/      <- lo específico de ZX 128K (paginación, WYZ player)
    cpc/             <- lo específico de CPC
  gfx/speccy/        <- gráficos de ZX (png)
  gfx/cpc/           <- gráficos de CPC (png)
  map/               <- el mapa (mapa.fmp de Mappy y mapa.map exportado)
  enems/             <- los enemigos y hotspots (enems.ene)
  ogt/               <- la música (CPC, y zx128/ para ZX 128K)
  script/            <- el script (script.spt), si lo hay
  utils/             <- las herramientas
msc4/                <- el código fuente del compilador de scripts
examples/            <- güegos de ejemplo (Goku Mal 128)
tests/               <- pruebas del motor
env/                 <- lo que hay que instalar
docs/                <- la documentación
```

## Compilar el ejemplo

`src` es un güego completo, Bootee, listo para compilar:

1. Abre una ventana de comandos (tecla Windows + R, escribe `cmd` y pulsa
   Intro).
2. Ve a la carpeta `src\dev` del repositorio (cambia la ruta por la tuya):

   ```bat
   cd C:\MK1v3.100\src\dev
   ```

3. Compila:

   ```bat
   comp-zx.bat
   ```

   Sale `bootee.tap`, la cinta de Spectrum. Para CPC, `comp-cpc.bat`, que
   deja `bootee.sna` (una instantánea) y `bootee.cdt` (la cinta).
4. Abre la cinta en tu emulador.

`comp-zx.bat` lo hace todo:

1. Convierte los gráficos, el mapa y los enemigos (capítulos 1 a 5).
2. Si `config.h` define `ACTIVATE_SCRIPTING`, compila el script (capítulo 8).
3. Si el güego tiene niveles, los construye (capítulo 10).
4. En 128K, prepara el reproductor de música y reparte las pantallas y los
   niveles por las páginas de RAM (capítulo 10).
5. Compila el güego con SDCC y comprueba que cabe en memoria (`ihx2bin`).
6. Monta la cinta y borra los ficheros intermedios.

Si algo falla, se para y dice qué. Se le pueden dar dos opciones:

* `comp-zx.bat justcompile`: no convierte nada, sólo compila. Es más rápido
  cuando sólo has tocado el código o `config.h`.
* `comp-zx.bat noclean`: no borra los ficheros intermedios (útil para ver qué
  ha pasado).

## Hacer un güego nuevo

1. **Copia la carpeta `src` entera** a otro sitio, con el nombre de tu güego
   (por ejemplo `C:\juegos\miguego`). Cópiala entera: los scripts de
   compilación buscan las herramientas en `utils`, al lado de `dev`.
2. **Sustituye los recursos** de Bootee por los tuyos, con los mismos nombres:

   | Qué | Dónde | Capítulo |
   |---|---|---|
   | Tileset y fuente | `gfx\speccy\work.png`, `gfx\speccy\font.png` | 1 |
   | Mapa | `map\mapa.fmp` (Mappy) y `map\mapa.map` (exportado) | 2 |
   | Sprites | `gfx\speccy\sprites.png` | 3 |
   | Título, marco, final, carga | `gfx\speccy\title.png`, `marco.png`, `ending.png`, `loading.png` | 4 |
   | Enemigos y *hotspots* | `enems\enems.ene` | 5 |
   | Música (128K) | `ogt\zx128\` | 7 |
   | Script | `script\script.spt` | 8 |

3. **Edita `dev\comp-zx.bat`** con un editor de textos:
   * cambia `set game=bootee` por el nombre de tu güego (sin espacios: es el
     nombre de la cinta, `miguego.tap`, y el del programa que carga);
   * en la línea de `mapcnv`, pon el tamaño de tu mapa en pantallas (Bootee
     tiene 6x5; ver el capítulo 2):

     ```bat
     "%U%\mapcnv" ..\map\mapa.map mapa.h 6 5 15 10 15 packed > nul
     ```

4. **Configura `dev\config.h`** (capítulo 6): el tamaño del mapa (que tiene
   que ser el mismo que en `mapcnv`), la pantalla de inicio, cuántos objetos
   hay que coger, cómo se mueve el jugador, qué enemigos hay…
5. Si hace falta, escribe tu propio código en `dev\custom.h` y `dev\extern.h`
   (capítulo 9).
6. **Compila** con `comp-zx.bat`, como el ejemplo.

Lo normal es ir poco a poco: primero el tileset y el mapa, compilar y ver que
se mueve por él; luego los sprites; luego los enemigos…

Cuando el güego crezca, o cuando salga una versión nueva del motor, conviene
no tener los cambios mezclados con los ficheros del motor. El
[capítulo 12](#capítulo-12---tu-güego-aparte-del-motor-y-el-ejemplo-de-goku-mal)
cuenta cómo separarlos.

---

# Capítulo 1 - El tileset

El tileset es la colección de tiles de 16x16 con los que se dibujan las
pantallas. Se dibuja en un png de 256x48 (16 tiles por fila, 3 filas: 48
tiles), siguiendo las restricciones de color del Spectrum (dos colores por
cada cuadro de 8x8). En ZX va en `gfx/speccy/work.png`; en CPC, en
`gfx/cpc/work.png`.

Para la paleta del Spectrum usa valores de R, G, B de 200 para los colores
sin BRIGHT y de 255 para los de BRIGHT.

![Paleta del Spectrum](img/paleta-zx.png)

*Los colores del Spectrum para los conversores: arriba sin BRIGHT, abajo con BRIGHT.*


## 16 o 48 tiles

* **16 tiles** (mapa *packed*, lo normal): el mapa guarda cada tile en 4
  bits, así que ocupa la mitad. Los tiles 0-15 son los del mapa. Permite las
  sombras automáticas y el tile alternativo de fondo.
* **48 tiles** (`UNPACKED_MAP`): el mapa guarda un byte por tile y se pueden
  usar los 48. Sin sombras automáticas ni tile alternativo.

## Los tiles especiales

| Tile | Uso |
|---|---|
| 0 | El fondo principal (por convención). |
| 14 | El bloque empujable, con `PLAYER_PUSH_BOXES`. Su comportamiento debe ser 10. |
| 15 | El cerrojo, si hay llaves. Comportamiento 10. |
| 16 | Recarga de vida (*hotspot* de tipo 3). |
| 17 | Objeto (*hotspot* de tipo 1). |
| 18 | Llave (*hotspot* de tipo 2). |
| 19 | Fondo alternativo: en mapas *packed* el motor pinta a veces el 19 en lugar del 0 (`NO_ALT_TILE` lo desactiva). |
| 20 | Recarga de munición (*hotspot* de tipo 4, `MAX_AMMO`). |
| 21 | Recarga de tiempo (*hotspot* de tipo 5, `TIMER_ENABLE`). |
| 22 | Punto de control (*hotspot* de tipo 6, `ENABLE_CHECKPOINTS`). |
| 32-47 | Con `USE_AUTO_TILE_SHADOWS`: la versión sombreada de los tiles 0-15. |
| 47 | Lo usa `clear_gamearea_tiles ()` para borrar la zona de juego. |

Algunos tilesets de 16 tiles, con los especiales (16-19) detrás:

![Tileset de Dogmole](img/tileset-dogmole.png)

*Dogmole Tuppowski: no hay bloques empujables, así que el tile 14 es un mejillón.*


![Tileset de Lala Lah](img/tileset-lala.png)

*Lala Lah: fondo (0), plataformas de tipo 4, obstáculos, una bola de pinchos que mata, el cerrojo en el 15; los especiales; y en la fila de abajo, las versiones sombreadas.*


![Tileset de D'Veel'Ng](img/tileset-dveelng.png)

*D'Veel'Ng (vista genital): con caja empujable (14) y cerrojo (15), ambos de tipo 10.*


![Tileset de Monono](img/tileset-monono.png)

*Monono: sin sombras.*

Y uno de 48 tiles (`UNPACKED_MAP`):

![Tileset de Zombie Calavera](img/tileset-48-zombie.png)

*Zombie Calavera: sin llaves ni empujables; sólo el 16 (recarga) y el 17 (objeto) son especiales.*


El *hotspot* se pinta con el tile `16 + tipo` (salvo el de tipo 3, que es
el 16).

## El comportamiento de los tiles

Cada tile tiene un comportamiento. Sin niveles se define en
`comportamiento_tiles`, al final de `config.h`; con niveles, en un fichero
`behs.txt` por nivel (capítulo 10).

| Valor | Significado |
|---|---|
| 0 | Traspasable. |
| 1 | Traspasable y **mata** (quita vida al tocarlo). |
| 2 | Traspasable y **esconde**: quieto detrás de él, el jugador está escondido (los fanties le pierden la pista). |
| 4 | **Plataforma**: sólo para al jugador si cae encima (vista lateral). |
| 8 | **Obstáculo**: para al jugador por todos lados. |
| 10 | **Interactuable**: obstáculo especial; los cerrojos (tile 15) y el bloque empujable (tile 14). |
| 16 | **Rompible** con los disparos o los puñetazos (`BREAKABLE_WALLS`). Súmale 8 (24) para que además sea obstáculo. |
| 32 | **Cinta transportadora** (`ENABLE_CONVEYORS`): súmale 8 (o 4) para poder estar encima; con 1 más lleva a la derecha, sin él a la izquierda (40 izquierda, 41 derecha). |
| 128 | **Especial**: lanza la sección `SPECIAL TILE TOUCHED` del script cuando el centro del jugador está sobre él. Se puede sumar a los demás (132 = especial y plataforma). |

Los valores se suman: el motor comprueba los bits. Un 9 (obstáculo que mata)
no tiene sentido porque no se puede tocar; un 24 (obstáculo rompible) sí.

## Las sombras

* `USE_AUTO_TILE_SHADOWS`: las sombras se dibujan a mano. La fila de abajo
  del tileset (tiles 32-47) tiene la versión "sombreada" de los tiles 0-15, y
  el motor usa esa versión en los tiles que quedan a la sombra de un
  obstáculo.
* `USE_AUTO_SHADOWS`: sombras automáticas oscureciendo los atributos. No
  ocupan tiles, pero se ven peor.

Sólo una de las dos, y sólo con mapas *packed*.

![Tileset de Cheril Perils](img/tileset-sombras-perils.png)

*El tileset de Cheril Perils: en la fila de abajo, los tiles sombreados (32-47).*


![Sombras en Cheril Perils](img/sombras-perils.png)

*El resultado: los obstáculos proyectan sombra sobre el fondo.*


![Sombras en Lala Lah](img/sombras-lala.png)

*Lo mismo en Lala Lah.*


## La fuente y la conversión (ZX)

El motor usa 256 "caracteres" de 8x8: los 64 primeros son la fuente (ASCII
32-95) y los 192 siguientes los trozos de los 48 tiles. La fuente es un png de
256x16 (`gfx/speccy/font.png`).

![Fuente](img/fuente.png)

*Una fuente: 64 caracteres, del espacio (ASCII 32) al guión bajo (95).*

`ts2bin` junta el tileset y la fuente en `ts.bin` (2304 bytes: 2048 de
gráficos y 256 de atributos):

```bat
..\utils\ts2bin ..\gfx\speccy\font.png ..\gfx\speccy\work.png ts.bin 7
```

El último parámetro es la tinta que se usa cuando un cuadro de 8x8 tiene un
solo color. `ts.bin` lo incluye `speccy/tileset.h`.

En CPC la conversión es con `mkts_om` (capítulo 11).

## El tileset para Mappy

Mappy quiere que el primer tile sea negro. Si tu tile 0 no lo es, Mappy añade
uno y desplaza todos los demás: en ese caso hay que convertir el mapa con
`fixmappy` (capítulo 2). Otra opción es hacer un png aparte para Mappy con un
tile negro delante.

![Mappy añade un tile negro](img/mappy-tile-negro.png)

*Si el primer tile no es negro, Mappy mete uno delante y todos se desplazan.*


---

# Capítulo 2 - El mapa

El mapa es un rectángulo de `MAP_W` x `MAP_H` pantallas de 15x10 tiles. Se
hace con **Mappy** (la versión modificada de `env/`): tiles de 16x16, un mapa
de `MAP_W * 15` x `MAP_H * 10` tiles. Se guarda en dos formatos:

* `.fmp`: el formato de trabajo de Mappy. Es el que se abre para editar.
* `.map`: el formato que se convierte. Una ristra de bytes, un tile por
  byte, por filas. Guarda siempre los dos.

![Nuevo mapa en Mappy](img/mappy-nuevo.png)

*Un mapa nuevo en Mappy: tiles de 16x16 y el tamaño en tiles (aquí 90x50: 6x5 pantallas).*


![Mapa en Mappy](img/mappy-mapa.png)

*Haciendo el mapa.*


Cuánto puede ocupar el mapa depende de lo que ocupe todo lo demás. Un mapa
*packed* ocupa 75 bytes por pantalla; uno *unpacked*, 150. Con
`COMPRESSED_LEVELS` el mapa va comprimido en el nivel y en memoria sólo está
el del nivel actual.

## La conversión: `mapcnv`

```bat
..\utils\mapcnv ..\map\mapa.map mapa.h 6 5 15 10 15 packed
```

| Parámetro | Significado |
|---|---|
| `mapa.map` | El mapa exportado de Mappy. |
| `mapa.h` | La salida. |
| `6 5` | `MAP_W` y `MAP_H`: el tamaño del mapa en pantallas. |
| `15 10` | El tamaño de cada pantalla en tiles (siempre 15x10). |
| `15` | El tile de los cerrojos (15; pon uno que no exista, como 99, si no hay llaves). Los cerrojos se guardan aparte, en la tabla `cerrojos`. |
| `packed` | Mapa de 16 tiles (4 bits por tile). Sin `packed`, un byte por tile (`UNPACKED_MAP` en `config.h`). |
| `fixmappy` | Resta 1 a cada tile (si Mappy añadió un tile negro al principio). |

`comp-zx.bat` y `comp-cpc.bat` traen la llamada con los valores de Bootee
(6x5): cámbialos por los de tu mapa. `MAP_W` y `MAP_H` en `config.h` tienen
que coincidir.

Como máximo 85 pantallas (`MAP_W * MAP_H <= 85`; el motor usa índices de un
byte para los enemigos, 3 por pantalla).

---

# Capítulo 3 - Los sprites

El motor maneja cuatro sprites de 16x16 (el jugador y tres enemigos) y, si hay
disparos, hasta `MAX_BULLETS` sprites de 8x8 para las balas. Los gráficos están
en el *spriteset*: un png de 256x32 con 16 gráficos de 16x16, cada uno con su
máscara al lado (cada gráfico ocupa 32x16: el sprite y su máscara).

## El orden de los gráficos

**Vista lateral:**

| # | Gráfico |
|---|---|
| 0, 1, 2 | Jugador mirando a la derecha: andando (frames 1, 2, 3); el 1 es también "parado" |
| 3 | Jugador mirando a la derecha, saltando |
| 4, 5, 6 | Jugador mirando a la izquierda: andando |
| 7 | Jugador mirando a la izquierda, saltando |
| 8, 9 | Enemigo de tipo 1 (dos frames) |
| 10, 11 | Enemigo de tipo 2 |
| 12, 13 | Enemigo de tipo 3 |
| 14, 15 | Plataforma móvil (tipo 4) |

![Spriteset de Cheril Perils](img/spriteset-lateral-perils.png)

*Cheril Perils: la jugadora a la derecha (andar y saltar), a la izquierda, tres enemigos y la plataforma. Cada gráfico lleva su máscara al lado.*


![Spriteset de Dogmole](img/spriteset-dogmole.png)

*El de Dogmole.*


La animación de andar es 1, 2, 3, 2, 1… (con
`PLAYER_ALTERNATE_ANIMATION`, 1, 2, 3, 1, 2, 3…). Con `PLAYER_BOOTEE` los
frames son otros: ver `move ()` en `engine.h`.

**Vista genital:**

| # | Gráfico |
|---|---|
| 0, 1 | Jugador mirando a la derecha (dos frames) |
| 2, 3 | Izquierda |
| 4, 5 | Arriba |
| 6, 7 | Abajo |
| 8-15 | Cuatro tipos de enemigos, dos frames cada uno |

![Spriteset de El Hobbit](img/spriteset-genital-hobbit.png)

*El Hobbit (vista genital): dos frames por dirección y cuatro enemigos.*


![Spriteset de Mega Meghan](img/spriteset-genital-meghan.png)

*Mega Meghan.*


## La conversión

```bat
..\utils\sprcnv ..\gfx\speccy\sprites.png speccy\sprites.h [nomask]
```

genera `speccy/sprites.h`: los gráficos en una tabla `const` (`sprite_data`)
y `sprite_1_a` … `sprite_16_c` apuntando a cada columna. `nomask` genera los
sprites sin máscara (para `NO_MASKS`, que los pinta con OR). Si la salida
acaba en `.bin`, `sprcnv` escribe los mismos bytes en binario, que es lo que
se usa para los spritesets de los niveles (capítulo 10).

## Los sprites extra

La explosión (el sprite 17, cuando muere un enemigo), el sprite vacío (18) y
la bala (19, de 8x8) están en `speccy/extrasprites.h`, escritos como una
tabla `const` de C (gráfico y máscara, byte a byte). Un güego que quiera los suyos sustituye ese fichero
(Goku Mal lo hace). Con `PLAYER_CAN_PUNCH` están también los del puño: el
20 (hacia la derecha) y el 21 (hacia la izquierda), de 8x8. En CPC son pngs:
`gfx/cpc/sprites_extra.png`, `sprites_bullet.png` y `sprites_punch.png` (los
dos puños, uno junto a otro).

![Explosión](img/sprite-explosion.png)

*La explosión (16x16, con su máscara).*


![Bala](img/sprite-bala.png)

*La bala (8x8, con su máscara).*


---

# Capítulo 4 - Las pantallas fijas

* **La pantalla de carga** (`loading.png`): sólo se usa en la cinta.
* **El título** (`title.png`): con el menú de control (1 teclado, 2 Kempston,
  3 Sinclair).
* **El marco** (`marco.png`): la pantalla en la que se juega, con la zona de
  juego (30x20 caracteres a partir de `VIEWPORT_X`, `VIEWPORT_Y`) y los
  marcadores.
* **El final** (`ending.png`).

Son pngs de 256x192 que se convierten a pantallas de Spectrum (`png2scr`) y
se comprimen (`zx0`). Con `DIRECT_TO_PLAY` el título **es** el marco: el
juego empieza sobre la pantalla de título y no hay `marco.png`, lo que ahorra
una pantalla comprimida. Bootee lo hace así.

![Título de Lala the Magical beta](img/titulo-lala.png)

*Una pantalla de título, con las opciones de control.*


![Marco de Lala Prologue](img/marco-lala.png)

*Un marco: la zona de juego y los marcadores alrededor.*


![Título y marco de Dogmole](img/titulo-marco-dogmole.png)

*Título y marco en una sola pantalla (`DIRECT_TO_PLAY`), como en Dogmole.*


```bat
..\utils\png2scr ..\gfx\speccy\title.png title.scr
..\utils\zx0 title.scr title.bin
```

En 48K las pantallas comprimidas van dentro del binario (`pantallas.h`). En
128K son recursos en las páginas de RAM (`RES_TITLE`, `RES_MARCO`,
`RES_ENDING`, capítulo 10).

## Los marcadores

Se colocan con coordenadas de **carácter** en `config.h` (sección III):

| Directivas | Qué muestra |
|---|---|
| `LIFE_X`, `LIFE_Y` | La vida. |
| `OBJECTS_X`, `OBJECTS_Y` | Los objetos (si no `DEACTIVATE_OBJECTS`). Con `ONLY_ONE_OBJECT` y scripting, `OBJECTS_ICON_X/Y` dibuja un icono. |
| `KEYS_X`, `KEYS_Y` | Las llaves (si no `DEACTIVATE_KEYS`). |
| `KILLED_X`, `KILLED_Y` | Los enemigos muertos (`PLAYER_SHOW_KILLS`). |
| `AMMO_X`, `AMMO_Y` | La munición (`MAX_AMMO`). |
| `TIMER_X`, `TIMER_Y` | El temporizador (`PLAYER_SHOW_TIMER`). |
| `ITEM_X`, `ITEM_Y` | El objeto que se lleva (`GET ITEM SET` del script). |
| `LINE_OF_TEXT`, `LINE_OF_TEXT_X` | La línea de `TEXT "..."` del script. |

Un marcador con la X a 99 no se pinta: es la forma de tener un contador sin
mostrarlo (por ejemplo, objetos que cuentan para ganar pero que no se ven).

---

# Capítulo 5 - Enemigos y *hotspots*

En cada pantalla puede haber hasta **tres enemigos** y **un *hotspot***. Para
MK1, las plataformas móviles también son enemigos (cuentan para el máximo de
tres).

## Los tipos de enemigos

| Tipo | Comportamiento | Gráfico |
|---|---|---|
| 1, 2, 3 | **Lineal**: va de un punto a otro y vuelve. Si los dos puntos no están en la misma fila o columna, se mueve en diagonal rebotando dentro del rectángulo que forman. | Sprites 8-9, 10-11, 12-13 |
| 4 | Vista lateral: **plataforma móvil** (horizontal o vertical; el jugador se sube y le arrastra). Vista genital: un cuarto enemigo lineal. | 14-15 |
| 5 | **Fanty** (`ENABLE_RANDOM_RESPAWN`): enemigo volador que persigue al jugador acelerando y atraviesa el escenario. Normalmente no se colocan: aparecen solos en lugar de los enemigos muertos (1 de cada 32 frames por enemigo muerto). | El del tipo 3 |
| 6 | **Custom** (`ENABLE_CUSTOM_TYPE_6`): el ejemplo es un volador que, si el jugador está a menos de `SIGHT_DISTANCE` píxeles, le persigue, y si no, vuelve a su sitio (los murciélagos de Cheril the Goddess, los cerebros de Goku Mal). | `TYPE_6_FIXED_SPRITE` (el número del enemigo menos 1) |
| 7 | **Perseguidor** (`ENABLE_PURSUERS`): sale de su sitio y va a por el jugador sin atravesar el escenario; si muere, vuelve a salir al rato (`DEATH_COUNT_EXPRESSION` frames). | Al azar, o `TYPE_7_FIXED_SPRITE` |

La velocidad de los lineales y las plataformas va en píxeles por frame: 1, 2 o
4 (potencias de dos; otros valores dan problemas).

![Trayectoria lineal](img/enemigo-lineal.png)

*Un enemigo lineal va y viene entre el inicio y el fin.*


![Trayectoria diagonal](img/enemigo-diagonal.png)

*Si el inicio y el fin no están alineados, rebota en diagonal dentro del rectángulo.*

Los fanties y los de tipo 6
usan `FANTY_MAX_V` y `FANTY_A` (en 1/256 de píxel por frame).

Los enemigos se pueden matar pisándolos (`PLAYER_KILLS_ENEMIES`) o
disparándoles (`PLAYER_CAN_FIRE`). Con `ENEMS_LIFE_GAUGE` aguantan varios
disparos. `PLAYER_MIN_KILLABLE` / `FIRE_MIN_KILLABLE` limitan qué tipos se
pueden matar.

Con `WALLS_STOP_ENEMIES`, los lineales se paran contra los obstáculos (y
contra todo lo que no sea traspasable con `EVERYTHING_IS_A_WALL`).

## Los *hotspots*

Una casilla por pantalla donde hay algo que coger:

| Tipo | Tile | Qué es |
|---|---|---|
| 1 | 17 | Objeto: suma 1 a `player.objs`. |
| 2 | 18 | Llave: suma 1 a `player.keys`. Con llaves, tocar un cerrojo (tile 15) gasta una y lo abre. |
| 3 | 16 | Recarga de vida (`PLAYER_REFILL`). |
| 4 | 20 | Recarga de munición (`MAX_AMMO`, `AMMO_REFILL`). |
| 5 | 21 | Recarga de tiempo (`TIMER_REFILL`). |
| 6 | 22 | Punto de control (`ENABLE_CHECKPOINTS`). |

Las recargas de vida tienen dos lógicas:

* Por defecto, una vez cogido el objeto o la llave de una pantalla, cada vez
  que se vuelve a entrar en ella hay una posibilidad entre cuatro de que
  aparezca una recarga de vida en su lugar.
* Con `USE_HOTSPOTS_TYPE_3`, las recargas aparecen sólo donde las pongas
  (*hotspots* de tipo 3).

Como sólo hay un *hotspot* por pantalla, el total de objetos y llaves no
puede pasar del número de pantallas. Planea cuántos cerrojos vas a poner.

Con `ONLY_ONE_OBJECT` sólo se puede llevar un objeto: si ya se lleva uno, el
*hotspot* no desaparece.

## El `ponedor`

Los enemigos y *hotspots* se colocan con el `ponedor` (`src\utils\ponedor.exe`),
que lee el mapa y el tileset:

```bat
ponedor.exe enems.ene
ponedor.exe new out=enems.ene map=mapa.map tiles=work.png size=6,5 scrsize=15,10 [adjust=1]
```

La primera forma abre un `.ene` para editarlo; la segunda crea uno nuevo.

`scrsize=15,10` es obligatorio para MK1 (por defecto son 16x12). `adjust=1`
si Mappy añadió un tile negro.

![Ponedor: crear](img/ponedor-nuevo.png)

*Crear un `.ene` nuevo desde la ventana del `ponedor`: tamaño del mapa, de la pantalla (15x10), 3 enemigos, `adjust`, tileset, mapa y salida.*


![Ponedor: abrir](img/ponedor-abrir.png)

*O abrir uno que ya existe.*

Un clic en una casilla empieza un enemigo
(pide el tipo); otro clic, donde acaba su trayectoria (pide la velocidad en
`Attr`). Para los tipos 5, 6 y 7 sólo importa la casilla de inicio. Los
*hotspots* se ponen con el botón derecho.

![Ponedor: velocidad](img/ponedor-velocidad.png)

*Al marcar el final de la trayectoria se pide la velocidad (`Attr`).*


![Ponedor: editar enemigo](img/ponedor-enemigo.png)

*Un clic en el inicio de un enemigo lo edita o lo borra.*


![Ponedor: hotspot](img/ponedor-hotspot.png)

*El tipo del *hotspot*.*

La parte de arriba de la ventana
dice `2b` o `3b`: el formato de los *hotspots* en el `.ene` (2 o 3 bytes); la
tecla `L` lo cambia.

## La conversión: `ene2h`

```bat
..\utils\ene2h ..\enems\enems.ene enems.h 2bytes
```

genera `enems.h` con las tablas `malotes []` (los enemigos) y `hotspots []`.
`2bytes` es para los `.ene` con *hotspots* de 2 bytes (los de Bootee). Con
niveles, los enemigos y *hotspots* van en el bundle del nivel
(`buildlevel`, capítulo 10).

---

# Capítulo 6 - Configurando el güego

Todo el comportamiento del motor se elige en `dev/config.h` con directivas
`#define`. Las que no se usan se dejan comentadas (`//#define`).

## I. Configuración general

| Directiva | Qué es |
|---|---|
| `MODE_128K` | Compila para ZX Spectrum 128K (capítulo 10). Se ignora en CPC. |
| `MAP_W`, `MAP_H` | Tamaño del mapa en pantallas. Con niveles, el máximo de pantallas de un nivel es `MAP_W * MAP_H`. |
| `SCR_INICIO` | Pantalla de inicio. |
| `PLAYER_INI_X`, `PLAYER_INI_Y` | Casilla de inicio. |
| `SCR_FIN` | Pantalla final (99 = no hay). |
| `PLAYER_FIN_X`, `PLAYER_FIN_Y` | Casilla a la que hay que llegar en la pantalla final. |
| `PLAYER_NUM_OBJETOS` | Objetos que hay que recoger para terminar. |
| `PLAYER_LIFE` | Vida inicial y máxima. |
| `PLAYER_REFILL` | Vida que da cada recarga. |
| `GAME_FRAME_TICKS` | Interrupciones (1/50 s) por frame de juego: 2 = 25 fps fijos. 0 = sin sincronizar, lo más rápido posible. En CPC, el equivalente `MIN_FAPS_PER_FRAME` sale de aquí. |
| `COMPRESSED_LEVELS` | Varios niveles (sólo con `MODE_128K`, capítulo 10). |
| `MAX_LEVELS` | Número de niveles. |
| `REFILL_ME` | Con niveles: recarga la vida al empezar cada nivel. |

**Cómo se gana:** cuando se han recogido `PLAYER_NUM_OBJETOS` objetos (con
niveles, los `max_objs` del nivel) y, si hay pantalla final, se está en su
casilla. El script puede ganar con `WIN GAME`, y un güego puede poner su
propia condición con `HOOK_WIN_CONDITION` (capítulo 9). **Se pierde** al
quedarse sin vida, con `GAME OVER` del script o, con `TIMER_GAMEOVER_0`, al
acabarse el tiempo.

## II. Tipo de motor

### Caja de colisión

| Directiva | Qué es |
|---|---|
| `BOUNDING_BOX_8_BOTTOM` | Caja de 8x8 abajo y centrada en el sprite (lo normal en vista lateral). |
| `BOUNDING_BOX_8_CENTERED` | Caja de 8x8 en el centro (para vista genital). |
| *(ninguna)* | Caja de 16x16. |
| `SMALL_COLLISION` | Colisión con enemigos de 8x8 en lugar de 12x12. |

![Cajas de colisión](img/colision.png)

*`BOUNDING_BOX_8_CENTERED` (izquierda) y `BOUNDING_BOX_8_BOTTOM` (derecha).*


### Directivas generales

| Directiva | Qué es |
|---|---|
| `PLAYER_CHECK_MAP_BOUNDARIES` | No deja salirse del mapa (si el mapa no tiene paredes en los bordes). |
| `DIRECT_TO_PLAY` | El título es también el marco del juego. |
| `DEACTIVATE_KEYS` | Sin llaves ni cerrojos. |
| `DEACTIVATE_OBJECTS` | Sin objetos. |
| `ONLY_ONE_OBJECT` | Sólo se puede llevar un objeto a la vez. |
| `OBJECT_COUNT` | Con scripting: el flag que cuenta los objetos (en vez de `player.objs`). |
| `DEACTIVATE_EVIL_TILE` | Los tiles de comportamiento 1 no matan. |
| `FULL_BOUNCE` | Al tocar algo que mata, el rebote es de `PLAYER_MAX_VX` (si no, la mitad de la velocidad). |
| `PLAYER_BOUNCES` | Al tocar algo que mata, el jugador rebota. |
| `SLOW_DRAIN` | Con `PLAYER_BOUNCES`: la vida baja 4 veces más despacio. |
| `PLAYER_FLICKERS` | Al tocar algo que mata, el jugador parpadea un rato y es invulnerable (en lugar de rebotar). |
| `MAP_BOTTOM_KILLS` | Salirse del mapa por abajo mata. |
| `WALLS_STOP_ENEMIES` | Los enemigos chocan con el escenario. |
| `EVERYTHING_IS_A_WALL` | Con lo anterior: cualquier tile que no sea 0 es pared (si no, sólo los 8). |
| `ENABLE_PURSUERS` | Enemigos de tipo 7. |
| `DEATH_COUNT_EXPRESSION` | Frames que tarda en volver un perseguidor muerto (p. ej. `20+(rand()&15)`). |
| `TYPE_7_FIXED_SPRITE` | Gráfico fijo para los de tipo 7. |
| `ENABLE_CUSTOM_TYPE_6` | Enemigos de tipo 6. |
| `TYPE_6_FIXED_SPRITE` | Su gráfico (número de enemigo menos 1). |
| `SIGHT_DISTANCE` | Distancia, en píxeles, a la que ven al jugador. |
| `USE_TWO_BUTTONS` | Teclado de dos botones: W A S D, N salta, M dispara. |
| `USE_HOTSPOTS_TYPE_3` | Las recargas de vida sólo salen donde se ponen. |
| `DONT_LIMIT_LIFE` | Las recargas de vida pueden pasar de `PLAYER_LIFE`. |
| `DIE_AND_RESPAWN` | Al perder una vida se vuelve al último sitio seguro: donde se pisó suelo por última vez (o lo que diga `SAFE x, y` en el script). Antes, `HOOK_PLAYER_DIES` (o un sonido y una pausa). Sólo vista lateral. |
| `ENABLE_CONVEYORS` | Cintas transportadoras (comportamiento 32), a `CONVEYOR_SPEED` (256 = 1 píxel por frame). |
| `TILE_GET`, `TILE_GET_FLAG` | El tile `TILE_GET` se coge al pasar por encima (monedas) y suma 1 al flag `TILE_GET_FLAG` (necesita scripting). |
| `TYPE_6_KILL_ON_TOUCH` | Los de tipo 6 desaparecen al tocar al jugador. |
| `ENABLE_SHOOTERS` | Enemigos de tipo 8: se mueven como los lineales y disparan al jugador. `TYPE_8_FIXED_SPRITE`, `TYPE_8_SHOOT_FREQ` (disparan si `(rand () & FREQ) == 1`), `TYPE_8_SAFE_DISTANCE` (más cerca no disparan), `COCO_SPEED_8`. |
| `ENABLE_CLOUDS` | Enemigos de tipo 9: siguen al jugador en horizontal a la velocidad `|mx|` y dejan caer cosas. `TYPE_9_FIXED_SPRITE`, `TYPE_9_SHOOT_FREQ`, `TYPE_9_SAFE_DISTANCE`, `COCO_SPEED_9`. |
| `MAX_COCOS`, `TYPE_8_FIRE_ONE` | Proyectiles de los tipos 8 y 9 en pantalla (usan el sprite de la bala) y, con `TYPE_8_FIRE_ONE`, uno por enemigo. |
| `KEYS_CUSTOM` | (ZX) Las teclas del juego: fire, right, left, down, up, con los códigos de `sp_LookupKey`. `KEY_ALSO_UP`: otra tecla que también hace de ARRIBA. |

### Bloques empujables

| Directiva | Qué es |
|---|---|
| `PLAYER_PUSH_BOXES` | El tile 14 (comportamiento 10) se empuja. En vista lateral sólo en horizontal. |
| `FIRE_TO_PUSH` | Hay que pulsar FIRE además de la dirección. |

Con scripting, empujar un bloque lanza la sección `TILE PUSHED`.

### Disparos

| Directiva | Qué es |
|---|---|
| `PLAYER_CAN_FIRE` | Activa los disparos. |
| `PLAYER_CAN_FIRE_FLAG` | Con scripting: sólo se dispara si este flag vale 1. |
| `PLAYER_BULLET_SPEED` | Velocidad de las balas (píxeles por frame). |
| `MAX_BULLETS` | Balas en pantalla a la vez. Cada una gasta memoria de sprites. |
| `PLAYER_BULLET_Y_OFFSET`, `PLAYER_BULLET_X_OFFSET` | Desde dónde salen. |
| `ENEMS_LIFE_GAUGE` | Disparos que aguanta un enemigo. |
| `LIMITED_BULLETS` | Las balas desaparecen tras unos frames: `LB_FRAMES` fijos, o los que diga el flag `LB_FRAMES_FLAG`. |
| `RESPAWN_ON_ENTER` | Los enemigos muertos resucitan al volver a entrar en la pantalla. |
| `FIRE_MIN_KILLABLE` | Sólo se pueden matar a tiros los enemigos de tipo >= N. |
| `CAN_FIRE_UP` | Vista lateral: disparar hacia arriba (con ARRIBA) y en diagonal. Mejor con `USE_TWO_BUTTONS`. |
| `MAX_AMMO` | Munición limitada (y su marcador). `AMMO_REFILL`: lo que da cada recarga; `INITIAL_AMMO`: con cuánta se empieza. |
| `BREAKABLE_WALLS` | Los tiles de comportamiento 16 se rompen a tiros (o a puñetazos); `BREAKABLE_WALLS_LIFE`: cuántos golpes de más aguantan (sin él, se rompen al primero). |
| `BREAKABLE_ANIM` | El muro se ve como `BREAKABLE_TILE` durante `MAX_BREAKABLE_FRAMES` frames antes de desaparecer (`MAX_BREAKABLE` a la vez). |
| `BREAKABLE_TILE_GET` | Al romperse ese tile, a veces deja un `TILE_GET`: si `(rand () & BREAKABLE_TILE_FREQ) <= BREAKABLE_TILE_FREQ_T`. |
| `PERSISTENT_BREAKABLE` | Lo roto sigue roto al volver a la pantalla (con niveles). |
| `PLAYER_CAN_PUNCH` | En lugar de disparar, FIRE da un puñetazo (sprites 20 y 21, ver el capítulo 3) que quita una vida a los enemigos y rompe muros. No va con `PLAYER_CAN_FIRE`. |
| `ENABLE_RANDOM_RESPAWN` | Fanties en lugar de los enemigos muertos. `FANTY_MAX_V`, `FANTY_A` (también para el tipo 6) y `FANTIES_LIFE_GAUGE`. |

En vista lateral, sin disparos se salta con FIRE; con disparos o puñetazos,
con ARRIBA (o con N si `USE_TWO_BUTTONS`).

### Scripting

| Directiva | Qué es |
|---|---|
| `ACTIVATE_SCRIPTING` | Activa el scripting (capítulo 8). |
| `SCRIPTING_DOWN` | La tecla de acción es ABAJO. |
| `SCRIPTING_KEY_M` | La tecla de acción es M. Sin ninguna de las dos, FIRE. |
| `MAX_FLAGS` | Más flags de los que usa el script. |
| `ITEM_X`, `ITEM_Y` | Dónde se pinta el objeto que se lleva (`GET ITEM SET`). |

Lo demás (`EXTERN`, la zona de fuego, `TIMER ZERO`…) se activa solo según lo
que use el script.

### Temporizador

| Directiva | Qué es |
|---|---|
| `TIMER_ENABLE` | Activa el temporizador. |
| `TIMER_INITIAL` | Valor inicial (máximo 99). |
| `TIMER_REFILL` | Lo que dan las recargas de tiempo (*hotspot* 5). |
| `TIMER_LAPSE` | Frames entre cada decremento. |
| `TIMER_START` | Empieza en marcha. |
| `TIMER_GAMEOVER_0` | Al llegar a 0, fin de la partida. |
| `TIMER_KILL_0` | Al llegar a 0, se pierde una vida. Con `TIMER_WARP_TO` (y `TIMER_WARP_TO_X`, `_Y`), además se va a esa pantalla. |
| `TIMER_AUTO_RESET` | Vuelve a empezar tras llegar a 0. |
| `SHOW_TIMER_OVER` | Cartel "TIME'S UP!". |

Con scripting, al llegar a 0 se lanza la sección `TIMER ZERO` si el script la
tiene, y la variable `TIMER` del script es el temporizador.

### Puntos de control

| Directiva | Qué es |
|---|---|
| `ENABLE_CHECKPOINTS` | Los *hotspots* de tipo 6 guardan el estado (pantalla, posición, flags, munición, tiempo). Al acabar la partida, el menú ofrece "1 START / 2 CONTINUE". |
| `CP_RESET_WHEN_DYING` | Al perder una vida, se vuelve al último punto de control. |
| `CP_RESET_ALSO_FLAGS` | Y se restauran los flags. |

Las llaves y los objetos no se guardan: está pensado para güegos llevados por
el script.

### Vista genital

| Directiva | Qué es |
|---|---|
| `PLAYER_MOGGY_STYLE` | Vista desde arriba. |
| `TOP_OVER_SIDE` | En diagonal, manda ARRIBA/ABAJO. |
| `PLAYER_BOUNCE_WITH_WALLS` | Rebota contra las paredes. |

### Vista lateral

| Directiva | Qué es |
|---|---|
| `PLAYER_HAS_JUMP` | Salta. |
| `PLAYER_HAS_JETPAC` | Vuela con un jetpac (`PLAYER_INCR_JETPAC`, `PLAYER_MAX_VY_JETPAC`). |
| `PLAYER_BOOTEE` | Salta siempre, como Bootee (no uses también `PLAYER_HAS_JUMP` ni `PLAYER_HAS_JETPAC`). ABAJO hace más corto el salto (`PLAYER_BOOTEE_CROUCH`). |
| `PLAYER_CUMULATIVE_JUMP` | Con `PLAYER_HAS_JUMP`: manteniendo el salto se salta más alto en cada rebote. |
| `PLAYER_HAS_SWIM` | Nada: sin gravedad, ARRIBA sube, ABAJO baja y sin tocar nada se flota hacia arriba (`PLAYER_MAX_VSWIM`, `PLAYER_ASWIM`). Con `PLAYER_HAS_JUMP` también, cada nivel dice si se salta o se nada (`buildlevel engine=0` o `1`). |
| `PLAYER_KILLS_ENEMIES` | Pisar a un enemigo lo mata. |
| `PLAYER_STOMPS_ON_ENEMIES` | Pisar a un enemigo hace rebotar sin matarlo. |
| `PLAYER_CAN_KILL_FLAG` | Con scripting: sólo se mata pisando si este flag vale 1. |
| `PLAYER_MIN_KILLABLE` | Sólo se pueden pisar los de tipo >= N. |
| `PLAYER_STEP_SOUND` | Ruido de pasos (no en Bootee). |

## III. Configuración de la pantalla

`VIEWPORT_X`, `VIEWPORT_Y`: la esquina de la zona de juego (30x20
caracteres), y las coordenadas de los marcadores (capítulo 4). Además:

| Directiva | Qué es |
|---|---|
| `PLAYER_SHOW_KILLS`, `PLAYER_SHOW_TIMER` | Mostrar esos contadores. |
| `LINE_OF_TEXT`, `LINE_OF_TEXT_X`, `LINE_OF_TEXT_ATTR` | Fila, columna y color del `TEXT` del script. |
| `USE_AUTO_SHADOWS` | Sombras por atributos. |
| `USE_AUTO_TILE_SHADOWS` | Sombras con los tiles 32-47. |
| `UNPACKED_MAP` | Mapa de 48 tiles, un byte por tile. |
| `NO_MASKS` | Sprites sin máscara (OR). Más rápido; feo sobre fondos con mucho dibujo. |
| `NO_ALT_TILE` | No sale el tile 19 en lugar del 0. |
| `PLAYER_ALTERNATE_ANIMATION` | Animación de andar 1, 2, 3, 1, 2, 3… |
| `MASKED_BULLETS` | Balas con máscara. |
| `ENABLE_TILANIMS` | Tiles animados: el valor es el primer tile animado. Van por parejas (40-41, 42-43…); en el mapa se pone el primero de la pareja y el motor va cambiando al azar entre los dos. Como mucho 64 por pantalla. |
| `PAUSE_ABORT` | H pausa, Y abandona la partida. |
| `GET_X_MORE` | Al coger un objeto, un cartel con los que faltan. |

## IV. El movimiento del jugador

Las posiciones van en coma fija **8.8**: 256 unidades son un píxel. Así que
las velocidades están en 1/256 de píxel por frame, y las aceleraciones en
1/256 de píxel por frame². En vista genital sólo se usan los valores
horizontales (para los dos ejes).

| Directiva | Ejemplo | Qué es |
|---|---|---|
| `PLAYER_MAX_VY_CAYENDO` | 2048 | Velocidad máxima de caída (8 píxeles/frame). |
| `PLAYER_G` | 128 | Gravedad (0,5 píxeles/frame²). |
| `PLAYER_VY_INICIAL_SALTO` | 256 | Velocidad al empezar el salto. |
| `PLAYER_MAX_VY_SALTANDO` | 1280 | Velocidad máxima de subida. |
| `PLAYER_INCR_SALTO` | 192 | Aceleración mientras se mantiene el salto. |
| `PLAYER_INCR_JETPAC` | 192 | Empuje del jetpac (mayor que `PLAYER_G`). |
| `PLAYER_MAX_VY_JETPAC` | 1024 | Velocidad máxima del jetpac. |
| `PLAYER_BOOTEE_CROUCH` | 512 | Bootee: lo que se suma a la velocidad al pulsar ABAJO. |
| `PLAYER_MAX_VX` | 1024 | Velocidad horizontal máxima. |
| `PLAYER_AX` | 192 | Aceleración horizontal. |
| `PLAYER_RX` | 256 | Rozamiento (frenada al soltar). |

## V. El comportamiento de los tiles

`comportamiento_tiles []`, 48 valores (ver el capítulo 1). Con
`COMPRESSED_LEVELS` no se usa: cada nivel trae los suyos.

---

# Capítulo 7 - Música y sonido

Los efectos se tocan con `PLAY_SFX (n)`. Los números son los mismos en todas
las versiones:

| n | Efecto | Lo usa el motor para |
|---|---|---|
| 0 | Enemigo destruido | |
| 1 | Enemigo tocado | Pausa (128K) |
| 2 | "Algo" | Menús, pantalla de nivel, checkpoints, game over |
| 3 | Salto | Saltos, pisar sin matar |
| 4 | Jugador tocado | Tocar a un enemigo |
| 5 | Enemigo destruido 2 | Pisar y matar |
| 6 | Disparo | |
| 7 | Objeto | Objetos, recargas de munición y tiempo |
| 8 | Llave | |
| 9 | Vida | Recargas de vida |
| 10 | Puñetazo | Tiles que matan |
| 11 | Moneda | |
| 12, 13 | Hablar | |
| 14 | Cerrojo | Abrir un cerrojo |

## ZX Spectrum 48K: beeper

`speccy/beeper.h` tiene los efectos (de Shiru). La música del título se hace
con Beepola, usando el motor *Phaser1*.

![Beepola](img/beepola.png)

*Beepola: la música del título de 48K se exporta como listado en ensamblador.*

Para cambiarla, compila la canción en Beepola con el motor Phaser1 como listado
en ensamblador y guárdalo como `ogt/beepola.asm`. `comp-zx`
lo convierte con `beepola2s` en `dev/speccy/music.s` cada vez que compilas. Si
no hay `ogt/beepola.asm`, se usa el `music.s` que haya.

Mientras suena un efecto el juego se para (el
beeper usa la CPU entera), así que los efectos se tocan entre `di` y `ei`.

## La música: WYZ Tracker

En 128K y en CPC la música es del WYZ player, y se compone con **WYZ
Tracker**. Cada máquina usa una versión distinta, y los ficheros de una no
valen para la otra:

| Máquina | Versión de WYZ Tracker | Dónde está |
|---|---|---|
| ZX Spectrum 128K | **0.5.0.2** | `env/WYZTracker-0.5.0.2.zip` |
| Amstrad CPC | **2.0.1.2** | `env/WYZTracker.2.0.1.2.7z` |

![WYZ Tracker](img/wyztracker.png)

*WYZ Tracker, con el que se hacen las canciones y los instrumentos del WYZ player.*

## ZX Spectrum 128K: WYZ player

La música y los efectos los toca el WYZ player desde la interrupción, en la
página 1 de RAM. `comp-zx.bat` lo ensambla (`speccy_128/wyz/wyzplayer.asm`)
con los datos del güego, que se buscan en `../ogt/zx128/` (o en `../ogt/`):

| Fichero | Qué es |
|---|---|
| `instrumentos.asm` | Instrumentos y pautas (los exporta WYZ Tracker 0.5.0.2). |
| `canciones.asm` | `SONG_0`… (con `INCBIN` de los `.mus`) y `TABLA_SONG`. |
| `efectos.asm` | Opcional: `EFECTO0`… y `TABLA_EFECTOS`. Si no está, los 15 efectos de MK1 de `speccy_128/wyz/efectos.asm`. |
| `*.mus` | Las canciones exportadas de WYZ Tracker 0.5.0.2. |

Las canciones se tocan con `wyz_play_music (n)` (n es su posición en
`TABLA_SONG`): 0 en el título, 1 en el juego (con niveles, la del nivel) y 2
en el game over. `wyz_stop_sound ()` para la música. Un güego con sus propios
efectos debe hacer que su `TABLA_EFECTOS` tenga las 15 entradas en el orden de
la tabla de arriba (el ejemplo de Goku Mal hace corresponder sus 9 efectos
con los números de MK1 así).

## Amstrad CPC

También el WYZ player (`cpc/wyz_player.s`), con la música hecha con WYZ
Tracker 2.0.1.2 y los datos en `../ogt/`: `instrumentos.asm` (que
`wyzTrackerParser` convierte en el módulo `instrumentos.s` cada vez que
compilas), los efectos de `cpc/efectos.s` (los 15 de la tabla de arriba) y las
canciones comprimidas que lista `cpc/songs.h` (0 título, 1 juego, 2 game
over).

---

# Capítulo 8 - El scripting (MSC4)

Cuando configurar no basta, tenemos el script. Es un lenguaje de *reacción*: el motor
lanza una **sección** del script cuando pasa algo (se entra en una pantalla,
se pulsa la tecla de acción, se coge un objeto, se mata a un enemigo…) y la
sección comprueba condiciones y ejecuta acciones:

```
ENTERING SCREEN 3
	IF %PUERTA_ABIERTA = 0
	THEN
		SET TILE (7, 4) = 13
	END
END

PRESS FIRE AT SCREEN 3
	IF PLAYER TOUCHES 6, 4
	IF OBJS >= 5
	THEN
		SET TILE (7, 4) = 0
		%PUERTA_ABIERTA = 1
		SOUND 7
	END
END
```

El lenguaje completo (todas las secciones, comandos y variables, cuándo lanza
el motor cada sección, `extern.h`, los niveles) está en [`msc4.md`](msc4.md).
Aquí va lo justo para empezar.

## Ponerlo en marcha

1. En `config.h`: `#define ACTIVATE_SCRIPTING` (y, si quieres,
   `SCRIPTING_DOWN` o `SCRIPTING_KEY_M` para la tecla de acción).
2. Escribe el script en `script/script.spt`.
3. `comp-zx.bat`. El script se compila solo, con `msc4`, antes que el
   güego. El intérprete es `dev/msc.h`, en C, y sólo se compila lo que el
   script usa.

Si el script tiene errores, `comp-zx.bat` se para y muestra lo que dice
msc4.

## Las secciones

| Sección | Cuándo |
|---|---|
| `ENTERING GAME` | Al empezar la partida (con niveles, cada nivel). |
| `ENTERING ANY` | Al entrar en cualquier pantalla. |
| `ENTERING SCREEN n` | Al entrar en la pantalla `n` (después de `ENTERING ANY`). |
| `PRESS FIRE AT ANY` | Al pulsar la tecla de acción (o dentro de la zona de fuego). |
| `PRESS FIRE AT SCREEN n` | Lo mismo, en la pantalla `n`. |
| `PLAYER GOT SOMETHING` | Al coger un *hotspot* (`HOTSPOT` dice de qué tipo). |
| `PLAYER KILLS ENEMY` | Al morir un enemigo. |
| `ENEMY TOUCHED` | Al tocar a un enemigo. |
| `SPECIAL TILE TOUCHED` | Cada frame que el jugador está en un tile de comportamiento 128. |
| `TILE PUSHED` | Al empujar un bloque. |
| `TILE DESTROYED` | Al romper un tile. |
| `TIMER ZERO` | Cuando el temporizador llega a 0. |

## Flags

El estado del script son los **flags**: `$0`, `$1`… (bytes de 0 a 255). Con
`ALIAS %NOMBRE = n` se les pone nombre. Los flags se ponen a 0 al empezar la
partida; con niveles, al empezar cada nivel. Desde C se leen como `flags [n]`.

## Texto y diálogos

* `TEXT "..."` escribe una línea en `LINE_OF_TEXT` (configurable en
  `config.h`).
* `TEXT BOX "..."` y `$F = DIALOG "A", "B", "C"` los muestra el güego: el
  intérprete descodifica el texto y llama a `text_box ()` o `dialog_box ()` de
  `extern.h` (capítulo 9). `tests/script/extern.h` tiene un ejemplo.

## Varios scripts

Con niveles, cada nivel tiene el suyo (capítulo 10). Se compilan todos juntos
listándolos en `dev/scripts.txt`, para que el intérprete tenga lo que
necesitan todos.

---

# Capítulo 9 - Código propio: `custom.h` y `extern.h`

Dos ficheros son del güego, no del motor:

* **`custom.h`**: los *ganchos* (hooks) del bucle principal, y cualquier
  código o dato propio del güego.
* **`extern.h`**: lo que el script llama (`EXTERN`, `TEXT BOX`, `DIALOG`).

## Los ganchos de `custom.h`

Un gancho es una función que el motor llama en un momento concreto si se
define su `HOOK_*`. Un gancho que no se define no ocupa nada.

| Gancho | Función | Cuándo |
|---|---|---|
| `HOOK_GAME_INIT` | `void hook_game_init (void)` | Una vez, al arrancar. Logos, idioma… |
| `HOOK_AFTER_TITLE` | `unsigned char hook_after_title (void)` | Tras la pantalla de título. Con niveles devuelve el nivel inicial (menús, contraseñas); puede cambiar también la vida y los flags. La música del título sigue sonando: la para el gancho. |
| `HOOK_LEVEL_INTRO` | `void hook_level_intro (void)` | Con niveles, sustituye a la pantalla "LEVEL XX" antes de cada nivel. Va antes de cargar el nivel: puede usar la pantalla y el tileset. |
| `HOOK_LEVEL_START` | `void hook_level_start (void)` | Con el nivel cargado, justo antes de jugar. |
| `HOOK_ENTERING_SCREEN` | `void hook_entering_screen (void)` | Al entrar en cada pantalla, ya pintada. |
| `HOOK_EACH_FRAME` | `void hook_each_frame (void)` | Cada frame, antes de volcar la pantalla. Puede acabar el nivel: `playing = 0` y `success = LEVEL_REPEAT` (se repite), `LEVEL_CLEARED` o `LEVEL_FAILED`. |
| `HOOK_PLAYER_DIES` | `void hook_player_dies (void)` | Con `DIE_AND_RESPAWN`, al perder una vida y antes de volver al sitio seguro (un sample, una animación). |
| `HOOK_WIN_CONDITION` | `unsigned char hook_win_condition (void)` | Cada frame: distinto de 0 si se ha superado el nivel. Sustituye a la condición normal (`WIN GAME` del script sigue valiendo). |
| `HOOK_LEVEL_END` | `void hook_level_end (void)` | Al superar un nivel (o el juego, sin niveles). |
| `HOOK_GAME_OVER` | `void hook_game_over (void)` | Sustituye a `game_over ()`. |
| `HOOK_GAME_ENDING` | `void hook_game_ending (void)` | Sustituye a `game_ending ()`. |

Ejemplo:

```c
#define HOOK_LEVEL_START
void hook_level_start (void) {
	print_str (VIEWPORT_X + 9, VIEWPORT_Y + 9, 71, "GET READY!");
	sp_UpdateNow ();
	espera_activa (50);
}
```

`custom.h` se incluye después del motor, así que se puede usar todo lo del
motor. El ejemplo completo es `examples/Goku Mal 128/dev/custom.h`, que hace
con estos ganchos todo lo que el Goku Mal original cambiaba dentro del motor.

## `extern.h`

Sólo se incluye si algún script usa `EXTERN`, `TEXT BOX` o `DIALOG`:

```c
void do_extern_action (unsigned char n, unsigned char m);   // EXTERN n, m
void text_box (void);              // TEXT BOX: el texto en msc_text_buf
unsigned char dialog_box (void);   // DIALOG: msc_options [0..2], msc_n_options;
                                   // devuelve 1, 2 o 3
```

## Lo que se puede usar del motor

Las variables y funciones más útiles:

| Qué | Qué es |
|---|---|
| `player` | El jugador: `x`, `y` (8.8), `vx`, `vy`, `life`, `objs`, `keys`, `killed`, `ammo`, `estado`… |
| `gpx`, `gpy` | Posición del jugador en píxeles (se calculan cada frame de `player.x`, `player.y`). |
| `set_player_at (x, y)` | Pone al jugador en (x, y) píxeles. |
| `n_pant`, `o_pant` | Pantalla actual y anterior. Cambiar `n_pant` cambia de pantalla. |
| `level` | Nivel actual (con niveles). |
| `LEVEL_MAP_W`, `LEVEL_MAX_OBJS`… | Datos del nivel actual (ver capítulo 10). |
| `flags []` | Los flags del script. |
| `qtile (x, y)`, `attr (x, y)` | Tile y comportamiento de la casilla (x, y) de la pantalla. |
| `set_map_tile (x, y, tile, comportamiento)` | Cambia una casilla (y la pinta). |
| `draw_coloured_tile (x, y, tile)` | Pinta un tile en coordenadas de carácter. |
| `print_str (x, y, color, cadena)` | Escribe un texto. |
| `print_number2 (x, y, n)` | Escribe un número de dos cifras. |
| `sp_UpdateNow ()` | Vuelca a pantalla lo pintado. |
| `espera_activa (frames)` | Espera, o hasta que se pulse una tecla. |
| `sp_WaitForNoKey ()`, `sp_KeyPressed (tecla)` | Teclado. |
| `PLAY_SFX (n)` | Efecto de sonido. |
| `redraw_scr ()` | Repinta la pantalla actual sin reiniciarla (con `PAUSE_ABORT`, `GET_X_MORE` o textos del script). |
| `clear_gamearea_tiles ()` | Borra la zona de juego (existe con niveles o con `ENABLE_CHECKPOINTS`). |
| `get_resource (RES_X, dirección)` | 128K: descomprime un recurso. |
| `wyz_play_music (n)`, `wyz_stop_sound ()` | 128K y CPC: música. |
| `gpit`, `gpjt`, `gpaux`, `rdx`, `rdy`… | Variables auxiliares globales (el motor las usa también: no confíes en su valor entre llamadas). |

Unas reglas de SDCC que conviene saber al escribir código propio:

* **Las variables globales no pueden llevar valor inicial.** El motor no las
  copia al arrancar (sólo las pone a cero), y `ihx2bin` da un error si
  aparece alguna. Las tablas que no cambian se declaran `const` (van con el
  código); las que cambian, se rellenan en el código (por ejemplo, con
  `memcpy` desde una tabla `const`, al empezar la partida).
* Las cadenas y tablas que se pasan a funciones del motor son `const`:
  `const unsigned char *`.
* El ensamblador va dentro de `__asm` … `__endasm;`, con la sintaxis de
  `sdasz80` (`ld a, #5` para los números, `ld a, 3(ix)`, etiquetas con `:`).
  Si va dentro de una función normal, tiene que dejar los registros como los
  encontró; lo cómodo es ponerlo en una función entera de ensamblador,
  `__naked`, que acaba en `ret`. Las variables de C se llaman igual con `_`
  delante (`_gpit`).
* En una función `__naked` el primer argumento llega en A (si es de 8 bits) o
  en HL (si es de 16) y se devuelve en A (8 bits) o DE (16 bits). Para los
  demás argumentos, mira la convención `__sdcccall(1)` en el manual de SDCC
  (`sdccman.pdf`, en la carpeta de GBDK-2020).
* Con `AT (dirección)` delante de una declaración, la variable va en esa
  dirección (`AT (BASE_CUSTOM) unsigned char mis_cosas [16];`).
* Las variables globales siguen siendo algo más rápidas que las locales en
  muchos casos, y `gpit`, `gpjt`… están ahí para eso.

---

# Capítulo 10 - ZX Spectrum 128K y juegos con niveles

## El modo 128K

Con `#define MODE_128K`:

* la música y los efectos los toca el WYZ player (capítulo 7);
* las pantallas fijas y los niveles van **comprimidos en las páginas 3, 4, 6
  y 7** de RAM y se descomprimen cuando hacen falta con
  `get_resource (RES_X, dirección)`;
* la cinta lleva un cargador que coloca cada página en su sitio.

`comp-zx.bat` lo hace todo: ensambla el WYZ player en `RAM1.bin` y genera
`wyz_addrs.h`; reparte con `librarian` los recursos de `dev/librarian.txt`
(si no hay, `title.bin`, `marco.bin` y `ending.bin`) en `RAM3.bin`… y genera
`librarian.h` con un `#define RES_<NOMBRE>` por recurso (el nombre del
archivo sin extensión: `level1c.bin` → `RES_LEVEL1C`); comprueba que lo que se
usa con otra página puesta queda por debajo de 0xC000; y monta la cinta.

En 128K la pila va por debajo del programa (24200) y nada que se use con otra
página en 0xC000 (la pila, el descompresor, la interrupción, los buffers de
nivel, el tileset y los sprites) puede estar en 0xC000-0xFFFF. Para eso las
variables del motor van delante de su código, y el descompresor, la
interrupción, el tileset y los sprites van al principio del código; el resto
del código sí puede pasar de 0xC000. Si el programa crece tanto que algo de
lo que no puede pasa de 0xC000, `comp-zx.bat` da un error (lo comprueba
`ihx2bin`).

## Juegos con niveles

Con `MODE_128K`, `COMPRESSED_LEVELS` y `MAX_LEVELS`, el güego tiene varios
niveles. Cada nivel tiene:

* un **bundle** con los datos de juego (cabecera, comportamientos, cerrojos,
  *hotspots*, enemigos y mapa), que genera `buildlevel`;
* opcionalmente, su **tileset** y su **spriteset**, como recursos aparte (que
  pueden compartir varios niveles);
* su **música** (el número de canción);
* opcionalmente, su **script**.

Cada nivel puede tener un mapa de distinto tamaño. `MAP_W * MAP_H` de
`config.h` es el máximo de pantallas (y fija el tamaño de los buffers).

El formato está descrito en [`formato-niveles.md`](formato-niveles.md).

### Construir los niveles: `levels.bat`

Si en `dev\` hay un `levels.bat`, `comp-zx.bat` lo llama antes de repartir los
recursos por las páginas de RAM. Es donde se construyen los niveles: para
cada uno, el bundle con `buildlevel`, y si lleva tileset o spriteset propios,
esos también; y todo se comprime con `zx0`:

```bat
@echo off
rem Nivel 1: bundle, tileset y spriteset
"%U%\buildlevel" map=..\map\mapa1.map ene=..\enems\enems1.ene behs=behs1.txt ^
	out=level1.bin maxpant=25 scr_ini=0 ini_x=2 ini_y=7 max_objs=10 life=3 2bytes > nul || exit /b 1
"%U%\ts2bin" ..\gfx\font.png ..\gfx\work1.png ts1.bin 7 > nul || exit /b 1
"%U%\sprcnv" ..\gfx\sprites1.png spr1.bin > nul || exit /b 1

rem zx0 no sobrescribe: se borra antes la salida
for %%f in (level1 ts1 spr1) do (
	if exist %%fc.bin del %%fc.bin
	"%U%\zx0" %%f.bin %%fc.bin > nul || exit /b 1
)
exit /b 0
```

`%U%` es la carpeta de las herramientas (la pone `comp-zx.bat`). Cada línea
acaba en `|| exit /b 1`, que para la compilación si esa herramienta falla, y
el fichero acaba en `exit /b 0`. Los `.bin` comprimidos (`level1c.bin`,
`ts1c.bin`, `spr1c.bin`) se ponen en `dev\librarian.txt`, uno por línea, para
que vayan a las páginas de RAM; cada uno se convierte en un
`RES_<NOMBRE>` (`RES_LEVEL1C`, `RES_TS1C`…) para la tabla de niveles.
El `levels.bat` de Goku Mal (capítulo 12) construye cinco niveles con una
subrutina.

`behs1.txt` tiene los 48 comportamientos separados por comas. Los parámetros
de `buildlevel` están en el capítulo 13.

### La tabla de niveles: `levelset.h`

```c
const LEVEL levels [MAX_LEVELS] = {
	// bundle      tileset   spriteset  música  script
	{ RES_LEVEL1C, RES_TS1C, RES_SPR1C, 3,      NO_RESOURCE },
	{ RES_LEVEL2C, RES_TS2C, RES_SPR2C, 4,      NO_RESOURCE },
};
```

`NO_RESOURCE` en el tileset o el spriteset deja los que haya (los del nivel
anterior o los del binario); ojo si se puede volver a un nivel anterior (al
volver a empezar la partida, por ejemplo): entonces cada nivel debe decir los
suyos.

### Los datos del nivel

El motor usa siempre `LEVEL_MAP_W`, `LEVEL_MAP_H`, `LEVEL_SCR_INI`,
`LEVEL_INI_X`, `LEVEL_INI_Y`, `LEVEL_MAX_OBJS`, `LEVEL_ENEMS_LIFE`,
`LEVEL_SCR_FIN`, `LEVEL_FIN_X` y `LEVEL_FIN_Y`: con niveles salen de la
cabecera del nivel; sin niveles, de `config.h`.

### El flujo de una partida con niveles

1. Título; `HOOK_AFTER_TITLE` elige el nivel inicial (por defecto el 0).
2. Para cada nivel: `HOOK_LEVEL_INTRO` (o la pantalla "LEVEL XX"),
   `prepare_level ()` (descomprime el bundle, el tileset, el spriteset y el
   script), se colocan jugador, enemigos y objetos, `ENTERING GAME` del
   script, la música del nivel, `HOOK_LEVEL_START`, y a jugar.
3. Al superarlo, `HOOK_LEVEL_END` y el siguiente nivel; tras el último,
   `HOOK_GAME_ENDING` (o `game_ending ()`). Al perder, `HOOK_GAME_OVER` (o
   `game_over ()`).
4. El script puede saltar a otro nivel (`WARP TO LEVEL`, que con su último
   parámetro se salta la presentación) o terminar el juego (`GAME ENDING`), y
   un gancho puede pedir que se repita el nivel (`LEVEL_REPEAT`).

Otras opciones para juegos con niveles: `LEVEL_TILESETS_NO_FONT` (los
tilesets de los niveles, hechos con `ts2bin nofont`, se cargan sin pisar la
fuente), `KEEP_FLAGS_BETWEEN_LEVELS` (los flags duran toda la partida),
`SCRIPT_TEXTS_AS_RESOURCE` (los textos de los scripts van en un recurso,
`text.bin`, en vez de en la RAM) y `TITLE_MUSIC`.

### Ejemplos

* `examples/Goku Mal 128/`: un güego completo de cinco niveles, con
  cinemáticas, contraseñas y su propia música y efectos (capítulo 12).
* `examples/Ninjajar/`: un güego enorme de 24 niveles con scripts, textos
  (en un recurso), mapa del mundo, contraseñas, lava y cinemáticas.
* `tests/levels/`: Bootee partido en dos niveles de distinto tamaño, con y
  sin scripts.

---

# Capítulo 11 - Amstrad CPC

El mismo motor compila para CPC (`comp-cpc.bat`) con la librería `cpcrslib`
(versión de los Mojon Twins) en lugar de `splib2`. Lo propio del CPC está en
`dev/cpc/`. Las diferencias:

* Los gráficos son pngs con la paleta del CPC (`gfx/cpc/pal.png`, modo 0 por
  defecto: `set mode=0` en `comp-cpc.bat`). Para dibujarlos, carga en tu
  editor la paleta de `env/cpc_pal.*`. Se convierten con `mkts_om` (así
  está en `comp-cpc.bat`, donde `%P%` es
  `platform=cpc cpcmode=0 pal=..\gfx\cpc\pal.png`):

  ```bat
  "%U%\mkts_om" %P% mode=chars greyordered in=..\gfx\cpc\font.png out=font.bin silent
  "%U%\mkts_om" %P% mode=strait2x2 greyordered in=..\gfx\cpc\work.png out=work.bin silent
  "%U%\mkts_om" %P% mode=sprites in=..\gfx\cpc\sprites.png out=sprites.bin max=16 silent
  "%U%\mkts_om" %P% mode=superbuffer in=..\gfx\cpc\title.png out=title.scr silent
  "%U%\mkts_om" platform=cpc mode=pals in=..\gfx\cpc\pal.png prefix=my_inks out=cpc\pal.h silent
  ```

* La música es del WYZ player, hecha con WYZ Tracker 2.0.1.2 (capítulo 7).
* La sincronía de frames la hace `sp_UpdateNow ()` (`MIN_FAPS_PER_FRAME`, que
  sale de `GAME_FRAME_TICKS`).
* La salida es `bootee.sna` (para emuladores) y una cinta `bootee.cdt` con
  cargador.
* No hay modo 128K ni niveles en CPC (`MODE_128K` se ignora).
* Los buffers del motor viven en los huecos de la memoria de vídeo
  (`cpc/sysvars.h`). El programa y sus variables tienen que acabar antes de
  0x8800, donde empiezan los buffers fijos; `ihx2bin` lo comprueba.
* La librería (`cpcrslib.lib`, en `dev/cpc`) tiene una variante "fg"
  (`cpcrslib_fg.lib`) con la que los sprites pueden pasar por detrás de los
  tiles que se marquen; ver `lib/cpcrslib-mt/README.md`.

---

# Capítulo 12 - Tu güego aparte del motor, y el ejemplo de Goku Mal

## El problema

Si haces tu güego como cuenta el capítulo 0, tus cambios quedan mezclados con
los ficheros del motor: has tocado `comp-zx.bat` para cambiar el nombre y las
conversiones, y `dev\` tiene a la vez tus ficheros (`config.h`, `custom.h`…)
y los del motor (`engine.h`, `mainloop.h`…). Para un güego pequeño no pasa
nada. Pero cuando salga una versión nueva del motor y quieras usarla, tendrás
que acordarte de qué ficheros eran tuyos y de qué cambiaste en
`comp-zx.bat`.

Para eso, `comp-zx.bat` busca en `dev\` unos ficheros opcionales con todo lo
que es propio de tu güego. Si existen, los usa; si no, hace lo de Bootee. Así
no hay que tocar `comp-zx.bat` nunca.

## Los ficheros de tu güego

| Fichero | Para qué | Si no está |
|---|---|---|
| `game.bat` | El nombre del güego. | `bootee` |
| `convert.bat` | La conversión de los gráficos, el mapa y los enemigos. | La de Bootee (la que hay escrita en `comp-zx.bat`). |
| `levels.bat` | Construir los niveles (capítulo 10). | No hay niveles. |
| `librarian.txt` | Lo que va en las páginas de RAM, en 128K (capítulo 10). | `title.bin`, `marco.bin` y `ending.bin`. |
| `scripts.txt` | La lista de scripts (capítulo 8). | `..\script\script.spt` |

`comp-zx.bat` los usa en este orden:

1. Lee `game.bat`.
2. Convierte: con `convert.bat` si existe; si no, como Bootee. (Con
   `justcompile` se salta este paso.)
3. Compila los scripts, si `config.h` define `ACTIVATE_SCRIPTING`.
4. Llama a `levels.bat`.
5. En 128K, ensambla la música y reparte lo de `librarian.txt` por las
   páginas de RAM.
6. Compila y monta la cinta.

Estos ficheros son sólo para ZX (`comp-zx.bat`). Para CPC se edita
`comp-cpc.bat` directamente.

### `game.bat`

Es una sola línea, con el nombre del güego:

```bat
set game=miguego
```

El nombre no puede llevar espacios. La cinta será `miguego.tap`, y el
programa que se ve al cargarla, `MIGUEGO`.

### `convert.bat`

Hace lo mismo que la parte de "convertir" de `comp-zx.bat`, pero con tus
ficheros y tus parámetros. Para un güego como Bootee pero con un mapa de 8x4
pantallas sería:

```bat
@echo off
rem Mapa y enemigos
"%U%\mapcnv" ..\map\mapa.map mapa.h 8 4 15 10 15 packed > nul || exit /b 1
"%U%\ene2h" ..\enems\enems.ene enems.h 2bytes > nul || exit /b 1

rem Tileset, fuente y sprites
"%U%\ts2bin" ..\gfx\speccy\font.png ..\gfx\speccy\work.png ts.bin 7 > nul || exit /b 1
"%U%\sprcnv" ..\gfx\speccy\sprites.png speccy\sprites.h > nul || exit /b 1

rem Pantallas fijas: a formato Spectrum y comprimidas
for %%s in (title marco ending loading) do (
	"%U%\png2scr" ..\gfx\speccy\%%s.png %%s.scr > nul || exit /b 1
)
for %%s in (title marco ending) do (
	if exist %%s.bin del %%s.bin
	"%U%\zx0" %%s.scr %%s.bin > nul || exit /b 1
)
exit /b 0
```

Cosas que hay que saber para escribirlo:

* **`%U%`** es la carpeta de las herramientas (`src\utils`). La pone
  `comp-zx.bat` antes de llamar a `convert.bat`. Las rutas son relativas a
  `dev\`, que es donde se ejecuta.
* **`> nul`** esconde lo que escribe cada herramienta. Si algo no funciona,
  quítalo para ver qué dice.
* **`|| exit /b 1`** al final de una línea quiere decir "si esto falla, para
  aquí y avisa del error". Así `comp-zx.bat` se entera y no sigue compilando
  con datos a medias.
* **`exit /b 0`** al final dice que todo ha ido bien.
* `zx0` no sobrescribe un fichero que ya existe: por eso se borra antes
  (`if exist ... del ...`).
* Dentro de un `.bat`, las variables de un `for` se escriben con dos `%`
  (`%%s`).

Un `convert.bat` puede convertir lo que quiera: más pantallas, otros nombres
de fichero… Lo único que tiene que dejar en `dev\` es lo que el motor espera:
`mapa.h`, `enems.h`, `ts.bin`, `speccy\sprites.h`, `loading.scr` y las
pantallas comprimidas que se usen (`title.bin`…). Con niveles, el mapa y los
enemigos van en los niveles (capítulo 10), y `convert.bat` no los convierte.

## Tu güego en su propia carpeta

Con estos ficheros se puede ir más lejos: que tu güego no tenga ni siquiera
una copia del motor. Tu carpeta sólo tiene lo tuyo, y un `make.bat` que, al
compilar, junta una copia del motor actual con tus ficheros. Es lo que hace
Goku Mal.

## El ejemplo de Goku Mal

`examples\Goku Mal 128` es un güego completo de 128K: cinco niveles, cada uno
con su mapa, su tileset y sus sprites; cinemáticas, contraseñas, pantalla de
zona, su propia música y sus efectos. Todo lo propio del güego va en ganchos
de `custom.h` (capítulo 9).

### Compilarlo

1. Abre una ventana de comandos y ve a la carpeta del ejemplo (las comillas hacen falta por los espacios
   del nombre; cambia la ruta por la tuya):

   ```bat
   cd "C:\MK1v3.100\examples\Goku Mal 128"
   ```

2. Compila:

   ```bat
   make.bat
   ```

   Tarda un poco: convierte las pantallas, construye los cinco niveles,
   ensambla la música y compila. Al final dice `gokumal.tap listo`.
4. Abre `gokumal.tap` en un emulador de **Spectrum 128K**.

`make.bat noclean` deja todos los ficheros intermedios en `build\dev`, por
si quieres ver qué se ha generado.

### Qué hay en la carpeta

```
Goku Mal 128\
  make.bat           <- compila el güego
  dev\               <- SÓLO los ficheros de dev que son del güego
    game.bat         <- set game=gokumal
    convert.bat      <- las pantallas, el tileset y los sprites del nivel 1
    levels.bat       <- construye los cinco niveles
    librarian.txt    <- lo que va en las páginas de RAM
    levelset.h       <- la tabla de niveles
    config.h         <- la configuración del motor para Goku Mal
    custom.h         <- todo su código propio
    speccy\extrasprites.h <- su explosión y su bala
  gfx\               <- gráficos (png)
  map\               <- los cinco mapas
  enems\             <- los enemigos de cada mapa
  levels\            <- los comportamientos de los tiles de cada mapa
  ogt\zx128\         <- su música y sus efectos para el WYZ player
```

No hay ni `engine.h`, ni `mainloop.h`, ni `comp-zx.bat`, ni `utils`.

### Qué hace `make.bat`

1. Borra `build\` (si existe) y la vuelve a crear.
2. Copia **todo** `src\dev` del repositorio a `build\dev`: el motor actual,
   con `comp-zx.bat` y los ficheros de Bootee.
3. Copia **encima** los ficheros de `dev\` de Goku Mal. Los que se llaman
   igual (`config.h`, `custom.h`…) sustituyen a los de Bootee; los nuevos
   (`game.bat`, `convert.bat`, `levels.bat`…) se añaden.
4. Enlaza `build\utils` con `src\utils` y `build\gfx`, `build\map`… con las
   carpetas del güego (con `mklink /J`, un enlace a una carpeta que no
   necesita permisos de administrador). Así, para `comp-zx.bat`, `build\`
   tiene la misma forma que `src\`.
5. Llama a `build\dev\comp-zx.bat`, que encuentra `game.bat`,
   `convert.bat` y `levels.bat` y los usa.
6. Copia `gokumal.tap` a la carpeta del güego.

Cuando el motor cambie, Goku Mal se compila con el nuevo sin tocar nada.

### Su `convert.bat`

Convierte el tileset y los sprites del nivel 1 (los que van dentro del
binario), la pantalla de carga y todas las pantallas fijas, que en Goku Mal
son muchas (título, final, zonas, siete cinemáticas, logos…):

```bat
"%U%\ts2bin" ..\gfx\font.png ..\gfx\work1.png ts.bin 7 > nul || exit /b 1
"%U%\sprcnv" ..\gfx\sprites1.png speccy\sprites.h > nul || exit /b 1
"%U%\png2scr" ..\gfx\loading.png loading.scr > nul || exit /b 1
for %%s in (title ending zoneA zoneB intro1 intro2 intro3 intro4 intro5 intro6 intro7 logo controls dedicado) do (
	"%U%\png2scr" ..\gfx\%%s.png %%s.scr > nul || exit /b 1
	if exist %%s.bin del %%s.bin
	"%U%\zx0" %%s.scr %%s.bin > nul || exit /b 1
)
```

No convierte ni mapa ni enemigos: van en los niveles.

### Su `levels.bat`

Los cinco niveles se construyen igual, así que `levels.bat` tiene una
subrutina, `:build`, y la llama una vez por nivel con sus datos:

```bat
rem         nivel mapa scr_ini ini_x ini_y max_objs vida
call :build 1 1 24  2 7 99 3 || exit /b 1
call :build 2 2  0  4 1 99 4 || exit /b 1
...
exit /b 0

:build
"%U%\buildlevel" map=..\map\mapa%2.MAP ene=..\enems\enems%2.ene behs=..\levels\behs%2.txt ^
	out=level%1.bin maxpant=25 scr_ini=%3 ini_x=%4 ini_y=%5 max_objs=%6 life=%7 lock=99 2bytes > nul || exit /b 1
"%U%\ts2bin" ..\gfx\font.png ..\gfx\work%2.png ts%1.bin 7 > nul || exit /b 1
"%U%\sprcnv" ..\gfx\sprites%2.png spr%1.bin > nul || exit /b 1
...
```

Dentro de la subrutina, `%1`, `%2`… son los números que se le pasan en el
`call`: `%1` el nivel, `%2` el mapa, etc. Los niveles van en el orden del
güego, que no es el de los mapas: el nivel 4 es el mapa 5.

`librarian.txt` lista lo que sale de aquí (`level1c.bin`, `ts1c.bin`,
`spr1c.bin`…) junto con las pantallas, y `levelset.h` lo junta en la tabla de
niveles (capítulo 10).

### Hacer lo mismo con tu güego

1. Crea una carpeta para tu güego con `gfx`, `map`, `enems`, `ogt`… como
   necesites, y una carpeta `dev` con **sólo** tus ficheros: `config.h`,
   `game.bat`, y lo que cambies (`convert.bat`, `custom.h`, `extern.h`,
   `levels.bat`, `librarian.txt`…).
2. Copia el `make.bat` de Goku Mal y cambia, cerca del final, `gokumal.tap`
   por el nombre de tu cinta. Si tu carpeta no está dentro de `examples`,
   cambia también la línea que busca el repositorio (`..\..` es "dos
   carpetas más arriba").
3. Compila con `make.bat`.

---

# Capítulo 13 - Las herramientas

Están todas en `src\utils`. Normalmente no hay que llamarlas a mano: lo hacen
`comp-zx.bat`, `comp-cpc.bat` y tus `convert.bat` y `levels.bat`.

| Herramienta | Uso |
|---|---|
| `ts2bin font.png work.png ts.bin tinta` | Tileset de ZX (2304 bytes). `nofont`, `notiles` o `blank` en lugar de un png. |
| `mapcnv mapa.map mapa.h W H 15 10 cerrojo [packed] [fixmappy]` | Mapa a `mapa.h` (tabla `const` y los cerrojos iniciales). |
| `ene2h enems.ene enems.h [2bytes]` | Enemigos y *hotspots* a `enems.h` (tablas `const` con el estado inicial y sus copias en RAM). |
| `sprcnv sprites.png sprites.h [nomask]` | Spriteset de ZX. Con salida `.bin`, el binario (spritesets por nivel). |
| `png2scr imagen.png imagen.scr` | Pantalla de 256x192 a formato Spectrum. |
| `zx0 entrada salida` | Compresor (el descompresor está en `dev/zx0.h`). |
| `buildlevel map= ene= behs= out= maxpant= scr_ini= ini_x= ini_y= [max_objs=] [life=] [scr_fin= fin_x= fin_y=] [mapw= maph=] [unpacked] [lock=15] [2bytes] [fixmappy] [noswap]` | Bundle de un nivel. `maxpant` es `MAP_W * MAP_H`; el tamaño del mapa sale del `.ene` (o de `mapw`/`maph`); `lock=99` si no hay cerrojos. |
| `librarian list=lista.txt out=librarian.h [dir=salida] [pages=3,4,6,7]` | Reparte recursos en páginas de RAM de 128K. |
| `librarian platform=gb list=lista.txt out=librarian.h [firstbank=3]` | Reparte recursos en bancos de ROM de Game Boy (un `res_bankN.s` por banco). |
| `gbcheck juego.map [stack=512]` | Game Boy: comprueba que el banco 0, cada banco de ROM y la RAM (con la pila) caben. |
| `msc4 in=a.spt[,b.spt] v=3_100 output=c [rooms=N]` | Compila los scripts (ver `msc4.md`). |
| `mkts_om platform=cpc ...` | Conversor de gráficos de CPC. |
| `mkts_om platform=gb mode=chars\|strait2x2\|sprites\|scr ...` | Conversor de gráficos de Game Boy (capítulo 14). |
| `wyzTrackerParser instrumentos.asm instrumentos.s` | Los instrumentos de WYZ Tracker 2.0 a un módulo de ensamblador (CPC). |
| `beepola2s beepola.asm music.s` | La exportación de Beepola a un módulo de ensamblador (la música del título de 48K). |
| `ihx2bin juego.ihx juego.bin dirección [juego.map [128k]]` | Saca el binario del enlazador y comprueba el mapa de memoria. |
| `pasmo` | Ensamblador (el WYZ player de 128K, el cargador de 128K y los de CPC). |
| `bin2tap`, `bas2tap` | Cintas de ZX. |
| `cpctbin2sna`, `cpc2cdt`, `zx7`, `imanol` | Instantáneas, cintas y cargadores de CPC. |
| `ponedor` | El editor de enemigos (capítulo 5). |
| `rle44map_sp`, `rle53map_sp`, `rle62map_sp` | Conversores de mapas a formatos RLE (no los usa el motor). |

---

# Capítulo 14 - Game Boy (en desarrollo)

El port de Game Boy está a medio hacer: esto es lo que hay de momento y se
irá completando. El objetivo es que el mismo juego (con sus gráficos de Game
Boy) funcione igual que en ZX y CPC, en un cartucho MBC1 de DMG.

Ya funcionan el motor, la pantalla del juego con su cámara, los sprites, el
marcador, los niveles (`COMPRESSED_LEVELS`), los scripts y los textos:
`bootee` y Ninjajar (`examples/Ninjajar`, `make.bat gb`) se juegan. Falta
el sonido.

## Compilar

```bat
cd src\dev
comp-gb.bat
```

Deja `bootee.gb`. (En Linux: `./comp-gb.sh`.)

## Cómo se ve el juego

La pantalla del Game Boy (160x144) es más pequeña que la del juego (240x160,
15x10 tiles). La pantalla del juego entera se pinta en el fondo (32x32
caracteres) y una cámara enseña un trozo, siguiendo al jugador y sin salirse
de la pantalla del juego.

El marcador va abajo, en la ventana. Se configura en `config.h`:

```c
#define GB_HUD_ROWS        2                        // Filas del marcador
#define GB_HUD_LINE0       "  LIFE  ITEMS  KEYS "  // Textos fijos (20 caracteres)
#define GB_HUD_LINE1       "                    "
#define GB_LIFE_X          3                        // Dónde van los números:
#define GB_LIFE_Y          1                        // la y es la fila del marcador
#define GB_OBJECTS_X       9
#define GB_OBJECTS_Y       1
#define GB_KEYS_X          15
#define GB_KEYS_Y          1
```

También hay `GB_OBJECTS_ICON_X/Y`, `GB_KILLED_X/Y`, `GB_AMMO_X/Y`,
`GB_TIMER_X/Y`, `GB_FLAG_X/Y`, `GB_ITEM_X/Y` y `GB_LINE_OF_TEXT_X`,
`GB_LINE_OF_TEXT`. Lo que no tenga coordenadas de Game Boy no se pinta
(`VIEWPORT_X`, `VIEWPORT_Y` y las coordenadas del Spectrum no se usan).
Lo que se ve del juego mide 160 x (144 - 8 x `GB_HUD_ROWS`) píxeles; los
sprites se apagan donde empieza la ventana, para que no la pisen.

Los mensajes (GAME OVER, PAUSED) salen en la ventana, que crece hacia
arriba: debajo del marcador quedan las filas del mensaje.

## Ventana, textos y pantallas desde el código del juego

`gb/printer.h` tiene lo que necesita el código propio de un juego
(`custom.h`, `extern.h`) en Game Boy. En las funciones de imprimir, una `y`
de 20 en adelante es la fila `y - 20` de la ventana.

| Función | Qué hace |
|---|---|
| `gb_win_open (n)` | La ventana crece `n` filas; quedan vacías debajo del marcador (filas `20 + GB_HUD_ROWS`...). Para mensajes y recuadros de texto. |
| `gb_win_close ()` | La ventana vuelve a ser solo el marcador. |
| `gb_win_fixed (n)` / `gb_win_fixed_off ()` | Sobre una pantalla fija (una cinemática), la ventana con `n` filas vacías (las 20...) tapando la parte de abajo. |
| `gb_show_screen (RES_X)` | Una pantalla fija, con fundidos (en lugar de `get_resource (RES_X, 16384)`). |
| `gb_text_screen ()` | Una pantalla vacía para escribir (créditos...). |
| `gb_fade_out (0)` y `gb_fade_pending = 1` | Fundido a negro; el siguiente `sp_UpdateNow` funde desde negro. |
| `gb_copy_from_bank (gb_res_bank (RES_X), gb_res_addr (RES_X) + n, buffer, len)` | Copia un trozo de un recurso sin comprimir (en lugar de `copy_from_RAMn`). |

Ninjajar es el ejemplo: busca `#ifdef GB` en su `custom.h` y su `extern.h`.

## Scripts y textos

El intérprete es el mismo, pero lee el script directamente de la ROM: con
niveles, el script de cada nivel es un recurso **sin comprimir** (en
`librarian_gb.txt`) y no ocupa RAM. Los textos (`SCRIPT_TEXTS_AS_RESOURCE`)
también van sin comprimir. `comp-gb` compila los scripts con los textos
partidos en líneas de `GB_TEXT_WIDTH` caracteres (`config.h`, 18 si no se
dice): la pantalla tiene 20.

## Juegos con niveles

Como en ZX (capítulo 10), con estas diferencias:

* Los gráficos de Game Boy van en `gfx/gb`. Cada tileset de nivel son 192
  patrones (48 tiles, `mkts_om mode=strait2x2`) y cada spriteset, los 16
  sprites del jugador y los enemigos (`mode=sprites max=16`); los extras
  vienen siempre de `sprites.png`.
* El juego trae un `levels_gb.bat` (`levels_gb.sh`) en lugar de
  `levels.bat`, y un `librarian_gb.txt`. Los bundles son los mismos: en
  Ninjajar están en `bundles.bat`, que llaman los dos.
* La fuente y `sprites.png` se convierten en `convert_gb.bat`
  (`convert_assets_gb` en `game.sh`).

## Los mandos

| Botón | Qué hace |
|---|---|
| Cruceta | Moverse (ARRIBA salta en los juegos que saltan con ARRIBA). |
| A | FIRE: disparo, puñetazo, acción. |
| B | Saltar (hace de ARRIBA o, si el juego salta con FIRE, de FIRE; con `USE_TWO_BUTTONS` es la tecla de salto). |
| ABAJO | La acción de los scripts (con `SCRIPTING_DOWN`). |
| START | Pausa (`PAUSE_ABORT`); en el título, empezar. |
| SELECT | Abortar la partida (`PAUSE_ABORT`). |

## La memoria

* **Banco 0** (0x0000-0x3FFF, siempre visible): el arranque y las librerías
  de GBDK, `gb/home.c` (interrupciones, paletas, fundidos, sprites, recursos,
  pantallas fijas), `gb/vram.s` y `gb/zx0.s` (el descompresor), en
  ensamblador del SM83.
* **Banco 1** (0x4000-0x7FFF, siempre puesto): el motor, `gb/churromain.c`,
  que es lo mismo que `churromain.c` con la capa del Game Boy
  (`gb/sysvars.h` y `gb/printer.h`). Con el banco 0, el motor ve 32K
  seguidos y no hay llamadas entre bancos; lo que hay que leer de otros
  bancos lo leen funciones del banco 0 (`get_resource`, `gb_peek`,
  `gb_copy_from_bank`), que luego vuelven a poner el banco 1.
* **Bancos 3 en adelante**: los recursos (`librarian platform=gb`), cada uno
  comprimido con zx0. `get_resource (res, destino)` pone su banco, lo
  descomprime en la RAM o, con la pantalla apagada, en la VRAM, y deja el
  banco que había.
* **RAM**: 8K (0xC000-0xDFFF). Los sprites que copia el DMA están en 0xC000
  (el `shadow_OAM` de GBDK) y en 0xDE00 (se escribe en uno mientras se
  enseña el otro); la pila empieza en 0xE000. `gbcheck` comprueba al
  compilar que los bancos no se desbordan y que las variables acaban antes
  de 0xDE00 (`stack=512`, que incluye ese segundo buffer); si algo no cabe,
  da un error.

La VRAM:

| Zona | Qué hay |
|---|---|
| 0x8000-0x87FF | Sprites: 128 patrones (en modo 8x16, 32 sprites de 16x16). |
| 0x8800-0x8BFF | La fuente: tiles 128-191 del fondo. |
| 0x8C00-0x97FF | 192 patrones: el tileset del nivel o una pantalla fija (tiles 192-255 y 0-127). |
| 0x9800 | El fondo (32x32: la pantalla de 30x20 cabe entera). |
| 0x9C00 | La ventana: el marcador, los mensajes y los textos. |

Los caracteres son los mismos que en el Spectrum: 0-63 la fuente y
64 + 4 x t los cuatro del tile t. Con el fondo en el modo 0x8800, el carácter
c es el tile c ^ 128 del Game Boy.

## Los gráficos

Van en `gfx/gb` y los convierte `mkts_om platform=gb`. Los cuatro tonos se
detectan por el brillo (blanco, gris claro, gris oscuro y negro son los
colores 0 a 3); un píxel transparente o de un color que no sea gris (magenta,
por ejemplo) es el color 0, que en los sprites es transparente.

| Fichero | Qué es |
|---|---|
| `font.png` | La fuente: 64 caracteres (256x16), como la del Spectrum. |
| `work.png` | El tileset: 48 tiles de 16x16 (256x48), como el del Spectrum. |
| `sprites.png` | 32 sprites de 16x16 (256x32, ver abajo). |
| `title.png`, `ending.png` | Pantallas fijas de 160x144. |

En `sprites.png`, la fila de arriba son los 16 sprites de siempre (jugador y
enemigos, en el mismo orden que en el Spectrum) y la de abajo los extras:
la explosión (17), uno vacío (18), la bala y los cocos (19, 8x8 arriba a la
izquierda de su sitio) y el puño hacia la derecha y hacia la izquierda (20 y
21, igual). Los 11 sitios que quedan son para el juego.

| Modo de `mkts_om` | Para qué |
|---|---|
| `chars` | La fuente: 64 patrones. |
| `strait2x2` | El tileset: 48 tiles de 2x2 patrones, 192 en total. |
| `sprites` (`metasize=2,2`) | Sprites de 16x16 para el modo 8x16: cada columna de arriba abajo. Con un número impar de filas (`metasize=1,1`) se añade un patrón vacío debajo. |
| `scr` | Una pantalla fija de 160x144: sus patrones sin repetir (como mucho 192; si hay más, avisa, y la compilación enseña el aviso) y su mapa de 20x18, escritos de forma que, descomprimidos en 0x8C00, los patrones llenan 0x8C00-0x97FF y el mapa cae en el fondo, en 0x9800. |

## Paletas y fundidos

Las paletas (`GB_PAL_BG`, `GB_PAL_OBJ0`, `GB_PAL_OBJ1` en `config.h`, por
defecto `0xE4`) dicen qué tono tiene cada color: así se eligen los tres
tonos visibles de los sprites. `gb_fade_out (0)` / `gb_fade_in (0)` funden
a negro y desde negro; con 1, a blanco y desde blanco. `GB_FADE_FRAMES` es
la duración de cada paso. `blackout ()` y `cortina ()` funden a negro.

## Pruebas

`tests/gbrun` es un Game Boy sin pantalla (con Peanut-GB) para las pruebas,
como `zxrun`: `gbrun juego.gb -f frames -k "60:sta+,62:sta-" -s 100 -o
captura`. `-d dirección,bytes` vuelca memoria al acabar; las direcciones de
las variables están en `obj_gb/juego.noi` (con `noclean`).

---

# Apéndice A - Trabajar en Linux

Todo lo de este manual se puede hacer también en Linux. Cada `.bat` tiene un
`.sh` equivalente con el mismo nombre, que hace lo mismo:

| Windows | Linux |
|---|---|
| (GBDK-2020 en `C:\gbdk`) | `source ~/mk1tools/mk1env.sh` (pone `GBDK_HOME`) |
| `comp-zx.bat`, `comp-cpc.bat` | `./comp-zx.sh`, `./comp-cpc.sh` |
| `game.bat` + `convert.bat` | `game.sh`: pone `game=` y define una función `convert_assets` |
| `levels.bat` | `levels.sh` (ejecutable) |
| `examples\Goku Mal 128\make.bat` | `./make.sh` |

Para instalar el entorno:

```sh
env/setup-linux.sh [directorio]     # FreeBASIC y GBDK-2020
source ~/mk1tools/mk1env.sh         # (o el directorio que le hayas dado)
src/utils/build-linux.sh            # compila las herramientas en src/utils/linux
```

`env/setup-linux.sh` instala FreeBASIC 1.10, descomprime GBDK-2020 desde
`env/gbdk-linux64.tar.gz` y escribe `mk1env.sh`, que pone `GBDK_HOME`. `src/utils/build-linux.sh` compila
todas las herramientas (las de FreeBASIC, `msc4` y las de C) en
`src/utils/linux/`, que es donde las buscan los `.sh`. `ponedor` es sólo para
Windows.

Un `game.sh` es así:

```sh
game=gokumal

convert_assets () {
	$U/ts2bin ../gfx/font.png ../gfx/work1.png ts.bin 7 > /dev/null || return 1
	$U/sprcnv ../gfx/sprites1.png speccy/sprites.h > /dev/null || return 1
	...
}
```

---

# Apéndice B - Mapa de memoria

**ZX 48K**

| Zona | Qué hay |
|---|---|
| 23300-23599 (`BASE_ROOM_BUFFERS`) | `map_attr` y `map_buff` de la pantalla actual. |
| 23600-23727 (`BASE_ARRAYS`) | Arrays de enemigos y balas. |
| 23728-23877 (`BASE_BRK_BUFF`) | Golpes de los muros rompibles. |
| 24200 | El programa y, detrás, sus variables. |
| `AD_FREE` (0xF000 - bloques) - 0xF000 | Bloques de memoria de los sprites (`NUMBLOCKS`). |
| 0xF000-0xF100 | Tabla de vectores IM2. |
| 0xF1F0 hacia abajo | La pila (64 bytes). |
| 0xF1F1 | La interrupción (ISR). |
| 0xF200-0xFFFF | Tablas de rotación de splib2. |

**ZX 128K**: igual, salvo que la pila empieza en 24200 y crece hacia abajo;
que a partir de 24200 van primero el arranque y las librerías, luego las
variables del motor (los buffers de nivel incluidos) y luego su código, para
que lo que se usa con otra página puesta quede por debajo de 0xC000; y que
las páginas 1 (WYZ player), 3, 4, 6 y 7 (recursos) se ponen en 0xC000-0xFFFF
cuando hacen falta.

**CPC**

| Zona | Qué hay |
|---|---|
| 0x100-0x3FF | El nametable (un byte por tile de la pantalla). |
| 0x400 | El programa y, detrás, sus variables (hasta 0x8800). |
| 0x8800 | La canción que suena, descomprimida. |
| 0x9000-0xBFFF | El superbuffer. |
| 0xC000-0xFFFF | La pantalla; en los huecos de 0x200 bytes de cada bloque de 2K, los buffers del motor (0xC600…, ver `cpc/sysvars.h`), la LUT de transparencias (0xFE00) y la pila (0xFFFF hacia abajo). |
