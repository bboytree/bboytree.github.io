#!/usr/bin/env python3
"""
add_photos.py - run by hand from the root of your site.

  python add_photos.py --baseline   (ONE time only: marks every photo already
                                     in photos/ as "handled" so it isn't re-added)
  python add_photos.py              (every time after you drop new photos in)

For each new photo in photos/ it:
  1. creates photos/<name>.html (never overwrites an existing page)
  2. puts the photo at the top of photos.json (newest-added first)
Then it rebuilds photos.html, photos_page2.html, photos_page3.html ... from
photos.json + photos_template.html, splitting them per_page photos at a time.

Your existing order is never changed; new photos always go on top.
"""

import argparse
import html
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PHOTOS_DIR = ROOT / "photos"
DATA_FILE = ROOT / "photos.json"
TEMPLATE_FILE = ROOT / "photos_template.html"
EXTENSIONS = {".jpg", ".jpeg"}  # matched case-insensitively

PAGE_WORDS = [
    "ONE", "TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN", "EIGHT", "NINE",
    "TEN", "ELEVEN", "TWELVE", "THIRTEEN", "FOURTEEN", "FIFTEEN", "SIXTEEN",
    "SEVENTEEN", "EIGHTEEN", "NINETEEN", "TWENTY",
]

PHOTO_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Bala Nature Scrapbook</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <meta property="og:title" content="{title} - Bala Nature Scrapbook">
  <meta property="og:description" content="{title}">
  <meta property="og:image" content="https://balanaturescrapbook.com/favicon/apple-touch-icon.png">
  <meta property="og:url" content="https://www.balanaturescrapbook.com">
  <meta property="og:type" content="website">

  <link href="https://fonts.googleapis.com/css2?family=Lora:wght@400;500;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/style.css">

  <link rel="icon" href="/favicon/favicon.ico">
  <link rel="icon" type="image/png" sizes="96x96" href="/favicon/favicon-96x96.png">
  <link rel="apple-touch-icon" href="/favicon/apple-touch-icon.png">
</head>

<body>
  <nav class="navbar">
    <a href="/index.html">About</a>
    <a href="/photos.html">Photos</a>
  </nav>

  <div class="container">

    <h1 class="page-title">{title}</h1>

<div class="feature-image">
  <figure>
    <img src="{image}" alt="{title} photo">

    <div class="image-meta">
      <span class="location">Location</span>
      <span class="date">
        Month <span class="year">YYYY</span>
      </span>
    </div>
  </figure>
</div>

    <div class="photo-details">

      <div class="notes">
        <p><strong>Notes:</strong></p>
        <p class="note-item">* Note</p>

      </div> <!-- .notes -->
    </div> <!-- .photo-details -->

  </div> <!-- .container -->

 

</body>
</html>
"""


# ---------- helpers ----------

def make_title(stem: str) -> str:
    """'soft_strokes' / 'soft-strokes' -> 'Soft Strokes'"""
    return re.sub(r"[_\-]+", " ", stem).strip().title()


def make_slug(stem: str) -> str:
    """'Soft Strokes 2' -> 'soft_strokes_2'"""
    return re.sub(r"[^a-z0-9]+", "_", stem.lower()).strip("_")


def added_time(path: Path) -> float:
    """When the file was added: creation time where the OS records it
    (macOS/Windows), otherwise last-changed time."""
    st = path.stat()
    return getattr(st, "st_birthtime", st.st_ctime)


def image_files() -> list[Path]:
    """Photos sitting directly in photos/ (the thumbnails folder is ignored)."""
    return [
        p for p in PHOTOS_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in EXTENSIONS
    ]


def load_data() -> dict:
    if not DATA_FILE.exists():
        sys.exit(f"Can't find {DATA_FILE.name}")
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def save_data(data: dict) -> None:
    out = ["{", f'  "per_page": {data["per_page"]},']
    if "seen" in data:
        out.append(f'  "seen": {json.dumps(sorted(data["seen"]))},')
    out.append('  "photos": [')
    lines = [f"    {json.dumps(p, ensure_ascii=False)}" for p in data["photos"]]
    out.append(",\n".join(lines))
    out.append("  ]")
    out.append("}")
    DATA_FILE.write_text("\n".join(out) + "\n", encoding="utf-8")


# ---------- gallery rendering ----------

def page_filename(n: int) -> str:
    return "photos.html" if n == 1 else f"photos_page{n}.html"


def page_label(n: int) -> str:
    word = PAGE_WORDS[n - 1] if n <= len(PAGE_WORDS) else str(n)
    return f"PAGE {word}"


def render_gallery(photos: list[dict]) -> str:
    figures = []
    for p in photos:
        figures.append(
            "      <figure>\n"
            f'        <a href="{html.escape(p["page"])}">\n'
            f'          <img src="{html.escape(p["img"])}" alt="{html.escape(p["alt"])}">\n'
            f'          <figcaption>{html.escape(p["caption"])}</figcaption>\n'
            "        </a>\n"
            "      </figure>\n"
        )
    return "\n".join(figures)


def render_pagination(n: int, total: int) -> str:
    if total == 1:
        return ""
    if n > 1:
        left = f'<a class="photo-pagination__previous" href="{page_filename(n - 1)}">TURN BACK</a>'
    else:
        left = '<span aria-hidden="true"></span>'
    if n < total:
        right = f'<a class="photo-pagination__next" href="{page_filename(n + 1)}">TURN PAGE</a>'
    else:
        right = '<span aria-hidden="true"></span>'
    return (
        '    <nav class="photo-pagination" aria-label="Photo pages">\n'
        '      <div class="photo-pagination__row">\n'
        f"        {left}\n"
        f'        <span class="photo-pagination__current">{page_label(n)}</span>\n'
        f"        {right}\n"
        "      </div>\n"
        "    </nav>"
    )


def build_gallery_pages(data: dict) -> None:
    if not TEMPLATE_FILE.exists():
        sys.exit(f"Can't find {TEMPLATE_FILE.name}")
    template = TEMPLATE_FILE.read_text(encoding="utf-8")
    photos = [p for p in data["photos"] if not p.get("hidden")]  # hidden ones are skipped
    per_page = int(data["per_page"])
    total = max(1, math.ceil(len(photos) / per_page))

    for n in range(1, total + 1):
        chunk = photos[(n - 1) * per_page : n * per_page]
        page = (
            template
            .replace("{{GALLERY}}", render_gallery(chunk))
            .replace("{{PAGINATION}}", render_pagination(n, total))
        )
        (ROOT / page_filename(n)).write_text(page, encoding="utf-8")
    # remove leftover pages (e.g. photos_page4.html) if photos were removed/hidden
    for old in ROOT.glob("photos_page*.html"):
        m = re.fullmatch(r"photos_page(\d+)\.html", old.name)
        if m and int(m.group(1)) > total:
            old.unlink()
            print(f"  - removed leftover {old.name}")
    print(f"Rebuilt {total} gallery page(s): "
          + ", ".join(page_filename(n) for n in range(1, total + 1)))


# ---------- main ----------

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", action="store_true",
                        help="mark all photos currently in photos/ as already handled")
    args = parser.parse_args()

    data = load_data()
    names = {p.name for p in image_files()}

    if args.baseline:
        data["seen"] = sorted(names)
        save_data(data)
        print(f"Baseline saved: {len(names)} existing photo(s) marked as handled.")
        return

    if "seen" not in data:
        sys.exit("First time? Run:  python add_photos.py --baseline\n"
                 "(this marks the photos you already have so they aren't re-added)")

    seen = set(data["seen"])
    new_photos = [p for p in image_files() if p.name not in seen]
    new_photos.sort(key=lambda p: (added_time(p), p.name), reverse=True)  # newest first

    new_entries = []
    for photo in new_photos:
        title = make_title(photo.stem)
        slug = make_slug(photo.stem)
        page_path = PHOTOS_DIR / f"{slug}.html"

        if page_path.exists():
            print(f"  ! {page_path.name} already exists - left untouched")
        else:
            page_path.write_text(
                PHOTO_PAGE_TEMPLATE.format(title=html.escape(title), image=photo.name),
                encoding="utf-8",
            )
            print(f"  + created photos/{page_path.name}")

        new_entries.append({
            "page": f"photos/{slug}.html",
            "img": f"photos/{photo.name}",
            "alt": f"{title} photo",
            "caption": title,
        })

    data["photos"] = new_entries + data["photos"]
    data["seen"] = sorted(seen | {p.name for p in new_photos})
    save_data(data)
    build_gallery_pages(data)
    print(f"Added {len(new_entries)} new photo(s).")


if __name__ == "__main__":
    main()
