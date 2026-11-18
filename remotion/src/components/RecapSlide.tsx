import React from "react";
import { FONTS } from "../brand/brand";
import { Bullet, SlideFrame, useAppear } from "../brand/Frame";
import { Rich } from "../brand/Rich";
import { useMeta, useTheme } from "../brand/ThemeContext";

export type RecapSlideProps = {
  kicker?: string;
  /** usually the lesson title */
  title: string;
  /** 3-5 takeaways (rich text); `at` = reveal time in seconds */
  takeaways: { text: string; at?: number }[];
  /** optional "Up next" strip, as on L31 / L37-41 end slides */
  upNext?: { lesson: number; title: string };
  upNextAt?: number;
};

export const RecapSlide: React.FC<RecapSlideProps> = (p) => {
  const theme = useTheme();
  const meta = useMeta();
  const up = useAppear(p.upNextAt);
  const gold = theme.name === "gold";
  return (
    <SlideFrame kicker={p.kicker ?? (gold ? `Lesson ${meta.lesson} · Recap` : `Lesson ${meta.lesson} · Summary`)} title={p.title}>
      <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
        {p.takeaways.map((k, i) => (
          <Item key={i} {...k} />
        ))}
      </div>
      {p.upNext && (
        <div style={{ ...up, position: "absolute", left: 0, right: 0, bottom: 10 }}>
          <div
            style={
              gold
                ? { background: "#EEF1F6", borderRadius: 6, padding: "22px 34px" }
                : { borderTop: `2px solid ${theme.rule}`, paddingTop: 28 }
            }
          >
            <div style={{ fontFamily: FONTS.sans, fontSize: 22, fontWeight: 600, letterSpacing: "0.2em", color: theme.accent, textTransform: "uppercase" }}>Up next</div>
            <div style={{ fontFamily: gold ? FONTS.serif : FONTS.sans, fontSize: 44, color: theme.ink, marginTop: 10, fontWeight: gold ? 400 : 500 }}>
              <Rich text={`Lesson ${p.upNext.lesson} — ${p.upNext.title}`} />
            </div>
          </div>
        </div>
      )}
    </SlideFrame>
  );
};

const Item: React.FC<{ text: string; at?: number }> = ({ text, at }) => {
  const a = useAppear(at);
  return <Bullet text={text} style={a} />;
};
