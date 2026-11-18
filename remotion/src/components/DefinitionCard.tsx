import React from "react";
import { Bullet, SlideFrame, useAppear } from "../brand/Frame";
import { Rich } from "../brand/Rich";
import { useMeta, useTheme } from "../brand/ThemeContext";

export type DefinitionCardProps = {
  /** e.g. "Definition 1.37" (default "Definition · Lesson NN") */
  kicker?: string;
  title: string;
  /** optional lead sentence inside the card, before the lines */
  lead?: string;
  leadAt?: number;
  /** card lines (rich text); bullets unless `plain` */
  lines: { text: string; at?: number; level?: number }[];
  plain?: boolean;
  /** e.g. "Sipser, Definition 1.64" – shown under the card */
  source?: string;
};

export const DefinitionCard: React.FC<DefinitionCardProps> = (p) => {
  const theme = useTheme();
  const meta = useMeta();
  const lead = useAppear(p.leadAt);
  return (
    <SlideFrame kicker={p.kicker ?? `Definition · Lesson ${meta.lesson}`} title={p.title}>
      <div
        style={{
          background: theme.card,
          border: `2px solid ${theme.cardBorder}`,
          borderLeft: `8px solid ${theme.name === "gold" ? theme.ink : theme.accent}`,
          borderRadius: 6,
          padding: "40px 52px 44px 48px",
          boxShadow: theme.name === "gold" ? "0 6px 24px rgba(20,32,60,0.06)" : "none",
          display: "flex",
          flexDirection: "column",
          gap: 22,
        }}
      >
        {p.lead && (
          <div style={{ ...lead, fontSize: 42, lineHeight: 1.35, color: theme.ink }}>
            <Rich text={p.lead} />
          </div>
        )}
        {p.lines.map((l, i) => (
          <Line key={i} {...l} plain={p.plain} />
        ))}
      </div>
      {p.source && <div style={{ fontSize: 22, color: theme.muted, marginTop: 22 }}>{p.source}</div>}
    </SlideFrame>
  );
};

const Line: React.FC<{ text: string; at?: number; level?: number; plain?: boolean }> = ({ text, at, level, plain }) => {
  const theme = useTheme();
  const a = useAppear(at);
  if (plain)
    return (
      <div style={{ ...a, fontSize: 40, lineHeight: 1.4, color: theme.body, marginLeft: (level ?? 0) * 48 }}>
        <Rich text={text} />
      </div>
    );
  return <Bullet text={text} level={level} style={a} />;
};
