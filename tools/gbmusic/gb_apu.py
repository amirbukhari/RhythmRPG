"""Game Boy (DMG) APU synthesizer — renders note events to real 8-bit audio.

This is the piece the original gbmusic pipeline was missing: it emits
`.lsdsng` project files that need LSDJ (whose ROM license forbids committing
it) to be heard. This module instead models the DMG's four sound channels
directly in numpy, faithfully enough that the output *is* the Game Boy
sound, not a bitcrush filter:

- Pulse 1 / Pulse 2: the four hardware duty cycles (12.5/25/50/75%), 4-bit
  volume envelopes stepping at 64 Hz, and pitches quantized to the real
  11-bit frequency register (f = 131072/(2048-N) Hz) — so high notes carry
  the authentic detune.
- Wave: 32-sample 4-bit wavetables clocked like CH3 (f = 65536/(2048-N)),
  with the hardware's 100/50/25% volume shifter.
- Noise: a real 15-bit (or 7-bit "metallic") LFSR clocked at
  262144/(divisor·2^shift) Hz, exactly as NR43 does it.

Channel DACs output unipolar 0..15 like the hardware; the mixdown then
passes through the DC-blocking high-pass the Game Boy's output capacitor
applies. Rendering is done 4x oversampled and decimated to kill aliasing
beyond what the DMG's own analog stage would pass.

Every synthesized event keeps the timestamp of the note it was transcribed
from, so a render of a song is sample-aligned with the original recording —
the measured beat grids in src/data/content/songs/ apply to both.
"""

from dataclasses import dataclass, field

import numpy as np
from scipy import signal as sps

GB_CLOCK = 4194304
FRAME_HZ = 64.0          # envelope clock (frame sequencer /64)
OVERSAMPLE = 4

# The four NR11 duty patterns (8 steps each), exactly as on hardware.
DUTY_PATTERNS = {
    0.125: np.array([0, 0, 0, 0, 0, 0, 0, 1], dtype=np.float32),
    0.25:  np.array([1, 0, 0, 0, 0, 0, 0, 1], dtype=np.float32),
    0.50:  np.array([1, 0, 0, 0, 0, 1, 1, 1], dtype=np.float32),
    0.75:  np.array([0, 1, 1, 1, 1, 1, 1, 0], dtype=np.float32),
}

# NR43 divisor table.
NOISE_DIVISORS = [8, 16, 32, 48, 64, 80, 96, 112]

# --- Wavetables (32 samples, 4-bit 0..15) -------------------------------
def _tri32():
    up = np.linspace(0, 15, 16)
    return np.round(np.concatenate([up, up[::-1]])).astype(np.float32)

def _saw32():
    return np.round(np.linspace(0, 15, 32)).astype(np.float32)

def _organ32():
    t = np.arange(32) / 32.0
    w = np.sin(2 * np.pi * t) + 0.5 * np.sin(4 * np.pi * t) + 0.25 * np.sin(6 * np.pi * t)
    w = (w - w.min()) / (w.max() - w.min())
    return np.round(w * 15).astype(np.float32)

WAVETABLES = {
    "triangle": _tri32(),
    "saw": _saw32(),
    "organ": _organ32(),
}


def midi_to_hz(pitch: float) -> float:
    return 440.0 * 2.0 ** ((pitch - 69.0) / 12.0)


def quantize_pulse_freq(freq: float) -> float:
    """Snap to the 11-bit pulse period register: f = 131072/(2048-N)."""
    n = int(round(2048.0 - 131072.0 / max(freq, 64.1)))
    n = min(2047, max(0, n))
    return 131072.0 / (2048 - n)


def quantize_wave_freq(freq: float) -> float:
    """CH3 full-cycle rate: f = 65536/(2048-N) (one cycle = 32 samples)."""
    n = int(round(2048.0 - 65536.0 / max(freq, 32.1)))
    n = min(2047, max(0, n))
    return 65536.0 / (2048 - n)


def _lfsr_sequence(width7: bool) -> np.ndarray:
    """Full period of the DMG noise LFSR (bit 0 inverted = DAC input)."""
    n = 127 if width7 else 32767
    reg = 0x7FFF
    out = np.empty(n, dtype=np.float32)
    for i in range(n):
        out[i] = 1.0 - (reg & 1)          # output is ~bit0
        xor = (reg ^ (reg >> 1)) & 1
        reg >>= 1
        reg |= xor << 14
        if width7:
            reg = (reg & ~0x40) | (xor << 6)
    return out

_LFSR15 = _lfsr_sequence(False)
_LFSR7 = _lfsr_sequence(True)


# --- Events --------------------------------------------------------------
@dataclass
class Note:
    """One pulse/wave channel note. Times in seconds, pitch in MIDI."""
    start: float
    end: float
    pitch: float
    volume: int = 12          # initial envelope volume 0..15
    env_period: int = 0       # NRx2 period 0..7 (0 = hold); steps of period/64s
    env_down: bool = True
    duty: float = 0.50        # pulse only
    vibrato_cents: float = 0.0
    vibrato_hz: float = 6.0
    vibrato_delay: float = 0.15
    arp_pitches: tuple = ()   # extra chord tones; cycles pitch at arp_hz
    arp_hz: float = 30.0
    # NR10-style frequency sweep (the classic LSDJ kick lives here):
    sweep_semitones: float = 0.0   # signed; applied over sweep_s then held
    sweep_s: float = 0.05


@dataclass
class NoiseHit:
    """One noise-channel trigger (kick/snare/hat)."""
    start: float
    volume: int = 13
    env_period: int = 2       # decay speed (bigger = longer tail)
    clock_shift: int = 4      # NR43 s: bigger = lower/darker
    divisor_code: int = 0     # NR43 r
    width7: bool = False      # 7-bit LFSR = metallic
    length: float = 0.4       # hard cutoff (like the length counter)


@dataclass
class ChannelPlan:
    """What to render on each of the four channels."""
    pulse1: list = field(default_factory=list)   # [Note]
    pulse2: list = field(default_factory=list)   # [Note]
    wave: list = field(default_factory=list)     # [Note]
    noise: list = field(default_factory=list)    # [NoiseHit]
    wavetable: str = "triangle"


# --- Rendering -----------------------------------------------------------
def _envelope(t: np.ndarray, volume: int, period: int, down: bool) -> np.ndarray:
    """4-bit hardware envelope: one step every period/64 s."""
    if period == 0:
        return np.full_like(t, float(volume))
    steps = np.floor(t * (FRAME_HZ / period))
    v = volume - steps if down else volume + steps
    return np.clip(v, 0.0, 15.0)


def _render_pulse_note(note: Note, sr: int, buf: np.ndarray):
    i0 = int(note.start * sr)
    i1 = min(int(note.end * sr), len(buf))
    if i1 <= i0:
        return
    n = i1 - i0
    t = np.arange(n, dtype=np.float64) / sr

    freq = quantize_pulse_freq(midi_to_hz(note.pitch))
    if note.arp_pitches:
        # LSDJ-style chord arp: cycle through tones at arp_hz.
        tones = np.array([quantize_pulse_freq(midi_to_hz(p))
                          for p in (note.pitch,) + tuple(note.arp_pitches)])
        idx = (np.floor(t * note.arp_hz) % len(tones)).astype(np.int64)
        freq_t = tones[idx]
    else:
        freq_t = np.full(n, freq)

    if note.vibrato_cents > 0:
        vib = np.sin(2 * np.pi * note.vibrato_hz * t) * (note.vibrato_cents / 1200.0)
        vib *= np.clip((t - note.vibrato_delay) / 0.1, 0.0, 1.0)  # fade in
        freq_t = freq_t * np.exp2(vib)

    if note.sweep_semitones:
        bend = note.sweep_semitones * np.minimum(t / max(note.sweep_s, 1e-3), 1.0)
        freq_t = np.maximum(freq_t * np.exp2(bend / 12.0), 64.1)

    phase = np.cumsum(freq_t) / sr
    pattern = DUTY_PATTERNS[note.duty]
    step = (np.floor(phase * 8) % 8).astype(np.int64)
    wave = pattern[step]

    vol = _envelope(t, note.volume, note.env_period, note.env_down).astype(np.float32)
    buf[i0:i1] = wave * vol / 15.0   # unipolar DAC 0..15, later DC-blocked


def _render_wave_note(note: Note, sr: int, buf: np.ndarray, table: np.ndarray):
    i0 = int(note.start * sr)
    i1 = min(int(note.end * sr), len(buf))
    if i1 <= i0:
        return
    n = i1 - i0
    t = np.arange(n, dtype=np.float64) / sr

    if note.arp_pitches:
        tones = np.array([quantize_wave_freq(midi_to_hz(p))
                          for p in (note.pitch,) + tuple(note.arp_pitches)])
        idx = (np.floor(t * note.arp_hz) % len(tones)).astype(np.int64)
        freq_t = tones[idx]
    else:
        freq_t = np.full(n, quantize_wave_freq(midi_to_hz(note.pitch)))

    phase = np.cumsum(freq_t) / sr
    idx = (np.floor(phase * 32) % 32).astype(np.int64)
    wave = table[idx]

    # CH3 has no envelope, only the 100/50/25%/mute shifter; approximate
    # dynamics by picking the nearest shift level from the note volume.
    shift = 1.0 if note.volume >= 12 else (0.5 if note.volume >= 7 else 0.25)
    buf[i0:i1] = wave * shift / 15.0


def _render_noise_hit(hit: NoiseHit, sr: int, buf: np.ndarray):
    i0 = int(hit.start * sr)
    dur = hit.length
    if hit.env_period > 0:
        dur = min(dur, hit.volume * hit.env_period / FRAME_HZ + 0.01)
    i1 = min(i0 + int(dur * sr), len(buf))
    if i1 <= i0:
        return
    n = i1 - i0
    t = np.arange(n, dtype=np.float64) / sr

    divisor = NOISE_DIVISORS[hit.divisor_code]
    lfsr_hz = GB_CLOCK / divisor / (1 << hit.clock_shift) / 2.0
    seq = _LFSR7 if hit.width7 else _LFSR15
    idx = (np.floor(t * lfsr_hz) % len(seq)).astype(np.int64)
    wave = seq[idx]

    vol = _envelope(t, hit.volume, hit.env_period, True).astype(np.float32)
    buf[i0:i1] = wave * vol / 15.0   # noise steals the channel: overwrite


def _monophonic_overwrite(events, render_fn, sr, buf):
    """Render in start order; later notes overwrite (hardware note-steal)."""
    for ev in sorted(events, key=lambda e: e.start):
        render_fn(ev, sr, buf)


def render_song(plan: ChannelPlan, duration: float, sr: int = 44100,
                mix=(0.85, 0.85, 0.80, 0.60), stereo: bool = True) -> np.ndarray:
    """Render a ChannelPlan to a float32 array (samples, 2) in [-1, 1].

    mix: per-channel gains (pulse1, pulse2, wave, noise).
    Stereo uses NR51-style soft panning: pu1 left-leaning, pu2
    right-leaning, wave/noise centered — the classic headphone image.
    """
    isr = sr * OVERSAMPLE
    n_over = int(np.ceil(duration * isr)) + isr // 10
    table = WAVETABLES[plan.wavetable]

    chans = []
    for events, render in (
        (plan.pulse1, _render_pulse_note),
        (plan.pulse2, _render_pulse_note),
        (plan.wave, lambda nte, r, b: _render_wave_note(nte, r, b, table)),
        (plan.noise, _render_noise_hit),
    ):
        buf = np.zeros(n_over, dtype=np.float32)
        _monophonic_overwrite(events, render, isr, buf)
        # decimate to output rate with an anti-aliasing FIR
        chans.append(sps.decimate(buf, OVERSAMPLE, ftype="fir", zero_phase=True))
        del buf

    n_out = int(np.ceil(duration * sr))
    chans = [c[:n_out] for c in chans]

    if stereo:
        pans = [(1.0, 0.6), (0.6, 1.0), (0.85, 0.85), (0.8, 0.8)]
    else:
        pans = [(1.0, 1.0)] * 4
    out = np.zeros((n_out, 2), dtype=np.float32)
    for c, g, (pl, pr) in zip(chans, mix, pans):
        out[:, 0] += c * g * pl
        out[:, 1] += c * g * pr

    # DC-blocking high-pass (the DMG's output capacitor), ~20 Hz.
    b, a = sps.butter(1, 20.0 / (sr / 2), "highpass")
    out = sps.lfilter(b, a, out, axis=0).astype(np.float32)

    peak = float(np.max(np.abs(out))) or 1.0
    out *= 0.891 / peak   # normalize to -1 dBFS
    return out
