<div align="center">

# LocalVideo

[Resource downloads and setup](docs/RESOURCES.md) · [Model disk footprints](docs/MODEL_STORAGE.md) · [Exact model files](configs/models.json)

The measured five-file Wan profile occupies **23.43 GiB** before environments, hot copies and outputs. Disk storage is different from VRAM. Keep the source clone and set `LOCALVIDEO_HOME` when installing agent skills separately.

**Turn AI short-film making from a lucky draw into a local pipeline you can re-run.**

[中文](README.md) · [Install](docs/INSTALL.md) · [Workflow](docs/WORKFLOW.md) · [Dialogue](docs/DIALOGUE.md) · [Models](docs/MODELS.md) · [Performance](docs/PERFORMANCE.md) · [Troubleshooting](docs/TROUBLESHOOTING.md) · [Reproducibility](docs/REPRODUCIBILITY.md) · [Privacy](docs/PRIVACY.md) · [Third-party notices](THIRD_PARTY_NOTICES.md)

</div>

A reusable video + multi-character dialogue production flow for local AI short-film and short-drama developers, with agent skills, ComfyUI orchestration, FFmpeg assembly, and performance / QC records. The repository holds source code, skills, JSON templates and docs.

## Why

Generating one clip is easy. The hard part is knowing what broke, and daring to re-run. LocalVideo separates the pipeline into named stages, each with its own artifacts and logs. A retry redoes only the bad shots, not the whole cut. Instead of scheduling inference at a fixed five-minutes-per-clip, it times cold start, sampling, decoding and editing separately, so you can see where the time goes. A single-GPU queue keeps execution ordered, local and reversible: every file lives in your working directory.

## What you get

Input → spoken-style scene script → structured storyboard → character / scene consistency → sentence-split CosyVoice2 → reviewed and locked audio track → 5–10 second Wan2.2-S2V shots → independent QC → FFmpeg edit / subtitles / mix → archive.

The locked audio track is the point: fix and review the voice first, then let picture align to it, rather than chasing dialogue behind frames.

No private photos, no cloned voices, no novel text, no finished films, no model weights, no keys.

## Route status

| Route | Status | Notes |
| --- | --- | --- |
| Wan2.2-S2V | Primary path | 5–10 s shots, per-shot QC |
| FreeVideo / H3 second pass / guide | Experimental | Runs, not settled |
| SVD | Limited, optional | Silent I2V, light motion only |
| LTX native AV | Runs, not passing | Historical false-subtitle / closed-mouth issues remain |
| ContentV official API | Limited | T2V only, no reference image / audio conditioning |
| Blender / Cycles / Eevee | Script-controlled route | Driven by scripts, not a generative model |
| LivePortrait / MuseTalk / LatentSync | Optional local animation / lip-sync | No guarantee of identity consistency or natural silent viewing |
| Music tools | Optional | Outside the main-line criteria |

The table records current state, not a promise that everything is production-ready.

## Three-step CPU smoke run

```bash
python -m pip install -e .
localvideo doctor
localvideo demo --work /absolute/new-demo
```

The CPU demo contains only a deterministic test card and test audio. It verifies environment, files, subtitles and assembly. It does **not** represent AI generation quality or natural dialogue.

## Going to real AI

Real generation needs a separate GPU environment prepared per `docs/INSTALL.md`, model weights downloaded under their own licenses, and your own lawful reference images and speech.

## Agent skills

- `skills/local-ai-video-production`
- `skills/wan22-s2v-local-production`
- `skills/scene-dialogue`

Copy them into your own Codex skills directory. Anything involving dialogue should use `scene-dialogue`.

## Measured boundaries

Historically tested on an RTX 5060 Ti 16GB with 32GB RAM. Wan scaled FP8 + 4-step LCM/LightX2V at 16fps, 832x480 was a specific historical combination; identical timings are not guaranteed on other hardware. Safe mode and optimized mode are recorded separately. The CPU weight-reuse hook is an experimental, version-bound component and must be re-validated whenever the model version changes.

## Privacy and contributing

Your assets, your machine, your files. MIT covers this repository's own code only; upstream models and tools follow their respective licenses — see `THIRD_PARTY_NOTICES.md`.
