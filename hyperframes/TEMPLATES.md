# Intro / outro templates (HyperFrames)

Two self-contained projects, each parameterised by variables. 1920×1080, render at 24 fps, silent.

| Template | Folder | Length | Variables |
|---|---|---|---|
| Intro | `hyperframes/intro/` | 6 s (fade to black from 5.5 s) | `lesson`, `title`, `course`, `style` |
| Outro | `hyperframes/outro/` | 9 s (fade to black from 8.4 s) | `lesson`, `next_lesson`, `next_title`, `course`, `style` |

`style`:
- `brand` (default) — COURSE.md brand: thumbnail navy `#0A1837`, JA logo lockup (cropped from thumbnail 038),
  teal `#0ACDBA` "Lesson NN" pill, cream `#FBF4E5` Inter Bold title, layout of the published L37–41 intros
  (left-aligned at x = 150, short accent rule at the bottom). Outro: "Up next" + pill + title, subscribe card.
- `series` — a close replica of the published Lesson 37/39/41 intro and "Up next" panel: navy `#13203C`, 14 px gold
  `#C9A227` left bar, "JIZZAKHIY ACADEMY · THEORY OF COMPUTATION" header, gold "LESSON NN", white serif
  (Computer Modern) title. No logo (the published intros have none).

## Render

Run from `C:\Education Content Creation\Video Lab\hyperframes` (ffmpeg/ffprobe must be on PATH:
`$env:PATH="<ffmpeg folder>;$env:PATH"`):

```powershell
# intro
npx --yes hyperframes@0.9.59 render intro --fps 24 --quality delivery `
  --variables '{"lesson":"38","title":"Converting Regular Expressions to NFAs","style":"brand"}' `
  -o ..\episodes\<slug>\02_visuals\scenes\S01.mp4

# outro
npx --yes hyperframes@0.9.59 render outro --fps 24 --quality delivery `
  --variables '{"lesson":"38","next_lesson":"39","next_title":"Preparing a DFA for State Elimination","style":"brand"}' `
  -o ..\episodes\<slug>\02_visuals\scenes\S99.mp4
```

In PowerShell, quoting JSON for native commands is fragile: prefer `--variables-file vars.json`
(examples in `renders/kit_test/hyperframes/*_vars.json`). Add `--strict-variables` to fail on typos.

Check after edits: `cd intro; npx --yes hyperframes@0.9.59 check` (expected warnings: first_frame_empty on the outro,
audio_none). Then extract and look at frames.

## Notes
- The outro is 9 s of picture; if the narration over it is longer, shorten the voice line, or render with a longer
  `data-duration` (edit `outro/index.html`, root `data-duration` and the fade time). Intro stays ≤ 8 s.
- Long titles shrink automatically (> 44 chars → 92 px, > 64 → 80 px on the intro; > 48 → 64 px on the outro).
- GSAP loads from the jsDelivr CDN (as in the scaffold), so rendering needs network access.
- The root `index.html` is the untouched scaffold; the templates are the two sub-folders.

Test renders (Lesson 38 → 39): `renders/kit_test/hyperframes/intro_L38*.mp4`, `outro_L38*.mp4`.
