#!/usr/bin/env python3
"""Dump https://driffle.com Next.js frontend + static assets + common probes."""

from __future__ import annotations

import json
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
ASSETS = OUT / "_next"
SITE = OUT / "site-assets"
PROBES = OUT / "probes"

BASE = "https://driffle.com"
ASSETS_CDN = "https://assets.driffle.com"
STATIC_CDN = "https://static.driffle.com"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

PAGES = [
    "/",
    "/store",
    "/login",
    "/signup",
    "/cart",
    "/sell-on-driffle",
    "/help",
    "/about-us",
    "/ru",
]

COMMON_PATHS = [
    "/robots.txt",
    "/sitemap.xml",
    "/manifest.json",
    "/favicon.ico",
    "/site-assets/favicon.ico",
    "/site-assets/favicon-16x16.png",
    "/site-assets/favicon-32x32.png",
    "/site-assets/apple-touch-icon.png",
    "/cdn-cgi/trace",
    "/api",
    "/api/",
    "/api/health",
    "/api/v1",
    "/api/v1/health",
    "/api/auth/session",
    "/api/user",
    "/api/products",
    "/api/search",
    "/_next/data",
    "/.well-known/security.txt",
]


def fetch(url: str, *, method: str = "GET", timeout: int = 45) -> tuple[int, dict[str, str], bytes]:
    headers = {
        "User-Agent": UA,
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
    }
    req = urllib.request.Request(url, headers=headers, method=method)
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.status, dict(resp.headers.items()), resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers.items()), exc.read() or b""
    except Exception as exc:
        return 0, {}, str(exc).encode()


def save(path: Path, body: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)


def url_to_local(url: str) -> Path:
    parsed = urllib.parse.urlparse(url)
    path = parsed.path.lstrip("/")
    if parsed.netloc and parsed.netloc not in {"driffle.com", "www.driffle.com"}:
        host = parsed.netloc.replace(":", "_")
        return OUT / "cdn" / host / path
    if path.startswith("_next/"):
        return OUT / path
    if path.startswith("site-assets/"):
        return OUT / path
    name = path.replace("/", "_") or "root"
    return OUT / "pages" / name


def download(url: str) -> dict:
    status, headers, body = fetch(url)
    dest = url_to_local(url)
    ok = 200 <= status < 300 and body
    if ok:
        save(dest, body)
    return {
        "url": url,
        "status": status,
        "size": len(body),
        "content_type": headers.get("Content-Type", ""),
        "dest": str(dest.relative_to(ROOT)) if ok else None,
    }


def extract_refs(html: str) -> list[str]:
    refs: list[str] = []
    for pat in (
        r'<script[^>]+src="([^"]+)"',
        r'<link[^>]+href="([^"]+)"',
        r'src="(/_next/[^"]+)"',
        r'href="(/_next/[^"]+)"',
        r'src="(/site-assets/[^"]+)"',
        r'href="(/site-assets/[^"]+)"',
        r'"(https://assets\.driffle\.com/[^"]+)"',
        r'"(https://static\.driffle\.com/[^"]+)"',
    ):
        refs.extend(re.findall(pat, html, flags=re.I))
    # drop next/image optimizer URLs (product CDN thumbnails) — keep a few originals separately
    cleaned = []
    for r in refs:
        if "/_next/image" in r:
            continue
        if r.startswith("//"):
            r = "https:" + r
        cleaned.append(r)
    return sorted(set(cleaned))


def absolutize(ref: str) -> str:
    if ref.startswith("http"):
        return ref
    return urllib.parse.urljoin(BASE + "/", ref.lstrip("/"))


def extract_next_data(html: str) -> dict | None:
    m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return {"raw": m.group(1)[:2000]}


def extract_apis_from_js(text: str) -> list[str]:
    pats = [
        r'https://[a-zA-Z0-9.-]*driffle\.com/[a-zA-Z0-9_./?=&%-]{3,120}',
        r'["\'](/api/[a-zA-Z0-9_./?=&%-]{2,80})["\']',
        r'["\'](https://api[a-zA-Z0-9.-]*\.driffle\.com[^"\']*)["\']',
    ]
    found: list[str] = []
    for pat in pats:
        found.extend(re.findall(pat, text))
    return sorted(set(found))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    ASSETS.mkdir(parents=True, exist_ok=True)
    SITE.mkdir(parents=True, exist_ok=True)
    PROBES.mkdir(parents=True, exist_ok=True)

    print("== pages ==")
    page_results = []
    html_blobs: list[str] = []
    for path in PAGES:
        url = BASE + path
        status, headers, body = fetch(url)
        rel = "index.html" if path == "/" else f"pages{path.rstrip('/')}.html".replace("/", "_")
        dest = OUT / rel if path == "/" else OUT / "pages" / (path.strip("/").replace("/", "_") + ".html")
        item = {
            "url": url,
            "status": status,
            "size": len(body),
            "content_type": headers.get("Content-Type", ""),
            "dest": None,
        }
        if 200 <= status < 300 and body:
            save(dest, body)
            item["dest"] = str(dest.relative_to(ROOT))
            text = body.decode("utf-8", "replace")
            html_blobs.append(text)
            next_data = extract_next_data(text)
            if next_data:
                nd_path = dest.with_suffix(".NEXT_DATA.json")
                nd_path.write_text(json.dumps(next_data, ensure_ascii=False, indent=2), encoding="utf-8")
                item["next_data"] = str(nd_path.relative_to(ROOT))
                item["buildId"] = next_data.get("buildId")
        page_results.append(item)
        print(f"  {status} {len(body):7d} {path}")

    # primary next data
    primary_html = html_blobs[0] if html_blobs else ""
    next_data = extract_next_data(primary_html)
    build_id = (next_data or {}).get("buildId")
    if next_data:
        (OUT / "__NEXT_DATA__.json").write_text(
            json.dumps(next_data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    print("== static refs ==")
    refs: set[str] = set()
    for html in html_blobs:
        refs.update(extract_refs(html))

    # always pull build manifests if we know buildId
    if build_id:
        for name in ("_buildManifest.js", "_ssgManifest.js"):
            refs.add(f"/_next/static/{build_id}/{name}")

    asset_results = []
    urls = [absolutize(r) for r in sorted(refs)]
    print(f"  downloading {len(urls)} assets...")
    with ThreadPoolExecutor(max_workers=12) as pool:
        futs = {pool.submit(download, u): u for u in urls}
        for fut in as_completed(futs):
            item = fut.result()
            asset_results.append(item)
            mark = "OK" if item.get("dest") else "FAIL"
            print(f"  {mark} {item['status']} {item['size']:7d} {item['url'][:110]}")

    # crawl deeper from downloaded JS for more chunks / API endpoints
    print("== js crawl ==")
    api_hits: set[str] = set()
    extra_chunks: set[str] = set()
    for p in OUT.rglob("*.js"):
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        api_hits.update(extract_apis_from_js(text))
        for chunk in re.findall(r'static/chunks/[a-zA-Z0-9._-]+\.js', text):
            extra_chunks.add("/_next/" + chunk)
        for css in re.findall(r'static/css/[a-zA-Z0-9._-]+\.css', text):
            extra_chunks.add("/_next/" + css)

    already = {a["url"] for a in asset_results}
    extra_urls = [absolutize(c) for c in sorted(extra_chunks) if absolutize(c) not in already]
    print(f"  extra chunks: {len(extra_urls)}")
    with ThreadPoolExecutor(max_workers=12) as pool:
        futs = {pool.submit(download, u): u for u in extra_urls[:200]}
        for fut in as_completed(futs):
            item = fut.result()
            asset_results.append(item)

    # re-scan after extra downloads
    for p in OUT.rglob("*.js"):
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        api_hits.update(extract_apis_from_js(text))

    print("== probes ==")
    probe_results = []
    for path in COMMON_PATHS:
        url = BASE + path
        status, headers, body = fetch(url)
        item = {
            "url": url,
            "status": status,
            "size": len(body),
            "content_type": headers.get("Content-Type", ""),
            "preview": body[:400].decode("utf-8", "replace"),
        }
        if 200 <= status < 300 and body and path not in {"/api", "/api/", "/_next/data"}:
            name = path.strip("/").replace("/", "_") or "root"
            dest = PROBES / name
            if "." not in Path(name).name:
                dest = PROBES / (name + ".bin")
            save(dest, body)
            item["dest"] = str(dest.relative_to(ROOT))
        probe_results.append(item)
        print(f"  {status} {len(body):7d} {path}")

    # probe discovered API-ish paths (relative /api only, capped)
    api_probe = []
    for hit in sorted(api_hits):
        if hit.startswith("/api/"):
            url = BASE + hit.split("?")[0]
        elif "driffle.com" in hit and "/api" in hit:
            url = hit.split("?")[0]
        else:
            continue
        if any(x["url"] == url for x in api_probe):
            continue
        status, headers, body = fetch(url)
        api_probe.append(
            {
                "url": url,
                "status": status,
                "size": len(body),
                "content_type": headers.get("Content-Type", ""),
                "preview": body[:300].decode("utf-8", "replace"),
            }
        )
        if len(api_probe) >= 40:
            break

    summary = {
        "dumped_at": datetime.now(timezone.utc).isoformat(),
        "base": BASE,
        "platform": "next.js",
        "buildId": build_id,
        "assetPrefix": (next_data or {}).get("assetPrefix"),
        "cdn": {"assets": ASSETS_CDN, "static": STATIC_CDN},
        "pages": page_results,
        "assets_downloaded": sum(1 for a in asset_results if a.get("dest")),
        "assets_failed": sum(1 for a in asset_results if not a.get("dest")),
        "asset_count": len(asset_results),
        "api_strings_found": sorted(api_hits)[:200],
        "probes": probe_results,
        "api_probes": api_probe,
    }

    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "assets.json").write_text(json.dumps(asset_results, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "api-strings.json").write_text(
        json.dumps(sorted(api_hits), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("wrote", OUT / "summary.json")
    print(f"done: pages={len(page_results)} assets_ok={summary['assets_downloaded']} apis={len(api_hits)}")


if __name__ == "__main__":
    main()
