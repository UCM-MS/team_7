# TDD — Technical Design Document

## 1. Technical baseline

- Engine: Godot 4.7 (project feature version `4.7`).
- Language: GDScript.
- Rendering: GL Compatibility renderer.
- Display: 1280×720 base viewport; `canvas_items` stretch mode.
- Main scene: `res://scenes/Main.tscn`.
- Dependencies: Godot built-in APIs only; no plugins or downloaded libraries.

## 2. Runtime startup

1. Godot loads `project.godot`.
2. `run/main_scene` loads `scenes/Main.tscn`.
3. The root `Control` attaches `scripts/Game.gd`.
4. `_ready()` sets the minimum size, loads save data, creates an `AudioStreamPlayer`, enables processing, and requests the first draw.
5. `_draw()` draws the current screen and rebuilds the button hit-area list.

## 3. Coordinate and number-line calculation

The gameplay number line represents values from −10 to +10. The horizontal coordinate for a value `v` is:

`x = left + ((clamp(v, -10, 10) - (-10)) / 20) × axis_width`

The inverse mapping is not required because answers are selected from explicit choices. Tick marks are drawn at every integer; numeric labels are shown at every second integer to reduce clutter. Half-unit values are supported by the robot marker even though tick labels remain integers.

## 4. Task generation

`LevelData.get_task(level_index, task_index)` reads a `[start, delta]` pair. For a standard task:

`answer = start + delta`

For the absolute-value planet:

`answer = abs(start)`

For the two-step planet:

`answer = start + delta + second_step`

For the half-unit planet, start and delta are multiplied by `0.5` before the result is calculated. The method returns a dictionary with `start`, `delta`, `answer`, `expression`, `display_start`, and `display_answer`.

## 5. Answer generation and validation

`Game._get_choices(answer)` creates four unique candidate numbers: the correct answer and distractors based on ±1 and the sign-reversed result. Additional values are added if a duplicate occurs. The array is rotated by a deterministic level/task offset so that the correct answer is not always in the same button position.

`Game._answer(chosen)` compares the chosen value with the expected answer using `is_equal_approx()` to avoid floating-point equality problems. Correct answers award points and advance the task. Incorrect answers reduce lives and leave the same task active for another attempt.

## 6. Scoring and progression

- Standard correct answer: `100 + lives × 10` points.
- Boss correct answer: standard points + 50.
- Incorrect answer: one life removed.
- When lives reach zero: restart current planet, reset its run score, and subtract 50 from total score (minimum total score 0).
- Five completed tasks: calculate stars, record completion, update unlocked level, update best score, and switch to the completion screen.

## 7. Save system

Godot `ConfigFile` writes to `user://roboticka_misia_save.cfg`.

Save is triggered after actions and answer processing. On startup, `_load_progress()` reads known keys. Missing keys use defaults. An active planet/task, remaining lives, and robot position are restored; Start Game resumes that task. Settings are saved alongside progression. The reset button restores the initial progression state.

## 8. Audio generation

A short mono 16-bit PCM buffer is generated in GDScript at 22,050 Hz. The sample waveform is a sine tone with a linear fade envelope. A 660 Hz tone is used for general button feedback, 880 Hz for a correct answer, and 180 Hz for an incorrect answer. Playback is skipped when sound is disabled.

## 9. Settings implementation

- Sound effects: controls synthesized feedback tones.
- Reduced motion: shortens feedback display timing; the current prototype does not use continuous character animation.
- High contrast: renders text in white for stronger contrast.

## 10. Test plan

| ID | Test | Steps | Expected result |
|---|---|---|---|
| T01 | Project startup | Import project and press F5. | Main menu appears without missing-resource errors. |
| T02 | Start game | Select Start Game. | Planet 1, task 1, number line, expression, four choices appear. |
| T03 | Correct answer | Choose the correct result. | Correct feedback appears, score increases, next task begins. |
| T04 | Wrong answer | Choose a distractor. | One heart is removed; same task remains available. |
| T05 | Life reset | Give three wrong answers on one task. | Planet restarts and total score is reduced by 50, not below zero. |
| T06 | Planet completion | Answer five tasks correctly. | Completion screen, stars, and next-planet unlock appear. |
| T07 | Locked planet | Open level select before unlocking it. | Locked card cannot be selected. |
| T08 | Save persistence | Complete a planet, close and reopen the game. | Score, completion, and unlocked planet remain. |
| T09 | Settings persistence | Toggle sound/contrast/motion and reopen. | Settings retain their values. |
| T10 | Reset save | Use reset progress in Settings. | Unlock state returns to planet 1 and completion records clear. |
| T11 | Touch input | Tap a button on a touch device. | The same action is triggered as a mouse click. |
| T12 | Half-unit task | Play planet 7. | Decimal values are displayed and accepted. |
| T13 | Absolute value | Play planet 4. | Expression uses absolute-value bars and target is non-negative. |
| T14 | Boss level | Unlock and complete planet 10. | Boss scoring bonus and completion behavior work. |

## 11. Known limitations and next technical steps

- The UI is drawn in one script, so controls are not individually exposed to Godot's accessibility tree.
- The current prototype does not include keyboard navigation or remappable controls.
- The reduced-motion option is a preference hook but there is little animation to reduce yet.
- High contrast currently changes text color; a full high-contrast theme should also change panels and borders.
- The pause/menu control returns to the main menu instead of opening a pause overlay.
- The decimal planet uses half-unit values, not arbitrary tenths/hundredths.
- Runtime validation in the Godot editor is still required on the target computer; this environment does not have the Godot executable installed.


## Background music implementation and tests (extension)

- Asset path: `res://audio/background_music.ogg` (OGG Vorbis). The copyrighted Lambada recording is not bundled; the project owner must supply an appropriately licensed audio file.
- Runtime node: a dedicated `AudioStreamPlayer` created by `Game.gd`; it does not replace the UI sound-effect player.
- Looping: OGG stream looping is enabled when the resource is loaded.
- Start condition: Start Game or direct level selection. Playback continues through menu/settings/level/complete screen transitions until disabled or the application exits.
- Persistence: `music_enabled` is saved and loaded separately from `sound_enabled`.

### Audio test cases
1. With a valid OGG file present, click Start Game and confirm music starts.
2. Complete a task and move to another planet; confirm music does not restart.
3. Open settings while playing; confirm music continues.
4. Toggle background music off; confirm only music stops and UI beeps remain controlled by the sound-effects setting.
5. Toggle music on during an active session; confirm music resumes.
6. Remove the OGG file; confirm the game still launches without an audio-loading error.
