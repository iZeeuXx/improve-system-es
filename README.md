# improve-system (en español)

Una skill para **Claude Code** que relee tus conversaciones con Claude y te entrega un informe:

- los errores que Claude repite;
- las tareas que le pides una y otra vez (→ una skill que crear);
- lo que haces a mano y se podría automatizar, con el tiempo que ganarías;
- las skills y reglas que sobran o se contradicen;
- y algún hábito tuyo que te hace perder tiempo.

Tú eliges qué aplicar («aplica la 1 y la 3» o «aplícalo todo») y Claude actualiza sus propias reglas o crea las skills.

**100 % local:** lee los archivos de conversación que Claude Code ya guarda en tu ordenador (`~/.claude/projects/`). No se envía nada a ningún sitio. El informe se guarda en `~/.claude/improve-system/informes/`.

## Qué cambia respecto al original

Es una adaptación de [improve-system](https://github.com/armandhespel-coder/improve-system) de **Armand Hespel** (en francés). Todo el mérito de la idea y del diseño es suyo. Esta versión:

- detecta tus correcciones **en español** («eso no», «otra vez», «te lo dije», «sigue sin funcionar»…) y en inglés;
- **oculta tokens, claves y contraseñas** antes de escribir el resumen;
- cuenta las **veces que paras a Claude** a mitad de una tarea (buena pista de que algo no va);
- tiene en cuenta los plugins instalados para no proponer lo que ya tienes;
- si tu `CLAUDE.md` indica una base de notas (por ejemplo, una bóveda de Obsidian), mira allí antes de proponer y apunta lo aprendido.

## Instalación

Necesitas **Claude Code** y **Python 3**.

**Lo más fácil:** pega esto en Claude Code.

```
Instala la skill improve-system desde https://github.com/iZeeuXx/improve-system-es :
copia la carpeta improve-system/ del repo en ~/.claude/skills/, luego ejecuta
python3 ~/.claude/skills/improve-system/digest.py --days 7 y dime cuántas sesiones ha encontrado.
```

**A mano:**

```
git clone https://github.com/iZeeuXx/improve-system-es
cp -r improve-system-es/improve-system ~/.claude/skills/
```

## Uso

En Claude Code, escribe `/improve-system` (una o dos veces por semana es lo ideal).
Lee el informe y responde «aplica la 1 y la 3» con las propuestas que te convenzan.

Para un periodo concreto: «/improve-system de los últimos 30 días».

## Qué hay dentro

- `improve-system/SKILL.md`: las instrucciones para Claude (análisis, formato del informe, cómo aplicar).
- `improve-system/digest.py`: resume tus sesiones recientes en un archivo compacto (mensajes, comandos, errores de herramientas, correcciones), para que Claude no tenga que leer megas de registros.

## Privacidad

El resumen y los informes contienen trozos de tus conversaciones. Se quedan en tu ordenador; no los subas a ningún sitio público.

## Licencia

MIT. Original © 2026 Armand Hespel · versión en español © 2026 iZeeuXx.
