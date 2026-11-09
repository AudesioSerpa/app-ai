"""Monta a faixa de narração completa a partir dos blocos e dos tempos de src/timeline.json."""
import json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
tl = json.loads((ROOT / "src" / "timeline.json").read_text())
out = sys.argv[1]
inputs, parts = [], []
for i, b in enumerate(tl["blocks"]):
    inputs += ["-i", str(ROOT / "public" / b["src"])]
    ms = round(b["start"] * 1000)
    parts.append(f"[{i}:a]aresample=48000,adelay={ms}|{ms}[a{i}]")
n = len(tl["blocks"])
filt = ";".join(parts) + ";" + "".join(f"[a{i}]" for i in range(n)) + f"amix=inputs={n}:normalize=0,apad,atrim=0:{tl['total']:.3f}[out]"
subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", filt, "-map", "[out]", "-ac", "2", "-c:a", "aac", "-b:a", "192k", out], check=True)
print("áudio ok", out)
