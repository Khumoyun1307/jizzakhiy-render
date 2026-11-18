import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { BRAND, FONTS, LAYOUT } from "./brand";
import { Rich } from "./Rich";
import { useMeta, useTheme } from "./ThemeContext";

/** Opacity + small rise for an element that appears at `at` seconds. */
export const useAppear = (at: number | undefined, dur = 0.45, rise = 18): React.CSSProperties => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (at === undefined || at === null) return {};
  const t = frame / fps;
  const p = interpolate(t, [at, at + dur], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  return { opacity: p, transform: `translateY(${(1 - p) * rise}px)` };
};

export const pad2 = (n: number) => String(n).padStart(2, "0");

export const defaultKicker = (lesson: number, theme: string) =>
  theme === "gold" ? `${BRAND.course} · Lesson ${lesson}` : `Lesson ${lesson}`;

export const Kicker: React.FC<{ text: string; style?: React.CSSProperties; color?: string }> = ({
  text,
  style,
  color,
}) => {
  const theme = useTheme();
  return (
    <div
      style={{
        fontFamily: FONTS.sans,
        fontSize: LAYOUT.kickerSize,
        fontWeight: 600,
        letterSpacing: "0.2em",
        textTransform: "uppercase",
        color: color ?? theme.kickerColor,
        whiteSpace: "pre",
        ...style,
      }}
    >
      {text.replace(/\s·\s/g, "  ·  ")}
    </div>
  );
};

/** Slide title with the theme's rule treatment (full-width hairline for teal, short gold underline for gold). */
export const Title: React.FC<{ text: string; size?: number; rule?: "full" | "short" | "none" }> = ({
  text,
  size,
  rule,
}) => {
  const theme = useTheme();
  const gold = theme.name === "gold";
  const fs = size ?? (gold ? 74 : LAYOUT.titleSize);
  const r = rule ?? (gold ? "short" : "full");
  return (
    <div>
      <div
        style={{
          fontFamily: theme.titleFont,
          fontWeight: theme.titleWeight,
          fontSize: fs,
          lineHeight: 1.12,
          letterSpacing: gold ? "0" : "-0.02em",
          color: theme.ink,
          marginTop: gold ? 6 : 4,
        }}
      >
        <Rich text={text} mathScale={gold ? 1 : 0.98} />
      </div>
      {r === "full" && <div style={{ height: 2, background: theme.rule, marginTop: 24 }} />}
      {r === "short" && <div style={{ width: 96, height: 6, background: theme.accent, marginTop: 8 }} />}
    </div>
  );
};

export const Footer: React.FC<{ variant?: "slide" | "title" }> = ({ variant = "slide" }) => {
  const theme = useTheme();
  const meta = useMeta();
  const gold = theme.name === "gold";
  const base: React.CSSProperties = { fontFamily: FONTS.sans, fontSize: LAYOUT.footerSize, color: theme.muted };
  return (
    <div style={{ position: "absolute", left: LAYOUT.marginX, right: LAYOUT.marginX, top: gold ? 998 : 1006 }}>
      {gold && <div style={{ height: 2, background: theme.rule, marginBottom: 20 }} />}
      {variant === "title" && !gold ? (
        <div style={base}>
          <span style={{ color: theme.ink, fontWeight: 600 }}>{BRAND.academy}</span>
          <span style={{ margin: "0 16px" }}>—</span>
          {meta.course}
        </div>
      ) : (
        <div style={{ ...base, display: "flex", justifyContent: "space-between" }}>
          <span style={{ color: theme.footerLeftColor, fontWeight: gold ? 600 : 400 }}>{BRAND.academy}</span>
          <span>
            {meta.course}
            <span style={{ margin: "0 12px" }}>·</span>
            {gold ? `Lesson ${meta.lesson}` : meta.lesson}
          </span>
        </div>
      )}
    </div>
  );
};

/** The standard content slide: background, kicker + title + rule at top, footer at bottom, body in between. */
export const SlideFrame: React.FC<{
  kicker?: string;
  title?: string;
  children?: React.ReactNode;
  footer?: boolean;
  bodyTop?: number;
}> = ({ kicker, title, children, footer = true, bodyTop }) => {
  const theme = useTheme();
  const meta = useMeta();
  const k = kicker ?? defaultKicker(meta.lesson, theme.name);
  return (
    <AbsoluteFill style={{ background: theme.bg, fontFamily: FONTS.sans, color: theme.body }}>
      <div style={{ position: "absolute", left: LAYOUT.marginX, right: LAYOUT.marginX, top: theme.name === "gold" ? 96 : 104 }}>
        {k && <Kicker text={k} />}
        {title !== undefined && <Title text={title} />}
      </div>
      <div
        style={{
          position: "absolute",
          left: LAYOUT.marginX,
          right: LAYOUT.marginX,
          top: bodyTop ?? (title ? 280 : 150),
          bottom: 110,
        }}
      >
        {children}
      </div>
      {footer && <Footer />}
    </AbsoluteFill>
  );
};

/** A bullet row; the marker matches the theme (teal dot or navy square). */
export const Bullet: React.FC<{ text: string; level?: number; style?: React.CSSProperties; size?: number }> = ({
  text,
  level = 0,
  style,
  size = LAYOUT.bodySize,
}) => {
  const theme = useTheme();
  const sub = level > 0;
  const fs = sub ? size * 0.85 : size;
  const marker = sub ? (
    <span style={{ color: theme.muted, fontSize: fs * 0.8 }}>–</span>
  ) : theme.bulletShape === "dot" ? (
    <span style={{ width: 11, height: 11, borderRadius: 6, background: theme.accent, display: "inline-block" }} />
  ) : (
    <span style={{ width: 12, height: 12, background: theme.ink, display: "inline-block" }} />
  );
  return (
    <div style={{ display: "flex", alignItems: "flex-start", marginLeft: sub ? 64 : 0, fontSize: fs, lineHeight: 1.35, ...style }}>
      <span style={{ width: sub ? 32 : 44, flex: "none", display: "inline-flex", alignItems: "center", height: fs * 1.35, transform: `translateY(${fs * 0.04}px)` }}>
        {marker}
      </span>
      <Rich text={text} />
    </div>
  );
};

/** Scene-level fade from/to the background colour (optional; the editor usually crossfades). */
export const SceneFade: React.FC<{ inSec?: number; outSec?: number; children: React.ReactNode }> = ({
  inSec = 0,
  outSec = 0,
  children,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const t = frame / fps;
  const total = durationInFrames / fps;
  let o = 1;
  if (inSec > 0) o = Math.min(o, interpolate(t, [0, inSec], [0, 1], { extrapolateRight: "clamp" }));
  if (outSec > 0) o = Math.min(o, interpolate(t, [total - outSec, total], [1, 0], { extrapolateLeft: "clamp" }));
  return <AbsoluteFill style={{ opacity: o }}>{children}</AbsoluteFill>;
};
