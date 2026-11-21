# Robotická číselná misia

A 2D educational mathematics game made with **Godot 4.7**. The player guides robot RX-7 along a horizontal number line, solves integer operations, repairs ten planets, unlocks later missions, and saves progress locally.

## Run the game

1. Install Godot 4.7 (or a compatible Godot 4.x release).
2. Extract this folder.
3. In Godot Project Manager choose **Import** and select `project.godot`.
4. Open the project and press **F6** (run current scene) or **F5** (run project).
5. The main scene is `scenes/Main.tscn`.

The project uses only built-in Godot nodes and GDScript; no external asset packs or plugins are required. The supplied concept image is kept in `assets/reference/` for design reference. The robot and interface in the playable build are drawn procedurally by GDScript, so the project remains self-contained.

## Game loop

1. Choose an unlocked planet.
2. Read the mission scenario and its learning objective.
3. Solve the displayed expression.
4. Select one of four answers. The robot's marker moves to the corresponding destination on the number line.
5. A wrong answer activates an obstacle and costs one energy heart. Three hearts are available per planet.
6. Complete five tasks to repair the planet, earn stars, and unlock the next one.
7. Progress, score, settings, completed planets, and the active task are saved in `user://roboticka_misia_save.cfg`. Choose Start Game again to continue the saved mission.

## Controls

Mouse click or touchscreen tap. There is no keyboard-only gameplay requirement.

## Project structure

```text
Roboticka_ciselna_misia/
├── project.godot
├── scenes/
│   └── Main.tscn
├── scripts/
│   ├── Game.gd
│   └── LevelData.gd
├── docs/
│   ├── GDD.md
│   ├── ADD.md
│   └── TDD.md
└── assets/reference/
    └── Robot_mission_reference.png
```

## Important implementation notes

- `Game.gd` owns the screen flow, drawing, click/touch handling, scoring, lives, feedback, audio beeps, settings, and save/load.
- `LevelData.gd` is the single source of truth for the ten planet scenarios and their five deterministic tasks.
- The number-line range is −10 to +10. All integer-level results remain in this range. The decimal planet uses half-unit values while keeping the same visual scale.
- Sound effects are short synthesized tones; no external audio files are needed.
- The settings include sound effects, reduced-motion preference, high-contrast text, and a progress reset.

## Current scope

This is a complete playable coursework prototype with ten levels and a repeatable core loop. The art is deliberately procedural rather than a pixel-perfect recreation of the reference image. The game currently uses a fixed 1280×720 design canvas and Slovak interface text. It is suitable for extension with imported sprite sheets, richer animations, a pause overlay, additional accessibility options, and teacher/assessment modes.


## Background music (new)

Background music starts when the player clicks **ZAČAŤ HRU** (or selects a planet directly), then continues looping through gameplay and screen/level transitions. It has a separate on/off control in **Nastavenia → Hudba na pozadí**; the existing sound-effects setting remains independent.

The project does not include the copyrighted “Lambada – Original Version (1989)” recording. To use a recording you are licensed to use, place an OGG Vorbis file at `audio/background_music.ogg`. See `audio/README_MUSIC.txt`. If the file is absent, the game still runs normally without background music.


### Background music troubleshooting

The audio player accepts `audio/background_music.ogg`, `audio/background_music.mp3`, or `audio/background_music.wav`. The filename and extension must match the real file format; renaming MP3 to OGG does not convert it. Wait for Godot to import the file and check the Output panel for a `Background music loaded` message.
