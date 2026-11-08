"""Gera out/creditos-imagens.txt (para colar na descrição do YouTube) a partir de src/media.json."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
import sys as _s
media = json.loads(Path(_s.argv[1]).read_text(encoding="utf-8")) if len(_s.argv) > 1 else json.loads((ROOT / "src" / "media.json").read_text(encoding="utf-8"))
seen, lines = set(), []
for sid in sorted(media):
    for f in media[sid]["files"]:
        key = f.get("page") or f["title"]
        if key in seen:
            continue
        seen.add(key)
        lines.append(f"• \"{f['title']}\" — {f.get('artist') or 'Desconhecido'} · {f.get('license')} · {f.get('page') or ''}".strip())
out = ROOT / "out" / "creditos-imagens.txt"
out.parent.mkdir(exist_ok=True)
header = ("Imagens: fotos reais com licença livre (CC0, domínio público, CC BY e CC BY-SA), obtidas pelo Openverse "
          "(WordPress Photo Directory, Metropolitan Museum of Art e Flickr). Mapas e artes gráficas: produção do canal. "
          "Paisagens e ruínas ilustram a narração e não são, necessariamente, o local exato dos fatos narrados.\n\n")
out.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")
print(f"{len(lines)} créditos → {out}")
