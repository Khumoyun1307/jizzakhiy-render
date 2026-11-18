import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { FONTS } from "../brand/brand";
import { Bullet, SlideFrame, useAppear } from "../brand/Frame";
import { Rich } from "../brand/Rich";
import { useMeta, useTheme } from "../brand/ThemeContext";

export type HomeworkCardProps = {
  kicker?: string;
  title?: string;
  /** problem statement lines (rich text) */
  problem: string[];
  /** "Pause the video and try it" badge appears at (s); default 1.0 */
  promptAt?: number;
  prompt?: string;
  /** solution steps; the problem card compacts and steps appear under "Solution" */
  solution?: { text: string; at?: number; level?: number }[];
  solutionTitle?: string;
};

export const HomeworkCard: React.FC<HomeworkCardProps> = (p) => {
  const theme = useTheme();
  const meta = useMeta();
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const promptAt = p.promptAt ?? 1;
  const solStart = p.solution?.[0]?.at;
  const solOn = solStart === undefined ? 0 : interpolate(t, [solStart - 0.5, solStart], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const promptIn = interpolate(t, [promptAt, promptAt + 0.4], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const promptO = promptIn * (1 - solOn);
  const pulse = 1 + 0.03 * Math.sin(Math.max(0, t - promptAt) * Math.PI * 1.2) * promptIn;
  const fs = 44 - 4 * solOn;
  return (
    <SlideFrame kicker={p.kicker ?? (theme.name === "gold" ? `Homework · Lesson ${meta.lesson}` : `Lesson ${meta.lesson} · Homework`)} title={p.title ?? "Try it yourself"}>
      <div
        style={{
          background: theme.card,
          border: `2px solid ${theme.cardBorder}`,
          borderTop: `6px solid ${theme.name === "gold" ? theme.ink : theme.accent}`,
          borderRadius: 6,
          padding: `${34 - 10 * solOn}px 48px`,
          display: "flex",
          flexDirection: "column",
          gap: 14,
        }}
      >
        {p.problem.map((l, i) => (
          <div key={i} style={{ fontSize: fs, lineHeight: 1.4, color: theme.ink }}>
            <Rich text={l} />
          </div>
        ))}
      </div>
      <div style={{ display: "flex", justifyContent: "center", marginTop: 56, opacity: promptO, transform: `scale(${pulse})`, height: promptO > 0 ? undefined : 0 }}>
        <div style={{ display: "inline-flex", alignItems: "center", gap: 22, padding: "18px 40px", borderRadius: 999, background: theme.accent, color: "#fff", fontFamily: FONTS.sans, fontWeight: 600, fontSize: 38 }}>
          <svg width={34} height={34} viewBox="0 0 34 34">
            <rect x={6} y={4} width={8} height={26} rx={2} fill="#fff" />
            <rect x={20} y={4} width={8} height={26} rx={2} fill="#fff" />
          </svg>
          {p.prompt ?? "Pause the video and try it"}
        </div>
      </div>
      {p.solution && (
        <div style={{ opacity: solOn, marginTop: 30 - 56 * solOn }}>
          <div style={{ fontSize: 22, fontWeight: 600, letterSpacing: "0.2em", textTransform: "uppercase", color: theme.accent, marginBottom: 16 }}>
            {p.solutionTitle ?? "Solution"}
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {p.solution.map((s, i) => (
              <Step key={i} {...s} />
            ))}
          </div>
        </div>
      )}
    </SlideFrame>
  );
};

const Step: React.FC<{ text: string; at?: number; level?: number }> = ({ text, at, level }) => {
  const a = useAppear(at);
  return <Bullet text={text} level={level} style={a} />;
};
