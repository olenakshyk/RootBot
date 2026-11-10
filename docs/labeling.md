# Розмітка кадрів у CVAT

Кадри для розмітки лежать у `data/to_label/<назва>/` (кадри з відео: `scripts/extract_frames.sh data/raw_data data/frames 2`).
Класи: [`config/piece_classes.txt`](../config/piece_classes.txt), назви й номери як у датасетах команди (v6). Розмічаємо 6 із них. Усе в браузері, нічого встановлювати не треба.

## 1. Підготовка (один раз, 5 хв)

1. Зареєструйся на <https://app.cvat.ai> (безкоштовно).
2. **Projects → `+` → Create a new project.**
   - Name: `rootbot`
   - У проєкті відкрий **Labels → вкладку Raw**.
   - Встав цей JSON і натисни **Done**:

     ```json
     [
       {"name": "marquise_warrior", "type": "any", "attributes": []},
       {"name": "eyrie_warrior", "type": "any", "attributes": []},
       {"name": "alliance_warrior", "type": "any", "attributes": []},
       {"name": "vagabond", "type": "any", "attributes": []},
       {"name": "eyrie_building", "type": "any", "attributes": []},
       {"name": "alliance_building", "type": "any", "attributes": []},
       {"name": "alliance_token", "type": "any", "attributes": []},
       {"name": "marquise_score", "type": "any", "attributes": []},
       {"name": "eyrie_score", "type": "any", "attributes": []},
       {"name": "alliance_score", "type": "any", "attributes": []},
       {"name": "vagabond_score", "type": "any", "attributes": []},
       {"name": "die", "type": "any", "attributes": []}
     ]
     ```

   - **Не змінюй порядок міток.** Він має бути однаковим у всіх, бо від нього залежать номери класів під час експорту.
   - **Submit & Open**.
3. **Tasks → `+` → Create a new task.**
   - Name: як тека з кадрами, наприклад `human_compare_20`
   - Project: `rootbot`
   - Перетягни кадри з теки `data/to_label/<назва>`
   - **Submit & Open**, потім відкрий **Job #1**.

> ⚠️ **Обов'язково вибери Project: `rootbot`**, інакше в задачі не буде міток.

**Перевірка:** у відкритому Job перейди на вкладку **Labels** праворуч. Там має бути 12 міток (**Items: 12**).

## 2. Розмітка

Малюємо лише **прямокутники**: Claude у браузері робить їх точно, а контури потім будує SAM
([`colab/boxes_to_outlines.ipynb`](../colab/boxes_to_outlines.ipynb)). Відкрий Job і дай Claude у браузері цей запит:

```text
Label this CVAT job. Use ONLY the Rectangle tool, never polygons or AI tools.

Labels:
- marquise_warrior: orange wooden warrior
- eyrie_warrior: blue wooden warrior
- alliance_warrior: green wooden warrior
- eyrie_building: dark blue square tile with a white branch
- alliance_building: square tile with a green border and a white centre with a red
  (or other colour) symbol; often half hidden under green warriors
- alliance_token: light-green round token with a fist

Do NOT label: dice, cards, white item tiles, score-track markers, brown square
tiles, round brown tokens, white or other figures, anything off the board.

How to work:
1. Go through the board area by area. Zoom in on each area before drawing.
2. Draw one rectangle per piece that contains the whole visible piece with a
   small margin; never cut off any part. Pick the correct label BEFORE drawing.
3. In clusters, every piece gets its own rectangle. Overlapping rectangles are fine.
4. If a piece is partly hidden, box all of its visible part. Skip pieces too blurry to identify.
5. Zoom out, compare with the frame, and fix any missed or wrong boxes.
6. Press Ctrl+S, go to the next frame with F, and repeat until the last frame.
```

## 3. Що як розмічати

| Мітка | Що це |
| --- | --- |
| `marquise_warrior` | помаранчевий дерев'яний воїн (котик) |
| `eyrie_warrior` | синій дерев'яний воїн |
| `eyrie_building` | темно-синя квадратна плитка з білою гілкою |
| `alliance_warrior` | зелений дерев'яний воїн |
| `alliance_building` | квадратна плитка: зелена рамка, біла середина з червоним (або іншим) символом |
| `alliance_token` | світло-зелений **круглий** жетон (кулак) |

Правила:

- Розмічай **кожну** таку фігурку, навіть якщо вона стоїть впритул до інших: **одна фігурка = один прямокутник**.
- Частково закрита фігурка: прямокутник навколо всієї видимої частини.
- **Не** розмічай: кубики, карти, квадратні плитки предметів, маркери на треку очок,
  коричневі квадратні будівлі й прості круглі жетони дерева Маркізи (наш бот їх не використовує),
  білі та інші фігурки, яких немає в таблиці.
- Фігурка дуже розмита або менша за ~10 пікселів - пропусти.

## Якщо щось не працює

- **Інструменти сірі, Items: 0** → у задачі немає міток. Відкрий задачу й перевір, чи вибрано проєкт `rootbot`.
  Якщо ні, додай мітки через **Labels → Raw** тим самим JSON, потім онови сторінку (**F5**).

## 4. Експорт

1. **Tasks → твоя задача → Actions → Export task dataset.**
2. Format: **Ultralytics YOLO Detection 1.0**, галочку **Save images** не став.
3. Завантаж zip і поклади поруч із кадрами: `data/to_label/<назва>.zip`. Контури з нього робить `colab/boxes_to_outlines.ipynb`.
