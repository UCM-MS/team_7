extends Control

const LEVELS := LevelData.LEVELS
const SAVE_PATH := "user://roboticka_misia_save.cfg"
const BG := Color("071a32")
const PANEL := Color("0d2b4d")
const PANEL_2 := Color("12395f")
const CYAN := Color("35d9f4")
const BLUE := Color("1689df")
const GREEN := Color("21d68a")
const YELLOW := Color("ffd64a")
const RED := Color("ff5967")
const WHITE := Color("f3f8ff")
const MUTED := Color("a9c4df")

var screen := "menu"
var selected_level := 0
var current_level := 0
var task_index := 0
var robot_position := 0.0
var lives := 3
var score := 0
var level_score := 0
var unlocked_level := 0
var completed_levels: Array[int] = []
var best_scores: Dictionary = {}
var sound_enabled := true
var reduced_motion := false
var high_contrast := false
var has_active_game := false
var feedback := ""
var feedback_timer := 0.0
var buttons: Array[Dictionary] = []
var audio_player: AudioStreamPlayer
var music_player: AudioStreamPlayer
var music_enabled := true
var music_started := false
var flash_timer := 0.0
var stars := 0

func _ready() -> void:
	custom_minimum_size = Vector2(960, 540)
	_load_progress()
	audio_player = AudioStreamPlayer.new()
	add_child(audio_player)
	music_player = AudioStreamPlayer.new()
	music_player.bus = "Master"
	music_player.volume_db = -8.0
	add_child(music_player)
	music_player.finished.connect(_on_music_finished)
	_load_background_music()
	set_process(true)
	queue_redraw()

func _process(delta: float) -> void:
	if feedback_timer > 0.0:
		feedback_timer = maxf(0.0, feedback_timer - delta)
		if feedback_timer == 0.0:
			feedback = ""
	if flash_timer > 0.0:
		flash_timer = maxf(0.0, flash_timer - delta)
	queue_redraw()

func _draw() -> void:
	buttons.clear()
	var size := get_viewport_rect().size
	draw_rect(Rect2(Vector2.ZERO, size), BG)
	_draw_stars(size)
	match screen:
		"menu": _draw_menu(size)
		"levels": _draw_levels(size)
		"game": _draw_game(size)
		"settings": _draw_settings(size)
		"help": _draw_help(size)
		"complete": _draw_complete(size)
	_draw_footer(size)
	if feedback != "":
		_draw_feedback(size)

func _draw_stars(size: Vector2) -> void:
	for i in range(38):
		var x := fposmod(float(i * 173 + 31), maxf(size.x, 1.0))
		var y := fposmod(float(i * 97 + 19), maxf(size.y, 1.0))
		var r := 1.0 + float(i % 3) * 0.55
		draw_circle(Vector2(x, y), r, Color(0.45, 0.78, 1.0, 0.22 + float(i % 4) * 0.08))

func _draw_header(title: String, subtitle: String = "") -> void:
	var w := get_viewport_rect().size.x
	draw_rect(Rect2(18, 14, w - 36, 70), PANEL, true, 14)
	draw_rect(Rect2(18, 14, w - 36, 70), Color(CYAN, 0.7), false, 2, true)
	_draw_text(title, Vector2(38, 53), 28, WHITE, true)
	if subtitle != "": _draw_text(subtitle, Vector2(40, 73), 12, MUTED)

func _draw_menu(size: Vector2) -> void:
	_draw_header("ROBOTICKÁ ČÍSELNÁ MISIA", "MATEMATICKÁ VÝPRAVA PO ČÍSELNEJ OSI")
	_draw_robot(Vector2(size.x * 0.72, size.y * 0.48), 1.65)
	_draw_panel(Rect2(38, 112, size.x * 0.47, 360), "PRÍBEH MISIE")
	_draw_text("Robot RX-7 cestuje medzi planétami,", Vector2(62, 164), 18, WHITE)
	_draw_text("aby opravil energetickú sieť galaxie.", Vector2(62, 191), 18, WHITE)
	_draw_text("Každá planéta ukrýva matematickú úlohu.", Vector2(62, 218), 18, WHITE)
	_draw_text("Vypočítaj výsledok a presuň robota", Vector2(62, 245), 18, WHITE)
	_draw_text("na správne miesto na číselnej osi.", Vector2(62, 272), 18, WHITE)
	_draw_text("Správne odpovede obnovujú energiu.", Vector2(62, 315), 16, GREEN)
	_draw_text("Tri chyby a misia sa musí opakovať.", Vector2(62, 342), 16, YELLOW)
	var x := size.x * 0.57
	_add_button(Rect2(x, size.y * 0.27, size.x * 0.31, 54), "ZAČAŤ HRU", "start", GREEN)
	_add_button(Rect2(x, size.y * 0.27 + 68, size.x * 0.31, 48), "VÝBER ÚROVNÍ", "levels", BLUE)
	_add_button(Rect2(x, size.y * 0.27 + 128, size.x * 0.31, 48), "NASTAVENIA", "settings", PANEL_2)
	_add_button(Rect2(x, size.y * 0.27 + 188, size.x * 0.31, 48), "AKO HRAŤ", "help", PANEL_2)
	_draw_panel(Rect2(38, size.y - 112, size.x - 76, 66), "POSTUP GALAXIOU")
	_draw_text("Odomknuté planéty: %d / %d     Celkové skóre: %d" % [unlocked_level + 1, LEVELS.size(), score], Vector2(58, size.y - 70), 16, WHITE)

func _draw_levels(size: Vector2) -> void:
	_draw_header("VÝBER PLANÉT", "Vyber si odomknutú úroveň. Postup sa ukladá automaticky.")
	var cols := 2
	var gap := 14.0
	var card_w := (size.x - 80.0 - gap) / 2.0
	var card_h := 82.0
	for i in range(LEVELS.size()):
		var col := i % cols
		var row := i / cols
		var rect := Rect2(30 + col * (card_w + gap), 104 + row * (card_h + 12), card_w, card_h)
		var unlocked := i <= unlocked_level
		var color := PANEL_2 if unlocked else Color("172638")
		draw_rect(rect, color, true, 10)
		draw_rect(rect, Color(CYAN, 0.65) if unlocked else Color("526477"), false, 2, true)
		_draw_text("%02d  %s" % [i + 1, LEVELS[i].name], rect.position + Vector2(15, 27), 16, WHITE if unlocked else MUTED, true)
		_draw_text(LEVELS[i].topic, rect.position + Vector2(15, 52), 12, MUTED)
		if best_scores.has(str(i)):
			_draw_text("Najlepšie skóre: %d" % int(best_scores[str(i)]), rect.position + Vector2(card_w - 160, 52), 11, YELLOW)
		var status := "DOKONČENÉ ★" if completed_levels.has(i) else ("ODOMKNUTÉ" if unlocked else "ZAMKNUTÉ")
		_draw_text(status, rect.position + Vector2(card_w - 128, 27), 11, GREEN if completed_levels.has(i) else (YELLOW if unlocked else MUTED))
		if unlocked:
			buttons.append({"rect":rect, "action":"choose_level", "value":i})
	_add_button(Rect2(30, size.y - 74, 170, 44), "SPÄŤ DO MENU", "menu", PANEL_2)

func _draw_game(size: Vector2) -> void:
	var level: Dictionary = LevelData.get_level(current_level)
	var task: Dictionary = LevelData.get_task(current_level, task_index)
	_draw_header("%02d  %s" % [current_level + 1, level.name], level.topic + "  •  ÚLOHA %d / %d" % [task_index + 1, LevelData.TASKS_PER_LEVEL])
	_add_button(Rect2(size.x - 178, 27, 140, 38), "PAUZA / MENU", "pause", PANEL_2)
	_draw_panel(Rect2(28, 102, size.x - 56, 108), "PRÍBEH PLANÉTY")
	_draw_text(level.story, Vector2(50, 153), 15, WHITE)
	_draw_text(level.objective, Vector2(50, 180), 14, CYAN)
	_draw_panel(Rect2(28, 224, size.x - 56, 250), "NAVIGAČNÁ ČÍSELNÁ OS")
	var axis_left := 82.0
	var axis_right := size.x - 82.0
	var axis_y := 390.0
	var axis_w := axis_right - axis_left
	draw_line(Vector2(axis_left, axis_y), Vector2(axis_right, axis_y), WHITE, 3, true)
	var min_v := -10.0
	var max_v := 10.0
	for n in range(-10, 11):
		var x := axis_left + (float(n) - min_v) / (max_v - min_v) * axis_w
		draw_line(Vector2(x, axis_y - 9), Vector2(x, axis_y + 9), WHITE, 2)
		if n % 2 == 0: _draw_text(str(n), Vector2(x - 8, axis_y + 30), 12, MUTED)
	var start_x := axis_left + (clampf(float(task.start), min_v, max_v) - min_v) / (max_v - min_v) * axis_w
	var robot_x := axis_left + (clampf(robot_position, min_v, max_v) - min_v) / (max_v - min_v) * axis_w
	var goal_x := axis_left + (clampf(float(task.answer), min_v, max_v) - min_v) / (max_v - min_v) * axis_w
	draw_line(Vector2(start_x, axis_y - 30), Vector2(goal_x, axis_y - 30), YELLOW, 3, true)
	draw_circle(Vector2(start_x, axis_y), 9, BLUE)
	draw_circle(Vector2(goal_x, axis_y), 8, GREEN)
	_draw_robot(Vector2(robot_x, axis_y - 67), 0.58)
	_draw_text("RX-7", Vector2(robot_x - 18, axis_y - 105), 12, CYAN, true)
	_draw_text("ŠTART %s" % task.display_start, Vector2(start_x - 28, axis_y + 53), 10, MUTED)
	_draw_text("CIEĽ ?", Vector2(goal_x - 25, axis_y - 48), 12, YELLOW, true)
	_draw_panel(Rect2(28, 490, size.x - 56, 142), "VYRIEŠ PRÍKLAD A VYBER CIEĽ")
	_draw_text(task.expression + " = ?", Vector2(54, 538), 25, WHITE, true)
	_draw_text("RX-7: " + task.display_start + "  →  ?", Vector2(54, 568), 14, MUTED)
	var choices := _get_choices(float(task.answer))
	var button_w := minf(130.0, (size.x - 420.0) / 4.0)
	for i in range(choices.size()):
		var bx := size.x - 4 * button_w - 4 * 12 + i * (button_w + 12)
		_add_button(Rect2(bx, 522, button_w, 56), _format_number(float(choices[i])), "answer", BLUE, choices[i])
		_draw_text(str(i + 1), Vector2(bx + 7, 536), 10, MUTED)
	_draw_text("Klávesy 1–4: výber odpovede   •   Esc: menu", Vector2(size.x - 4 * button_w - 4 * 12, 600), 11, MUTED)
	_draw_hud(size)

func _draw_hud(size: Vector2) -> void:
	var right := size.x - 218
	_draw_panel(Rect2(right, 100, 190, 104), "STAV ROBOTA")
	_draw_text("Životy: " + "♥ ".repeat(lives) + "♡ ".repeat(3 - lives), Vector2(right + 15, 151), 17, RED, true)
	_draw_text("Skóre: %d" % score, Vector2(right + 15, 181), 14, YELLOW)
	var progress := float(task_index) / float(LevelData.TASKS_PER_LEVEL)
	draw_rect(Rect2(right + 15, 190, 155, 7), Color("294760"), true, 3)
	draw_rect(Rect2(right + 15, 190, 155 * progress, 7), GREEN, true, 3)

func _draw_settings(size: Vector2) -> void:
	_draw_header("NASTAVENIA", "Uprav si spôsob zobrazovania hry.")
	_draw_panel(Rect2(70, 120, size.x - 140, 390), "PREFERENCIE HRÁČA")
	_add_button(Rect2(110, 175, size.x - 220, 52), "Zvukové efekty: " + ("ZAPNUTÉ" if sound_enabled else "VYPNUTÉ"), "toggle_sound", GREEN if sound_enabled else PANEL_2)
	_add_button(Rect2(110, 245, size.x - 220, 52), "Obmedziť animácie: " + ("ÁNO" if reduced_motion else "NIE"), "toggle_motion", GREEN if reduced_motion else PANEL_2)
	_add_button(Rect2(110, 315, size.x - 220, 52), "Vysoký kontrast: " + ("ÁNO" if high_contrast else "NIE"), "toggle_contrast", GREEN if high_contrast else PANEL_2)
	_add_button(Rect2(110, 385, size.x - 220, 48), "Hudba na pozadí: " + ("ZAPNUTÁ" if music_enabled else "VYPNUTÁ"), "toggle_music", GREEN if music_enabled else PANEL_2)
	_add_button(Rect2(110, 447, size.x - 220, 44), "VYMAZAŤ ULOŽENÝ POSTUP", "reset_save", RED)
	_add_button(Rect2(30, size.y - 74, 170, 44), "SPÄŤ DO MENU", "menu", PANEL_2)

func _draw_help(size: Vector2) -> void:
	_draw_header("AKO HRAŤ", "Jednoduché pravidlá matematickej výpravy")
	_draw_panel(Rect2(45, 112, size.x - 90, size.y - 205), "PRAVIDLÁ MISIE")
	var lines := [
		"1. Na začiatku úlohy vidíš štartovaciu pozíciu robota a matematický príklad.",
		"2. Vypočítaj výsledok. Kladné číslo posúva robota doprava, záporné doľava.",
		"3. Vyber jednu zo štyroch odpovedí. Správna odpoveď posunie RX-7 na cieľ.",
		"4. Nesprávna odpoveď aktivuje prekážku a odoberie jeden život. Môžeš skúšať ďalej.",
		"5. Na dokončenie planéty vyrieš päť úloh. Po dokončení sa odomkne ďalšia planéta.",
		"6. Postup, skóre a odomknuté úrovne sa ukladajú automaticky do lokálneho súboru.",
		"Ovládanie: kliknutie myšou alebo dotyk na odpoveď či tlačidlo.",
		"Klávesnica: 1–4 vyberie odpoveď, Enter spustí hru / ďalšiu planétu, Esc vráti do menu."
	]
	for i in range(lines.size()): _draw_text(lines[i], Vector2(75, 170 + i * 42), 15, WHITE)
	_add_button(Rect2(30, size.y - 74, 170, 44), "SPÄŤ DO MENU", "menu", PANEL_2)

func _draw_complete(size: Vector2) -> void:
	_draw_header("PLANÉTA OPRAVENÁ!", "Výborne, RX-7 obnovil energetickú sieť.")
	_draw_robot(Vector2(size.x * 0.5, size.y * 0.38), 1.3)
	_draw_text("Získané hviezdy: " + "★".repeat(stars), Vector2(size.x * 0.5 - 110, size.y * 0.58), 28, YELLOW, true)
	_draw_text("Skóre tejto planéty: %d" % level_score, Vector2(size.x * 0.5 - 110, size.y * 0.64), 17, WHITE)
	if current_level < LEVELS.size() - 1:
		_add_button(Rect2(size.x * 0.5 - 125, size.y * 0.73, 250, 52), "ĎALŠIA PLANÉTA", "next_level", GREEN)
	_add_button(Rect2(30, size.y - 74, 170, 44), "VÝBER ÚROVNÍ", "levels", BLUE)
	_add_button(Rect2(size.x - 200, size.y - 74, 170, 44), "HLAVNÉ MENU", "menu", PANEL_2)

func _draw_footer(size: Vector2) -> void:
	_draw_text("ROBOTICKÁ ČÍSELNÁ MISIA  •  MATEMATIKA  •  2D", Vector2(22, size.y - 12), 10, MUTED)

func _draw_feedback(size: Vector2) -> void:
	var color := GREEN if feedback.begins_with("SPRÁVNE") else RED
	var rect := Rect2(size.x * 0.28, 90, size.x * 0.44, 42)
	draw_rect(rect, Color(color, 0.95), true, 8)
	_draw_text(feedback, Vector2(rect.position.x + 14, rect.position.y + 27), 15, BG, true)

func _draw_panel(rect: Rect2, title: String) -> void:
	draw_rect(rect, PANEL, true, 12)
	draw_rect(rect, Color(CYAN, 0.35), false, 2, true)
	_draw_text(title, rect.position + Vector2(16, 25), 12, CYAN, true)

func _draw_text(value: String, pos: Vector2, font_size: int, color: Color, bold: bool = false) -> void:
	var c := Color.WHITE if high_contrast else color
	draw_string(ThemeDB.fallback_font, pos, value, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size + (1 if bold else 0), c)

func _draw_robot(pos: Vector2, scale_factor: float) -> void:
	var s := scale_factor
	var body := Rect2(pos + Vector2(-23, -4) * s, Vector2(46, 45) * s)
	draw_line(pos + Vector2(-13, -34) * s, pos + Vector2(-20, -48) * s, CYAN, 2.5 * s)
	draw_line(pos + Vector2(13, -34) * s, pos + Vector2(20, -48) * s, CYAN, 2.5 * s)
	draw_circle(pos + Vector2(-20, -49) * s, 4 * s, YELLOW)
	draw_circle(pos + Vector2(20, -49) * s, 4 * s, YELLOW)
	draw_rect(body, Color("d8efff"), true, 10 * s)
	draw_rect(body, CYAN, false, 2 * s, true)
	draw_rect(Rect2(pos + Vector2(-19, 4) * s, Vector2(38, 22) * s), Color("08213d"), true, 8 * s)
	draw_circle(pos + Vector2(-9, 15) * s, 5 * s, CYAN)
	draw_circle(pos + Vector2(9, 15) * s, 5 * s, CYAN)
	draw_line(pos + Vector2(-15, 42) * s, pos + Vector2(-20, 53) * s, Color("d8efff"), 7 * s)
	draw_line(pos + Vector2(15, 42) * s, pos + Vector2(20, 53) * s, Color("d8efff"), 7 * s)

func _add_button(rect: Rect2, label: String, action: String, color: Color, value: Variant = null) -> void:
	draw_rect(rect, color, true, 9)
	draw_rect(rect, Color(CYAN, 0.65), false, 1.5, true)
	var font_size := 14
	var text_width := ThemeDB.fallback_font.get_string_size(label, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size).x
	_draw_text(label, Vector2(rect.position.x + (rect.size.x - text_width) / 2.0, rect.position.y + rect.size.y / 2.0 + 5), font_size, WHITE, true)
	buttons.append({"rect":rect, "action":action, "value":value})

func _get_choices(answer: float) -> Array[float]:
	var values: Array[float] = [answer, answer + 1.0, answer - 1.0, -answer]
	if is_equal_approx(answer, 0.0): values = [0.0, 1.0, -1.0, 2.0]
	var unique: Array[float] = []
	for v in values:
		if not unique.has(v): unique.append(v)
	var offset := 2
	while unique.size() < 4:
		var candidate := answer + float(offset)
		if not unique.has(candidate): unique.append(candidate)
		offset += 1
	# Stable order, but move the correct answer to a different slot per task.
	var shift := (task_index + current_level) % 4
	var ordered: Array[float] = []
	for i in range(4): ordered.append(unique[(i + shift) % 4])
	return ordered

func _format_number(value: float) -> String:
	if is_equal_approx(value, roundf(value)): return str(int(roundf(value)))
	return str(snappedf(value, 0.5)).replace(".", ",")

func _input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		# Godot emulates a mouse click from every touch by default
		# (input_devices/pointing/emulate_mouse_from_touch). The real touch is
		# handled below, so skip the emulated copy to avoid a double action.
		if event.device == InputEvent.DEVICE_ID_EMULATION:
			return
		_handle_click(event.position)
	elif event is InputEventScreenTouch and event.pressed:
		_handle_click(event.position)
	elif event is InputEventKey and event.pressed and not event.echo:
		_handle_key(event.physical_keycode)

# Keyboard shortcuts: 1–4 choose an answer, Enter confirms the main action
# of the screen, Esc returns to the main menu.
func _handle_key(keycode: Key) -> void:
	var answer_keys := [KEY_1, KEY_2, KEY_3, KEY_4]
	var numpad_keys := [KEY_KP_1, KEY_KP_2, KEY_KP_3, KEY_KP_4]
	var slot := answer_keys.find(keycode)
	if slot == -1: slot = numpad_keys.find(keycode)
	if slot != -1:
		if screen != "game": return
		var task: Dictionary = LevelData.get_task(current_level, task_index)
		var choices := _get_choices(float(task.answer))
		_play_beep(660.0)
		_handle_action("answer", choices[slot])
		get_viewport().set_input_as_handled()
		return
	match keycode:
		KEY_ESCAPE:
			if screen != "menu":
				_play_beep(660.0)
				_handle_action("menu")
		KEY_ENTER, KEY_KP_ENTER:
			if screen == "menu":
				_play_beep(660.0)
				_handle_action("start")
			elif screen == "complete" and current_level < LEVELS.size() - 1:
				_play_beep(660.0)
				_handle_action("next_level")
		_:
			return
	get_viewport().set_input_as_handled()

func _handle_click(pos: Vector2) -> void:
	for i in range(buttons.size() - 1, -1, -1):
		var b: Dictionary = buttons[i]
		if b.rect.has_point(pos):
			_play_beep(660.0)
			_handle_action(str(b.action), b.get("value"))
			return

func _handle_action(action: String, value: Variant = null) -> void:
	match action:
		"start": _continue_or_start()
		"levels": screen = "levels"
		"settings": screen = "settings"
		"help": screen = "help"
		"menu": screen = "menu"
		"pause": screen = "menu"
		"choose_level": _start_level(int(value))
		"answer": _answer(float(value))
		"next_level": _start_level(mini(current_level + 1, LEVELS.size() - 1))
		"toggle_sound": sound_enabled = not sound_enabled
		"toggle_motion": reduced_motion = not reduced_motion
		"toggle_contrast": high_contrast = not high_contrast
		"toggle_music": _toggle_music()
		"reset_save": _reset_progress()
	_update_music_state()
	_save_progress()
	queue_redraw()

func _continue_or_start() -> void:
	_begin_music_session()
	if has_active_game and current_level <= unlocked_level and task_index < LevelData.TASKS_PER_LEVEL:
		screen = "game"
	else:
		_start_level(unlocked_level)

func _start_level(index: int) -> void:
	_begin_music_session()
	has_active_game = true
	current_level = clampi(index, 0, LEVELS.size() - 1)
	task_index = 0
	lives = 3
	level_score = 0
	robot_position = float(LevelData.get_task(current_level, 0).start)
	feedback = ""
	screen = "game"

func _answer(chosen: float) -> void:
	if screen != "game": return
	var task: Dictionary = LevelData.get_task(current_level, task_index)
	if is_equal_approx(chosen, float(task.answer)):
		var delta := float(task.answer) - float(task.start)
		robot_position = float(task.answer)
		var points := 100 + (lives * 10)
		if current_level == 9: points += 50
		score += points
		level_score += points
		feedback = "SPRÁVNE! RX-7 sa posunul o %s." % _format_number(delta)
		feedback_timer = 1.0 if reduced_motion else 1.4
		_play_beep(880.0)
		task_index += 1
		if task_index >= LevelData.TASKS_PER_LEVEL:
			_complete_level()
		else:
			robot_position = float(LevelData.get_task(current_level, task_index).start)
	else:
		lives -= 1
		var push := -1.0 if float(task.answer) >= float(task.start) else 1.0
		robot_position = clampf(float(task.start) + push, -10.0, 10.0)
		feedback = "PREKÁŽKA! Skús to znova. Zostáva %d ♥" % lives
		feedback_timer = 1.2
		flash_timer = 0.25
		_play_beep(180.0)
		if lives <= 0:
			lives = 3
			score = maxi(0, score - 50)
			feedback = "ENERGIA SA MINULA. Úroveň začína odznova."
			feedback_timer = 1.8
			task_index = 0
			level_score = 0
			robot_position = float(LevelData.get_task(current_level, 0).start)
	_save_progress()
	queue_redraw()

func _complete_level() -> void:
	has_active_game = false
	stars = 3 if lives == 3 else (2 if lives == 2 else 1)
	if not completed_levels.has(current_level): completed_levels.append(current_level)
	unlocked_level = mini(maxi(unlocked_level, current_level + 1), LEVELS.size() - 1)
	best_scores[str(current_level)] = maxi(int(best_scores.get(str(current_level), 0)), level_score)
	screen = "complete"
	_save_progress()

func _reset_progress() -> void:
	unlocked_level = 0
	has_active_game = false
	current_level = 0
	task_index = 0
	lives = 3
	robot_position = 0.0
	completed_levels.clear()
	best_scores.clear()
	score = 0
	_save_progress()
	feedback = "POSTUP BOL VYNULOVANÝ."
	feedback_timer = 1.6

func _load_progress() -> void:
	var cfg := ConfigFile.new()
	if cfg.load(SAVE_PATH) != OK: return
	score = int(cfg.get_value("progress", "score", 0))
	level_score = int(cfg.get_value("progress", "level_score", 0))
	unlocked_level = clampi(int(cfg.get_value("progress", "unlocked_level", 0)), 0, LEVELS.size() - 1)
	var saved_completed: Array = cfg.get_value("progress", "completed_levels", [])
	completed_levels.clear()
	for entry in saved_completed:
		completed_levels.append(int(entry))
	best_scores = cfg.get_value("progress", "best_scores", {})
	current_level = clampi(int(cfg.get_value("progress", "current_level", 0)), 0, LEVELS.size() - 1)
	task_index = clampi(int(cfg.get_value("progress", "task_index", 0)), 0, LevelData.TASKS_PER_LEVEL - 1)
	lives = clampi(int(cfg.get_value("progress", "lives", 3)), 1, 3)
	robot_position = float(cfg.get_value("progress", "robot_position", LevelData.get_task(current_level, task_index).start))
	has_active_game = bool(cfg.get_value("progress", "has_active_game", false))
	sound_enabled = bool(cfg.get_value("settings", "sound_enabled", true))
	music_enabled = bool(cfg.get_value("settings", "music_enabled", true))
	reduced_motion = bool(cfg.get_value("settings", "reduced_motion", false))
	high_contrast = bool(cfg.get_value("settings", "high_contrast", false))

func _save_progress() -> void:
	var cfg := ConfigFile.new()
	cfg.set_value("progress", "score", score)
	cfg.set_value("progress", "level_score", level_score)
	cfg.set_value("progress", "unlocked_level", unlocked_level)
	cfg.set_value("progress", "completed_levels", completed_levels)
	cfg.set_value("progress", "best_scores", best_scores)
	cfg.set_value("progress", "current_level", current_level)
	cfg.set_value("progress", "task_index", task_index)
	cfg.set_value("progress", "lives", lives)
	cfg.set_value("progress", "robot_position", robot_position)
	cfg.set_value("progress", "has_active_game", has_active_game)
	cfg.set_value("settings", "sound_enabled", sound_enabled)
	cfg.set_value("settings", "music_enabled", music_enabled)
	cfg.set_value("settings", "reduced_motion", reduced_motion)
	cfg.set_value("settings", "high_contrast", high_contrast)
	cfg.save(SAVE_PATH)

# Background music is separate from short interface sound effects.
# Supported files: audio/background_music.ogg, .mp3 or .wav.
func _load_background_music() -> void:
	var candidates := [
		"res://audio/background_music.ogg",
		"res://audio/background_music.mp3",
		"res://audio/background_music.wav"
	]
	for music_path in candidates:
		if not ResourceLoader.exists(music_path):
			continue
		var loaded: Resource = load(music_path)
		if loaded == null or not (loaded is AudioStream):
			push_warning("Music file exists but Godot could not load it as audio: " + music_path)
			continue
		var stream := loaded as AudioStream
		if stream is AudioStreamOggVorbis:
			(stream as AudioStreamOggVorbis).loop = true
		elif stream is AudioStreamMP3:
			(stream as AudioStreamMP3).loop = true
		music_player.stream = stream
		print("Background music loaded: ", music_path)
		return
	push_warning("No background music found. Add background_music.ogg, background_music.mp3 or background_music.wav to res://audio/.")

func _on_music_finished() -> void:
	# Fallback looping for formats that do not expose a native loop setting.
	if music_enabled and music_started and screen != "menu" and music_player.stream != null and not music_player.playing:
		music_player.play()

func _begin_music_session() -> void:
	music_started = true

# Single place that decides what the music player does:
# - music disabled → stopped,
# - main menu → paused (resumes from the same spot when the player leaves the menu),
# - any other screen after the session started → playing.
func _update_music_state() -> void:
	if music_player == null or music_player.stream == null:
		return
	if not music_enabled:
		music_player.stream_paused = false
		if music_player.playing:
			music_player.stop()
		return
	if not music_started:
		return
	if screen == "menu":
		if music_player.playing:
			music_player.stream_paused = true
	elif music_player.stream_paused:
		music_player.stream_paused = false
	elif not music_player.playing:
		music_player.play()

func _toggle_music() -> void:
	music_enabled = not music_enabled
	_update_music_state()
	_save_progress()

func _play_beep(frequency: float) -> void:
	if not sound_enabled or audio_player == null: return
	var sample_rate := 22050
	var duration := 0.055
	var count := int(sample_rate * duration)
	var bytes := PackedByteArray()
	bytes.resize(count * 2)
	for i in range(count):
		var envelope := 1.0 - float(i) / float(count)
		var sample := int(sin(TAU * frequency * float(i) / float(sample_rate)) * 5000.0 * envelope)
		bytes.encode_s16(i * 2, sample)
	var wav := AudioStreamWAV.new()
	wav.format = AudioStreamWAV.FORMAT_16_BITS
	wav.mix_rate = sample_rate
	wav.stereo = false
	wav.data = bytes
	audio_player.stream = wav
	audio_player.play()
