"""Calcula o tempo de cada frase-âncora dentro dos áudios e gera src/timeline.json.

Método: estima o início de cada parágrafo pela proporção de palavras (descontando
as pausas <break>), e "encaixa" esse início no fim de silêncio real mais próximo
detectado no áudio com o ffmpeg. Dentro do parágrafo, interpola pelas palavras.
"""
import json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NARR = ROOT.parent / "narracao"
AUDIO = ROOT / "public" / "audio"
sys.path.insert(0, str(Path(__file__).parent))
from plan import S, OVERLAYS, CUES  # noqa: E402

GAP = 1.2          # silêncio entre blocos (s)
VINHETA = 6.0      # vinheta depois do bloco 03 (s)
TAIL_END = 20.0    # espaço final para a tela final do YouTube (s)
FPS = 30


def duration(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]).strip())


def silence_ends(p):
    out = subprocess.run(["ffmpeg", "-i", str(p), "-af", "silencedetect=noise=-38dB:d=0.35", "-f", "null", "-"], capture_output=True, text=True).stderr
    return [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", out)]


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


def analyse_block(b):
    raw = (NARR / f"bloco-{b:02d}.txt").read_text(encoding="utf-8")
    dur = duration(AUDIO / f"bloco-{b:02d}.mp3")
    paras = [p for p in re.split(r"\n\s*\n", raw) if p.strip()]
    # tokens: palavras e pausas
    items = []  # (kind, value, para_idx)
    for i, p in enumerate(paras):
        for m in re.finditer(r'<break time="([0-9.]+)s" />|\S+', p):
            if m.group(1):
                items.append(("brk", float(m.group(1)), i))
            else:
                items.append(("w", m.group(0), i))
    nwords = sum(1 for k, *_ in items if k == "w")
    brk = sum(v for k, v, _ in items if k == "brk")
    k = (dur - brk - 0.4) / nwords
    # tempo estimado de cada item
    t, times = 0.15, []
    for kind, v, _ in items:
        times.append(t)
        t += k if kind == "w" else v
    # início estimado de cada parágrafo (primeira palavra)
    para_first = {}
    for idx, (kind, v, pi) in enumerate(items):
        if kind == "w" and pi not in para_first:
            para_first[pi] = idx
    sil = silence_ends(AUDIO / f"bloco-{b:02d}.mp3")
    snapped, last = {}, 0.0
    for pi in sorted(para_first):
        est = times[para_first[pi]]
        cands = [s for s in sil if abs(s - est) < 4.5 and s >= last]
        st = min(cands, key=lambda s: abs(s - est)) if cands and pi > 0 else est
        snapped[pi] = st
        last = st
    # recalcula tempos com correção por parágrafo (offset)
    corr, off = [], 0.0
    for idx, (kind, v, pi) in enumerate(items):
        if pi in para_first:
            off = snapped[pi] - times[para_first[pi]]
        corr.append(times[idx] + off)
    words = [(i, items[i][1]) for i in range(len(items)) if items[i][0] == "w"]
    return dur, words, corr


def find_anchor(words, corr, anchor, b):
    clean = lambda x: re.sub(r"[^\w]", "", x.lower())
    toks = [clean(x) for x in norm(anchor).split(" ") if clean(x)]
    seq = [clean(w) for _, w in words]
    for j in range(len(seq) - len(toks) + 1):
        if seq[j:j + len(toks)] == toks:
            return corr[words[j][0]]
    raise SystemExit(f"Âncora não encontrada no bloco {b}: {anchor!r}")


def main():
    blocks, t0 = [], 0.0
    data = {}
    for b in range(1, 14):
        dur, words, corr = analyse_block(b)
        data[b] = (words, corr)
        blocks.append({"block": b, "start": round(t0, 3), "duration": round(dur, 3), "src": f"audio/bloco-{b:02d}.mp3"})
        t0 += dur + GAP
        if b == 3:
            blocks[-1]["vinhetaAt"] = round(t0 - GAP + 0.6, 3)
            t0 += VINHETA
    total = t0 - GAP + TAIL_END
    bstart = {x["block"]: x["start"] for x in blocks}
    scenes = []
    for i, s in enumerate(S):
        words, corr = data[s["block"]]
        at = find_anchor(words, corr, s["anchor"], s["block"])
        scenes.append({"id": f"s{i:03d}", "block": s["block"], "kind": s["kind"], "queries": s["queries"], "t": round(bstart[s["block"]] + max(0, at - 0.25), 3)})
    overlays = []
    for (b, anchor, typ, text, d) in OVERLAYS:
        words, corr = data[b]
        at = find_anchor(words, corr, anchor, b)
        overlays.append({"block": b, "type": typ, "text": text, "t": round(bstart[b] + at + 0.4, 3), "d": d})
    cues = {}
    for (b, anchor, name) in CUES:
        words, corr = data[b]
        cues[name] = round(bstart[b] + find_anchor(words, corr, anchor, b), 3)
    out = {"cues": cues, "fps": FPS, "total": round(total, 3), "blocks": blocks, "scenes": scenes, "overlays": overlays}
    (ROOT / "src" / "timeline.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"total {total/60:.2f} min · {len(scenes)} cenas · {len(overlays)} overlays")


if __name__ == "__main__":
    main()
