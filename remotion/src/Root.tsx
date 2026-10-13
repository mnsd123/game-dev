import { CalculateMetadataFunction, Composition } from "remotion";
import { Overlay } from "./Overlay";
import { OverlayProps } from "./types";

const calculateMetadata: CalculateMetadataFunction<OverlayProps> = async ({ props }) => ({
  durationInFrames: Math.max(1, props.durationInFrames),
  // nền trong suốt để ffmpeg chồng lên video quay
  defaultCodec: "prores",
  defaultProResProfile: "4444",
  defaultPixelFormat: "yuva444p10le",
  defaultVideoImageFormat: "png",
});

const sample: OverlayProps = {
  durationInFrames: 150,
  overlays: [
    { text: "Cười mà phải che miệng?", start: 0, end: 1.6, position: "top", style: "hook", animation: "word_by_word", emphasis: [] },
    { text: "Trắng sau 5–7 ngày", start: 1.8, end: 3.4, position: "center", style: "commit", animation: "highlight", emphasis: ["5–7 ngày"] },
    { text: "15 phút tại nhà", start: 3.0, end: 4.2, position: "top", style: "label", animation: "slide", emphasis: [] },
    { text: "Bấm giỏ hàng", start: 4.0, end: 5.0, position: "bottom", style: "cta", animation: "pop", emphasis: [] },
  ],
};

export const Root: React.FC = () => (
  <Composition
    id="Overlay"
    component={Overlay}
    width={1080}
    height={1920}
    fps={30}
    durationInFrames={sample.durationInFrames}
    defaultProps={sample}
    calculateMetadata={calculateMetadata}
  />
);
