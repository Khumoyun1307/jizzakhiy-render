"""TraceHighlighter: input tape + moving read head + active state set, driving a StateDiagram.

    tr = TraceHighlighter(diagram, "aab", position=DOWN * 3)
    self.play(tr.show())                       # tape, head on cell 0, start set highlighted
    for i in range(len(word)):
        self.play(*tr.step_anims(i))           # flashes the edges used, moves head, updates active set
    self.play(tr.finish())                     # verdict: accept / reject from the spec

Active sets come from the spec itself (nfa_run: symbol moves + ε-closure), so the trace is always consistent
with what is drawn. Pass `sets=[...]` to override with the fact-checked sets from scenes.json instead.
"""
from __future__ import annotations

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    AnimationGroup,
    Create,
    FadeIn,
    FadeOut,
    MathTex,
    RoundedRectangle,
    Square,
    Succession,
    Text,
    Transform,
    Triangle,
    VGroup,
    Wait,
)
import numpy as np

from . import jz_style as S
from .jz_style import P
from .state_diagram import StateDiagram, nfa_run


class TraceHighlighter(VGroup):
    def __init__(
        self,
        diagram: StateDiagram,
        word: str | list[str],
        position=DOWN * 3.0,
        cell: float = 0.7,
        sets: list[list[str]] | None = None,
        show_set: bool = True,
        set_name: str = "",
    ):
        super().__init__()
        self.d = diagram
        self.word = list(word)
        run = nfa_run(diagram.spec, self.word)
        self.sets = sets if sets is not None else [r[0] for r in run]
        self.used = [r[1] for r in run]
        self.cell = cell
        # tape
        cells = VGroup()
        for ch in self.word or [" "]:
            sq = Square(cell, color=P.INK, stroke_width=3).set_fill(P.STATE_FILL, 1)
            sym = MathTex(S.sym_tex(ch), color=P.INK).scale(0.95) if ch.strip() else VGroup()
            cells.add(VGroup(sq, sym))
        cells.arrange(RIGHT, buff=0)
        for c in cells:
            if len(c) > 1 and len(c[1]):
                c[1].move_to(c[0])
        self.cells = cells
        caption = S.jz_kicker("Input", color=P.MUTED, size=20)
        caption.next_to(cells, LEFT, buff=0.35)
        self.tape = VGroup(caption, cells)
        # read head: teal triangle above the cell + teal outline on the cell
        self.head = VGroup(
            Triangle(color=P.ACCENT, fill_opacity=1, stroke_width=0).scale(0.14).rotate(np.pi),
        )
        self.frame = Square(cell, color=P.ACCENT, stroke_width=7)
        # active set readout
        self.show_set = show_set
        self.set_name = set_name
        self.readout = self._readout(self.sets[0]) if show_set else VGroup()
        self.add(self.tape, self.frame, self.head, self.readout)
        self.move_to(position)
        self._place_head(0)
        self._place_readout(self.readout)

    # ------------------------------------------------------------ layout
    def _readout(self, states):
        inner = ", ".join(self.d.spec.get("labels", {}).get(s, S.state_tex(s)) for s in states) or r"\,"
        body = r"\emptyset" if not states else r"\{" + inner + r"\}"
        prefix = (self.set_name + " = ") if self.set_name else ""
        t = MathTex(prefix + body, color=P.ACCENT).scale(0.9)
        return t

    def _place_readout(self, m):
        m.next_to(self.cells, RIGHT, buff=0.6)

    def _cell_center(self, i):
        i = min(i, len(self.cells) - 1)
        c = self.cells[i][0].get_center()
        if i == len(self.word):  # past the end
            c = self.cells[-1][0].get_center() + RIGHT * self.cell
        return c

    def _place_head(self, i):
        c = self.cells[min(i, len(self.cells) - 1)][0].get_center() + (RIGHT * self.cell if i >= len(self.word) else 0)
        self.frame.move_to(c)
        self.head.next_to(self.frame, UP, buff=0.08)

    # ------------------------------------------------------------ animations
    def show(self):
        """Fade the tape in and highlight the start set (ε-closure of the start state)."""
        return AnimationGroup(
            FadeIn(self.tape, shift=UP * 0.2),
            FadeIn(self.frame),
            FadeIn(self.head, shift=DOWN * 0.1),
            FadeIn(self.readout),
            self.d.highlight_states(self.sets[0]),
            lag_ratio=0.15,
        )

    def step_anims(self, i: int, edge_flash: bool = True):
        """Animations for reading symbol i: edges used flash teal, head moves, active set updates.
        Play them in two calls for clarity:  self.play(tr.flash_edges(i)); self.play(tr.advance(i))"""
        return [self.flash_edges(i), self.advance(i)] if edge_flash else [self.advance(i)]

    def flash_edges(self, i: int):
        used = [e for e in self.used[i + 1] if e in self.d.edges]
        if not used:
            return Wait(0.2)
        return self.d.highlight_edges(used, on=True)

    def advance(self, i: int):
        prev, nxt = set(self.sets[i]), set(self.sets[i + 1])
        used = [e for e in self.used[i + 1] if e in self.d.edges]
        target = self.cells[i][0].get_center() + RIGHT * self.cell
        new_readout = self._readout(self.sets[i + 1])
        self._place_readout(new_readout)
        anims = [
            self.frame.animate.move_to(target).set_stroke(opacity=0 if i + 1 >= len(self.word) else 1),  # stroke only: set_opacity would fill the square
            self.head.animate.move_to(target + UP * (self.cell / 2 + 0.08 + self.head.height / 2)),
            self.cells[i].animate.set_opacity(0.45),
            Transform(self.readout, new_readout),
        ]
        off = [s for s in prev - nxt]
        on = [s for s in self.d.spec["states"] if s in nxt]
        if off:
            anims.append(self.d.highlight_states(off, on=False))
        if on:
            anims.append(self.d.highlight_states(on, on=True))
        if used:
            anims.append(self.d.highlight_edges(used, on=False))
        return AnimationGroup(*anims)

    def accepted(self) -> bool:
        return bool(set(self.sets[-1]) & set(self.d.spec.get("accept", [])))

    def finish(self, text: str | None = None):
        ok = self.accepted()
        msg = text or ("accept" if ok else "reject")
        col = P.ACCENT if ok else "#B42318"
        badge_t = S.jz_text(msg.upper(), size=26, weight="SEMIBOLD", color=col)
        box = RoundedRectangle(corner_radius=0.12, width=badge_t.width + 0.5, height=badge_t.height + 0.3, color=col, stroke_width=3)
        badge = VGroup(box, badge_t.move_to(box)).next_to(self.readout, RIGHT, buff=0.45)
        self.badge = badge
        return FadeIn(badge, scale=0.9)
