import {
  AbsoluteFill,
  Easing,
  Img,
  staticFile,
  interpolate,
  interpolateColors,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { FONT_STACK, GraphicItem, OverlayItem, PALETTE, Safe, safeCenteredW } from "./types";

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
              // hạt trang trí chạy dọc mép (ngoài vùng an toàn): giữ mờ < 85 % để không thành "vật thể đặc"
              background: `rgba(${c.glow}, 0.7)`,
              boxShadow: `0 0 ${size * 2}px ${size}px rgba(${c.glow}, 0.45)`,
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
export const CounterFx: React.FC<{ item: GraphicItem; safe: Safe }> = ({ item, safe }) => {
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
        // nội dung căn giữa vùng an toàn, không phải giữa khung (nền tím vẫn phủ kín)
        paddingTop: safe.top,
        paddingBottom: safe.bottom,
        boxSizing: "border-box",
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


// ───────────── Phong cách Vox: bút dạ vàng, khoanh tay, giấy dán ─────────────

/** Nhãn bút dạ: chữ đen đậm, vệt vàng quét từ trái sang, nghiêng nhẹ. */
const Highlight: React.FC<{ text: string; fontSize: number; delay?: number; rotate?: number; maxWidth?: number }> = ({
  text,
  fontSize,
  delay = 0,
  rotate = -2,
  maxWidth = 816,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const sweep = interpolate(frame - delay, [0, 0.3 * fps], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.6, 0, 0.3, 1),
  });
  const textIn = interpolate(frame - delay, [0.12 * fps, 0.28 * fps], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <span
      style={{
        display: "inline-block",
        rotate: `${rotate}deg`,
        padding: "6px 22px 10px",
        fontFamily: FONT_STACK,
        fontWeight: 900,
        fontSize,
        lineHeight: 1.1,
        color: `rgba(17,17,17,${textIn})`,
        textTransform: "uppercase",
        backgroundImage: `linear-gradient(100deg, ${PALETTE.marker} 0%, ${PALETTE.marker} 96%, transparent 100%)`,
        backgroundSize: `${sweep * 100}% 86%`,
        backgroundPosition: "0 60%",
        backgroundRepeat: "no-repeat",
        // xuống dòng trong bề rộng an toàn thay vì tràn ra mép (vệt bút dạ tô theo từng dòng)
        maxWidth,
        boxSizing: "border-box",
        textWrap: "balance",
        boxDecorationBreak: "clone",
        WebkitBoxDecorationBreak: "clone",
      }}
    >
      {text}
    </span>
  );
};

/** Chữ kiểu Vox: dòng chính trên vệt bút dạ vàng, dòng phụ trên dải giấy trắng. */
export const VoxLabel: React.FC<{ item: OverlayItem; safe: Safe }> = ({ item, safe }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const exit = interpolate(frame, [durationInFrames - 6, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const subIn = interpolate(frame, [10, 16], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ alignItems: "center", opacity: exit }}>
      <div style={{ position: "absolute", top: `${(item.y ?? 0.5) * 100}%`, textAlign: "center",
                    maxWidth: item.max_w ?? safeCenteredW(safe) }}>
        <Highlight text={item.text} fontSize={66} maxWidth={item.max_w ?? safeCenteredW(safe)} />
        {item.sub ? (
          <div style={{ marginTop: 10 }}>
            <span
              style={{
                display: "inline-block",
                rotate: "1deg",
                padding: "6px 16px",
                background: "#FFFFFF",
                fontFamily: FONT_STACK,
                fontWeight: 700,
                fontSize: 36,
                color: "#111111",
                opacity: subIn,
              }}
            >
              {item.sub}
            </span>
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};

/** Đường vòng khoanh vẽ tay: vượt quá một vòng một chút, bán kính rung nhẹ. */
const handEllipse = (cx: number, cy: number, rx: number, ry: number, wob: number) => {
  const pts: string[] = [];
  for (let i = 0; i <= 40; i++) {
    const a = (i / 40) * Math.PI * 2.12 - 0.4;
    const r = 1 + wob * Math.sin(i * 1.7);
    pts.push(`${(cx + rx * r * Math.cos(a)).toFixed(1)},${(cy + ry * r * Math.sin(a)).toFixed(1)}`);
  }
  return `M${pts.join(" L")}`;
};

/** Vox callout: khoanh đỏ vẽ tay quanh vùng (cx, cy, rx, ry) → mũi tên → nhãn bút dạ bên dưới. */
export const CalloutFx: React.FC<{ item: GraphicItem; safe: Safe }> = ({ item, safe }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const W = 1080;
  const H = 1920;
  const cx = (item.cx ?? 0.5) * W;
  const cy = (item.cy ?? 0.5) * H;
  const rx = (item.rx ?? 0.25) * W;
  const ry = (item.ry ?? 0.08) * H;
  const t0 = Math.round(0.22 * fps); // chờ zoom ống kính gần xong
  const draw = interpolate(frame, [t0, t0 + 0.3 * fps], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.quad),
  });
  const arrow = interpolate(frame, [t0 + 0.25 * fps, t0 + 0.42 * fps], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const exit = interpolate(frame, [durationInFrames - 5, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  // nhãn dưới vòng khoanh; không đủ chỗ trong vùng an toàn thì đặt lên trên vòng
  const LABEL_H = 100;
  const below = cy + ry + 0.1 * H;
  const above = cy - ry - 0.1 * H - LABEL_H;
  const labelBelow = below + LABEL_H <= H - safe.bottom || above < safe.top;
  const labelY = Math.max(safe.top, Math.min(labelBelow ? below : above, H - safe.bottom - LABEL_H));
  const L = 2600;
  const ax0 = Math.min(cx + 0.18 * W, W - safe.rail_w - 20);
  const ay0 = labelBelow ? labelY - 10 : labelY + LABEL_H + 10;
  const ax1 = cx + rx * 0.55;
  const ay1 = labelBelow ? cy + ry * 0.95 : cy - ry * 0.95;
  return (
    <AbsoluteFill style={{ opacity: exit }}>
      <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>
        {[0, 1].map((k) => (
          <path
            key={k}
            d={handEllipse(cx + k * 4, cy - k * 3, rx * (1 + k * 0.03), ry * (1 - k * 0.04), 0.035)}
            fill="none"
            stroke={PALETTE.ink}
            strokeWidth={k ? 6 : 11}
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeDasharray={L}
            strokeDashoffset={L * (1 - draw)}
            opacity={k ? 0.75 : 1}
            style={{ filter: "drop-shadow(0 2px 3px rgba(0,0,0,0.35))" }}
          />
        ))}
        {item.label ? (
          <>
            <path
              d={`M${ax0},${ay0} Q${ax0 + 40},${(ay0 + ay1) / 2} ${ax1},${ay1}`}
              fill="none"
              stroke={PALETTE.ink}
              strokeWidth={9}
              strokeLinecap="round"
              strokeDasharray={600}
              strokeDashoffset={600 * (1 - arrow)}
            />
            {arrow >= 1 && (
              <path
                d={labelBelow ? `M${ax1 - 30},${ay1 + 22} L${ax1},${ay1} L${ax1 + 26},${ay1 + 30}`
                  : `M${ax1 - 30},${ay1 - 22} L${ax1},${ay1} L${ax1 + 26},${ay1 - 30}`}
                fill="none"
                stroke={PALETTE.ink}
                strokeWidth={9}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            )}
          </>
        ) : null}
      </svg>
      {item.label ? (
        <div style={{ position: "absolute", top: labelY, left: 0, right: 0, textAlign: "center" }}>
          <Highlight text={item.label} fontSize={70} delay={t0 + Math.round(0.35 * fps)} maxWidth={safeCenteredW(safe)} />
        </div>
      ) : null}
    </AbsoluteFill>
  );
};

/** Vox collage: nền giấy có hạt, các ảnh (cắt từ nguồn) dán băng keo, nghiêng, nhãn bút dạ. */
export const CollageFx: React.FC<{ item: GraphicItem; safe: Safe }> = ({ item, safe }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const stills = item.stills ?? [];
  const fade = interpolate(frame, [0, 4, durationInFrames - 5, durationInFrames], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  // ảnh ≤ 600x400 (+ viền) đặt trong vùng an toàn: ảnh 2 lệch trái để né hàng cột nút, nhãn ảnh 2 vẫn trên mép dưới
  const IMG_W = 600;
  const IMG_H = 400;
  const layout = stills.length === 1
    ? [{ top: Math.round((safe.top + 1920 - safe.bottom) / 2 - 250), left: Math.round((1080 - IMG_W - 32) / 2), rot: -3 }]
    : [
        // chừa ~60 px cho nghiêng ±5°, băng keo và nhãn bút dạ thò ra ngoài ảnh
        { top: safe.top + 40, left: safe.side + 60, rot: -5 },
        { top: 1920 - safe.bottom - 560, left: 1080 - safe.rail_w - IMG_W - 32 - 50, rot: 4 },
      ];
  return (
    <AbsoluteFill style={{ opacity: fade, background: PALETTE.paper }}>
      <svg width={1080} height={1920} style={{ position: "absolute", inset: 0, opacity: 0.35, mixBlendMode: "multiply" }}>
        <filter id="grain">
          <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves={2} seed={3} />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="100%" height="100%" filter="url(#grain)" />
      </svg>
      {stills.slice(0, 2).map((st, i) => {
        const at = Math.round(i * 0.45 * fps);
        const p = spring({ frame: frame - at, fps, config: { damping: 14, stiffness: 150 } });
        const L = layout[i];
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              top: L.top,
              left: L.left,
              rotate: `${L.rot}deg`,
              translate: `0px ${interpolate(p, [0, 1], [120, 0])}px`,
              opacity: Math.min(1, p * 1.5),
            }}
          >
            <div style={{ background: "#FFFFFF", padding: 16, paddingBottom: 18, boxShadow: "0 18px 36px rgba(0,0,0,0.28)" }}>
              <Img src={staticFile(st.file)} style={{ maxWidth: IMG_W, maxHeight: IMG_H, display: "block" }} />
            </div>
            <div
              style={{
                position: "absolute",
                top: -26,
                left: "40%",
                width: 170,
                height: 52,
                rotate: `${-L.rot * 1.6}deg`,
                background: "rgba(240, 228, 196, 0.85)",
                boxShadow: "0 2px 4px rgba(0,0,0,0.12)",
              }}
            />
            {st.label ? (
              <div style={{ position: "absolute", bottom: -64, left: i ? "auto" : 10, right: i ? 10 : "auto" }}>
                <Highlight text={st.label} fontSize={68} delay={at + Math.round(0.25 * fps)} rotate={i ? 2 : -3} />
              </div>
            ) : null}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};


/** Thang màu răng: các ô màu từ trắng (1) tới vàng (n), con trỏ trượt from_shade → to_shade.
 *  Chỉ dùng số người nói nói ra; nhãn ghi nguồn ("theo trải nghiệm của …"). Thẻ nằm gọn trong vùng an toàn. */
export const ShadeFx: React.FC<{ item: GraphicItem }> = ({ item }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const fade = useFade();
  const enter = spring({ frame, fps, config: { damping: 14, stiffness: 170 } });
  const from = item.from_shade ?? 10;
  const to = item.to_shade ?? 5;
  const n = Math.max(10, from, to);
  const move = interpolate(frame, [0.35 * fps, Math.max(0.35 * fps + 1, durationInFrames * 0.7)], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.bezier(0.45, 0, 0.2, 1),
  });
  const W = 680;
  const cell = (W - 60) / n;
  const pos = from + (to - from) * move; // mức hiện tại (số thực)
  const px = 30 + (pos - 0.5) * cell;
  const shown = Math.round(pos);
  const swatch = (i: number) => interpolateColors(i, [1, n], ["#FFFFFF", "#D9AE52"]);
  return (
    <AbsoluteFill style={{ opacity: fade, alignItems: "center" }}>
      <div
        style={{
          position: "absolute",
          top: `${(item.y ?? 0.15) * 100}%`,
          width: W,
          height: 300,
          boxSizing: "border-box",
          borderRadius: 32,
          background: PALETTE.plumCard,
          boxShadow: "0 20px 50px rgba(0,0,0,0.4)",
          scale: interpolate(enter, [0, 1], [0.8, 1]),
          fontFamily: FONT_STACK,
          fontWeight: 900,
          color: "#FFFFFF",
        }}
      >
        <div style={{ position: "absolute", top: 22, left: 30, fontSize: 34, letterSpacing: "0.06em" }}>THANG MÀU RĂNG</div>
        <div style={{ position: "absolute", top: 14, right: 30, fontSize: 64, color: PALETTE.pink }}>{shown}</div>
        <div style={{ position: "absolute", top: 120, left: 30, display: "flex" }}>
          {Array.from({ length: n }).map((_, i) => (
            <div key={i} style={{ width: cell - 4, marginRight: 4, height: 70, borderRadius: 10, background: swatch(i + 1),
                                  border: "2px solid rgba(0,0,0,0.15)", boxSizing: "border-box", display: "flex",
                                  alignItems: "flex-end", justifyContent: "center", fontSize: 20, color: "#5B4630" }}>
              {i + 1}
            </div>
          ))}
        </div>
        {/* con trỏ */}
        <div style={{ position: "absolute", top: 86, left: px - 18, width: 0, height: 0,
                      borderLeft: "18px solid transparent", borderRight: "18px solid transparent",
                      borderTop: `26px solid ${PALETTE.pink}` }} />
        {item.label ? (
          <div style={{ position: "absolute", bottom: 22, left: 30, right: 30, fontSize: 28, fontWeight: 700,
                        color: "rgba(255,255,255,0.85)" }}>{item.label}</div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};

/** Thanh gạt trước/sau: 2 ảnh cắt từ nguồn chồng nhau trong khung an toàn, vạch dọc quét trái → phải lộ ảnh "sau". */
export const WipeFx: React.FC<{ item: GraphicItem; safe: Safe }> = ({ item, safe }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const stills = item.stills ?? [];
  const fade = interpolate(frame, [0, 4, durationInFrames - 5, durationInFrames], [0, 1, 1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const sweep = interpolate(frame, [0.4 * fps, Math.max(0.4 * fps + 1, durationInFrames * 0.65)], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.bezier(0.65, 0, 0.35, 1),
  });
  const BW = safeCenteredW(safe);
  const top = safe.top + 40;
  const BH = 1920 - safe.bottom - top - 40;
  const before = stills[0];
  const after = stills[1] ?? stills[0];
  const img: React.CSSProperties = { position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" };
  const tag = (text: string, side: "left" | "right", bg: string) => (
    <div style={{ position: "absolute", top: 24, [side]: 24, padding: "8px 26px", borderRadius: 999, background: bg,
                  color: "#FFFFFF", fontFamily: FONT_STACK, fontWeight: 900, fontSize: 44 }}>{text}</div>
  );
  return (
    <AbsoluteFill style={{ opacity: fade, background: `radial-gradient(circle at 50% 45%, #5A1F49 0%, ${PALETTE.plum} 75%)`,
                           alignItems: "center" }}>
      <div style={{ position: "absolute", top, width: BW, height: BH, borderRadius: 28, overflow: "hidden",
                    boxShadow: "0 24px 60px rgba(0,0,0,0.45)", background: "#000" }}>
        {before ? <Img src={staticFile(before.file)} style={img} /> : null}
        {after ? (
          <div style={{ position: "absolute", inset: 0, clipPath: `inset(0 ${(1 - sweep) * 100}% 0 0)` }}>
            <Img src={staticFile(after.file)} style={img} />
          </div>
        ) : null}
        <div style={{ position: "absolute", top: 0, bottom: 0, left: `calc(${sweep * 100}% - 4px)`, width: 8,
                      background: "#FFFFFF", boxShadow: "0 0 18px rgba(0,0,0,0.5)" }} />
        {tag((before?.label || "Trước").toUpperCase(), "left", "rgba(0,0,0,0.55)")}
        {sweep > 0.55 ? tag((after?.label || "Sau").toUpperCase(), "right", PALETTE.keyBox) : null}
      </div>
    </AbsoluteFill>
  );
};
