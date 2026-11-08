import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { GOLD, SERIF, SANS, PARCHMENT } from "./theme";

export type OverlayData = { block: number; type: "ref" | "place" | "title" | "credit" | "cta"; text: string; t: number; d: number };

export const Overlay: React.FC<{ data: OverlayData }> = ({ data }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const total = data.d * fps;
  const op = interpolate(frame, [0, 0.6 * fps, total - 0.7 * fps, total], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const rise = interpolate(frame, [0, 0.6 * fps], [14, 0], { extrapolateRight: "clamp" });

  if (data.type === "ref") {
    // referência bíblica: canto inferior esquerdo, dourada, legível na TV
    return (
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "flex-start", padding: "0 0 110px 110px", pointerEvents: "none" }}>
        <div style={{ opacity: op, transform: `translateY(${rise}px)`, display: "flex", alignItems: "center", gap: 22, padding: "16px 34px 16px 24px", background: "linear-gradient(90deg, rgba(10,7,3,0.78), rgba(10,7,3,0.35) 85%, rgba(10,7,3,0))", borderLeft: `4px solid ${GOLD}` }}>
          <div style={{ fontFamily: SERIF, fontWeight: 700, fontSize: 50, color: GOLD, letterSpacing: 1.5, textShadow: "0 2px 12px rgba(0,0,0,0.9)" }}>{data.text}</div>
        </div>
      </AbsoluteFill>
    );
  }

  if (data.type === "place") {
    return (
      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "flex-start", padding: "90px 0 0 110px", pointerEvents: "none" }}>
        <div style={{ opacity: op, transform: `translateY(${-rise}px)`, padding: "14px 40px 16px 22px", background: "linear-gradient(90deg, rgba(10,7,3,0.72), rgba(10,7,3,0.3) 85%, rgba(10,7,3,0))" }}>
          <div style={{ width: 70, height: 3, background: GOLD, marginBottom: 14 }} />
          <div style={{ fontFamily: SERIF, fontSize: 44, color: PARCHMENT, letterSpacing: 3, textShadow: "0 2px 14px rgba(0,0,0,0.95)" }}>{data.text}</div>
        </div>
      </AbsoluteFill>
    );
  }

  if (data.type === "title") {
    // título de seção: centralizado na parte de baixo
    return (
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 150, pointerEvents: "none" }}>
        <div style={{ opacity: op, textAlign: "center", transform: `translateY(${rise}px)` }}>
          <div style={{ fontFamily: SERIF, fontSize: 64, color: GOLD, letterSpacing: 4, textShadow: "0 3px 20px rgba(0,0,0,0.95)" }}>{data.text}</div>
          <div style={{ width: 360, height: 2, margin: "18px auto 0", background: `linear-gradient(90deg, transparent, ${GOLD}, transparent)` }} />
        </div>
      </AbsoluteFill>
    );
  }

  if (data.type === "credit") {
    return (
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "flex-end", padding: "0 90px 60px 0", pointerEvents: "none" }}>
        <div style={{ opacity: op * 0.9, fontFamily: SANS, fontSize: 24, color: "#e6dccb", maxWidth: 900, textAlign: "right", textShadow: "0 2px 10px rgba(0,0,0,1)" }}>{data.text}</div>
      </AbsoluteFill>
    );
  }

  // cta discreto (só quando showCta = true)
  return (
    <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "flex-end", padding: "70px 90px 0 0", pointerEvents: "none" }}>
      <div style={{ opacity: op * 0.9, fontFamily: SANS, fontWeight: 600, fontSize: 28, letterSpacing: 2, color: PARCHMENT, padding: "10px 22px", border: `1.5px solid ${GOLD}`, borderRadius: 40, background: "rgba(10,7,3,0.45)" }}>{data.text}</div>
    </AbsoluteFill>
  );
};
