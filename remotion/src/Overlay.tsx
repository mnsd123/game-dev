import { loadFont } from "@remotion/fonts";
import { useEffect, useState } from "react";
import {
  AbsoluteFill,
  Easing,
  Sequence,
  cancelRender,
  continueRender,
  delayRender,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { Colors, DEFAULT_COLORS, OverlayItem, OverlayProps } from "./types";

const FONT_STACK = '"BrandFont", "Be Vietnam Pro", Arial, "DejaVu Sans", sans-serif';
const EXIT_FRAMES = 6;

const TOP: Record<OverlayItem["position"], string> = { top: "12%", center: "42%", bottom: "70%" };

type Piece = { t: string; em: boolean };

/** Tách câu thành đoạn thường / đoạn được tô highlight. emphasis rỗng → tô cả câu. */
const splitEmphasis = (text: string, emphasis: string[]): Piece[] => {
  if (emphasis.length === 0) return [{ t: text, em: true }];
  const lower = text.toLowerCase();
  const marks = new Array(text.length).fill(false);
  for (const e of emphasis) {
    const idx = lower.indexOf(e.toLowerCase());
    if (idx >= 0) for (let i = idx; i < idx + e.length; i++) marks[i] = true;
  }
  const out: Piece[] = [];
  for (let i = 0; i < text.length; i++) {
    const last = out[out.length - 1];
    if (last && last.em === marks[i]) last.t += text[i];
    else out.push({ t: text[i], em: marks[i] });
  }
  return out;
};

const Marker: React.FC<{ progress: number; color: string; children: React.ReactNode }> = ({ progress, color, children }) => (
  <span
    style={{
      backgroundImage: `linear-gradient(transparent 52%, ${color} 52%, ${color} 92%, transparent 92%)`,
      backgroundSize: `${progress * 100}% 100%`,
      backgroundRepeat: "no-repeat",
      boxDecorationBreak: "clone",
      WebkitBoxDecorationBreak: "clone",
    }}
  >
    {children}
  </span>
);

const Item: React.FC<{ item: OverlayItem; colors: Colors }> = ({ item, colors }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const enter = spring({ frame, fps, config: { damping: 14, stiffness: 180, mass: 0.6 } });
  const exit = interpolate(frame, [durationInFrames - EXIT_FRAMES, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const isCard = item.style === "commit" || item.style === "label" || item.style === "cta";
  const bg = item.style === "commit" ? colors.card : colors.accent;
  const fg = isCard ? (item.style === "commit" ? colors.cardText : colors.accentText) : colors.text;
  const fontSize = item.style === "commit" ? 84 : item.style === "hook" ? 88 : item.style === "plain" ? 64 : 60;

  const textStyle: React.CSSProperties = isCard
    ? { color: fg }
    : { color: fg, WebkitTextStroke: `14px ${colors.stroke}`, paintOrder: "stroke fill" };

  // vệt highlight quét qua chữ sau khi chữ đã hiện
  const markerProgress = interpolate(frame, [0.25 * fps, 0.7 * fps], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.65, 0, 0.35, 1),
  });

  const words = item.text.split(/\s+/);
  const content =
    item.animation === "word_by_word" ? (
      words.map((w, i) => {
        const p = spring({ frame: frame - i * 4, fps, config: { damping: 16, stiffness: 220 } });
        return (
          <span
            key={i}
            style={{
              display: "inline-block",
              marginRight: "0.25em",
              opacity: p,
              translate: `0px ${interpolate(p, [0, 1], [30, 0])}px`,
            }}
          >
            {w}
          </span>
        );
      })
    ) : item.animation === "highlight" ? (
      splitEmphasis(item.text, item.emphasis).map((p, i) =>
        p.em ? (
          <Marker key={i} progress={markerProgress} color={colors.marker}>
            {p.t}
          </Marker>
        ) : (
          <span key={i}>{p.t}</span>
        )
      )
    ) : (
      item.text
    );

  const scale =
    item.animation === "pop" || item.animation === "highlight"
      ? interpolate(enter, [0, 1], [0.6, 1])
      : 1;
  const slideX = item.animation === "slide" ? interpolate(enter, [0, 1], [-700, 0]) : 0;
  // CTA đập nhẹ để kéo mắt
  const pulse = item.style === "cta" ? 1 + 0.04 * Math.sin((frame / fps) * Math.PI * 3) : 1;
  // thẻ cam kết lắc nhẹ khi xuất hiện
  const wiggle = item.style === "commit" ? interpolate(frame, [0, 6, 12, 18], [-4, 3, -1.5, 0], { extrapolateRight: "clamp" }) : 0;

  return (
    <AbsoluteFill style={{ alignItems: "center" }}>
      <div
        style={{
          position: "absolute",
          top: TOP[item.position],
          maxWidth: 1000,
          textAlign: "center",
          textWrap: "balance",
          fontFamily: FONT_STACK,
          fontWeight: 900,
          fontSize,
          lineHeight: 1.18,
          opacity: (item.animation === "none" || item.animation === "word_by_word" ? 1 : Math.min(1, enter * 1.5)) * exit,
          scale: scale * pulse,
          translate: `${slideX}px 0px`,
          rotate: `${wiggle}deg`,
          padding: isCard ? "22px 40px" : 0,
          borderRadius: isCard ? 28 : 0,
          backgroundColor: isCard ? bg : "transparent",
          boxShadow: isCard ? "0 18px 40px rgba(0,0,0,0.35)" : "none",
          ...textStyle,
        }}
      >
        {content}
      </div>
    </AbsoluteFill>
  );
};

export const Overlay: React.FC<OverlayProps> = ({ overlays, fontFile, colors }) => {
  const { fps } = useVideoConfig();
  const [handle] = useState(() => (fontFile ? delayRender("Tải font brand") : null));
  useEffect(() => {
    if (!fontFile || handle === null) return;
    loadFont({ family: "BrandFont", url: staticFile(fontFile), weight: "900" })
      .then(() => continueRender(handle))
      .catch((e) => cancelRender(e));
  }, [fontFile, handle]);

  const c: Colors = { ...DEFAULT_COLORS, ...(colors ?? {}) };
  return (
    <AbsoluteFill style={{ backgroundColor: "transparent" }}>
      {overlays.map((o, i) => {
        const from = Math.round(o.start * fps);
        const dur = Math.max(1, Math.round(o.end * fps) - from);
        return (
          <Sequence key={i} from={from} durationInFrames={dur} name={o.text}>
            <Item item={o} colors={c} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
