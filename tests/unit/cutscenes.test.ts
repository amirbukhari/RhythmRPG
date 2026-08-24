import { describe, it, expect } from "vitest";
import { CUTSCENES, cutsceneById } from "../../src/data/content/cutscenes";

// The told spine (world-bible §9): seven scripted beats. Five are shipped as
// cutscenes here (the other two, The House and The Threshold, are folded into
// the Rite and the Leaving). This guards the two that the finale depends on and
// that had no equivalent in the old canon -- The Den and The Sitting-Down --
// against the exact failure the style contract §4.10 warns about: a story beat
// that silently never fires while every gate stays green.

const VALID_STAGES = new Set(["black", "obelisk", "litho", "fold", "house", "waterline", "scar", "rain"]);

describe("cutscene data integrity", () => {
  it("every cutscene is well-formed (unique id + flag, non-empty frames, valid stages, non-empty lines)", () => {
    const ids = new Set<string>();
    const flags = new Set<string>();
    for (const c of CUTSCENES) {
      expect(c.id, "id").toBeTruthy();
      expect(c.flag, `${c.id} flag`).toBeTruthy();
      expect(ids.has(c.id), `duplicate id ${c.id}`).toBe(false);
      expect(flags.has(c.flag), `duplicate flag ${c.flag}`).toBe(false);
      ids.add(c.id);
      flags.add(c.flag);
      expect(c.frames.length, `${c.id} frames`).toBeGreaterThan(0);
      for (const f of c.frames) {
        expect(VALID_STAGES.has(f.stage), `${c.id} stage ${f.stage}`).toBe(true);
        expect(f.lines.length, `${c.id} frame lines`).toBeGreaterThan(0);
        for (const line of f.lines) expect(line.trim().length, `${c.id} line`).toBeGreaterThan(0);
      }
    }
  });

  it("ships the two finale-critical beats with the flags the triggers gate on", () => {
    const den = cutsceneById("the_den");
    expect(den, "the_den registered").toBeDefined();
    expect(den!.flag).toBe("seen_den"); // OverworldScene fires this off clearing node_19
    // The Harrow's line the whole finale hangs on (world-bible §9 beat 5).
    expect(JSON.stringify(den!.frames)).toContain("Nothing up here took your boy");

    const sitting = cutsceneById("the_sitting_down");
    expect(sitting, "the_sitting_down registered").toBeDefined();
    expect(sitting!.flag).toBe("seen_sitting"); // checkEnterKeep gates on this flag
    // The reveal landing on MIR, not just the player (world-bible §9 beat 6):
    // the name he has been outrunning is the last word of the beat.
    const lastFrame = sitting!.frames[sitting!.frames.length - 1];
    expect(lastFrame.lines[lastFrame.lines.length - 1]).toBe("Lunal.");
  });
});
