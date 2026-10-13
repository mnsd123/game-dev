export type OverlayItem = {
  text: string;
  start: number; // giây, theo timeline output
  end: number;
  position: "top" | "center" | "bottom";
  style: "hook" | "commit" | "label" | "cta" | "plain";
  animation: "pop" | "word_by_word" | "highlight" | "slide" | "none";
  emphasis: string[];
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
  fontFile?: string; // file trong public/ (Python chép từ library/brand/)
  colors?: Partial<Colors>;
};

export const DEFAULT_COLORS: Colors = {
  text: "#FFFFFF",
  stroke: "#111111",
  marker: "rgba(255, 222, 60, 0.9)",
  card: "#FFFFFF",
  cardText: "#111111",
  accent: "#1F6FFF",
  accentText: "#FFFFFF",
};
