"""Jizzakhiy Academy Manim kit.  `from lib import *` gives manim + house style + diagram tools."""
from manim import *  # noqa: F401,F403

from .jz_style import (  # noqa: F401
    EDGE_LABEL_SCALE,
    LABEL_SCALE,
    SANS,
    STATE_R,
    STROKE,
    P,
    Palette,
    apply_defaults,
    jz_kicker,
    jz_text,
    state_tex,
    sym_tex,
    use_theme,
)
from .state_diagram import StateDiagram, eps_closure, nfa_run, nfa_step  # noqa: F401
from .trace import TraceHighlighter  # noqa: F401
from .chrome import SeriesChrome, grid, px  # noqa: F401
