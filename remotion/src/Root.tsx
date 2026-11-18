import React from "react";
import { Composition } from "remotion";
import { VIDEO } from "./brand/brand";
import { calculateSceneMetadata, Scene, SceneProps } from "./Scene";

const defaultProps: SceneProps = {
  lesson: 38,
  theme: "teal",
  component: "LessonSlide",
  data: { layout: "title", kicker: "Lesson 38 · Regular Languages", title: "Converting Regular Expressions to NFAs" },
};

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="Scene"
      component={Scene as unknown as React.FC<Record<string, unknown>>}
      durationInFrames={VIDEO.fps * 6}
      fps={VIDEO.fps}
      width={VIDEO.width}
      height={VIDEO.height}
      defaultProps={defaultProps as unknown as Record<string, unknown>}
      calculateMetadata={calculateSceneMetadata as never}
    />
  );
};
