import {
  AbsoluteFill,
  Easing,
  interpolate,
  interpolateColors,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { FONT_STACK, GraphicItem } from "./types";

const LIGHT = {
  blue: { solid: "#2F7BFF", glow: "47, 123, 255" },
  red: { solid: "#FF3B4E", glow: "255, 59, 78" },
};
const FADE = 8;

const useFade = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  return interpolate(frame, [0, FADE, durationInFrames - FADE, durationInFrames], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
};

/** Đèn xanh/đỏ: viền sáng màu nhịp thở quanh khung + hạt sáng bay lên + thẻ đồng hồ đếm phút. */
export const LightFx: React.FC<{ item: GraphicItem }> = ({ item }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const fade = useFade();
  const c = LIGHT[item.color];
  const breathe = 0.75 + 0.25 * Math.sin((frame / fps) * Math.PI * 1.6);
  const enter = spring({ frame, fps, config: { damping: 14, stiffness: 160 } });
  const progress = interpolate(frame, [FADE, durationInFrames - FADE], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const R = 46;
  const C = 2 * Math.PI * R;

  return (
    <AbsoluteFill style={{ opacity: fade }}>
      {/* vầng sáng quanh mép khung, giữa khung để trống cho mặt/sản phẩm */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(ellipse 75% 60% at 50% 50%, transparent 55%, rgba(${c.glow}, ${0.42 * breathe}) 100%)`,
          boxShadow: `inset 0 0 160px 30px rgba(${c.glow}, ${0.55 * breathe})`,
        }}
      />
      {/* hạt sáng dọc hai mép */}
      {Array.from({ length: 10 }).map((_, i) => {
        const side = i % 2 === 0 ? 40 + (i * 7) % 60 : 1080 - 40 - (i * 11) % 60;
        const speed = 160 + (i * 37) % 120;
        const y = 1920 - (((frame + i * 23) * speed) / fps) % 2100;
        const size = 10 + (i * 5) % 14;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: side,
              top: y,
              width: size,
              height: size,
              borderRadius: "50%",
              background: `rgba(${c.glow}, 0.9)`,
              boxShadow: `0 0 ${size * 2}px ${size}px rgba(${c.glow}, 0.6)`,
            }}
          />
        );
      })}
      {/* thẻ đồng hồ */}
      <div
        style={{
          position: "absolute",
          top: `${(item.y ?? 0.1) * 100}%`,
          left: "50%",
          translate: `-50% ${interpolate(enter, [0, 1], [-40, 0])}px`,
          scale: interpolate(enter, [0, 1], [0.85, 1]),
          height: 150,
          display: "flex",
          alignItems: "center",
          gap: 26,
          padding: "0 40px 0 22px",
          borderRadius: 75,
          background: "rgba(10, 12, 20, 0.72)",
          border: `3px solid rgba(${c.glow}, 0.9)`,
          boxShadow: `0 0 40px rgba(${c.glow}, 0.55)`,
        }}
      >
        <svg width={112} height={112} viewBox="0 0 112 112">
          <circle cx={56} cy={56} r={R} fill="none" stroke="rgba(255,255,255,0.18)" strokeWidth={10} />
          <circle
            cx={56}
            cy={56}
            r={R}
            fill="none"
            stroke={c.solid}
            strokeWidth={10}
            strokeLinecap="round"
            strokeDasharray={C}
            strokeDashoffset={C * (1 - progress)}
            transform="rotate(-90 56 56)"
          />
          <circle cx={56} cy={56} r={18 + 4 * breathe} fill={c.solid} style={{ filter: `drop-shadow(0 0 12px ${c.solid})` }} />
        </svg>
        <div style={{ fontFamily: FONT_STACK, fontWeight: 900, fontSize: 54, color: "#FFFFFF", whiteSpace: "nowrap" }}>
          {item.label}
        </div>
      </div>
    </AbsoluteFill>
  );
};

const TOOTH =
  "M40,30 C40,8 80,4 100,20 C120,4 160,8 160,30 C170,80 150,110 145,150 C140,205 122,218 114,182 " +
  "C109,160 91,160 86,182 C78,218 60,205 55,150 C50,110 30,80 40,30 Z";

const Sparkle: React.FC<{ x: number; y: number; s: number; delay: number }> = ({ x, y, s, delay }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: frame - delay, fps, config: { damping: 10, stiffness: 200 } });
  const twinkle = 0.8 + 0.2 * Math.sin((frame - delay) / 3);
  return (
    <path
      d={`M${x},${y - s} L${x + s * 0.25},${y - s * 0.25} L${x + s},${y} L${x + s * 0.25},${y + s * 0.25} ` +
        `L${x},${y + s} L${x - s * 0.25},${y + s * 0.25} L${x - s},${y} L${x - s * 0.25},${y - s * 0.25} Z`}
      fill="#FFFFFF"
      stroke="#9AD7FF"
      strokeWidth={2}
      style={{ transformOrigin: `${x}px ${y}px`, scale: `${p * twinkle}` }}
    />
  );
};

/** Icon răng ngả vàng → trắng, nhãn "Trước"/"Sau", thanh màu răng. Ghi rõ "Hình minh họa" (không phải ảnh thật). */
export const WhitenFx: React.FC<{ item: GraphicItem }> = ({ item }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const fade = useFade();
  const enter = spring({ frame, fps, config: { damping: 13, stiffness: 170 } });
  const t = interpolate(frame, [durationInFrames * 0.2, durationInFrames * 0.65], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.45, 0, 0.25, 1),
  });
  const fill = interpolateColors(t, [0, 1], ["#E2BE5E", "#FFFFFF"]);
  const sparkleAt = Math.round(durationInFrames * 0.62);

  return (
    <AbsoluteFill style={{ opacity: fade, alignItems: "center" }}>
      <div
        style={{
          position: "absolute",
          top: `${(item.y ?? 0.1) * 100}%`,
          width: 520,
          height: 520,
          borderRadius: 40,
          background: "rgba(255, 255, 255, 0.9)",
          boxShadow: "0 24px 60px rgba(0,0,0,0.35)",
          scale: interpolate(enter, [0, 1], [0.7, 1]),
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          fontFamily: FONT_STACK,
          fontWeight: 900,
        }}
      >
        <div style={{ position: "relative", height: 84, width: "100%", marginTop: 22 }}>
          {(["Trước", "Sau"] as const).map((label, i) => (
            <div
              key={label}
              style={{
                position: "absolute",
                inset: 0,
                textAlign: "center",
                fontSize: 60,
                color: i === 0 ? "#8A6A1E" : "#1F6FFF",
                opacity: i === 0 ? 1 - t : t,
              }}
            >
              {label}
            </div>
          ))}
        </div>
        <svg width={300} height={300} viewBox="0 0 200 230">
          <path d={TOOTH} fill={fill} stroke="#3A3A3A" strokeWidth={5} strokeLinejoin="round" />
          <path d="M62,44 C70,30 88,30 94,40" fill="none" stroke="rgba(255,255,255,0.85)" strokeWidth={7} strokeLinecap="round" />
          {frame >= sparkleAt && (
            <>
              <Sparkle x={168} y={34} s={20} delay={sparkleAt} />
              <Sparkle x={30} y={70} s={14} delay={sparkleAt + 4} />
              <Sparkle x={160} y={120} s={11} delay={sparkleAt + 8} />
            </>
          )}
        </svg>
        <div
          style={{
            width: 400,
            height: 22,
            borderRadius: 11,
            marginTop: 8,
            background: "linear-gradient(90deg, #D9B04A, #F3E3B0, #FFFFFF)",
            border: "2px solid rgba(0,0,0,0.15)",
            position: "relative",
          }}
        >
          <div
            style={{
              position: "absolute",
              top: -9,
              left: `calc(${t * 100}% - 18px)`,
              width: 36,
              height: 36,
              borderRadius: "50%",
              background: "#1F6FFF",
              border: "5px solid #FFFFFF",
              boxShadow: "0 3px 8px rgba(0,0,0,0.35)",
            }}
          />
        </div>
        <div style={{ marginTop: 16, fontSize: 26, fontWeight: 600, color: "#666666" }}>Hình minh họa</div>
      </div>
    </AbsoluteFill>
  );
};
