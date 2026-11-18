import katex from "katex";
import React, { useMemo } from "react";
import { useTheme } from "./ThemeContext";

/** Render a TeX string with KaTeX (Computer Modern / Latin Modern look). */
export const Tex: React.FC<{ tex: string; display?: boolean; style?: React.CSSProperties }> = ({
  tex,
  display,
  style,
}) => {
  const html = useMemo(
    () =>
      katex.renderToString(tex, {
        displayMode: !!display,
        throwOnError: false,
        strict: "ignore",
        output: "html",
        macros: { "\\eps": "\\varepsilon" },
      }),
    [tex, display],
  );
  return <span style={{ ...style }} dangerouslySetInnerHTML={{ __html: html }} />;
};

/**
 * Rich text mini-markup used in every text prop:
 *   $...$     inline math (KaTeX)           e.g. "Start at $E(\{q_0\})$"
 *   $$...$$   display math on its own line
 *   **x**     accent emphasis (teal / gold, semibold) – like "NFA" on L31 slides
 *   __x__     ink bold (dark, semibold) – like "equivalent" on L40 slides
 *   \$        literal dollar sign
 */
export const Rich: React.FC<{ text: string; style?: React.CSSProperties; mathScale?: number }> = ({
  text,
  style,
  mathScale = 1.08,
}) => {
  const theme = useTheme();
  const nodes = useMemo(() => parse(text), [text]);
  return (
    <span style={style}>
      {nodes.map((n, i) => {
        if (n.kind === "math")
          return <Tex key={i} tex={n.v} style={{ fontSize: `${mathScale}em` }} />;
        if (n.kind === "dmath")
          return (
            <span key={i} style={{ display: "block", margin: "0.25em 0", fontSize: `${mathScale}em` }}>
              <Tex tex={n.v} display />
            </span>
          );
        if (n.kind === "accent")
          return (
            <span key={i} style={{ color: theme.accent, fontWeight: 600 }}>
              <Rich text={n.v} mathScale={mathScale} />
            </span>
          );
        if (n.kind === "bold")
          return (
            <span key={i} style={{ color: theme.ink, fontWeight: 600 }}>
              <Rich text={n.v} mathScale={mathScale} />
            </span>
          );
        return <React.Fragment key={i}>{n.v}</React.Fragment>;
      })}
    </span>
  );
};

type Node = { kind: "text" | "math" | "dmath" | "accent" | "bold"; v: string };

function parse(s: string): Node[] {
  const out: Node[] = [];
  let buf = "";
  let i = 0;
  const flush = () => {
    if (buf) out.push({ kind: "text", v: buf });
    buf = "";
  };
  while (i < s.length) {
    if (s[i] === "\\" && s[i + 1] === "$") {
      buf += "$";
      i += 2;
      continue;
    }
    if (s.startsWith("$$", i)) {
      const j = s.indexOf("$$", i + 2);
      if (j > 0) {
        flush();
        out.push({ kind: "dmath", v: s.slice(i + 2, j) });
        i = j + 2;
        continue;
      }
    }
    if (s[i] === "$") {
      let j = i + 1;
      while (j < s.length && !(s[j] === "$" && s[j - 1] !== "\\")) j++;
      if (j < s.length) {
        flush();
        out.push({ kind: "math", v: s.slice(i + 1, j) });
        i = j + 1;
        continue;
      }
    }
    let matched = false;
    for (const [tok, kind] of [
      ["**", "accent"],
      ["__", "bold"],
    ] as const) {
      if (s.startsWith(tok, i)) {
        const j = s.indexOf(tok, i + 2);
        if (j > 0) {
          flush();
          out.push({ kind, v: s.slice(i + 2, j) });
          i = j + 2;
          matched = true;
          break;
        }
      }
    }
    if (matched) continue;
    buf += s[i];
    i++;
  }
  flush();
  return out;
}
