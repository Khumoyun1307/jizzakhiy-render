# Slide scenes (Remotion) — props schema

One generic composition, `Scene`, renders every slide type from a JSON props file.
Output is 1920×1080, 24 fps, H.264 yuv420p, no audio track.

```powershell
cd "C:\Education Content Creation\Video Lab\remotion"
npx remotion render src/index.ts Scene out.mp4 --props=path\to\scene.json --muted
# quick still to check layout (frame number at 24 fps):
npx remotion still src/index.ts Scene out.png --props=path\to\scene.json --frame=120
```

`durationInFrames` is computed by `calculateMetadata`: `round(durationSec × 24)`. If `durationSec` is omitted it is
derived from the last reveal time + 3 s (QuizCard: reason time + 4 s). For production always pass
`durationSec = clip duration + pause_seconds + 0.3`.

Brand tokens live in `src/brand/brand.ts` (sampled from past lessons; see the header comment there).

## Common fields

| field | type | notes |
|---|---|---|
| `component` | `"LessonSlide" \| "DefinitionCard" \| "BulletBuild" \| "MathTable" \| "QuizCard" \| "HomeworkCard" \| "RecapSlide"` | required |
| `lesson` | number | used in the default kicker and the footer "Theory of Computation · NN" |
| `theme` | `"teal"` (default) \| `"gold"` | teal = Lessons 14–36 look (white, Inter Bold titles, teal). gold = Lessons 37–41 look (off-white #F6F7FA, navy serif titles, gold accent, square bullets) |
| `course` | string | default "Theory of Computation" |
| `durationSec` | number | total length in seconds |
| `fadeInSec`, `fadeOutSec` | number | optional whole-scene fade (default 0; the editor normally crossfades) |
| `data` | object | component props (below) |

All times (`at`, `textAt`, `thinkAt`, …) are **seconds from the start of the scene**. Take them from the word
timings in `03_audio/timings.json`. Items without `at` are spread evenly over the scene.

### Rich text (every text field)

| markup | result |
|---|---|
| `$...$` | inline KaTeX math (Computer Modern / Latin Modern look) — `$\varepsilon$`, `$\emptyset$`, `$R_1 \cup R_2$`, `$\delta'(q_0, a)$` |
| `$$...$$` | display math on its own line (left-aligned) |
| `**x**` | accent emphasis (teal / gold semibold), like "NFA" on L31 slides |
| `__x__` | dark bold, like "equivalent" on L40 slides |
| `\$` | a literal dollar sign |

In JSON, backslashes are doubled: `"$\\varepsilon$"`. Never write ASCII stand-ins (eps, 0 for ∅, q0).

## Components

### LessonSlide — `examples/lesson_slide_title.json`, `lesson_slide_statement.json`, `lesson_slide_content.json`
`{ layout: "title" | "statement" | "content", kicker?, title?, text?, bullets?: string[], math?, source?, textAt? }`
- `title`: opening card (L31 0:02 style; gold theme = centred serif card).
- `statement`: one big sentence (overview / key idea / question) + short accent rule + `source`.
- `content`: kicker + title + rule + static bullets (prefix `"- "` for a sub-bullet) + optional display `math` (TeX, no `$`).

### BulletBuild — `examples/bullet_build.json`
`{ kicker?, title, bullets: [{ text, at?, level? }], math?, mathAt?, source?, focus? }`
Bullets fade/rise in at `at`. `level: 1` = sub-bullet. `focus: true` dims earlier bullets when the next appears.

### DefinitionCard — `examples/definition_card.json`
`{ kicker? ("Definition 1.52"), title, lead?, leadAt?, lines: [{ text, at?, level? }], plain?, source? }`
Card with accent left bar; `plain: true` drops the bullet markers.

### MathTable — `examples/math_table.json`
`{ kicker?, title, columns: string[], rows: string[][], rowAt?: number[], highlights?: [{ row, col?, at, until? }], colWidths?, size?, caption?, rowHeaders? }`
Rows appear at `rowAt[i]`. A highlight without `col` outlines the whole row; with `col` a single cell. Cells are rich text
(wrap math in `$…$`). Default cell size 38 px; keep ≤ 6 rows.

### QuizCard — `examples/quiz_card.json`
`{ kicker?, question, options?: string[], correct?, thinkAt?, countdown? (5), answerAt?, answer, reason?, reasonAt?, thinkLabel? }`
Timeline: question visible from 0 → at `thinkAt` "Pause and think" + countdown ring (5…1, then a pause icon) →
at `answerAt` (default `thinkAt + countdown`) the ring leaves, the correct option lights up and the answer card appears →
`reason` at `reasonAt` (default answerAt + 0.8). Set `thinkAt` to the end of the narrated question.

### HomeworkCard — `examples/homework_card.json`
`{ kicker?, title? ("Try it yourself"), problem: string[], promptAt?, prompt? ("Pause the video and try it"), solution?: [{ text, at, level? }], solutionTitle? }`
Problem card, then the pulsing pause badge at `promptAt`; when the first solution step's `at` arrives the badge leaves
and the steps build under "Solution". For long solutions use a separate BulletBuild / Manim scene.

### RecapSlide — `examples/recap_slide.json`
`{ kicker?, title, takeaways: [{ text, at? }], upNext?: { lesson, title }, upNextAt? }`
L31 "Summary" / L37–41 "Recap" end slide with optional "Up next" strip.

Gold-theme examples: `*_gold.json`. Test renders: `renders/kit_test/remotion/`.

## Rules (from the slide-builder spec)
Body text ≥ 40 px (the components default to 40), ≤ ~6 lines per slide, content inside the 160 px side margins.
After rendering, extract first/middle/last frames with ffmpeg and look at them.
