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
import { CalloutFx, CollageFx, CounterFx, LightFx, ShadeFx, TeethFx, VoxLabel, WhitenFx, WipeFx } from "./Graphics";
import {
  Colors, DEFAULT_COLORS, DEFAULT_SAFE, FONT_STACK, OverlayItem, OverlayProps, PALETTE, Safe, applyPreset, hasRich,
  parseRich, plainText, safeCenteredW,
} from "./types";
import { EndCardFx, KineticFx, LightTimerFx, PaperSwipeFx } from "./Graphics";

/** Chữ có nhấn: *từ* = accent, [từ] = accent2; phần thường dùng màu `plain`. */
const Rich: React.FC<{ text: string; plain: string }> = ({ text, plain }) => (
  <>
    {parseRich(text).map((p, i) => (
      <span key={i} style={{ color: p.tone === "accent" ? PALETTE.pink : p.tone === "accent2" ? PALETTE.accent2 : plain }}>
        {p.t}
      </span>
    ))}
  </>
);

/** Dời phần tử theo tâm ngang an toàn (xc): lệch trái ở hàng cột nút bên phải. */
const Shift: React.FC<{ xc?: number | null; children: React.ReactNode }> = ({ xc, children }) => (
  <AbsoluteFill style={{ translate: `${((xc ?? 0.5) - 0.5) * 1080}px 0px` }}>{children}</AbsoluteFill>
);

// khớp FONT_PX / PAD_PX trong vf/placement.py (Python ước lượng chiều cao để chọn chỗ đặt)
const FONT_PX: Record<OverlayItem["style"], number> = { hook: 80, commit: 72, label: 54, cta: 58, plain: 60, lower: 72, tag: 50, vox: 66 };
const PAD_PX: Record<OverlayItem["style"], number> = { hook: 18, commit: 22, label: 16, cta: 20, plain: 14, lower: 22, tag: 12, vox: 16 };
const SUB_PX = 38;

/** Thẻ hai dòng (style guide mục 4): nền tím mận, dòng chính hồng viết hoa, dòng phụ trắng chữ thường. */
const LowerCard: React.FC<{ item: OverlayItem; safe: Safe }> = ({ item, safe }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const enter = spring({ frame, fps, config: { damping: 16, stiffness: 190 } });
  const exit = interpolate(frame, [durationInFrames - EXIT_FRAMES, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const subIn = interpolate(frame, [5, 12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const isTag = item.style === "tag";
  return (
    <AbsoluteFill style={{ alignItems: "center" }}>
      <div
        style={{
          position: "absolute",
          top: item.y != null ? `${item.y * 100}%` : TOP[item.position],
          maxWidth: item.max_w ?? safeCenteredW(safe),
          boxSizing: "border-box",
          textAlign: "center",
          fontFamily: FONT_STACK,
          padding: `${PAD_PX[item.style]}px ${isTag ? 34 : 40}px`,
          borderRadius: isTag ? 999 : 26,
          background: isTag ? PALETTE.keyBox : PALETTE.plumCard,
          boxShadow: "0 14px 34px rgba(0,0,0,0.35)",
          opacity: Math.min(1, enter * 1.4) * exit,
          translate: `0px ${interpolate(enter, [0, 1], [36, 0])}px`,
          scale: isTag ? interpolate(enter, [0, 1], [0.6, 1]) : 1,
          rotate: isTag ? "-4deg" : "0deg",
        }}
      >
        <div style={{ fontWeight: 900, fontSize: FONT_PX[item.style], lineHeight: 1.12, color: isTag ? "#FFFFFF" : PALETTE.pink,
                      textTransform: "uppercase", letterSpacing: "0.01em" }}>
          {/* có *nhấn* / [nhấn] → phần thường màu chữ preset, phần nhấn accent; không có → cả dòng accent */}
          {!isTag && hasRich(item.text) ? <Rich text={item.text} plain={PALETTE.cardText} /> : plainText(item.text)}
        </div>
        {item.sub ? (
          <div style={{ marginTop: 6, fontWeight: 700, fontSize: SUB_PX, color: PALETTE.cardText, opacity: subIn }}>
            <Rich text={item.sub} plain={PALETTE.cardText} />
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};
const EXIT_FRAMES = 6;

// khi Python chưa đặt y: vị trí mặc định vẫn trong vùng an toàn (trên 12.5 %, dưới 65.6 %)
const TOP: Record<OverlayItem["position"], string> = { top: "14%", center: "42%", bottom: "54%" };

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

const Item: React.FC<{ item: OverlayItem; colors: Colors; safe: Safe }> = ({ item, colors, safe }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const enter = spring({ frame, fps, config: { damping: 14, stiffness: 180, mass: 0.6 } });
  const exit = interpolate(frame, [durationInFrames - EXIT_FRAMES, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const isCard = item.style === "commit" || item.style === "label" || item.style === "cta";
  // chữ hook/plain: viền đen + nền tối mờ để đọc được trên mọi nền
  const bg = item.style === "commit" ? colors.card : isCard ? colors.accent : "rgba(0, 0, 0, 0.5)";
  const fg = isCard ? (item.style === "commit" ? colors.cardText : colors.accentText) : colors.text;
  const fontSize = FONT_PX[item.style];

  const textStyle: React.CSSProperties = isCard
    ? { color: fg }
    : { color: fg, WebkitTextStroke: `9px ${colors.stroke}`, paintOrder: "stroke fill" };

  // vệt highlight quét qua chữ sau khi chữ đã hiện
  const markerProgress = interpolate(frame, [0.25 * fps, 0.7 * fps], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.65, 0, 0.35, 1),
  });

  const words = plainText(item.text).split(/\s+/);
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
      splitEmphasis(plainText(item.text), item.emphasis).map((p, i) =>
        p.em ? (
          <Marker key={i} progress={markerProgress} color={colors.marker}>
            {p.t}
          </Marker>
        ) : (
          <span key={i}>{p.t}</span>
        )
      )
    ) : (
      <Rich text={item.text} plain={fg} />
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
          top: item.y != null ? `${item.y * 100}%` : TOP[item.position],
          maxWidth: item.max_w ?? safeCenteredW(safe),
          boxSizing: "border-box",
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
          padding: `${PAD_PX[item.style]}px 36px`,
          borderRadius: 28,
          backgroundColor: bg,
          boxShadow: isCard ? "0 18px 40px rgba(0,0,0,0.35)" : "none",
          letterSpacing: "-0.01em",
          ...textStyle,
        }}
      >
        {content}
      </div>
    </AbsoluteFill>
  );
};

export const Overlay: React.FC<OverlayProps> = ({ overlays, graphics, fontFile, colors, safe, preset, tokens }) => {
  const sz: Safe = { ...DEFAULT_SAFE, ...(safe ?? {}) };
  applyPreset(tokens, preset);
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
      {(graphics ?? []).map((g, i) => {
        const from = Math.round(g.start * fps);
        const dur = Math.max(1, Math.round(g.end * fps) - from);
        return (
          <Sequence key={`g${i}`} from={from} durationInFrames={dur} name={`${g.kind} ${g.label}`}>
            <Shift xc={g.xc}>
            {g.kind === "light" ? <LightFx item={g} /> : g.kind === "teeth" ? <TeethFx item={g} />
              : g.kind === "counter" ? <CounterFx item={g} safe={sz} /> : g.kind === "callout" ? <CalloutFx item={g} safe={sz} />
              : g.kind === "collage" ? <CollageFx item={g} safe={sz} /> : g.kind === "shade" ? <ShadeFx item={g} />
              : g.kind === "wipe" ? <WipeFx item={g} safe={sz} /> : g.kind === "light_timer" ? <LightTimerFx item={g} />
              : g.kind === "kinetic" ? <KineticFx item={g} safe={sz} /> : g.kind === "end_card" ? <EndCardFx item={g} />
              : g.kind === "paper_swipe" ? <PaperSwipeFx />
              : <WhitenFx item={g} />}
            </Shift>
          </Sequence>
        );
      })}
      {overlays.map((o, i) => {
        const from = Math.round(o.start * fps);
        const dur = Math.max(1, Math.round(o.end * fps) - from);
        return (
          <Sequence key={i} from={from} durationInFrames={dur} name={o.text}>
            <Shift xc={o.xc}>
            {o.style === "lower" || o.style === "tag" ? <LowerCard item={o} safe={sz} /> : o.style === "vox" ? <VoxLabel item={o} safe={sz} />
              : <Item item={o} colors={c} safe={sz} />}
            </Shift>
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
