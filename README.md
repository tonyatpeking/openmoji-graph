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

### devtools

- remember to disable devtools from Cargo.toml in production releases


### Connection Rules

- group - subgroup
- base - variations (skin tones, sexes, group: flags, subgroups: keycap)
- sanitation "flag: ", "keycap: ", "family: ", "couple with heart: ", "kiss: ", "men holding hands: dark skin tone", "woman and man holding hands: medium skin tone, dark skin tone", "person taking bath: medium-light skin tone"
- "person in lotus position" -> "woman in lotus position" -> "woman in lotus position: light skin tone"

### lazy SVG loading

- SVGs are loaded lazily to reduce initial load time
- When node is clicked, start loading SVG, onLoad callback will then add node and links to graph


### Bugs

- Clicking does not work reliably when objects are moving
- Clicking uses object mesh for collision, making some objects hard to click (using png sprite might help with this)
- Page refresh causes memory leak
- Certain emoji have wrong draw order?
- Islands can be created when there are loops (could be a feature)
- Removing nodes causes abrupt screen shift (to center the nodes?) Adding nodes does not cause this

### Todo

- New nodes should be created near the expanded node
- Gamify by creating objectives
    - Start with a random node, find a path to the target node
- Allow for extended expansion over the top 10 connections
- Allow for node popup to show node info
- Allow for link popup to show link info
    - Why was this link made?
- Graph becomes too cluttered with many nodes
    - Allow for node grouping?
    - Make nodes 'pop' when they hit the border?


## Attributions

All emojis designed by [OpenMoji](https://openmoji.org/) – the open-source emoji and icon project. License: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/#)

Emoji frequency data from [https://home.unicode.org/emoji/emoji-frequency/](https://home.unicode.org/emoji/emoji-frequency/)
