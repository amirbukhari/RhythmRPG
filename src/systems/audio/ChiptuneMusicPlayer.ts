import * as Tone from "tone";
import { battleTrackUrl } from "./BattleTracks";

/**
 * Plays the rendered chiptune battle tracks (see BattleTracks.ts), looped
 * and anchored to a transport-time origin, replacing BeatmapSonifier as the
 * musical bed (PRD §11.2 / §20.2 item 2). The sonifier stays on top as the
 * downbeat/telegraph cue layer -- the PRD's "rhythm clarity before
 * difficulty" pillar wants the beat *marked*, and a machine-transcribed
 * track doesn't guarantee an audible downbeat by itself.
 *
 * Timing model: players are deliberately NOT Tone.Player.sync()'d. All
 * callers reason in Transport-position seconds (TransportClock.currentTime);
 * this class converts that origin to AudioContext time once at start
 * (ctxAt = now + (startAt - transport.seconds)) and lets Web Audio's
 * sample-accurate buffer looping take it from there. See the two-clocks
 * warning in BattleScene.checkBossPhaseTransition -- mixing Transport and
 * AudioContext time silently broke a boss transition once already, so the
 * conversion lives in exactly one place.
 *
 * Because each rendered file's length is an exact whole multiple of its
 * beatmap's pattern loop, buffer looping stays bar-aligned with the
 * MeterSequence judgment math without any per-loop re-anchoring.
 */
export class ChiptuneMusicPlayer {
  private buffers = new Map<string, Tone.ToneAudioBuffer>();
  private player: Tone.Player | null = null;
  private volumeDb = 0;

  /**
   * Fetch+decode the given tracks before battle starts. Unknown trackIds
   * (no rendered file yet) and load failures resolve silently -- battles
   * must remain playable sonifier-only rather than hard-failing on audio
   * assets (and e2e boots must not hang on a 404).
   */
  async preload(trackIds: string[]): Promise<void> {
    await Promise.all(
      trackIds.map(async (trackId) => {
        if (this.buffers.has(trackId)) return;
        const url = battleTrackUrl(trackId);
        if (!url) return;
        try {
          const buffer = await new Tone.ToneAudioBuffer().load(url);
          this.buffers.set(trackId, buffer);
        } catch {
          // Missing/undecodable asset: fall back to sonifier-only.
        }
      })
    );
  }

  /**
   * Starts looping `trackId` such that buffer position 0 corresponds to
   * transport time `startAtSeconds` (the current beatmap's bar-1-beat-1,
   * same origin BeatmapSonifier.start takes). `playbackRate` is the
   * accessibility game-speed multiplier -- the transport BPM is already
   * speed-scaled, so the audio must stretch identically to stay aligned.
   * Returns false when no buffer is available (caller keeps sonifier-only).
   */
  start(trackId: string, startAtSeconds: number, playbackRate = 1): boolean {
    this.stop();
    const buffer = this.buffers.get(trackId);
    if (!buffer) return false;

    const player = new Tone.Player(buffer).toDestination();
    player.loop = true;
    player.playbackRate = playbackRate;
    player.volume.value = this.volumeDb;

    const transportNow = Tone.getTransport().seconds;
    const ctxAt = Tone.now() + (startAtSeconds - transportNow);
    if (ctxAt >= Tone.now()) {
      player.start(ctxAt);
    } else {
      // Origin is already in the past (battle start computes it as "now",
      // which by the time we run may be microseconds behind): start
      // immediately, offset into the loop by the transport time already
      // elapsed, scaled to buffer-seconds by the playback rate.
      const offset = ((Tone.now() - ctxAt) * playbackRate) % buffer.duration;
      player.start(Tone.now(), offset);
    }
    this.player = player;
    return true;
  }

  /** linear 0..1, per the settings.volumeMusic scale used across the app. */
  setVolume(linear: number): void {
    this.volumeDb = linear <= 0 ? -Infinity : Tone.gainToDb(linear);
    if (this.player) this.player.volume.value = this.volumeDb;
  }

  stop(): void {
    if (this.player) {
      this.player.stop();
      this.player.dispose();
      this.player = null;
    }
  }

  dispose(): void {
    this.stop();
    this.buffers.forEach((b) => b.dispose());
    this.buffers.clear();
  }
}
