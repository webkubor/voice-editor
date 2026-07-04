# Cover Image Log

## 2026-04-14

- Purpose: redesign the repository hero cover for `Voice Editor`
- Final file: `assets/cover.jpg`
- Selected source: `assets/generated/cover-2026-04-14/candidate-1.jpg`
- Previous cover backup: `assets/generated/cover-2026-04-14/cover-before-2026-04-14.jpg`
- Generator: MiniMax image generation
- Access path:
  - attempted with `mmx image generate`
  - fell back to the official MiniMax image API because the local `mmx` CLI image route returned `HTTP 404`
- Model: `image-01`
- Aspect ratio: `16:9`
- Candidate count: `3`
- Visual direction:
  - dark, cold, open-source product banner
  - snow crystal waveform
  - cyan glow
  - no text, no people, GitHub README friendly
- Prompt:

```text
Cinematic open-source Chinese TTS workstation cover banner, winter snow and cold mist, luminous cyan audio waveform made of snow crystals, subtle studio hardware silhouette, elegant dark slate background, premium product-art direction, clean composition for GitHub README hero image, no text, no letters, no watermark, no people, high detail
```

- Output candidates:
  - `assets/generated/cover-2026-04-14/candidate-1.jpg`
  - `assets/generated/cover-2026-04-14/candidate-2.jpg`
  - `assets/generated/cover-2026-04-14/candidate-3.jpg`

- Selection note:
  - candidate 1 was chosen because it reads best as a repository header and keeps the strongest “audio waveform in snow” metaphor without distracting shapes.
