extends RefCounted
class_name LevelData

# Ten short missions. Each task is a deterministic number-line movement.
# `delta` is the movement; `answer` is the destination (start + delta).
const TASKS_PER_LEVEL := 5
const LEVELS := [
	{"name":"Planéta PLUS", "topic":"Kladné čísla", "story":"RX-7 opravuje solárne panely. Každý správny krok ho posunie doprava.", "objective":"Precvič si pohyb doprava po kladných číslach.", "tasks":[[0,2],[1,3],[2,4],[3,2],[4,3]]},
	{"name":"Planéta MÍNUS", "topic":"Záporné čísla", "story":"Na ľadovej planéte sa robot musí pohybovať doľava k zamrznutému vysielaču.", "objective":"Precvič si odčítanie a pohyb doľava.", "tasks":[[5,-2],[3,-4],[1,-3],[0,-2],[-2,-3]]},
	{"name":"Planéta NULA", "topic":"Prechod cez nulu", "story":"Most cez nulový kráter sa aktivuje iba vtedy, keď správne prejdeš cez nulu.", "objective":"Prechádzaj medzi zápornými a kladnými číslami.", "tasks":[[-3,5],[2,-4],[-2,4],[3,-6],[-4,7]]},
	{"name":"Planéta ZRKADLO", "topic":"Absolútna hodnota", "story":"Zrkadlový kryštál ukazuje vzdialenosť čísla od nuly.", "objective":"Nájdi absolútnu hodnotu a prejdi na jej pozíciu.", "tasks":[[-5,10],[-3,6],[4,-0],[-7,14],[2,-4]], "absolute":true},
	{"name":"Planéta ROVNICE", "topic":"Sčítanie a odčítanie", "story":"Energetické články sa nabijú po vyriešení zmiešaných príkladov.", "objective":"Vyrieš sčítanie a odčítanie celých čísel.", "tasks":[[-2,5],[4,-7],[-5,3],[1,-6],[-3,8]]},
	{"name":"Planéta POROVNANIE", "topic":"Porovnávanie čísel", "story":"Navigačný systém potrebuje správne určiť cieľ na číselnej osi.", "objective":"Vypočítaj výsledok a skontroluj jeho polohu na osi.", "tasks":[[6,-3],[-6,4],[2,-5],[-4,6],[5,-8]]},
	{"name":"Planéta DESATINNÁ", "topic":"Desatinné čísla", "story":"RX-7 kalibruje presné meracie zariadenie. Tentoraz pracuje s polovicami jednotiek.", "objective":"Rozpoznaj znamienko a veľkosť zmeny; výsledok sa zaokrúhli na polovicu.", "tasks":[[-2,1],[1,-2],[-3,2],[2,1],[-1,-2]], "scale":0.5},
	{"name":"Planéta DVOJKROK", "topic":"Výrazy s viacerými krokmi", "story":"Dve brány strážia cestu ku kryštálu. Vyrieš oba pohyby v správnom poradí.", "objective":"Spoj dva kroky do jedného výsledku.", "tasks":[[1,4],[-2,5],[4,-6],[-5,7],[3,-5]], "two_step":true},
	{"name":"Planéta PREKÁŽKY", "topic":"Zmiešané opakovanie", "story":"Meteority blokujú trasu. Každá správna odpoveď bezpečne navedie robota ďalej.", "objective":"Zopakuj kladné, záporné čísla aj prechod cez nulu.", "tasks":[[-6,4],[5,-9],[-3,8],[7,-5],[-2,-6]], "hazards":true},
	{"name":"BOSS: Pevnosť", "topic":"Záverečná matematická výzva", "story":"Boss stráži centrálny kryštál. Použi všetko, čo si sa naučil na predchádzajúcich planétach.", "objective":"Dokonči päť náročnejších výpočtov a obnov energiu základne.", "tasks":[[-7,9],[6,-10],[-4,8],[8,-12],[-6,11]], "boss":true}
]

static func get_level(index: int) -> Dictionary:
	return LEVELS[clampi(index, 0, LEVELS.size() - 1)]

static func get_task(level_index: int, task_index: int) -> Dictionary:
	var level: Dictionary = get_level(level_index)
	var pair: Array = level.tasks[task_index % level.tasks.size()]
	var start_value: float = float(pair[0])
	var delta_value: float = float(pair[1])
	if level.has("scale"):
		start_value *= float(level.scale)
		# Alternate half-step values while retaining a readable number line.
		delta_value *= float(level.scale)
	var answer: float = start_value + delta_value
	var expression := _format_number(start_value) + (" + " if delta_value >= 0 else " − ") + _format_number(absf(delta_value))
	if level.get("absolute", false):
		var original: float = start_value
		answer = absf(original)
		delta_value = answer - original
		expression = "|" + _format_number(original) + "|"
	elif level.get("two_step", false):
		var second: float = -2.0 if task_index % 2 == 0 else 3.0
		answer += second
		expression += (" + " if second >= 0 else " − ") + _format_number(absf(second))
		# Keep the single displayed movement equal to the combined route.
		delta_value = answer - start_value
	return {"start":start_value, "delta":delta_value, "answer":answer, "expression":expression, "display_start":_format_number(start_value), "display_answer":_format_number(answer)}

static func _format_number(value: float) -> String:
	if is_equal_approx(value, roundf(value)):
		return str(int(roundf(value)))
	return str(snappedf(value, 0.5)).replace(".", ",")
