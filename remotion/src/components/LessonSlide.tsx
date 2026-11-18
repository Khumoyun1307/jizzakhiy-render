import React from "react";
import { AbsoluteFill } from "remotion";
import { FONTS, LAYOUT } from "../brand/brand";
import { Bullet, Footer, Kicker, SlideFrame, Title, useAppear } from "../brand/Frame";
import { Rich } from "../brand/Rich";
import { useMeta, useTheme } from "../brand/ThemeContext";

export type LessonSlideProps = {
  /** "title": opening title card; "statement": one big sentence (overview / key idea / question); "content": title + static bullets / math */
  layout?: "title" | "statement" | "content";
  kicker?: string;
  title?: string;
  /** statement layout: the sentence (rich text) */
  text?: string;
  /** content layout: static bullets (rich text); prefix with "- " for a sub-bullet */
  bullets?: string[];
  /** content layout: a display-math block under the bullets (TeX, no $ delimiters) */
  math?: string;
  /** small source line, e.g. "Sipser, Theorem 1.39" */
  source?: string;
  /** seconds at which the text/bullets/math appear (optional) */
  textAt?: number;
};

export const LessonSlide: React.FC<LessonSlideProps> = (p) => {
  const layout = p.layout ?? "content";
  if (layout === "title") return <TitleCard {...p} />;
  if (layout === "statement") return <Statement {...p} />;
  return (
    <SlideFrame kicker={p.kicker} title={p.title ?? ""}>
      <ContentBody {...p} />
    </SlideFrame>
  );
};

const ContentBody: React.FC<LessonSlideProps> = (p) => {
  const theme = useTheme();
  const a = useAppear(p.textAt);
  return (
    <div style={{ ...a, display: "flex", flexDirection: "column", gap: 22 }}>
      {(p.bullets ?? []).map((b, i) => {
        const sub = b.startsWith("- ");
        return <Bullet key={i} text={sub ? b.slice(2) : b} level={sub ? 1 : 0} />;
      })}
      {p.math && (
        <div style={{ fontSize: 46, color: theme.ink, marginTop: 10 }}>
          <Rich text={`$$${p.math}$$`} mathScale={1} />
        </div>
      )}
      {p.source && <div style={{ fontSize: 22, color: theme.muted, marginTop: 18 }}>{p.source}</div>}
    </div>
  );
};

/** Matches the L31 opening card (teal) / L40 opening card (gold, centred serif). */
const TitleCard: React.FC<LessonSlideProps> = (p) => {
  const theme = useTheme();
  const meta = useMeta();
  const a = useAppear(p.textAt ?? 0.1, 0.6, 24);
  if (theme.name === "gold") return <Statement {...p} text={p.text ?? p.title} kicker={p.kicker ?? `Lesson ${meta.lesson}`} />;
  return (
    <AbsoluteFill style={{ background: theme.bg, fontFamily: FONTS.sans }}>
      <div style={{ position: "absolute", left: LAYOUT.marginX, right: 300, top: 0, bottom: 0, display: "flex", flexDirection: "column", justifyContent: "center", ...a }}>
        <Kicker text={p.kicker ?? `Lesson ${meta.lesson}`} style={{ fontSize: 26, letterSpacing: "0.22em" }} />
        <div style={{ fontWeight: 700, fontSize: 96, lineHeight: 1.08, letterSpacing: "-0.025em", color: theme.ink, marginTop: 18 }}>
          <Rich text={p.title ?? ""} />
        </div>
        <div style={{ width: 120, height: 3, background: theme.accent, marginTop: 52 }} />
      </div>
      <Footer variant="title" />
    </AbsoluteFill>
  );
};

/** One key sentence: L31 "overview" style (teal, top-left) or L40 centred serif style (gold). */
const Statement: React.FC<LessonSlideProps> = (p) => {
  const theme = useTheme();
  const meta = useMeta();
  const a = useAppear(p.textAt ?? 0.1, 0.6, 20);
  const text = p.text ?? p.title ?? "";
  if (theme.name === "gold") {
    return (
      <AbsoluteFill style={{ background: theme.bg, fontFamily: FONTS.sans }}>
        <div style={{ position: "absolute", left: 240, right: 240, top: 0, bottom: 120, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", textAlign: "center", ...a }}>
          {p.kicker !== "" && (
            <>
              <Kicker text={p.kicker ?? `Lesson ${meta.lesson}`} color={theme.accent} />
              <div style={{ width: 60, height: 3, background: theme.accent, marginTop: 12 }} />
            </>
          )}
          <div style={{ fontFamily: FONTS.serif, fontSize: 64, lineHeight: 1.3, color: theme.ink, marginTop: 64 }}>
            <Rich text={text} mathScale={1} />
          </div>
          {p.source && <div style={{ fontSize: 22, color: theme.muted, marginTop: 30 }}>{p.source}</div>}
        </div>
        <Footer />
      </AbsoluteFill>
    );
  }
  return (
    <AbsoluteFill style={{ background: theme.bg, fontFamily: FONTS.sans }}>
      <div style={{ position: "absolute", left: LAYOUT.marginX, right: 360, top: 0, bottom: 0, display: "flex", flexDirection: "column", justifyContent: "center", ...a }}>
        <Kicker text={p.kicker ?? `Lesson ${meta.lesson} · Overview`} />
        <div style={{ fontSize: 64, lineHeight: 1.22, letterSpacing: "-0.015em", fontWeight: 500, color: theme.ink, marginTop: 20 }}>
          <Rich text={text} />
        </div>
        <div style={{ width: 120, height: 3, background: theme.accent, marginTop: 40 }} />
        {p.source && <div style={{ fontSize: 24, color: theme.muted, marginTop: 26 }}>{p.source}</div>}
      </div>
      <Footer />
    </AbsoluteFill>
  );
};

export { Title };
