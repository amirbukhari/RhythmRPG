import * as Tone from "tone";
import type { Beatmap } from "../../data/schemas/Beatmap";
import type { TransportClock } from "./TransportClock";
import { eventSeconds, patternLengthSeconds } from "../combat/MeterSequence";

/**
 * Sonifies a beatmap's downbeat and enemyTelegraph events as audible synth
 * hits scheduled against Tone.Transport, looping for the length of the
 * authored pattern. Originally this was the only audio in the game; now the
 * rendered chiptune tracks (ChiptuneMusicPlayer/BattleTracks) are the
 * musical bed and this remains layered on top as the downbeat/telegraph cue
 * layer -- the machine-transcribed tracks don't guarantee an audibly marked
 * downbeat by themselves, and "rhythm clarity before difficulty" (PRD §7.3)
 * wants the judgment grid explicitly audible.
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
   * Starts looping playback of the beatmap's pattern. `bpm` is the
   * *effective* (speed-adjusted) tempo the transport is actually running at
   * -- pass this.effectiveBpm, not beatmap.bpm directly, or clicks will
   * drift out of sync whenever accessibility game-speed scaling is active.
   *
   * `startAtSeconds` is the absolute transport time treated as this
   * pattern's own bar-1-beat-1 -- required for a mid-battle boss phase
   * transition (PRD §8.7), where the new phase's beatmap starts playing at
   * whatever transport time the transition occurs, not at transport zero.
   * Tone.Transport.scheduleRepeat's startTime is an absolute transport
   * position, so event offsets must be shifted by this or a phase change
   * partway through a battle would replay the new pattern from the wrong
   * point (or in the past, which Tone silently no-ops).
   */
  start(beatmap: Beatmap, bpm: number, startAtSeconds = 0): void {
    this.stop();
    // Meter-aware: a boss beatmap's bars are not all the same length in
    // seconds, so this must use the same MeterSequence math BattleScene
    // uses for judgment, not a flat beatsPerBar assumption.
    const loopLength = patternLengthSeconds(beatmap.meterSequence, bpm);

    for (const event of beatmap.events) {
      const offset = startAtSeconds + eventSeconds(beatmap.meterSequence, event.bar, event.step, beatmap.subdivision, bpm);
      if (event.type === "downbeat") {
        // Forward the precise scheduled time Tone passes in -- using "now"
        // implicitly here (by omitting it) is exactly the main-thread-timer
        // imprecision PRD §10.2 exists to avoid, and Tone.js warns about it.
        this.scheduledIds.push(
          this.clock.scheduleRepeat((time) => this.downbeatSynth.triggerAttackRelease("C3", "32n", time), loopLength, offset)
        );
      } else if (event.type === "enemyTelegraph") {
        this.scheduledIds.push(
          this.clock.scheduleRepeat((time) => this.telegraphSynth.triggerAttackRelease("A4", "16n", time), loopLength, offset)
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
