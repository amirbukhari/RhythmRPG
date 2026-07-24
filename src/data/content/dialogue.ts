// Talkable NPCs (owner: "fill the game with NPCs that we can talk to and move
// the story and side stories forward").
//
// The Fold is a town, so it is a town of PEOPLE -- most NPCs stand in the
// drowned village, combat-free, and the game's premise (the Rite, the rule,
// Lunal, Nari) is carried through what they say. A few drowned souls are met
// on the climb. Dialogue REACTS to story state: each NPC has ordered `beats`,
// and the first beat whose `requires` flag is satisfied is the one that plays,
// so the same person says something different before you leave, after you've
// left, and after Nari is taken.
//
// Flags available to `requires`: "leftFold" (Mir has stepped out of the Fold),
// "nariLost" (taken on the surface), "cleared:<nodeId>" (a fight won), plus any
// flag a beat `sets` (persisted in SaveProfile.storyFlags). A beat with no
// `requires` is the default and MUST come last.

export type NpcLook = "elder" | "woman" | "man" | "child" | "pilgrim" | "hooded";

export interface DialogueBeat {
  /** Flag that must be set for this beat to be eligible. Omit for the default. */
  requires?: string;
  /** Flag set when this beat finishes (one-way; for side-story progress). */
  sets?: string;
  /** Lines revealed one at a time; advance/close with E. */
  lines: string[];
}

export interface NpcDef {
  id: string;
  name: string;
  col: number;
  row: number;
  look: NpcLook;
  beats: DialogueBeat[];
}

// --- The Fold (the drowned town) -- main story + side stories ---------------
export const NPCS: NpcDef[] = [
  {
    id: "cantor",
    name: "The Cantor",
    col: 23,
    row: 177,
    look: "elder",
    beats: [
      {
        requires: "nariLost",
        lines: [
          "You went up. No one goes up.",
          "And you came back down without him. Of course you did. The rule is the rule; the deep is owed its voice.",
          "Kneel with me. The obelisk forgives even this. It will let you forget him, if you ask. That is its mercy.",
          "...No? Then go back up, heretic, and be the one thing down here that still refuses.",
        ],
      },
      {
        requires: "leftFold",
        lines: [
          "You're still here? I felt the water change when you crossed the town line.",
          "Every rule we were ever given, we obeyed. That is what a Fold is: a thing that folds. You did not fold.",
          "I should be afraid of you. Instead I find I am praying you make it.",
        ],
      },
      {
        sets: "met_cantor",
        lines: [
          "Kneel, child. The stone opened this morning; a rule has been given.",
          "It has always been this way. We wake on the floor, we pray, once a year a rule is added, and we are grateful.",
          "You are looking at me as though the rule were a cruelty. It is an ORDER. There is a difference, and forgetting it is the only sin down here.",
          "Go home to your wife and your son. Obey, and be at peace.",
        ],
      },
    ],
  },
  {
    id: "meret",
    name: "Meret, a mother",
    col: 19,
    row: 171,
    look: "woman",
    beats: [
      {
        requires: "nariLost",
        lines: [
          "You're back. And your arms are empty.",
          "I lost mine three rules ago. The deep was owed a voice, and hers was the youngest that year.",
          "I have envied you all day -- that you RAN. Go and un-empty your arms. Do the thing I was too folded to do.",
        ],
      },
      {
        sets: "met_meret",
        lines: [
          "You heard it too, then. 'The unnamed voice is owed to the deep.'",
          "They'll say it means any child. It doesn't. It means the youngest that hasn't been given a place in the song yet.",
          "It means your Nari.",
          "...Don't kneel about it. Do something the rest of us never could.",
        ],
      },
    ],
  },
  {
    id: "doubter",
    name: "Ath, who counts",
    col: 26,
    row: 161,
    look: "man",
    beats: [
      {
        requires: "leftFold",
        lines: [
          "You did it. You walked out. I have stood at the town line a thousand times and never once put a foot past it.",
          "Tell me what's up there. Tell me the light is real.",
        ],
      },
      {
        sets: "met_doubter",
        lines: [
          "Nobody leaves. It isn't a law -- I've read every rule, all of them, and leaving isn't forbidden.",
          "It's just that to leave, you'd have to admit there's an UP. And an up means we fell. And falling means... we're not saved. We drowned.",
          "I count the rules to keep from thinking about that. I'm up to a number I can't say out loud.",
        ],
      },
    ],
  },
  {
    id: "sella",
    name: "Sella, the baker's daughter",
    col: 16,
    row: 155,
    look: "woman",
    beats: [
      {
        requires: "met_sella",
        lines: [
          "You came back to hear the rest. Most people don't.",
          "I cut every mooring on the green before the water took us. Every boat but mine -- I was going to be last, you see. Noble.",
          "My rope ran out. That's the whole story. The one time being last mattered, I ran out of rope being last.",
          "If you find your boy: don't be noble. Be FAST.",
        ],
      },
      {
        sets: "met_sella",
        lines: [
          "You're the one leaving. Word travels, even down here.",
          "See the boat still straining at its line above the green? That one's mine. I never got in it.",
          "...Come back and I'll tell you why. It isn't a happy reason.",
        ],
      },
    ],
  },
  {
    id: "wren",
    name: "Wren, a child",
    col: 27,
    row: 156,
    look: "child",
    beats: [
      {
        requires: "nariLost",
        lines: [
          "Where's Nari? You always have Nari.",
          "...Oh. Is he playing the hiding game? He's SO bad at the hiding game. His feet always stick out.",
          "When you find where he's hiding, tell him Wren looked. Tell him I looked everywhere.",
        ],
      },
      {
        sets: "met_wren",
        lines: [
          "Are you Nari's papa? Nari says you can hear the singing better than anyone.",
          "I can hear it a little. When I hold really still. It sounds like it wants something.",
          "Don't let it have Nari. It already got my sister and she doesn't play anymore, she just... hums.",
        ],
      },
    ],
  },
  {
    id: "old_holt",
    name: "Old Holt, who nearly climbed",
    col: 32,
    row: 153,
    look: "elder",
    beats: [
      {
        requires: "leftFold",
        lines: [
          "So you're doing it. Good. GOOD.",
          "Listen to an old fool who didn't: up there, everything you love is weight, and weight is what sinks you.",
          "You'll want to set the boy down to climb faster. Don't. Whatever it costs -- carry him. Carrying him is the whole point.",
        ],
      },
      {
        sets: "met_holt",
        lines: [
          "I had my hand on the town line once. Rope coiled, lamp lit, the whole plan.",
          "Then I thought: what if the up is worse? And I put the rope down. Fifty years ago, I put the rope down.",
          "You've got a son and a reason. I had neither, and still I couldn't. Go on. Shame me.",
        ],
      },
    ],
  },

  // --- The climb (drowned souls met on the way up) ------------------------
  {
    id: "climber_wretch",
    name: "A climbing wretch",
    col: 18,
    row: 120,
    look: "pilgrim",
    beats: [
      {
        requires: "nariLost",
        lines: [
          "Empty-handed going up. That's the only way that means anything now, friend.",
          "I've been climbing these wrecks so long I weigh nothing. That's why I still climb -- there's nothing left of me to sink.",
        ],
      },
      {
        sets: "met_wretch",
        lines: [
          "Careful on the masts. They stand like trees but they remember being ships.",
          "You've got a heaviness to you. A living kind. The song will feel it a mile off.",
          "Whatever you're carrying up there -- and I see that you're carrying something -- hold it tighter than you're holding it now.",
        ],
      },
    ],
  },
  {
    id: "salt_foreman",
    name: "A salt-struck figure",
    col: 44,
    row: 174,
    look: "hooded",
    beats: [
      {
        sets: "met_foreman",
        lines: [
          "...three steps... from the lift... I only stopped to listen...",
          "Don't. Don't stare ahead too long. That's all it takes. You stare at the sound long enough and you become a thing that's only listening.",
          "Cover your ears when it gets loud near the top. Cover the boy's first.",
        ],
      },
    ],
  },
  {
    id: "hooded_watcher",
    name: "A hooded watcher",
    col: 45,
    row: 176,
    look: "hooded",
    beats: [
      {
        requires: "nariLost",
        lines: [
          "You're hunting the thing that took him. A beast, you think. A den, claws, a larder.",
          "There's no blood at the den's mouth. Did you notice? A beast leaves blood.",
          "Whatever keeps your boy set his little prints down GENTLY, one at a time, facing in. Ask yourself who does a thing like that.",
          "...I've said too much. Go up. You'll understand at the top, and you'll wish you didn't.",
        ],
      },
      {
        sets: "met_watcher",
        lines: [
          "You don't know me. But I knew her, before the mask.",
          "When you reach the Stage -- and you will -- remember that the worst things in this world were done by someone who loved you.",
          "That's all. Go on.",
        ],
      },
    ],
  },
];

export function npcsForMap(): NpcDef[] {
  return NPCS;
}
