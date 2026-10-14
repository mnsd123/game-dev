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
};

export type GraphicItem = {
  kind: "light" | "whiten" | "teeth" | "counter" | "callout" | "collage";
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
  stills?: { file: string; label: string }[]; // collage: ảnh trong public/
};

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
};

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
