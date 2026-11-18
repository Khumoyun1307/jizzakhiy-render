import { loadFont } from "@remotion/google-fonts/Inter";
import { continueRender, delayRender } from "remotion";
import "katex/dist/katex.min.css";

// Inter (regular, medium, semibold, bold) – the slide sans used in every past lesson.
loadFont("normal", { weights: ["400", "500", "600", "700"], subsets: ["latin", "latin-ext", "greek"] });

let gated = false;
/** Block rendering until the KaTeX (Computer Modern) faces are loaded, so math never flashes. */
export const ensureMathFonts = () => {
  if (gated || typeof document === "undefined") return;
  gated = true;
  const handle = delayRender("Loading KaTeX fonts");
  const faces = [
    "20px KaTeX_Main",
    "italic 20px KaTeX_Main",
    "bold 20px KaTeX_Main",
    "italic 20px KaTeX_Math",
    "20px KaTeX_AMS",
    "20px KaTeX_Size1",
    "20px KaTeX_Size2",
    "20px KaTeX_Caligraphic",
  ];
  Promise.all(faces.map((f) => document.fonts.load(f, "AqεΣ∅∪")))
    .then(() => document.fonts.ready)
    .then(() => continueRender(handle))
    .catch(() => continueRender(handle));
};

// Display math is left-aligned like the past slides (KaTeX centres it by default).
if (typeof document !== "undefined" && !document.getElementById("jz-katex")) {
  const s = document.createElement("style");
  s.id = "jz-katex";
  s.textContent = ".katex-display{margin:0.2em 0 !important}.katex-display>.katex{text-align:left !important}.jz-center .katex-display>.katex{text-align:center !important}";
  document.head.appendChild(s);
}