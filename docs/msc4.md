# MSC4 — el lenguaje de scripts de MK1 v3.100

*Compilador:* `msc4` (`msc4/msc4.bas`, versión `msc v4.7.20261030`).
*Intérprete:* `src/dev/msc.h`.

MSC4 es el lenguaje de scripts de MTE MK1 v3.100. Este documento lo cuenta
entero: cómo se escribe un script, qué hace cada comando, cómo se compila y
cómo se engancha con tu propio código. El capítulo 8 del
[manual](manual.md#capítulo-8---el-scripting-msc4) es una introducción más
corta. (El mismo compilador existe también para MK1 v3.2, que usa otro
intérprete; aquí sólo se habla de MK1 v3.100.)

## Índice

1. [Para qué sirve MSC4](#1-para-qué-sirve-msc4)
2. [Ponerlo en marcha](#2-ponerlo-en-marcha)
3. [Línea de comandos](#3-línea-de-comandos)
4. [Estructura léxica](#4-estructura-léxica)
5. [Directivas](#5-directivas)
6. [Las secciones](#6-las-secciones)
7. [Las cláusulas](#7-las-cláusulas)
8. [Valores, expresiones e indirecciones](#8-valores-expresiones-e-indirecciones)
9. [Variables especiales](#9-variables-especiales)
10. [Las comprobaciones](#10-las-comprobaciones)
11. [Las acciones](#11-las-acciones)
12. [Subrutinas](#12-subrutinas)
13. [Texto y diálogos](#13-texto-y-diálogos)
14. [El inventario de un solo hueco](#14-el-inventario-de-un-solo-hueco)
15. [Tu código: `extern.h`](#15-tu-código-externh)
16. [Juegos con niveles](#16-juegos-con-niveles)
17. [Ejemplos](#17-ejemplos)
18. [Apéndice: el binario y el intérprete](#18-apéndice-el-binario-y-el-intérprete)

---

## 1. Para qué sirve MSC4

MSC4 es un lenguaje de scripts pequeño y deliberadamente tonto que te permite
añadir comportamiento a un güego de MK1 sin escribir C. Es un
lenguaje de *reacción*: el motor dispara un **evento** (el jugador entra en una
pantalla, el jugador pulsa la tecla de acción, el jugador toca un tile
especial…), y el script reacciona comprobando unas pocas condiciones y
ejecutando unas pocas acciones.

El modelo mental es:

```
evento  ──►  sección  ──►  cláusula 1  ──►  cláusula 2  ──►  cláusula 3  ──►  ...
                        (IF…THEN…)    (IF…THEN…)    (IF…THEN…)
```

* Una **sección** está ligada a un tipo de evento. Hay una sección por cada
  tipo de evento, más una sección por pantalla para los dos eventos
  "indexados" (*entrar en una pantalla*, *pulsar acción en una pantalla*).
* Una **sección** contiene una lista ordenada de **cláusulas**.
* Una **cláusula** es una lista de **condiciones** seguida de una lista de
  **acciones**. Las acciones se ejecutan **sólo si todas las condiciones de la
  cláusula son ciertas**.
* Las cláusulas de una sección se evalúan **en orden**. Una cláusula cuyas
  condiciones fallan se salta. Una cláusula puede parar la sección entera con
  `BREAK`.

Lo que MSC4 *no* es: no es un lenguaje de propósito general. No hay bucles, ni
aritmética más allá de `+`/`-` sobre valores de 8 bits, ni funciones
definidas por el usuario salvo `SUB`/`CALL`, ni arrays. Todo lo que no sea
expresable se delega en el motor mediante la acción `EXTERN`.

El estado se guarda en **flags**: un array de valores de 8 bits (`flags []`)
que vive en el motor y se comparte con el script.

---

## 2. Ponerlo en marcha

1. En `dev/config.h`, activa el scripting:

   ```c
   #define ACTIVATE_SCRIPTING          // Activa el scripting
   //#define SCRIPTING_DOWN            // Tecla de acción: abajo
   //#define SCRIPTING_KEY_M           // Tecla de acción: M (si no, FIRE)
   //#define MAX_FLAGS     32          // Más flags de los que usan los scripts
   //#define ITEM_X        28          // GET ITEM: tile del objeto en el marcador
   //#define ITEM_Y        1
   //#define LINE_OF_TEXT  1           // TEXT "...": fila,
   //#define LINE_OF_TEXT_X 1          // columna
   //#define LINE_OF_TEXT_ATTR 71      // y color
   ```

2. Escribe el script en `script/script.spt`.
3. Compila como siempre (`comp-zx.bat` o `comp-cpc.bat`). Si `config.h`
   define `ACTIVATE_SCRIPTING`, el script se compila solo antes que el
   güego. Si tiene errores, la compilación se para y se muestra lo que dice
   msc4; los avisos se muestran pero no la paran.

Un güego puede tener varios scripts (uno por nivel, por ejemplo: ver la
[sección 16](#16-juegos-con-niveles)). Entonces se escribe en `dev/` un
`scripts.txt` con la lista, una ruta por línea (las que empiezan por `#` son
comentarios):

```
# Los scripts de los niveles
../script/nivel1.spt
../script/nivel2.spt
```

y se compilan todos juntos.

### Qué genera msc4

| Fichero | Contenido |
|---|---|
| `<script>.spt.bin` | El bytecode de cada script (junto al `.spt`). Con niveles, se comprime y va como recurso. |
| `msc-config.h` | Lo que necesitan **todos** los scripts juntos: qué condiciones, acciones, variables especiales y secciones se usan, cuántos flags, el tamaño del script más grande, los textos y un `SCRIPT_<NOMBRE>` por script. |
| `msc-scripts.h` | El bytecode como arrays de C (`script_<nombre>` y `msc_scripts []`, indexado por `SCRIPT_<NOMBRE>`) y los textos (`msc_texts`). |

El intérprete (`dev/msc.h`) es C normal. Cada condición y cada acción está
bajo su propio `#ifdef`, y `msc-config.h` dice cuáles se compilan: **sólo
entra en el güego lo que tus scripts usan**. Un script que nunca use
`DIALOG` no tendrá ni un byte de código de diálogos. Como todos los scripts
se compilan juntos, el intérprete tiene lo que necesita cualquiera de ellos:
un nivel puede usar `DIALOG` aunque los demás no lo usen.

Lo mismo pasa con algunas partes del motor, que se activan solas según lo
que usen los scripts:

| Si el script usa… | …el motor incluye |
|---|---|
| `EXTERN`, `TEXT BOX`, `DIALOG` | tu `extern.h` (ver la [sección 15](#15-tu-código-externh)) |
| `SET FIRE ZONE` | la zona de fuego |
| `TILE PUSHED`, `MOVED_*` | lo que necesita la sección de bloques empujados |
| `TIMER ZERO` | la llamada a la sección al llegar el temporizador a 0 (necesita `TIMER_ENABLE`) |
| `TEXT BOX`, `DIALOG` | `redraw_scr ()`, para que `extern.h` pueda borrar sus recuadros |
| `GET ITEM SET` | con `ITEM_X` / `ITEM_Y` en `config.h`, el objeto en el marcador |
| cualquier sección | sólo las llamadas a las secciones que existen |

El tamaño de `flags []` es el flag más alto que aparece en los scripts, más
uno, salvo que `config.h` defina `MAX_FLAGS`. Ojo con las indirecciones
(`$$3`): si el flag 3 puede valer más que eso, define `MAX_FLAGS`. Leer un
flag fuera de rango da 0 y escribirlo no hace nada.

---

## 3. Línea de comandos

No hace falta llamar a msc4 a mano: lo hace `comp-zx.bat`. Por si acaso:

```
msc4 in=f1.spt[,f2.spt,...] v=3_100 output=c [rooms=N]
     [interpreter=msc-config.h] [scripts=msc-scripts.h]
     [allopcodes] [debug] [textdebug]
```

| Opción | Obligatoria | Significado |
|---|---|---|
| `in=` | sí | Lista de ficheros `.spt`, separados por comas. Se produce un `.bin` por fichero. |
| `v=3_100` | sí | La versión del motor. |
| `output=c` | sí | Genera `msc-config.h` y `msc-scripts.h` para el intérprete en C. |
| `rooms=N` | no | Número de pantallas del mapa, para los scripts que no digan `ROOMS = N`. `comp-zx.bat` pasa `MAP_W * MAP_H`. |
| `interpreter=` | no | Nombre de `msc-config.h`. |
| `scripts=` | no | Nombre de `msc-scripts.h`. |
| `allopcodes` | no | Activa en `msc-config.h` **todas** las condiciones y acciones, se usen o no. Para pruebas. |
| `debug` | no | Traza de la compilación: los tokens que ve el compilador y el bytecode que produce para cada línea. |
| `textdebug` | no | Vuelca la codificación en 5 bits de cada texto. |
| `text=` | no | Fichero con los textos codificados (por defecto `text.bin`). |
| `textres` | no | Los textos van **solo** en `text=`, que el juego pone como recurso de 128K (sin comprimir) en `librarian.txt`; no ocupan RAM. `comp-zx` lo pasa si `config.h` tiene `SCRIPT_TEXTS_AS_RESOURCE`. |
| `textwidth=N` | no | Los textos se parten en líneas de N caracteres, diga lo que diga `TEXT WIDTH` en los scripts. Lo pasa `comp-gb` (con `GB_TEXT_WIDTH` de `config.h`, 18 si no está). |

`debug` es *muy* útil mientras escribes un script.

Con errores, msc4 no escribe nada (ni `.bin`, ni `msc-config.h`) y sale con
código 1.

---

## 4. Estructura léxica

* **No distingue mayúsculas** en ningún sitio: cabeceras de sección, palabras
  clave, nombres de alias. (Los *números* de flag son dígitos, así que por
  supuesto tampoco hay problema.)
* Los **comentarios** empiezan por `#` y llegan hasta el final de la línea. Un
  `#` dentro de una cadena entrecomillada *no* empieza un comentario.
* Los **espacios en blanco** no son significativos, salvo que las palabras
  clave deben estar separadas de sus argumentos.
* Los operadores de comparación `=`, `<`, `>`, `!` pueden escribirse sin
  espacios alrededor: `IF $A=3` y `IF $A = 3` son equivalentes.
* `,`, `(`, `)` y `[`, `]` son *separadores de token* en el fuente, no parte de
  un token. Así que `SET TILE (5,6) = 3` y `SET TILE 5 6 = 3` son lo mismo.
* `_` es separador de token **sólo en las cabeceras de sección** (ver más
  abajo). Dentro de expresiones y comandos es un carácter normal (por eso las
  opciones de un diálogo pueden llevar espacios pero no comas — ver la
  [sección 13](#13-texto-y-diálogos)).
* Cadenas entrecomilladas: `"..."`. Las comillas las quita el tokenizador;
  todo lo que hay entre ellas (espacios, comas, puntuación) se conserva tal
  cual.

### 4.1 El prefijo `ON`

Si una línea empieza por `ON ` (sin distinguir mayúsculas), se quitan esos tres
caracteres antes de analizarla. Existe para que una sección pueda escribirse
`ON TILE PUSHED` en vez de `TILE PUSHED` (o `ON PLAYER KILLS ENEMY`, `ON TIMER
ZERO`…). Vale para las cabeceras de sección y para las condiciones
(`ON IF …` no tiene mucho sentido, pero se acepta).

### 4.2 Las cabeceras de sección se buscan de forma flexible

Las cabeceras de sección se comparan token a token, y `_` es un separador a
ese nivel. Por tanto, todo esto es la misma sección:

```
PRESS FIRE AT ANY
PRESS_FIRE AT ANY
press_fire at any
```

Lo mismo vale para `PLAYER_KILLS_ENEMY` / `PLAYER KILLS ENEMY`,
`PLAYER_GOT_SOMETHING` / `PLAYER GOT SOMETHING`, `SPECIAL_TILE_TOUCHED` /
`SPECIAL TILE TOUCHED`, `ENEMY_TOUCHED` / `ENEMY TOUCHED`.

---

## 5. Directivas

Las directivas se escriben en el nivel superior del script (fuera de cualquier
sección) y surten efecto desde ese punto. Normalmente se ponen al principio.

| Directiva | Sintaxis | Efecto |
|---|---|---|
| `ROOMS` | `ROOMS = N` | Número de pantallas del mapa. Dimensiona el índice de secciones. También se puede dar en la línea de comandos (`rooms=N`); manda el valor del script. |
| `ALIAS` | `ALIAS %NOMBRE = N` | Liga el nombre `%NOMBRE` al número de flag `N`. Ver la [sección 8.3](#83-los-alias). |
| `ITEM SLOT` | `ITEM SLOT = N` | Qué flag guarda el "objeto que llevas" (ver la [sección 14](#14-el-inventario-de-un-solo-hueco)). |
| `ITEM EMPTY` | `ITEM EMPTY = N` | Qué valor de tile significa "no llevo nada" (por defecto `0`). La palabra `EMPTY` en el script se sustituye por este número. |
| `TEXT WIDTH` | `TEXT WIDTH = N` | Ancho de línea (en caracteres) que usa el codificador de textos de 5 bits. Por defecto `24`. La opción `textwidth=N` de msc4 manda sobre él (la usa la compilación de Game Boy, con la pantalla más estrecha). |
| `NOINDEXED` | `NOINDEXED` | Puramente documental: dice que el güego no usa las secciones por pantalla (y quita el aviso de que falta `ROOMS`). No cambia el binario. |
| `FASTNPANT` | `FASTNPANT` | Compila `IF NPANT = N` con una condición propia, más rápida (ver la [sección 10.4](#104-if-npant--n)). |

`SUB` no es una directiva en el sentido habitual, pero es una construcción de
nivel superior; ver la [sección 12](#12-subrutinas).

### 5.1 La palabra `EMPTY`

En cualquier sitio donde se espere un valor puedes escribir `EMPTY`; el
compilador lo sustituye por el valor de la directiva `ITEM EMPTY` (por
defecto `0`). Esto hace explícita la intención:

```
%CARRYING = EMPTY      # "no llevo nada"
```

---

## 6. Las secciones

Una sección empieza con su cabecera en una línea propia y termina con una
línea que contenga sólo `END`. El cuerpo de la sección es una secuencia de
cláusulas.

### 6.1 La lista de secciones

| Cabecera | Índice | Se dispara cuando |
|---|---|---|
| `ENTERING GAME` | 0 | Una sola vez, justo antes del primer frame de una partida nueva. |
| `ENTERING ANY` | 1 | Cada vez que el jugador entra en una pantalla (incluida la primera). |
| `ENTERING SCREEN n` | 16 + 2n | Cada vez que el jugador entra en la pantalla `n`. Se ejecuta **después** de `ENTERING ANY`. |
| `PRESS FIRE AT ANY` | 2 | Cada vez que se pulsa la tecla de acción. |
| `PRESS FIRE AT SCREEN n` | 17 + 2n | Cada vez que se pulsa la tecla de acción estando en la pantalla `n`. Se ejecuta **después** de `PRESS FIRE AT ANY`. |
| `PLAYER GOT SOMETHING` | 3 | El jugador recoge un hotspot (un objeto / una moneda, según el juego). |
| `PLAYER KILLS ENEMY` | 4 | Muere un enemigo. |
| `SPECIAL TILE TOUCHED` | 5 | El jugador está sobre un tile cuyo comportamiento tiene el bit 7 puesto (comportamiento `128 + n`). |
| `TIMER ZERO` | 6 | El temporizador llega a 0. |
| `TILE PUSHED` | 7 | El jugador empuja un bloque (tile 14). `MOVED_TILE`, `MOVED_X` y `MOVED_Y` dicen qué tile tapó y dónde quedó; `TX`, `TY` son esas mismas coordenadas. |
| `ENEMY TOUCHED` | 8 | El jugador choca con un enemigo. |
| `TILE DESTROYED` | 9 | Se rompe un tile (`BREAKABLE_WALLS`); `TX`, `TY` son sus coordenadas. |

Una misma pantalla puede aparecer varias veces en una cabecera, en cuyo caso se
usa el *mismo* bytecode para todas:

```
ENTERING SCREEN 0, 2, 20
PRESS FIRE AT SCREEN 2, 7, 12, 17
```

### 6.2 Orden de ejecución

Para un evento dado, el motor llama a las secciones en este orden:

```
ENTERING ANY          →   ENTERING SCREEN n
PRESS FIRE AT ANY     →   PRESS FIRE AT SCREEN n
```

Esto es *fundamental*: si quieres que un comportamiento por pantalla
sobrescriba a uno global, pon el global en `ENTERING ANY` y el particular en
`ENTERING SCREEN n`, que se ejecuta después (mira la subrutina `PLACEBOX` en
la [sección 17.1](#171-una-caja-que-se-coge-y-se-suelta)).

### 6.3 Dónde lanza el motor cada sección

| Sección | Cuándo, exactamente | TX, TY |
|---|---|---|
| `ENTERING GAME` | Al empezar la partida (con niveles, al empezar cada nivel, con el script de ese nivel). | — |
| `ENTERING ANY` + `ENTERING SCREEN n` | Al entrar en una pantalla, después de pintarla y de colocar los enemigos y el objeto. | centro del jugador |
| `PRESS FIRE AT ANY` + `PRESS FIRE AT SCREEN n` | Al pulsar la tecla de acción, o cada frame dentro de la zona de fuego (`SET FIRE ZONE`). | centro del jugador |
| `PLAYER GOT SOMETHING` | Al coger un objeto, después de procesarlo. | — (`HOTSPOT` es su tipo) |
| `PLAYER KILLS ENEMY` | Al morir un enemigo (pisotón o disparo). | — (`EN_*`) |
| `ENEMY TOUCHED` | Al chocar el jugador con un enemigo, antes del daño. | — (`EN_*`) |
| `SPECIAL TILE TOUCHED` | Cada frame que el centro del jugador está en un tile con el bit 7 (128) de comportamiento. | el tile especial |
| `TILE PUSHED` | Después de mover al jugador, si ha empujado un bloque. | dónde quedó el bloque |
| `TILE DESTROYED` | Al romperse un tile. | el tile roto |
| `TIMER ZERO` | Cuando el temporizador llega a 0 (con `SHOW_TIMER_OVER`, después del cartel). | — |

Las secciones de pantalla sólo se ejecutan si la pantalla es menor que el
`ROOMS` del script. `OPANT` vale, durante las secciones `ENTERING`, la
pantalla de la que se viene (`0xFF` al empezar). Si un script de `ENTERING`
cambia de pantalla (`WARP TO`, `NPANT = n`), la nueva se pinta en el frame
siguiente. `PARAM` vale `0xFF` al entrar en una sección.

### 6.4 ¿Qué tecla es "FIRE"?

La tecla de acción se configura en `config.h`:

```c
#define ACTIVATE_SCRIPTING     // activa el motor de scripting
#define SCRIPTING_DOWN         // usa DOWN como tecla de acción
//#define SCRIPTING_KEY_M      // usa M como tecla de acción
```

Si no se define ninguna, se usa `FIRE`.

---

## 7. Las cláusulas

El esqueleto de una sección:

```
ENTERING SCREEN 3
	IF <condición>
	IF <condición>
	THEN
		<acción>
		<acción>
	END
	IF <condición>
	THEN
		<acción>
	END
END
```

Reglas de la forma:

* Una línea `IF` empieza una cláusula. **Varias líneas `IF` seguidas van
  acumulando condiciones** (AND lógico).
* `THEN` debe ir en una línea propia y cambia de "recoger condiciones" a
  "recoger acciones".
* `END` en una línea propia **cierra la cláusula actual** y vuelve al estado
  "buscar el siguiente `IF`".
* El `END` final de la sección (cuando no hay ninguna cláusula abierta) cierra
  la sección.

Evaluación:

* Las condiciones de una cláusula se evalúan en orden; en cuanto una es falsa
  la cláusula se salta entera.
* Si todas las condiciones se cumplen, las acciones se ejecutan en orden.
* Después se evalúa la siguiente cláusula. Una cláusula **no** es un `else`:
  varias cláusulas de la misma sección pueden dispararse todas.
* `BREAK` (ver la [sección 11](#11-las-acciones)) aborta la sección entera: no se
  evalúa ninguna cláusula más.

### 7.1 Terminadores

`BREAK`, `WIN GAME`, `GAME OVER` y `RERUN` terminan la cláusula de inmediato,
así que lo que vaya detrás no se ejecuta nunca. El compilador avisa si les
pones más código detrás:

```
Warning! unreachable code @ 13
```

---

## 8. Valores, expresiones e indirecciones

### 8.1 Los tres tipos de valor

| Sintaxis | Significado |
|---|---|
| `123` | Un número literal, `0 … 254`. |
| `$n` | El **contenido** del flag `n`. |
| `%NOMBRE` | Azúcar sintáctico para `$n`, donde `n` es el flag ligado a `%NOMBRE`. |

`FLAG n` es otra forma de escribir `$n`, y compone:

```
FLAG n        == $n
FLAG FLAG n   == $$n
```

(`$` también se escribe `FLAG`, así que `FLAG FLAG FLAG 3` es `$$$3`.) Ojo:
no se permite `$` delante de un alias: escribe `FLAG %NOMBRE`, no `$%NOMBRE`…
excepto que `$%NOMBRE` *sí* se acepta y significa "el flag cuyo número es el
contenido del flag ligado a `%NOMBRE`" (ver la [sección 8.3](#83-los-alias)).

### 8.2 Indirección infinita

Las cadenas de `$` no tienen límite: un `$` seguido de un índice de flag
significa "el contenido de ese flag"; el contenido de un flag es un byte, y si
ese byte es `255` (`$FF`) significa "otra indirección".

En el bytecode, un valor se codifica así:

| Secuencia de bytes | Significado |
|---|---|
| `n` | el literal `n` (0…254) |
| `FF n` | `flags[n]` |
| `FF FF n` | `flags[flags[n]]` |
| … | y así sucesivamente |

### 8.3 Los alias

Un alias da un *nombre* a un número de flag:

```
ALIAS %CARRYING = 0
```

Tras esta directiva, `%CARRYING` se puede usar en cualquier sitio donde se
espere un valor, y significa `$0`.

* El nombre no distingue mayúsculas (`%carrying` = `%CARRYING`).
* El nombre puede llevar letras, dígitos y guiones bajos.
* `&%NOMBRE` da el **número** del flag, no su contenido. Este es el operador
  "dame un puntero", y es lo que permite escribir código que trabaja con un
  flag que sólo se conoce al jugar (ver el ejemplo de la
  [sección 17.4](#174-el-idioma-alias)):

  ```
  %G = &%MEDA1        # %G := el número de flag de %MEDA1
  $%G = 1             # poner a 1 ese flag
  ```

* Los alias también se pueden introducir *implícitamente*: usar un `%NOMBRE`
  desconocido en el script reserva el primer hueco de flag libre para él e
  imprime la asignación al final de la compilación:

  ```
  %conseguido -> $0
  %total_frutas -> $1
  ```

  El orden de reserva es el orden de primer uso, así que **no te fíes de
  él**: declara explícitamente con `ALIAS` los aliases que te importen.

### 8.4 Expresiones

Hay tres cosas que se pueden usar donde se espera un valor, además de los
valores normales:

```
TILE AT (x, y)     el número de tile en las coordenadas de pantalla dadas
BEH AT (x, y)      el comportamiento del tile en las coordenadas dadas
DIALOG "a", "b", "c"   la opción que elige el jugador (1, 2 o 3)
```

Se escriben exactamente como una asignación a una pseudo-variable:

```
%BOXT = TILE AT (%BOXX, %BOXY)
IF BEH AT (TX, %AUX) <> 0
%RES = DIALOG "SI", "NO", "QUIZAS"
```

Las coordenadas pueden ser a su vez valores (flags, literales, variables
especiales).

`DIALOG` es el caso raro: no es un *valor* en sentido matemático, es una
llamada al motor que saca un menú y devuelve la opción elegida. Aun así se
codifica como un valor, así que se puede guardar en un flag y usar más tarde,
o pasarle directamente a `RERUN`.

---

## 9. Variables especiales

Además de los flags normales (`$0 … $254`), el compilador expone un conjunto
de **variables especiales** respaldadas por el estado del motor. Se codifican
como pseudo-flags en el rango `$E5 … `$FE`.

| Nombre | Pseudo-flag | Significado | Lectura | Escritura |
|---|---|---|---|---|
| `NPANT` (o `N_PANT`) | `$FE` | La pantalla en la que está el jugador. Escribirla le cambia de pantalla en el siguiente frame (como `WARP TO`). | ✔ | ✔ |
| `PX` | `$FD` | X del jugador, en **píxeles**. Escribirla lo coloca ahí. | ✔ | ✔ |
| `PY` | `$FC` | Y del jugador, en **píxeles**. Escribirla lo coloca ahí. | ✔ | ✔ |
| `KILLED` | `$FB` | Número de enemigos matados hasta ahora. | ✔ | ✔ |
| `OBJS` | `$FA` | Número de objetos (hotspots) recogidos. | ✔ | ✔ |
| `LIFE` | `$F9` | Vida del jugador. | ✔ | ✔ |
| `TX` | `$F8` | Tile X (depende de la sección: ver abajo). | ✔ | ✘ |
| `TY` | `$F7` | Tile Y (depende de la sección). | ✔ | ✘ |
| `TN` | `$F6` | El tile que hay ahora en `TX`, `TY`. | ✔ | ✘ |
| `HOTSPOT` | `$F5` | El tipo del último objeto cogido (3 si era una recarga de vida que aparece sola sin `USE_HOTSPOTS_TYPE_3`). | ✔ | ✘ |
| `MOVED_TILE` | `$F4` | El tile que tapó el último bloque empujado. | ✔ | ✘ |
| `MOVED_X` | `$F3` | X (tile) donde quedó el último bloque empujado. | ✔ | ✘ |
| `MOVED_Y` | `$F2` | Y (tile) donde quedó el último bloque empujado. | ✔ | ✘ |
| `TIMER` | `$F1` | El valor del temporizador (`ctimer.t`; necesita `TIMER_ENABLE`). | ✔ | ✔ |
| `HIDE_HOTSPOTS` | `$F0` | Si vale distinto de 0, el objeto de la pantalla no se pinta ni se puede coger; vuelve a 0 al entrar en cada pantalla, así que se pone en `ENTERING`. | ✔ | ✔ |
| `DONT_MAKE_FANTIES` | `$EF` | Con `ENABLE_RANDOM_RESPAWN`, si vale distinto de 0 no salen fanties; vuelve a 0 al entrar en cada pantalla. | ✔ | ✔ |
| `EN_T` | `$EE` | El **tipo** del enemigo que se está tocando (1, 2, 3…). | ✔ | ✔ |
| `EN_N` | `$ED` | El **número** del enemigo que se está tocando dentro de la pantalla: 0, 1 o 2. No es su tipo (eso es `EN_T`). | ✔ | ✘ |
| `EN_X` | `$EC` | X del enemigo (píxeles). | ✔ | ✔ |
| `EN_Y` | `$EB` | Y del enemigo (píxeles). | ✔ | ✔ |
| `OPANT` (o `O_PANT`) | `$EA` | La pantalla en la que estaba el jugador antes de entrar en la actual. | ✔ | ✔ |
| `PARAM` | `$E9` | El parámetro pasado a la ejecución actual de la sección. | ✔ | ✔ |
| `TILE AT (x,y)` | `$E8` | Expresión, ver la [sección 8.4](#84-expresiones). | ✔ | ✘ |
| `BEH AT (x,y)` | `$E7` | Expresión. | ✔ | ✘ |
| `DIALOG …` | `$E6` | Expresión. | ✔ | ✘ |
| `LEVEL` | `$E5` | El nivel (con `COMPRESSED_LEVELS`): su posición en la tabla de `levelset.h`. `IF LEVEL = 3`. | ✔ | ✘ |

Notas:

* `TX`, `TY` los fija el motor antes de lanzar cada sección. Para las de
  pantalla y las de la tecla de acción son el tile del centro del jugador
  (`(x + 8) >> 4`, `(y + 8) >> 4`); para `SPECIAL TILE TOUCHED`, el tile
  especial; para `TILE PUSHED`, dónde quedó el bloque; para
  `TILE DESTROYED`, el tile roto. `TN` se lee en el momento.
* `OPANT` vale `0xFF` mientras la partida está empezando, así que conviene
  comprobar `OPANT < número de pantallas` antes de fiarse de él.

---

## 10. Las comprobaciones

Una comprobación es una línea `IF`. La forma general es

```
IF <valor> <operador> <valor>
```

con los operadores `=`, `<`, `>`, `<=`, `>=`, `<>` y `!=` (`!=` y `<>` son lo
mismo).

### 10.1 Comparaciones

| Se escribe | Significado |
|---|---|
| `IF $A = $B` | iguales |
| `IF $A <> $B` | distintos (también `!=`) |
| `IF $A < $B` | menor |
| `IF $A > $B` | mayor |
| `IF $A <= $B` | menor o igual |
| `IF $A >= $B` | mayor o igual |

Los dos operandos pueden ser literales, flags, alias o expresiones. Las
comparaciones son **de 8 bits sin signo**.

### 10.2 `IF TRUE`

`IF TRUE` es la forma idiomática de escribir una cláusula sin condiciones. Se
codifica como una condición "siempre cierta" (el opcode `$F0`).

### 10.3 Comprobaciones del jugador

| Se escribe | Significado |
|---|---|
| `IF PLAYER AT (x, y)` | El **centro** del sprite del jugador está en el tile `(x, y)` (coordenadas de tile). |
| `IF PLAYER TOUCHES (x, y)` | **Idéntico** a `PLAYER AT` (ver la nota de abajo). |
| `IF PLAYER IN_X a, b` | La X del jugador en **píxeles** está entre `a` y `b` (ambos incluidos). |
| `IF PLAYER IN_Y a, b` | La Y del jugador en **píxeles** está entre `a` y `b` (ambos incluidos). |
| `IF PLAYER FALLING` | El jugador está cayendo: `vy > 0` **y** `player.possee` es 0 (o sea, no está apoyado en nada). |
| `IF PLAYER NOT_FALLING` | La negación de lo anterior: `vy <= 0` **o** `player.possee != 0`. También se puede escribir `PLAYER NOT FALLING`. |
| `IF PLAYER STILL` | `vx == 0 && vy == 0`. |
| `IF PLAYER NEAR (x, y)` | El jugador (su esquina, `PX`, `PY`) está a 15 píxeles o menos de `(x*16, y*16)` en los dos ejes: está tocando el tile `(x, y)` con cualquier parte del sprite. Es el `PLAYER_TOUCHES` de los scripts antiguos. |

> **`TOUCHES` no quiere decir "cualquier parte del sprite toca el tile".**
> `TOUCHES` y `AT` son lo mismo: comparan el *tile del centro* del jugador con
> `(x, y)`. Para "tocar" con cualquier parte del sprite está `NEAR`.

> **`IN_X` / `IN_Y` van en píxeles, no en tiles.** Para comprobar tiles, usa
> `TX`/`TY`:
>
> ```
> IF TX = 5
> IF TY = 6
> ```

> **`FALLING` y `NOT FALLING` son negaciones exactas la una de la otra.**

### 10.4 `IF NPANT = N`

`IF NPANT = N` es la forma normal de preguntar "¿estoy en la pantalla N?".
Con la directiva `FASTNPANT` se compila a una condición propia que compara
directamente con la pantalla actual, en lugar de pasar por la lectura
genérica de valores: es algo más rápido.

Sólo se optimiza la forma con `=`; `IF NPANT <> 3` usa el camino genérico.

---

## 11. Las acciones

Las acciones son las sentencias dentro de una cláusula. El lado izquierdo de
una asignación debe ser un *flag* (o una variable especial escribible).

### 11.1 Flags

| Se escribe | Efecto |
|---|---|
| `$A = B` | `flags[A] = B` |
| `SET $A = B` | lo mismo |
| `INC $A, B` | `flags[A] += B` |
| `FLIPFLOP $A` | `flags[A] = 1 - flags[A]` (alterna entre 0 y 1) |
| `DEC $A, B` | `flags[A] -= B` |
| `ADD FLAGS x, y` | `flags[x] += flags[y]` |
| `SUB FLAGS x, y` | `flags[x] -= flags[y]` |

`$A` puede ser un alias (`%A = 3`) o una variable especial escribible
(`PY = 32`). `B` puede ser un literal, un flag, un alias, una variable especial
o una expresión.

La aritmética es de 8 bits y **da la vuelta**: `DEC $A, 1` sobre un flag que
vale 0 da 255.

### 11.2 La pantalla

| Se escribe | Efecto |
|---|---|
| `SET TILE (x, y) = t` | Pone el tile `t` en las coordenadas de pantalla dadas (en tiles). El comportamiento del tile se toma de la tabla de comportamientos. |
| `SET BEH (x, y) = b` | Cambia el *comportamiento* del tile en `(x, y)` sin tocar el tile en sí. |
| `PRINT TILE (x, y) = t` | Dibuja un tile sobre la pantalla en `(x, y)` (overlay, no toca el mapa). `x`, `y` son coordenadas de **carácter** (no de tile) contadas desde la esquina del área de juego (el intérprete les suma `VIEWPORT_X`, `VIEWPORT_Y`), así que valen igual en todas las máquinas. Para pintar en el marcador, que en cada máquina está en un sitio, mejor un `EXTERN` con `#ifdef` en `extern.h` (como hace Ninjajar). |
| `WARP TO n, x, y` | Teletransporta al jugador a la pantalla `n`, posición en píxeles `(x*16, y*16)`. |
| `WARP TO LEVEL l, n, x, y [, s]` | Termina el nivel y pasa al nivel `l` (con `COMPRESSED_LEVELS`), a su pantalla `n` y al tile `(x, y)`. Con `s` distinto de 0, sin la presentación del nivel ni el marco (sigue la pantalla que había). Termina el script. |
| `REENTER` | Se vuelve a entrar en la pantalla: se repinta y se ejecutan otra vez sus `ENTERING`, pero sin resucitar a los enemigos (`RESPAWN_ON_ENTER`). Termina la **cláusula** (las siguientes sí se evalúan). |
| `REPOSTN x, y` | El jugador al tile `(x, y)`, quieto, y `REENTER`. |
| `REDRAW` | Repinta la pantalla tal y como está (después de un `TEXT BOX`, por ejemplo). |
| `ENEMY n ON` / `ENEMY n OFF` | Resucita / quita al enemigo `n` (0, 1 o 2) de la pantalla. |
| `SET FIRE ZONE x1, y1, x2, y2` | Define una zona (en píxeles) en la que estar equivale a pulsar la tecla de acción: se ejecutan `PRESS FIRE AT ANY` y `PRESS FIRE AT SCREEN n` cada frame mientras el jugador esté dentro. Se apaga al cambiar de pantalla, así que se define en `ENTERING`. |
| `SET FIRE ZONE TILES x1, y1, x2, y2` | Lo mismo con coordenadas de tile (la zona va de la esquina del tile `(x1, y1)` al final del tile `(x2, y2)`). |

### 11.3 El jugador

| Se escribe | Efecto |
|---|---|
| `RECHARGE` | Pone la vida del jugador a `PLAYER_LIFE` (el de `config.h`). |
| `SAFE x, y` | Con `DIE_AND_RESPAWN`: el sitio al que se vuelve al perder una vida pasa a ser el tile `(x, y)` de esta pantalla. |
| `SHOW` | Fuerza un refresco de pantalla (`sp_UpdateNow ()`). |
| `PAUSE n` | Espera `n` cincuentavos de segundo. |

### 11.4 Sonido, texto, externos

| Se escribe | Efecto |
|---|---|
| `SOUND n` | Toca el efecto de sonido `n` (`PLAY_SFX (n)`: beeper en 48K, WYZ player en 128K y CPC). Los números están en el capítulo 7 del manual. |
| `MUSIC n` | Toca la canción `n`, que pasa a ser la del nivel (la que vuelve a sonar tras perder una vida con `DIE_AND_RESPAWN`). |
| `TEXT "…"` | Escribe una línea corta de texto en la fila `LINE_OF_TEXT`, columna `LINE_OF_TEXT_X`, con el color `LINE_OF_TEXT_ATTR` (los tres en `config.h`). La línea se borra al entrar en cada pantalla. |
| `TEXT BOX "…"` | Muestra una caja de texto: la pinta tu `text_box ()` de `extern.h` (ver la [sección 15](#15-tu-código-externh)). |
| `EXTERN n, m` | Llama a tu `do_extern_action (n, m)` de `extern.h`. El segundo parámetro vale 0 por defecto. Es la salida hacia tu propio código C. |
| `PAUSE n` | ver arriba. |

### 11.5 Objetos

| Se escribe | Efecto |
|---|---|
| `GET ITEM SET $F` | Coge el objeto sobre el que está el jugador (ver la [sección 14](#14-el-inventario-de-un-solo-hueco)). |

### 11.6 Decoraciones

```
DECOS
	3, 4, 5
	6, 7, 8
END
```

`DECOS` pinta una lista de tiles de una vez (es lo mismo que escribir varios
`SET TILE`, pero ocupa menos). Cada línea es
`x, y, tile`.

El bloque `DECOS` lo termina un `END`, y la cláusula que lo contiene necesita
**su propio** `END` después:

```
IF TRUE
THEN
	DECOS
		3, 4, 5
	END
	SOUND 1
END
```

### 11.7 Control de flujo y estado de partida

| Se escribe | Efecto |
|---|---|
| `BREAK` | Para la ejecución de la sección entera. Las cláusulas restantes no se evalúan. |
| `WIN GAME` | Termina la sección y supera el nivel (o el güego, si no hay niveles o es el último). |
| `GAME OVER` | Termina la sección y la partida. |
| `GAME ENDING` | Termina el juego (con `COMPRESSED_LEVELS`): se acaba la partida y se muestra el final (`HOOK_GAME_ENDING`). |
| `RERUN v` | Pone `PARAM` a `v` y reinicia la sección actual desde arriba. |
| `CALL nombre` | Ejecuta la subrutina `nombre` (ver la [sección 12](#12-subrutinas)). |

`BREAK`, `WIN GAME`, `GAME OVER` y `RERUN` son *terminadores*: el compilador
avisa de cualquier código que venga después en la misma cláusula.

Con `HOOK_WIN_CONDITION` en `custom.h`, tu propio código también puede decidir
que se ha superado el nivel (capítulo 9 del manual).

### 11.8 Diálogos

| Se escribe | Efecto |
|---|---|
| `$F = DIALOG "a", "b", "c"` | Presenta un menú con hasta tres opciones y guarda la opción elegida (1, 2 o 3) en `$F`. |

`DIALOG` es una *expresión*; se puede usar directamente en una comparación,
pero el patrón habitual es guardarla y luego hacer `RERUN` con el resultado,
lo que convierte la sección en una máquina de estados (ver la
[sección 17.3](#173-una-máquina-de-estados-con-diálogo)).

---

## 12. Subrutinas

```
SUB MIPROCEDIMIENTO
	IF TRUE
	THEN
		$5 = 1
	END
END
```

y, desde cualquier sitio:

```
CALL MIPROCEDIMIENTO
```

Reglas:

* La subrutina puede definirse antes o después del `CALL`. Un `CALL` a una
  `SUB` que no existe es un error.
* Un `BREAK` en la subrutina sale sólo de ella; `WIN GAME`, `GAME OVER` y
  `RERUN` terminan también la sección que la llamó.
* El cuerpo de una subrutina es sintácticamente idéntico al de una sección:
  cláusulas con condiciones y acciones.
* Las subrutinas viven en el mismo binario que las secciones, y cada script
  tiene las suyas.
* Los nombres no distinguen mayúsculas.

---

## 13. Texto y diálogos

### 13.1 Dos sistemas de texto distintos

| | `TEXT "…"` | `TEXT BOX "…"` |
|---|---|---|
| Se guarda | tal cual, dentro del bytecode | en 5 bits por carácter, con los textos de todos los scripts |
| Lo pinta | el motor, en una línea del marcador | tu `text_box ()` de `extern.h` |
| Requiere | `LINE_OF_TEXT`, `LINE_OF_TEXT_X` y `LINE_OF_TEXT_ATTR` en `config.h` | nada (sólo escribir `text_box ()`) |
| Ajuste de línea | no | sí, a `TEXT WIDTH` caracteres |

`TEXT` sirve para mensajes cortos en el marcador. `TEXT BOX` es para textos
largos, en una caja que dibuja tu propio código.

### 13.2 La codificación de 5 bits

El compilador empaqueta los textos de `TEXT BOX` y `DIALOG` en valores de 5
bits, con un mecanismo de escape:

| Valor | Significado |
|---|---|
| `0` | ESC — el siguiente valor es un carácter "extendido" |
| `1 … 26` | `A` … `Z` |
| `27` | `,` |
| `28` | `.` |
| `29` | `?` |
| `30` | `!` |
| `31` | espacio |
| ESC `0` | fin de cadena |
| ESC `1 … 30` | ASCII 33 … 62 (`!` … `>`) |
| ESC `31` | salto de línea (lo mete el ajuste de línea) |

Consecuencias:

* **Las minúsculas se convierten en mayúsculas.** Escribe los textos en
  mayúsculas.
* Los caracteres acentuados de los alfabetos español/francés **no están
  soportados** y se descartan en silencio. `VIEJO` vale, `PERA` no.
* Los caracteres fuera del conjunto soportado (por ejemplo `@`, `[`, `\`, `]`,
  `_`, `{`, `|`, `}`) se descartan en silencio.
* El ajuste de línea parte la línea a los `TEXT WIDTH` caracteres (24 por
  defecto) e inserta un salto de línea. Parte por espacios, así que las
  palabras largas no se dividen.
* Los textos idénticos se guardan una sola vez.

### 13.3 Diálogos

```
%RES = DIALOG "MAS FRUTA", "OTRO LUGAR"
```

* Hasta **tres** opciones.
* Las cadenas de las opciones pasan por el mismo codificador de 5 bits, así que
  aplican las mismas restricciones de caracteres.
* **Las comas son separadores de opciones**: una opción no puede contener
  comas. Los espacios valen tal cual (se codifican con el valor 31 del
  codificador de 5 bits). Además, en las opciones de diálogo un `_` en el
  fuente se convierte en un espacio antes de codificarse, por si prefieres
  escribirlo así.
* El intérprete descodifica las opciones en `msc_options [0..2]` (las que no
  hay quedan como `""`), pone en `msc_n_options` cuántas hay y llama a tu
  `dialog_box ()` de `extern.h`, que devuelve la elegida (ver la
  [sección 15](#15-tu-código-externh)).

---

## 14. El inventario de un solo hueco

MSC4 trae una pequeña comodidad para los güegos en los que el jugador sólo
puede llevar **un** objeto a la vez (una llave, un medallón…). Es la
combinación de las directivas `ITEM SLOT` / `ITEM EMPTY`, la acción
`GET ITEM SET` y la sección `SPECIAL TILE TOUCHED`.

La idea:

* Un flag (el *hueco de objeto*, p.ej. `ITEM SLOT = 0`) guarda el número de
  tile del objeto que lleva el jugador. `ITEM EMPTY` (0 por defecto) quiere
  decir "no lleva nada".
* Otro flag por objeto registra si ya se ha recogido.
* Los objetos se colocan en el mapa como tiles con comportamiento `128` (bit 7
  del comportamiento puesto).
* Cuando el jugador anda sobre uno de esos tiles, el motor dispara
  `SPECIAL TILE TOUCHED`, con `TN` = el número de tile y `TX`/`TY` = sus
  coordenadas.

En el script:

```
SPECIAL TILE TOUCHED
	IF TN = 18
	THEN
		GET ITEM SET %LLAVE
		SOUND 7
	END
END
```

`GET ITEM SET $F`:

* no hace nada si el hueco de objeto no está vacío;
* si no, pone el número de tile en el hueco de objeto;
* quita el tile de la pantalla (tile 0 en `TX`, `TY`);
* pone el flag `$F` a 1.

Para que el objeto que llevas se vea en el marcador, define `ITEM_X` e
`ITEM_Y` en `config.h`: el motor pinta ahí el tile que haya en el hueco de
objeto cada vez que cambia.

---

## 15. Tu código: `extern.h`

`dev/extern.h` es del güego, no del motor. Se incluye sólo si algún script
usa `EXTERN`, `TEXT BOX` o `DIALOG`, y trae las tres funciones vacías, cada
una bajo el `#ifdef` que la activa:

```c
#ifdef MSC_AU_E4
	void do_extern_action (unsigned char n, unsigned char m) {
		// EXTERN n, m
	}
#endif

#ifdef MSC_AU_E6
	void text_box (void) {
		// TEXT BOX "...": el texto, en ASCII, está en msc_text_buf, partido
		// en líneas de MSC_TEXT_WIDTH caracteres con '\n'.
	}
#endif

#ifdef MSC_RV_E6
	unsigned char dialog_box (void) {
		// $F = DIALOG "A", "B", "C": las opciones están en msc_options [0],
		// [1] y [2] ("" si no hay) y cuántas hay en msc_n_options.
		// Devuelve la elegida: 1, 2 o 3.
		return 1;
	}
#endif
```

* **`EXTERN n, m`** llama a `do_extern_action (n, m)`. Es la puerta hacia
  cualquier cosa que el lenguaje no sepa hacer: un `switch (n)` con un caso
  por cada cosa que necesite tu güego.

  ```c
  void do_extern_action (unsigned char n, unsigned char m) {
  	switch (n) {
  		case 0: /* pon a cero la tabla de cosas cogidas */ break;
  		case 1: /* apunta que se ha cogido la cosa m */ break;
  		case 2: /* actualiza el marcador */ break;
  	}
  }
  ```

* **`TEXT BOX`** descodifica el texto en `msc_text_buf` y llama a
  `text_box ()`. Dibujar la caja, esperar a que se pulse una tecla y
  borrarla es cosa tuya; para borrarla puedes repintar la pantalla con
  `redraw_scr ()`.
* **`DIALOG`** descodifica las opciones en `msc_options [0..2]`, pone en
  `msc_n_options` cuántas hay y llama a `dialog_box ()`, que tiene que
  presentar las opciones, dejar elegir una y devolver 1, 2 o 3.

`tests/script/extern.h` es un ejemplo completo: un recuadro centrado en la
zona de juego, espera a una tecla, opciones que se eligen con 1, 2 o 3 y
`redraw_scr ()` para borrarlo.

---

## 16. Juegos con niveles

Con `COMPRESSED_LEVELS` (capítulo 10 del manual) cada nivel tiene su
script. Se compilan todos juntos (la lista va en `dev/scripts.txt`) y cada
`.spt.bin` se comprime con `zx0` en tu `levels.bat` y se pone en
`librarian.txt` como un recurso más. La tabla de niveles (`levelset.h`) lleva
el recurso del script en el último campo:

```c
const LEVEL levels [MAX_LEVELS] = {
	// bundle      tileset        spriteset      música  script
	{ RES_LEVEL1C, RES_TILESET1C, RES_SPRITES1C, 2,      RES_SCRIPT1C },
	{ RES_LEVEL2C, NO_RESOURCE,   NO_RESOURCE,   3,      NO_RESOURCE },
};
```

Al empezar cada nivel el motor descomprime su script; un nivel sin script
(`NO_RESOURCE`) no ejecuta nada. Los flags se ponen a 0 al empezar cada
nivel, y `ENTERING GAME` se ejecuta al principio de cada uno. `tests/levels`
es un ejemplo con dos niveles, cada uno con su script. Ver también
[`formato-niveles.md`](formato-niveles.md).

Sin niveles se usa el primer script de la lista. Un güego con varios
scripts pero sin niveles puede cambiar de script desde `custom.h`
(`msc_script = msc_scripts [SCRIPT_OTRO];`).

---

## 17. Ejemplos

### 17.1 Una caja que se coge y se suelta

Un güego con una caja (un cajón) que el jugador puede coger y dejar. La posición de la caja se guarda en tres
flags, y una subrutina hace el pintado de verdad, porque hay que hacerlo tanto
al coger la caja como al soltarla.

```
# Box
# =======

# The box is initialised for each "level" in the screen it first appears if
# %NEWLEVEL = 1. %BOXP, %BOXX, %BOXY, %BOXT control the location and the tile
# it overwrites.
# We use %BOXP = 99 to signify we have the box.

SUB PLACEBOX
	# Make sure the box is placed using the right tile
	IF TRUE
	THEN
		%BOXT = TILE AT (%BOXX, %BOXY)
		%AUX = 33
	END

	IF %BOXT > 0
	IF %BOXT < 7
	THEN
		%AUX = %BOXT
		INC %AUX, 33
	END

	IF TRUE
	THEN
		SET TILE (%BOXX, %BOXY) = %AUX
	END
END
```

Notas:

* Los bloques `SUB` tienen exactamente el mismo aspecto que las secciones.
* `%BOXT = TILE AT (%BOXX, %BOXY)` lee el tile que hay ahora mismo bajo la
  caja, para poder restaurarlo.
* `IF %BOXT > 0` / `IF %BOXT < 7` implementan "0 < x < 7" (no hay `&&`).

La caja se coge y se suelta en la sección `PRESS FIRE AT ANY`:

```
PRESS_FIRE AT ANY
	# We don't have expressions so...
	IF TRUE
	THEN
		%AUX = TY
		INC %AUX, 1
		%TAUX = TILE AT (TX, %AUX)
	END

	# Get the box
	IF %BOX9 <> 99
	IF %TAUX > 32
	IF %TAUX < 41
	THEN
		%BOXP = 99
		SET TILE (TX, %AUX) = %BOXT
		SOUND 1
		%CARRYING = 33
		BREAK
	END

	# Place the box
	IF %BOXP = 99
	IF BEH AT (TX, %AUX) <> 0
	IF TY > 0
	THEN
		%BOXP = NPANT
		%BOXX = TX
		%BOXY = TY
		DEC PY, 20
		SOUND 1
		CALL PLACEBOX
		%CARRYING = 47
	END

END
```

Notas:

* `BREAK` evita que la cláusula de "soltar la caja" se ejecute en el mismo
  frame que la de "coger la caja".
* `NPANT`, `TX`, `TY`, `PY` son variables especiales usadas como valores
  corrientes.
* `CALL PLACEBOX` devuelve al medio de la cláusula.

### 17.2 Un script completo y autocontenido

```
# ------------------------------------------------------------------
# A tiny example: a door that opens when you press the action key
# while standing on the right tile, and a box you can pick up.
# ------------------------------------------------------------------

ROOMS = 8

# The flag that holds the item we are carrying.
ITEM SLOT = 0
ITEM EMPTY = 47
ALIAS %CARRYING = 0
ALIAS %DOOR_OPEN = 1
ALIAS %HAS_KEY = 2

# Text boxes are wrapped at 22 characters.
TEXT WIDTH = 22

# ------------------------------------------------------------------
# New game: reset everything.
# ------------------------------------------------------------------

ENTERING GAME
	IF TRUE
	THEN
		%CARRYING = EMPTY
		%DOOR_OPEN = 0
		%HAS_KEY = 0
	END
END

# ------------------------------------------------------------------
# Screen 3 has the key; screen 5 has the door.
# ------------------------------------------------------------------

ENTERING SCREEN 3
	IF %HAS_KEY = 0
	THEN
		# The key has behaviour 128, so it is a "special tile".
		SET TILE (7, 4) = 16
	END
END

ENTERING SCREEN 5
	IF %DOOR_OPEN = 0
	THEN
		SET TILE (10, 6) = 17
	END
END

# ------------------------------------------------------------------
# Picking the key up: it is a tile with behaviour 128, so the engine
# fires SPECIAL TILE TOUCHED when we walk over it.
# ------------------------------------------------------------------

SPECIAL TILE TOUCHED
	IF TN = 16
	THEN
		GET ITEM SET %HAS_KEY
		SOUND 7
	END
END

# ------------------------------------------------------------------
# Opening the door: press the action key while standing on it.
# ------------------------------------------------------------------

PRESS FIRE AT SCREEN 5
	IF %DOOR_OPEN = 0
	IF %HAS_KEY = 1
	IF PLAYER AT (10, 6)
	THEN
		%DOOR_OPEN = 1
		SET TILE (10, 6) = 0
		%CARRYING = EMPTY
		SOUND 2
		TEXT BOX "THE DOOR IS OPEN."
	END
END
```

### 17.3 Una máquina de estados con diálogo

La expresión `DIALOG` junto con `RERUN` permite que una sección se comporte
como una corrutina. `PARAM` le dice a la sección en qué "paso" está.

```
# %STATE = 0 : we have not talked to the old man yet
# %STATE = 1 : he asked us to get more fruit
# %STATE = 2 : we have talked twice, we are done

ENTERING GAME
	IF TRUE
	THEN
		%STATE = 0
	END
END

ENEMY TOUCHED
	IF EN_T = 1
	THEN
		# Did we already talk to him?
		IF %STATE = 0
		THEN
			%STATE = 1
			TEXT BOX "BRING ME MORE FRUIT AND WE WILL SPLIT IT."
			%ANSWER = DIALOG "OK", "NO WAY"
			RERUN %ANSWER
		END

		# PARAM is 1 or 2 depending on the option the player chose.
		IF %STATE = 1
		IF PARAM = 1
		THEN
			TEXT BOX "GOOD BOY. GO AND FETCH MORE."
			%STATE = 2
			BREAK
		END

		IF %STATE = 1
		IF PARAM = 2
		THEN
			TEXT BOX "THEN GO AWAY!"
			%STATE = 2
			BREAK
		END
	END
END
```

Cómo funciona:

* `%STATE` es un flag normal: sobrevive entre ejecuciones de la sección.
* `DIALOG` devuelve 1, 2 o 3.
* `RERUN %ANSWER` pone `PARAM` a ese valor y reinicia la sección desde arriba;
  la sección entonces encuentra la rama `IF PARAM = …` que corresponde.
* El `BREAK` al final de una rama para la sección, de modo que las otras
  cláusulas `IF PARAM = …` no se evalúan.

### 17.4 El idioma `&%ALIAS`

Un güego en el que el mismo código tiene que abrir cuatro puertas distintas y
recoger cuatro medallones distintos, pero el *flag* que hay que poner sólo se
conoce al jugar:

```
# Draw medallions
# Note how we use & to know the actual flag #

ENTERING SCREEN 3
	IF %MEDA1 = 0
	THEN
		SET TILE (8, 1) = 37
		%MX = 8
		%MY = 1
		%K = 37
		%G = &%MEDA1
	END
END
```

y más tarde, cuando el jugador usa el medallón en una cripta:

```
PRESS FIRE AT ANY
	IF %DGX <> 0
	IF PLAYER TOUCHES (%DGX, %GY)
	IF %CARRYING = %K
	THEN
		%CARRYING = EMPTY
		SET TILE (%GX, %GY) = 0
		$%G = 1          # set the flag whose number is in %G
		SOUND 2
	END
END
```

* `&%MEDA1` evalúa al *número* del flag ligado a `%MEDA1`.
* `%G` guarda ese número.
* `$%G = 1` pone a 1 el flag cuyo número está guardado en `%G`.

---

## 18. Apéndice: el binario y el intérprete

### 18.1 El índice de secciones

El índice es una tabla de offsets de 16 bits little endian, uno por hueco de
sección:

| Hueco | Sección |
|---|---|
| 0 | `ENTERING GAME` |
| 1 | `ENTERING ANY` |
| 2 | `PRESS FIRE AT ANY` |
| 3 | `PLAYER GOT SOMETHING` |
| 4 | `PLAYER KILLS ENEMY` |
| 5 | `SPECIAL TILE TOUCHED` |
| 6 | `TIMER ZERO` |
| 7 | `TILE PUSHED` |
| 8 | `ENEMY TOUCHED` |
| 9 | `TILE DESTROYED` |
| 10…14 | reservados |
| 15 | el número de pantallas del índice (`ROOMS`), para que el intérprete no lea fuera de él |
| 16 + 2n | `ENTERING SCREEN n` |
| 17 + 2n | `PRESS FIRE AT SCREEN n` |

El índice tiene `16 + 2 * ROOMS` entradas. Un offset de `0` quiere decir "no
existe esa sección". Los offsets cuentan desde el principio del binario
(incluyen el tamaño del índice).

### 18.2 El bytecode de una sección

Una sección es una secuencia de cláusulas, terminada con `$FF`:

```
clausula  clausula  ...  clausula  $FF
```

y una cláusula es:

```
<longitud> <condición>… $FF <acción>… [$FF]
```

* El byte de longitud le dice al intérprete dónde empieza la siguiente
  cláusula, así que una cláusula se puede saltar en O(1) cuando una condición
  falla.
* El `$FF` que sigue a las condiciones significa "THEN": vienen las acciones.
* El `$FF` que sigue a las acciones significa "fin de cláusula". Se omite si
  la cláusula terminó con un terminador (`BREAK`, `WIN GAME`, `GAME OVER`,
  `RERUN`).

Un texto de `TEXT BOX` o una opción de `DIALOG` se guarda como su número en la
tabla de textos.

### 18.3 El mapa de opcodes

**Condiciones**

| Opcode | Significado |
|---|---|
| `$01` | `A = B` |
| `$02` | `A < B` |
| `$03` | `A >= B` |
| `$04` | `A <> B` |
| `$05` | `NPANT = N` (sólo con `FASTNPANT`) |
| `$21` | `PLAYER IN_X (a, b)` (píxeles) |
| `$22` | `PLAYER IN_Y (a, b)` (píxeles) |
| `$23` | `PLAYER AT (x, y)` (tile del centro) |
| `$24` | `PLAYER FALLING` (`vy > 0 && !possee`) |
| `$25` | `PLAYER NOT_FALLING` (`vy <= 0 \|\| possee`) |
| `$26` | `PLAYER STILL` |
| `$F0` | `TRUE` |

**Acciones**

| Opcode | Significado |
|---|---|
| `$00` | `FLAGS[a] = v` |
| `$01` | `FLAGS[a] += v` |
| `$02` | `FLAGS[a] -= v` |
| `$20` | `SET TILE (x, y) = t` |
| `$21` | `SET BEH (x, y) = b` |
| `$22` | lista de `DECOS` |
| `$30` | `GET ITEM SET $f` |
| `$50` | `PRINT TILE (x, y) = t` |
| `$51` | `SET FIRE ZONE x1, y1, x2, y2` |
| `$52` | `SET FIRE ZONE TILES x1, y1, x2, y2` |
| `$03` | `FLIPFLOP $f` |
| `$60` | `REENTER` |
| `$61` | `REDRAW` |
| `$62` | `REPOSTN x, y` |
| `$63` / `$64` | `ENEMY n ON` / `OFF` |
| `$65` | `SAFE x, y` |
| `$6D` | `WARP TO n, x, y` |
| `$6E` | `WARP TO LEVEL l, n, x, y, s` |
| `$E0` | `SOUND n` |
| `$E1` | `SHOW` |
| `$E2` | `RECHARGE` |
| `$E3` | `TEXT "…"` (en línea) |
| `$E4` | `EXTERN n, m` |
| `$E5` | `PAUSE n` |
| `$E6` | `TEXT BOX "…"` (número de texto) |
| `$E7` | `MUSIC n` |
| `$F0` | `WIN GAME` |
| `$F1` | `GAME OVER` |
| `$F2` | `BREAK` |
| `$F3` | `RERUN v` |
| `$F4` | `CALL` (dirección de la subrutina) |
| `$F5` | `GAME ENDING` |

### 18.4 El intérprete

`src/dev/msc.h` es una pequeña máquina:

```
msc_run         ; busca la sección en el índice y la ejecuta
msc_clausules   ; recorre las cláusulas: lee la longitud de cada una
msc_conditions  ; evalúa las condiciones (sale en cuanto una falla)
msc_actions     ; ejecuta las acciones
msc_value       ; lee un valor: literal, flag (con indirección) o variable especial
```

Cada condición está bajo `#ifdef MSC_CU_xx`, cada acción bajo
`#ifdef MSC_AU_xx`, cada variable especial bajo `MSC_RV_xx` (leída) o
`MSC_LV_xx` (escrita) y cada sección bajo `MSC_SECT_*`, donde `xx` es su
opcode. `msc-config.h` define los que usan los scripts.

El intérprete mínimo (una sección, una condición, una acción) ocupa unos
750 bytes; con todo, unos 4 KB.

### 18.5 Reconstruir el compilador

msc4 está escrito en FreeBASIC (`msc4/`). `src/utils/build-windows.bat` lo
compila, junto con las demás utilidades, y deja `msc4.exe` en `src/utils`. A
mano:

```
fbc -x msc4.exe msc4.bas mtparser.bas cmdlineparser.bas mt5bitEsc.bas
```
