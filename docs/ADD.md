# ADD — Architecture / Application Design Document

## 1. Architecture summary

The project uses a small, data-driven Godot architecture. A single main scene hosts the application UI and game state. Level content is separated from presentation and gameplay logic in a dedicated data script.

```text
project.godot
    └── scenes/Main.tscn
          └── Control (Main)
                └── scripts/Game.gd
                      ├── LevelData.gd (level and task definitions)
                      ├── ConfigFile (local persistence)
                      └── AudioStreamPlayer (generated feedback tones)
```

## 2. Main modules

### 2.1 Main scene — `scenes/Main.tscn`

- Root node: `Control` named `Main`.
- Loads `scripts/Game.gd`.
- Fills the viewport and receives mouse/touch input.
- The UI is drawn in `_draw()` rather than assembled from many editor-created nodes. This keeps the prototype portable and makes the screen layout easy to inspect in one script.

### 2.2 Game controller — `scripts/Game.gd`

Responsibilities:

- maintain the active screen (`menu`, `levels`, `game`, `settings`, `help`, `complete`);
- maintain selected/current level, task index, score, lives, stars, and robot position;
- render panels, buttons, robot, number line, HUD, and feedback;
- register button rectangles and map mouse/touch coordinates to actions;
- map keyboard shortcuts (`1`–`4`, `Enter`, `Esc`) to the same actions;
- validate selected answers and apply rewards/penalties;
- handle level completion and unlock progression;
- generate short WAV tones at runtime;
- load and save progress/settings.

Important methods:

| Method | Responsibility |
|---|---|
| `_draw()` | Dispatches drawing for the active screen. |
| `_draw_game()` | Draws task, number line, robot, choices, and HUD. |
| `_handle_click()` | Finds the pressed button rectangle. |
| `_handle_action()` | Routes menu and gameplay actions. |
| `_answer()` | Checks answer and applies reward or penalty. |
| `_complete_level()` | Awards stars, stores completion, unlocks next planet. |
| `_load_progress()` / `_save_progress()` | Persist state using `ConfigFile`. |
| `_play_beep()` | Generates a short tone without an external audio asset. |

### 2.3 Level data — `scripts/LevelData.gd`

`LevelData` is the canonical source of level names, topics, story text, objectives, task pairs, and special rules. `get_level(index)` returns the level dictionary. `get_task(level_index, task_index)` transforms a starting value and movement delta into an expression, answer, and display strings.

The task pair is `[start, delta]`; the expected destination is normally `start + delta`. Special level flags:

- `absolute`: answer is the absolute value of the start value;
- `scale`: scales integer values to half-unit values for the decimal planet;
- `two_step`: appends a second movement and combines both movements;
- `hazards`: marks the mixed review planet in the content data;
- `boss`: adds a boss-level scoring bonus.

## 3. State model

| Variable | Meaning |
|---|---|
| `screen` | Current application screen. |
| `current_level` | Active planet index (0–9). |
| `task_index` | Active task index (0–4). |
| `robot_position` | Current displayed robot coordinate on the number line. |
| `lives` | Remaining energy hearts (0–3 during a task sequence). |
| `score` | Persistent total score. |
| `level_score` | Score earned in the current planet run. |
| `unlocked_level` | Highest planet index available to select. |
| `completed_levels` | Array of completed planet indices. |
| `best_scores` | Dictionary mapping planet index to best score. |

## 4. Screen flow

```text
Main Menu ──Start──> Gameplay ──5 correct tasks──> Level Complete
    │                    │                              │
    ├──Level Select──────┘                              ├──Next Planet──> Gameplay
    ├──Settings                                          ├──Level Select
    └──Help                                              └──Main Menu
```

The gameplay pause/menu button currently returns to the main menu. State is saved after actions, so returning to the menu does not erase persistent progress. Start Game resumes the saved active task when one exists.

## 5. Data and persistence design

File: `user://roboticka_misia_save.cfg`  
Format: Godot `ConfigFile` (INI-like sections).

`[progress]`: `score`, `unlocked_level`, `completed_levels`, `best_scores`, `current_level`, `task_index`, `lives`, `robot_position`, `has_active_game`.  
`[settings]`: `sound_enabled`, `music_enabled`, `reduced_motion`, `high_contrast`.

The file is stored in the user's Godot application data directory, not in the exported game folder. If no save file exists, default values are used.

## 6. Input design

- Mouse: left click.
- Touch: screen touch press. Godot also emits an emulated mouse click for every touch (`emulate_mouse_from_touch` is enabled by default); `_input()` discards mouse events whose `device` is `InputEvent.DEVICE_ID_EMULATION`, otherwise one tap would run its action twice (e.g. a settings toggle would switch back, or an answer would also be submitted for the next task).
- Keyboard: `_handle_key()` reads `physical_keycode`. `1`–`4` / numpad `1`–`4` choose the answer in that slot (the slot order comes from `_get_choices()`, the same function used for drawing), `Enter` starts/continues the game in the menu or opens the next planet on the completion screen, and `Esc` returns to the main menu.
- Buttons are represented by `Rect2` hit areas registered during drawing.
- Input is handled centrally by `_input()`, `_handle_click()` and `_handle_key()`; all of them dispatch to `_handle_action()`.

## 7. Rendering design

The main `Control` draws the background, star field, panels, typography, number-line ticks, robot, buttons, progress bar, and feedback. Colors are constants in `Game.gd`. The robot is a procedural composition of lines, rectangles, and circles. The design targets a 1280×720 viewport with canvas-item stretch enabled.

## 8. Error handling and edge cases

- Level index is clamped to the valid range.
- Task access wraps only within a level's defined task array.
- Wrong answers cannot reduce score below zero after a failed run.
- Answer choices are made unique before drawing.
- Missing or invalid save files fall back to defaults.
- The reset action clears progress and saves the new default state.

## 9. Extensibility

For a larger production version, replace procedural drawing with reusable scenes (`Robot.tscn`, `PlanetCard.tscn`, `AnswerButton.tscn`, `NumberLine.tscn`), move task definitions to JSON or custom Resources, and add an explicit pause overlay and localized text resources. Keep `LevelData` as the authoritative level data model.


## Background audio subsystem (extension)

`Game.gd` creates a dedicated `AudioStreamPlayer` for background music, separate from the existing short synthesized UI sound effects. `_load_background_music()` loads `res://audio/background_music.ogg` when present and enables looping for OGG Vorbis streams. `_begin_music_session()` starts playback on game start or direct planet selection. The player remains alive across screen and level changes, so the track continues without restarting. `_update_music_state()` runs after every action and is the single place that decides the player state: stopped when music is disabled, paused (`stream_paused`) on the `menu` screen, and playing on every other screen once the session has started. Returning from the menu unpauses the stream, so playback continues from the same position. `music_enabled` is persisted in the settings section of the local save file.
