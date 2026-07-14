import * as Tone from "tone";

/**
 * Procedural battle SFX (PRD §11.2's "battle SFX pack", first fill).
 * Synthesized with Tone so the fight has hits/parries/dashes/ultimates TODAY;
 * per the §11.5 manifest rule these count as placeholder slots until real
 * recorded SFX drop into the same calls. Every trigger is failure-tolerant
 * (audio context not running must never break a fight tick).
 */
export class SfxPlayer {
  private hitSynth = new Tone.MembraneSynth({ pitchDecay: 0.02, octaves: 5, envelope: { attack: 0.001, decay: 0.18, sustain: 0 } }).toDestination();
  private hurtSynth = new Tone.MembraneSynth({ pitchDecay: 0.04, octaves: 3, envelope: { attack: 0.001, decay: 0.25, sustain: 0 } }).toDestination();
  private parrySynth = new Tone.MetalSynth({ envelope: { attack: 0.001, decay: 0.22, release: 0.05 }, harmonicity: 7.1, resonance: 900 }).toDestination();
  private dashNoise = new Tone.NoiseSynth({ noise: { type: "white" }, envelope: { attack: 0.004, decay: 0.11, sustain: 0 } });
  private dashFilter = new Tone.Filter(1400, "bandpass").toDestination();
  private ultSynth = new Tone.PolySynth(Tone.Synth, { oscillator: { type: "sawtooth" }, envelope: { attack: 0.01, decay: 0.5, sustain: 0.1, release: 0.4 } }).toDestination();

  constructor() {
    this.dashNoise.connect(this.dashFilter);
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
  }

  private safe(fn: () => void): void {
    try {
      fn();
    } catch {
      /* audio context not running -- SFX are garnish, never fatal */
    }
  }

  /** A player hit landing; on-beat hits ring brighter. */
  hit(onBeat: boolean): void {
    this.safe(() => this.hitSynth.triggerAttackRelease(onBeat ? "A2" : "F2", "16n"));
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
    for (const node of [this.hitSynth, this.hurtSynth, this.parrySynth, this.dashNoise, this.dashFilter, this.ultSynth]) node.dispose();
  }
}
