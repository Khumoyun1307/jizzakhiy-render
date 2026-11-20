<#
.SYNOPSIS
  Render a lesson's scenes on GitHub Actions (repo Khumoyun1307/jizzakhiy-render) and download the results.

.EXAMPLE
  tools\cloud_render.ps1 -Episode toc-038-converting-regex-to-nfas
  tools\cloud_render.ps1 -Episode toc-038-converting-regex-to-nfas -Scenes S02,S11
  tools\cloud_render.ps1 -Episode toc-038-converting-regex-to-nfas -Assemble -OutDir renders\cloud_test

  -Scenes     scene ids to render (default: every scene in 01_script/scenes.json)
  -Assemble   also build final.mp4 / captions.srt / chapters.txt / edit_log.md in the cloud
              (with -Scenes, the other scenes are taken from the local 02_visuals/scenes/*.mp4)
  -QaPrep     only make 04_edit/transcript_words.json + 04_edit/frames/ for the existing 04_edit/final.mp4
              (uploads final.mp4 + edit_log.md; the assemble step already does this for new masters)
  -OutDir     download into <OutDir>\scenes and <OutDir>\04_edit instead of the episode folder
  -PublishCode  also update the repo's main branch with the lab's current render code
  -CodeOnly   with -PublishCode: update main and stop (no episode push, no run)
  -DryRun     build the temp clone, list what would be pushed, push nothing
  -NoWait     trigger the run and return (download later with: gh run download <id> -R <repo>)
  -KeepCloud  keep the run's artifacts and the ep/<episode> branch (by default both are deleted after a successful download)

Pushes ONLY render code + the episode's render inputs (scenes.json, scene code, slide props, HyperFrames copy,
03_audio clips/timings/words/blocks) to branch ep/<episode>. Uses the gh login (no tokens in files).
#>
param(
  [Parameter(Mandatory = $true)][string]$Episode,
  [string[]]$Scenes = @(),
  [switch]$Assemble,
  [switch]$QaPrep,
  [string]$OutDir = "",
  [string]$Repo = "Khumoyun1307/jizzakhiy-render",
  [switch]$PublishCode,
  [switch]$NoWait,
  [switch]$DryRun,
  [switch]$CodeOnly,
  [switch]$KeepCloud
)
$ErrorActionPreference = "Stop"
# Owner decision 2026-11-17: never upload a finished video. Assemble in the cloud (-Assemble) instead; that job also makes the QA transcript and frames.
if ($QaPrep) { throw "-QaPrep is disabled: it uploads a finished video. Re-assemble with -Assemble; that also produces transcript_words.json and frames/." }
$Lab = Split-Path -Parent $PSScriptRoot
$Ep = Join-Path $Lab "episodes\$Episode"
if (-not (Test-Path "$Ep\01_script\scenes.json")) { throw "No episode at $Ep" }
$Scenes = @($Scenes | ForEach-Object { $_ -split "[,\s]+" } | Where-Object { $_ } | ForEach-Object { $_.ToUpper() })
$Csv = $Scenes -join ","

function Run([string]$exe, [string[]]$argv, [int]$tries = 4, [string]$cleanDir = "") {
  # native stderr (git/gh progress) is not an error; retry through transient network failures
  $ErrorActionPreference = "Continue"
  for ($k = 1; $k -le $tries; $k++) {
    if ($cleanDir -and (Test-Path $cleanDir)) { Remove-Item -Recurse -Force $cleanDir }
    $out = & $exe @argv 2>&1 | ForEach-Object { "$_" }
    if ($LASTEXITCODE -eq 0) { return $out }
    if ($k -lt $tries) { Write-Host "retry ${k}: $exe $($argv[0..1] -join ' ') ($($out | Select-Object -Last 1))"; Start-Sleep -Seconds (5 * $k) }
  }
  throw "$exe $($argv -join ' ') failed ($LASTEXITCODE): $($out -join "`n")"
}
function Mirror([string]$src, [string]$dst, [string[]]$xd = @(), [string[]]$xf = @()) {
  $a = @($src, $dst, "/MIR", "/NFL", "/NDL", "/NJH", "/NJS", "/NP", "/R:1", "/W:1")
  if ($xd.Count) { $a += "/XD"; $a += $xd }
  if ($xf.Count) { $a += "/XF"; $a += $xf }
  & robocopy @a | Out-Null
  if ($LASTEXITCODE -ge 8) { throw "robocopy $src failed ($LASTEXITCODE)" }
  $global:LASTEXITCODE = 0
}
function CopyFile([string]$src, [string]$dst) {
  New-Item -ItemType Directory -Force (Split-Path -Parent $dst) | Out-Null
  Copy-Item -LiteralPath $src -Destination $dst -Force
}

# ---------------------------------------------------------------- 1. temp clone of the render repo
$tmp = Join-Path $env:TEMP ("jz-render-" + [guid]::NewGuid().ToString("N").Substring(0, 8))
Write-Host "Cloning $Repo -> $tmp"
Run gh @("repo", "clone", $Repo, $tmp, "--", "--depth", "1", "--quiet") -cleanDir $tmp | Out-Null
Push-Location $tmp
try {
  # push with the gh login only (empty helper line resets helpers from the global config)
  Add-Content -Path "$tmp\.git\config" -Value "[credential]`n`thelper =`n`thelper = !gh auth git-credential"
  Run git @("config", "core.autocrlf", "input")   # repo stores LF (bash scripts run on Linux)
  $uid = Run gh @("api", "user", "--jq", ".id"); $login = Run gh @("api", "user", "--jq", ".login")
  Run git @("config", "user.name", $login)
  Run git @("config", "user.email", "$uid+$login@users.noreply.github.com")

  # ---------------------------------------------------------------- 2. render code (render code ONLY)
  Mirror "$Lab\remotion" "$tmp\remotion" @("node_modules", "out", "build", ".git", ".cache", ".remotion") @("*.log", ".env*")
  Mirror "$Lab\hyperframes" "$tmp\hyperframes" @("node_modules", ".hyperframes", "renders") @("AGENTS.md", "CLAUDE.md", "*.log", "*.mp4", ".env*")
  Mirror "$Lab\manim\lib" "$tmp\manim\lib" @("__pycache__") @("*.pyc")
  Mirror "$Lab\tools\cloud" "$tmp\tools\cloud" @("__pycache__") @("*.log")
  New-Item -ItemType Directory -Force "$tmp\assets\images" | Out-Null
  Get-ChildItem "$Lab\assets\images\ja_logo*.png" | ForEach-Object { Copy-Item $_.FullName "$tmp\assets\images\" -Force }
  foreach ($f in "assemble.py", "av_check.py", "qa_prep.py", "transcribe.py", "cloud_render.ps1") { CopyFile "$Lab\tools\$f" "$tmp\tools\$f" }
  CopyFile "$Lab\tools\cloud\render.yml" "$tmp\.github\workflows\render.yml"
  CopyFile "$Lab\tools\cloud\README.md" "$tmp\README.md"
  CopyFile "$Lab\tools\cloud\gitignore" "$tmp\.gitignore"
  # no local machine paths in docs
  $tm = "$tmp\hyperframes\TEMPLATES.md"
  if (Test-Path $tm) {
    $t = [IO.File]::ReadAllText($tm) -replace 'C:\\Users\\[^\\"]+\\AppData\\Local\\Microsoft\\WinGet\\Links', '<ffmpeg folder>'
    [IO.File]::WriteAllText($tm, $t)
  }

  function Assert-Clean {
    $bad = Get-ChildItem -Recurse -File -Path $tmp | Where-Object {
      $_.FullName -notmatch '\\\.git\\' -and $_.Extension -notin ".wav", ".png", ".ttf", ".woff2", ".mp4", ".jpg"
    } | Select-String -SimpleMatch -List -Pattern @($env:USERNAME + "\", "Introduction to Theory of Computation", "00_brief\") |
      Select-Object -ExpandProperty Path -Unique
    $leak = Get-ChildItem -Recurse -Force -Path $tmp | Where-Object {
      $_.FullName -notmatch '\\\.git\\' -and ($_.Name -in ".env", ".venv", "00_brief", "node_modules", "05_qa", "06_publish" -or $_.FullName -match 'Theory of Computation')
    }
    if ($bad -or $leak) { throw "Refusing to push, private content found:`n$($bad -join "`n")`n$($leak.FullName -join "`n")" }
  }
  Assert-Clean

  if ($PublishCode -and -not $DryRun) {
    Run git @("add", "-A")
    git diff --cached --quiet
    if ($LASTEXITCODE -ne 0) {
      Run git @("commit", "-q", "-m", "Update render code from the lab")
      Run git @("push", "-q", "origin", "HEAD:main")
      Write-Host "main updated"
    }
    if ($CodeOnly) { return }
  }

  # ---------------------------------------------------------------- 3. episode inputs -> branch ep/<id>
  Run git @("checkout", "-q", "-B", "ep/$Episode")
  $dst = "$tmp\episodes\$Episode"
  if (Test-Path $dst) { Remove-Item -Recurse -Force $dst }
  CopyFile "$Ep\01_script\scenes.json" "$dst\01_script\scenes.json"
  if (Test-Path "$Ep\01_script\chapters.json") { CopyFile "$Ep\01_script\chapters.json" "$dst\01_script\chapters.json" }
  Get-ChildItem "$Ep\02_visuals\manim\*.py" -ErrorAction SilentlyContinue | ForEach-Object { CopyFile $_.FullName "$dst\02_visuals\manim\$($_.Name)" }
  Get-ChildItem "$Ep\02_visuals\slides\*" -Include *.json, *.py -ErrorAction SilentlyContinue | ForEach-Object { CopyFile $_.FullName "$dst\02_visuals\slides\$($_.Name)" }
  if (Test-Path "$Ep\02_visuals\hyperframes") {
    Mirror "$Ep\02_visuals\hyperframes" "$dst\02_visuals\hyperframes" @("node_modules", ".hyperframes", "renders") @("AGENTS.md", "CLAUDE.md", "*.log", "*.mp4", ".env*")
  }
  foreach ($f in "blocks.json", "scene_timings.json", "timings.json", "caption_fixes.json") {
    if (Test-Path "$Ep\03_audio\$f") { CopyFile "$Ep\03_audio\$f" "$dst\03_audio\$f" }
  }
  Get-ChildItem "$Ep\03_audio\words\*.json" | ForEach-Object { CopyFile $_.FullName "$dst\03_audio\words\$($_.Name)" }
  Get-ChildItem "$Ep\03_audio\clips\*.wav" | ForEach-Object { CopyFile $_.FullName "$dst\03_audio\clips\$($_.Name)" }
  if ($Assemble -and $Scenes.Count) {
    # scenes not rendered in this run come from the local renders
    $all = (Get-Content -Raw -Encoding UTF8 "$Ep\01_script\scenes.json" | ConvertFrom-Json).scenes | ForEach-Object { $_.id }
    foreach ($s in $all) {
      if ($Scenes -notcontains $s) {
        $p = "$Ep\02_visuals\scenes\$s.mp4"
        if (-not (Test-Path $p)) { throw "-Assemble needs $p (or add $s to -Scenes)" }
        CopyFile $p "$dst\02_visuals\scenes\$s.mp4"
      }
    }
  }
  if ($QaPrep) {
    foreach ($f in "final.mp4", "edit_log.md") {
      if (-not (Test-Path "$Ep\04_edit\$f")) { throw "-QaPrep needs $Ep\04_edit\$f" }
      CopyFile "$Ep\04_edit\$f" "$dst\04_edit\$f"
    }
  }
  Assert-Clean
  if ($DryRun) {
    Get-ChildItem -Recurse -File $tmp | Where-Object { $_.FullName -notmatch '\\\.git\\' } |
      ForEach-Object { "{0,10} {1}" -f $_.Length, $_.FullName.Substring($tmp.Length + 1) }
    Write-Host "DryRun: nothing pushed. Temp clone kept at $tmp"
    return
  }
  Run git @("add", "-A")
  if ($QaPrep) { Run git @("add", "-f", "episodes/$Episode/04_edit") }
  git diff --cached --quiet
  if ($LASTEXITCODE -ne 0) { Run git @("commit", "-q", "-m", "Render inputs for $Episode") }
  Run git @("push", "-q", "-f", "origin", "HEAD:refs/heads/ep/$Episode")
}
finally {
  Pop-Location
  if (-not $DryRun) { Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue }
}

# ---------------------------------------------------------------- 4. trigger, wait
$since = (Get-Date).ToUniversalTime().AddSeconds(-5)
$asm = if ($Assemble) { "true" } else { "false" }
Run gh @("workflow", "run", "render.yml", "-R", $Repo, "--ref", "ep/$Episode", "-f", "episode=$Episode", "-f", "scenes=$Csv", "-f", "assemble=$asm", "-f", "qa_prep_only=$(if ($QaPrep) { 'true' } else { 'false' })")
$run = $null
for ($i = 0; $i -lt 30 -and -not $run; $i++) {
  Start-Sleep -Seconds 3
  $ErrorActionPreference = "Continue"   # retry through transient network errors
  $list = (gh run list -R $Repo --workflow render.yml --branch "ep/$Episode" --event workflow_dispatch --limit 5 --json databaseId,createdAt,url 2>$null | ConvertFrom-Json)
  $ErrorActionPreference = "Stop"
  $run = $list | Where-Object { ([datetime]$_.createdAt).ToUniversalTime() -ge $since } | Select-Object -First 1
}
if (-not $run) { throw "Could not find the workflow run" }
Write-Host "Run: $($run.url)"
if ($NoWait) { return }
$ErrorActionPreference = "Continue"
do {
  gh run watch $run.databaseId -R $Repo --interval 30 2>&1 | Out-Null
  $st = (gh run view $run.databaseId -R $Repo --json status,conclusion 2>$null | ConvertFrom-Json)
} while (-not $st -or $st.status -ne "completed")
$ok = ($st.conclusion -eq "success")

# ---------------------------------------------------------------- 5. timing summary (real numbers from the API)
$jobs = ((Run gh @("run", "view", "$($run.databaseId)", "-R", $Repo, "--json", "jobs")) -join "`n" | ConvertFrom-Json).jobs
$rj = @($jobs | Where-Object { $_.name -match '^S\d' -and $_.startedAt -and $_.completedAt })
$peak = 0
foreach ($j in $rj) {
  $t = [datetime]$j.startedAt
  $n = @($rj | Where-Object { [datetime]$_.startedAt -le $t -and [datetime]$_.completedAt -gt $t }).Count
  if ($n -gt $peak) { $peak = $n }
}
$jobs | ForEach-Object {
  $sec = if ($_.startedAt -and $_.completedAt) { [int]([datetime]$_.completedAt - [datetime]$_.startedAt).TotalSeconds } else { "-" }
  "{0,-28} {1,-9} {2,5} s" -f $_.name, $_.conclusion, $sec
} | Write-Host
Write-Host "Peak concurrent render jobs: $peak"

# ---------------------------------------------------------------- 6. download
$sceneDir = if ($OutDir) { Join-Path $OutDir "scenes" } else { "$Ep\02_visuals\scenes" }
$editDir = if ($OutDir) { Join-Path $OutDir "04_edit" } else { "$Ep\04_edit" }
$dl = Join-Path $env:TEMP ("jz-dl-" + [guid]::NewGuid().ToString("N").Substring(0, 8))
$ErrorActionPreference = "Stop"
Run gh @("run", "download", "$($run.databaseId)", "-R", $Repo, "-D", $dl) | Out-Null
Get-ChildItem $dl -Directory -Filter "scene-*" | ForEach-Object {
  New-Item -ItemType Directory -Force $sceneDir | Out-Null
  Copy-Item "$($_.FullName)\*.mp4" $sceneDir -Force
  Write-Host "scene  -> $sceneDir\$($_.Name.Substring(6)).mp4"
}
Get-ChildItem $dl -Directory | Where-Object { $_.Name -like "final-*" -or $_.Name -like "qa-*" } | ForEach-Object {
  New-Item -ItemType Directory -Force $editDir | Out-Null
  $framesDir = Join-Path $editDir "frames"
  if (Test-Path $framesDir) { Remove-Item -Recurse -Force $framesDir }
  if (Test-Path "$editDirrames") { Remove-Item -Recurse -Force "$editDirrames" }
  Copy-Item "$($_.FullName)\*" $editDir -Recurse -Force
  Write-Host "final  -> $editDir"
}
Remove-Item -Recurse -Force $dl -ErrorAction SilentlyContinue

# ---------------------------------------------------------------- 7. cleanup: nothing lesson-specific stays in the public repo
# Deleting the run removes its artifacts (scene/final videos) and logs; deleting the branch removes the pushed clips and code.
# A failed run is kept so it can be debugged; rerun with -KeepCloud to keep a successful one too.
if ($ok -and -not $KeepCloud) {
  $ErrorActionPreference = "Continue"
  gh run delete $run.databaseId -R $Repo 2>&1 | Out-Null
  gh api -X DELETE "repos/$Repo/git/refs/heads/ep/$Episode" 2>&1 | Out-Null
  Write-Host "cleanup: deleted run $($run.databaseId) (artifacts + logs) and branch ep/$Episode"
}
if (-not $ok) { throw "Workflow run failed: $($run.url)" }
