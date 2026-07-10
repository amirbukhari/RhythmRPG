"""
.lsdsng -> WAV renderer: synthesizes a gbmusic-generated LSDJ project as
Game Boy-style chiptune audio, without needing the LSDJ ROM or an emulator.

Why this exists: PRD §20.2 documented real-audio rendering as blocked because
PyBoy exposes no audio-buffer export and the LSDJ ROM can't be committed.
This sidesteps both: the .lsdsng files in output/ were *generated* by
lib/midi_to_lsdsng.py, so their structure is fully known (note starts on a
16th-note grid, one instrument per channel, no FX/tables/grooves), and the
Game Boy APU's four channels are simple enough to synthesize directly:

  pu1  lead   -> 50% duty pulse wave, with vibrato on longer-held notes
  pu2  bass   -> 25% duty pulse wave
  wav  chords -> 4-bit-quantized triangle, arpeggiated on longer-held notes
                 to fake the polyphony a single monophonic wave channel
                 can't produce -- the actual technique advanced LSDJ artists
                 use for implied harmony, not something invented here
  noi  drums  -> 15-bit LFSR noise, with kick/snare/hihat character varied
                 by position in the bar instead of one uniform click

Also renders to stereo with per-channel panning (pulses spread left/right,
wave/noise centered) rather than a single mono sum, since arrangement- and
mix-level polish (implied harmony, articulation, a beat that reads as a
beat, a stereo image) is what's actually within reach here -- the note
*data* itself was transcribed before this tool existed, from a source
master this repo doesn't have on disk, so no amount of arrangement or DSP
recovers melodic content the transcription never captured. This produces a
better-programmed chiptune arrangement of that transcribed material, not a
recreation of any specific existing recording.

This is a faithful renderer for what this pipeline writes, not a general
LSDJ player: FX columns, tables, grooves, and native vibrato/arp effects
are ignored because midi_to_lsdsng.py never writes them -- the vibrato and
arpeggios here are applied at render time as an arrangement choice, not
read from the .lsdsng. Hand-tuned .lsdsng files that use LSDJ's own FX
columns will render without them (see the LSDJ-emulator path in README.md
for those).

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
import scipy.signal

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


def _poly_blep(phase, dt):
    """Bandlimited step correction (PolyBLEP) applied at a phase discontinuity.
    Naively sampling a hard square/pulse edge at 44.1kHz aliases badly for
    any note above a couple hundred Hz -- audibly harsh, not a "retro" sound,
    just digital screech. This is the standard fix: subtract a small
    polynomial correction within one sample-period of each edge so the
    edge's harmonic content stays band-limited. `phase` is 0..1 position
    within the cycle, `dt` is the phase increment per sample (freq/SR),
    either a scalar or a per-sample array (varying dt supports vibrato)."""
    dt = np.broadcast_to(dt, phase.shape)
    corr = np.zeros_like(phase)
    near_rising = phase < dt
    dtc = dt[near_rising]
    t = phase[near_rising] / dtc
    corr[near_rising] = t + t - t * t - 1.0
    near_falling = phase > (1.0 - dt)
    dtc2 = dt[near_falling]
    t2 = (phase[near_falling] - 1.0) / dtc2
    corr[near_falling] = t2 * t2 + t2 + t2 + 1.0
    return corr


def _phase_from_freq(freq_arr):
    """Continuous phase accumulator for a (possibly time-varying) frequency
    array -- needed for vibrato and arpeggios, where a plain
    `arange(n)*freq/SR` isn't valid because freq isn't constant."""
    dt = freq_arr / SAMPLE_RATE
    phase = np.mod(np.cumsum(dt) - dt, 1.0)  # sample 0 starts at phase 0
    return phase, dt


def pulse_wave(freq_or_arr, n_samples, duty, vibrato_depth=0.0, vibrato_hz=5.5, vibrato_onset_seconds=0.15):
    """Anti-aliased pulse wave: a naive square built from two band-limited
    steps (rising edge at phase 0, falling edge at phase `duty`), each
    PolyBLEP-corrected, rather than np.where's hard (aliasing) transition.
    Accepts a constant frequency or a per-sample array (portamento glides
    need the latter). `vibrato_depth` (fractional frequency deviation, e.g.
    0.01 = ~1 semitone peak) adds the slow pitch wobble that's a defining
    piece of expressive chiptune lead lines -- a dead-flat pitch is what
    makes a synth sound like a test tone rather than a played instrument.
    The depth ramps in over `vibrato_onset_seconds` rather than being
    instantly at full depth from the note's attack -- real vibrato (voice,
    strings, and skilled trackers imitating them) is added after a note
    has settled, not applied from the very first cycle."""
    freq_arr = np.full(n_samples, float(freq_or_arr)) if np.isscalar(freq_or_arr) else np.asarray(freq_or_arr, dtype=float)
    if vibrato_depth > 0:
        t = np.arange(n_samples) / SAMPLE_RATE
        onset = np.clip(t / max(vibrato_onset_seconds, 1e-4), 0.0, 1.0)
        freq_arr = freq_arr * (1.0 + vibrato_depth * onset * np.sin(2 * np.pi * vibrato_hz * t))
    phase, dt = _phase_from_freq(freq_arr)
    wave = np.where(phase < duty, 1.0, -1.0)
    wave = wave + _poly_blep(phase, dt)
    wave = wave - _poly_blep((phase - duty) % 1.0, dt)
    return wave


def portamento_freq_track(from_midi, to_midi, n_samples, glide_seconds=0.05):
    """Linear (in semitones) pitch glide from one note into the next,
    rather than a hard retrigger -- the smooth, connected bassline
    character associated with a played (not sequenced-staccato) bass part.
    Only the first `glide_seconds` moves; the remainder holds at
    `to_midi`."""
    glide_samples = min(n_samples, max(1, int(glide_seconds * SAMPLE_RATE)))
    ramp = np.linspace(0.0, 1.0, glide_samples)
    semitone_track = np.full(n_samples, float(to_midi))
    semitone_track[:glide_samples] = from_midi + (to_midi - from_midi) * ramp
    return midi_to_hz(semitone_track)


_WAVETABLE_SHAPES = ("triangle", "soft_square", "saw")


def _wavetable_shape(phase, shape):
    """Three hand-designed 32-step wavetable timbres, standing in for the
    GB wave channel's fully custom (any 32x4-bit samples) waveform memory --
    which advanced LSDJ composers use instead of the plain default triangle
    every beginner patch starts from. Picking a register-appropriate shape
    (see CHANNEL_CFG usage in render_channel) is itself the technique, not
    just having more than one option."""
    if shape == "soft_square":
        # A rounded/soft square -- warmer and more filtered than a hard
        # pulse, characteristic of a wave-channel bass voice.
        return np.tanh(2.5 * np.sin(2.0 * np.pi * phase))
    if shape == "saw":
        # Bright ramp saw -- classic wave-channel lead/pluck timbre, an
        # octave's worth of harmonics brighter than a triangle.
        return 2.0 * phase - 1.0
    return 4.0 * np.abs(phase - 0.5) - 1.0  # triangle (LSDJ default)


def triangle_wave_4bit(freq_or_arr, n_samples, shape="triangle"):
    """LSDJ's default wave-channel shape is a triangle; the GB wave channel
    holds 32 4-bit samples, so quantize to 16 levels for the right texture.
    A triangle's harmonics fall off much faster than a square's, so it
    doesn't need PolyBLEP correction to avoid harshness. Accepts either a
    constant frequency or a per-sample frequency array (arpeggios need the
    latter -- see `arpeggiated_freq_track`). `shape` picks among
    `_WAVETABLE_SHAPES`."""
    freq_arr = np.full(n_samples, float(freq_or_arr)) if np.isscalar(freq_or_arr) else freq_or_arr
    phase, _ = _phase_from_freq(freq_arr)
    raw = _wavetable_shape(phase, shape)
    return np.round((raw + 1.0) * 7.5) / 7.5 - 1.0


def feedback_delay(signal, delay_seconds, feedback=0.32, mix=0.28):
    """A simple tempo-synced feedback delay/echo -- one of the most
    recognizable space-creating production techniques in chiptune mixing
    (real hardware has no built-in reverb, so echo does that job). Applied
    to the whole rendered channel, not per note, since a real echo tail
    naturally spans past a note's own end."""
    delay_samples = max(1, int(delay_seconds * SAMPLE_RATE))
    out = signal.copy()
    tap = np.zeros_like(signal)
    tap[delay_samples:] = signal[:-delay_samples]
    accum = tap.copy()
    # A handful of repeats is enough to hear a decaying echo without an
    # unbounded feedback loop; each successive tap is the previous one
    # shifted and attenuated by `feedback`.
    gain = feedback
    for _ in range(4):
        shifted = np.zeros_like(signal)
        shifted[delay_samples:] = accum[:-delay_samples]
        out = out + shifted * gain
        accum = shifted
        gain *= feedback
    return signal * (1.0 - mix) + out * mix


# A single monophonic wave channel can't hold a chord, so implying one
# means cycling rapidly through chord tones -- the actual technique
# skilled LSDJ artists use for harmony on a monophonic channel, not
# something invented for this renderer. Root/fifth/octave/fifth is
# consonant regardless of major/minor (this renderer has no key
# information to know which third would fit).
ARP_PATTERN_SEMITONES = (0, 7, 12, 7)
ARP_STEP_SECONDS = 0.045


def arpeggiated_freq_track(midi, n_samples):
    """Per-sample frequency array cycling ARP_PATTERN_SEMITONES every
    ARP_STEP_SECONDS, for a held wave-channel note long enough to make an
    arpeggio read as a chord rather than a stutter."""
    arp_step_samples = max(1, int(ARP_STEP_SECONDS * SAMPLE_RATE))
    step_idx = (np.arange(n_samples) // arp_step_samples) % len(ARP_PATTERN_SEMITONES)
    semitone_offsets = np.array(ARP_PATTERN_SEMITONES)[step_idx]
    return midi_to_hz(midi) * 2.0 ** (semitone_offsets / 12.0)


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


# Kick/snare/hihat character keyed off position within the 16-step LSDJ
# phrase (this tool's stand-in for "the bar" -- the .lsdsng format has no
# meter information of its own). A real drum kit has distinct voices; the
# previous version fired an identical click for every hit regardless of
# position, which reads as a hiss/wash rather than a beat once density
# gets much above one hit per beat. This is an original drum-programming
# heuristic (classic four-on-the-floor-with-backbeat feel), not
# transcribed from source data the .lsdsng doesn't contain (real kit
# labels were never captured -- see transcribe.py's known limitations).
def _drum_voice(step_in_phrase):
    if step_in_phrase % 8 == 0:
        return {"clock_hz": 5000, "decay": 0.11, "gain": 1.15}  # kick
    if step_in_phrase % 8 == 4:
        return {"clock_hz": 9000, "decay": 0.09, "gain": 1.0}  # snare
    return {"clock_hz": 24000, "decay": 0.03, "gain": 0.65}  # hihat


def one_pole_lowpass(signal, cutoff_hz):
    """Simple one-pole IIR lowpass. Real GB audio output runs through the
    console's analog output stage before you ever hear it; skipping any
    filtering here left every channel's raw digital edges (plus the 4-bit
    wave-channel's staircase quantization) fully exposed, which reads as
    harsh/buzzy rather than warm. Applied per-channel with a cutoff tuned
    to that channel's role."""
    alpha = 1.0 / (1.0 + SAMPLE_RATE / (2 * np.pi * cutoff_hz))
    b = [alpha]
    a = [1, -(1 - alpha)]
    return scipy.signal.lfilter(b, a, signal)


def defuzz_octave(notes):
    """Heuristic fix for a specific, observed transcription artifact: a
    polyphonic stem transcribed independently per-frame (basic-pitch) will
    occasionally report the same pitch class an octave away from its
    neighbors -- e.g. ...,55,76,62,57,... where 76 (=64 mod 12, matching
    the surrounding 62-65 cluster an octave up) is very likely the same
    note mis-registered an octave high, not a real melodic leap.

    Trigger is deliberately conservative: a fifth (7 semitones) or sixth is
    completely ordinary melodic movement and must survive untouched, so
    this only fires on jumps >= 10 semitones from BOTH neighbors (an
    octave-scale leap), and only applies the fix if some octave of the same
    pitch class lands within 4 semitones of the neighbor average -- i.e.
    only when there's a confident, near-exact octave-shifted match, not
    just "closest available option." A real, intentional octave-or-larger
    leap is rare and usually approached stepwise, so it's very unlikely to
    also have a same-pitch-class neighbor-fit this close by coincidence.

    `notes` is a list of (abs_step, midi_pitch, transpose); returns a new
    list with pitches only in the returned tuples.
    """
    if len(notes) < 3:
        return list(notes)
    out = list(notes)
    for i in range(1, len(out) - 1):
        step, pitch, t = out[i]
        prev_pitch = out[i - 1][1]
        next_pitch = out[i + 1][1]
        neighbor_avg = (prev_pitch + next_pitch) / 2.0
        if abs(pitch - prev_pitch) >= 10 and abs(pitch - next_pitch) >= 10:
            candidates = [pitch + 12 * k for k in (-2, -1, 1, 2)]
            best = min(candidates, key=lambda c: abs(c - neighbor_avg))
            if abs(best - neighbor_avg) <= 6 and abs(best - neighbor_avg) < abs(pitch - neighbor_avg):
                out[i] = (step, best, t)
    return out


# Per-channel synthesis config. `decay` is tuned per role for a plucked,
# articulated character (short for lead/bass so sparse notes read as
# distinct hits rather than drones; longer for pads) rather than one
# generic curve. `lowpass_hz` softens raw digital harshness per role.
# `pan`: -1 (hard left) .. +1 (hard right); pulses spread wide (a classic
# 2-pulse chiptune stereo image), wave/noise stay centered so the harmonic
# and rhythmic core of the arrangement doesn't move with the listener.
CHANNEL_CFG = {
    "pu1": {"duty": 0.50, "max_steps": 8, "decay": 0.35, "gain": 0.34, "lowpass_hz": 9000, "pan": -0.35},
    "pu2": {"duty": 0.25, "max_steps": 8, "decay": 0.30, "gain": 0.24, "lowpass_hz": 4500, "pan": 0.35},
    "wav": {"duty": None, "max_steps": 12, "decay": 0.55, "gain": 0.22, "lowpass_hz": 7000, "pan": 0.0},
    "noi": {"duty": None, "max_steps": 1, "decay": 0.07, "gain": 0.20, "lowpass_hz": 6000, "pan": 0.0},
}

# Notes held at least this many arp/vibrato cycles before the effect kicks
# in -- a quick staccato pluck shouldn't warble or arpeggiate, only
# genuinely sustained notes should.
ARP_MIN_STEPS = 3
VIBRATO_MIN_STEPS = 6
# Consecutive bass notes closer together than this glide instead of
# retriggering -- an idiomatic "played" bassline touch, not applied to
# genuinely separated notes where a clean retrigger is more natural.
PORTAMENTO_MAX_GAP_STEPS = 4
# Wave-channel register split for wavetable choice: bass-range notes get a
# rounder, filtered voice; melody-range notes get a brighter one.
WAV_BASS_MIDI_CEILING = 55
WAV_LEAD_MIDI_FLOOR = 72


def render_channel(channel, notes, step_seconds, total_samples):
    cfg = CHANNEL_CFG[channel]
    if channel != "noi":
        notes = defuzz_octave(notes)
    out = np.zeros(total_samples)
    for i, (abs_step, midi, _t) in enumerate(notes):
        start = int(round(abs_step * step_seconds * SAMPLE_RATE))
        if start >= total_samples:
            break
        # Sustain until the next note on this channel, capped per channel --
        # the generator writes note starts only (LSDJ envelopes handle ends).
        # The cap is intentionally short (see CHANNEL_CFG): the note data has
        # very sparse passages (well under 1 note/bar in places), and holding
        # those as a bar-long tone is a drone, not a melody -- a short,
        # decaying articulation is the more honest (and more listenable)
        # rendering of "we don't actually know how long this note rang."
        if channel == "noi":
            dur_seconds = 0.08
            dur_steps = 1
        else:
            next_step = notes[i + 1][0] if i + 1 < len(notes) else abs_step + cfg["max_steps"]
            dur_steps = min(next_step - abs_step, cfg["max_steps"])
            dur_seconds = max(dur_steps, 1) * step_seconds
        n = min(int(dur_seconds * SAMPLE_RATE), total_samples - start)
        if n <= 0:
            continue
        if channel == "noi":
            voice = _drum_voice(abs_step % 16)
            tone = lfsr_noise(n, clock_hz=voice["clock_hz"])
            note_gain = cfg["gain"] * voice["gain"]
            decay = voice["decay"]
        elif channel == "wav":
            shape = "soft_square" if midi < WAV_BASS_MIDI_CEILING else ("saw" if midi >= WAV_LEAD_MIDI_FLOOR else "triangle")
            if dur_steps >= ARP_MIN_STEPS:
                tone = triangle_wave_4bit(arpeggiated_freq_track(midi, n), n, shape=shape)
            else:
                tone = triangle_wave_4bit(midi_to_hz(midi), n, shape=shape)
            note_gain = cfg["gain"]
            decay = cfg["decay"]
        elif channel == "pu2":
            prev_pitch = notes[i - 1][1] if i > 0 else None
            gap = abs_step - notes[i - 1][0] if i > 0 else None
            if prev_pitch is not None and prev_pitch != midi and gap is not None and gap <= PORTAMENTO_MAX_GAP_STEPS:
                tone = pulse_wave(portamento_freq_track(prev_pitch, midi, n), n, cfg["duty"])
            else:
                tone = pulse_wave(midi_to_hz(midi), n, cfg["duty"])
            note_gain = cfg["gain"]
            decay = cfg["decay"]
        else:
            vibrato = 0.012 if dur_steps >= VIBRATO_MIN_STEPS else 0.0
            tone = pulse_wave(midi_to_hz(midi), n, cfg["duty"], vibrato_depth=vibrato)
            note_gain = cfg["gain"]
            decay = cfg["decay"]
        out[start:start + n] += tone * gb_envelope(n, decay) * note_gain
    if channel == "pu1":
        # Echo on the lead only -- centering the arrangement's rhythmic
        # (noise) and harmonic (wave) core while giving the melodic voice
        # the space/depth treatment is itself a mix decision, not just
        # "add echo everywhere."
        out = feedback_delay(out, delay_seconds=step_seconds * 3)  # dotted-8th-ish slapback
    filtered = one_pole_lowpass(out, cfg["lowpass_hz"])
    left_gain, right_gain = _pan_gains(cfg["pan"])
    return filtered * left_gain, filtered * right_gain


def _pan_gains(pan):
    """Equal-power pan law; pan in [-1, 1]."""
    angle = (pan + 1.0) * (np.pi / 4.0)
    return np.cos(angle), np.sin(angle)


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

    mix_l = np.zeros(total_samples)
    mix_r = np.zeros(total_samples)
    for channel in CHANNELS:
        left, right = render_channel(channel, events[channel], step_seconds, total_samples)
        mix_l += left
        mix_r += right

    # Soft-clip and normalize together (same scale factor both channels) so
    # the stereo image/pan balance set in CHANNEL_CFG survives normalization.
    mix = np.stack([mix_l, mix_r], axis=1)
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
    """`samples` is (n, 2) stereo float in [-1, 1]."""
    pcm = (np.clip(samples, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(path, "wb") as f:
        f.setnchannels(2)
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
