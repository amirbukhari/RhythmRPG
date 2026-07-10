"""
.lsdsng -> WAV renderer: synthesizes a gbmusic-generated LSDJ project as
Game Boy-style chiptune audio, without needing the LSDJ ROM or an emulator.

Why this exists: PRD §20.2 documented real-audio rendering as blocked because
PyBoy exposes no audio-buffer export and the LSDJ ROM can't be committed.
This sidesteps both: the .lsdsng files in output/ were *generated* by
lib/midi_to_lsdsng.py, so their structure is fully known (note starts on a
16th-note grid, one instrument per channel, no FX/tables/grooves), and the
Game Boy APU's four channels are simple enough to synthesize directly:

  pu1  lead   -> 50% duty pulse wave
  pu2  bass   -> 25% duty pulse wave
  wav  chords -> 4-bit-quantized triangle (LSDJ's default wave shape)
  noi  drums  -> 15-bit LFSR noise burst

This is a faithful renderer for what this pipeline writes, not a general
LSDJ player: FX columns, tables, grooves, and vibrato are ignored because
midi_to_lsdsng.py never writes them. Hand-tuned .lsdsng files that use those
features will render without them.

Usage:
  python3 render_lsdsng.py <input.lsdsng> <output.wav> [--bpm N] [--loop-beats N]

  --bpm         overrides the song's stored tempo. Used to render each track
                at its beatmap's authored BPM so music and judgment grid stay
                bar-aligned in-game (see render_all_tracks.py).
  --loop-beats  cut the render to the largest whole multiple of this many
                quarter-note beats (the beatmap's pattern loop length), so
                the audio loops seamlessly against the gameplay pattern. If
                the music is shorter than one pattern it is padded to one.
"""

import argparse
import os
import sys
import wave

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
import pylsdj  # noqa: E402

SAMPLE_RATE = 44100
STEPS_PER_PHRASE = 16
PHRASES_PER_CHAIN = 16
CHANNELS = ("pu1", "pu2", "wav", "noi")

NOTE_NAMES = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6,
              "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}


def note_str_to_midi(note):
    """Inverse of lib/midi_to_lsdsng.py's midi_note_to_lsdj_note: 'C 4' -> 60."""
    name = note[:2].strip()
    octave = int(note[2], 16)
    return (octave + 1) * 12 + NOTE_NAMES[name]


def parse_lsdsng(path):
    """Extract per-channel note events from a gbmusic-generated .lsdsng.

    Returns (tempo, {channel: [(abs_step, midi_pitch, transpose)]}).
    abs_step is on the global 16th-note grid (4 steps per beat).
    """
    proj = pylsdj.load_lsdsng(path)
    song = proj.song
    tempo = song.song_data.tempo

    def is_silent_chain(chain_idx):
        raw = song.song_data.chain_phrases[chain_idx]
        return all(p == 0xFF for p in raw)

    events = {c: [] for c in CHANNELS}
    for channel in CHANNELS:
        for row_idx, row in enumerate(song.song_data.song):
            chain_idx = getattr(row, channel)
            if chain_idx == 0xFF or not song.song_data.chain_alloc_table[chain_idx] or is_silent_chain(chain_idx):
                continue
            phrase_ids = song.song_data.chain_phrases[chain_idx]
            transposes = song.song_data.chain_transposes[chain_idx]
            for slot in range(PHRASES_PER_CHAIN):
                phrase_idx = phrase_ids[slot]
                if phrase_idx == 0xFF or not song.song_data.phrase_alloc_table[phrase_idx]:
                    continue
                notes = song.song_data.phrase_notes[phrase_idx]
                for step, note in enumerate(notes):
                    if note == "---":
                        continue
                    abs_step = (row_idx * PHRASES_PER_CHAIN + slot) * STEPS_PER_PHRASE + step
                    # LSDJ chain transpose is a signed-byte semitone offset.
                    t = transposes[slot]
                    t = t - 256 if t > 127 else t
                    events[channel].append((abs_step, note_str_to_midi(note) + t, t))
    for channel in CHANNELS:
        events[channel].sort(key=lambda e: e[0])
    return tempo, events


def midi_to_hz(midi):
    return 440.0 * 2.0 ** ((midi - 69) / 12.0)


def gb_envelope(n_samples, decay_seconds, sustain_level=0.0):
    """GB-style stepped volume decay: exponential decay quantized to the
    APU's 15 volume levels, which gives the characteristic chiptune 'zipper'
    fade instead of a smooth one."""
    t = np.arange(n_samples) / SAMPLE_RATE
    env = (1.0 - sustain_level) * np.exp(-t / max(decay_seconds, 1e-4)) + sustain_level
    return np.round(env * 15) / 15


def pulse_wave(freq, n_samples, duty):
    phase = (np.arange(n_samples) * freq / SAMPLE_RATE) % 1.0
    return np.where(phase < duty, 1.0, -1.0)


def triangle_wave_4bit(freq, n_samples):
    """LSDJ's default wave-channel shape is a triangle; the GB wave channel
    holds 32 4-bit samples, so quantize to 16 levels for the right texture."""
    phase = (np.arange(n_samples) * freq / SAMPLE_RATE) % 1.0
    tri = 4.0 * np.abs(phase - 0.5) - 1.0
    return np.round((tri + 1.0) * 7.5) / 7.5 - 1.0


def lfsr_noise(n_samples, clock_hz=32768, seed=0x7FFF):
    """15-bit LFSR noise as the GB noise channel produces it, sample-held
    at clock_hz."""
    n_clocks = int(np.ceil(n_samples * clock_hz / SAMPLE_RATE)) + 1
    lfsr = seed
    bits = np.empty(n_clocks, dtype=np.float64)
    for i in range(n_clocks):
        bit = (lfsr ^ (lfsr >> 1)) & 1
        lfsr = (lfsr >> 1) | (bit << 14)
        bits[i] = 1.0 if (lfsr & 1) else -1.0
    idx = (np.arange(n_samples) * clock_hz // SAMPLE_RATE).astype(np.int64)
    return bits[idx]


# Per-channel synthesis config: (duty/None, max sustain in steps, decay s, gain)
CHANNEL_CFG = {
    "pu1": {"duty": 0.50, "max_steps": 16, "decay": 0.60, "gain": 0.30},
    "pu2": {"duty": 0.25, "max_steps": 12, "decay": 0.50, "gain": 0.28},
    "wav": {"duty": None, "max_steps": 16, "decay": 0.80, "gain": 0.30},
    "noi": {"duty": None, "max_steps": 1, "decay": 0.06, "gain": 0.26},
}


def render_channel(channel, notes, step_seconds, total_samples):
    cfg = CHANNEL_CFG[channel]
    out = np.zeros(total_samples)
    for i, (abs_step, midi, _t) in enumerate(notes):
        start = int(round(abs_step * step_seconds * SAMPLE_RATE))
        if start >= total_samples:
            break
        # Sustain until the next note on this channel, capped per channel --
        # the generator writes note starts only (LSDJ envelopes handle ends).
        if channel == "noi":
            dur_seconds = 0.08
        else:
            next_step = notes[i + 1][0] if i + 1 < len(notes) else abs_step + cfg["max_steps"]
            dur_steps = min(next_step - abs_step, cfg["max_steps"])
            dur_seconds = max(dur_steps, 1) * step_seconds
        n = min(int(dur_seconds * SAMPLE_RATE), total_samples - start)
        if n <= 0:
            continue
        if channel == "noi":
            tone = lfsr_noise(n)
        elif channel == "wav":
            tone = triangle_wave_4bit(midi_to_hz(midi), n)
        else:
            tone = pulse_wave(midi_to_hz(midi), n, cfg["duty"])
        out[start:start + n] += tone * gb_envelope(n, cfg["decay"]) * cfg["gain"]
    return out


def render(path, bpm=None, loop_beats=None):
    tempo, events = parse_lsdsng(path)
    bpm = bpm or tempo
    step_seconds = 15.0 / bpm  # one 16th note

    max_step = max((n[-1][0] for n in events.values() if n), default=0)
    music_beats = (max_step + 1) / 4.0

    if loop_beats:
        multiples = max(1, int(music_beats // loop_beats))
        total_beats = multiples * loop_beats
    else:
        # Round up to a whole 4-beat bar so bare renders still loop cleanly.
        total_beats = int(np.ceil(music_beats / 4.0)) * 4
    total_samples = int(round(total_beats * 4 * step_seconds * SAMPLE_RATE))

    mix = np.zeros(total_samples)
    for channel in CHANNELS:
        mix += render_channel(channel, events[channel], step_seconds, total_samples)

    # Soft-clip and normalize; keep headroom so in-game volume math is sane.
    mix = np.tanh(mix * 1.2)
    peak = np.max(np.abs(mix))
    if peak > 0:
        mix = mix * (0.90 / peak)

    note_count = sum(len(v) for v in events.values())
    return mix, {
        "stored_tempo": tempo,
        "render_bpm": bpm,
        "music_beats": music_beats,
        "rendered_beats": total_beats,
        "duration_seconds": total_samples / SAMPLE_RATE,
        "note_count": note_count,
        "notes_per_channel": {c: len(events[c]) for c in CHANNELS},
    }


def write_wav(path, samples):
    pcm = (np.clip(samples, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(path, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SAMPLE_RATE)
        f.writeframes(pcm.tobytes())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--bpm", type=float, default=None)
    ap.add_argument("--loop-beats", type=float, default=None)
    args = ap.parse_args()

    samples, info = render(args.input, bpm=args.bpm, loop_beats=args.loop_beats)
    write_wav(args.output, samples)
    for k, v in info.items():
        print(f"  {k}: {v}")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
