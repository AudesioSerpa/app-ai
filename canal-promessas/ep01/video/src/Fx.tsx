import React from "react";
import { AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig, Easing } from "remotion";
import timeline from "./timeline.json";
import { GOLD, GOLD_DEEP, SERIF, BODY, SANS, PARCHMENT, goldText } from "./theme";

const cues = (timeline as any).cues as Record<string, number>;

// Fundo escuro e quente, com luz suave girando devagar
export const LightBg: React.FC<{ bg?: string }> = ({ bg }) => {
  const frame = useCurrentFrame();
  const rot = frame * 0.03;
  return (
    <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 40%, #2a1d0f 0%, #120c06 60%, #070503 100%)" }}>
      {bg ? <Img src={staticFile(bg)} style={{ position: "absolute", width: "100%", height: "100%", objectFit: "cover", filter: "blur(18px) brightness(0.32) saturate(0.8)", transform: "scale(1.15)" }} /> : null}
      <AbsoluteFill style={{ background: `conic-gradient(from ${rot}deg at 50% -10%, rgba(232,194,106,0) 0deg, rgba(232,194,106,0.10) 18deg, rgba(232,194,106,0) 36deg, rgba(232,194,106,0.07) 70deg, rgba(232,194,106,0) 95deg, rgba(232,194,106,0.09) 140deg, rgba(232,194,106,0) 170deg, rgba(232,194,106,0) 360deg)`, mixBlendMode: "screen" }} />
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at center, rgba(0,0,0,0) 45%, rgba(0,0,0,0.7) 100%)" }} />
    </AbsoluteFill>
  );
};

const useFade = (inAt = 0, len = 0.8) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return interpolate(frame, [inAt * fps, (inAt + len) * fps], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
};

const Rule: React.FC<{ w?: number; op?: number }> = ({ w = 420, op = 1 }) => (
  <div style={{ width: w, height: 2, margin: "26px auto", background: `linear-gradient(90deg, transparent, ${GOLD}, transparent)`, opacity: op }} />
);

const Center: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", textAlign: "center", padding: "0 160px" }}>{children}</AbsoluteFill>
);

const ATITUDES = ["Dar, mesmo tendo pouco", "Ser constante", "O Reino em primeiro lugar", "Aprender o contentamento"];

export const Fx: React.FC<{ name: string; dur: number; start?: number; bg?: string }> = ({ name, dur, start = 0, bg }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const sec = frame / fps;
  const rel = (cue: string) => (cues[cue] ?? 0) - start; // segundos desde o início da cena

  if (name === "titulo-serie") {
    const a = useFade(0.2), b = useFade(1.2);
    return (
      <AbsoluteFill>
        <LightBg bg={bg} />
        <Center>
          <div style={{ fontFamily: SANS, fontSize: 30, letterSpacing: 10, color: PARCHMENT, opacity: a }}>EPISÓDIO 1</div>
          <Rule op={a} />
          <div style={{ fontFamily: SERIF, fontSize: 74, lineHeight: 1.2, ...goldText, opacity: b }}>A promessa escrita<br />de dentro de uma prisão</div>
        </Center>
      </AbsoluteFill>
    );
  }

  if (name === "versiculo") {
    const t = Math.max(0.5, rel("versiculo"));
    const a = useFade(t, 1.2);
    const glow = 0.6 + 0.4 * Math.sin(sec * 1.2);
    return (
      <AbsoluteFill>
        <LightBg bg={bg} />
        <Center>
          <div style={{ fontFamily: SERIF, fontSize: 128, letterSpacing: 4, color: GOLD, opacity: a, textShadow: `0 0 ${40 * glow}px rgba(232,194,106,0.45), 0 4px 24px rgba(0,0,0,0.9)` }}>Filipenses 4:19</div>
          <Rule w={560} op={a} />
          <div style={{ fontFamily: BODY, fontStyle: "italic", fontSize: 40, color: PARCHMENT, opacity: a * 0.9 }}>Almeida Revista e Corrigida</div>
        </Center>
      </AbsoluteFill>
    );
  }

  if (name === "pleroo") {
    const a = useFade(0.3, 1), b = useFade(1.6, 1), c = useFade(3.2, 1);
    return (
      <AbsoluteFill>
        <LightBg bg={bg} />
        <Center>
          <div style={{ fontFamily: SANS, fontSize: 30, letterSpacing: 8, color: PARCHMENT, opacity: a }}>"SUPRIRÁ" NO GREGO</div>
          <div style={{ fontFamily: BODY, fontSize: 190, color: GOLD, opacity: b, textShadow: "0 0 40px rgba(232,194,106,0.35), 0 4px 24px rgba(0,0,0,0.9)", marginTop: 10 }}>πληρόω</div>
          <div style={{ fontFamily: BODY, fontStyle: "italic", fontSize: 52, color: PARCHMENT, opacity: b }}>pleróo</div>
          <Rule op={c} />
          <div style={{ fontFamily: SERIF, fontSize: 52, ...goldText, opacity: c }}>encher, completar</div>
        </Center>
      </AbsoluteFill>
    );
  }

  if (name === "das-segundo") {
    const tDas = Math.max(1, rel("das"));
    const tSeg = Math.max(tDas + 2, rel("segundo"));
    const intro = useFade(0.2, 0.8);
    const lineIn = useFade(tDas - 0.3, 0.7);
    const strike = interpolate(sec, [tSeg - 1.2, tSeg - 0.4], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
    const segS = spring({ frame: frame - Math.round(tSeg * fps), fps, config: { damping: 14, stiffness: 90 } });
    const dasOp = interpolate(sec, [tSeg + 0.6, tSeg + 1.6], [1, 0.25], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
    return (
      <AbsoluteFill>
        <LightBg bg={bg} />
        <AbsoluteFill style={{ alignItems: "center", paddingTop: 150 }}>
          <div style={{ fontFamily: SANS, fontSize: 30, letterSpacing: 10, color: PARCHMENT, opacity: intro }}>O DETALHE ESCONDIDO</div>
          <Rule op={intro} />
        </AbsoluteFill>
        <Center>
          <div style={{ display: "flex", alignItems: "baseline", gap: 36, opacity: lineIn, fontFamily: SERIF }}>
            <div style={{ position: "relative", fontSize: 120, color: PARCHMENT, opacity: dasOp }}>
              DAS
              <div style={{ position: "absolute", left: -10, right: -10, top: "52%", height: 10, background: "#c0392b", transformOrigin: "left center", transform: `scaleX(${strike}) rotate(-4deg)`, borderRadius: 5 }} />
            </div>
            <div style={{ fontSize: 66, color: PARCHMENT, fontFamily: BODY, fontStyle: "italic" }}>suas riquezas</div>
          </div>
          <div style={{ marginTop: 40, fontFamily: SERIF, fontWeight: 700, fontSize: 150, color: GOLD, opacity: Math.min(1, segS), transform: `scale(${0.7 + 0.3 * segS})`, textShadow: "0 0 50px rgba(232,194,106,0.5), 0 4px 24px rgba(0,0,0,0.9)" }}>
            SEGUNDO
          </div>
          <div style={{ fontFamily: BODY, fontStyle: "italic", fontSize: 60, color: PARCHMENT, opacity: Math.min(1, segS) }}>as suas riquezas</div>
        </Center>
      </AbsoluteFill>
    );
  }

  if (name === "quatro-atitudes") {
    const a = useFade(0.3), b = useFade(1.3);
    return (
      <AbsoluteFill>
        <LightBg bg={bg} />
        <Center>
          <div style={{ fontFamily: SERIF, fontSize: 200, color: GOLD, opacity: a, textShadow: "0 0 40px rgba(232,194,106,0.35)" }}>4</div>
          <div style={{ fontFamily: SERIF, fontSize: 66, ...goldText, opacity: b }}>atitudes da igreja de Filipos</div>
        </Center>
      </AbsoluteFill>
    );
  }

  if (name.startsWith("atitude-")) {
    const n = Number(name.split("-")[1]);
    const s = spring({ frame, fps, config: { damping: 16 } });
    const b = useFade(0.5);
    return (
      <AbsoluteFill>
        <LightBg bg={bg} />
        <Center>
          <div style={{ fontFamily: SANS, fontSize: 32, letterSpacing: 10, color: PARCHMENT, opacity: s }}>ATITUDE</div>
          <div style={{ fontFamily: SERIF, fontSize: 210, color: GOLD, lineHeight: 1, opacity: s, transform: `scale(${0.8 + 0.2 * s})`, textShadow: "0 0 40px rgba(232,194,106,0.4)" }}>{n}</div>
          <Rule op={b} />
          <div style={{ fontFamily: SERIF, fontSize: 80, ...goldText, opacity: b }}>{ATITUDES[n - 1]}</div>
        </Center>
      </AbsoluteFill>
    );
  }

  if (name === "resumo-atitudes") {
    const ts = ["r1", "r2", "r3", "r4"].map((c, i) => Math.max(0.3 + i * 0.6, rel(c)));
    return (
      <AbsoluteFill>
        <LightBg bg={bg} />
        <Center>
          <div style={{ textAlign: "left" }}>
            {ATITUDES.map((t, i) => {
              const op = interpolate(sec, [ts[i] - 0.2, ts[i] + 0.5], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
              return (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: 40, margin: "22px 0", opacity: op, transform: `translateX(${(1 - op) * -30}px)` }}>
                  <div style={{ fontFamily: SERIF, fontSize: 84, color: GOLD, width: 80, textAlign: "center" }}>{i + 1}</div>
                  <div style={{ fontFamily: SERIF, fontSize: 64, color: PARCHMENT, textShadow: "0 2px 14px rgba(0,0,0,0.8)" }}>{t}</div>
                </div>
              );
            })}
          </div>
        </Center>
      </AbsoluteFill>
    );
  }

  if (name === "proximo") {
    const a = useFade(0.2), b = useFade(1.0);
    return (
      <AbsoluteFill>
        <LightBg bg={bg} />
        {/* texto no alto à esquerda: o resto da tela fica livre para a tela final do YouTube */}
        <div style={{ position: "absolute", top: 110, left: 120 }}>
          <div style={{ fontFamily: SANS, fontSize: 30, letterSpacing: 10, color: PARCHMENT, opacity: a }}>PRÓXIMO EPISÓDIO</div>
          <div style={{ width: 380, height: 2, margin: "22px 0", background: `linear-gradient(90deg, ${GOLD}, transparent)`, opacity: a }} />
          <div style={{ fontFamily: SERIF, fontSize: 84, ...goldText, opacity: b }}>A viúva de Sarepta</div>
          <div style={{ fontFamily: BODY, fontStyle: "italic", fontSize: 40, color: PARCHMENT, opacity: b, marginTop: 8 }}>1 Reis 17:8-16</div>
        </div>
      </AbsoluteFill>
    );
  }

  // fallback: cena sem mídia encontrada
  return <LightBg bg={bg} />;
};

export { GOLD_DEEP };
