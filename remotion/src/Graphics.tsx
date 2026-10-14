import {
  AbsoluteFill,
  Easing,
  interpolate,
  interpolateColors,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { FONT_STACK, GraphicItem, PALETTE } from "./types";

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
      {/* thẻ đồng hồ — chỉ khi có nhãn (nguồn đã có chữ in sẵn thì bỏ, tránh vòng tròn trơ trọi đè lên mặt) */}
      {item.label && <div
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
      </div>}
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

const YELLOW = "#D8B24A";
const WHITE = "#FFFFFF";
// 6 răng hàm trên + 6 răng hàm dưới (x, rộng, cao) trong viewBox 560x300
const UPPER = [
  [118, 52, 66], [172, 56, 78], [230, 58, 88], [290, 58, 88], [350, 56, 78], [408, 52, 66],
];
const LOWER = [
  [140, 48, 52], [190, 50, 58], [242, 52, 62], [296, 52, 62], [348, 50, 58], [398, 48, 52],
];

/** Hàm răng vector: pha xanh — thanh LED quét, răng vàng → trắng lần lượt; pha đỏ — nướu dịu lại, răng lấp lánh.
 *  Ghi "Minh họa" (đồ hoạ, không phải kết quả thật). */
export const TeethFx: React.FC<{ item: GraphicItem }> = ({ item }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const fade = useFade();
  const enter = spring({ frame, fps, config: { damping: 13, stiffness: 170 } });
  const splitF = Math.round(durationInFrames * (item.split ?? 0.56));
  // split = 1: chỉ pha xanh; răng trắng xong ở 80 % thời lượng rồi lấp lánh
  const blueEnd = Math.max(FADE + 1, Math.min(splitF, Math.round(durationInFrames * 0.8)));
  const blue = interpolate(frame, [FADE, blueEnd], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  // không có pha đỏ (split ≈ 1) thì khoảng [splitF, cuối] rỗng → red = 0
  const red = splitF < durationInFrames - FADE - 1
    ? interpolate(frame, [splitF, durationInFrames - FADE], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })
    : 0;
  const inRed = frame >= splitF;
  const phase = inRed ? LIGHT.red : LIGHT.blue;
  const pulse = 0.7 + 0.3 * Math.sin((frame / fps) * Math.PI * 2.4);
  // thanh LED quét trái → phải trong pha xanh
  const sweepX = interpolate(blue, [0, 1], [70, 490]);

  const toothFill = (x: number, w: number) => {
    const center = x + w / 2;
    // răng trắng dần khi thanh sáng đã quét qua
    const p = interpolate(sweepX - center, [-20, 60], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
    return interpolateColors(Math.max(p, inRed ? 1 : 0), [0, 1], [YELLOW, WHITE]);
  };

  return (
    <AbsoluteFill style={{ opacity: fade, alignItems: "center" }}>
      <div
        style={{
          position: "absolute",
          top: `${(item.y ?? 0.08) * 100}%`,
          width: 540,
          height: 350,
          borderRadius: 40,
          background: PALETTE.plumCard,
          border: `4px solid rgba(${phase.glow}, ${0.6 + 0.4 * pulse})`,
          boxShadow: `0 0 ${50 * pulse}px rgba(${phase.glow}, 0.65), 0 20px 50px rgba(0,0,0,0.45)`,
          scale: interpolate(enter, [0, 1], [0.75, 1]),
          overflow: "hidden",
        }}
      >
        <svg width={540} height={350} viewBox="-30 -50 620 400">
          <defs>
            <linearGradient id="beam" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0" stopColor={phase.solid} stopOpacity="0" />
              <stop offset="0.5" stopColor={phase.solid} stopOpacity="0.85" />
              <stop offset="1" stopColor={phase.solid} stopOpacity="0" />
            </linearGradient>
            <radialGradient id="gumGlow">
              <stop offset="0" stopColor="#FF4D5E" stopOpacity={0.75 * red * pulse} />
              <stop offset="1" stopColor="#FF4D5E" stopOpacity="0" />
            </radialGradient>
            <clipPath id="mouth">
              <path d="M70,40 C170,-10 390,-10 490,40 C480,190 380,250 280,250 C180,250 80,190 70,40 Z" />
            </clipPath>
          </defs>
          {/* môi */}
          <path d="M40,40 C160,-40 400,-40 520,40 C510,230 390,290 280,290 C170,290 50,230 40,40 Z" fill="#E7708E" />
          {/* lòng miệng */}
          <path d="M70,40 C170,-10 390,-10 490,40 C480,190 380,250 280,250 C180,250 80,190 70,40 Z" fill="#4A1624" />
          <g clipPath="url(#mouth)">
            {/* nướu trên/dưới — đỏ ửng rồi dịu lại ở pha đỏ */}
            <path d="M60,0 L500,0 L500,34 C400,20 160,20 60,34 Z" fill={interpolateColors(red, [0, 1], ["#F39AAA", "#F7B6C2"])} />
            <path d="M60,250 L500,250 L500,200 C400,214 160,214 60,200 Z" fill={interpolateColors(red, [0, 1], ["#F39AAA", "#F7B6C2"])} />
            <ellipse cx={280} cy={30} rx={260} ry={60} fill="url(#gumGlow)" />
            <ellipse cx={280} cy={215} rx={240} ry={50} fill="url(#gumGlow)" />
            {UPPER.map(([x, w, h], i) => (
              <rect key={`u${i}`} x={x} y={22} width={w} height={h} rx={16} fill={toothFill(x, w)} stroke="#B98F7A" strokeWidth={2} />
            ))}
            {LOWER.map(([x, w, h], i) => (
              <rect key={`l${i}`} x={x} y={212 - h} width={w} height={h} rx={14} fill={toothFill(x, w)} stroke="#B98F7A" strokeWidth={2} />
            ))}
            {/* thanh LED quét (pha xanh), phủ cả hàm (pha đỏ) */}
            {!inRed ? (
              <rect x={sweepX - 70} y={0} width={140} height={260} fill="url(#beam)" style={{ mixBlendMode: "screen" }} />
            ) : null}
          </g>
          {/* răng lấp lánh khi đã trắng */}
          {frame >= blueEnd && (
            <>
              <Sparkle x={150} y={50} s={22} delay={blueEnd} />
              <Sparkle x={395} y={60} s={18} delay={blueEnd + 5} />
              <Sparkle x={280} y={180} s={14} delay={blueEnd + 10} />
            </>
          )}
        </svg>
        {/* chấm màu pha đèn + nhãn nhỏ bắt buộc */}
        <div
          style={{
            position: "absolute",
            left: 26,
            top: 22,
            width: 30,
            height: 30,
            borderRadius: "50%",
            background: phase.solid,
            boxShadow: `0 0 ${18 * pulse}px ${phase.solid}`,
          }}
        />
        <div
          style={{
            position: "absolute",
            right: 22,
            bottom: 14,
            fontFamily: FONT_STACK,
            fontWeight: 700,
            fontSize: 24,
            color: "rgba(255,255,255,0.7)",
          }}
        >
          Minh họa
        </div>
      </div>
    </AbsoluteFill>
  );
};


/** Thẻ toàn màn hình đếm ngày (style guide mục 5: bộ đếm kiểu B + thẻ chuyển ý kiểu A): "NGÀY 1 → 7". */
export const CounterFx: React.FC<{ item: GraphicItem }> = ({ item }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const fade = interpolate(frame, [0, 5, durationInFrames - 5, durationInFrames], [0, 1, 1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const p = interpolate(frame, [4, durationInFrames - 8], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.bezier(0.3, 0, 0.2, 1),
  });
  const day = Math.max(1, Math.min(7, 1 + Math.floor(p * 7)));
  const bump = spring({ frame: frame - Math.round((day - 1) / 7 * (durationInFrames - 12)) - 4, fps,
                        config: { damping: 9, stiffness: 260 } });
  return (
    <AbsoluteFill
      style={{
        opacity: fade,
        background: `radial-gradient(circle at 50% 45%, #5A1F49 0%, ${PALETTE.plum} 70%)`,
        alignItems: "center",
        justifyContent: "center",
        fontFamily: FONT_STACK,
        fontWeight: 900,
      }}
    >
      <div style={{ color: "#FFFFFF", fontSize: 56, letterSpacing: "0.12em" }}>NGÀY</div>
      <div style={{ color: PALETTE.pink, fontSize: 300, lineHeight: 1, scale: interpolate(bump, [0, 1], [1.25, 1]) }}>{day}</div>
      <div style={{ display: "flex", gap: 22, marginTop: 34 }}>
        {Array.from({ length: 7 }).map((_, i) => (
          <div key={i} style={{ width: 34, height: 34, borderRadius: "50%",
                                background: i < day ? PALETTE.pink : "rgba(255,255,255,0.18)",
                                boxShadow: i < day ? `0 0 16px ${PALETTE.pink}` : "none" }} />
        ))}
      </div>
      {item.label ? <div style={{ marginTop: 40, color: "#FFFFFF", fontSize: 44, fontWeight: 700 }}>{item.label}</div> : null}
    </AbsoluteFill>
  );
};
