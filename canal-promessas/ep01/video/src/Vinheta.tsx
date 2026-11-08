import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig, Easing } from "remotion";
import { GOLD, SERIF, SANS, PARCHMENT } from "./theme";

// Vinheta da série (6 s): luz dourada atravessa a tela e revela o título
export const Vinheta: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const sec = frame / fps;
  const sweep = interpolate(sec, [0.2, 2.2], [-40, 140], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) });
  const title = spring({ frame: frame - Math.round(1.1 * fps), fps, config: { damping: 18, stiffness: 70 } });
  const sub = interpolate(sec, [2.2, 3.0], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const out = interpolate(frame, [durationInFrames - 0.8 * fps, durationInFrames], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const inn = interpolate(sec, [0, 0.5], [0, 1], { extrapolateRight: "clamp" });
  const letter = interpolate(sec, [1.1, 4.5], [26, 14], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const particles = Array.from({ length: 40 }, (_, i) => {
    const x = (i * 97.3) % 100, y0 = (i * 53.7) % 100, sp = 0.6 + ((i * 13) % 10) / 10;
    const y = (y0 - sec * 4 * sp + 200) % 100;
    return <div key={i} style={{ position: "absolute", left: `${x}%`, top: `${y}%`, width: 3 + (i % 3), height: 3 + (i % 3), borderRadius: 9, background: GOLD, opacity: 0.25 + ((i * 7) % 10) / 25, filter: "blur(0.6px)" }} />;
  });
  return (
    <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 50%, #2b1e0e 0%, #0d0905 65%, #050302 100%)", opacity: inn * out }}>
      {particles}
      <AbsoluteFill style={{ background: `linear-gradient(105deg, transparent ${sweep - 18}%, rgba(255,226,150,0.35) ${sweep}%, transparent ${sweep + 18}%)`, mixBlendMode: "screen" }} />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", textAlign: "center" }}>
        <div style={{ fontFamily: SANS, fontSize: 28, letterSpacing: 12, color: PARCHMENT, opacity: sub }}>SÉRIE DE DOCUMENTÁRIOS</div>
        <div style={{ width: 520 * Math.min(1, title), height: 2, margin: "26px 0", background: `linear-gradient(90deg, transparent, ${GOLD}, transparent)` }} />
        <div style={{ fontFamily: SERIF, fontWeight: 700, fontSize: 150, letterSpacing: letter, color: GOLD, opacity: Math.min(1, title), transform: `scale(${0.9 + 0.1 * title})`, textShadow: "0 0 60px rgba(232,194,106,0.45), 0 6px 30px rgba(0,0,0,0.9)" }}>
          DEUS PROVERÁ
        </div>
        <div style={{ width: 520 * Math.min(1, title), height: 2, margin: "26px 0", background: `linear-gradient(90deg, transparent, ${GOLD}, transparent)` }} />
        <div style={{ fontFamily: "'Cormorant Garamond', serif", fontStyle: "italic", fontSize: 44, color: PARCHMENT, opacity: sub }}>As promessas de provisão na Bíblia</div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
