"""Jizzakhiy Academy house style for Manim.

Import this first in every scene file:

    import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    from lib import *          # style + StateDiagram + TraceHighlighter

Colours were sampled from past finished lessons (see remotion/src/brand/brand.ts):
  teal theme (Lessons 14-36): ink #202124, body #404247, teal #13736C, hairline #E4E5EA
  gold theme (Lessons 37-41): navy ink #14203C, gold #C9A227, light-blue state fill #E3ECFA
"""
from __future__ import annotations

import os
from pathlib import Path

import manimpango
from manim import (
    Arc,
    ArcBetweenPoints,
    Arrow,
    Circle,
    CurvedArrow,
    DashedLine,
    Dot,
    Line,
    MathTex,
    Polygon,
    Rectangle,
    RoundedRectangle,
    Square,
    Tex,
    TexTemplate,
    Text,
    VMobject,
    config,
)

# ---------------------------------------------------------------- tool paths (MiKTeX / ffmpeg may be missing from PATH)
import shutil

for _p in (
    Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/MiKTeX/miktex/bin/x64",
    Path("C:/Program Files/MiKTeX/miktex/bin/x64"),
    Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/WinGet/Links",
):
    if _p.is_dir() and str(_p) not in os.environ.get("PATH", ""):
        if (_p.name == "x64" and shutil.which("latex") is None) or (_p.name == "Links" and shutil.which("ffmpeg") is None):
            os.environ["PATH"] = str(_p) + os.pathsep + os.environ.get("PATH", "")

# ---------------------------------------------------------------- fonts
FONT_DIR = Path(__file__).resolve().parent / "fonts"
for _f in sorted(FONT_DIR.glob("*.ttf")):
    manimpango.register_font(str(_f))
SANS = "Inter"  # same face as the Remotion slides (Inter 400/500/600/700 bundled in lib/fonts)

# ---------------------------------------------------------------- palette
WHITE_BG = "#FFFFFF"


class Palette:
    """Mutable palette so a scene can switch theme with use_theme("gold")."""

    name = "teal"
    BG = "#FFFFFF"
    INK = "#202124"  # strokes, state circles, labels
    BODY = "#404247"  # secondary text
    MUTED = "#6F727A"  # captions
    ACCENT = "#13736C"  # teal highlight (active states, edges, read head)
    ACCENT_SOFT = "#DDF0ED"  # fill of highlighted states / tape cells
    RULE = "#E4E5EA"  # hairlines, tape cell borders
    FADED = "#B8BBC2"  # de-emphasised elements
    STATE_FILL = "#FFFFFF"  # inside of state circles / tape cells (white card look)
    CARD = "#FFFFFF"  # diagram cards


P = Palette


def use_theme(name: str = "teal") -> None:
    """'teal' = L14-36 look (default). 'gold' = L37-41 look (navy ink, gold accent, off-white #F6F7FA bg,
    white state fill, sampled from the L40 final video)."""
    if name == "gold":
        P.name, P.BG, P.INK, P.BODY, P.MUTED = "gold", "#F6F7FA", "#14203C", "#4C5465", "#4E5464"
        P.ACCENT, P.ACCENT_SOFT, P.RULE, P.FADED = "#C9A227", "#F5EBC6", "#D6DBE1", "#B9C0CC"
        P.STATE_FILL, P.CARD = "#FFFFFF", "#FFFFFF"
    else:
        P.name, P.BG, P.INK, P.BODY, P.MUTED = "teal", "#FFFFFF", "#202124", "#404247", "#6F727A"
        P.ACCENT, P.ACCENT_SOFT, P.RULE, P.FADED = "#13736C", "#DDF0ED", "#E4E5EA", "#B8BBC2"
        P.STATE_FILL, P.CARD = "#FFFFFF", "#FFFFFF"
    apply_defaults()


# ---------------------------------------------------------------- sizes (Manim units; 1 unit = 135 px at 1080p)
STROKE = 5  # state / edge stroke width (matches the ~5 px strokes of L40 diagrams)
STATE_R = 0.48  # state radius (~65 px)
LABEL_SCALE = 0.95  # state label MathTex scale
EDGE_LABEL_SCALE = 0.85


def apply_defaults() -> None:
    config.background_color = P.BG
    config.frame_rate = 24
    MathTex.set_default(color=P.INK)
    Tex.set_default(color=P.INK)
    Text.set_default(color=P.INK, font=SANS)
    Circle.set_default(color=P.INK, stroke_width=STROKE)
    Line.set_default(color=P.INK, stroke_width=STROKE)
    Arrow.set_default(color=P.INK, stroke_width=STROKE)


apply_defaults()


def jz_text(s: str, size: float = 36, weight: str = "NORMAL", color: str | None = None, **kw) -> Text:
    """Inter text; size in px at 1080p (Text font_size is in 1080p px-ish units)."""
    return Text(s, font=SANS, font_size=size, weight=weight, color=color or P.INK, **kw)


def jz_kicker(s: str, color: str | None = None, size: float = 22) -> Text:
    """Small uppercase letter-spaced kicker like 'LESSON 38'."""
    spaced = " ".join(s.upper())
    return Text(spaced, font=SANS, font_size=size, weight="SEMIBOLD", color=color or P.ACCENT)


EPS_NAMES = {"", "e", "eps", "epsilon", "ε", "\\varepsilon", "\\epsilon"}


def sym_tex(sym: str) -> str:
    """Alphabet symbol -> TeX (ε names become \\varepsilon)."""
    return r"\varepsilon" if sym in EPS_NAMES else sym


def state_tex(name: str) -> str:
    """'q0' -> 'q_{0}', 'q_start' -> 'q_{\\text{start}}', 'q12' -> 'q_{12}'."""
    import re

    m = re.fullmatch(r"([A-Za-z]+)_?(\d+)", name)
    if m:
        return f"{m.group(1)}_{{{m.group(2)}}}"
    m = re.fullmatch(r"([A-Za-z])_([A-Za-z]+)", name)
    if m:
        return f"{m.group(1)}_{{\\text{{{m.group(2)}}}}}"
    return name
