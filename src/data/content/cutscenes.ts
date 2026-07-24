// Scripted story beats -- "cutscenes" (owner: "we also need cutscenes").
//
// The Drowned Chorus is a minimal-text, "found not told" world (world-bible
// §"How the story is told"), so these are deliberately spare: a handful of
// staged lines over a simple composed visual, in the same voice as the echoes
// and the finale. They are the few moments the game DOES tell you something
// outright -- the ones the environment can't carry alone.
//
// The CutsceneScene renders each frame's `lines` fading in over a `stage`
// composition it knows how to draw (no per-scene art needed -- everything is
// procedural glow/shape, matching the v11.2 register). Cutscenes fire once at
// story beats and set a save flag so they never replay.

export type StageKind =
  | "black" // empty dark field
  | "obelisk" // the Fold monolith, its crown-light pulsing
  | "litho" // a small baby-shaped stone idol, lit from within
  | "fold" // the drowned town, silt and prayer-rings
  | "waterline" // the Breach seam: dark water below, pale sky above
  | "scar" // the hostile surface, scorched and clawed
  | "rain"; // rain far above, seen from below -- the ending register

export interface CutsceneFrame {
  /** One or more lines, revealed one after another. */
  lines: string[];
  /** The composed backdrop the CutsceneScene draws behind the lines. */
  stage: StageKind;
  /** Optional accent tint for the stage glow (defaults per stage). */
  tint?: number;
}

export interface Cutscene {
  id: string;
  /** Save flag set once this plays, so it never repeats. */
  flag: string;
  frames: CutsceneFrame[];
}

// The marquee beat: the Rite. This seats the entire premise -- the obelisk's
// yearly rule, the litho, and the sentence it passes on Nari -- BEFORE the
// player ever leaves the Fold. Plays once, at the very start of a new game.
const RITE: Cutscene = {
  id: "rite_opening",
  flag: "seen_rite",
  frames: [
    {
      stage: "fold",
      lines: [
        "We woke on the ocean floor, and the obelisk was already there.",
        "Already listening. We have prayed to it for as long as anyone remembers -- which is not long. It does not let us remember.",
      ],
    },
    {
      stage: "obelisk",
      lines: [
        "Once a year, the stone opens.",
        "And once a year, it gives us a new rule to live by. We have never once refused one.",
      ],
    },
    {
      stage: "litho",
      lines: [
        "This year, the thing that comes out has the face of a child.",
        "It has no breath behind it. When its mouth opens, the whole Fold goes still.",
      ],
    },
    {
      stage: "litho",
      tint: 0xc25424,
      lines: [
        '"The unnamed voice," it says, "is owed to the deep."',
        "It is a general rule. It could mean anyone. We all know at once whose small voice it means.",
      ],
    },
    {
      stage: "fold",
      lines: [
        "Lunal asks where a thing could be hidden that the song could not find.",
        "I do not answer her. I am already reaching for my boots.",
        "No one leaves the Fold. Tonight I am going to carry my son up out of it.",
      ],
    },
  ],
};

// Leaving the Fold -- the threshold. (The overworld already fires a small
// toast here; this is its cutscene upgrade, played the first time Mir steps
// out of region 0.)
const LEAVING: Cutscene = {
  id: "leaving_fold",
  flag: "seen_leaving",
  frames: [
    {
      stage: "fold",
      tint: 0x49c6bd,
      lines: [
        "Nari walks behind me the way he always has -- for no reason but that his father is walking.",
        "Behind us, the prayer-lamps. Ahead, only up.",
      ],
    },
    {
      stage: "waterline",
      lines: [
        "The wrecks all point the same way. Every ship that ever sank down here points up.",
        "If the surface is where the rule can't reach, then the surface is where we're going. The chorus begins.",
      ],
    },
  ],
};

// The Breach: the taking. Fires on Mir's first step onto the surface -- the
// same beat as the "NARI?" toast, but staged.
const TAKEN: Cutscene = {
  id: "nari_taken",
  flag: "seen_taken",
  frames: [
    {
      stage: "waterline",
      lines: [
        "The air burns going in. The first breath is fire; the second is his name.",
        "For one measure -- one -- I turn to look at the sky.",
      ],
    },
    {
      stage: "scar",
      tint: 0xc25424,
      lines: [
        "When I turn back, the scuffle in the mud is two feet, then one, then none.",
        "He did not cry out. Whatever lifted him, he was not afraid of it.",
        "NARI. He was right behind me.",
      ],
    },
  ],
};

export const CUTSCENES: Cutscene[] = [RITE, LEAVING, TAKEN];

export function cutsceneById(id: string): Cutscene | undefined {
  return CUTSCENES.find((c) => c.id === id);
}
