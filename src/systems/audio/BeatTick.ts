import * as Tone from "tone";

/**
 * The opt-in audible beat tick (PRD §9.3 "optional audible beat tick").
 *
 * With the judged beat now derived from the playing song (PRD §8.3), the
 * always-on BeatmapSonifier click is retired from the fight; this small
 * synth replaces it for players who want an explicit audible metronome on
 * top of the music. It is triggered by the fight loop when the song's beat
 * grid crosses a beat -- deliberately immediate rather than pre-scheduled,
 * because pre-scheduling against the transport would re-introduce exactly
 * the two-clock drift (element time vs transport time) that §8.3 removes.
 * A one-frame trigger latency is acceptable for an assist cue; judgment
 * itself never runs through this class.
 */
export class BeatTick {
  private synth = new Tone.Synth({
    oscillator: { type: "square" },
    envelope: { attack: 0.001, decay: 0.05, sustain: 0, release: 0.04 },
  }).toDestination();

  constructor() {
    this.synth.volume.value = -14;
  }

  /** linear 0..1, per the settings.volumeMusic scale used across the app. */
  setVolume(linear: number): void {
    this.synth.volume.value = linear <= 0 ? -Infinity : -14 + Tone.gainToDb(linear);
  }

  trigger(): void {
    try {
      this.synth.triggerAttackRelease("C5", "32n");
    } catch {
      /* audio context not running -- the tick is an assist, never fatal */
    }
  }

  dispose(): void {
    this.synth.dispose();
  }
}
