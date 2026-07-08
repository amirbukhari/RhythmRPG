import * as Tone from "tone";
import type { Beatmap } from "../../data/schemas/Beatmap";
import type { TransportClock } from "./TransportClock";

/**
 * Converts a beatmap event's (bar, step) at its subdivision resolution into
 * seconds relative to the pattern's own start (bar 1, step 0 = 0s) -- pure
 * and unit-testable, unlike the synth playback that consumes it.
 */
export function beatmapEventSeconds(bar: number, step: number, bpm: number, beatsPerBar: number, subdivision: number): number {
  const secondsPerBar = (60 / bpm) * beatsPerBar;
  const secondsPerStep = secondsPerBar / subdivision;
  return (bar - 1) * secondsPerBar + step * secondsPerStep;
}

/**
 * Sonifies a beatmap's downbeat and enemyTelegraph events as audible synth
 * hits scheduled against Tone.Transport, looping for the length of the
 * authored pattern. This is scratch-track sonification, not the shipped
 * soundtrack (PRD §11.2's DAW-authored stems / tools/gbmusic chiptune
 * pipeline are the real music path) -- but it makes the audio-clock-driven
 * timing in PRD §10.2 actually audible instead of a silent scheduler,
 * which matters for a game whose entire premise is playing to the beat.
 */
export class BeatmapSonifier {
  private downbeatSynth = new Tone.Synth({
    oscillator: { type: "square" },
    envelope: { attack: 0.001, decay: 0.06, sustain: 0, release: 0.05 },
  }).toDestination();

  private telegraphSynth = new Tone.Synth({
    oscillator: { type: "sawtooth" },
    envelope: { attack: 0.001, decay: 0.18, sustain: 0, release: 0.1 },
  }).toDestination();

  private scheduledIds: number[] = [];

  constructor(private readonly clock: TransportClock) {
    this.downbeatSynth.volume.value = -12;
    this.telegraphSynth.volume.value = -8;
  }

  /**
   * Starts looping playback of the beatmap's pattern from the current
   * transport position. `bpm` is the *effective* (speed-adjusted) tempo the
   * transport is actually running at -- pass this.effectiveBpm, not
   * beatmap.bpm directly, or clicks will drift out of sync whenever
   * accessibility game-speed scaling is active.
   */
  start(beatmap: Beatmap, bpm: number): void {
    this.stop();
    const beatsPerBar = beatmap.meterSequence[0]?.num ?? 4;
    const totalBars = Math.max(...beatmap.meterSequence.map((m) => m.startBar + m.bars - 1), 1);
    const patternLengthSeconds = beatmapEventSeconds(totalBars + 1, 0, bpm, beatsPerBar, beatmap.subdivision);

    for (const event of beatmap.events) {
      const offset = beatmapEventSeconds(event.bar, event.step, bpm, beatsPerBar, beatmap.subdivision);
      if (event.type === "downbeat") {
        // Forward the precise scheduled time Tone passes in -- using "now"
        // implicitly here (by omitting it) is exactly the main-thread-timer
        // imprecision PRD §10.2 exists to avoid, and Tone.js warns about it.
        this.scheduledIds.push(
          this.clock.scheduleRepeat((time) => this.downbeatSynth.triggerAttackRelease("C3", "32n", time), patternLengthSeconds, offset)
        );
      } else if (event.type === "enemyTelegraph") {
        this.scheduledIds.push(
          this.clock.scheduleRepeat((time) => this.telegraphSynth.triggerAttackRelease("A4", "16n", time), patternLengthSeconds, offset)
        );
      }
    }
  }

  /** linear 0..1, per the settings.volumeMusic scale used across the app. */
  setVolume(linear: number): void {
    const db = linear <= 0 ? -Infinity : Tone.gainToDb(linear);
    this.downbeatSynth.volume.value = -12 + db;
    this.telegraphSynth.volume.value = -8 + db;
  }

  stop(): void {
    this.scheduledIds.forEach((id) => this.clock.clearSchedule(id));
    this.scheduledIds = [];
  }

  dispose(): void {
    this.stop();
    this.downbeatSynth.dispose();
    this.telegraphSynth.dispose();
  }
}
