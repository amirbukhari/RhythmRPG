"""The dilution probe -- the measurement the whole generated-art pipeline rests on.

    python3 tools/art/probe_dilution.py

WHAT IT MEASURES
Whether a clause at the END of a prompt still reaches the image as the prompt
gets longer. One fixed subject sentence, one fixed seed, one fixed size; the
only variable is how much bland filler is inserted before the final clause.

THE RESULT (2026-08, flux via Pollinations, seed 8842, 512x288)

    162 chars   the lemon tree is THERE
    587 chars   the lemon tree is GONE
   1012 chars   gone
   1522 chars   gone

The filler says nothing that contradicts the tree. It does not push it out of
the frame, it just thins the signal until the clause stops arriving at all.

WHY IT MATTERS
This is dilution, not truncation. There is no token cliff to sit under -- the
degradation is gradual and total, and it starts early. Two consequences, both
now enforced in `plates.py`:

  1. A long "cinematic painterly atmospheric" style preamble does not add style,
     it DELETES SUBJECT MATTER. `contract.RENDER + LIGHT + PALETTE + WORLD` is
     ~1000 characters of precisely the filler measured here.
  2. Prompts get a hard character budget, canon-critical facts first, asserted at
     build time. If a prompt needs more, something else gets cut.

It also reframes two of the character probes recorded in
docs/design/style-contract.md §1 ("full body is ignored half the time", "the
combination cannot hold at once"): those prompts were >1500 characters, so they
were being diluted, not refused. The authored-rig decision does not rest on
them -- it rests on identity across 22 states, real animation, and silhouette
readability at 22 world pixels, none of which a generator provides at any prompt
length -- but the probes should not be cited as evidence of a hard model limit.

A NOTE ON THE FIRST VERSION OF THIS PROBE
It asked for "The chair is BRIGHT GREEN, not red." after establishing a red
chair, and the chair stayed red at EVERY length including 131 characters. That
measured contradiction-handling (diffusion models resolve a negated override by
ignoring it), not dilution. A probe whose control case already fails measures
nothing. Hence the neutral, additive subject used here.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gen  # noqa: E402

BASE = "An empty room with plain white walls and a wooden floor, photographed straight on. "
FILLER = "The room is quiet and the light is soft and the air is still and nothing moves here. "
# Additive and non-conflicting: nothing earlier in the prompt denies a tree.
TAIL = "A large potted lemon tree in a terracotta pot stands in the centre of the room."
SEED = 8842
PADS = (0, 5, 10, 16)


def main():
    out = Path(__file__).resolve().parent / ".probe"
    out.mkdir(exist_ok=True)
    imgs = []
    for pad in PADS:
        p = BASE + FILLER * pad + TAIL
        imgs.append(gen.generate(p, 512, 288, SEED))
        print("%5d chars (~%3d tokens)" % (len(p), len(p) // 4))
    sheet = out / "dilution.png"
    gen.contact_sheet(imgs, cols=2, cell=(512, 288)).save(sheet)
    print("\nreading order is left-to-right, top-to-bottom -> %s" % sheet)
    print("the tree should be visible in the first cell and absent in the rest.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
