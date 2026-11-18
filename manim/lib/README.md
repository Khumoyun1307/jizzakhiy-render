# Jizzakhiy Academy Manim kit (`manim/lib`)

```python
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # scene file lives in manim/
from lib import *        # manim + house style + StateDiagram + TraceHighlighter
```

Render (from the Video Lab root; MiKTeX/ffmpeg are added to PATH automatically by `jz_style`):

```powershell
.venv\Scripts\manim.exe -qh --fps 24 --media_dir renders/manim manim/demo_nfa.py DemoNFA
# output: renders/manim/videos/demo_nfa/1080p24/DemoNFA.mp4  (1920x1080, 24 fps, silent)
```

## `jz_style.py`
- White background, ink `#202124`, teal `#13736C` highlight, soft teal fill `#DDF0ED` (sampled from Lesson 31).
  `use_theme("gold")` switches to the Lessons 37–41 palette, sampled from the L40 final video: off-white bg `#F6F7FA`,
  navy ink `#14203C`, body `#4C5465`, gold accent `#C9A227` with pale-gold active fill `#F5EBC6`, rule `#D6DBE1`,
  white state fill (`P.STATE_FILL`, `P.CARD`).
  Colours are on `P` (`P.INK`, `P.ACCENT`, `P.ACCENT_SOFT`, `P.MUTED`, `P.RULE`, …).
- Text uses **Inter** (bundled in `lib/fonts`, registered automatically): `jz_text(s, size, weight)`, `jz_kicker("Lesson 38")`.
- Math uses LaTeX `MathTex` (Computer Modern = same look as the KaTeX slides). `sym_tex("eps") -> \varepsilon`,
  `state_tex("q0") -> q_{0}`, `state_tex("q_start") -> q_{\text{start}}`.
- Sizes: `STROKE = 5`, `STATE_R = 0.48` (≈ 65 px), matching the L40 diagrams.

## `SeriesChrome(title_tex, lesson, kicker=...)` (`chrome.py`)
Series slide frame for diagram scenes: letter-spaced kicker `THEORY OF COMPUTATION · LESSON 38`, Computer Modern title with
a gold underline under its first word, footer rule + "Jizzakhiy Academy" / "Theory of Computation · Lesson 38" (L40 layout,
compact header inside the top 180 px). `chrome.place_right(mob)` right-aligns a header expression on the title row.
`grid(x, y)` converts the script's 16×9 grid (origin top-left, y down, 120 px units) to Manim points; `px(x, y)` does 1080p pixels.

## `StateDiagram(spec)`
```python
spec = {
  "states": ["q0","q1","q2"], "start": "q0", "accept": ["q2"], "alphabet": ["a","b"],
  "delta":  {"q0": {"a": ["q1"], "eps": ["q2"]}, "q1": {"b": ["q0","q2"]}},
  "layout": {"q0": [-3,0], "q1": [0,1.5], "q2": [3,0]},         # Manim units, frame is ±7.1 × ±4
  # optional: "labels": {"q0": "q_0"}, "start_dir": "left"|"up"|[dx,dy], "bend": {"q0->q1": 0.5},
  #           "loop_dir": {"q1": "down"}, "dash_epsilon": True, "scale": 1.0,
  #           "starts": ["q0","q3"] (several start arrows, e.g. component machines), "start_dir": {"q0": [-1,1]},
  #           "start_len": 0.5, "bridge": {"q2->q0": 2.6} (smooth arc over/under everything, extreme y in Manim units),
  #           "via": {"q2->q0": [x,y]} (circular arc through a point), "via_label": {"q2->q0": "inside"}
}
d = StateDiagram(spec)
```
- Start arrow, double circle for accept states, self-loops (placed away from neighbours, or `loop_dir`),
  opposite pairs drawn as two arcs bending apart, several symbols on one pair merged as `a, b`,
  ε written `\varepsilon` (`"eps"`, `"ε"`, `""` all mean ε). Edge labels are placed on the side with least overlap.
- Parts: `d.nodes["q1"]` (`.circle`, `.inner`, `.label`), `d.edges[("q0","q1")]` (`.path`, `.label`), `d.start_arrow`,
  `d.start_arrows[s]`. `d.hide(states=, edges=, starts=)` hides parts for a later `build_*` / `d.reveal_start(s)`.
- Never animate (`.animate`) a hidden part together with its reveal: the target copy keeps opacity 0.
- Parallel renders sharing one `--media_dir` can crash on the Tex cache (WinError 32): compile new TeX in one process first.

### Building incrementally
```python
d.hide_all(); self.add(d)
self.play(d.build_states(["q0"]))                         # circle + label (+ start arrow)
self.play(d.build_edges([("q0","q1"), ("q0","q2")]))       # arrow then label
self.play(d.build_edges_from(["q1"]))                      # every edge leaving q1
for anim in d.build_groups([{"states": ["q1","q2"]}, {"edges_from": ["q0"]}]): self.play(anim)
```

### Highlighting
`d.highlight_states(["q1"])`, `d.highlight_states(["q1"], on=False)`, `d.highlight_edges([("q0","q1")])`,
`d.reset_highlight()` — all return animations for `self.play`.

## `TraceHighlighter(diagram, word, position=DOWN*3, sets=None, set_name="")`
Input tape with a teal read head, the current active-state set as `\{q_0, q_1\}`, and the active states filled teal.
Active sets are computed from the spec (`nfa_run`: symbol moves + ε-closure); pass `sets=[...]` to use the fact-checked
sets from `scenes.json` instead.
```python
tr = TraceHighlighter(d, "aba", position=DOWN*3.05)
self.play(tr.show())
for i in range(len(tr.word)):
    self.play(tr.flash_edges(i))   # edges used by symbol i turn teal
    self.play(tr.advance(i))       # head moves, set updates, states re-highlight
self.play(tr.finish())             # ACCEPT / REJECT badge from the spec's accept states
```
Helpers: `eps_closure(spec, states)`, `nfa_step(spec, states, sym)`, `nfa_run(spec, word)`.

## Not built yet
`SubsetTable`, `StackView`, `TuringTape`, `ParseTree`, `DerivationSteps`, `GNFARip` (listed in the animator spec) —
add them here when a lesson first needs them.

Demo: `manim/demo_nfa.py` (6-state ε-NFA build + trace of `aba`). Test render: `renders/kit_test/manim/DemoNFA.mp4`.
