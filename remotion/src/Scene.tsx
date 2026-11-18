import React from "react";
import { AbsoluteFill, CalculateMetadataFunction } from "remotion";
import { ThemeName, VIDEO } from "./brand/brand";
import { ensureMathFonts } from "./brand/fonts";
import { SceneFade } from "./brand/Frame";
import { BrandProvider } from "./brand/ThemeContext";
import { BulletBuild, BulletBuildProps } from "./components/BulletBuild";
import { DefinitionCard, DefinitionCardProps } from "./components/DefinitionCard";
import { HomeworkCard, HomeworkCardProps } from "./components/HomeworkCard";
import { LessonSlide, LessonSlideProps } from "./components/LessonSlide";
import { MathTable, MathTableProps } from "./components/MathTable";
import { QuizCard, QuizCardProps, quizTimes } from "./components/QuizCard";
import { RecapSlide, RecapSlideProps } from "./components/RecapSlide";

type Common = {
  /** lesson number used in kicker defaults and footer */
  lesson: number;
  course?: string;
  /** "teal" = L14-36 look (default), "gold" = L37-41 look */
  theme?: ThemeName;
  /** total scene length in seconds (clip + pause + 0.3 s tail). If omitted it is derived from the timings. */
  durationSec?: number;
  fadeInSec?: number;
  fadeOutSec?: number;
};

export type SceneProps = Common &
  (
    | { component: "LessonSlide"; data: LessonSlideProps }
    | { component: "DefinitionCard"; data: DefinitionCardProps }
    | { component: "BulletBuild"; data: BulletBuildProps }
    | { component: "MathTable"; data: MathTableProps }
    | { component: "QuizCard"; data: QuizCardProps }
    | { component: "HomeworkCard"; data: HomeworkCardProps }
    | { component: "RecapSlide"; data: RecapSlideProps }
  );

const lastTime = (p: SceneProps): number => {
  const ats: number[] = [0];
  const push = (x?: number) => x !== undefined && ats.push(x);
  const d = p.data as Record<string, unknown>;
  switch (p.component) {
    case "QuizCard": {
      const q = quizTimes(p.data);
      return q.reasonAt + 4;
    }
    case "BulletBuild":
      p.data.bullets.forEach((b) => push(b.at));
      push(p.data.mathAt);
      break;
    case "DefinitionCard":
      p.data.lines.forEach((b) => push(b.at));
      break;
    case "MathTable":
      (p.data.rowAt ?? []).forEach(push);
      (p.data.highlights ?? []).forEach((h) => push(h.until ?? h.at));
      break;
    case "HomeworkCard":
      push(p.data.promptAt);
      (p.data.solution ?? []).forEach((s) => push(s.at));
      break;
    case "RecapSlide":
      p.data.takeaways.forEach((b) => push(b.at));
      push(p.data.upNextAt);
      break;
    default:
      push(d.textAt as number | undefined);
  }
  return Math.max(...ats) + 3;
};

/** Spread missing reveal times evenly across the scene (rule: "otherwise spread the bullets evenly"). */
const fillTimes = <T extends { at?: number }>(items: T[] | undefined, total: number, start = 0.6): T[] | undefined => {
  if (!items || items.every((i) => i.at !== undefined)) return items;
  const span = Math.max(1, total - start - 2);
  return items.map((it, i) => (it.at !== undefined ? it : { ...it, at: start + (span * i) / items.length }));
};

export const normalize = (p: SceneProps): SceneProps => {
  const total = p.durationSec ?? 10;
  const q = JSON.parse(JSON.stringify(p)) as SceneProps;
  if (q.component === "BulletBuild") q.data.bullets = fillTimes(q.data.bullets, total)!;
  if (q.component === "DefinitionCard") q.data.lines = fillTimes(q.data.lines, total)!;
  if (q.component === "RecapSlide") q.data.takeaways = fillTimes(q.data.takeaways, total)!;
  return q;
};

export const calculateSceneMetadata: CalculateMetadataFunction<SceneProps> = ({ props }) => {
  const sec = props.durationSec ?? lastTime(props);
  return {
    durationInFrames: Math.max(1, Math.round(sec * VIDEO.fps)),
    fps: VIDEO.fps,
    width: VIDEO.width,
    height: VIDEO.height,
    props: normalize({ ...props, durationSec: sec }),
  };
};

export const Scene: React.FC<SceneProps> = (props) => {

  ensureMathFonts();
  const meta = { lesson: props.lesson, course: props.course ?? "Theory of Computation", theme: props.theme ?? "teal" };
  let body: React.ReactNode = null;
  switch (props.component) {
    case "LessonSlide":
      body = <LessonSlide {...props.data} />;
      break;
    case "DefinitionCard":
      body = <DefinitionCard {...props.data} />;
      break;
    case "BulletBuild":
      body = <BulletBuild {...props.data} />;
      break;
    case "MathTable":
      body = <MathTable {...props.data} />;
      break;
    case "QuizCard":
      body = <QuizCard {...props.data} />;
      break;
    case "HomeworkCard":
      body = <HomeworkCard {...props.data} />;
      break;
    case "RecapSlide":
      body = <RecapSlide {...props.data} />;
      break;
    default:
      body = <div style={{ fontSize: 60, color: "red", padding: 100 }}>Unknown component {(props as { component: string }).component}</div>;
  }
  return (
    <BrandProvider meta={meta}>
      <AbsoluteFill style={{ background: "#fff" }}>
        <SceneFade inSec={props.fadeInSec} outSec={props.fadeOutSec}>
          {body}
        </SceneFade>
      </AbsoluteFill>
    </BrandProvider>
  );
};
