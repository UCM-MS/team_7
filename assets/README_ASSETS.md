# Asset pack – Robotická číselná misia (Tím č. 7)

Všetky assety v tomto priečinku sú **vlastné** (vektorové, kreslené kódom v `_source/generate_assets.py`).
Netreba žiadny externý balík a môžeme ich ďalej voľne upravovať. Štýl a farby vychádzajú
z `reference/Robot_mission_reference.png` a palety v ADD (kap. 2.2).

Náhľady: `reference/overview_*.png` (prehľad podľa kategórií) a `reference/mockup_*.png`
(ukážkové obrazovky poskladané z týchto assetov).

## Štruktúra

```text
assets/
├── backgrounds/        pozadia 1280×720 (základňa + 10 planét) + parallax vrstva hviezd
├── sprites/
│   ├── robot/          RX-7: sprite sheety (128×128 na snímku), samostatné snímky, portrét 512 px, robot_frames.tres
│   ├── obstacles/      prekážky 128×128 (plus, mínus, L ×4 rotácie, bariéra 128×64, meteorit)
│   ├── items/          kryštál energie, bonusový drahokam, hviezda, batéria, srdce (128×128)
│   └── planets/        10 planét na mapu úrovní (256×256) + zamknutá planéta + bodka cesty
├── ui/
│   ├── buttons/        tlačidlá 192×64 (normal/hover/pressed/disabled) + štvorcové 96×96 pre odpovede
│   ├── panels/         panely (9-slice), karta úrovne, bublina reči
│   ├── hud/            rám a výplne ukazovateľa energie, prázdne srdce/hviezda
│   ├── icons/          18 ikon 128×128, biele + tyrkysové (_cyan)
│   ├── numberline/     prvky číselnej osi (dielik osi, ryhy, značky, šípky, vlajka cieľa)
│   ├── logo/           logo_full.png (1200×400), logo_title_only.png
│   └── app_icon.png    ikona aplikácie 256×256
├── effects/            efekty: sprite sheety 6 snímok (768×128) + statické verzie, effects_frames.tres
├── reference/          referencia, mockupy, prehľady
└── _source/            generátor + SVG zdroje (.gdignore – Godot ich neimportuje)
```

## Robot RX-7 (`sprites/robot/`)

| Animácia | Súbor | Snímky | Odporúčaná rýchlosť | Slučka |
|---|---|---|---|---|
| idle | `robot_idle_sheet.png` | 4 | 5 FPS | áno |
| walk | `robot_walk_sheet.png` | 6 | 10 FPS | áno |
| jump | `robot_jump_sheet.png` | 4 | 8 FPS | nie |
| success | `robot_success_sheet.png` | 4 | 8 FPS | áno |
| hurt | `robot_hurt_sheet.png` | 3 | 8 FPS | nie |

- Snímka 128×128 px, chodidlá na y ≈ 121 → pre `AnimatedSprite2D` nastav `offset = Vector2(0, -57)`
  (alebo `centered = false` a `position.y -= 121`), aby robot stál na osi.
- Pri pohybe doľava stačí `flip_h = true`.
- `robot_frames.tres` = hotový `SpriteFrames` so všetkými animáciami (overené v Godot 4.5).
- `robot_portrait.png` (512 px, ukazuje prstom) – hlavné menu; `robot_idle_large.png` – výsledková obrazovka.

## UI – 9-slice okraje (`NinePatchRect` / `StyleBoxTexture`)

| Súbor | Veľkosť | Okraj (patch margin) |
|---|---|---|
| `ui/buttons/button_*.png` | 192×64 | 20 vľavo/vpravo/hore, 24 dole (tieň) |
| `ui/buttons/button_square_*.png` | 96×96 | 20 (dole 24) |
| `ui/panels/panel.png`, `panel_dark.png`, `panel_highlight.png` | 128×128 | 24 |
| `ui/panels/panel_header.png` | 256×128 | 24 (hore 44 – pás nadpisu) |
| `ui/panels/level_card*.png` | 256×96 | 18 |
| `ui/hud/bar_frame.png` | 256×32 | 14 |
| `ui/hud/bar_fill_*.png` | 64×24 | 12 |

Tlačidlá: `TextureButton` (normal/hover/pressed/disabled) alebo `Button` + `StyleBoxTexture` v téme.

## Efekty (`effects/`)

`fx_success`, `fx_error`, `fx_crystal`, `fx_stars`, `fx_portal` – 6 snímok 128×128, 14 FPS
(`effects_frames.tres`). Portál sa opakuje v slučke, ostatné sa prehrajú raz.

## Pozadia (`backgrounds/`)

| Súbor | Použitie |
|---|---|
| `bg_base_damaged.png` / `bg_base_repaired.png` | menu / základňa pred a po oprave (ADD 2.3) |
| `bg_level_01_plus.png` … `bg_level_10_boss.png` | pozadie konkrétnej planéty (poradie podľa `LevelData.gd`) |
| `layer_stars_parallax.png` | priehľadná vrstva hviezd pre `ParallaxBackground` |

Stredná a horná časť pozadí je zámerne pokojná, aby bola čitateľná číselná os a zadanie.

## Nastavenie importu v Godote

- Pixel-perfect nie je potrebné – grafika je hladká: nechaj filter **Linear** a zapni **Mipmaps** iba pri
  silnom zmenšovaní (napr. planéty na mape).
- Projekt má `stretch/mode = canvas_items` a 1280×720 → pozadia sa zobrazia 1:1.

## Úprava / pregenerovanie

```bash
python3 assets/_source/generate_assets.py
```

Vyžaduje Inkscape (na macOS sa nájde automaticky v `/Applications/Inkscape.app`, inak premenná `INKSCAPE`).
Farby sú v slovníku `PAL`, animácie robota v `ROBOT_ANIMS`, témy pozadí v `BG_THEMES`.
Po pregenerovaní Godot assety automaticky reimportuje.

## Fonty

ADD určuje **Rajdhani** (nadpisy, tlačidlá) a **Inter** (texty, príklady) – oba SIL OFL, stiahnuť z
Google Fonts do `assets/fonts/`. Logo a mockupy sú zatiaľ vyrenderované systémovým fontom
Avenir Next Heavy; po doplnení Rajdhani stačí v generátore zmeniť `font-family`.
