import React, { createContext, useContext } from "react";
import { THEMES, Theme, ThemeName } from "./brand";

export type SceneMeta = { lesson: number; course: string; theme: ThemeName };

const ThemeCtx = createContext<Theme>(THEMES.teal);
const MetaCtx = createContext<SceneMeta>({ lesson: 0, course: "Theory of Computation", theme: "teal" });

export const BrandProvider: React.FC<{ meta: SceneMeta; children: React.ReactNode }> = ({ meta, children }) => (
  <MetaCtx.Provider value={meta}>
    <ThemeCtx.Provider value={THEMES[meta.theme] ?? THEMES.teal}>{children}</ThemeCtx.Provider>
  </MetaCtx.Provider>
);

export const useTheme = () => useContext(ThemeCtx);
export const useMeta = () => useContext(MetaCtx);
