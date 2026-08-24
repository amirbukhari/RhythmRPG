import * as Tone from "tone";

/**
 * Procedural battle SFX (PRD §11.2's "battle SFX pack", first fill).
 * Synthesized with Tone so the fight has hits/parries/dashes/ultimates TODAY;
 * per the §11.5 manifest rule these count as placeholder slots until real
 * recorded SFX drop into the same calls. Every trigger is failure-tolerant
 * (audio context not running must never break a fight tick).
 *
 * THE GAME IS UNDERWATER AND THE SOUND WAS NOT.
 * Every voice here used to run `.toDestination()` -- straight out, dry, full
 * bandwidth. A dry click is the audio equivalent of an untinted sprite: it does
 * not belong to the room it happens in, and *The Drowned Chorus* has exactly one
 * room. Everything now goes through a shared bus:
 *
 *   voices -> lowpass 3.4kHz (a slope, not a wall) -> short dark reverb -> out
 *
 * That single chain is the largest single improvement to how the fight sounds,
 * and it costs two nodes. The lowpass takes the glassy top off a MetalSynth so
 * a parry rings rather than spits; the reverb is short (1.1s, high wet on the
 * tail only) so hits stay tight enough to play to a grid -- a long tail would
 * smear the transient the player is timing against, which is the one thing the
 * §8.3 windows cannot afford.
 *
 * IMPACTS ARE TWO LAYERS, and this is why a hit now lands. A single
 * MembraneSynth is a body with no transient: it says "thud", never "crack".
 * Real impact sound is a click on top of a body, and the click is what the ear
 * reads as force -- so the tier scales the TRANSIENT (brightness and level),
 * while the body only changes pitch. A Perfect is not a louder thud, it is a
 * sharper one.
 */
export class SfxPlayer {
  // The room. Voices connect here, not to the destination.
  private out = new Tone.Gain(1).toDestination();
  private verb = new Tone.Reverb({ decay: 1.1, preDelay: 0.012, wet: 0.26 }).connect(this.out);
  private room = new Tone.Filter({ frequency: 3400, type: "lowpass", rolloff: -24 }).connect(this.verb);

  private hitSynth = new Tone.MembraneSynth({ pitchDecay: 0.02, octaves: 5, envelope: { attack: 0.001, decay: 0.18, sustain: 0 } }).connect(this.room);
  private hurtSynth = new Tone.MembraneSynth({ pitchDecay: 0.04, octaves: 3, envelope: { attack: 0.001, decay: 0.25, sustain: 0 } }).connect(this.room);
  private parrySynth = new Tone.MetalSynth({ envelope: { attack: 0.001, decay: 0.22, release: 0.05 }, harmonicity: 7.1, resonance: 900 }).connect(this.room);
  private dashNoise = new Tone.NoiseSynth({ noise: { type: "white" }, envelope: { attack: 0.004, decay: 0.11, sustain: 0 } });
  private dashFilter = new Tone.Filter(1400, "bandpass").connect(this.room);
  private ultSynth = new Tone.PolySynth(Tone.Synth, { oscillator: { type: "sawtooth" }, envelope: { attack: 0.01, decay: 0.5, sustain: 0.1, release: 0.4 } }).connect(this.room);
  /** The impact transient -- the click over the body. Bandpass is swept by tier. */
  private crack = new Tone.NoiseSynth({ noise: { type: "pink" }, envelope: { attack: 0.0006, decay: 0.045, sustain: 0 } });
  private crackFilter = new Tone.Filter({ frequency: 2600, type: "bandpass", Q: 1.1 }).connect(this.room);

  constructor() {
    this.dashNoise.connect(this.dashFilter);
    this.crack.connect(this.crackFilter);
    this.setVolume(1);
  }

  /** linear 0..1 from settings.volumeSfx. */
  setVolume(linear: number): void {
    const base = linear <= 0 ? -Infinity : Tone.gainToDb(linear);
    this.hitSynth.volume.value = base - 8;
    this.hurtSynth.volume.value = base - 6;
    this.parrySynth.volume.value = base - 14;
    this.dashNoise.volume.value = base - 16;
    this.ultSynth.volume.value = base - 10;
    this.crack.volume.value = base - 15;
  }

  private safe(fn: () => void): void {
    try {
      fn();
    } catch {
      /* audio context not running -- SFX are garnish, never fatal */
    }
  }

  /** A player hit landing; on-beat hits ring brighter. Kept for the two
   * callers that only know the binary window. */
  hit(onBeat: boolean): void {
    this.safe(() => this.hitSynth.triggerAttackRelease(onBeat ? "A2" : "F2", "16n"));
  }

  /**
   * M3: the impact voice, PITCHED BY TIER. A rhythm game teaches its window
   * through the ear before the eye -- a perfect lands a fifth above an off-beat
   * scuff, so a player learns where the beat is without ever reading the
   * popup. Heavy blows add a low body under the transient; a killing blow adds
   * a short ring above it, so a death is punctuated rather than merely final.
   */
  impact(tier: "perfect" | "great" | "good" | "off", heavy: boolean, fatal: boolean): void {
    const note = { perfect: "E3", great: "B2", good: "G2", off: "E2" }[tier];
    // The transient carries the tier. See THE GAME IS UNDERWATER above: a
    // Perfect is a SHARPER hit, not a louder one, so the tier moves the click's
    // centre frequency and level and leaves the body's loudness alone.
    const bright = { perfect: 5200, great: 3900, good: 2900, off: 1700 }[tier];
    const punch = { perfect: 0.95, great: 0.72, good: 0.5, off: 0.3 }[tier];
    this.safe(() => {
      const t = Tone.now();
      this.crackFilter.frequency.setValueAtTime(bright, t);
      this.crack.triggerAttackRelease("64n", t, punch * (heavy ? 1.15 : 1));
      this.hitSynth.triggerAttackRelease(note, heavy ? "8n" : "16n", t + 0.004);
      if (heavy) this.hurtSynth.triggerAttackRelease("C1", "16n", t + 0.012);
      if (fatal) this.ultSynth.triggerAttackRelease(["A3", "E4"], "16n", t + 0.05);
    });
  }

  /** The player getting struck. */
  hurt(): void {
    this.safe(() => this.hurtSynth.triggerAttackRelease("C2", "8n"));
  }

  parry(): void {
    this.safe(() => this.parrySynth.triggerAttackRelease("G5", "16n"));
  }

  dash(): void {
    this.safe(() => this.dashNoise.triggerAttackRelease("16n"));
  }

  ultimate(): void {
    this.safe(() => {
      this.hurtSynth.triggerAttackRelease("C1", "4n");
      this.ultSynth.triggerAttackRelease(["A2", "E3", "A3"], "8n", Tone.now() + 0.05);
    });
  }

  dispose(): void {
    for (const node of [
      this.hitSynth,
      this.hurtSynth,
      this.parrySynth,
      this.dashNoise,
      this.dashFilter,
      this.ultSynth,
      this.crack,
      this.crackFilter,
      this.room,
      this.verb,
      this.out,
    ])
      node.dispose();
  }
}
