import React, { useMemo } from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig, Easing } from "remotion";
import { geoMercator, geoPath } from "d3-geo";
import { feature } from "topojson-client";
import land from "world-atlas/land-50m.json";
import { GOLD, SERIF, SANS } from "./theme";

type City = { name: string; lon: number; lat: number; label?: "l" | "r" | "t" | "b"; key?: boolean };
type MapDef = { title: string; note?: string; route: City[]; extra?: City[]; seas?: { name: string; lon: number; lat: number }[]; pad?: number };

const C = (name: string, lat: number, lon: number, label: City["label"] = "r", key = true): City => ({ name, lat, lon, label, key });
const W = (lat: number, lon: number): City => ({ name: "", lat, lon, key: false }); // ponto de passagem sem nome

const MAPS: Record<string, MapDef> = {
  macedonia: {
    title: "Macedônia · Império Romano",
    note: "Via Egnácia (traçado aproximado)",
    route: [C("Dirráquio", 41.32, 19.45, "l"), W(41.1, 20.8), W(41.0, 21.33), W(40.8, 22.05), C("Tessalônica", 40.64, 22.94, "b"), C("Anfípolis", 40.82, 23.85, "t", false), C("Filipos", 41.01, 24.29, "t"), C("Neápolis", 40.94, 24.41, "b", false)],
    seas: [{ name: "Mar Egeu", lat: 39.3, lon: 24.6 }, { name: "Mar Adriático", lat: 41.6, lon: 17.6 }],
    pad: 160,
  },
  "troade-filipos": {
    title: "De Trôade a Filipos",
    note: "Rota aproximada · Atos 16:11-12",
    route: [C("Trôade", 39.75, 26.16, "r"), C("Samotrácia", 40.48, 25.53, "r"), C("Neápolis", 40.94, 24.41, "b"), C("Filipos", 41.01, 24.29, "t")],
    extra: [C("Tessalônica", 40.64, 22.94, "l", false)],
    seas: [{ name: "Mar Egeu", lat: 39.6, lon: 24.9 }],
    pad: 220,
  },
  "filipos-corinto": {
    title: "De Filipos a Corinto",
    note: "Rota aproximada · Atos 17-18",
    route: [C("Filipos", 41.01, 24.29, "t"), C("Anfípolis", 40.82, 23.85, "t", false), C("Tessalônica", 40.64, 22.94, "l"), C("Bereia", 40.52, 22.2, "l", false), W(39.5, 22.9), C("Atenas", 37.97, 23.73, "r"), C("Corinto", 37.91, 22.88, "l")],
    seas: [{ name: "Mar Egeu", lat: 39.0, lon: 24.8 }],
    pad: 170,
  },
  "jerusalem-roma": {
    title: "De Jerusalém a Roma",
    note: "Rota aproximada · Atos 21-28",
    route: [C("Jerusalém", 31.78, 35.23, "r"), C("Cesareia", 32.5, 34.89, "l"), W(33.56, 35.37), W(35.2, 32.0), C("Mirra", 36.26, 29.98, "t", false), W(35.5, 27.0), C("Creta", 34.93, 24.8, "b", false), W(35.5, 19.0), C("Malta · naufrágio", 35.95, 14.4, "b"), C("Siracusa", 37.07, 15.29, "r", false), W(38.11, 15.65), C("Putéoli", 40.82, 14.12, "r", false), C("Roma", 41.9, 12.5, "t")],
    seas: [{ name: "Mar Mediterrâneo", lat: 34.2, lon: 20.5 }],
    pad: 110,
  },
  "filipos-roma": {
    title: "A viagem de Epafrodito",
    note: "Rota aproximada · mais de 1.000 km",
    route: [C("Filipos", 41.01, 24.29, "t"), W(40.82, 23.85), C("Tessalônica", 40.64, 22.94, "b"), W(40.8, 22.05), W(41.0, 21.33), W(41.1, 20.8), C("Dirráquio", 41.32, 19.45, "t"), C("Brundísio", 40.64, 17.94, "b"), W(40.47, 17.24), W(40.96, 15.82), W(41.13, 14.78), C("Cápua", 41.08, 14.25, "b", false), C("Roma", 41.9, 12.5, "t")],
    seas: [{ name: "Mar Adriático", lat: 42.2, lon: 16.4 }, { name: "Mar Egeu", lat: 39.4, lon: 24.6 }],
    pad: 140,
  },
};

const landGeo = feature(land as any, (land as any).objects.land) as any;

export const MapScene: React.FC<{ name: string; dur: number }> = ({ name, dur }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const def = MAPS[name];

  const { projection, landPath, routePath, pts } = useMemo(() => {
    const all = [...def.route, ...(def.extra ?? [])];
    const bbox = { type: "MultiPoint", coordinates: all.map((c) => [c.lon, c.lat]) } as any;
    const proj = geoMercator().fitExtent([[def.pad ?? 150, (def.pad ?? 150) + 60], [width - (def.pad ?? 150), height - (def.pad ?? 150)]], bbox);
    const path = geoPath(proj);
    const line = def.route.map((c) => proj([c.lon, c.lat]) as [number, number]);
    // linha suave (Catmull-Rom -> Bézier)
    let d = `M ${line[0][0]} ${line[0][1]}`;
    for (let i = 0; i < line.length - 1; i++) {
      const p0 = line[i - 1] ?? line[i], p1 = line[i], p2 = line[i + 1], p3 = line[i + 2] ?? p2;
      const c1 = [p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6];
      const c2 = [p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6];
      d += ` C ${c1[0]} ${c1[1]}, ${c2[0]} ${c2[1]}, ${p2[0]} ${p2[1]}`;
    }
    // posição relativa (0-1) de cada ponto ao longo da linha, para acender as cidades na hora certa
    const seg = line.map((p, i) => (i === 0 ? 0 : Math.hypot(p[0] - line[i - 1][0], p[1] - line[i - 1][1])));
    const tot = seg.reduce((a, b) => a + b, 0);
    let acc = 0;
    const rel = seg.map((s) => (acc += s) / tot);
    return { projection: proj, landPath: path(landGeo) ?? "", routePath: d, pts: def.route.map((c, i) => ({ ...c, xy: line[i], rel: rel[i] })) };
  }, [name, width, height]);

  const drawEnd = Math.min(dur * 0.75, Math.max(6, dur - 3));
  const progress = interpolate(frame, [fps * 1.2, fps * drawEnd], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) });
  const zoom = interpolate(frame, [0, dur * fps], [1.0, 1.06], { extrapolateRight: "clamp" });
  const titleOp = interpolate(frame, [0, fps * 0.8], [0, 1], { extrapolateRight: "clamp" });
  const tip = pts.length ? (() => {
    // ponta da linha: interpola entre pontos pela posição relativa
    for (let i = 1; i < pts.length; i++) if (progress <= pts[i].rel) {
      const a = pts[i - 1], b = pts[i], u = (progress - a.rel) / Math.max(1e-6, b.rel - a.rel);
      return [a.xy[0] + (b.xy[0] - a.xy[0]) * u, a.xy[1] + (b.xy[1] - a.xy[1]) * u];
    }
    return pts[pts.length - 1].xy;
  })() : [0, 0];

  const labelPos = (c: City, xy: [number, number]) => {
    const o = 18;
    switch (c.label) {
      case "l": return { x: xy[0] - o, y: xy[1] + 8, anchor: "end" as const };
      case "t": return { x: xy[0], y: xy[1] - o, anchor: "middle" as const };
      case "b": return { x: xy[0], y: xy[1] + o + 22, anchor: "middle" as const };
      default: return { x: xy[0] + o, y: xy[1] + 8, anchor: "start" as const };
    }
  };

  return (
    <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 45%, #1d3141 0%, #0c1720 70%, #070d12 100%)" }}>
      <svg width={width} height={height} style={{ transform: `scale(${zoom})`, transformOrigin: "50% 50%" }}>
        <defs>
          <linearGradient id="landg" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#cdb98c" />
            <stop offset="1" stopColor="#a8926a" />
          </linearGradient>
          <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="6" result="b" />
            <feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>
        <path d={landPath} fill="url(#landg)" stroke="#6f5d3f" strokeWidth={1.2} opacity={0.92} />
        {(def.seas ?? []).map((s) => {
          const p = projection([s.lon, s.lat]) as [number, number];
          return <text key={s.name} x={p[0]} y={p[1]} fill="#7fa3b8" fontFamily={SERIF} fontSize={30} letterSpacing={6} textAnchor="middle" opacity={0.75} fontStyle="italic">{s.name.toUpperCase()}</text>;
        })}
        {(def.extra ?? []).map((c) => {
          const xy = projection([c.lon, c.lat]) as [number, number];
          const lp = labelPos(c, xy);
          return (
            <g key={c.name} opacity={0.75}>
              <circle cx={xy[0]} cy={xy[1]} r={6} fill="#3b2f20" />
              <text x={lp.x} y={lp.y} fill="#2b2216" fontFamily={SERIF} fontSize={26} textAnchor={lp.anchor}>{c.name}</text>
            </g>
          );
        })}
        <path d={routePath} fill="none" stroke="#000" strokeOpacity={0.35} strokeWidth={9} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - progress} />
        <path d={routePath} fill="none" stroke={GOLD} strokeWidth={5.5} strokeLinecap="round" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - progress} filter="url(#glow)" />
        {pts.filter((c) => c.name).map((c) => {
          const on = progress >= c.rel - 0.001;
          const op = on ? 1 : 0.0;
          const lp = labelPos(c, c.xy);
          return (
            <g key={c.name} opacity={op}>
              <circle cx={c.xy[0]} cy={c.xy[1]} r={c.key ? 11 : 8} fill={GOLD} stroke="#2b1d08" strokeWidth={3} />
              <text x={lp.x} y={lp.y} fill="#1b140b" stroke="#e9dcc0" strokeWidth={6} paintOrder="stroke" fontFamily={SERIF} fontWeight={700} fontSize={c.key ? 36 : 28} textAnchor={lp.anchor}>{c.name}</text>
            </g>
          );
        })}
        {progress > 0 && progress < 1 ? <circle cx={tip[0]} cy={tip[1]} r={10} fill="#fff6d8" filter="url(#glow)" /> : null}
      </svg>
      <div style={{ position: "absolute", top: 56, left: 80, opacity: titleOp }}>
        <div style={{ fontFamily: SERIF, fontSize: 52, color: GOLD, letterSpacing: 3, textShadow: "0 2px 16px rgba(0,0,0,0.9)" }}>{def.title}</div>
        {def.note ? <div style={{ fontFamily: SANS, fontSize: 26, color: "#d9cfbd", marginTop: 6, textShadow: "0 2px 10px rgba(0,0,0,0.9)" }}>{def.note}</div> : null}
      </div>
    </AbsoluteFill>
  );
};
