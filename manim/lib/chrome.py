"""Series slide chrome for Manim scenes, matched pixel-for-pixel to the Remotion slides (and L37-L41):
measured on 02_visuals/scenes/S05.mp4 (Lesson 38) at 1080p.

    kicker  "<SECTION> · LESSON 38"  Inter semibold, letter-spaced, body colour; cap top y=101, cap height 16 px, x=160
    title   Computer Modern serif, navy; cap top y=141, cap height 53 px (baseline ~193), x=160
    underline  gold, 96 x 6 px at x 160-256, y 219-224
    footer  rule y=998-999 (x 160-1760); "Jizzakhiy Academy" (semibold navy) left and "<course> · Lesson N" right,
            text box y 1024-1044 (22 px Inter)

    chrome = SeriesChrome("Stage 1: the leaves", lesson=38, kicker="Worked example")
    self.add(chrome)
    expr = ...; chrome.place_right(expr)   # header expression, right-aligned on the title row

Calibration (manim Text): cap height = 1.40 x font_size  ->  22 px Inter = font_size 11.4.
Tex: cap height ~= font_size px  ->  title font_size 53.
"""
from __future__ import annotations

import numpy as np
from manim import LEFT, RIGHT, UL, UR, Line, Tex, VGroup

from . import jz_style as S
from .jz_style import P

LEFT_X, RIGHT_X = 160, 1760
TEXT_22PX = 11.4  # manim Text font_size that renders 22 px Inter (cap height 16 px)


def px(x: float, y: float) -> np.ndarray:
    """1080p pixel coordinates (origin top-left, y down) -> Manim point."""
    return np.array([(x - 960) / 135.0, (540 - y) / 135.0, 0.0])


def grid(x: float, y: float, unit: float = 120.0) -> np.ndarray:
    """16x9 script grid (origin top-left, y down, 1 unit = 120 px) -> Manim point."""
    return px(x * unit, y * unit)


def _tracked(s: str) -> str:
    """Uppercase with letter tracking like the slides' CSS letter-spacing (U+2005 between letters)."""
    return " ".join(s.upper())


def kicker_text(section: str, lesson: int) -> str:
    """Series wording: '<SECTION> · LESSON NN'."""
    return _tracked(section) + "   ·   " + _tracked(f"Lesson {lesson}")


class SeriesChrome(VGroup):
    def __init__(self, title_tex: str, lesson: int, kicker: str = "Theory of Computation",
                 course: str = "Theory of Computation", title_size: float = 53, **_ignored):
        super().__init__()
        self.kicker = S.jz_text(kicker_text(kicker, lesson), size=TEXT_22PX, weight="SEMIBOLD", color=P.BODY)
        self._cap_top(self.kicker, "L", 101)
        self.title = self._make_title(title_tex, title_size)
        self.title.move_to(px(LEFT_X, 141), aligned_edge=UL)
        self.underline = Line(px(LEFT_X, 221.5), px(LEFT_X + 96, 221.5), color=P.ACCENT, stroke_width=6)
        self.rule = Line(px(LEFT_X, 998.5), px(RIGHT_X, 998.5), color=P.RULE, stroke_width=2)
        self.brand = S.jz_text("Jizzakhiy Academy", size=TEXT_22PX, weight="SEMIBOLD", color=P.INK)
        self.brand.move_to(px(LEFT_X, 1024), aligned_edge=UL)
        self.course = S.jz_text(f"{course}  ·  Lesson {lesson}", size=TEXT_22PX, color=P.BODY)
        self.course.move_to(px(RIGHT_X, 1024), aligned_edge=UR)
        self.header = VGroup(self.kicker, self.title, self.underline)
        self.footer = VGroup(self.rule, self.brand, self.course)
        self.add(self.header, self.footer)

    @staticmethod
    def _cap_top(mob, _ch, y):
        # kicker is all caps/digits: its bounding-box top is the cap top
        mob.move_to(px(LEFT_X, y), aligned_edge=UL)

    def place_right(self, mob, x_right: float = RIGHT_X, y: float | None = None):
        """Right-align a header element (e.g. the regular expression) on the title row (cap band 141-193)."""
        yy = px(0, 167 if y is None else y)[1]
        mob.move_to([px(x_right, 0)[0] - mob.width / 2, yy, 0])
        return mob

    @staticmethod
    def _make_title(title_tex: str, title_size: float):
        head, _, tail = title_tex.partition(" ")
        parts = [head, tail] if tail else [head]
        return Tex(*parts, color=P.INK, font_size=title_size, arg_separator=" ")
