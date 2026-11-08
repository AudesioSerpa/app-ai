"""Busca vídeos reais no Mixkit (licença gratuita, sem atribuição obrigatória) para as cenas de foto.
Uso: python3 scripts/fetch_mixkit.py           -> busca candidatos e grava src/mixkit.json
     python3 scripts/fetch_mixkit.py --sheet   -> folha de contato com as miniaturas para revisão
Só aceita vídeos com a "Mixkit Stock Video Free License"; ignora os de licença restrita (720p só para uso pessoal).
"""
import json, re, subprocess, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).parent))
from plan import S  # noqa: E402

UA = {"User-Agent": "Mozilla/5.0"}
OUT = ROOT / "src" / "mixkit.json"
PUB = ROOT / "public" / "mixkit"
STOP = {"the", "a", "of", "and", "in", "on", "at", "with", "over", "old", "ancient", "close", "up", "closeup", "view", "at"}
# temas que não queremos (IA, animação, festa, símbolos de outras religiões etc.)
BAN = re.compile(r"\b(ai|3d|animation|animated|render|cgi|digital|hologram|neon|party|club|halloween|buddha|buddhist|hindu|temple|bikini|sexy|kiss|wine|beer|cocktail|bar|casino|bitcoin|crypto|tarot|witch|skull|zombie|horror|gun|blood|cigarette|smoking|christmas|wedding|bridesmaid|jogging|motorcyclist|dancer|japan|avocado|surprised|eerie|cactus|greenhouses|holiday|stadium|business|handshake|fingernails)\b", re.I)

# buscas em inglês por cena (cenas de lugares antigos específicos ficam com as fotos)
Q = json.loads((Path(__file__).parent / "mixkit_queries.json").read_text(encoding="utf-8"))


def get(url, tries=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return ""
            time.sleep(3 * (i + 1))
        except Exception:
            time.sleep(3 * (i + 1))
    return ""


def search(q):
    slug = re.sub(r"[^a-z0-9]+", "-", q.lower()).strip("-")
    h = get(f"https://mixkit.co/free-stock-video/{slug}/")
    res, seen = [], set()
    for m in re.finditer(r'href="/free-stock-video/([a-z0-9-]+)-(\d+)/"', h):
        title, vid = m.group(1), m.group(2)
        if vid in seen or BAN.search(title.replace("-", " ")):
            continue
        seen.add(vid)
        res.append((vid, title))
    return res


def license_of(vid, title):
    h = get(f"https://mixkit.co/free-stock-video/{title}-{vid}/")
    if 'data-license="videoFree">Mixkit Stock Video Free License' in h and "Personal Use only" not in h:
        return "Mixkit Free License"
    return "restricted" if h else None


def fetch():
    data = json.loads(OUT.read_text()) if OUT.exists() else {}
    PUB.mkdir(parents=True, exist_ok=True)
    used = {v["id"] for v in data.values()} | set(Q.get("_badids", []))
    for sid, qs in Q.items():
        if sid.startswith("_") or sid in data:
            continue
        pick = None
        for q in qs:
            words = {w for w in re.findall(r"[a-z]+", q.lower()) if w not in STOP}
            for vid, title in search(q)[:12]:
                if vid in used:
                    continue
                tw = set(title.split("-"))
                if not words & tw:
                    continue
                lic = license_of(vid, title)
                if lic != "Mixkit Free License":
                    continue
                pick = (vid, title, q)
                break
            if pick:
                break
        if not pick:
            print(sid, "— nada", qs)
            continue
        vid, title, q = pick
        dst = PUB / f"{sid}_{vid}.mp4"
        # a página de download traz o link real (vídeos novos vêm em 1080p)
        links = re.findall(r'https://assets\.mixkit\.co/[^"]+\.mp4', get(f"https://mixkit.co/free-stock-video/download/{vid}/"))
        links = sorted(set(links), key=lambda u: ("1080" in u, "720" in u), reverse=True) or [f"https://assets.mixkit.co/videos/{vid}/{vid}-720.mp4"]
        subprocess.run(["curl", "-s", "-f", "-m", "300", "-A", "Mozilla/5.0", "-o", str(dst), links[0]], check=False)
        if not dst.exists() or dst.stat().st_size < 50000:
            print(sid, "falha download", vid)
            continue
        wh = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", str(dst)], capture_output=True, text=True).stdout.strip().split(",")
        if len(wh) == 2 and int(wh[1]) > int(wh[0]):  # vídeo vertical: não serve para TV
            dst.unlink()
            used.add(vid)
            print(sid, "vertical, descartado", vid)
            continue
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(dst)], capture_output=True, text=True).stdout.strip() or 0)
        data[sid] = {"id": vid, "file": f"mixkit/{dst.name}", "title": title.replace("-", " "), "page": f"https://mixkit.co/free-stock-video/{title}-{vid}/", "license": "Mixkit Free License", "dur": dur, "query": q}
        used.add(vid)
        OUT.write_text(json.dumps(data, indent=1, ensure_ascii=False))
        print(sid, "ok", title, f"{dur:.0f}s")


def sheet():
    from PIL import Image, ImageDraw, ImageFont
    data = json.loads(OUT.read_text())
    anchors = {f"s{i:03d}": s["anchor"] for i, s in enumerate(S)}
    items = sorted(data.items())
    W, H, cols = 384, 216, 4
    rows = (len(items) + cols - 1) // cols
    img = Image.new("RGB", (cols * W, rows * (H + 58)), "black")
    d = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=14)
    tmp = Path("/tmp/claude-0/mxthumb.jpg")
    for n, (sid, v) in enumerate(items):
        x, y = (n % cols) * W, (n // cols) * (H + 58)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(min(3, v["dur"] / 2)), "-i", str(ROOT / "public" / v["file"]), "-frames:v", "1", "-vf", f"scale={W}:{H}:force_original_aspect_ratio=decrease", str(tmp)])
        try:
            img.paste(Image.open(tmp), (x, y))
        except Exception:
            pass
        d.text((x + 4, y + H + 2), f"{sid}: {anchors[sid][:44]}", fill="yellow", font=font)
        d.text((x + 4, y + H + 22), v["title"][:52], fill="white", font=font)
    out = ROOT / "out" / "revisao-mixkit.jpg"
    img.save(out, quality=80)
    print(out, len(items))


if __name__ == "__main__":
    sheet() if "--sheet" in sys.argv else fetch()
