import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / "data/colombia_normas/constitucion.json").read_text(encoding="utf-8"))
bad = [a["numero"] for a in data["articulos"] if "Ã" in a["texto"] or "Â" in a["texto"]]
lines = [
    f"version={data['_version']} total={len(data['articulos'])} bad={bad}",
]
for n in [1, 10, 29, 370]:
    t = next(a["texto"] for a in data["articulos"] if a["numero"] == n)
    lines.append(f"Art{n}={t[:120]}")
(ROOT / "data/colombia_normas/_check.txt").write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
