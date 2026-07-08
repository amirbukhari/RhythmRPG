import * as Tone from "tone";

/**
 * Thin wrapper around Tone.Transport — the single source of truth for all
 * musical/combat timing. PRD §10.2: no gameplay judgment may be derived from
 * setTimeout/setInterval/requestAnimationFrame alone.
 */
export class TransportClock {
  /** Must be called only after a user gesture (see AudioGateScene). */
  async start(bpm: number): Promise<void> {
    await Tone.start();
    Tone.getTransport().bpm.value = bpm;
    Tone.getTransport().start();
  }

  /** Current transport position in seconds, hardware-clock derived. */
  get currentTime(): number {
    return Tone.getTransport().seconds;
  }

  scheduleAt(time: number, callback: (time: number) => void): number {
    return Tone.getTransport().schedule(callback, time);
  }

  stop(): void {
    Tone.getTransport().stop();
  }
}
