import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile, useVideoConfig } from "remotion";
import timeline from "./timeline.json";
import mediaJson from "./media.json";
import { SceneView, SceneData } from "./Scene";
import { Overlay, OverlayData } from "./Overlay";
import { Vinheta } from "./Vinheta";
import { INK } from "./theme";
import overrides from "../scripts/overrides.json";
import mixkit from "./mixkit.json";

// vídeos reais do Mixkit (entram antes das fotos da cena)
const MIX = mixkit as unknown as Record<string, { file: string; dur: number; w: number; h: number }>;
// cenas puladas na revisão, a não ser que agora tenham vídeo
const SKIP = new Set<string>(((overrides as any)._skip ?? []).filter((id: string) => !MIX[id]));
const DROP = new Set<string>((overrides as any)._dropfiles ?? []);

export type EpisodeProps = { showCta: boolean };

type MediaMap = Record<string, { files: { file: string; type: "image" | "video"; w?: number; h?: number }[] }>;
const rawMedia = mediaJson as unknown as MediaMap;
// remove fotos descartadas na revisão
const media: MediaMap = Object.fromEntries(
  Object.entries(rawMedia).map(([k, v]) => [k, { files: v.files.filter((f) => !DROP.has(f.file.replace(/^media\//, "").replace(/\.\w+$/, ""))) }])
);
for (const [k, v] of Object.entries(MIX)) {
  const imgs = SKIP.has(k) || (overrides as any)._skip?.includes(k) ? [] : media[k]?.files ?? [];
  media[k] = { files: [{ file: v.file, type: "video", w: v.w, h: v.h, dur: v.dur } as any, ...imgs] };
}

const DISSOLVE = 0.9; // segundos

export const Episode: React.FC<EpisodeProps> = ({ showCta }) => {
  const { fps } = useVideoConfig();
  const f = (s: number) => Math.round(s * fps);
  // cenas puladas na revisão: a cena anterior continua na tela
  const scenes = (timeline.scenes as unknown as SceneData[]).filter((s) => !SKIP.has(s.id));
  const blocks = timeline.blocks as { block: number; start: number; duration: number; src: string; vinhetaAt?: number }[];
  const vinheta = blocks.find((b) => b.vinhetaAt !== undefined)!.vinhetaAt!;
  const VIN = 6;
  // fundo das peças gráficas: última foto anterior a elas
  const bgFor = (i: number) => {
    for (let j = i - 1; j >= 0; j--) {
      const fl = media[scenes[j].id]?.files?.find((x) => x.type === "image");
      if (fl) return fl.file;
    }
    return undefined;
  };

  return (
    <AbsoluteFill style={{ backgroundColor: INK }}>
      {/* Faixa visual */}
      {scenes.map((sc, i) => {
        const next = scenes[i + 1];
        let start = sc.t;
        let end = next ? next.t : timeline.total;
        // a vinheta ocupa a tela; a cena seguinte começa depois dela
        if (start < vinheta + VIN && end > vinheta) end = Math.max(start + 0.1, vinheta + 0.2);
        const prev = scenes[i - 1];
        const dissolve =
          !prev || prev.block !== sc.block || sc.kind.startsWith("map") || sc.kind.startsWith("fx") || prev.kind.startsWith("map") || prev.kind.startsWith("fx");
        const lead = dissolve && i > 0 ? DISSOLVE : 0;
        const from = f(start - lead);
        const dur = Math.max(1, f(end) - from);
        return (
          <Sequence key={sc.id} from={from} durationInFrames={dur + (next ? f(DISSOLVE) : 0)} layout="none">
            <SceneView scene={sc} files={media[sc.id]?.files ?? []} fadeIn={lead} index={i} sceneDur={(end - start) + lead} bg={bgFor(i)} />
          </Sequence>
        );
      })}

      {/* Vinheta */}
      <Sequence from={f(vinheta)} durationInFrames={f(VIN)}>
        <Vinheta />
      </Sequence>

      {/* Referências, lugares, títulos */}
      {(timeline.overlays as OverlayData[])
        .filter((o) => showCta || o.type !== "cta")
        .map((o, i) => (
          <Sequence key={i} from={f(o.t)} durationInFrames={f(o.d)} layout="none">
            <Overlay data={o} />
          </Sequence>
        ))}

      {/* Narração */}
      {blocks.map((b) => (
        <Sequence key={b.block} from={f(b.start)} durationInFrames={f(b.duration) + 2} layout="none">
          <Audio src={staticFile(b.src)} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
