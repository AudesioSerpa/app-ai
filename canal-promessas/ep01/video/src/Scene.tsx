import React from "react";
import { AbsoluteFill, Img, interpolate, Loop, OffthreadVideo, staticFile, useCurrentFrame, useVideoConfig, Easing } from "remotion";
import { MapScene } from "./MapScene";
import { Fx } from "./Fx";

export type SceneData = { id: string; block: number; kind: string; t: number };
type File = { file: string; type: "image" | "video"; w?: number; h?: number };

// movimentos lentos de câmera (zoom e panorâmica), alternados por cena
const MOVES = [
  { s0: 1.04, s1: 1.14, x0: 0, x1: -2, y0: 0, y1: -1 },
  { s0: 1.14, s1: 1.04, x0: -2, x1: 1, y0: 1, y1: 0 },
  { s0: 1.08, s1: 1.08, x0: -3, x1: 3, y0: 0, y1: 0 },
  { s0: 1.05, s1: 1.15, x0: 1, x1: 2, y0: 1, y1: -1 },
  { s0: 1.08, s1: 1.08, x0: 3, x1: -3, y0: -1, y1: 1 },
];

const KenBurns: React.FC<{ src: string; dur: number; seed: number }> = ({ src, dur, seed }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const m = MOVES[seed % MOVES.length];
  const p = interpolate(frame, [0, Math.max(1, dur * fps)], [0, 1], { extrapolateRight: "clamp", easing: Easing.inOut(Easing.sin) });
  const s = m.s0 + (m.s1 - m.s0) * p;
  const x = m.x0 + (m.x1 - m.x0) * p;
  const y = m.y0 + (m.y1 - m.y0) * p;
  return (
    <AbsoluteFill style={{ overflow: "hidden", backgroundColor: "#000" }}>
      {/* fundo desfocado para fotos verticais */}
      <Img src={staticFile(src)} style={{ position: "absolute", width: "100%", height: "100%", objectFit: "cover", filter: "blur(40px) brightness(0.45)", transform: "scale(1.2)" }} />
      <Img
        src={staticFile(src)}
        style={{ position: "absolute", width: "100%", height: "100%", objectFit: "cover", transform: `scale(${s}) translate(${x}%, ${y}%)` }}
      />
    </AbsoluteFill>
  );
};

const VideoClip: React.FC<{ src: string; dur: number }> = ({ src, dur }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = interpolate(frame, [0, Math.max(1, dur * fps)], [1.02, 1.08], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ overflow: "hidden", backgroundColor: "#000" }}>
      <Loop durationInFrames={Math.round(12 * fps)}>
        <OffthreadVideo src={staticFile(src)} muted style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${s})` }} />
      </Loop>
    </AbsoluteFill>
  );
};

const Vignette: React.FC = () => (
  <AbsoluteFill style={{ background: "radial-gradient(ellipse at center, rgba(0,0,0,0) 55%, rgba(0,0,0,0.55) 100%)" }} />
);

export const SceneView: React.FC<{ scene: SceneData; files: File[]; fadeIn: number; index: number; sceneDur: number; bg?: string }> = ({ scene, files, fadeIn, index, sceneDur, bg }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const opacity = fadeIn > 0 ? interpolate(frame, [0, fadeIn * fps], [0, 1], { extrapolateRight: "clamp" }) : 1;

  let content: React.ReactNode = null;
  if (scene.kind.startsWith("map:")) {
    content = <MapScene name={scene.kind.slice(4)} dur={sceneDur} />;
  } else if (scene.kind.startsWith("fx:")) {
    content = <Fx name={scene.kind.slice(3)} dur={sceneDur} start={scene.t - fadeIn} bg={bg} />;
  } else if (files.length === 0) {
    content = <Fx name="fallback" dur={sceneDur} bg={bg} />;
  } else if (files[0].type === "video") {
    content = <VideoClip src={files[0].file} dur={sceneDur} />;
  } else {
    // fotos divididas em partes iguais, com corte seco entre elas
    const part = sceneDur / files.length;
    const k = Math.min(files.length - 1, Math.floor(frame / fps / part));
    content = (
      <AbsoluteFill>
        {files.map((fl, j) =>
          j === k ? (
            <AbsoluteFill key={j}>
              <ShiftedKB src={fl.file} startSec={j * part} dur={part + 1} seed={index * 3 + j} portrait={!!fl.w && !!fl.h && fl.w < fl.h * 1.25} />
            </AbsoluteFill>
          ) : null
        )}
      </AbsoluteFill>
    );
  }
  return (
    <AbsoluteFill style={{ opacity }}>
      {content}
      {!scene.kind.startsWith("fx") && !scene.kind.startsWith("map") ? <Vignette /> : null}
    </AbsoluteFill>
  );
};

// Ken Burns que começa a contar do início da sua parte
const ShiftedKB: React.FC<{ src: string; startSec: number; dur: number; seed: number; portrait?: boolean }> = ({ src, startSec, dur, seed, portrait }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const local = frame - Math.round(startSec * fps);
  const m = MOVES[seed % MOVES.length];
  const p = interpolate(local, [0, Math.max(1, dur * fps)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.sin) });
  const s = m.s0 + (m.s1 - m.s0) * p;
  const x = m.x0 + (m.x1 - m.x0) * p;
  const y = m.y0 + (m.y1 - m.y0) * p;
  return (
    <AbsoluteFill style={{ overflow: "hidden", backgroundColor: "#000" }}>
      <Img src={staticFile(src)} style={{ position: "absolute", width: "100%", height: "100%", objectFit: "cover", filter: "blur(40px) brightness(0.45)", transform: "scale(1.2)" }} />
      <Img src={staticFile(src)} style={{ position: "absolute", width: "100%", height: "100%", objectFit: portrait ? "contain" : "cover", transform: portrait ? `scale(${0.96 + (s - 1) * 0.6})` : `scale(${s}) translate(${x}%, ${y}%)`, filter: portrait ? "drop-shadow(0 10px 40px rgba(0,0,0,0.8))" : undefined }} />
    </AbsoluteFill>
  );
};

export { KenBurns };
