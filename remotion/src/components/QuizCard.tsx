import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { FONTS } from "../brand/brand";
import { SlideFrame, useAppear } from "../brand/Frame";
import { Rich } from "../brand/Rich";
import { useMeta, useTheme } from "../brand/ThemeContext";

export type QuizCardProps = {
  kicker?: string;
  /** the question (rich text) */
  question: string;
  /** optional multiple-choice options (rich text); shown as A, B, C… */
  options?: string[];
  /** index of the correct option, highlighted when the answer appears */
  correct?: number;
  /** when "Pause and think" + countdown ring appear (s). Default 0.6 s after the question. */
  thinkAt?: number;
  /** countdown length in seconds (default 5) */
  countdown?: number;
  /** when the answer appears (default thinkAt + countdown) */
  answerAt?: number;
  /** answer headline (rich text) */
  answer: string;
  /** one-line reason (rich text) */
  reason?: string;
  /** reason appears at (default answerAt + 0.8) */
  reasonAt?: number;
  thinkLabel?: string;
};

export const quizTimes = (p: QuizCardProps) => {
  const thinkAt = p.thinkAt ?? 1;
  const countdown = p.countdown ?? 5;
  const answerAt = p.answerAt ?? thinkAt + countdown;
  const reasonAt = p.reasonAt ?? answerAt + 0.8;
  return { thinkAt, countdown, answerAt, reasonAt };
};

export const QuizCard: React.FC<QuizCardProps> = (p) => {
  const theme = useTheme();
  const meta = useMeta();
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const { thinkAt, countdown, answerAt, reasonAt } = quizTimes(p);
  const ans = useAppear(answerAt, 0.5, 16);
  const reason = useAppear(reasonAt, 0.5, 12);
  const kicker = p.kicker ?? (theme.name === "gold" ? `Question · Lesson ${meta.lesson}` : `Lesson ${meta.lesson} · Quick check`);
  const ansOn = interpolate(t, [answerAt, answerAt + 0.4], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <SlideFrame kicker={kicker} bodyTop={150}>
      <div style={{ position: "absolute", left: 0, top: 0, width: 1180 }}>
        <div style={{ fontFamily: theme.titleFont, fontWeight: theme.name === "gold" ? 400 : 600, fontSize: 56, lineHeight: 1.25, color: theme.ink, letterSpacing: theme.name === "gold" ? 0 : "-0.01em" }}>
          <Rich text={p.question} mathScale={1} />
        </div>
        {p.options && (
          <div style={{ display: "flex", flexDirection: "column", gap: 16, marginTop: 40 }}>
            {p.options.map((o, i) => {
              const ok = i === p.correct;
              const hl = ok ? ansOn : 0;
              const dim = !ok && p.correct !== undefined ? 1 - 0.45 * ansOn : 1;
              return (
                <div
                  key={i}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 24,
                    fontSize: 40,
                    color: theme.body,
                    opacity: dim,
                    padding: "12px 22px",
                    borderRadius: 8,
                    border: `2px solid ${hl > 0 ? theme.accent : theme.cardBorder}`,
                    background: hl > 0 ? `color-mix(in srgb, ${theme.accent} ${Math.round(12 * hl)}%, ${theme.card})` : theme.card,
                  }}
                >
                  <span style={{ width: 48, height: 48, borderRadius: 24, flex: "none", display: "inline-flex", alignItems: "center", justifyContent: "center", fontSize: 26, fontWeight: 700, color: hl > 0.5 ? "#fff" : theme.accent, background: hl > 0.5 ? theme.accent : "transparent", border: `2px solid ${theme.accent}` }}>
                    {String.fromCharCode(65 + i)}
                  </span>
                  <Rich text={o} />
                </div>
              );
            })}
          </div>
        )}
        <div
          style={{
            ...ans,
            marginTop: 44,
            borderLeft: `8px solid ${theme.accent}`,
            background: theme.card,
            border: `2px solid ${theme.cardBorder}`,
            borderLeftWidth: 8,
            borderLeftColor: theme.accent,
            borderRadius: 6,
            padding: "24px 36px",
          }}
        >
          <div style={{ fontFamily: FONTS.sans, fontSize: 22, fontWeight: 600, letterSpacing: "0.2em", color: theme.accent, textTransform: "uppercase" }}>Answer</div>
          <div style={{ fontSize: 44, color: theme.ink, fontWeight: 600, marginTop: 8, lineHeight: 1.3 }}>
            <Rich text={p.answer} />
          </div>
          {p.reason && (
            <div style={{ ...reason, fontSize: 36, color: theme.body, marginTop: 10, lineHeight: 1.38 }}>
              <Rich text={p.reason} />
            </div>
          )}
        </div>
      </div>
      <Countdown thinkAt={thinkAt} seconds={countdown} answerAt={answerAt} label={p.thinkLabel ?? "Pause and think"} />
    </SlideFrame>
  );
};

const Countdown: React.FC<{ thinkAt: number; seconds: number; answerAt: number; label: string }> = ({ thinkAt, seconds, answerAt, label }) => {
  const theme = useTheme();
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const appear = interpolate(t, [thinkAt, thinkAt + 0.4], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const leave = interpolate(t, [answerAt, answerAt + 0.4], [1, 0.0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const o = Math.min(appear, leave);
  if (o <= 0) return null;
  const elapsed = Math.min(Math.max(t - thinkAt, 0), seconds);
  const frac = 1 - elapsed / seconds;
  const n = Math.max(1, Math.ceil(seconds - elapsed - 1e-6));
  const done = t - thinkAt >= seconds;
  const R = 120;
  const C = 2 * Math.PI * R;
  return (
    <div style={{ position: "absolute", right: 0, top: 40, width: 360, display: "flex", flexDirection: "column", alignItems: "center", opacity: o, transform: `scale(${0.94 + 0.06 * appear})` }}>
      <div style={{ fontSize: 24, fontWeight: 600, letterSpacing: "0.2em", textTransform: "uppercase", color: theme.accent, marginBottom: 26 }}>{label}</div>
      <svg width={300} height={300} viewBox="0 0 300 300">
        <circle cx={150} cy={150} r={R} fill={theme.card} stroke={theme.rule} strokeWidth={14} />
        <circle
          cx={150}
          cy={150}
          r={R}
          fill="none"
          stroke={theme.accent}
          strokeWidth={14}
          strokeLinecap="round"
          strokeDasharray={C}
          strokeDashoffset={C * (1 - frac)}
          transform="rotate(-90 150 150)"
        />
        <text x={150} y={150} textAnchor="middle" dominantBaseline="central" fontFamily={FONTS.sans} fontWeight={700} fontSize={110} fill={theme.ink}>
          {done ? "" : n}
        </text>
        {done && (
          <g transform="translate(150 150)" fill={theme.ink}>
            <rect x={-30} y={-40} width={20} height={80} rx={4} />
            <rect x={10} y={-40} width={20} height={80} rx={4} />
          </g>
        )}
      </svg>
    </div>
  );
};
