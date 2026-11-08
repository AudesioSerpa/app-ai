"""Baixa fotos e vídeos reais do Wikimedia Commons para cada cena do timeline.

- Só aceita licenças livres para uso comercial: domínio público, CC0, CC BY, CC BY-SA.
- Rejeita qualquer arquivo marcado como gerado por IA.
- Prefere imagens horizontais e com boa resolução.
- Grava os créditos em src/media.json (usados na descrição do YouTube).
"""
import json, math, re, subprocess, sys, time, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEDIA = ROOT / "public" / "media"
TL = ROOT / "src" / "timeline.json"
OUT = ROOT / "src" / "media.json"
UA = "DeusProveraDoc/1.0 (https://github.com/AudesioSerpa/app-ai; documentary research)"
API = "https://commons.wikimedia.org/w/api.php"
AI_WORDS = re.compile(r"ai[- ]generated|midjourney|dall[- ]?e|stable diffusion|generative ai|artificial intelligence generated|made with ai|firefly", re.I)
OK_LIC = re.compile(r"^(public domain|pd|cc0|cc[- ]by(-sa)?( \d\.\d)?|cc by(-sa)? \d\.\d.*|attribution|no restrictions)", re.I)
BAN = re.compile(r"nazi|swastika|ouija|auschwitz|kolbe|pataphysic|spiritual work|noose|rock ?& ?roll|nude|naked|renoir|judgement of paris|buddha|buddhist|hindu|ganesh|shiva|varanasi|bitcoin|crypto|pizza|cartoon|clip ?art|foursquare|halloween|tarot|occult|witch|skull", re.I)
PER_IMAGE = 13.0  # segundos por foto antes de trocar


def get(url, binary=False, tries=5):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Api-User-Agent": UA})
            with urllib.request.urlopen(req, timeout=90 if binary else 40) as r:
                data = r.read()
            return data if binary else json.loads(data)
        except Exception as e:  # 429 / 504 / rede
            wait = 65 if "429" in str(e) else 4 * (i + 1)
            print(f"   ! {e} — aguardando {wait}s", flush=True)
            time.sleep(wait)
    return None


def strip_html(s):
    return re.sub(r"<[^>]+>", "", s or "").strip()


OV = "https://api.openverse.org/v1/images/"
SRC_RANK = {"wordpress": 0, "met": 1, "flickr": 2}


def search(query, video=False):
    """Busca no Openverse (fotos reais com licença livre): WordPress Photo Directory (CC0),
    Metropolitan Museum (CC0) e Flickr (CC BY / CC BY-SA / CC0 / domínio público)."""
    if video:
        return []  # sem fonte de vídeo livre acessível: a cena usa fotos
    params = {"q": query, "source": "wordpress,met,flickr", "license_type": "commercial,modification",
              "page_size": 20, "mature": "false"}
    time.sleep(3.5)
    d = get(OV + "?" + urllib.parse.urlencode(params))
    if not d:
        return []
    res = []
    for i, r in enumerate(d.get("results", [])):
        tags = " ".join(t.get("name", "") for t in (r.get("tags") or []))
        if AI_WORDS.search(r.get("title") or "") or AI_WORDS.search(tags) or BAN.search(r.get("title") or "") or BAN.search(tags):
            continue
        w, h = r.get("width") or 0, r.get("height") or 0
        src = r.get("source", "")
        if src not in SRC_RANK or (w and w < 900):
            continue
        lic = r.get("license", "")
        lic_txt = "CC0" if lic == "cc0" else ("Domínio público" if lic == "pdm" else f"CC {lic.upper()} {r.get('license_version') or ''}".strip())
        res.append({
            "title": (r.get("title") or "Sem título")[:120], "url": r["url"], "page": r.get("foreign_landing_url"),
            "license": lic_txt, "artist": (r.get("creator") or "Desconhecido")[:120], "source": src,
            "w": w, "h": h, "landscape": (not w) or w >= h * 1.2, "rank": i,
        })
    res.sort(key=lambda c: (c["rank"] // 6, not c["landscape"], -(c["w"] or 2400)))
    return res


def to_mp4(src, dst):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-t", "40", "-an",
                    "-vf", "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=30",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", str(dst)], check=True)


def main():
    tl = json.loads(TL.read_text(encoding="utf-8"))
    scenes = tl["scenes"]
    media = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    used = {f["title"] for m in media.values() for f in m["files"]}
    # modo revisão: troca as cenas listadas em overrides.json
    ov_path = ROOT / "scripts" / "overrides.json"
    ov = json.loads(ov_path.read_text(encoding="utf-8")) if ov_path.exists() else {}
    if "--fix" in sys.argv:
        for fid in ov.get("_drop", []):
            sid, k = fid.rsplit("_", 1)
            if sid in media:
                media[sid]["files"] = [f for f in media[sid]["files"] if not f["file"].endswith(f"{sid}_{k}.jpg")] or media[sid]["files"]
        for sid, qs in ov.items():
            if sid.startswith("_") or media.get(sid, {}).get("fixed"):
                continue
            media.pop(sid, None)  # os títulos antigos continuam em `used`, então não voltam
        for sc in scenes:
            if sc["id"] in ov and not sc["id"].startswith("_"):
                sc["queries"] = ov[sc["id"]]
                sc["fix"] = True
    ends = [scenes[i + 1]["t"] for i in range(len(scenes) - 1)] + [tl["total"]]
    for sc, end in zip(scenes, ends):
        if sc["kind"] not in ("img", "vid") or sc["id"] in media:
            continue
        dur = end - sc["t"]
        video = sc["kind"] == "vid"
        want = 1 if video else max(1, math.ceil(dur / PER_IMAGE))
        print(f"{sc['id']} b{sc['block']} {sc['kind']} {dur:.0f}s → {want} · {sc['queries'][0]}", flush=True)
        cands = []
        for q in sc["queries"]:
            cands += search(q, video)
            if len([c for c in cands if c["title"] not in used]) >= 1:
                break
        if video and not cands:  # sem vídeo: cai para foto
            for q in sc["queries"]:
                cands += search(q, False)
                if cands:
                    break
            video = False
            want = max(1, math.ceil(dur / PER_IMAGE))
        fresh = [c for c in cands if c["title"] not in used]
        picks = (fresh + [c for c in cands if c["title"] in used])[:want]
        files = []
        for k, c in enumerate(picks):
            time.sleep(3)
            data = get(c["url"], binary=True)
            if not data:
                continue
            if video:
                tmp = MEDIA / f"{sc['id']}_tmp"
                tmp.write_bytes(data)
                name = f"{sc['id']}_{k}.mp4"
                try:
                    to_mp4(tmp, MEDIA / name)
                finally:
                    tmp.unlink(missing_ok=True)
            else:
                name = f"{sc['id']}_{k}{'r' if sc.get('fix') else ''}.jpg"
                tmp = MEDIA / f"{sc['id']}_{k}_orig"
                tmp.write_bytes(data)
                try:
                    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(tmp), "-vf", "scale='min(2400,iw)':-2", "-q:v", "3", "-frames:v", "1", str(MEDIA / name)], check=True)
                except subprocess.CalledProcessError:
                    print("   ! falha ao converter", c["title"]); continue
                finally:
                    tmp.unlink(missing_ok=True)
            used.add(c["title"])
            files.append({"file": f"media/{name}", "type": "video" if video else "image", **{x: c.get(x) for x in ("title", "page", "license", "artist", "source", "w", "h")}})
            print(f"   ✓ {c['title']} [{c['license']}]", flush=True)
        if files:
            media[sc["id"]] = {"files": files, **({"fixed": True} if sc.get("fix") else {})}
        else:
            print("   ✗ nada encontrado", flush=True)
        OUT.write_text(json.dumps(media, ensure_ascii=False, indent=1), encoding="utf-8")
    print("FIM", len(media), "cenas com mídia")


if __name__ == "__main__":
    main()
