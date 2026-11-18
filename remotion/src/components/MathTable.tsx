import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { SlideFrame, useAppear } from "../brand/Frame";
import { Rich } from "../brand/Rich";
import { useTheme } from "../brand/ThemeContext";

export type MathTableProps = {
  kicker?: string;
  title: string;
  /** header cells (rich text, e.g. "$\\delta'$", "$0$") */
  columns: string[];
  /** body rows of rich-text cells; a bare TeX cell must still be wrapped in $...$ */
  rows: string[][];
  /** seconds at which each row appears (missing => visible from the start) */
  rowAt?: number[];
  /** highlight a row (or a single cell when col is given) in the accent colour from `at` until `until` */
  highlights?: { row: number; col?: number; at: number; until?: number }[];
  /** relative column widths, e.g. [2,1,1] */
  colWidths?: number[];
  /** font size of cells (default 38) */
  size?: number;
  caption?: string;
  /** first column rendered as row headers (bold ink) */
  rowHeaders?: boolean;
};

export const MathTable: React.FC<MathTableProps> = (p) => {
  const theme = useTheme();
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const n = p.columns.length;
  const w = p.colWidths ?? Array(n).fill(1);
  const grid = w.map((x) => `${x}fr`).join(" ");
  const fs = p.size ?? 38;
  const hl = (r: number, c: number | "row") => {
    let v = 0;
    for (const h of p.highlights ?? []) {
      if (h.row !== r) continue;
      if (c === "row" ? h.col !== undefined : h.col !== c) continue;
      const on = interpolate(t, [h.at, h.at + 0.3], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
      const off = h.until === undefined ? 1 : interpolate(t, [h.until, h.until + 0.3], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
      v = Math.max(v, Math.min(on, off));
    }
    return v;
  };
  return (
    <SlideFrame kicker={p.kicker} title={p.title}>
      <div style={{ background: theme.card, border: `2px solid ${theme.cardBorder}`, borderRadius: 6, overflow: "hidden" }}>
        <div style={{ display: "grid", gridTemplateColumns: grid, background: theme.name === "gold" ? "#EEF1F6" : "#F3F7F6", borderBottom: `2px solid ${theme.name === "gold" ? theme.ink : theme.accent}` }}>
          {p.columns.map((c, i) => (
            <div key={i} style={{ padding: "16px 28px", fontSize: fs, fontWeight: 600, color: theme.ink, textAlign: i === 0 && p.rowHeaders ? "left" : "center" }}>
              <Rich text={c} />
            </div>
          ))}
        </div>
        {p.rows.map((row, r) => (
          <Row key={r} at={p.rowAt?.[r]}>
            <div style={{ display: "grid", gridTemplateColumns: grid, borderTop: r ? `1px solid ${theme.rule}` : undefined, background: `rgba(${hexToRgb(theme.accent)},${0.16 * hl(r, "row")})`, boxShadow: hl(r, "row") > 0 ? `inset 0 0 0 ${3 * hl(r, "row")}px ${theme.accent}` : undefined }}>
              {row.map((cell, c) => {
                const h = hl(r, c);
                return (
                  <div
                    key={c}
                    style={{
                      padding: "12px 28px",
                      fontSize: fs,
                      color: c === 0 && p.rowHeaders ? theme.ink : theme.body,
                      fontWeight: c === 0 && p.rowHeaders ? 600 : 400,
                      textAlign: c === 0 && p.rowHeaders ? "left" : "center",
                      background: `rgba(${hexToRgb(theme.accent)},${0.16 * h})`,
                      boxShadow: h > 0 ? `inset 0 0 0 ${3 * h}px ${theme.accent}` : undefined,
                    }}
                  >
                    <Rich text={cell} />
                  </div>
                );
              })}
            </div>
          </Row>
        ))}
      </div>
      {p.caption && <div style={{ fontSize: 26, color: theme.muted, marginTop: 20, textAlign: "center" }}><Rich text={p.caption} /></div>}
    </SlideFrame>
  );
};

const Row: React.FC<{ at?: number; children: React.ReactNode }> = ({ at, children }) => {
  const a = useAppear(at, 0.4, 10);
  return <div style={a}>{children}</div>;
};

const hexToRgb = (h: string) => {
  const n = parseInt(h.slice(1), 16);
  return `${(n >> 16) & 255},${(n >> 8) & 255},${n & 255}`;
};
