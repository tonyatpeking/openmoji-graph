# OpenMoji Graph

## Tech Stack
- Tauri + Vue 3 + Vite + TypeScript

## Dependencies

- rust
- tauri
- nodejs


## Commands

### Desktop
- `cargo tauri dev`
    - Run in dev mode
- `cargo tauri build`
    - Build app for current platform
    - Builds to `src-tauri/target/release/bundle`

### Web

- `npm run dev`
    - Run in dev mode
- `npm run build` 
    - Build webpage for production to `dist`
- `npm run preview`
    - Serve webpage from `dist` for preview



### Connection Rules

- group - subgroup
- base - variations (skin tones, sexes, group: flags, subgroups: keycap)
- sanitation "flag: ", "keycap: ", "family: ", "couple with heart: ", "kiss: ", "men holding hands: dark skin tone", "woman and man holding hands: medium skin tone, dark skin tone", "person taking bath: medium-light skin tone"
- "person in lotus position" -> "woman in lotus position" -> "woman in lotus position: light skin tone"

## Attributions

All emojis designed by [OpenMoji](https://openmoji.org/) – the open-source emoji and icon project. License: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/#)