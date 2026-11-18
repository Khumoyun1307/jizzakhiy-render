/**
 * Jizzakhiy Academy brand kit.
 *
 * Colours were sampled with ffmpeg + PIL from past finished lessons (2026-11-16):
 *   "teal" theme  <- Lesson_31_Subset_Construction_final.mp4 (0:02 title card, 2:00 slide)
 *                    (same look as Lessons 14-36)
 *   "gold" theme  <- Lesson_40_State_Elimination_Rule_final.mp4 / Lesson_41 (Lessons 37-41)
 *   navy / pill   <- Theory_of_Computation_Thumbnails/038_Converting_Regular_Expressions_to_NFAs.png
 */

export const VIDEO = { width: 1920, height: 1080, fps: 24 } as const;

export type ThemeName = "teal" | "gold";

export type Theme = {
  name: ThemeName;
  bg: string; // slide background
  card: string; // card / table / diagram panel background
  cardBorder: string;
  ink: string; // title ink
  body: string; // body text
  muted: string; // footer, captions, sources
  accent: string; // kicker, bullets, emphasis, rules
  accentSoft: string; // highlight fill (table cells, active rows)
  rule: string; // thin hairline rules
  bulletShape: "dot" | "square";
  titleFont: string; // CSS font-family for slide titles
  titleWeight: number;
  kickerColor: string;
  footerLeftColor: string;
};

export const FONTS = {
  // Inter is loaded via @remotion/google-fonts in fonts.ts
  sans: "Inter, 'Segoe UI', Arial, sans-serif",
  // KaTeX_Main is Computer Modern / Latin Modern style (ships with KaTeX)
  serif: "KaTeX_Main, 'Latin Modern Roman', 'CMU Serif', Georgia, serif",
};

export const THEMES: Record<ThemeName, Theme> = {
  teal: {
    name: "teal",
    bg: "#FFFFFF",
    card: "#FFFFFF",
    cardBorder: "#E4E5EA",
    ink: "#202124", // sampled title ink #202126
    body: "#404247", // sampled body text
    muted: "#6F727A", // sampled footer
    accent: "#13736C", // sampled kicker #1A7069 / bullet #117468 / rule #15736F
    accentSoft: "#E3F2F0",
    rule: "#E4E5EA", // sampled hairline under title
    bulletShape: "dot",
    titleFont: FONTS.sans,
    titleWeight: 700,
    kickerColor: "#13736C",
    footerLeftColor: "#6F727A",
  },
  gold: {
    name: "gold",
    bg: "#F6F7FA", // sampled
    card: "#FFFFFF",
    cardBorder: "#D6DBE1",
    ink: "#14203C", // sampled navy title #16203A, state strokes #15203C
    body: "#4C5465", // sampled
    muted: "#4E5464",
    accent: "#C9A227", // sampled gold underline #CAA21B / bar #C8A025
    accentSoft: "#E3ECFA", // light blue highlight used on states in L40
    rule: "#D6DBE1", // sampled footer rule
    bulletShape: "square",
    titleFont: FONTS.serif,
    titleWeight: 400,
    kickerColor: "#4D5463",
    footerLeftColor: "#14203C",
  },
};

/** Navy brand used on intro / outro / thumbnails. */
export const NAVY = {
  thumbNavy: "#0A1837", // thumbnail background
  seriesNavy: "#13203C", // L37-41 intro/outro background
  panel: "#1F2E55", // "UP NEXT" panel on L37-41 outros
  pillTeal: "#0ACDBA", // "Lesson NN" pill on thumbnails
  pillText: "#081B36",
  cream: "#FBF4E5", // heavy display type on thumbnails
  ice: "#BAD0E9", // thumbnail subtitle
  header: "#AAB7D1", // small caps header on navy intro
  gold: "#C9A227",
};

/** Layout constants measured from 1920x1080 frames. */
export const LAYOUT = {
  marginX: 160, // left/right content margin (L31); L40 uses 150
  kickerY: 104,
  titleSize: 64,
  titleCardSize: 96,
  kickerSize: 22,
  bodySize: 40,
  footerSize: 21,
  footerY: 1004, // top of footer text box
};

export const BRAND = {
  academy: "Jizzakhiy Academy",
  course: "Theory of Computation",
};
