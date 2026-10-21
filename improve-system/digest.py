"""Resume las sesiones recientes de Claude Code en un digest compacto para /improve-system.

Lee ~/.claude/projects/*/*.jsonl modificados desde el último pase (o --days N) y guarda:
mensajes del usuario (recortados), comandos /skills lanzados, errores de herramientas y
mensajes que parecen una corrección. Escribe ~/.claude/improve-system/digest.md.
Todo es local: no hace ninguna llamada de red.

  python3 digest.py              # desde el último pase (7 días la primera vez)
  python3 digest.py --days 30    # forzar una ventana
  python3 digest.py --mark       # guardar «ahora» como último pase

Basado en improve-system de Armand Hespel (MIT): https://github.com/armandhespel-coder/improve-system
"""
import argparse, json, re, sys, time
from collections import Counter
from pathlib import Path

HOME = Path.home() / ".claude"
PROJECTS = HOME / "projects"
OUT = HOME / "improve-system"
STATE = OUT / "state.json"
MAX_CHARS = 50_000          # tiene que caber en una sola lectura (~25k tokens)
MSG_CHARS = 350

# Frases con las que el usuario corrige a Claude (español e inglés).
CORRECTION = re.compile(
    r"(^no[,.!\s]|\beso no\b|no es eso|así no|asi no|otra vez|de nuevo|te (he )?dicho|ya te dije|"
    r"te lo dije|por qu[eé] has|no funciona|sigue sin|sigue igual|sigue fallando|no va\b|está mal|esta mal|"
    r"mal hecho|te has equivocado|te equivocas|te has olvidado|se te ha olvidado|olvidaste|no te pedí|"
    r"no te he pedido|para(r)? ya|deshaz|vuelve a hacer|rehaz|no hagas|"
    r"that's wrong|not what i|you forgot|i told you|i said|try again)", re.I)

# Secretos que no deben acabar en el digest ni en el informe.
SECRET = re.compile(
    r"(eyJ[\w-]{10,}\.[\w-]{10,}\.[\w-]{5,}|sk-[\w-]{16,}|gh[pousr]_\w{20,}|xox[bpas]-[\w-]{10,}|"
    r"AKIA[0-9A-Z]{16}|(?:token|key|password|secret|contraseña)=\S+)", re.I)


def text_of(content):
    if isinstance(content, str):
        return content
    out = []
    for b in content or []:
        if isinstance(b, dict) and b.get("type") == "text":
            out.append(b.get("text", ""))
    return "\n".join(out)


def clean(s):
    m = re.search(r"<command-name>(.*?)</command-name>.*?<command-args>(.*?)</command-args>", s, re.S)
    if m:
        s = f"{m.group(1)} {m.group(2)}"
    s = re.sub(r"<(system-reminder|ide_[a-z_]+|local-command-[a-z]+|bash-stdout|bash-stderr)>.*?</\1>", "", s, flags=re.S)
    s = re.sub(r"<pasted_content[^>]*>.*?</pasted_content[^>]*>", "[texto pegado]", s, flags=re.S)
    s = re.sub(r"<[^>]{1,40}>", "", s)
    s = SECRET.sub("[oculto]", s)
    return re.sub(r"\s+", " ", s).strip()


def session(path):
    humans, errors, commands, tools, interrupts = [], [], [], Counter(), 0
    proj, start = path.parent.name, None
    for line in path.open(encoding="utf-8", errors="replace"):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("isSidechain"):
            continue
        start = start or d.get("timestamp")
        if d.get("cwd"):
            proj = Path(d["cwd"]).name
        msg = d.get("message") or {}
        content = msg.get("content")
        if d.get("type") == "assistant" and isinstance(content, list):
            for b in content:
                if isinstance(b, dict) and b.get("type") == "tool_use":
                    tools[b.get("name", "?")] += 1
        if d.get("type") != "user":
            continue
        if isinstance(content, list):
            for b in content:
                if isinstance(b, dict) and b.get("type") == "tool_result" and b.get("is_error"):
                    c = b.get("content")
                    e = clean(c if isinstance(c, str) else text_of(c))
                    if e and "doesn't want" not in e and "rejected" not in e:
                        errors.append(e[:200])
        if d.get("toolUseResult") is not None or d.get("isMeta"):
            continue
        raw = text_of(content)
        if not raw or raw.startswith("Tool loaded") or "<task-notification>" in raw:
            continue
        if raw.startswith("[Request interrupted"):
            interrupts += 1
            continue
        m = re.search(r"<command-name>/?(.*?)</command-name>", raw)
        if m:
            commands.append(m.group(1))
        t = clean(raw)
        if t:
            humans.append(t)
    return {"proj": proj, "start": (start or "")[:16].replace("T", " "), "humans": humans,
            "errors": errors, "commands": commands, "tools": tools, "interrupts": interrupts}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=float)
    ap.add_argument("--mark", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "informes").mkdir(exist_ok=True)
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    if a.mark:
        state["last_run"] = time.time()
        STATE.write_text(json.dumps(state))
        print("último pase guardado")
        return
    since = time.time() - a.days * 86400 if a.days else state.get("last_run", time.time() - 7 * 86400)
    recent = time.time() - 120     # ignorar la sesión en curso (se acaba de escribir)
    files = sorted((p for p in PROJECTS.glob("*/*.jsonl") if since < p.stat().st_mtime < recent),
                   key=lambda p: p.stat().st_mtime)
    sessions, seen = [], {}
    for s in map(session, files):          # sesiones reanudadas o bifurcadas repiten mensajes: quedarse con la última
        if s["humans"]:
            key = tuple(s["humans"][:4])
            if key in seen:
                sessions[seen[key]] = s
            else:
                seen[key] = len(sessions); sessions.append(s)

    cmds, tools, errs, per_proj, stops = Counter(), Counter(), Counter(), Counter(), Counter()
    for s in sessions:
        cmds.update(s["commands"]); tools.update(s["tools"]); per_proj[s["proj"]] += 1
        stops[s["proj"]] += s["interrupts"]
        errs.update(re.sub(r"\d+", "N", e)[:120] for e in s["errors"])

    head = [f"# Digest — {len(sessions)} sesiones desde {time.strftime('%Y-%m-%d %H:%M', time.localtime(since))}", "",
            "## Datos",
            "- Sesiones por proyecto: " + ", ".join(f"{p} {n}" for p, n in per_proj.most_common()),
            "- Skills / comandos lanzados: " + (", ".join(f"/{c} ×{n}" for c, n in cmds.most_common(25)) or "ninguno"),
            "- Veces que el usuario paró a Claude a mitad: " + (", ".join(f"{p} {n}" for p, n in stops.most_common() if n) or "ninguna"),
            "- Herramientas: " + ", ".join(f"{t} {n}" for t, n in tools.most_common(15)),
            "", "## Errores de herramientas que se repiten"]
    head += [f"- ×{n} {e}" for e, n in errs.most_common(20) if n > 1] or ["- nada repetido"]
    head += ["", "## Correcciones (mensajes que recolocan a Claude)"]
    for s in sessions:
        for h in s["humans"][1:]:
            if CORRECTION.search(h[:200]):
                head.append(f"- [{s['proj']}] {h[:MSG_CHARS]}")

    body = ["", "## Sesiones (1.er mensaje = el encargo; después, las repreguntas)"]
    for s in sessions:
        body.append(f"\n### {s['start']} · {s['proj']} · {len(s['humans'])} msj · {len(s['errors'])} errores · {s['interrupts']} paradas")
        for i, h in enumerate(s["humans"][:12]):
            body.append(f"{'>' if i == 0 else '-'} {h[:MSG_CHARS * (2 if i == 0 else 1)]}")
        if len(s["humans"]) > 12:
            body.append(f"- … +{len(s['humans']) - 12} mensajes")

    text = "\n".join(head)[: MAX_CHARS // 2]
    text += "\n".join(body)[: MAX_CHARS - len(text)]
    (OUT / "digest.md").write_text(text, encoding="utf-8")
    print(f"{len(sessions)} sesiones -> {OUT / 'digest.md'} ({len(text)} caracteres)")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
