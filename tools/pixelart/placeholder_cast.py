"""Placeholder cast (PRD v11.2 purge): the owner threw out ALL AI-generated
sprite art -- "throw out anything that generated art that isn't the
grass/water/ground/path/boss ground areas". The painted ground plate stays;
every figure is replaced by a deliberately minimal, code-drawn glow-shape
(HLD-prototype register: soft dark silhouette + one accent) at the SAME
sheet dimensions and paths as the HD cast, so no engine contract changes:

    band/mir/{idle,run,attack}.png     200x200 frames
    enemies/slime.png                  128x128 x2
    enemies/drifter.png                140x140 x2
    enemies/elite_wraith.png           180x180 x2
    enemies/the_conductor.png          192x192 x2
    enemies/conductor_colossal.png     208x288 x2
    env/shared/save_obelisk.png        29x38 (functional save point)

Accents mirror the runtime FOE_ACCENT glows so auras and bodies agree.
Deterministic; run any time. Real character art drops back into the same
slots when a direction is chosen (hd_cast.py remains the generator).
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).parent))
from hd_cast import attack_frames, breathe, pack, run_frames  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]

INK = (16, 20, 32, 255)  # silhouette body
ACCENT = {
    "mir": (73, 198, 189),  # teal (player glow)
    "slime": (154, 202, 67),
    "drifter": (159, 232, 224),
    "elite_wraith": (73, 198, 189),
    "the_conductor": (240, 166, 72),
    "conductor_colossal": (240, 166, 72),
}
SS = 4  # supersample factor for smooth edges


def _canvas(w: int, h: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def _finish(im: Image.Image, w: int, h: int) -> Image.Image:
    return im.resize((w, h), Image.LANCZOS)


def _core(d: ImageDraw.ImageDraw, box: tuple[float, float, float, float], rgb: tuple[int, int, int]) -> None:
    """A soft luminous core: bright ellipse over a wider dim halo."""
    x0, y0, x1, y1 = box
    pad = (x1 - x0) * 0.45
    d.ellipse((x0 - pad, y0 - pad, x1 + pad, y1 + pad), fill=rgb + (70,))
    d.ellipse(box, fill=rgb + (235,))


def figure_humanoid(w: int, h: int, fig_h: int, accent: tuple[int, int, int],
                    hat: bool = False, guitar: bool = False) -> Image.Image:
    """A slim standing silhouette, feet at the bottom margin, facing left."""
    im, d = _canvas(w, h)
    W, H = w * SS, h * SS
    fh = fig_h * SS
    foot = H - max(2, H // 50)
    cx = W / 2
    head_r = fh * 0.085
    head_cy = foot - fh + head_r * 1.6
    body_w = fh * 0.22
    # body capsule (shoulders to feet)
    d.rounded_rectangle((cx - body_w / 2, head_cy + head_r * 1.2, cx + body_w / 2, foot), radius=body_w / 2, fill=INK)
    d.ellipse((cx - head_r, head_cy - head_r, cx + head_r, head_cy + head_r), fill=INK)
    if hat:
        brim = body_w * 1.15
        d.rectangle((cx - brim / 2, head_cy - head_r * 1.35, cx + brim / 2, head_cy - head_r * 0.9), fill=INK)
        d.rectangle((cx - head_r * 0.85, head_cy - head_r * 3.4, cx + head_r * 0.85, head_cy - head_r * 1.2), fill=INK)
    # accent core at the chest
    chest_y = head_cy + head_r * 2.6
    r = body_w * 0.32
    _core(d, (cx - r, chest_y - r, cx + r, chest_y + r), accent)
    if guitar:
        # a coral-red diagonal slab across the hip -- the guitar silhouette
        gr = (255, 94, 80)
        hip_y = foot - fh * 0.42
        d.line((cx - body_w * 1.35, hip_y + body_w * 0.7, cx + body_w * 1.1, hip_y - body_w * 0.7), fill=gr + (235,), width=int(body_w * 0.34))
    return _finish(im, w, h)


def figure_mound(w: int, h: int, fig_h: int, accent: tuple[int, int, int]) -> Image.Image:
    """The slime: a wide soft mound with a luminous core."""
    im, d = _canvas(w, h)
    W, H = w * SS, h * SS
    fh = fig_h * SS
    foot = H - max(2, H // 50)
    cx = W / 2
    mw = fh * 1.15
    d.ellipse((cx - mw / 2, foot - fh, cx + mw / 2, foot + fh * 0.28), fill=INK)
    r = fh * 0.2
    _core(d, (cx - r, foot - fh * 0.55 - r, cx + r, foot - fh * 0.55 + r), accent)
    return _finish(im, w, h)


def figure_shard(w: int, h: int, fig_h: int, accent: tuple[int, int, int]) -> Image.Image:
    """The wraith: a tall tapered flame/shard."""
    im, d = _canvas(w, h)
    W, H = w * SS, h * SS
    fh = fig_h * SS
    foot = H - max(2, H // 50)
    cx = W / 2
    bw = fh * 0.36
    d.polygon([(cx, foot - fh), (cx + bw / 2, foot - fh * 0.35), (cx + bw * 0.38, foot), (cx - bw * 0.38, foot), (cx - bw / 2, foot - fh * 0.35)], fill=INK)
    r = fh * 0.09
    _core(d, (cx - r, foot - fh * 0.72 - r, cx + r, foot - fh * 0.72 + r), accent)
    return _finish(im, w, h)


def figure_hood(w: int, h: int, fig_h: int, accent: tuple[int, int, int]) -> Image.Image:
    """The drifter: a hooded teardrop."""
    im, d = _canvas(w, h)
    W, H = w * SS, h * SS
    fh = fig_h * SS
    foot = H - max(2, H // 50)
    cx = W / 2
    bw = fh * 0.5
    d.pieslice((cx - bw / 2, foot - fh, cx + bw / 2, foot - fh + bw), 180, 360, fill=INK)
    d.polygon([(cx - bw / 2, foot - fh + bw / 2), (cx + bw / 2, foot - fh + bw / 2), (cx + bw * 0.36, foot), (cx - bw * 0.36, foot)], fill=INK)
    r = fh * 0.075
    _core(d, (cx - r, foot - fh * 0.78 - r, cx + r, foot - fh * 0.78 + r), accent)
    return _finish(im, w, h)


def obelisk(w: int = 29, h: int = 38) -> Image.Image:
    im, d = _canvas(w, h)
    W, H = w * SS, h * SS
    cx = W / 2
    d.rounded_rectangle((cx - W * 0.19, H * 0.08, cx + W * 0.19, H * 0.98), radius=W * 0.12, fill=(58, 66, 84, 255))
    d.rounded_rectangle((cx - W * 0.045, H * 0.2, cx + W * 0.045, H * 0.62), radius=W * 0.04, fill=(73, 198, 189, 230))
    return _finish(im, w, h)


def main() -> None:
    # Mir: strips derive from the base pose exactly like the real cast did.
    fig_h = 176
    base = figure_humanoid(200, 200, fig_h, ACCENT["mir"], guitar=True)
    out = ROOT / "assets/sprites/band/mir"
    out.mkdir(parents=True, exist_ok=True)
    pack([base, breathe(base, fig_h)]).save(out / "idle.png")
    pack(run_frames(base, fig_h)).save(out / "run.png")
    pack(attack_frames(base, fig_h)).save(out / "attack.png")

    foes = {
        "slime": (figure_mound, 128, 128, 104),
        "drifter": (figure_hood, 140, 140, 122),
        "elite_wraith": (figure_shard, 180, 180, 158),
        "the_conductor": (lambda w, h, f, a: figure_humanoid(w, h, f, a, hat=True), 192, 192, 170),
        "conductor_colossal": (lambda w, h, f, a: figure_humanoid(w, h, f, a, hat=True), 208, 288, 272),
    }
    enemies = ROOT / "assets/sprites/enemies"
    enemies.mkdir(parents=True, exist_ok=True)
    for name, (fn, w, h, f) in foes.items():
        b = fn(w, h, f, ACCENT[name])
        pack([b, breathe(b, f)]).save(enemies / f"{name}.png")

    shared = ROOT / "assets/sprites/env/shared"
    shared.mkdir(parents=True, exist_ok=True)
    obelisk().save(shared / "save_obelisk.png")
    print("placeholder cast written (mir strips, 5 foe sheets, obelisk)")


if __name__ == "__main__":
    main()
