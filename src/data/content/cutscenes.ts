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
  | "litho" // the stone child: an infant's face with no breath behind it
  | "fold" // the drowned town, silt and prayer-rings
  | "house" // the clock-keeper's room -- where the argument does not happen
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
        "Nobody remembers arriving. Nobody finds that strange -- it happened to all of us, so there is no one left to compare it with.",
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
        "The plaza empties the way it always does after a rule. Quietly, and in good order, and without anyone looking at us.",
      ],
    },
    {
      stage: "house",
      lines: [
        "At home Nari is asleep, and neither of us wakes him.",
        "Lunal does not ask me what I am going to do. I do not ask her.",
        "She puts her coat on and goes out to arrange something she does not explain. I sit down and start lacing my boots.",
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
        "If the rule cannot reach past the water, then past the water is where we are going.",
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

// The Den (world-bible §9 beat 5): the end of the Scar. Every track led here,
// and Mir came ready for the beast that made them. He finds a man instead -- the
// Harrow, who has dug this whole waste for longer than tools last, sorting the
// small things the ground gives up, still cutting a child's height into his
// doorpost every morning for a child who is not there. He is what Mir becomes if
// he keeps searching for a monster. The line the finale depends on: "Nothing up
// here took your boy." Fires once, when the den's mouth (node_19) is cleared.
const THE_DEN: Cutscene = {
  id: "the_den",
  flag: "seen_den",
  frames: [
    {
      stage: "scar",
      lines: [
        "Every track in the Scar leads to this one doorway, and not one of them leads back out of it. I came ready for the thing that dug them.",
        "There is no thing. There is a lamp, and a man, and he does not look up when I come in.",
      ],
    },
    {
      stage: "scar",
      lines: [
        "He has worked this waste longer than his tools last, and they do not last -- worn to the socket, a hundred of them, sorted by how much is left.",
        "Beside him, laid out on cloth, is everything small the ground gave up. A shoe. A comb. Bones too little to be anyone grown. None of it thrown away. All of it kept.",
      ],
    },
    {
      stage: "scar",
      tint: 0xc25424,
      lines: [
        "Two marks are cut in his doorpost -- one tall, one small -- fresh over old, so many times the wood is worn hollow. He measures a child who is not here.",
        '"Nothing up here took your boy," he says, the way you would tell a man the time.',
        "I look at his hands. They are mine. I make myself not believe him. I still have somewhere to be.",
      ],
    },
  ],
};

// The Sitting-Down (world-bible §9 beat 6): leaving the Scar, alone, finally
// reading his own evidence -- "no fight music for a while". This is the beat the
// retired story never had: the reveal happening to MIR, not just the player. No
// blood anywhere; prints set down gently; and beside the small ones, always, a
// woman's stride, leading not chasing. He lets the name he has been outrunning
// arrive. Fires on stepping into the Keep's region, once he has met the Harrow.
const THE_SITTING_DOWN: Cutscene = {
  id: "the_sitting_down",
  flag: "seen_sitting",
  frames: [
    {
      stage: "scar",
      lines: [
        "A mile out of the den my legs stop, and I sit down in the dirt where there is no one to see it, and I let myself read the ground the way it has been the whole time.",
      ],
    },
    {
      stage: "scar",
      lines: [
        "No blood. Not once, not anywhere, the entire way up. Small prints set down soft, one at a time -- the tread of something carried and set down to rest, not something that ran.",
        "And beside them at every stretch, the same second stride. Grown. Stopping each time the small one strayed. Waiting for it. Not chasing it. Walking it somewhere.",
      ],
    },
    {
      stage: "black",
      tint: 0x2a4650,
      lines: [
        "A woman's stride. Gone out the night the rule was read; back by morning with mud on her boots from somewhere there is no mud.",
        "I have hunted a monster the length of a world to keep from having to say her name.",
        "Lunal.",
      ],
    },
  ],
};

export const CUTSCENES: Cutscene[] = [RITE, LEAVING, TAKEN, THE_DEN, THE_SITTING_DOWN];

export function cutsceneById(id: string): Cutscene | undefined {
  return CUTSCENES.find((c) => c.id === id);
}
