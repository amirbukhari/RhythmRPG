"""v2 arrangement: author a Game Boy COVER of the song, don't replay a dump.

The v1 arranger played basic-pitch's raw note events back verbatim. That
inherits every transcription artifact — ragged onsets, dust notes, chord
churn — and none of what makes chiptune sound intentional. This module
instead rebuilds each song the way a tracker musician covers one:

- The lead is traced from the vocal stem with pYIN (monophonic f0 + voicing
  confidence), not polyphonic transcription — a clean single line.
- A chord progression is detected per half-bar (chroma templates + Viterbi
  smoothing), and the wave channel plays AUTHORED patterns from it: driving
  16th arpeggios in loud sections, shimmer-arp pads in quiet ones.
- The bass is pYIN-traced, falls back to chord roots when the stem has
  energy but no confident pitch, and plays staccato eighths in drive
  sections / sustains in pads.
- EVERYTHING is quantized to the song's own measured beat grid
  (src/data/content/songs/<id>.json, PRD §8.3) subdivided into 16ths — so
  the render is machine-tight AND lands exactly on the grid the game
  judges. Quantization can't drift from judgment: it snaps TO the truth.
- Drums: classified hits snap to 16th cells, one hit per cell with
  snare > kick > hat priority on the single noise channel, and every kick
  also fires the classic LSDJ pitch-sweep kick on pulse 2 (the bass ducks
  around it, exactly like real LSDJ arrangements).
"""

import json
import os

import numpy as np

from gb_apu import Note, NoiseHit

PC_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

LEAD_RANGE = (55, 89)
FILL_RANGE = (57, 86)
BASS_RANGE = (36, 55)
WAVE_ROOT_RANGE = (55, 74)


# ------------------------------------------------------------- the grid --
class Grid:
    """The measured beat grid, subdivided. All quantization goes through
    this, so events stay on the exact timeline the game judges."""

    def __init__(self, beat_times, duration):
        beats = [float(b) for b in beat_times if 0.0 <= b < duration]
        if len(beats) < 2:  # degenerate fallback: 120 BPM straight
            beats = list(np.arange(0.0, duration, 0.5))
        pre = []
        step = beats[1] - beats[0]
        t = beats[0] - step
        while t > 0.02:
            pre.append(t)
            t -= step
        post = []
        step = beats[-1] - beats[-2]
        t = beats[-1] + step
        while t < duration:
            post.append(t)
            t += step
        self.beats = pre[::-1] + beats + post
        lines = []
        for a, b in zip(self.beats, self.beats[1:]):
            for k in range(4):
                lines.append(a + (b - a) * k / 4.0)
        lines.append(self.beats[-1])
        self.lines16 = np.array(lines)

    def cells(self, div=16):
        """Non-overlapping (t0, t1) windows: div=16 -> 16ths, 8 -> 8ths."""
        pts = self.lines16[:: (1 if div == 16 else 2)]
        return list(zip(pts[:-1], pts[1:]))

    def half_bars(self):
        """(t0, t1) spanning two beats each — the chord-detection window."""
        b = self.beats
        return [(b[i], b[min(i + 2, len(b) - 1)]) for i in range(0, len(b) - 1, 2)]

    def snap16(self, t):
        return float(self.lines16[int(np.argmin(np.abs(self.lines16 - t)))])


def load_grid(song_name, duration, songs_dir=None):
    songs_dir = songs_dir or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "../../src/data/content/songs")
    path = os.path.join(songs_dir, f"{song_name}.json")
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
        return Grid([ms / 1000.0 for ms in data["beatTimesMs"]], duration), True
    return Grid([], duration), False


# --------------------------------------------------- pitch/energy tracks --
def extract_pitch(path, cache_path, fmin_note, fmax_note, frame=2048):
    """pYIN f0 track + voicing confidence + RMS for one stem (cached)."""
    if os.path.exists(cache_path):
        with open(cache_path) as f:
            return json.load(f)
    import librosa
    y, sr = librosa.load(path, sr=22050, mono=True)
    hop = 512
    f0, _, vprob = librosa.pyin(
        y, fmin=librosa.note_to_hz(fmin_note), fmax=librosa.note_to_hz(fmax_note),
        sr=sr, frame_length=frame, hop_length=hop)
    rms = librosa.feature.rms(y=y, frame_length=frame, hop_length=hop)[0]
    times = librosa.times_like(f0, sr=sr, hop_length=hop)
    midi = 69.0 + 12.0 * np.log2(np.maximum(f0, 1e-6) / 440.0)
    track = {
        "t": [round(float(x), 4) for x in times],
        "m": [None if np.isnan(v) else round(float(m), 2)
              for v, m in zip(f0, midi)],
        "p": [0.0 if np.isnan(v) else round(float(v), 3) for v in vprob],
        "r": [round(float(x), 5) for x in rms[:len(times)]],
    }
    with open(cache_path, "w") as f:
        json.dump(track, f)
    return track


def cell_summary(track, cells, voiced_min=0.4, prob_min=0.45):
    """Per cell: (median pitch or None, mean rms). Voicing-gated."""
    t = np.array(track["t"])
    m = np.array([np.nan if v is None else v for v in track["m"]])
    p = np.array(track["p"])
    r = np.array(track["r"])
    out = []
    for a, b in cells:
        sel = (t >= a) & (t < b)
        if not sel.any():
            out.append((None, 0.0))
            continue
        rms = float(np.mean(r[sel]))
        voiced = sel & ~np.isnan(m) & (p > prob_min)
        if voiced.sum() / sel.sum() < voiced_min:
            out.append((None, rms))
            continue
        out.append((float(np.median(m[voiced])), rms))
    return out


def _rms_to_vel(values):
    """Map cell RMS onto MIDI velocity, scaled per-song."""
    vals = np.array([v for v in values if v > 0])
    if not len(vals):
        return lambda r: 90
    lo, hi = np.percentile(vals, 25), np.percentile(vals, 95)
    def f(r):
        x = (r - lo) / max(hi - lo, 1e-9)
        return int(round(45 + 82 * min(1.0, max(0.0, x))))
    return f


def notes_from_cells(summary, cells, join_semitones=0.6):
    """Merge per-cell pitches into notes; returns [[pitch,s,e,vel], ...]."""
    vel_of = _rms_to_vel([r for _, r in summary])
    raw = []
    for (pv, rms), (a, b) in zip(summary, cells):
        if pv is None:
            continue
        if raw and abs(pv - raw[-1][0]) <= join_semitones \
                and abs(raw[-1][2] - a) < 1e-6:
            raw[-1][2] = b
            raw[-1][3] = max(raw[-1][3], rms)
        else:
            raw.append([pv, a, b, rms])
    return [[int(round(p)), s, e, vel_of(r)] for p, s, e, r in raw]


def _fold(pitch, lo, hi):
    while pitch < lo:
        pitch += 12
    while pitch > hi:
        pitch -= 12
    return pitch


def _center(notes, target):
    if not notes:
        return notes
    med = float(np.median([n[0] for n in notes]))
    shift = 12 * round((target - med) / 12.0)
    return [[p + shift, s, e, v] for p, s, e, v in notes]


# ------------------------------------------------------ chord detection --
_TEMPLATES = []
for root in range(12):
    _TEMPLATES.append((root, "maj", (root, (root + 4) % 12, (root + 7) % 12)))
    _TEMPLATES.append((root, "min", (root, (root + 3) % 12, (root + 7) % 12)))
    _TEMPLATES.append((root, "5", (root, (root + 7) % 12)))


def detect_chords(path, grid, cache_path, bass_path=None):
    """Per half-bar (root_pc, quality) via chroma templates + Viterbi.
    The bass stem's chroma (when given) is blended in as root evidence —
    rock guitar voicings alone are often root-ambiguous. Returns
    [(t0, t1, root_or_None, quality)]."""
    if os.path.exists(cache_path):
        with open(cache_path) as f:
            return [tuple(x) for x in json.load(f)]
    import librosa
    y, sr = librosa.load(path, sr=22050, mono=True)
    hop = 1024
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop)
    if bass_path:
        yb, _ = librosa.load(bass_path, sr=22050, mono=True)
        cb = librosa.feature.chroma_cqt(y=yb, sr=22050, hop_length=hop)
        n = min(chroma.shape[1], cb.shape[1])
        chroma = chroma[:, :n] + 0.9 * cb[:, :n]
    rms = librosa.feature.rms(y=y, hop_length=hop)[0]
    times = librosa.times_like(chroma[0], sr=sr, hop_length=hop)

    windows = grid.half_bars()
    feats, energy = [], []
    for a, b in windows:
        sel = (times >= a) & (times < b)
        if not sel.any():
            feats.append(np.zeros(12))
            energy.append(0.0)
            continue
        feats.append(chroma[:, sel].mean(axis=1))
        energy.append(float(rms[sel].mean()))
    gate = np.percentile([e for e in energy if e > 0] or [0], 20)

    n_states = len(_TEMPLATES) + 1        # + no-chord
    scores = np.zeros((len(windows), n_states))
    for i, (c, e) in enumerate(zip(feats, energy)):
        tot = c.sum() + 1e-9
        for j, (root, _, pcs) in enumerate(_TEMPLATES):
            w = sum((1.4 if pc == root else 1.0) * c[pc] for pc in pcs)
            scores[i, j] = w / (tot * (1.0 + 0.12 * len(pcs)))
        scores[i, -1] = 0.42 if e <= gate else 0.18

    switch = 0.10                          # Viterbi: discourage churn
    dp = scores[0].copy()
    back = np.zeros((len(windows), n_states), dtype=int)
    for i in range(1, len(windows)):
        best_prev = int(np.argmax(dp))
        new_dp = np.empty(n_states)
        for j in range(n_states):
            stay, move = dp[j], dp[best_prev] - switch
            back[i, j] = j if stay >= move else best_prev
            new_dp[j] = max(stay, move) + scores[i, j]
        dp = new_dp
    path_states = [int(np.argmax(dp))]
    for i in range(len(windows) - 1, 0, -1):
        path_states.append(int(back[i, path_states[-1]]))
    path_states.reverse()

    out = []
    for (a, b), s in zip(windows, path_states):
        if s == len(_TEMPLATES):
            out.append((float(a), float(b), None, None))
        else:
            root, kind, _ = _TEMPLATES[s]
            out.append((float(a), float(b), int(root), kind))
    with open(cache_path, "w") as f:
        json.dump(out, f)
    return out


# ----------------------------------------------------------- lead voice --
def arrange_lead(vocal_track, other_notes, grid):
    """pYIN vocal line quantized to 16ths; rests >= 4 beats are filled with
    the top line of the 'other' stem (quantized to 8ths, quieter, 25% duty)."""
    cells16 = grid.cells(16)
    summary = cell_summary(vocal_track, cells16)
    mono = notes_from_cells(summary, cells16)
    mono = _center(mono, 74)
    mono = [[_fold(p, *LEAD_RANGE), s, e, v] for p, s, e, v in mono]

    beat = float(np.median(np.diff(grid.beats)))
    min_gap = 4.0 * beat
    gaps, cursor = [], 0.0
    end_time = grid.lines16[-1]
    for p, s, e, v in mono + [[0, end_time, end_time, 0]]:
        if s - cursor >= min_gap:
            gaps.append((cursor, s))
        cursor = max(cursor, e)

    fills = []
    if other_notes:
        cells8 = grid.cells(8)
        for ga, gb in gaps:
            span = [(a, b) for a, b in cells8 if a >= ga - 1e-3 and b <= gb + 1e-3]
            cvals = []
            for a, b in span:
                mid = (a + b) / 2
                active = [n for n in other_notes
                          if n[1] <= mid < n[2] and n[3] >= 26]
                if not active:
                    cvals.append((None, 0.0))
                    continue
                top = max(active, key=lambda n: n[0])
                cvals.append((float(top[0]), top[3] / 127.0))
            seg = notes_from_cells(cvals, span, join_semitones=0.4)
            seg = _center(seg, 76)
            fills.extend([_fold(p, *FILL_RANGE), s, e, v] for p, s, e, v in seg)

    out = [Note(start=s, end=e, pitch=p, volume=_v(v, 10, 15), duty=0.50,
                env_period=0,
                vibrato_cents=25.0 if (e - s) >= 2.2 * beat / 4 else 0.0,
                vibrato_hz=5.6, vibrato_delay=0.18)
           for p, s, e, v in mono]
    out.extend(Note(start=s, end=e, pitch=p, volume=_v(v, 8, 12), duty=0.25,
                    vibrato_cents=14.0 if (e - s) >= 3 * beat / 4 else 0.0)
               for p, s, e, v in fills)
    return sorted(out, key=lambda n: n.start), len(fills)


def _v(vel, lo, hi):
    return int(round(lo + (hi - lo) * min(127, max(0, vel)) / 127.0))


# ------------------------------------------------------------ wave voice --
def arrange_wave(chords, grid, drive_windows):
    """Authored accompaniment from the chord track: driving 16th arpeggios
    in loud sections, sustained shimmer-arp pads in quiet ones."""
    notes = []
    for (a, b, root, kind), drive in zip(chords, drive_windows):
        if root is None:
            continue
        third = 4 if kind == "maj" else (3 if kind == "min" else 7)
        r = _fold(60 + root, *WAVE_ROOT_RANGE)
        tones = [r, r + third, r + 7, r + 12] if kind != "5" else [r, r + 7, r + 12, r + 19]
        if drive:
            lines = grid.lines16[(grid.lines16 >= a - 1e-4) & (grid.lines16 < b - 1e-4)]
            for i, t0 in enumerate(lines):
                t1 = t0 + (lines[1] - lines[0] if len(lines) > 1 else (b - a) / 8)
                notes.append(Note(start=float(t0), end=float(t0 + 0.88 * (t1 - t0)),
                                  pitch=tones[i % 4], volume=13, env_period=0))
        else:
            notes.append(Note(start=a, end=b, pitch=tones[0],
                              arp_pitches=tuple(tones[1:3]), arp_hz=24.0,
                              volume=9))
    return notes


# ------------------------------------------------------------ bass voice --
def arrange_bass(bass_track, chords, grid, drive_windows):
    """pYIN bass per 8th; chord-root fallback where the stem has energy but
    no confident pitch. Staccato eighths in drive, sustains in pads."""
    cells8 = grid.cells(8)
    summary = cell_summary(bass_track, cells8, voiced_min=0.4)
    vel_of = _rms_to_vel([r for _, r in summary])
    silence = np.percentile([r for _, r in summary if r > 0] or [0], 30)

    def chord_at(t):
        for a, b, root, kind in chords:
            if a <= t < b:
                return root
        return None

    def drive_at(t):
        for (a, b, *_), d in zip(chords, drive_windows):
            if a <= t < b:
                return d
        return True

    events = []
    for (pv, rms), (a, b) in zip(summary, cells8):
        pitch = None
        if pv is not None:
            pitch = _fold(int(round(pv)), *BASS_RANGE)
        elif rms > silence:
            root = chord_at((a + b) / 2)
            if root is not None:
                pitch = _fold(36 + root, *BASS_RANGE)
        if pitch is None:
            continue
        events.append([pitch, a, b, vel_of(rms), drive_at(a)])

    out = []
    for pitch, a, b, vel, drive in events:
        if not drive and out and out[-1].pitch == pitch \
                and abs(out[-1].end - a) < 0.06:
            out[-1].end = b - 0.02 * (b - a)   # pad: sustain through
            continue
        gate = 0.82 if drive else 0.98
        out.append(Note(start=a, end=a + gate * (b - a), pitch=pitch,
                        volume=_v(vel, 9, 14), duty=0.25))
    return out


KICK_DUCK = 0.075


def inject_kicks(bass_notes, kick_times):
    """The LSDJ move: every kick is a fast pitch-sweep on pulse 2; the bass
    ducks around it. Returns the merged pulse-2 note list."""
    kicks = sorted(kick_times)
    ducked = []
    for n in sorted(bass_notes, key=lambda x: x.start):
        segs = [(n.start, n.end)]
        for k in kicks:
            if k >= n.end or k + KICK_DUCK <= n.start:
                continue
            new = []
            for s0, s1 in segs:
                if k <= s0 and k + KICK_DUCK >= s1:
                    continue
                if s0 < k:
                    new.append((s0, min(s1, k)))
                if s1 > k + KICK_DUCK:
                    new.append((max(s0, k + KICK_DUCK), s1))
            segs = new
        for s0, s1 in segs:
            if s1 - s0 >= 0.04:
                ducked.append(Note(start=s0, end=s1, pitch=n.pitch,
                                   volume=n.volume, duty=n.duty))
    ducked.extend(
        Note(start=k, end=k + 0.07, pitch=74, volume=15, env_period=1,
             duty=0.50, sweep_semitones=-38.0, sweep_s=0.05)
        for k in kicks)
    return sorted(ducked, key=lambda n: n.start)


# ----------------------------------------------------------- percussion --
NOISE_PRESETS = {
    #        vol_hi env  shift w7    length
    "kick":  (12,   1,   6,    False, 0.08),   # thump; the sweep carries it
    "snare": (13,   1,   4,    False, 0.16),
    "hat":   (8,    1,   1,    True,  0.045),
}
_PRIORITY = {"snare": 2, "kick": 1, "hat": 0}


def arrange_noise(hits, grid):
    """Snap classified hits to 16th cells; one hit per cell on the single
    noise channel (snare > kick > hat). Returns (noise_hits, kick_times)."""
    best = {}
    for t, kind, strength in hits:
        cell = grid.snap16(t)
        cur = best.get(cell)
        if cur is None or (_PRIORITY[kind], strength) > (_PRIORITY[cur[0]], cur[1]):
            best[cell] = (kind, strength)
    out, kicks = [], []
    for cell in sorted(best):
        kind, strength = best[cell]
        vol_hi, env, shift, w7, length = NOISE_PRESETS[kind]
        vol = max(6, int(round(vol_hi * (0.6 + 0.4 * strength))))
        out.append(NoiseHit(start=cell, volume=min(15, vol), env_period=env,
                            clock_shift=shift, divisor_code=0, width7=w7,
                            length=length))
        if kind == "kick":
            kicks.append(cell)
    for h, nxt in zip(out, out[1:]):
        h.length = min(h.length, max(0.02, nxt.start - h.start))
    return out, kicks


# -------------------------------------------------------------- assembly --
def drive_profile(drum_hits, other_track, chords):
    """Per half-bar: is this a driving section (busy drums / loud band) or a
    pad section? Steers the wave pattern and bass articulation."""
    t = np.array(other_track["t"])
    r = np.array(other_track["r"])
    loud = np.percentile(r[r > 0], 65) if (r > 0).any() else 0.0
    hit_times = np.array([h[0] for h in drum_hits]) if drum_hits else np.array([])
    out = []
    for a, b, _, _ in chords:
        n_hits = int(((hit_times >= a) & (hit_times < b)).sum()) if len(hit_times) else 0
        sel = (t >= a) & (t < b)
        rms = float(r[sel].mean()) if sel.any() else 0.0
        out.append(n_hits >= 5 or rms >= loud)
    return out


def build_plan(name, stems, work_dir, duration, other_notes, drum_hits,
               wavetable="saw"):
    """Everything above, wired together. Returns (ChannelPlan, stats)."""
    from gb_apu import ChannelPlan

    grid, measured = load_grid(name, duration)

    vocal_track = extract_pitch(
        stems["vocals"], os.path.join(work_dir, f"{name}.vocals.pyin.json"),
        "E2", "A5")
    bass_track = extract_pitch(
        stems["bass"], os.path.join(work_dir, f"{name}.bass.pyin.json"),
        "E1", "G3", frame=4096)
    other_track = extract_pitch(   # only its RMS is used (drive profile)
        stems["other"], os.path.join(work_dir, f"{name}.other.pyin.json"),
        "E2", "A5")

    chords = detect_chords(
        stems["other"], grid, os.path.join(work_dir, f"{name}.chords2.json"),
        bass_path=stems["bass"])
    drive = drive_profile(drum_hits, other_track, chords)

    lead, n_fills = arrange_lead(vocal_track, other_notes, grid)
    noise, kick_times = arrange_noise(drum_hits, grid)
    bass = arrange_bass(bass_track, chords, grid, drive)
    pulse2 = inject_kicks(bass, kick_times)
    wave = arrange_wave(chords, grid, drive)

    named = sum(1 for *_, r, k in chords if r is not None)
    stats = {
        "grid": "measured" if measured else "tracked",
        "chords_named": f"{named}/{len(chords)}",
        "drive_windows": f"{sum(drive)}/{len(drive)}",
        "lead_fills": n_fills,
        "kicks_swept": len(kick_times),
    }
    plan = ChannelPlan(pulse1=lead, pulse2=pulse2, wave=wave, noise=noise,
                       wavetable=wavetable)
    return plan, stats
