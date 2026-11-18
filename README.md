# jizzakhiy-render

Cloud render pipeline for **Jizzakhiy Academy** lesson videos (YouTube academic tutorials).
It renders each scene of a lesson in its own GitHub Actions job (up to 20 at a time), then assembles the master.

This repository holds render code only:

| Folder | What |
|---|---|
| `remotion/` | Slide scenes (one `Scene` composition driven by a props JSON, see `remotion/SCENES.md`) |
| `hyperframes/` | Intro / outro templates (`hyperframes/TEMPLATES.md`) |
| `manim/lib/` | Manim house style, state diagrams, trace highlighter |
| `assets/images/` | Brand logos |
| `tools/` | `assemble.py` (master edit), `av_check.py` (spec check), `cloud_render.ps1` (local helper), `cloud/` (CI scripts) |

Per-lesson inputs (scene list, scene code, slide props, narration clips and timings) are pushed to a branch
`ep/<episode-id>` by `tools/cloud_render.ps1`; the workflow renders from that branch.

## Run

From the lab on Windows:

```powershell
tools\cloud_render.ps1 -Episode toc-038-converting-regex-to-nfas                 # every scene
tools\cloud_render.ps1 -Episode toc-038-converting-regex-to-nfas -Scenes S02,S11 # some scenes
tools\cloud_render.ps1 -Episode toc-038-converting-regex-to-nfas -Assemble       # + final.mp4
```

Or by hand: `gh workflow run render.yml --ref ep/<id> -f scenes=S02,S11 -f assemble=false`.

Workflow `render.yml`: `plan` (matrix from `01_script/scenes.json`) → `render` (one scene per ubuntu job:
Manim + TeX Live, Remotion, or HyperFrames) → `assemble` (artifact `final-<episode>`: final.mp4, captions.srt,
chapters.txt, edit_log.md, av_check.txt). Scene artifacts are `scene-<id>`.
