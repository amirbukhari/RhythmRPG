import * as Tone from "tone";

/**
 * Procedural soundtrack (PRD §11.2). The game is a music game; this makes it
 * one without shipping a multi-megabyte audio file. A real composed loop --
 * bass, pad chords, a chiptune arpeggio, and drums -- is synthesised with
 * Tone.js and played against Tone.Transport (the same clock the rhythm combat
 * runs on), so the music and the beat are the same thing.
 *
 * Mood: "The Drowned Chorus" -- A-minor, slow and gothic, i–VI–III–VII, with
 * intensity layered in for combat/boss. One shared instance, driven by scenes:
 *   menu/explore  -> pad + bass (calm, spacious)
 *   combat        -> + drums + arpeggio
 *   boss          -> + faster arpeggio + heavier drums
 */

type Mode = "menu" | "explore" | "combat" | "boss";

interface Chord {
  bass: string; // root, one octave low
  pad: string[]; // triad
  arp: string[]; // notes to arpeggiate (16ths)
}

// A minor, i – VI – III – VII (Am – F – C – G): epic, melancholic, resolves onward.
const PROGRESSION: Chord[] = [
  { bass: "A1", pad: ["A3", "C4", "E4"], arp: ["A4", "C5", "E5", "C5"] },
  { bass: "F1", pad: ["F3", "A3", "C4"], arp: ["F4", "A4", "C5", "A4"] },
  { bass: "C2", pad: ["C4", "E4", "G4"], arp: ["C5", "E5", "G5", "E5"] },
  { bass: "G1", pad: ["G3", "B3", "D4"], arp: ["G4", "B4", "D5", "B4"] },
];

export class MusicEngine {
  private started = false;
  private bar = 0;
  private mode: Mode = "menu";
  private volume = 0.7;

  private out = new Tone.Volume(-60).toDestination();
  private reverb = new Tone.Reverb({ decay: 6, wet: 0.35 }).connect(this.out);

  private pad = new Tone.PolySynth(Tone.Synth, {
    oscillator: { type: "fatsawtooth", count: 2, spread: 24 },
    envelope: { attack: 0.6, decay: 0.4, sustain: 0.7, release: 2.4 },
    volume: -20,
  }).connect(this.reverb);

  private bass = new Tone.MonoSynth({
    oscillator: { type: "triangle" },
    filter: { Q: 2, type: "lowpass" },
    envelope: { attack: 0.02, decay: 0.2, sustain: 0.5, release: 0.4 },
    filterEnvelope: { attack: 0.02, decay: 0.2, sustain: 0.3, baseFrequency: 120, octaves: 2.5 },
    volume: -14,
  }).connect(this.out);

  private arp = new Tone.Synth({
    oscillator: { type: "square" },
    envelope: { attack: 0.001, decay: 0.14, sustain: 0.05, release: 0.1 },
    volume: -22,
  }).connect(this.reverb);

  private kick = new Tone.MembraneSynth({
    octaves: 6,
    envelope: { attack: 0.001, decay: 0.32, sustain: 0 },
    volume: -8,
  }).connect(this.out);

  private hat = new Tone.NoiseSynth({
    noise: { type: "white" },
    envelope: { attack: 0.001, decay: 0.04, sustain: 0 },
    volume: -26,
  }).connect(this.out);

  private snare = new Tone.NoiseSynth({
    noise: { type: "pink" },
    envelope: { attack: 0.001, decay: 0.18, sustain: 0 },
    volume: -18,
  }).connect(this.out);

  private loop: Tone.Loop | null = null;

  /** Master music volume 0..1 (from settings). */
  setVolume(v: number): void {
    this.volume = Math.max(0, Math.min(1, v));
    if (this.started) this.rampToMode();
  }

  setMode(mode: Mode): void {
    this.mode = mode;
    if (this.started) this.rampToMode();
  }

  private targetDb(): number {
    if (this.volume <= 0.001) return -60;
    const base = -14 + 20 * (this.volume - 1); // 0 -> -34, 1 -> -14
    return Math.max(-60, base);
  }

  private rampToMode(): void {
    this.out.volume.rampTo(this.targetDb(), 1.2);
  }

  /**
   * Start the loop. The Tone AudioContext must already be running (unlocked in
   * AudioGateScene). Idempotent -- safe to call from every scene.
   */
  start(): void {
    if (this.started) {
      this.rampToMode();
      return;
    }
    this.started = true;
    const transport = Tone.getTransport();
    if (transport.state !== "started") {
      transport.bpm.value = 96;
      transport.start();
    }
    this.loop?.dispose();
    this.loop = new Tone.Loop((time) => this.playBar(time), "1m").start(0);
    this.rampToMode();
  }

  private playBar(time: number): void {
    const chord = PROGRESSION[this.bar % PROGRESSION.length];
    this.bar++;
    const q = Tone.Time("4n").toSeconds();
    const e = Tone.Time("8n").toSeconds();
    const s = Tone.Time("16n").toSeconds();

    // pad: sustain the chord across the bar
    this.pad.triggerAttackRelease(chord.pad, "1m", time);

    // bass: root pulse on eighths (root/root/fifth-feel via octave bob)
    for (let i = 0; i < 8; i++) {
      const note = i % 4 === 2 ? Tone.Frequency(chord.bass).transpose(12).toNote() : chord.bass;
      this.bass.triggerAttackRelease(note, "8n", time + i * e, i % 2 === 0 ? 0.9 : 0.5);
    }

    if (this.mode === "menu") return; // calm: pad + bass only

    // drums: kick on 1 & 3, snare on 2 & 4, hats on eighths
    for (let b = 0; b < 4; b++) {
      if (b % 2 === 0) this.kick.triggerAttackRelease("C1", "8n", time + b * q);
      else this.snare.triggerAttackRelease("16n", time + b * q);
    }
    for (let i = 0; i < 8; i++) this.hat.triggerAttackRelease("32n", time + i * e, 0.3);

    // arpeggio: 16ths over the chord (denser for boss)
    const dense = this.mode === "boss";
    const steps = dense ? 16 : 8;
    const stepLen = dense ? s : e;
    for (let i = 0; i < steps; i++) {
      const n = chord.arp[i % chord.arp.length];
      const note = dense && i % 8 >= 4 ? Tone.Frequency(n).transpose(12).toNote() : n;
      this.arp.triggerAttackRelease(note, dense ? "16n" : "8n", time + i * stepLen, 0.6);
    }
  }

  stop(): void {
    this.out.volume.rampTo(-60, 0.8);
  }
}

/** One shared soundtrack for the whole game. */
export const music = new MusicEngine();
