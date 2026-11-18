"""Series slide chrome for Manim scenes (Lessons 37-41 look, measured from the L40 final video at 1080p):

    kicker  "THEORY OF COMPUTATION · LESSON 40"  Inter semibold, letter-spaced, body colour, left x=150 px
    title   Computer Modern serif, navy, with a short gold underline under its first word
    footer  hairline rule at y=1000 px (x 150-1770), text centred at y=1024 (kept out of the 3% safe margin), "Jizzakhiy Academy" left (bold navy), "<course> · Lesson N" right

    chrome = SeriesChrome("Stage 1: the leaves", lesson=38, kicker="Worked example")
    self.add(chrome)              # or self.play(chrome.intro())
    expr = ...; chrome.place_right(expr)   # header expression, right-aligned on the title row

Compact variant (default) keeps the header inside the top 180 px so diagrams can use the rest of the frame.
"""
from __future__ import annotations

import numpy as np
from manim import DOWN, LEFT, RIGHT, UP, UL, FadeIn, Line, Tex, VGroup, Write, AnimationGroup

from . import jz_style as S
from .jz_style import P


def px(x: float, y: float) -> np.ndarray:
    """1080p pixel coordinates (origin top-left, y down) -> Manim point."""
    return np.array([(x - 960) / 135.0, (540 - y) / 135.0, 0.0])


def grid(x: float, y: float, unit: float = 120.0) -> np.ndarray:
    """16x9 script grid (origin top-left, y down, 1 unit = 120 px) -> Manim point."""
    return px(x * unit, y * unit)


def _spaced(s: str) -> str:
    return " ".join(s.upper())


class SeriesChrome(VGroup):
    def __init__(self, title_tex: str, lesson: int, kicker: str = "Theory of Computation",
                 course: str = "Theory of Computation", title_size: float = 50, compact: bool = True):
        super().__init__()
        left = 150
        ky, ty = (52, 112) if compact else (110, 172)
        self.kicker = S.jz_text(_spaced(kicker) + "  ·  " + _spaced(f"Lesson {lesson}"), size=19,
                                weight="SEMIBOLD", color=P.BODY)
        self.kicker.move_to(px(left, ky), aligned_edge=LEFT)
        self.title = self._make_title(title_tex, title_size)
        self.title.move_to(px(left, ty), aligned_edge=LEFT)
        # gold underline as wide as the first word (the title is built as Tex(first_word, rest))
        w = self.title[0].width
        y = self.title.get_bottom()[1] - 0.12
        x0 = self.title.get_left()[0]
        self.underline = Line([x0, y, 0], [x0 + w, y, 0], color=P.ACCENT, stroke_width=6)
        self.rule = Line(px(150, 1000), px(1770, 1000), color=P.RULE, stroke_width=2)
        self.brand = S.jz_text("Jizzakhiy Academy", size=21, weight="SEMIBOLD", color=P.INK)
        self.brand.move_to(px(150, 1024), aligned_edge=LEFT)
        self.course = S.jz_text(f"{course}  ·  Lesson {lesson}", size=21, color=P.BODY)
        self.course.move_to(px(1770, 1024), aligned_edge=RIGHT)
        self.header = VGroup(self.kicker, self.title, self.underline)
        self.footer = VGroup(self.rule, self.brand, self.course)
        self.add(self.header, self.footer)

    def place_right(self, mob, x_right: float = 1770, y: float | None = None):
        """Right-align a header element (e.g. the regular expression) on the title row."""
        yy = self.title.get_center()[1] if y is None else px(0, y)[1]
        mob.move_to([px(x_right, 0)[0] - mob.width / 2, yy, 0])
        return mob

    @staticmethod
    def _make_title(title_tex: str, title_size: float):
        head, _, tail = title_tex.partition(" ")
        parts = [head, tail] if tail else [head]
        return Tex(*parts, color=P.INK, font_size=title_size, arg_separator=" ")
