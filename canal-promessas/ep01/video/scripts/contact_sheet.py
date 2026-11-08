"""Monta folhas de contato (miniaturas com o id da cena e a frase da narração) para revisar as fotos.
Uso: python3 scripts/contact_sheet.py BLOCO_INICIAL BLOCO_FINAL
"""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).parent))
from plan import S  # noqa: E402

b0, b1 = int(sys.argv[1]), int(sys.argv[2])
tl = json.loads((ROOT / "src" / "timeline.json").read_text(encoding="utf-8"))
media = json.loads((ROOT / "src" / "media.json").read_text(encoding="utf-8"))
anchors = {f"s{i:03d}": s["anchor"] for i, s in enumerate(S)}
items = []
for sc in tl["scenes"]:
    if not (b0 <= sc["block"] <= b1) or sc["id"] not in media:
        continue
    for k, f in enumerate(media[sc["id"]]["files"]):
        if f["type"] == "image":
            items.append((f"{sc['id']}_{k}", anchors[sc["id"]], ROOT / "public" / f["file"], f["title"]))
W, H, cols = 384, 216, 4
rows = (len(items) + cols - 1) // cols
sheet = Image.new("RGB", (cols * W, rows * (H + 58)), "black")
d = ImageDraw.Draw(sheet)
font = ImageFont.load_default(size=14)
for n, (sid, anchor, path, title) in enumerate(items):
    x, y = (n % cols) * W, (n // cols) * (H + 58)
    try:
        im = Image.open(path).convert("RGB")
        im.thumbnail((W, H))
        sheet.paste(im, (x + (W - im.width) // 2, y))
    except Exception:
        pass
    d.text((x + 4, y + H + 2), f"{sid}: {anchor[:44]}", fill="yellow", font=font)
    d.text((x + 4, y + H + 22), title[:52], fill="white", font=font)
out = ROOT / "out" / f"revisao-b{b0:02d}-b{b1:02d}.jpg"
out.parent.mkdir(exist_ok=True)
sheet.save(out, quality=80)
print(out, len(items))
