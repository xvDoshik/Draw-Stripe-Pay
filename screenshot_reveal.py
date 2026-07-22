#!/usr/bin/env python3
"""Render Driffle Reveal clone page and save a screenshot via Playwright."""

from __future__ import annotations

import argparse
import html as html_lib
import json
import math
import random
import re
import string
from datetime import datetime, timedelta, timezone
from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output" / "screenshots"
ORIGIN = "https://driffle.com"
CDN = "https://static.driffle.com/fit-in/360x504/media-gallery/production"

# Verified Crypto Voucher Europe covers from Driffle CDN (keyed by face value)
COVERS_BY_AMOUNT: dict[int, list[str]] = {
    100: [
        f"{CDN}/53a866a8-d975-4d2c-818f-6cda28328b50_crypto-voucher-bitcoin-europe-100eur-43450jpg",
    ],
    110: [
        f"{CDN}/906fe568-1e0e-45f3-9706-18b3e0067bb1_crypto-voucher-europe-110-eur-110708.png",
        f"{CDN}/386749ba-1ef9-4272-91d3-eb938e49264c_crypto-voucher-europe-110-eur-122073.png",
        f"{CDN}/3a427cab-7262-4ef3-9f36-0d81b9239131_crypto-voucher-europe-110-eur-121994.png",
        f"{CDN}/b7707334-e620-404e-a974-0510f0a05e38_crypto-voucher-europe-110-eur-121915.png",
    ],
    120: [
        f"{CDN}/aea81266-023a-4e86-a0e4-a93702bf935f_crypto-voucher-europe-120-eur-110709.png",
    ],
    130: [
        f"{CDN}/6d785a04-0699-49b7-aefa-0b977553fc78_crypto-voucher-europe-130-eur-110710.png",
    ],
    140: [
        f"{CDN}/7266e7c3-e907-4fbd-993b-a8ab900d043d_crypto-voucher-europe-140-eur-110711.png",
    ],
    150: [
        f"{CDN}/ca66a931-2767-4212-9f2b-ffc2b59707eb_crypto-voucher-bitcoin-europe-150eur-52900jpg",
    ],
    160: [
        f"{CDN}/9b660f4e-96b0-4434-92c5-60a458fb9be6_crypto-voucher-europe-160-eur-110712.png",
    ],
    190: [
        f"{CDN}/f72955ae-d22b-4693-8d52-264cf38afa10_crypto-voucher-europe-190-eur-110715.png",
    ],
}

# Amount bands 100–350: bias to 110–150, allow 200–250 and up to 350
AMOUNT_CHOICES: list[tuple[int, int]] = [
    # (amount, weight)
    (100, 6),
    (110, 18),
    (120, 14),
    (130, 14),
    (140, 14),
    (150, 14),
    (160, 5),
    (170, 3),
    (180, 3),
    (190, 4),
    (200, 4),
    (210, 2),
    (220, 3),
    (230, 2),
    (240, 2),
    (250, 5),
    (280, 2),
    (300, 3),
    (320, 1),
    (350, 2),
]

WORKER_POOL = [
    "@xv_Doshik",
    "@gwertyI23",
    "@geemx",
    "@BiPKEP",
    "@ionpr",
    "@cykru",
    "@Aleksand748e",
]


def pick_amount() -> int:
    amounts, weights = zip(*AMOUNT_CHOICES)
    return int(random.choices(amounts, weights=weights, k=1)[0])


def pick_worker() -> str:
    return random.choice(WORKER_POOL)


def shuffled_workers(n: int) -> list[str]:
    """Fair-ish shuffle: reshuffle pool cycles so tags don't clump."""
    out: list[str] = []
    while len(out) < n:
        chunk = list(WORKER_POOL)
        random.shuffle(chunk)
        out.extend(chunk)
    return out[:n]


def format_caption(amount: int, worker: str, currency: str = "EUR") -> str:
    tag = worker if worker.startswith("@") else f"@{worker}"
    templates = [
        "🚀 Profit: {amount} {currency}\n🥷 Worker: {worker}",
        "🚀 Profit: {amount} {currency}\n🥷 Worker: {worker}",
        "🚀 Profit : {amount} {currency}\n🥷 Worker: {worker}",
        "🚀 Profit: {amount}{currency}\n🥷 Worker: {worker}",
        "🚀 Profit: {amount} {currency}\n🥷 {worker}",
        "🚀 {amount} {currency}\n🥷 Worker: {worker}",
        "🚀 Profit: {amount} {currency}\nWorker: {worker}",
        "Profit: {amount} {currency}\n🥷 Worker: {worker}",
    ]
    tpl = random.choice(templates)
    return tpl.format(amount=amount, currency=currency, worker=tag)


def cover_for_amount(amount: int) -> str:
    if amount in COVERS_BY_AMOUNT:
        return random.choice(COVERS_BY_AMOUNT[amount])
    # nearest available art (title/code still show the true amount)
    nearest = min(COVERS_BY_AMOUNT.keys(), key=lambda a: abs(a - amount))
    return random.choice(COVERS_BY_AMOUNT[nearest])


# Back-compat alias used nowhere critical
PRODUCT_POOL = [
    {"amount": a, "currency": "EUR", "region": "Europe", "region_code": "EU", "img": imgs[0]}
    for a, imgs in sorted(COVERS_BY_AMOUNT.items())
]

LOCALES = [
    ("EUR", "English", "IT"),
    ("EUR", "English", "DE"),
    ("EUR", "Deutsch", "DE"),
    ("EUR", "Italiano", "IT"),
    ("EUR", "Français", "FR"),
    ("EUR", "Español", "ES"),
    ("USD", "English", "US"),
    ("GBP", "English", "GB"),
]

FLAG_GRADIENTS = {
    "IT": "linear-gradient(90deg,#009246 0 33.33%,#fff 33.33% 66.66%,#ce2b37 66.66% 100%)",
    "DE": "linear-gradient(180deg,#000 0 33.33%,#dd0000 33.33% 66.66%,#ffce00 66.66% 100%)",
    "FR": "linear-gradient(90deg,#002395 0 33.33%,#fff 33.33% 66.66%,#ed2939 66.66% 100%)",
    "ES": "linear-gradient(180deg,#aa151b 0 25%,#f1bf00 25% 75%,#aa151b 75% 100%)",
    "US": "linear-gradient(180deg,#b22234 0 14%,#fff 14% 28%,#b22234 28% 42%,#fff 42% 57%,#b22234 57% 71%,#fff 71% 85%,#b22234 85% 100%)",
    "GB": "linear-gradient(135deg,#012169 0%,#fff 35%,#c8102e 50%,#fff 65%,#012169 100%)",
}

EMAIL_FIRST = [
    "alexander", "sebastian", "christopher", "jonathan", "nicholas", "benjamin", "dominic",
    "frederick", "matthias", "andreas", "lorenzo", "francesco", "giovanni", "alessandro",
    "valentina", "katarzyna", "margaret", "elizabeth", "christina", "victoria", "isabella",
    "natalia", "sophie", "camille", "juliette", "antoine", "maximilian", "leonardo",
    "patrick", "gabriel", "raphael", "thiago", "emmanuel", "stephanie", "jennifer",
    "michael", "daniel", "thomas", "martin", "stefan", "lukasz", "wojciech", "bartosz",
    "henrik", "johannes", "philippe", "nicolas", "clemence", "aurelie", "mathieu",
]
EMAIL_LAST = [
    "anderson", "richardson", "thompson", "henderson", "peterson", "morrison", "sullivan",
    "bernardi", "rossellini", "ferrari", "esposito", "conti", "moreau", "dupont",
    "lefebvre", "schneider", "mueller", "wagner", "hoffmann", "kowalski", "nowak",
    "wisniewski", "jansen", "deboer", "vanberg", "olsen", "bergstrom", "nilsson",
    "castillo", "hernandez", "ramirez", "silva", "oliveira", "ferreira", "costa",
    "novak", "horvath", "petrov", "ivanov", "smirnov", "karlsen", "eriksson",
]
# Real mail providers / ISP domains (not inventing TLDs)
EMAIL_DOMAINS = [
    "gmail.com",
    "googlemail.com",
    "outlook.com",
    "hotmail.com",
    "live.com",
    "yahoo.com",
    "yahoo.co.uk",
    "yahoo.fr",
    "yahoo.de",
    "icloud.com",
    "me.com",
    "mac.com",
    "proton.me",
    "protonmail.com",
    "pm.me",
    "gmx.com",
    "gmx.de",
    "gmx.net",
    "web.de",
    "t-online.de",
    "freenet.de",
    "mail.de",
    "posteo.de",
    "mailbox.org",
    "orange.fr",
    "free.fr",
    "laposte.net",
    "sfr.fr",
    "wanadoo.fr",
    "libero.it",
    "virgilio.it",
    "alice.it",
    "tin.it",
    "email.it",
    "tiscali.it",
    "hotmail.it",
    "outlook.it",
    "wp.pl",
    "o2.pl",
    "interia.pl",
    "onet.pl",
    "seznam.cz",
    "centrum.cz",
    "email.cz",
    "mail.ru",
    "yandex.ru",
    "bk.ru",
    "inbox.ru",
    "list.ru",
    "ukr.net",
    "i.ua",
    "meta.ua",
    "rambler.ru",
    "btinternet.com",
    "sky.com",
    "virginmedia.com",
    "blueyonder.co.uk",
    "aol.com",
    "zoho.com",
    "fastmail.com",
    "hey.com",
    "tutanota.com",
    "tutamail.com",
]

# Default product data (same as Tampermonkey CFG)
DEFAULTS = {
    "email": "jonathan.richardson@gmail.com",
    "title": "Crypto Voucher 110 EUR Gift Card (Europe) - Digital Key",
    "product_type": "giftcard",
    "platform": "Crypto Voucher",
    "region": "Europe",
    "code": "CV110EU-7X9M2-PLK4Q-NZ8JD-Y3F6R",
    "revealed_at": "July 21, 2025 at 07:09 PM UTC",
    "locale_label": "EUR - English",
    "product_img": (
        f"{CDN}/906fe568-1e0e-45f3-9706-18b3e0067bb1_crypto-voucher-europe-110-eur-110708.png"
    ),
    "product_url": "https://driffle.com/store?productType=giftcard&platform=Crypto+Voucher",
    "flag_css": FLAG_GRADIENTS["IT"],
    "amount": 110,
    "currency": "EUR",
}

# Common desktop/laptop viewports (real device sizes people screenshot from)
VIEWPORT_POOL = [
    # 16:9
    {"width": 1920, "height": 1080, "aspect": "16:9"},
    {"width": 1600, "height": 900, "aspect": "16:9"},
    {"width": 1536, "height": 864, "aspect": "16:9"},
    {"width": 1366, "height": 768, "aspect": "16:9"},
    {"width": 1280, "height": 720, "aspect": "16:9"},
    # 16:10
    {"width": 1920, "height": 1200, "aspect": "16:10"},
    {"width": 1680, "height": 1050, "aspect": "16:10"},
    {"width": 1440, "height": 900, "aspect": "16:10"},
    {"width": 1280, "height": 800, "aspect": "16:10"},
    # 3:2 / Mac-ish
    {"width": 1512, "height": 982, "aspect": "3:2"},
    {"width": 1470, "height": 956, "aspect": "3:2"},
    {"width": 1440, "height": 960, "aspect": "3:2"},
    # 5:4 / older
    {"width": 1280, "height": 1024, "aspect": "5:4"},
    # ultrawide (rarer)
    {"width": 2560, "height": 1080, "aspect": "21:9"},
]

DEFAULT_FINGERPRINT = {
    "width": 1440,
    "height": 900,
    "aspect": "16:10",
    "dpr": 2.0,
    "full_page": True,
    "zoom": 1.0,
    "format": "png",
    "jpeg_quality": 92,
    "scroll_y": 0,
    "page_max_width": 1120,
    "page_pad_x": 24,
    "page_pad_top": 8,
    "page_pad_bottom": 48,
    "hdr_height": 72,
    "hdr_pad_x": 24,
    "steps_width": 700,
    "steps_width_narrow": 500,
    "modal_radius": 12,
    "cover_w": 120,
    "cover_h": 168,
    "btn_w": 176,
    "noise_opacity": 0.0,
}


def _chunk(n: int = 5) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(random.choices(alphabet, k=n))


def random_email() -> str:
    first = random.choice(EMAIL_FIRST)
    last = random.choice(EMAIL_LAST)
    # always longer local-part: first.last (+ optional digits / middle initial)
    roll = random.random()
    if roll < 0.55:
        user = f"{first}.{last}"
    elif roll < 0.75:
        user = f"{first}.{last}{random.randint(1, 99)}"
    elif roll < 0.88:
        mid = random.choice(string.ascii_lowercase)
        user = f"{first}.{mid}.{last}"
    else:
        user = f"{first}_{last}"
    return f"{user}@{random.choice(EMAIL_DOMAINS)}"


def random_code(amount: int, region_code: str) -> str:
    prefix = f"CV{amount}{region_code}"
    return f"{prefix}-{_chunk()}-{_chunk()}-{_chunk()}-{_chunk()}"


def random_revealed_at() -> str:
    """Reveal time = today (real clock), random time not after now."""
    now = datetime.now(timezone.utc)
    # seconds since midnight UTC, pick a moment earlier today (or now)
    secs_today = now.hour * 3600 + now.minute * 60 + now.second
    offset = random.randint(0, max(secs_today, 0))
    dt = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(seconds=offset)
    if dt > now:
        dt = now
    hour12 = dt.strftime("%I").lstrip("0") or "12"
    return f"{dt.strftime('%B')} {dt.day}, {dt.year} at {hour12}:{dt.strftime('%M %p')} UTC"


def randomize_fingerprint() -> dict:
    """Vary capture traits that otherwise fingerprint every shot as the same script."""
    vp = random.choice(VIEWPORT_POOL)
    # small jitter so sizes aren't only exact catalog entries
    w = vp["width"] + random.choice([0, 0, 0, -8, -16, 8, 16, 24, -24])
    h = vp["height"] + random.choice([0, 0, 0, -10, 10, -20, 20])
    w = max(1100, min(w, 2560))
    h = max(700, min(h, 1440))

    dpr = random.choices(
        [1.0, 1.25, 1.5, 1.75, 2.0],
        weights=[18, 12, 28, 10, 32],
    )[0]
    full_page = random.random() < 0.72
    zoom = round(random.uniform(0.92, 1.06), 3)
    # most keep png; jpeg changes compression fingerprint
    fmt = random.choices(["png", "jpeg"], weights=[70, 30])[0]
    jpeg_quality = random.randint(84, 96) if fmt == "jpeg" else 92
    scroll_y = 0 if full_page else random.randint(0, 40)

    return {
        "width": w,
        "height": h,
        "aspect": vp["aspect"],
        "dpr": dpr,
        "full_page": full_page,
        "zoom": zoom,
        "format": fmt,
        "jpeg_quality": jpeg_quality,
        "scroll_y": scroll_y,
        "page_max_width": random.choice([1040, 1080, 1120, 1160, 1200]),
        "page_pad_x": random.choice([16, 20, 24, 28, 32]),
        "page_pad_top": random.choice([4, 6, 8, 10, 12, 16]),
        "page_pad_bottom": random.choice([32, 40, 48, 56, 64, 80, 96]),
        "hdr_height": random.choice([64, 68, 72, 76, 80]),
        "hdr_pad_x": random.choice([16, 20, 24, 28, 32]),
        "steps_width": random.choice([560, 620, 660, 700, 740]),
        "steps_width_narrow": random.choice([420, 460, 500, 540]),
        "modal_radius": random.choice([10, 12, 14]),
        "cover_w": random.choice([112, 116, 120, 124, 128]),
        "cover_h": random.choice([156, 162, 168, 174, 180]),
        "btn_w": random.choice([160, 168, 176, 184, 192]),
        # tiny grain so pixel hashes diverge even on identical layouts
        "noise_opacity": round(random.uniform(0.012, 0.035), 3),
    }


def randomize_cfg(seed: int | None = None) -> dict:
    if seed is not None:
        random.seed(seed)
    amount = pick_amount()
    currency = "EUR"
    region = "Europe"
    region_code = "EU"
    product_img = cover_for_amount(amount)
    currency_label, lang, flag = random.choice(LOCALES)
    # keep currency consistent with product when EUR voucher
    if currency == "EUR":
        currency_label = "EUR"
        flag = random.choice(["IT", "DE", "FR", "ES"])
        lang = random.choice(["English", "Deutsch", "Italiano", "Français"])
    cfg = {
        "email": random_email(),
        "title": f"Crypto Voucher {amount} {currency} Gift Card ({region}) - Digital Key",
        "product_type": "giftcard",
        "platform": "Crypto Voucher",
        "region": region,
        "code": random_code(amount, region_code),
        "revealed_at": random_revealed_at(),
        "locale_label": f"{currency_label} - {lang}",
        "product_img": product_img,
        "product_url": "https://driffle.com/store?productType=giftcard&platform=Crypto+Voucher",
        "flag_css": FLAG_GRADIENTS.get(flag, FLAG_GRADIENTS["IT"]),
        "amount": amount,
        "currency": currency,
        "worker": pick_worker(),
        "fingerprint": randomize_fingerprint(),
    }
    cfg["caption"] = format_caption(cfg["amount"], cfg["worker"], cfg["currency"])
    return cfg


T = {
    "bg1": "#161616",
    "bg2": "#0C0C0C",
    "bg3": "#212121",
    "bg4": "#353535",
    "t1": "#FFFFFF",
    "t2": "#BFBFBF",
    "t3": "#8F8F8F",
    "primary": "#4885FF",
    "primary_hover": "#477BFF",
    "grey_btn": "#353535",
    "grey_btn_hover": "#535353",
    "border2": "#353535",
    "divider": "#ffffff1a",
    "radius2": "8px",
    "radius3": "12px",
    "gift_bg": "#FF7F6A",
    "gift_text": "#FFFFFF",
    "step_idle": "#4D4D4D",
}

LOGO_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 123 32" width="123" height="32" aria-label="Driffle logo">
  <path d="M22.0464 10.5545L11.8925 7.22134L11.8002 11.1101L18.7233 11.6656L22.0464 10.5545Z" fill="#839EFF"></path>
  <path d="M21.677 20.7404L3.21536 30.9252L11.5231 31.2955L23.7078 22.5922L21.677 20.7404Z" fill="#839EFF"></path>
  <path d="M25 9.07432L6.72298 0.741333L8.19991 24.6292L11.6153 23.1478L11.8922 7.22255L22.0461 10.5557L21.6769 20.7405L23.7077 22.5923L25 9.07432Z" fill="#416AFF"></path>
  <path d="M6.72311 0.741333L1 3.33382L3.2154 30.9253L21.677 20.7405L22.0463 10.5557L18.7232 11.6668V19.9998L8.20004 24.6292L6.72311 0.741333Z" fill="#263BFC"></path>
  <path d="M48.2291 26.3227V8.57852H44.2518V14.8795L44.9975 17.0523H44.0032C43.3569 15.4348 42.1637 13.8897 39.0564 13.8897C35.4272 13.8897 33.6125 16.7626 33.6125 20.2148C33.6125 23.6671 35.4272 26.5641 39.0564 26.5641C42.1637 26.5641 43.3569 25.019 44.0032 23.4015H44.9975L44.2518 25.5743V26.3227H48.2291ZM44.2518 20.2148C44.2518 22.2669 43.0586 23.1843 40.9208 23.1843C38.783 23.1843 37.5898 22.2669 37.5898 20.2148C37.5898 18.1628 38.783 17.2695 40.9208 17.2695C43.0586 17.2695 44.2518 18.1628 44.2518 20.2148Z" fill="white"></path>
  <path d="M50.4713 26.3227H54.4486V17.3661L60.8371 17.511V14.1311L52.6091 13.938C51.2419 13.9138 50.4713 14.6381 50.4713 15.9659V26.3227Z" fill="white"></path>
  <path d="M67.2332 12.924C68.6999 12.924 69.6196 12.2481 69.6196 10.9927C69.6196 9.76146 68.6999 9.06135 67.2332 9.06135C65.7666 9.06135 64.8966 9.76146 64.8966 10.9927C64.8966 12.2481 65.7666 12.924 67.2332 12.924ZM62.0876 26.3227H73.0252V22.9429H69.4705V15.9176C69.4705 14.5657 68.6998 13.8173 67.3078 13.8897L62.5848 14.1311V17.511L65.6423 17.3661V22.9429H62.0876V26.3227Z" fill="white"></path>
  <path d="M82.3221 11.9584H84.957V8.57852H82.8192C78.6182 8.57852 76.6544 10.4133 76.6544 13.6966V14.1311H74.2681V17.511H76.6544V22.9429H74.2681V26.3227H84.261V22.9429H80.6317V17.511H84.261V14.1311H80.6317V13.8173C80.6317 12.4653 81.1537 11.9584 82.3221 11.9584Z" fill="white"></path>
  <path d="M93.9986 11.9584H96.6335V8.57852H94.4957C90.2947 8.57852 88.3309 10.4133 88.3309 13.6966V14.1311H85.9445V17.511H88.3309V22.9429H85.9445V26.3227H95.9375V22.9429H92.3082V17.511H95.9375V14.1311H92.3082V13.8173C92.3082 12.4653 92.8302 11.9584 93.9986 11.9584Z" fill="white"></path>
  <path d="M97.621 26.3227H108.559V22.9429H105.078V10.4374C105.078 9.08549 104.308 8.36124 102.916 8.40952L98.1182 8.57852V11.9584L101.101 11.8135V22.9429H97.621V26.3227Z" fill="white"></path>
  <path d="M109.303 20.07C109.303 23.5223 111.516 26.5641 116.338 26.5641C120.688 26.5641 122.752 23.7878 123 22.0255H119.023C118.774 22.9429 117.73 23.4257 116.338 23.4257C114.076 23.4257 113.032 22.4359 113.032 21.0357H122.553V19.8286C122.553 16.1349 119.818 13.8897 115.916 13.8897C112.013 13.8897 109.303 16.2073 109.303 20.07ZM113.032 18.8629C113.032 17.9455 113.703 17.0281 115.916 17.0281C118.128 17.0281 118.824 17.9455 118.824 18.8629H113.032Z" fill="white"></path>
</svg>"""


def esc(value: str) -> str:
    return html_lib.escape(str(value), quote=True)


def type_meta(product_type: str) -> tuple[str, str, str]:
    if product_type == "giftcard":
        return T["gift_bg"], T["gift_text"], "GIFT CARD"
    return T["bg4"], T["t1"], product_type.upper()


def build_html(cfg: dict) -> str:
    tag_bg, tag_text, tag_label = type_meta(cfg["product_type"])
    origin = ORIGIN
    fp = {**DEFAULT_FINGERPRINT, **(cfg.get("fingerprint") or {})}
    noise = float(fp["noise_opacity"])
    return f"""<!DOCTYPE html>
<html lang="en" style="color-scheme:dark">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Reveal Product | Driffle</title>
<style>
@font-face{{font-family:Onest-Regular;src:url(https://assets.driffle.com/fonts/Onest/Onest-VariableFont_wght.woff2) format("woff2");font-weight:400;font-style:normal;font-display:swap}}
@font-face{{font-family:Onest-Medium;src:url(https://assets.driffle.com/fonts/Onest/Onest-VariableFont_wght.woff2) format("woff2");font-weight:500;font-style:normal;font-display:swap}}
@font-face{{font-family:Onest-SemiBold;src:url(https://assets.driffle.com/fonts/Onest/Onest-VariableFont_wght.woff2) format("woff2");font-weight:600;font-style:normal;font-display:swap}}
@font-face{{font-family:Onest-Bold;src:url(https://assets.driffle.com/fonts/Onest/Onest-VariableFont_wght.woff2) format("woff2");font-weight:700;font-style:normal;font-display:swap}}
*{{box-sizing:border-box}}
html,body{{margin:0;padding:0;background:{T["bg2"]};color:{T["t1"]};font-family:Onest-Medium,system-ui,sans-serif;min-height:100%}}
body{{zoom:{fp["zoom"]}}}
a{{color:inherit;text-decoration:none}}
button{{font:inherit;border:0;cursor:pointer;background:none;color:inherit}}
img{{display:block;max-width:100%}}
.hdr{{height:{fp["hdr_height"]}px;display:flex;align-items:center;justify-content:space-between;padding:0 {fp["hdr_pad_x"]}px;background:{T["bg2"]};position:relative;z-index:2}}
.logo{{display:inline-flex;align-items:center;height:28px}}
.logo svg{{height:28px;width:118px}}
.locale{{display:inline-flex;align-items:center;gap:8px;font:14px/18px Onest-Medium;color:{T["t2"]}}}
.flag{{width:18px;height:18px;border-radius:50%;overflow:hidden;box-shadow:inset 0 0 0 1px rgba(255,255,255,.12);background:{cfg.get("flag_css", FLAG_GRADIENTS["IT"])}}}
.steps-wrap{{width:{fp["steps_width"]}px;display:flex;position:absolute;left:50%;transform:translateX(-50%)}}
.steps{{width:100%;border-radius:6px;display:flex;align-items:center;justify-content:space-between}}
.step{{display:flex;align-items:center;justify-content:center}}
.step-num{{background-color:#fff;border-radius:8px;color:#000;border:none;height:40px;width:40px;display:flex;align-items:center;justify-content:center;font-size:16px;position:relative;font-family:Onest-Bold}}
.step-num.is-active{{background-color:transparent;color:{T["step_idle"]};border:2px solid {T["step_idle"]}}}
.step-num img{{width:20px;height:20px;display:block}}
.step-label{{font-size:16px;font-family:Onest-SemiBold;line-height:19px;color:#fff;margin-left:12px}}
.step-line{{flex-grow:1;margin:12px;border-bottom:2px solid #fff}}
.page{{max-width:{fp["page_max_width"]}px;margin:0 auto;padding:{fp["page_pad_top"]}px {fp["page_pad_x"]}px {fp["page_pad_bottom"]}px}}
.mail{{display:flex;align-items:flex-start;gap:16px;background:{T["bg1"]};border:1px solid {T["divider"]};border-radius:{T["radius3"]};padding:16px;margin:8px 0 24px;box-shadow:0px 4px 32px rgba(0,0,0,.04)}}
.mail-ico{{width:24px;height:24px;flex:0 0 auto;margin-top:2px;display:grid;place-items:center}}
.mail-ico img{{width:24px;height:24px;filter:invert(48%) sepia(98%) saturate(1800%) hue-rotate(201deg) brightness(101%) contrast(101%)}}
.mail h2{{margin:0 0 4px;font:16px/20px Onest-Bold;color:{T["t1"]}}}
.mail p{{margin:0;font:14px/18px Onest-Medium;color:{T["t2"]}}}
.mail b{{font-family:Onest-SemiBold;color:{T["t1"]};font-weight:600}}
.modal{{position:relative;background:{T["bg1"]};border:1px solid {T["divider"]};border-radius:{fp["modal_radius"]}px;box-shadow:0px 0px 48px rgba(0,0,0,.16);overflow:hidden}}
.close{{position:absolute;top:12px;right:12px;z-index:2;width:32px;height:32px;border-radius:8px;display:grid;place-items:center}}
.close img{{width:20px;height:20px;filter:invert(1)}}
.modal-title{{margin:0;padding:20px 24px 12px;font:20px/24px Onest-Bold;color:{T["t1"]}}}
.sep{{height:1px;background:{T["divider"]};margin:0 24px;width:calc(100% - 48px)}}
.product{{display:grid;grid-template-columns:{fp["cover_w"]}px 1fr;gap:16px;padding:20px 24px 8px}}
.cover{{width:{fp["cover_w"]}px;height:{fp["cover_h"]}px;border-radius:{T["radius2"]};object-fit:cover;background:{T["bg3"]}}}
.ptitle{{margin:0 0 10px;font:18px/24px Onest-Bold;color:{T["t1"]};max-width:640px}}
.ptitle .ext{{display:inline-flex;vertical-align:middle;margin-left:6px;opacity:.85}}
.ptitle .ext img{{width:14px;height:14px;filter:invert(.7)}}
.badge{{display:inline-block;background:{tag_bg};color:{tag_text};font:11px/14px Onest-Bold;letter-spacing:.02em;text-transform:uppercase;padding:4px 8px;border-radius:6px;margin-bottom:14px}}
.meta{{display:grid;grid-template-columns:1fr 1fr;gap:12px;max-width:520px}}
.meta-box{{background:{T["bg2"]};border:1px solid {T["divider"]};border-radius:10px;padding:12px 14px}}
.meta-label{{font:12px/14px Onest-Medium;color:{T["t3"]};margin-bottom:6px}}
.meta-val{{display:flex;align-items:center;gap:8px;font:14px/18px Onest-SemiBold;color:{T["t1"]}}}
.meta-val img{{width:18px;height:18px;border-radius:4px;object-fit:cover}}
.meta-val .globe{{width:16px;height:16px;filter:invert(.75)}}
.detail{{padding:8px 24px 22px}}
.detail h3{{margin:12px 0;font:15px/18px Onest-Bold;color:{T["t1"]}}}
.keybox{{display:flex;align-items:center;justify-content:space-between;gap:12px;background:{T["bg3"]};border:1px solid {T["border2"]};border-radius:{T["radius2"]};padding:12px 16px;min-height:52px;margin-bottom:14px}}
.keytext{{flex:1;font:16px/24px Onest-SemiBold;color:{T["t1"]};overflow-wrap:anywhere}}
.copy-ico{{width:32px;height:32px;border-radius:8px;display:grid;place-items:center;flex:0 0 auto}}
.copy-ico img{{width:24px;height:24px;filter:invert(1)}}
.actions{{display:flex;align-items:flex-end;justify-content:space-between;gap:16px;flex-wrap:wrap}}
.btns{{display:flex;gap:12px;flex-wrap:wrap}}
.btn{{height:48px;width:{fp["btn_w"]}px;border-radius:{T["radius2"]};display:inline-flex;align-items:center;justify-content:center;font:16px/24px Onest-Bold}}
.btn-primary{{background:{T["primary"]};color:#fff}}
.btn-grey{{background:{T["grey_btn"]};color:{T["t1"]}}}
.revealed{{font:14px/14px Onest-Medium;color:{T["t2"]};padding-bottom:4px}}
.revealed span{{color:{T["t1"]};font-family:Onest-SemiBold}}
.help{{margin:16px 0 0;font:12px/16px Onest-Medium;color:{T["t2"]}}}
.help a{{text-decoration:underline;color:{T["t1"]}}}
.help .note{{color:{T["t3"]}}}
.noise{{pointer-events:none;position:fixed;inset:0;z-index:9999;opacity:{noise};mix-blend-mode:overlay;background-image:url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")}}
@media (max-width:1609px){{.steps-wrap{{width:{fp["steps_width_narrow"]}px}}}}
</style>
</head>
<body>
  <div class="noise" aria-hidden="true"></div>
  <header class="hdr">
    <a class="logo" href="{origin}/">{LOGO_SVG}</a>
    <div class="steps-wrap" aria-label="Checkout steps">
      <div class="steps">
        <div class="step">
          <div class="step-num"><img src="{origin}/icons/check_circle_outline.svg" alt=""/></div>
          <div class="step-label">Cart</div>
        </div>
        <div class="step-line"></div>
        <div class="step">
          <div class="step-num"><img src="{origin}/icons/check_circle_outline.svg" alt=""/></div>
          <div class="step-label">Checkout</div>
        </div>
        <div class="step-line"></div>
        <div class="step">
          <div class="step-num is-active"><div>3</div></div>
          <div class="step-label">Reveal</div>
        </div>
      </div>
    </div>
    <div class="locale"><span class="flag" aria-hidden="true"></span>{esc(cfg["locale_label"])}</div>
  </header>
  <main class="page">
    <section class="mail">
      <div class="mail-ico"><img src="{origin}/icons/mark-email-read.svg" alt=""/></div>
      <div>
        <h2>Order delivered to your email</h2>
        <p>You can activate products at any time from the email we have sent you at <b data-redact="email">{esc(cfg["email"])}</b></p>
      </div>
    </section>
    <section class="modal" role="dialog" aria-label="Reveal Product">
      <button class="close" aria-label="Close"><img src="{origin}/icons/close-24.svg" alt=""/></button>
      <h1 class="modal-title">Reveal Product</h1>
      <div class="sep"></div>
      <div class="product">
        <img class="cover" src="{esc(cfg["product_img"])}" alt="product"/>
        <div>
          <h2 class="ptitle">
            {esc(cfg["title"])}
            <a class="ext" href="{esc(cfg["product_url"])}" title="Open product">
              <img src="{origin}/icons/open_in_new.svg" alt=""/>
            </a>
          </h2>
          <div class="badge">{esc(tag_label)}</div>
          <div class="meta">
            <div class="meta-box">
              <div class="meta-label">Platform</div>
              <div class="meta-val">
                <img src="{esc(cfg["product_img"])}" alt=""/>
                {esc(cfg["platform"])}
              </div>
            </div>
            <div class="meta-box">
              <div class="meta-label">Region</div>
              <div class="meta-val">
                <img class="globe" src="{origin}/icons/globe-black.svg" alt=""/>
                {esc(cfg["region"])}
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="detail">
        <h3>Product Detail</h3>
        <div class="keybox">
          <div class="keytext"><span data-redact="code">{esc(cfg["code"])}</span></div>
          <button class="copy-ico" title="Copy"><img src="{origin}/icons/content-copy-24.svg" alt=""/></button>
        </div>
        <div class="actions">
          <div class="btns">
            <button class="btn btn-primary">Copy to clipboard</button>
            <button class="btn btn-grey">Activation Guide</button>
          </div>
          <div class="revealed">Revealed on <span>{esc(cfg["revealed_at"])}</span></div>
        </div>
        <p class="help">
          Facing issues with the product? You can raise a ticket
          <a href="{origin}/support/ticket/product/create">here</a>.
          <span class="note"> (Our support will get in touch with you within 48 hours)</span>
        </p>
      </div>
    </section>
  </main>
</body>
</html>
"""


def slugify(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return s[:48] or "reveal"


# Default Telegram photo-editor brush palette
TELEGRAM_BRUSH_COLORS = [
    (255, 59, 48),    # red
    (255, 149, 0),    # orange
    (255, 204, 0),    # yellow
    (52, 199, 89),    # green
    (90, 200, 250),   # light blue
    (0, 122, 255),    # blue
    (175, 82, 222),   # purple
    (255, 45, 85),    # pink
    (255, 255, 255),  # white
    (142, 142, 147),  # grey
]


def _doc_box(page, selector: str) -> dict | None:
    """Element box in document CSS px (accounts for scroll)."""
    el = page.query_selector(selector)
    if not el:
        return None
    return page.evaluate(
        """(el) => {
          const r = el.getBoundingClientRect();
          return {
            x: r.x + window.scrollX,
            y: r.y + window.scrollY,
            w: r.width,
            h: r.height,
          };
        }""",
        el,
    )


def _finger_path(
    x0: float,
    x1: float,
    y_mid: float,
    *,
    amp: float,
    wobble: float,
    waves: float,
    steps: int,
) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    phase = random.uniform(0, math.tau)
    for i in range(steps):
        t = i / max(steps - 1, 1)
        t = t + 0.035 * math.sin(t * math.pi * 3 + phase)
        t = max(0.0, min(1.0, t))
        x = x0 + (x1 - x0) * t + random.gauss(0, wobble * 0.25)
        y = y_mid + amp * math.sin(t * math.pi * waves + phase) + random.gauss(0, wobble)
        pts.append((x, y))
    return pts


def _solid_stroke(
    draw: ImageDraw.ImageDraw,
    pts: list[tuple[float, float]],
    *,
    width: float,
    color: tuple[int, int, int, int],
) -> None:
    """Opaque round brush — flat color, only path shape varies."""
    if len(pts) < 2:
        return
    w = max(2, int(round(width)))
    r = w / 2
    for i in range(len(pts) - 1):
        x1, y1 = pts[i]
        x2, y2 = pts[i + 1]
        dist = math.hypot(x2 - x1, y2 - y1)
        n = max(1, int(dist / max(r * 0.35, 1.0)))
        for k in range(n + 1):
            u = k / n
            x = x1 + (x2 - x1) * u
            y = y1 + (y2 - y1) * u
            draw.ellipse((x - r, y - r, x + r, y + r), fill=color)


def smear_secrets(
    image_path: Path,
    boxes_css: list[dict],
    *,
    dpr: float = 1.0,
) -> None:
    """Finger-smear: Telegram brush color; code stroke ≈ to mid of keybox."""
    if not boxes_css:
        return
    img = Image.open(image_path).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    rgb = random.choice(TELEGRAM_BRUSH_COLORS)
    ink = (*rgb, 255)

    for box in boxes_css:
        kind = box.get("kind", "email")
        x = float(box["x"]) * dpr
        y = float(box["y"]) * dpr
        w = float(box["w"]) * dpr
        h = float(box["h"]) * dpr

        pad_x = random.uniform(2, 6) * dpr
        x0 = x - pad_x + random.uniform(-1, 2) * dpr
        x1 = x + w + pad_x + random.uniform(-1, 2) * dpr

        # code: stretch stroke roughly to the middle of the key row
        if kind == "code" and box.get("field"):
            fx = float(box["field"]["x"]) * dpr
            fw = float(box["field"]["w"]) * dpr
            mid_target = fx + fw * random.uniform(0.46, 0.56)
            x1 = max(x1, mid_target + random.uniform(-6, 10) * dpr)
            # keep full text covered
            x1 = max(x1, x + w + random.uniform(4, 12) * dpr)

        mid_y = y + h / 2 + random.uniform(-h * 0.06, h * 0.06)

        # a bit wider than the glyph line
        if kind == "code":
            brush = h * random.uniform(1.25, 1.55)
            brush = max(11 * dpr, min(brush, 30 * dpr))
        else:
            brush = h * random.uniform(1.05, 1.3)
            brush = max(8 * dpr, min(brush, 24 * dpr))

        n_strokes = 1 if random.random() < 0.5 else 2
        for s in range(n_strokes):
            if s % 2 == 0:
                a, b = x0 + random.uniform(-1, 2), x1 + random.uniform(-2, 1)
            else:
                a, b = x1 + random.uniform(-1, 2), x0 + random.uniform(-2, 1)
            row = mid_y + random.uniform(-h * 0.08, h * 0.08)
            pts = _finger_path(
                a,
                b,
                row,
                amp=random.uniform(h * 0.03, h * 0.14),
                wobble=random.uniform(0.25, 0.9) * dpr,
                waves=random.uniform(0.6, 1.5),
                steps=random.randint(12, 20),
            )
            width = brush if s == 0 else brush * random.uniform(0.9, 1.0)
            _solid_stroke(draw, pts, width=width, color=ink)

    img = Image.alpha_composite(img, overlay)
    suffix = image_path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        img.convert("RGB").save(image_path, quality=random.randint(88, 95), optimize=True)
    else:
        img.save(image_path)


def screenshot_reveal(
    cfg: dict,
    *,
    out_path: Path,
    width: int | None = None,
    height: int | None = None,
    full_page: bool | None = None,
    html_path: Path | None = None,
    redact: bool = True,
) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    fp = {**DEFAULT_FINGERPRINT, **(cfg.get("fingerprint") or {})}
    if width is not None:
        fp["width"] = width
    if height is not None:
        fp["height"] = height
    if full_page is not None:
        fp["full_page"] = full_page
    cfg = {**cfg, "fingerprint": fp}

    html = build_html(cfg)
    if html_path is None:
        html_path = OUT / "reveal-page.html"
    html_path.write_text(html, encoding="utf-8")

    img_type = "jpeg" if fp["format"] == "jpeg" else "png"
    if img_type == "jpeg" and out_path.suffix.lower() not in {".jpg", ".jpeg"}:
        out_path = out_path.with_suffix(".jpg")
    elif img_type == "png" and out_path.suffix.lower() != ".png":
        out_path = out_path.with_suffix(".png")

    dpr = float(fp["dpr"])
    secret_boxes: list[dict] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": int(fp["width"]), "height": int(fp["height"])},
            device_scale_factor=dpr,
        )
        page.goto(html_path.resolve().as_uri(), wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(random.randint(500, 1100))
        try:
            page.wait_for_selector("img.cover", state="visible", timeout=15000)
            page.evaluate(
                """async () => {
                  await document.fonts.ready;
                  const imgs = [...document.images];
                  await Promise.all(imgs.map(img => img.complete ? null : new Promise(r => {
                    img.onload = img.onerror = r;
                  })));
                }"""
            )
        except Exception:
            pass
        if fp.get("scroll_y"):
            page.evaluate(f"window.scrollTo(0, {int(fp['scroll_y'])})")
        page.wait_for_timeout(random.randint(200, 600))

        if redact:
            email_box = _doc_box(page, '[data-redact="email"]')
            if email_box and email_box["w"] > 2 and email_box["h"] > 2:
                secret_boxes.append({**email_box, "kind": "email"})
            code_box = _doc_box(page, '[data-redact="code"]')
            if code_box and code_box["w"] > 2 and code_box["h"] > 2:
                field = _doc_box(page, ".keybox")
                secret_boxes.append({**code_box, "kind": "code", "field": field})

        out_path.parent.mkdir(parents=True, exist_ok=True)
        shot_kwargs: dict = {
            "path": str(out_path),
            "full_page": bool(fp["full_page"]),
            "type": img_type,
        }
        if img_type == "jpeg":
            shot_kwargs["quality"] = int(fp["jpeg_quality"])
        page.screenshot(**shot_kwargs)
        browser.close()

    if redact and secret_boxes:
        smear_secrets(out_path, secret_boxes, dpr=dpr)

    # record actual output path used
    cfg["fingerprint"]["output_ext"] = out_path.suffix.lstrip(".")
    cfg["fingerprint"]["redacted"] = bool(redact and secret_boxes)
    return out_path


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Screenshot Driffle Reveal clone page")
    ap.add_argument(
        "--fixed",
        action="store_true",
        help="Use DEFAULTS / CLI overrides instead of randomize_cfg()",
    )
    ap.add_argument("--seed", type=int, default=None, help="RNG seed for reproducible random cfg")
    ap.add_argument("--count", type=int, default=1, help="How many randomized screenshots to make")
    ap.add_argument("--email", default=None)
    ap.add_argument("--title", default=None)
    ap.add_argument("--code", default=None)
    ap.add_argument("--platform", default=None)
    ap.add_argument("--region", default=None)
    ap.add_argument("--product-type", default=None)
    ap.add_argument("--revealed-at", default=None)
    ap.add_argument("--locale-label", default=None)
    ap.add_argument("--product-img", default=None)
    ap.add_argument("--product-url", default=None)
    ap.add_argument("--worker", default=None, help="Force worker tag, e.g. @xv_Doshik")
    ap.add_argument("--width", type=int, default=None, help="Override viewport width")
    ap.add_argument("--height", type=int, default=None, help="Override viewport height")
    ap.add_argument("--dpr", type=float, default=None, help="Override device scale factor")
    ap.add_argument("--format", choices=["png", "jpeg"], default=None)
    ap.add_argument("--no-full-page", action="store_true")
    ap.add_argument(
        "--no-fingerprint",
        action="store_true",
        help="Keep default capture fingerprint (1440x900 @2x png)",
    )
    ap.add_argument(
        "--no-redact",
        action="store_true",
        help="Do not finger-smear email/code on the screenshot",
    )
    ap.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output image path (default: output/screenshots/reveal-*.png|.jpg)",
    )
    return ap.parse_args()


def apply_overrides(cfg: dict, args: argparse.Namespace) -> dict:
    mapping = {
        "email": args.email,
        "title": args.title,
        "code": args.code,
        "platform": args.platform,
        "region": args.region,
        "product_type": args.product_type,
        "revealed_at": args.revealed_at,
        "locale_label": args.locale_label,
        "product_img": args.product_img,
        "product_url": args.product_url,
    }
    out = dict(cfg)
    for key, value in mapping.items():
        if value is not None:
            out[key] = value

    if args.worker is not None:
        out["worker"] = args.worker if args.worker.startswith("@") else f"@{args.worker}"

    amount = int(out.get("amount") or DEFAULTS.get("amount") or 110)
    currency = out.get("currency") or "EUR"
    worker = out.get("worker") or pick_worker()
    out["worker"] = worker
    out["caption"] = format_caption(amount, worker, currency)

    fp = {**DEFAULT_FINGERPRINT, **(out.get("fingerprint") or {})}
    if args.no_fingerprint:
        fp = dict(DEFAULT_FINGERPRINT)
    if args.width is not None:
        fp["width"] = args.width
    if args.height is not None:
        fp["height"] = args.height
    if args.dpr is not None:
        fp["dpr"] = args.dpr
    if args.format is not None:
        fp["format"] = args.format
    if args.no_full_page:
        fp["full_page"] = False
    out["fingerprint"] = fp
    return out


def main() -> None:
    args = parse_args()
    count = max(1, args.count)
    if args.output and count > 1:
        raise SystemExit("--output cannot be used with --count > 1")

    workers = shuffled_workers(count) if count > 1 and args.worker is None else None

    for i in range(count):
        seed = None if args.seed is None else args.seed + i
        if args.fixed:
            cfg = dict(DEFAULTS)
            cfg["fingerprint"] = (
                dict(DEFAULT_FINGERPRINT) if args.no_fingerprint else randomize_fingerprint()
            )
            cfg["worker"] = pick_worker()
            cfg["caption"] = format_caption(int(cfg["amount"]), cfg["worker"], cfg.get("currency", "EUR"))
        else:
            cfg = randomize_cfg(seed)
            if args.no_fingerprint:
                cfg["fingerprint"] = dict(DEFAULT_FINGERPRINT)
        if workers is not None:
            cfg["worker"] = workers[i]
            cfg["caption"] = format_caption(int(cfg["amount"]), cfg["worker"], cfg.get("currency", "EUR"))
        cfg = apply_overrides(cfg, args)

        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        suffix = f"-{i + 1}" if count > 1 else ""
        ext = ".jpg" if cfg["fingerprint"].get("format") == "jpeg" else ".png"
        out = args.output or (OUT / f"reveal-{slugify(cfg['code'])}{suffix}-{ts}{ext}")
        path = screenshot_reveal(
            cfg,
            out_path=out,
            width=None,
            height=None,
            full_page=None,
            redact=not args.no_redact,
        )
        caption = cfg.get("caption") or format_caption(
            int(cfg["amount"]), cfg.get("worker") or pick_worker(), cfg.get("currency", "EUR")
        )
        cfg["caption"] = caption
        caption_path = path.with_suffix(".txt")
        caption_path.write_text(caption + "\n", encoding="utf-8")
        meta_path = path.with_suffix(".json")
        meta_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(caption)
        print(f"saved {path}")
        print(f"text  {caption_path}")
        print(f"cfg   {meta_path}")
        print(f"html  {OUT / 'reveal-page.html'}")


if __name__ == "__main__":
    main()
