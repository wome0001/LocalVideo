# LocalVideo contribution rules

- Read README and the route's documented limitations before changing behavior.
- Video dialogue always uses skills/scene-dialogue. Preserve approved audio bytes and cues.
- Research unfamiliar model APIs in official docs and pin versions before implementation.
- Use configurable paths; never assume a Windows username or drive letter.
- Never commit photos, voices, generated results, model weights, secrets, machine inventories or private project material. Tests create their own synthetic data outside the repo.
- Keep native inference, edited duration, interpolation and upscale claims separate. Record cold/warm cost, actual sampler execution and failures.
- Verify technical integrity, action/identity/lip sync, naturalness and cross-shot continuity separately; automated checks do not approve subjective quality.
- Require an independent read-only reviewer for public releases and high-impact changes. Do not relax failed acceptance conditions.
- Prefer deterministic scripts. If using CodeBuddy CLI, explicitly pass --port 0, constrain scope and verify its actual output.
- No destructive cleanup by default. Keep recoverable evidence and never delete system paging files.
