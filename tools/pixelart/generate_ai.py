"""Generate the game's art via an image-gen API, then import it into the
engine slot -- fully automated, run from inside this environment.

I (Claude Code) cannot synthesize images myself, but the sandbox proxy reaches
the image-gen APIs, so with ONE API key in the environment this script does the
whole loop for each asset: build the prompt (global style block + palette + the
per-slot prompt from docs/design/art-prompts.md) -> call the API -> save the raw
PNG -> run it through import_asset.py (palette-quantize, key background,
downscale, slice frames) -> write the engine-ready asset into assets/.

Providers:
  pollinations          (KEYLESS, free -- the default; Flux-based, no key needed)
  REPLICATE_API_TOKEN   (pixel-art models, pay-per-use)
  OPENAI_API_KEY        (gpt-image-1)
  STABILITY_API_KEY     (stable-image core)

Usage:
  # one asset:
  python3 generate_ai.py --provider openai \
      --prompt "$(cat prompt.txt)" --out assets/sprites/enemies/slime/idle.png \
      --frame 48x48 --frames 2
  # batch from a manifest (list of {out, prompt, frame, frames|grid, key, opaque}):
  python3 generate_ai.py --provider replicate --batch slots.json
  # see the exact API call without a key / without spending:
  python3 generate_ai.py --provider openai --prompt "test" --out /tmp/x.png --frame 48x48 --dry-run
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import ssl
import time
import urllib.request
from pathlib import Path

import import_asset as I

# Prepended to every prompt so all output shares the world + palette (mirrors
# the Global Style Block + master palette in docs/design/art-prompts.md).
STYLE_PREFIX = (
    "Pixel art, Hyper Light Drifter / Blasphemous register, beautiful moody gothic. "
    "World: 'The Drowned Chorus' -- drowned/gothic, ocean-floor abyss, salt and rust, "
    "melting black clocks, bone and pearl, blood, rot-green, a looming Conductor. "
    "Dark near-black base values with searing accents: abyssal teal, plum/magenta, "
    "ember-gold, blood red. Strong readable silhouettes, top-left light, limited palette, "
    "ordered dithering (no gradients, no blur, no text, no watermark), crisp pixels. "
)
PALETTE_HINT = (
    "Use only these colours: #05060a #0f111a #1c1f2b #f4efe2 #d8ceb6 #a89d84 #e07030 "
    "#a8431c #f0a648 #f4d27a #c22f34 #7d1b20 #49c6bd #1f6f77 #153a52 #79b855 #426e33 "
    "#8a52a0 #4b2a57 #b98fca #dcae86 #ad7552 #97a2ae #586470. "
)
# For cutout sprites the world/scene prefix makes the model paint a SCENE (it
# even adds clocks). A minimal prefix + hard isolation gives a clean subject on
# a plain white backdrop that flood_key() removes cleanly.
SPRITE_PREFIX = (
    "simple 8-bit pixel art game sprite, single subject, bold thick black outline, "
    "flat limited gothic palette, dark moody colours, centered, full body, "
    "ISOLATED on a plain solid WHITE background, no scenery, no environment, "
    "no background details, no ground, no shadow. Subject: "
)

CA_BUNDLE = os.environ.get("SSL_CERT_FILE") or "/root/.ccr/ca-bundle.crt"


def _opener() -> urllib.request.OpenerDirector:
    """Proxy- and CA-aware opener (the sandbox routes HTTPS through a proxy
    with its own CA)."""
    ctx = ssl.create_default_context()
    if Path(CA_BUNDLE).exists():
        try:
            ctx.load_verify_locations(CA_BUNDLE)
        except Exception:
            pass
    handlers: list[urllib.request.BaseHandler] = [urllib.request.HTTPSHandler(context=ctx)]
    proxies = urllib.request.getproxies()
    if proxies:
        handlers.append(urllib.request.ProxyHandler(proxies))
    return urllib.request.build_opener(*handlers)


_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"


def _post(url: str, headers: dict[str, str], body: bytes, timeout: int = 180) -> bytes:
    headers = {"User-Agent": _UA, "Accept": "*/*", **headers}
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with _opener().open(req, timeout=timeout) as r:
        return r.read()


def _get(url: str, headers: dict[str, str], timeout: int = 60) -> bytes:
    headers = {"User-Agent": _UA, "Accept": "*/*", **headers}
    req = urllib.request.Request(url, headers=headers, method="GET")
    with _opener().open(req, timeout=timeout) as r:
        return r.read()


def _aspect(w: int, h: int) -> str:
    from math import gcd
    g = gcd(w, h) or 1
    return f"{w // g}:{h // g}"


# --- provider adapters: each returns raw image bytes for a prompt at ~w×h ---

def gen_pollinations(prompt: str, w: int, h: int, seed: int = 0, model: str = "flux") -> bytes:
    """Keyless, free (Flux). GET with the prompt in the path + size params."""
    import urllib.parse
    q = urllib.parse.quote(prompt, safe="")
    url = (f"https://image.pollinations.ai/prompt/{q}"
           f"?width={w}&height={h}&nologo=true&model={model}&seed={seed}")
    return _get(url, {}, timeout=180)


def gen_openai(prompt: str, w: int, h: int) -> bytes:
    key = os.environ["OPENAI_API_KEY"]
    # gpt-image-1 supports 1024x1024 / 1024x1536 / 1536x1024; pick nearest orientation
    size = "1024x1024" if abs(w - h) < 64 else ("1536x1024" if w > h else "1024x1536")
    body = json.dumps({"model": "gpt-image-1", "prompt": prompt, "size": size, "n": 1}).encode()
    hdr = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    resp = json.loads(_post("https://api.openai.com/v1/images/generations", hdr, body))
    return base64.b64decode(resp["data"][0]["b64_json"])


def gen_stability(prompt: str, w: int, h: int) -> bytes:
    key = os.environ["STABILITY_API_KEY"]
    # multipart/form-data with only text fields; boundary hand-built (stdlib only)
    b = "----drownedchorus"
    parts = []
    for k, v in (("prompt", prompt), ("output_format", "png"), ("aspect_ratio", _aspect(w, h))):
        parts.append(f"--{b}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n")
    payload = ("".join(parts) + f"--{b}--\r\n").encode()
    hdr = {"Authorization": f"Bearer {key}", "Accept": "image/*", "Content-Type": f"multipart/form-data; boundary={b}"}
    return _post("https://api.stability.ai/v2beta/stable-image/generate/core", hdr, payload)


def gen_replicate(prompt: str, w: int, h: int, model: str = "black-forest-labs/flux-schnell") -> bytes:
    key = os.environ["REPLICATE_API_TOKEN"]
    hdr = {"Authorization": f"Bearer {key}", "Content-Type": "application/json", "Prefer": "wait"}
    body = json.dumps({"input": {"prompt": prompt, "aspect_ratio": _aspect(w, h), "output_format": "png"}}).encode()
    resp = json.loads(_post(f"https://api.replicate.com/v1/models/{model}/predictions", hdr, body))
    # with Prefer: wait the prediction usually returns completed; else poll
    for _ in range(60):
        if resp.get("status") in ("succeeded", "failed", "canceled"):
            break
        time.sleep(2)
        resp = json.loads(_get(resp["urls"]["get"], {"Authorization": f"Bearer {key}"}))
    if resp.get("status") != "succeeded":
        raise RuntimeError(f"replicate: {resp.get('status')}: {resp.get('error')}")
    out = resp["output"]
    img_url = out[0] if isinstance(out, list) else out
    return _get(img_url, {})


PROVIDERS = {"pollinations": gen_pollinations, "openai": gen_openai, "stability": gen_stability, "replicate": gen_replicate}
KEY_ENV = {"pollinations": None, "openai": "OPENAI_API_KEY", "stability": "STABILITY_API_KEY", "replicate": "REPLICATE_API_TOKEN"}
# what resolution to ask the API for per asset kind (bigger = more detail, then downscaled)
GEN_SIZE = {"background": (1280, 720), "boss": (768, 1024), "sprite": (768, 768), "tile": (1024, 1024), "piece": (768, 768)}


def full_prompt(p: str, kind: str = "sprite") -> str:
    if kind in ("sprite", "boss", "piece"):
        return SPRITE_PREFIX + p
    return STYLE_PREFIX + PALETTE_HINT + p


def _parse_size(s: str) -> tuple[int, int]:
    w, h = s.lower().split("x")
    return int(w), int(h)


def one(provider: str, prompt: str, out: str, frame: str, *, frames: int = 1, grid: str | None = None,
        key: str | None = None, opaque: bool = False, kind: str = "sprite", quantize: bool = True,
        seed: int = 0, dry_run: bool = False, keep_raw: str | None = None) -> None:
    fw, fh = _parse_size(frame)
    cols, rows = (_parse_size(grid) if grid else (frames, 1))
    gw, gh = GEN_SIZE.get(kind, (768, 768))
    fp = full_prompt(prompt, kind)
    if dry_run:
        print(f"[dry-run] {provider}@{gw}x{gh} -> import -> {out} "
              f"({fw}x{fh}, {cols*rows} frame(s), {'opaque' if opaque else 'keyed'}, "
              f"{'quantized' if quantize else 'full-colour'})")
        print(f"  prompt: {fp[:150]}...")
        return
    keyenv = KEY_ENV[provider]
    if keyenv and keyenv not in os.environ:
        raise SystemExit(f"missing {keyenv} in environment")
    fn = PROVIDERS[provider]
    raw = fn(fp, gw, gh, seed) if provider == "pollinations" else fn(fp, gw, gh)
    raw_path = Path(keep_raw) if keep_raw else Path("/tmp") / (Path(out).stem + "_raw.png")
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_bytes(raw)
    from PIL import Image
    if kind == "background":
        # Hyper Light Drifter register: detailed pixel art, NOT chunky muddy
        # 8-bit. Quantize at native res to a rich ADAPTIVE palette with no
        # dither -- keeps vivid colour + fine detail, reads as crisp pixel art
        # at the game's 3x display scale.
        img = I.pixelate(Image.open(raw_path), fw, fh, colors=96, dither=False)
    elif kind in ("sprite", "boss", "piece"):
        # cutout on a plain white backdrop -> flood-remove the background, then
        # pixelate the subject to the frame size. Characters (sprite/boss) snap
        # to the master palette for cast cohesion; environment `piece`s keep a
        # rich adaptive palette (HLD detail) so kitbashed scenes stay vivid.
        keyed = I.flood_key(Image.open(raw_path), tol=80)
        one_frame = I.pixelate(keyed, fw, fh, dither=False, colors=(64 if kind == "piece" else None))
        img = one_frame if (cols * rows) <= 1 else I.pack_strip([one_frame] * (cols * rows), fw, fh)
    else:
        img = I.import_asset(raw_path, fw, fh, cols=cols, rows=rows,
                             do_quantize=quantize, do_key=not opaque, key_color=key)
    dst = Path(out)
    dst.parent.mkdir(parents=True, exist_ok=True)
    img.save(dst)
    print(f"generated + imported -> {dst} ({img.width}x{img.height})")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", choices=list(PROVIDERS), required=True)
    ap.add_argument("--prompt")
    ap.add_argument("--out")
    ap.add_argument("--frame", default="48x48")
    ap.add_argument("--frames", type=int, default=1)
    ap.add_argument("--grid")
    ap.add_argument("--key")
    ap.add_argument("--opaque", action="store_true")
    ap.add_argument("--batch", help="JSON file: list of slot dicts")
    ap.add_argument("--kind", default="sprite", choices=list(GEN_SIZE))
    ap.add_argument("--no-quantize", action="store_true")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="cap batch size (for a cheap test run)")
    a = ap.parse_args()

    if a.batch:
        slots = json.loads(Path(a.batch).read_text())
        if a.limit:
            slots = slots[: a.limit]
        for s in slots:
            one(a.provider, s["prompt"], s["out"], s.get("frame", "48x48"),
                frames=s.get("frames", 1), grid=s.get("grid"), key=s.get("key"),
                opaque=s.get("opaque", False), kind=s.get("kind", "sprite"),
                quantize=not s.get("no_quantize", False), seed=s.get("seed", 0),
                dry_run=a.dry_run)
    else:
        if not (a.prompt and a.out):
            raise SystemExit("need --prompt and --out (or --batch)")
        one(a.provider, a.prompt, a.out, a.frame, frames=a.frames, grid=a.grid,
            key=a.key, opaque=a.opaque, dry_run=a.dry_run)


if __name__ == "__main__":
    main()
