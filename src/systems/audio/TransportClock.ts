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
    if (Tone.getTransport().state !== "started") {
      Tone.getTransport().start();
    }
  }

  setBpm(bpm: number): void {
    Tone.getTransport().bpm.value = bpm;
  }

  reset(): void {
    const transport = Tone.getTransport();
    transport.stop();
    transport.position = 0;
    transport.cancel(0);
  }

  /** Current transport position in seconds, hardware-clock derived. */
  get currentTime(): number {
    return Tone.getTransport().seconds;
  }

  scheduleAt(time: number, callback: (time: number) => void): number {
    return Tone.getTransport().schedule(callback, time);
  }

  /** interval e.g. "4n" for quarter notes. Returns an id usable with clearSchedule. */
  scheduleRepeat(callback: (time: number) => void, interval: string): number {
    return Tone.getTransport().scheduleRepeat(callback, interval);
  }

  clearSchedule(id: number): void {
    Tone.getTransport().clear(id);
  }

  stop(): void {
    Tone.getTransport().stop();
  }
}
