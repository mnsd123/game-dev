// font brand (library/brand/*.ttf, hiện là Montserrat ExtraBold — đủ dấu tiếng Việt) nạp tên "BrandFont"
export const FONT_STACK = '"BrandFont", Montserrat, "Be Vietnam Pro", Arial, "DejaVu Sans", sans-serif';

export type OverlayItem = {
  text: string;
  start: number; // giây, theo timeline output
  end: number;
  position: "top" | "center" | "bottom";
  style: "hook" | "commit" | "label" | "cta" | "plain" | "lower" | "tag" | "vox";
  animation: "pop" | "word_by_word" | "highlight" | "slide" | "none";
  emphasis: string[];
  y?: number | null; // mép trên, 0–1 chiều cao khung (Python chọn chỗ không che mặt)
  sub?: string; // style lower: dòng phụ
  max_w?: number | null; // bề rộng hộp tối đa (px) theo vùng an toàn — Python điền
  xc?: number | null; // tâm ngang hộp (0–1) — Python điền (lệch trái ở hàng cột nút)
};

export type GraphicItem = {
  kind: "light" | "whiten" | "teeth" | "counter" | "callout" | "collage" | "shade" | "wipe"
    | "light_timer" | "kinetic" | "end_card" | "paper_swipe";
  start: number;
  end: number;
  color: "blue" | "red";
  label: string;
  y?: number | null;
  split?: number; // teeth: tỉ lệ pha đèn xanh
  cx?: number; // callout: tâm + bán kính vòng khoanh (tỉ lệ khung)
  cy?: number;
  rx?: number;
  ry?: number;
  stills?: { file: string; label: string }[]; // collage/wipe: ảnh trong public/
  from_shade?: number; // shade: mức thang màu lúc đầu → lúc sau
  to_shade?: number;
  xc?: number | null; // tâm ngang thẻ (0–1) theo vùng an toàn — Python điền
  rows?: { min: number; title: string; sub: string; color: "blue" | "red"; at: number }[]; // light_timer
  words?: string[]; // kinetic: từng cụm đập lên màn hình
  sub?: string; // end_card: dòng phụ
  live?: boolean; // end_card: huy hiệu LIVE
};

// vùng an toàn TikTok (px trên khung 1080x1920) — nguồn số liệu: vf/safezone.py
export type Safe = { top: number; bottom: number; side: number; rail_w: number; rail_top: number };
export const DEFAULT_SAFE: Safe = { top: 240, bottom: 660, side: 120, rail_w: 180, rail_top: 840 };
/** Bề rộng tối đa (px) của hộp căn giữa khung, nằm trọn trong vùng an toàn kể cả hàng cột nút. */
export const safeCenteredW = (s: Safe) => 2 * Math.min(540 - s.side, 1080 - s.rail_w - 540) - 24;

// bảng màu style guide (library/style-guide.md mục 8, đã duyệt 2026-10-14)
export const PALETTE = {
  plum: "#3A1230",
  plumCard: "rgba(58, 18, 48, 0.88)",
  pink: "#FF8DBA",
  keyBox: "#E0245E",
  // Vox: bút dạ vàng, mực đỏ khoanh, giấy
  marker: "#FFE14D",
  ink: "#FF3B30",
  paper: "#EFE6D6",
  accent2: "#40D6FF", // [từ] trong chữ — xanh (đèn xanh)
  cardText: "#FFFFFF", // chữ thường trên thẻ preset
};

export type Tokens = {
  colors: Record<string, number[]>;
  presets: Record<string, { box?: string; box_alpha?: number; text?: string; accent?: string; accent2?: string;
                             highlight?: string; radius?: number }>;
};

const rgba = (c: number[], a = 1) => `rgba(${c[0]}, ${c[1]}, ${c[2]}, ${a})`;

/** Đổi bảng màu theo preset của biến thể (library/brand/tokens.json). Gọi một lần trước khi vẽ;
 *  props giống nhau cho mọi khung hình nên sửa PALETTE tại chỗ là an toàn. */
export const applyPreset = (tokens?: Tokens, preset?: string | null) => {
  const p = tokens?.presets?.[preset ?? "pink"];
  if (!tokens || !p) return;
  const C = tokens.colors;
  if (p.box && p.box !== "none" && C[p.box]) {
    PALETTE.plum = rgba(C[p.box]);
    PALETTE.plumCard = rgba(C[p.box], (p.box_alpha ?? 235) / 255);
  }
  if (p.accent && C[p.accent]) PALETTE.pink = rgba(C[p.accent]);
  if (p.accent2 && C[p.accent2]) PALETTE.accent2 = rgba(C[p.accent2]);
  if (p.text && C[p.text]) PALETTE.cardText = rgba(C[p.text]);
  if (p.highlight && C[p.highlight]) PALETTE.marker = rgba(C[p.highlight]);
};

/** "a *b* [c]" → đoạn thường / accent (*…*) / accent2 ([…]). */
export const parseRich = (text: string): { t: string; tone: "plain" | "accent" | "accent2" }[] => {
  const out: { t: string; tone: "plain" | "accent" | "accent2" }[] = [];
  const re = /\*([^*]+)\*|\[([^\]]+)\]/g;
  let last = 0;
  let m: RegExpExecArray | null;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push({ t: text.slice(last, m.index), tone: "plain" });
    out.push(m[1] != null ? { t: m[1], tone: "accent" } : { t: m[2], tone: "accent2" });
    last = m.index + m[0].length;
  }
  if (last < text.length) out.push({ t: text.slice(last), tone: "plain" });
  return out;
};
export const hasRich = (text: string) => /\*[^*]+\*|\[[^\]]+\]/.test(text);
export const plainText = (text: string) => parseRich(text).map((p) => p.t).join("");

export type Colors = {
  text: string; // chữ chính
  stroke: string; // viền chữ
  marker: string; // vệt highlight
  card: string; // nền thẻ cam kết
  cardText: string;
  accent: string; // nhãn, CTA
  accentText: string;
};

export type OverlayProps = {
  durationInFrames: number;
  overlays: OverlayItem[];
  graphics?: GraphicItem[];
  fontFile?: string; // file trong public/ (Python chép từ library/brand/)
  colors?: Partial<Colors>;
  safe?: Safe;
  preset?: string | null;
  tokens?: Tokens;
};

export const DEFAULT_COLORS: Colors = {
  text: "#FFFFFF",
  stroke: "#111111",
  marker: "rgba(255, 222, 60, 0.9)",
  card: "#FFFFFF",
  cardText: "#111111",
  accent: "#E8487F", // hồng Smilee (hộp quà, máy)
  accentText: "#FFFFFF",
};
