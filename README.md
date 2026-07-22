# Draw Stripe Pay

Локальный генератор «доказательств» покупки: реалистичный скриншот страницы **Reveal Product** (Crypto Voucher / Driffle-стиль) + готовый текст для поста.

Один запуск — картинка, caption и json с параметрами. Данные, вьюпорт, замазка и воркер шафлятся так, чтобы серия скринов не выглядела клонами.

---

## Что умеет

| Блок | Описание |
|------|----------|
| **Reveal UI** | Тёмная вёрстка под Driffle: степпер Cart → Checkout → Reveal, mail-баннер, модалка с ключом |
| **Суммы** | Номиналы **100–350 EUR**, упор на **110–150**, реже 200–250 и до 350 |
| **Почта** | Длинные `имя.фамилия@…` на реальных доменах (gmx, libero, wp.pl, orange.fr, …) |
| **Дата reveal** | Всегда **сегодняшний UTC**, время рандомное, не из будущего |
| **Код** | Формат `CV{amount}EU-XXXXX-…` |
| **Замазка** | Сплошной штрих «пальцем» как в редакторе Telegram: палитра кистей TG, email + код |
| **Fingerprint** | Viewport / aspect / DPR / zoom / padding / png\|jpeg — чтобы кадры отличались |
| **Caption** | Готовый текст Profit + Worker из пула тегов |

---

## Структура репо

```
draw-stripe-pay/
├── screenshot_reveal.py      # основной генератор
├── driffle-fake-reveal.user.js
├── dump_driffle.py           # опциональный дамп сайта
├── reveal-assets/            # svg-иконки / лого
├── requirements.txt
├── output/screenshots/       # сюда пишутся результаты (в git не коммитятся)
└── README.md
```

В `.gitignore`: куки, дампы, `__pycache__`, `.venv`, всё содержимое `output/screenshots/` кроме `.gitkeep`.

---

## Установка

Нужны Python 3.10+ и Chromium через Playwright.

```bash
cd draw-stripe-pay
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

Зависимости: `playwright`, `Pillow`.

---

## Быстрый старт

```bash
source .venv/bin/activate
python screenshot_reveal.py
```

Пример вывода в консоль:

```
🚀 Profit: 140 EUR
🥷 Worker: @geemx
saved output/screenshots/reveal-cv140eu-....png
text  output/screenshots/reveal-cv140eu-....txt
cfg   output/screenshots/reveal-cv140eu-....json
```

Рядом с PNG/JPG всегда:

- **`.txt`** — caption для копипаста в чат  
- **`.json`** — полный cfg (email, code, amount, fingerprint, worker, …)

---

## Caption

Формат фиксированный:

```
🚀 Profit: {amount} EUR
🥷 Worker: @{tag}
```

`amount` = тот же номинал, что на скрине.  
`Worker` берётся из пула (шафл; при `--count N` теги размазываются циклами без комков):

| # | Tag |
|---|-----|
| 1 | `@xv_Doshik` |
| 2 | `@gwertyI23` |
| 3 | `@geemx` |
| 4 | `@BiPKEP` |
| 5 | `@ionpr` |
| 6 | `@cykru` |
| 7 | `@Aleksand748e` |

Принудительно:

```bash
python screenshot_reveal.py --worker @xv_Doshik
```

---

## Рандомизация данных

По умолчанию каждый запуск крутит новый cfg:

- **Продукт** — сумма + обложка с CDN (для редких номиналов — ближайший арт)
- **Email** — `firstname.lastname` / `first.m.last` / `first_last` + цифры
- **Locale / флаг** — EUR + IT/DE/FR/ES (языки English / Deutsch / Italiano / Français)
- **Revealed on** — дата = сейчас (UTC), время ≤ now
- **Fingerprint** — размер окна, DPR, zoom, отступы, full_page, png/jpeg
- **Замазка** — цвет кисти TG, форма штриха; код закрыт целиком, длина ≈ до середины поля

Воспроизводимый прогон:

```bash
python screenshot_reveal.py --seed 42
```

Без шафла fingerprint (фиксированный 1440×900 @2x):

```bash
python screenshot_reveal.py --no-fingerprint
```

Фиксированный дефолтный продукт (можно добить CLI-оверрайдами):

```bash
python screenshot_reveal.py --fixed --email someone@gmx.de
```

---

## Замазка (redact)

После скриншота Pillow рисует **сплошной** штрих поверх:

1. email в баннере  
2. кода в Product Detail  

Стиль — кисть Telegram (красный / оранжевый / жёлтый / зелёный / голубой / синий / фиолетовый / розовый / белый / серый). Один цвет на кадр, меняется только форма.

Отключить:

```bash
python screenshot_reveal.py --no-redact
```

---

## Пакетная генерация

```bash
# 20 рандомных кадров
python screenshot_reveal.py --count 20

# только фото без json — вручную удали .json/.html или забери из папки
```

С `--count` нельзя указывать `-o` (один путь на много файлов).

Кастомная папка — цикл снаружи или копируй из `output/screenshots/`.

---

## CLI (полный список)

```bash
python screenshot_reveal.py -h
```

| Флаг | Смысл |
|------|--------|
| `--count N` | N скринов подряд |
| `--seed N` | seed RNG (+i для каждого из count) |
| `--fixed` | DEFAULTS вместо полного randomize |
| `--worker @tag` | зафиксировать воркера |
| `--email` / `--code` / `--title` / … | точечные оверрайды полей |
| `--width` `--height` `--dpr` | вьюпорт |
| `--format png\|jpeg` | формат файла |
| `--no-full-page` | кадр = viewport, не вся страница |
| `--no-fingerprint` | дефолтный fingerprint |
| `--no-redact` | без замазки |
| `-o PATH` | путь к одному файлу |

---

## Tampermonkey-оверлей

Файл `driffle-fake-reveal.user.js` — демо Reveal поверх реального driffle.com.

Триггеры:

- hash `#driffle-reveal`
- query `?driffle_reveal=1`
- пункт меню / FAB «Reveal demo»

Стили и ассеты завязаны на токены/CDN Driffle (не generic mock).

---

## Dump сайта (опционально)

```bash
python dump_driffle.py
```

Тянет публичные страницы/чанки Next.js в `output/` для ресёрча.  
**Куки и авторизационные дампы в git не входят** — см. `.gitignore`.  
Сессионные `cookies.json` / `cookies.full.json` держи только локально.

---

## Типичный воркфлоу

1. `python screenshot_reveal.py --count 10`  
2. Открыть `output/screenshots/`  
3. Картинку + текст из `.txt` — в пост  
4. При необходимости подогнать: `--seed`, `--worker`, `--format jpeg`, `--width 1920`

---

## Замечания

- Нужен интернет: шрифты Onest, обложки и иконки грузятся с CDN Driffle.  
- JPEG чуть легче и «шумнее» по артефактам — удобно для разнообразия серии.  
- Обложки на CDN есть не для всех номиналов: для 200–350 подставляется ближайший арт, в title/code сумма всё равно целевая.  
- Не коммить `output/screenshots/*` и любые cookie-файлы.

---

## Лицензия / использование

Внутренний инструмент. Используй на свой страх и риск; репозиторий не содержит чужих сессий и продакшен-секретов.
