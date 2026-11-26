# GDD — Game Design Document

## 1. Project overview

**Title:** Robotická číselná misia (Robotic Number Mission)  
**Genre:** 2D educational puzzle / mathematics game  
**Engine:** Godot 4.7  
**Target audience:** Grade 2 of lower secondary school (approximately ages 13–14)  
**Subject:** Mathematics — integers, signed operations, absolute value, and movement on a number line  
**Platform:** Desktop first; mouse and touchscreen input are supported  
**Session length:** Approximately 10–20 minutes for a short play session

## 2. High concept

RX-7 is a small repair robot travelling through a galaxy whose energy network has failed. Each planet represents a mathematics topic. The player solves an expression and chooses its result. A correct answer moves the robot to the matching point on a number line, repairs the planet, awards points, and unlocks the next mission. Incorrect answers trigger a simple obstacle penalty and consume one of three energy hearts.

## 3. Problem and learning purpose

Learners can perform integer calculations mechanically but may struggle to connect positive and negative values with direction, distance from zero, and position. The game makes the number line the central play space: positive movement is to the right, negative movement is to the left, and crossing zero is visible.

## 4. Learning outcomes

By completing the game, a learner should be able to:

- locate positive, negative, and zero values on a number line;
- interpret addition as movement to the right or left;
- calculate integer addition and subtraction;
- understand crossing zero;
- interpret absolute value as distance from zero;
- combine two consecutive operations;
- check a calculated result against its position on the number line.

## 5. Core gameplay loop

**Select planet → read scenario → inspect expression and starting position → calculate → select answer → robot moves / obstacle penalty → repeat five tasks → planet completion → unlock next planet.**

## 6. Game rules and balance

- Each planet contains five deterministic tasks.
- Each planet starts with three energy hearts.
- Correct answer: +100 points, plus a small remaining-energy bonus; the boss planet grants an additional 50 points per task.
- Incorrect answer: −1 heart. The robot is visually displaced one unit away from the goal; the player can retry the same task.
- At zero hearts, the current planet restarts and 50 total points are deducted (score cannot become negative).
- A completed planet is recorded and the next planet is unlocked.
- Star rating: three stars with three hearts remaining, two stars with two hearts, one star with one heart.
- Best score per planet is retained.

## 7. World and level scenarios

| # | Planet / scenario | Learning focus | Scenario objective |
|---|---|---|---|
| 1 | Planéta PLUS | Positive integers | Restore solar panels by moving right on the number line. |
| 2 | Planéta MÍNUS | Negative integers | Navigate left across an icy planet. |
| 3 | Planéta NULA | Crossing zero | Cross the zero crater in both directions. |
| 4 | Planéta ZRKADLO | Absolute value | Move to the non-negative distance represented by absolute value. |
| 5 | Planéta ROVNICE | Addition and subtraction | Recharge energy cells with mixed integer calculations. |
| 6 | Planéta POROVNANIE | Position and comparison | Calculate destinations and interpret their relative positions. |
| 7 | Planéta DESATINNÁ | Half-unit values | Calibrate a measuring device using half-unit increments. |
| 8 | Planéta DVOJKROK | Multi-step expressions | Combine two sequential movements into one destination. |
| 9 | Planéta PREKÁŽKY | Mixed review | Review signed operations while navigating a meteor field. |
| 10 | BOSS: Pevnosť | Final mixed challenge | Complete a final set of more demanding integer movements. |

Each planet has five fixed tasks. Exact starting values and movement deltas are defined in `scripts/LevelData.gd` so that GDD level descriptions and implemented data can be checked against one source.

## 8. Interface and UX

- Main menu: start game, level selection, settings, and instructions.
- Level selection: ten cards show topic, lock state, completion status, and the best score achieved on the planet.
- Gameplay: planet story, objective, number line, current expression, four answer buttons, hearts, score, and task progress.
- Completion screen: stars, level score, next planet, level selection, and main menu.
- Settings: sound effects, reduced-motion preference, high-contrast text, and reset progress.
- Input: mouse click, touchscreen tap, and keyboard shortcuts (`1`–`4` answer, `Enter` start/next planet, `Esc` menu).

## 9. Visual direction

Use a deep-space navy background, cyan outlines, blue panels, bright green correct states, yellow navigation markers, and red obstacle feedback. RX-7 is a friendly white-and-cyan robot. The uploaded reference image informs the palette, planet progression, HUD, and robot theme. The prototype uses procedural vector-like drawing to avoid external dependencies.

## 10. Audio direction

Short synthesized tones provide click/correct/error feedback. The sound toggle disables these tones. There is no background music in this version.

## 11. Persistence and replayability

The game saves total score, unlocked planet index, completed planet indices, best planet scores, current planet, current task, remaining lives, robot position, and settings to Godot's `user://` directory. Selecting Start Game resumes an active mission. The reset option clears progress. Tasks are deterministic, allowing a teacher or learner to repeat a planet and compare performance.

## 12. Success criteria

The game is successful when a learner can start a mission, understand the direction of movement, solve all five tasks, receive feedback, complete the planet, return to the menu, close and reopen the game, and find the saved unlock state intact.

## 13. Scope boundaries

Included: ten planets, five tasks per planet, integer/half-unit arithmetic, number-line visualization, answer selection, score, lives, stars, unlocking, local saving, settings, help, and synthesized feedback tones.

Not included in this build: online accounts, cloud saves, multiplayer, teacher analytics, procedural level generation, voice-over, external music, and a full illustrated sprite animation system.
