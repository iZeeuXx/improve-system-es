---
name: improve-system
description: Analiza el historial local de sesiones de Claude Code (~/.claude/projects/*.jsonl) y saca un informe con los errores que Claude repite, las tareas que el usuario rehace a mano y merecen una skill o un script, y las reglas que conviene añadir a CLAUDE.md o a la memoria. Úsala cuando el usuario diga «improve system», «mejora mi sistema», «analiza mis sesiones», «qué estoy haciendo mal con Claude» o «qué skills debería crear». Conviene lanzarla una o dos veces por semana.
---

# /improve-system: el sistema que se mejora solo

Todo es local: nada sale del ordenador. El informe son **propuestas**; solo se aplican cuando el usuario da el visto bueno (o dice «aplícalo todo»). Escribe el informe en el idioma del usuario y en lenguaje claro, sin jerga.

## 1. Digest

```
python3 ~/.claude/skills/improve-system/digest.py           # desde el último pase (7 días la primera vez)
python3 ~/.claude/skills/improve-system/digest.py --days 30 # si el usuario pide otro periodo
```

Lee `~/.claude/improve-system/digest.md` entero (una sola lectura). **Nunca** leas los `.jsonl` en bruto: son enormes.
Si sale 0 sesiones, di «nada nuevo desde el último pase» y para.

## 2. Contexto (para no proponer lo que ya existe)

- `~/.claude/CLAUDE.md` y los `CLAUDE.md` de los proyectos que salen en el digest (búsqueda dirigida, no leer todo).
- Memoria: `~/.claude/projects/*/memory/MEMORY.md` si existe.
- Skills instaladas: `~/.claude/skills`, `.claude/skills` de los proyectos y los plugins de `~/.claude/plugins/installed_plugins.json`.
- Informes anteriores: `~/.claude/improve-system/informes/` (no vuelvas a proponer algo ya rechazado o hecho).
- Si el `CLAUDE.md` indica una base de notas (p. ej. una bóveda de Obsidian), busca en ella con grep si el error o la idea ya está apuntado.

## 3. Análisis: busca PATRONES (2 veces o más), no anécdotas

El digest detecta correcciones por palabras clave: no entiende. Descarta el ruido (un «no» en una frase normal no es una corrección).

1. **Lo que Claude falla:** correcciones repetidas, los mismos errores de herramientas, instrucciones que ya estaban escritas y no se siguieron (→ reescribirlas o subirlas de sitio, no duplicarlas).
2. **Skills que crear:** encargos que se repiten con los mismos pasos, flujos de varios pasos rehechos a mano.
3. **Automatizaciones:** tareas largas y repetitivas (script, hook, tarea programada…) con el tiempo ganado estimado a partir de las sesiones (duración, número de repreguntas). Nunca inventes cifras.
4. **Limpieza:** skills o plugins que nunca se usan, reglas que se contradicen entre `CLAUDE.md`, memorias caducadas.
5. **Para ti:** hábitos del usuario que le cuestan tiempo (encargos poco claros, contexto que repite en cada sesión…). Con tacto.

Indica la confianza de cada hallazgo: «2 veces, a vigilar» es mejor que vender como seguro un falso positivo.

## 4. Informe

Escribe `~/.claude/improve-system/informes/AAAA-MM-DD.md`, corto:

```
# Mejora del sistema — <fecha> (<N> sesiones)
## Lo más importante (3 como mucho)
## 1. Lo que Claude falla        → regla exacta que añadir + archivo donde va
## 2. Skills que crear           → nombre, cuándo se activa, pasos, prueba (sesiones citadas)
## 3. Automatizaciones           → qué, cómo, tiempo ganado
## 4. Limpieza
## 5. Para ti
```

Cada propuesta: numerada, con 1 prueba (fecha + proyecto + cita corta) y el texto EXACTO que se pegaría. Máximo 10 propuestas.
No copies secretos (claves, tokens, contraseñas) ni datos personales sensibles al informe.
Después ejecuta `python3 ~/.claude/skills/improve-system/digest.py --mark`.

En el chat, enseña solo el resumen (lo más importante y la lista numerada en una línea cada una) y la ruta del informe.

## 5. Aplicar

Cuando el usuario responda «aplica la 1, 3 y 5» (o «todo»): haz los cambios (`CLAUDE.md`, memoria, skill nueva en `~/.claude/skills/<nombre>/SKILL.md`) y marca esas propuestas como hechas en el informe.
Si una propuesta es un error resuelto o un aprendizaje reutilizable y el `CLAUDE.md` indica una base de notas, apúntalo también allí siguiendo sus normas, y dilo en una línea.

---
Basado en [improve-system](https://github.com/armandhespel-coder/improve-system) de Armand Hespel (MIT).
