"""StateDiagram: a finite-automaton drawing built from a spec dict.

spec = {
  "states":   ["q0", "q1", ...],                    # order = default build order
  "start":    "q0",
  "accept":   ["q2"],
  "alphabet": ["a", "b"],                            # informational; "eps"/"ε"/"" = epsilon
  "delta":    {"q0": {"a": ["q1"], "eps": ["q2"]}},  # NFA style; DFA = one-element lists
  "layout":   {"q0": [-4, 0], "q1": [-1, 1], ...},   # Manim units (x right, y up), centre = [0,0]
  # optional
  "labels":   {"q0": "q_0"},                         # TeX override for state labels
  "start_dir": "left",                               # side the start arrow comes from: left/up/down/right or [dx,dy]
  "bend":     {"q1->q2": 0.5},                        # force a curve (radians; + bends left of travel)
  "loop_dir": {"q1": "up"},                          # self-loop side (default: away from neighbours)
  "dash_epsilon": False,                             # draw ε-edges dashed (L40 style)
  "scale": 1.0,                                      # multiply all layout coordinates
  "starts":   ["q0", "q3"],                          # several start arrows (component machines); default [start]
  "start_dir": {"q0": "left", "q3": [-1, 1]},        # ...per state (a single value applies to all)
  "start_len": 0.85,                                 # start-arrow length (Manim units)
  "via":      {"q2->q0": [0, 3]},                    # route an edge as a circular arc through this point
  "bridge":   {"q3->q0": 2.6},                       # route as a smooth "bridge" over (or under) everything,
                                                     #   with its extreme point at this y (Manim units)
  "via_label": {"q2->q0": "inside"},                  # label outside (default) or inside a via/bridge curve
}

Edges with several symbols between the same pair are merged into one arrow with label "a, b".
Opposite pairs (p->q and q->p) are drawn as two arcs bending apart.
"""
from __future__ import annotations

import math
from typing import Iterable

import numpy as np
from manim import (
    DOWN,
    LEFT,
    ORIGIN,
    RIGHT,
    UP,
    AnimationGroup,
    ArcBetweenPoints,
    Arrow,
    Circle,
    Create,
    DashedVMobject,
    FadeIn,
    GrowArrow,
    Line,
    MathTex,
    StealthTip,
    TipableVMobject,
    ArrowTriangleFilledTip,
    VGroup,
    VMobject,
    Write,
    LaggedStart,
)

from . import jz_style as S
from .jz_style import P


def _vec(v) -> np.ndarray:
    v = list(v)
    return np.array([float(v[0]), float(v[1]), 0.0])


_DIRS = {"left": LEFT, "right": RIGHT, "up": UP, "down": DOWN}


def _dir(v) -> np.ndarray:
    if isinstance(v, str):
        return _DIRS[v]
    d = _vec(v)
    return d / (np.linalg.norm(d) or 1)


def _rot(v: np.ndarray, a: float) -> np.ndarray:
    c, s = math.cos(a), math.sin(a)
    return np.array([c * v[0] - s * v[1], s * v[0] + c * v[1], 0.0])


class _BezierEdge(TipableVMobject):
    def __init__(self, p0, p1, p2, p3, **kw):
        super().__init__(**kw)
        self.start_new_path(p0)
        self.add_cubic_bezier_curve_to(p1, p2, p3)


class StateNode(VGroup):
    def __init__(self, name: str, tex: str, accept: bool, r: float):
        self.name = name
        self.circle = Circle(radius=r, color=P.INK, stroke_width=S.STROKE).set_fill(P.STATE_FILL, opacity=1)
        parts = [self.circle]
        self.inner = None
        if accept:
            self.inner = Circle(radius=r * 0.8, color=P.INK, stroke_width=S.STROKE * 0.8)
            parts.append(self.inner)
        self.label = MathTex(tex, color=P.INK).scale(S.LABEL_SCALE)
        if self.label.width > r * 1.6:
            self.label.scale_to_fit_width(r * 1.6)
        super().__init__(*parts, self.label)


class Edge(VGroup):
    def __init__(self, src: str, dst: str, path: VMobject, label: MathTex, epsilon_only: bool):
        self.src, self.dst = src, dst
        self.path = path
        self.label = label
        self.epsilon_only = epsilon_only
        super().__init__(path, label)


class StateDiagram(VGroup):
    """Build with StateDiagram(spec). Parts: .nodes[name], .edges[(src,dst)], .start_arrow."""

    def __init__(self, spec: dict, radius: float = S.STATE_R, label_scale: float = S.EDGE_LABEL_SCALE, **kw):
        super().__init__(**kw)
        self.spec = spec
        self.r = radius
        self.label_scale = label_scale
        sc = float(spec.get("scale", 1.0))
        self.pos = {s: _vec(spec["layout"][s]) * sc for s in spec["states"]}
        accept = set(spec.get("accept", []))
        labels = spec.get("labels", {})
        self.nodes: dict[str, StateNode] = {}
        for s in spec["states"]:
            n = StateNode(s, labels.get(s, S.state_tex(s)), s in accept, radius).move_to(self.pos[s])
            self.nodes[s] = n
        # merge symbols per (src,dst)
        pairs: dict[tuple[str, str], list[str]] = {}
        for src, row in (spec.get("delta") or {}).items():
            for sym, targets in row.items():
                if isinstance(targets, str):
                    targets = [targets]
                for t in targets:
                    pairs.setdefault((src, t), []).append(sym)
        self.pair_syms = pairs
        self._placed: list[np.ndarray] = []  # label boxes placed so far: [cx, cy, w, h]
        self.edges: dict[tuple[str, str], Edge] = {}
        for (src, dst), syms in pairs.items():
            self.edges[(src, dst)] = self._make_edge(src, dst, syms)
        starts = spec.get("starts")
        if starts is None:
            starts = [spec["start"]] if spec.get("start") is not None else []
        self.start_arrows = {s: self._make_start(s) for s in starts}
        self.start_arrow = self.start_arrows.get(spec.get("start"))
        self.add(*[e for e in self.edges.values()], *self.nodes.values())
        self.add(*self.start_arrows.values())
        # remember each part's opacities so hide_all()/build_*() can restore them exactly
        self._style = {id(m): (m.get_fill_opacity(), m.get_stroke_opacity()) for m in self.get_family()}

    def _reveal(self, mob):
        for m in mob.get_family():
            fo, so = self._style.get(id(m), (m.get_fill_opacity(), 1.0))
            m.set_fill(opacity=fo, family=False)
            m.set_stroke(opacity=so, family=False)
        return mob

    # ------------------------------------------------------------ construction
    def _label_tex(self, syms: list[str]) -> str:
        seen = []
        for s in syms:
            t = S.sym_tex(s)
            if t not in seen:
                seen.append(t)
        return ", ".join(seen)

    def _start_dir(self, s):
        sd = self.spec.get("start_dir", "left")
        if isinstance(sd, dict):
            sd = sd.get(s, "left")
        return _dir(sd)

    def _make_start(self, s=None):
        s = s if s is not None else self.spec.get("start")
        if s is None:
            return None
        d = self._start_dir(s)
        end = self.pos[s] + d * self.r
        start = end + d * float(self.spec.get("start_len", 0.85))
        a = Line(start, end, color=P.INK, stroke_width=S.STROKE)
        a.add_tip(tip_shape=ArrowTriangleFilledTip, tip_length=0.2, tip_width=0.2)
        return a

    def _loop_dir(self, s: str) -> np.ndarray:
        ld = self.spec.get("loop_dir", {}).get(s)
        if ld is not None:
            return _dir(ld)
        # away from neighbours and from the start arrow; prefer up, then down
        neigh = [self.pos[b] - self.pos[s] for (a, b) in self.pair_syms if a == s and b != s]
        neigh += [self.pos[a] - self.pos[s] for (a, b) in self.pair_syms if b == s and a != s]
        if s in self.spec.get("starts", [self.spec.get("start")]):
            neigh.append(self._start_dir(s) * 2)
        best, score = UP, -1e9
        for cand in (UP, DOWN, _rot(UP, 0.6), _rot(UP, -0.6), _rot(DOWN, 0.6), _rot(DOWN, -0.6), LEFT, RIGHT):
            sc = 0.0
            for v in neigh:
                n = np.linalg.norm(v) or 1
                sc -= max(0.0, float(np.dot(cand, v / n))) * 3 / n
            if np.allclose(cand, UP):
                sc += 0.25
            if np.allclose(cand, DOWN):
                sc += 0.15
            if sc > score:
                best, score = cand, sc
        return best

    def _make_edge(self, src: str, dst: str, syms: list[str]) -> Edge:
        r = self.r
        eps_only = all(s in S.EPS_NAMES for s in syms)
        lbl = MathTex(self._label_tex(syms), color=P.INK).scale(self.label_scale)
        if src == dst:
            d = self._loop_dir(src)
            c = self.pos[src]
            spread = 0.55
            p1 = c + _rot(d, spread) * r
            p2 = c + _rot(d, -spread) * r
            path = ArcBetweenPoints(p1, p2, angle=-math.pi * 1.55, color=P.INK, stroke_width=S.STROKE)
            path.add_tip(tip_shape=ArrowTriangleFilledTip, tip_length=0.18, tip_width=0.18)
            # put the label just beyond the loop's real outermost point (bounding box of the arc along d)
            pts = path.get_all_points()
            far = pts[np.argmax(pts @ d)]
            box_c = (pts.min(0) + pts.max(0)) / 2
            perp = np.array([-d[1], d[0], 0.0])
            anchor = box_c + d * float((far - box_c) @ d)
            lbl.move_to(anchor + d * (0.14 + 0.5 * self._extent(lbl, d)) + perp * 0.0)
            self._remember(lbl)
            return Edge(src, dst, self._maybe_dash(path, eps_only), lbl, eps_only)
        a, b = self.pos[src], self.pos[dst]
        u = (b - a) / np.linalg.norm(b - a)
        key = f"{src}->{dst}"
        bridge = self.spec.get("bridge", {}).get(key)
        if bridge is not None:
            path, mid, outward = self._bridge(a, b, float(bridge) * float(self.spec.get("scale", 1.0)), r)
            if self.spec.get("via_label", {}).get(key) == "inside":
                outward = -outward
            self._place_label(lbl, mid, [outward], u, flexible=False)
            return Edge(src, dst, self._maybe_dash(path, eps_only), lbl, eps_only)
        via = self.spec.get("via", {}).get(key)
        if via is not None:
            path, mid, outward = self._via_arc(a, b, _vec(via) * float(self.spec.get("scale", 1.0)), r)
            if self.spec.get("via_label", {}).get(key) == "inside":
                outward = -outward
            self._place_label(lbl, mid, [outward], u, flexible=False)
            return Edge(src, dst, self._maybe_dash(path, eps_only), lbl, eps_only)
        bend = self.spec.get("bend", {}).get(key)
        if bend is None:
            bend = 0.45 if (dst, src) in self.pair_syms else 0.0
        if abs(bend) < 1e-6:
            start, end = a + u * r, b - u * r
            path = Line(start, end, color=P.INK, stroke_width=S.STROKE)
            path.add_tip(tip_shape=ArrowTriangleFilledTip, tip_length=0.2, tip_width=0.2)
            mid = (start + end) / 2
            normal = _rot(u, math.pi / 2)
            self._place_label(lbl, mid, [normal, -normal], u)
        else:
            # leave the circles at +/- bend/1.6 from the centre line; bend>0 = curve to the LEFT of travel... we
            # use a clockwise arc (negative angle) so that the pair p->q, q->p separate cleanly.
            off = bend * 0.8
            start = a + _rot(u, off) * r
            end = b + _rot(-u, -off) * r
            path = ArcBetweenPoints(start, end, angle=-2 * bend, color=P.INK, stroke_width=S.STROKE)
            path.add_tip(tip_shape=ArrowTriangleFilledTip, tip_length=0.2, tip_width=0.2)
            mid = path.point_from_proportion(0.5)
            chord_mid = (start + end) / 2
            outward = mid - chord_mid
            n = np.linalg.norm(outward)
            outward = outward / n if n > 1e-6 else _rot(u, math.pi / 2)
            self._place_label(lbl, mid, [outward], u, flexible=False)
        return Edge(src, dst, self._maybe_dash(path, eps_only), lbl, eps_only)

    @staticmethod
    def _via_arc(a, b, v, r):
        """Circular arc from circle a to circle b (radius r) passing through point v. Returns (path, apex, outward)."""
        ax, ay, bx, by, vx, vy = a[0], a[1], b[0], b[1], v[0], v[1]
        dd = 2 * (ax * (by - vy) + bx * (vy - ay) + vx * (ay - by))
        ox = ((ax**2 + ay**2) * (by - vy) + (bx**2 + by**2) * (vy - ay) + (vx**2 + vy**2) * (ay - by)) / dd
        oy = ((ax**2 + ay**2) * (vx - bx) + (bx**2 + by**2) * (ax - vx) + (vx**2 + vy**2) * (bx - ax)) / dd
        o = np.array([ox, oy, 0.0])
        R = float(np.linalg.norm(a - o))
        ang = lambda p: math.atan2(p[1] - oy, p[0] - ox)
        ta, tb, tv = ang(a), ang(b), ang(v)
        tau = 2 * math.pi
        d_ab, d_av = (tb - ta) % tau, (tv - ta) % tau
        if d_av < d_ab:
            sign, sweep = 1.0, d_ab
        else:
            sign, sweep = -1.0, -(tau - d_ab)
        delta = 2 * math.asin(min(1.0, r / (2 * R)))
        t0, t1 = ta + sign * delta, tb - sign * delta
        p0 = o + R * np.array([math.cos(t0), math.sin(t0), 0.0])
        p1 = o + R * np.array([math.cos(t1), math.sin(t1), 0.0])
        path = ArcBetweenPoints(p0, p1, angle=sweep - 2 * sign * delta, color=P.INK, stroke_width=S.STROKE)
        path.add_tip(tip_shape=ArrowTriangleFilledTip, tip_length=0.2, tip_width=0.2)
        out = v - o
        out = out / (np.linalg.norm(out) or 1)
        return path, v, out

    @staticmethod
    def _bridge(a, b, y_peak, r, tilt=0.45):
        """Cubic 'bridge' from circle a to circle b leaving/entering vertically, extreme point at y_peak."""
        side = 1.0 if y_peak > (a[1] + b[1]) / 2 else -1.0
        sx = 1.0 if b[0] >= a[0] else -1.0
        d0 = np.array([sx * tilt, side, 0.0]); d0 /= np.linalg.norm(d0)
        d3 = np.array([-sx * tilt, side, 0.0]); d3 /= np.linalg.norm(d3)
        p0, p3 = a + d0 * r, b + d3 * r
        Y = (8 * y_peak - p0[1] - p3[1]) / 6
        dx = (p3[0] - p0[0]) * 0.12
        p1 = np.array([p0[0] + dx, Y, 0.0])
        p2 = np.array([p3[0] - dx, Y, 0.0])
        path = _BezierEdge(p0, p1, p2, p3, color=P.INK, stroke_width=S.STROKE)
        path.add_tip(tip_shape=ArrowTriangleFilledTip, tip_length=0.2, tip_width=0.2)
        mid = 0.125 * p0 + 0.375 * p1 + 0.375 * p2 + 0.125 * p3
        return path, mid, np.array([0.0, side, 0.0])

    def hide(self, states=(), edges=(), starts=()):
        """Hide selected parts (to be revealed later with build_states / build_edges / reveal_start)."""
        mobs = [self.nodes[s] for s in states] + [self.edges[tuple(e)] for e in edges]
        mobs += [self.start_arrows[s] for s in starts if s in self.start_arrows]
        for mob in mobs:
            for m in mob.get_family():
                m.set_fill(opacity=0, family=False)
                m.set_stroke(opacity=0, family=False)
        return self

    def reveal_start(self, s):
        a = self.start_arrows[s]
        self._reveal(a)
        return Create(a)

    def _maybe_dash(self, path: VMobject, eps_only: bool) -> VMobject:
        if not (eps_only and self.spec.get("dash_epsilon")):
            return path
        tip = path.pop_tips()[0] if hasattr(path, "pop_tips") and path.has_tip() else None
        dashed = DashedVMobject(path, num_dashes=max(6, int(path.get_arc_length() / 0.18)), dashed_ratio=0.55)
        dashed.set_stroke(P.INK, S.STROKE)
        if tip is not None:
            dashed.add(tip)
        return dashed

    @staticmethod
    def _extent(m, d) -> float:
        return abs(d[0]) * m.width + abs(d[1]) * m.height

    def _remember(self, lbl):
        self._placed.append(np.array([*lbl.get_center()[:2], lbl.width, lbl.height]))

    def _overlap(self, center, w, h) -> float:
        cost = 0.0
        for s, p in self.pos.items():
            dx = max(abs(center[0] - p[0]) - w / 2, 0)
            dy = max(abs(center[1] - p[1]) - h / 2, 0)
            dist = math.hypot(dx, dy)
            if dist < self.r + 0.08:
                cost += 10 * (self.r + 0.08 - dist)
        for cx, cy, pw, ph in self._placed:
            ox = (w + pw) / 2 + 0.06 - abs(center[0] - cx)
            oy = (h + ph) / 2 + 0.06 - abs(center[1] - cy)
            if ox > 0 and oy > 0:
                cost += 10 * ox * oy + 1
        return cost

    def _place_label(self, lbl, mid, normals, u, flexible=True):
        best, bc = None, 1e9
        ts = [0.0, -0.18, 0.18, -0.32, 0.32] if flexible else [0.0, -0.15, 0.15]
        for i, nrm in enumerate(normals):
            # prefer labels above / left for the first normal
            pref = 0.0
            if flexible and nrm[1] < -1e-6:
                pref = 0.05
            for t in ts:
                gap = 0.1 + 0.5 * self._extent(lbl, nrm)
                c = mid + u * t * 1.0 + nrm * gap
                cost = self._overlap(c, lbl.width, lbl.height) + pref + abs(t) * 0.3 + i * 0.02
                if cost < bc:
                    best, bc = c, cost
        lbl.move_to(best)
        self._remember(lbl)

    # ------------------------------------------------------------ queries
    def node(self, s: str) -> StateNode:
        return self.nodes[s]

    def edge(self, src: str, dst: str) -> Edge:
        return self.edges[(src, dst)]

    def edges_touching(self, states: Iterable[str]) -> list[Edge]:
        st = set(states)
        return [e for (a, b), e in self.edges.items() if a in st and b in st]

    # ------------------------------------------------------------ incremental build helpers
    def hide_all(self):
        """Make everything invisible so a scene can build it piece by piece with the animations below."""
        for m in self.get_family():
            m.set_fill(opacity=0, family=False)
            m.set_stroke(opacity=0, family=False)
        return self

    def build_states(self, states: Iterable[str], lag: float = 0.15, start_arrow: bool = True) -> AnimationGroup:
        anims = []
        for s in states:
            n = self.nodes[s]
            self._reveal(n)
            parts = [Create(n.circle)]
            if n.inner is not None:
                parts.append(Create(n.inner))
            parts.append(Write(n.label))
            anims.append(AnimationGroup(*parts))
            if start_arrow and s in self.start_arrows:
                self._reveal(self.start_arrows[s])
                anims.append(Create(self.start_arrows[s]))
        return LaggedStart(*anims, lag_ratio=lag)

    def build_edges(self, pairs: Iterable[tuple[str, str]], lag: float = 0.2) -> AnimationGroup:
        anims = []
        for p in pairs:
            e = self.edges[tuple(p)]
            self._reveal(e)
            anims.append(AnimationGroup(Create(e.path), Write(e.label), lag_ratio=0.5))
        return LaggedStart(*anims, lag_ratio=lag)

    def build_edges_from(self, states: Iterable[str]) -> AnimationGroup:
        st = list(states)
        return self.build_edges([k for k in self.edges if k[0] in st])

    def build_groups(self, groups: list[dict]) -> list[AnimationGroup]:
        """groups = [{"states": [...]} | {"edges": [[a,b],...]} | {"edges_from": [...]}] -> list of animations."""
        out = []
        for g in groups:
            if "states" in g:
                out.append(self.build_states(g["states"]))
            if "edges" in g:
                out.append(self.build_edges([tuple(x) for x in g["edges"]]))
            if "edges_from" in g:
                out.append(self.build_edges_from(g["edges_from"]))
        return out

    # ------------------------------------------------------------ highlighting
    def highlight_states(self, states: Iterable[str], on: bool = True, fill: bool = True) -> AnimationGroup:
        anims = []
        for s in states:
            n = self.nodes[s]
            col = P.ACCENT if on else P.INK
            parts = [n.circle.animate.set_stroke(col, S.STROKE).set_fill(P.ACCENT_SOFT if (on and fill) else P.STATE_FILL, 1)]
            if n.inner is not None:
                parts.append(n.inner.animate.set_stroke(col))
            parts.append(n.label.animate.set_color(col))
            anims.append(AnimationGroup(*parts))
        return AnimationGroup(*anims)

    def highlight_edges(self, pairs: Iterable[tuple[str, str]], on: bool = True) -> AnimationGroup:
        anims = []
        col = P.ACCENT if on else P.INK
        for p in pairs:
            e = self.edges[tuple(p)]
            anims.append(AnimationGroup(e.path.animate.set_color(col), e.label.animate.set_color(col)))
        return AnimationGroup(*anims)

    def reset_highlight(self) -> AnimationGroup:
        return AnimationGroup(
            self.highlight_states(self.nodes.keys(), on=False), self.highlight_edges(self.edges.keys(), on=False)
        )


# ------------------------------------------------------------ NFA semantics from the spec (for traces)
def _eps_targets(spec, s):
    out = []
    for sym, t in (spec.get("delta", {}).get(s) or {}).items():
        if sym in S.EPS_NAMES:
            out += [t] if isinstance(t, str) else list(t)
    return out


def eps_closure(spec: dict, states: Iterable[str]) -> list[str]:
    seen = list(dict.fromkeys(states))
    stack = list(seen)
    while stack:
        s = stack.pop()
        for t in _eps_targets(spec, s):
            if t not in seen:
                seen.append(t)
                stack.append(t)
    order = spec["states"]
    return sorted(seen, key=order.index)


def nfa_step(spec: dict, states: Iterable[str], sym: str) -> tuple[list[str], list[tuple[str, str]]]:
    """Returns (next active set after ε-closure, edges used by the symbol move)."""
    nxt, used = [], []
    for s in states:
        t = (spec.get("delta", {}).get(s) or {}).get(sym, [])
        t = [t] if isinstance(t, str) else t
        for x in t:
            used.append((s, x))
            if x not in nxt:
                nxt.append(x)
    return eps_closure(spec, nxt), used


def nfa_run(spec: dict, word: str | list[str]) -> list[tuple[list[str], list[tuple[str, str]]]]:
    """[(active set, edges used to get there)] for each prefix (index 0 = before reading anything)."""
    cur = eps_closure(spec, [spec["start"]])
    out = [(cur, [])]
    for ch in word:
        cur, used = nfa_step(spec, cur, ch)
        out.append((cur, used))
    return out
