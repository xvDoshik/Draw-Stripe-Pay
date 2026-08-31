EN | [RU](docs/README_RU.md)

## Draw Stripe Pay 🎨

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)

Local generator for purchase "proof" screenshots: realistic **Reveal Product** page (Crypto Voucher / Driffle-style) + ready post text.

One run - image, caption, and json with parameters. Data, viewport, redaction, and worker shuffle so a series of screenshots does not look like clones.

---

## ✨ Features

| Block | Description |
|------|----------|
| **Reveal UI** | Dark Driffle-style layout: stepper Cart → Checkout → Reveal, mail banner, key modal |
| **Amounts** | Denominations **100-350 EUR**, focus on **110-150**, less often 200-250 up to 350 |
| **Email** | Long `name.surname@…` on real domains (gmx, libero, wp.pl, orange.fr, …) |
| **Reveal date** | Always **today's UTC**, random time, not from the future |
| **Code** | Format `CV{amount}EU-XXXXX-…` |
| **Redaction** | Solid Telegram-style brush stroke: TG brush palette, email + code |
| **Fingerprint** | Viewport / aspect / DPR / zoom / padding / png\|jpeg - frames differ |
| **Caption** | Ready Profit + Worker text from tag pool |

---

## 📁 Structure

```
draw-stripe-pay/
├── screenshot_reveal.py      # main generator
├── driffle-fake-reveal.user.js
├── dump_driffle.py           # optional site dump
├── reveal-assets/            # svg icons / logos
├── requirements.txt
├── output/screenshots/       # results go here (not committed)
└── README.md
```

In `.gitignore`: cookies, dumps, `__pycache__`, `.venv`, all `output/screenshots/` except `.gitkeep`.

---

## 🚀 Quick start

Python 3.10+ and Chromium via Playwright required.

```bash
cd draw-stripe-pay
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

Dependencies: `playwright`, `Pillow`.

---

## 🎮 Usage

```bash
source .venv/bin/activate
python screenshot_reveal.py
```

Example console output:

```
🚀 Profit: 140 EUR
🥷 Worker: @geemx
saved output/screenshots/reveal-cv140eu-....png
text  output/screenshots/reveal-cv140eu-....txt
cfg   output/screenshots/reveal-cv140eu-....json
```

Alongside PNG/JPG always:

- **`.txt`** - caption for copy-paste to chat  
- **`.json`** - full cfg (email, code, amount, fingerprint, worker, …)

---

## 📝 Caption

Fixed format:

```
🚀 Profit: {amount} EUR
🥷 Worker: @{tag}
```

`amount` = same denomination as on screen.  
`Worker` from pool (shuffle; with `--count N` tags spread cyclically without clumps):

| # | Tag |
|---|-----|
| 1 | `@xv_Doshik` |
| 2 | `@gwertyI23` |
| 3 | `@geemx` |
| 4 | `@BiPKEP` |
| 5 | `@ionpr` |
| 6 | `@cykru` |
| 7 | `@Aleksand748e` |

Force specific worker:

```bash
python screenshot_reveal.py --worker @xv_Doshik
```

---

## 🎲 Data randomization

Each run spins a new cfg by default:

- **Product** - amount + CDN cover (for rare denominations - nearest art)
- **Email** - `firstname.lastname` / `first.m.last` / `first_last` + digits
- **Locale / flag** - EUR + IT/DE/FR/ES (languages English / Deutsch / Italiano / Français)
- **Revealed on** - date = now (UTC), time ≤ now
- **Fingerprint** - window size, DPR, zoom, padding, full_page, png/jpeg
- **Redaction** - TG brush color, stroke shape; code fully covered, length ≈ to mid-field

Reproducible run:

```bash
python screenshot_reveal.py --seed 42
```

No fingerprint shuffle (fixed 1440×900 @2x):

```bash
python screenshot_reveal.py --no-fingerprint
```

Fixed default product (CLI overrides available):

```bash
python screenshot_reveal.py --fixed --email someone@gmx.de
```

---

## 🖌 Redaction

After screenshot Pillow draws a **solid** stroke over:

1. email in banner  
2. code in Product Detail  

Style - Telegram brush (red / orange / yellow / green / cyan / blue / purple / pink / white / gray). One color per frame, only shape changes.

Disable:

```bash
python screenshot_reveal.py --no-redact
```

---

## 📦 Batch generation

```bash
# 20 random frames


python screenshot_reveal.py --count 20

# photos only without json - manually delete .json/.html or pick from folder
```

With `--count` you cannot use `-o` (one path for many files).

Custom folder - loop externally or copy from `output/screenshots/`.

---

## 📋 Commands

```bash
python screenshot_reveal.py -h
```

| Flag | Meaning |
|------|--------|
| `--count N` | N screenshots in a row |
| `--seed N` | seed RNG (+i for each of count) |
| `--fixed` | DEFAULTS instead of full randomize |
| `--worker @tag` | lock worker |
| `--email` / `--code` / `--title` / … | per-field overrides |
| `--width` `--height` `--dpr` | viewport |
| `--format png\|jpeg` | file format |
| `--no-full-page` | frame = viewport, not full page |
| `--no-fingerprint` | default fingerprint |
| `--no-redact` | no redaction |
| `-o PATH` | path to single file |

---

## 🔧 Tampermonkey overlay

File `driffle-fake-reveal.user.js` - Reveal demo overlay on real driffle.com.

Triggers:

- hash `#driffle-reveal`
- query `?driffle_reveal=1`
- menu item / FAB "Reveal demo"

Styles and assets tied to Driffle tokens/CDN (not generic mock).

---

## 🔍 Site dump (optional)

```bash
python dump_driffle.py
```

Pulls public pages/Next.js chunks to `output/` for research.  
**Cookies and auth dumps are not in git** - see `.gitignore`.  
Session `cookies.json` / `cookies.full.json` - local only.

---

## 🔄 Typical workflow

1. `python screenshot_reveal.py --count 10`  
2. Open `output/screenshots/`  
3. Image + text from `.txt` - into post  
4. If needed tune: `--seed`, `--worker`, `--format jpeg`, `--width 1920`

---

## ⚠️ Notes

- Internet required: Onest fonts, covers and icons load from Driffle CDN.  
- JPEG is slightly lighter and noisier in artifacts - good for series variety.  
- CDN covers not available for all denominations: for 200-350 nearest art is substituted, title/code still target amount.  
- Do not commit `output/screenshots/*` or any cookie files.

---

## 📄 License / usage

Internal tool. Use at your own risk; repository contains no third-party sessions or production secrets.
