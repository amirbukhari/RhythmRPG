"""Painterly art generation + cutout, self-contained.

Replaces the v10 pixel pipeline (`tools/pixelart/`) for the production art
path. Three reasons this is a fresh module rather than a patch:

  1. The old chain hard-fails on this environment's Python (3.8): its type
     aliases subscript builtins at runtime (`tuple[int, ...]`), so nothing in
     `tools/pixelart/` imports at all. Every helper here is 3.8-safe.
  2. Its prompt contract is two revisions stale -- `generate_ai.py` still asks
     for "Pixel art ... ordered dithering ... crisp pixels" (the register PRD
     v11.0 retired) and names "a looming Conductor" (the character world-bible
     v16.0 deleted).
  3. `hd_cast.py` asks for "full body SIDE VIEW" art for a game with a
     top-down camera, which is why the cast never sat in the world.

Nothing here quantizes, dithers, outlines or pixelates. Art is generated large
and downsampled with LANCZOS only (PRD §11.1: authored at >=2x its on-screen
size, never upsampled).
"""

from __future__ import annotations

import hashlib
import io
import ssl
import time
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "tools" / "art" / ".cache"

ENDPOINT = "https://image.pollinations.ai/prompt/"


# --------------------------------------------------------------------------
# generation
# --------------------------------------------------------------------------
def generate(prompt, width, height, seed, model="flux", retries=4, cache=True):
    """Fetch one generated image. Cached on disk by (prompt, size, seed) so a
    re-run of a build is free and deterministic -- the review-and-reroll loop
    only pays for slots whose prompt or seed actually changed."""
    key = hashlib.sha256(
        ("%s|%d|%d|%d|%s" % (prompt, width, height, seed, model)).encode("utf-8")
    ).hexdigest()[:24]
    CACHE.mkdir(parents=True, exist_ok=True)
    hit = CACHE / ("%s.png" % key)
    if cache and hit.exists():
        return Image.open(hit).convert("RGBA")

    qs = urllib.parse.urlencode(
        {
            "width": width,
            "height": height,
            "seed": seed,
            "model": model,
            "nologo": "true",
            "private": "true",
        }
    )
    url = ENDPOINT + urllib.parse.quote(prompt, safe="") + "?" + qs
    ctx = ssl.create_default_context()
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "drowned-chorus/1.0"})
            with urllib.request.urlopen(req, timeout=180, context=ctx) as r:
                raw = r.read()
            img = Image.open(io.BytesIO(raw)).convert("RGBA")
            if cache:
                img.save(hit)
            return img
        except Exception as exc:  # transient endpoint failures are the norm
            last = exc
            time.sleep(3 + attempt * 4)
    raise RuntimeError("generation failed after %d tries: %s" % (retries, last))


# --------------------------------------------------------------------------
# cutout: the generator returns JPEG (no alpha) on a flat backdrop
# --------------------------------------------------------------------------
def key_background(img, bg=(255, 255, 255), tol=52, feather=1.0):
    """Alpha-key a flat backdrop by colour distance, flood-filled from the
    border inward so light *inside* the figure (a pale shirt, a lit tool) is
    never punched out -- the failure mode that shredded the old wraith."""
    img = img.convert("RGBA")
    w, h = img.size
    px = img.load()
    br, bg_, bb = bg
    t2 = tol * tol * 3

    def is_bg(x, y):
        r, g, b, _ = px[x, y]
        dr, dg, db = r - br, g - bg_, b - bb
        return dr * dr + dg * dg + db * db <= t2

    # iterative flood from the frame edge (explicit stack: 3.8 recursion limits)
    seen = bytearray(w * h)
    stack = []
    for x in range(w):
        stack.append((x, 0))
        stack.append((x, h - 1))
    for y in range(h):
        stack.append((0, y))
        stack.append((w - 1, y))
    while stack:
        x, y = stack.pop()
        if x < 0 or y < 0 or x >= w or y >= h:
            continue
        i = y * w + x
        if seen[i]:
            continue
        if not is_bg(x, y):
            continue
        seen[i] = 1
        stack.append((x + 1, y))
        stack.append((x - 1, y))
        stack.append((x, y + 1))
        stack.append((x, y - 1))

    mask = Image.new("L", (w, h), 255)
    mp = mask.load()
    for y in range(h):
        row = y * w
        for x in range(w):
            if seen[row + x]:
                mp[x, y] = 0
    if feather:
        mask = mask.filter(ImageFilter.GaussianBlur(feather))
    out = img.copy()
    out.putalpha(mask)
    return out


def largest_island(img, min_alpha=24):
    """Keep only the biggest connected blob -- drops the speckle and stray
    limbs the generator likes to leave floating beside a subject."""
    w, h = img.size
    a = img.split()[3].load()
    label = bytearray(w * h)
    best, best_n = None, 0
    for sy in range(h):
        for sx in range(w):
            i0 = sy * w + sx
            if label[i0] or a[sx, sy] < min_alpha:
                continue
            stack = [(sx, sy)]
            cells = []
            label[i0] = 1
            while stack:
                x, y = stack.pop()
                cells.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h:
                        j = ny * w + nx
                        if not label[j] and a[nx, ny] >= min_alpha:
                            label[j] = 1
                            stack.append((nx, ny))
            if len(cells) > best_n:
                best, best_n = cells, len(cells)
    if not best:
        return img
    keep = Image.new("L", (w, h), 0)
    kp = keep.load()
    for x, y in best:
        kp[x, y] = 255
    out = img.copy()
    out.putalpha(ImageChops.multiply(img.split()[3], keep))
    return out


def autocrop(img, min_alpha=8):
    a = img.split()[3]
    box = a.point(lambda v: 255 if v >= min_alpha else 0).getbbox()
    return img.crop(box) if box else img


def cutout(img, bg=(255, 255, 255), tol=52):
    """Full import: key the backdrop, drop floaters, trim to the figure."""
    return autocrop(largest_island(autocrop(key_background(img, bg=bg, tol=tol))))


# --------------------------------------------------------------------------
# placement
# --------------------------------------------------------------------------
def fit_frame(fig, frame_w, frame_h, figure_h, foot_pad=2):
    """Scale a cutout to an exact figure height and seat its feet on the frame
    baseline, so every character in the game shares one ground line and one
    scale contract (PRD §11.1.2 step 2 -- freeze the rules)."""
    fig = autocrop(fig)
    scale = float(figure_h) / fig.height
    w = max(1, int(round(fig.width * scale)))
    fig = fig.resize((w, figure_h), Image.LANCZOS)
    out = Image.new("RGBA", (frame_w, frame_h), (0, 0, 0, 0))
    baseline = frame_h - foot_pad
    out.alpha_composite(fig, ((frame_w - w) // 2, baseline - figure_h))
    return out


def pack_strip(frames):
    fw, fh = frames[0].size
    sheet = Image.new("RGBA", (fw * len(frames), fh), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        sheet.alpha_composite(f, (i * fw, 0))
    return sheet


def contact_sheet(images, cols=4, cell=(200, 200), bg=(10, 14, 18)):
    """Review grid -- the batch never counts as shipped until it has been
    looked at (PRD §11.1.2 step 5)."""
    cw, ch = cell
    rows = (len(images) + cols - 1) // cols
    out = Image.new("RGB", (cw * cols, ch * max(1, rows)), bg)
    for i, im in enumerate(images):
        im = im.convert("RGBA")
        s = min(float(cw) / im.width, float(ch) / im.height)
        im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
        x = (i % cols) * cw + (cw - im.width) // 2
        y = (i // cols) * ch + (ch - im.height) // 2
        out.paste(im, (x, y), im)
    return out
