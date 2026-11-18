import React from "react";
import { Bullet, SlideFrame, useAppear } from "../brand/Frame";
import { Rich } from "../brand/Rich";
import { useTheme } from "../brand/ThemeContext";

export type BulletItem = { text: string; at?: number; level?: number };

export type BulletBuildProps = {
  kicker?: string;
  title: string;
  /** Bullets revealed at `at` seconds (from scene start). Missing `at` values are filled in by Scene (spread evenly). */
  bullets: BulletItem[];
  /** optional display math block revealed at mathAt */
  math?: string;
  mathAt?: number;
  source?: string;
  /** dim earlier bullets when a later one appears (focus mode) */
  focus?: boolean;
};

export const BulletBuild: React.FC<BulletBuildProps> = (p) => {
  const theme = useTheme();
  return (
    <SlideFrame kicker={p.kicker} title={p.title}>
      <div style={{ display: "flex", flexDirection: "column", gap: 26 }}>
        {p.bullets.map((b, i) => (
          <BulletRow key={i} item={b} next={p.focus ? p.bullets[i + 1]?.at : undefined} />
        ))}
        {p.math && <MathBlock tex={p.math} at={p.mathAt} />}
      </div>
      {p.source && (
        <div style={{ position: "absolute", bottom: 0, fontSize: 22, color: theme.muted }}>{p.source}</div>
      )}
    </SlideFrame>
  );
};

const BulletRow: React.FC<{ item: BulletItem; next?: number }> = ({ item, next }) => {
  const a = useAppear(item.at);
  const dim = useAppear(next, 0.4, 0);
  const o = (a.opacity as number | undefined) ?? 1;
  const d = next !== undefined ? 1 - 0.55 * ((dim.opacity as number) ?? 0) : 1;
  return <Bullet text={item.text} level={item.level ?? 0} style={{ ...a, opacity: o * d }} />;
};

const MathBlock: React.FC<{ tex: string; at?: number }> = ({ tex, at }) => {
  const theme = useTheme();
  const a = useAppear(at);
  return (
    <div style={{ ...a, fontSize: 46, color: theme.ink, marginLeft: 44 }}>
      <Rich text={`$$${tex}$$`} mathScale={1} />
    </div>
  );
};
