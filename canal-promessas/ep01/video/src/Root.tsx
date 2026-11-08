import "@fontsource/cinzel/500.css";
import "@fontsource/cinzel/700.css";
import "@fontsource/cormorant-garamond/500.css";
import "@fontsource/cormorant-garamond/600-italic.css";
import "@fontsource/inter/400.css";
import "@fontsource/inter/600.css";
import React from "react";
import { Composition } from "remotion";
import { Episode, EpisodeProps } from "./Episode";
import timeline from "./timeline.json";

export const RemotionRoot: React.FC = () => {
  const defaults: EpisodeProps = { showCta: false };
  return (
    <>
      <Composition
        id="Episodio01"
        component={Episode}
        durationInFrames={Math.ceil(timeline.total * timeline.fps)}
        fps={timeline.fps}
        width={1920}
        height={1080}
        defaultProps={defaults}
      />
    </>
  );
};
