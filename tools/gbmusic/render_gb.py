"""Audio → authentic 8-bit Game Boy audio, end to end.

The original gbmusic pipeline (convert.py) stops at an .lsdsng project that
needs LSDJ to be heard. This renderer goes all the way to sound:

    input.mp3
      | soundfile decode (wav for the separator)
      v
    Demucs htdemucs -> vocals / bass / other / drums stems
      |                                            |
      | basic-pitch (audio->MIDI notes)            | onset detect + spectral
      v                                            v  band split
    arrangement (this file):                    kick / snare / hat
      vocals -> pulse 1  (50% duty lead, vibrato on held notes)
      bass   -> pulse 2  (25% duty, octave-folded into GB range)
      other  -> wave     (chords collapsed to LSDJ-style arpeggios)
      drums  -> noise    (three LFSR presets by hit class)
      |
      v
    gb_apu.render_song  ->  44.1 kHz stereo  ->  MP3 (lameenc)

Note timestamps are never quantized or tempo-mapped: every event lands at
the second it occurs in the recording, so the output is sample-aligned with
the original and the measured beat grids in src/data/content/songs/ remain
valid for both versions.

Usage:
    python3 render_gb.py input.mp3 output.mp3 [--work-dir DIR]
        [--wavetable saw|triangle|organ] [--mono] [--report out.json]

Stems and transcriptions are cached in --work-dir, so re-renders after
arrangement tweaks skip the expensive Demucs/basic-pitch steps.
"""

import argparse
import json
import os
import sys
import tempfile

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gb_apu import ChannelPlan, Note, NoiseHit, render_song

STEM_NAMES = ["vocals", "bass", "drums", "other"]

# Register ranges (MIDI) each channel gets folded into by octaves.
LEAD_RANGE = (55, 89)    # G3..F6
BASS_RANGE = (36, 62)    # C2 (the pulse register floor is 64 Hz)..D4
WAVE_RANGE = (43, 84)    # G2..C6

MIN_NOTE_LEN = 0.055
MERGE_GAP = 0.035


# ---------------------------------------------------------------- stems --
def decode_to_wav(mp3_path, wav_path):
    y, sr = sf.read(mp3_path, dtype="float32", always_2d=True)
    sf.write(wav_path, y, sr)
    return len(y) / sr


def separate(wav_path, work_dir, model="htdemucs"):
    """Demucs via its Python API (torchaudio's file loader now requires
    torchcodec/ffmpeg, so we hand it a soundfile-loaded tensor instead)."""
    out_root = os.path.join(work_dir, "demucs_out")
    track = os.path.splitext(os.path.basename(wav_path))[0]
    stem_dir = os.path.join(out_root, model, track)
    stems = {n: os.path.join(stem_dir, f"{n}.wav") for n in STEM_NAMES}
    if all(os.path.exists(p) for p in stems.values()):
        print(f"      stems cached in {stem_dir}")
        return stems

    import torch
    from demucs.apply import apply_model
    from demucs.pretrained import get_model

    y, sr = sf.read(wav_path, dtype="float32", always_2d=True)
    m = get_model(model)
    if sr != m.samplerate:
        import librosa
        y = librosa.resample(y.T, orig_sr=sr, target_sr=m.samplerate).T
        sr = m.samplerate
    if y.shape[1] == 1:
        y = np.repeat(y, 2, axis=1)

    wav = torch.from_numpy(y.T.copy())
    ref = wav.mean(0)
    wav = (wav - ref.mean()) / (ref.std() + 1e-8)
    with torch.no_grad():
        sources = apply_model(m, wav[None], device="cpu", split=True,
                              overlap=0.25, progress=True)[0]
    sources = sources * (ref.std() + 1e-8) + ref.mean()

    os.makedirs(stem_dir, exist_ok=True)
    for name, src in zip(m.sources, sources):
        sf.write(os.path.join(stem_dir, f"{name}.wav"), src.numpy().T, sr)
    missing = [n for n, p in stems.items() if not os.path.exists(p)]
    if missing:
        raise RuntimeError(f"Demucs did not produce stems: {missing}")
    return stems


# -------------------------------------------------------- transcription --
def transcribe_pitched(path, cache_path):
    """basic-pitch a stem -> [[pitch, start, end, velocity], ...] (cached)."""
    if os.path.exists(cache_path):
        with open(cache_path) as f:
            return json.load(f)
    from basic_pitch.inference import predict
    _, midi_data, _ = predict(str(path))
    notes = []
    for inst in midi_data.instruments:
        for n in inst.notes:
            notes.append([int(n.pitch), float(n.start), float(n.end), int(n.velocity)])
    with open(cache_path, "w") as f:
        json.dump(notes, f)
    return notes


def classify_drums(path, cache_path):
    """Onset-detect the drum stem and split hits into kick/snare/hat by
    spectral band energy. Returns [[t, kind, strength01], ...] (cached)."""
    if os.path.exists(cache_path):
        with open(cache_path) as f:
            return json.load(f)
    import librosa
    y, sr = librosa.load(path, sr=None, mono=True)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    onsets = librosa.onset.onset_detect(
        y=y, sr=sr, onset_envelope=onset_env, units="time")
    strengths = librosa.onset.onset_detect(
        y=y, sr=sr, onset_envelope=onset_env, units="frames")
    peak_vals = onset_env[strengths] if len(strengths) else np.array([1.0])
    ref = float(np.percentile(peak_vals, 90)) or 1.0

    win = int(0.06 * sr)
    hits = []
    for t, fr in zip(onsets, strengths):
        i0 = int(t * sr)
        seg = y[i0:i0 + win]
        if len(seg) < 32:
            continue
        spec = np.abs(np.fft.rfft(seg * np.hanning(len(seg))))
        freqs = np.fft.rfftfreq(len(seg), 1.0 / sr)
        total = float(np.sum(spec)) or 1.0
        low = float(np.sum(spec[freqs < 150])) / total
        mid = float(np.sum(spec[(freqs >= 150) & (freqs < 2000)])) / total
        centroid = float(np.sum(spec * freqs)) / total
        # Rules calibrated on the separated drum stems: kicks carry the low
        # band; snares are mid-heavy with no low; hats are all sizzle.
        # Mixed strikes (kick+hat on the same onset) go to the kick — the
        # backbone matters most on a single noise channel.
        if low >= 0.30:
            kind = "kick"
        elif centroid >= 5200 and low <= 0.10:
            kind = "hat"
        elif mid >= 0.30 and low <= 0.10:
            kind = "snare"
        elif low >= 0.15:
            kind = "kick"
        else:
            kind = "hat" if centroid >= 4800 else "snare"
        strength = float(min(1.0, onset_env[fr] / ref))
        hits.append([float(t), kind, strength])
    with open(cache_path, "w") as f:
        json.dump(hits, f)
    return hits


# ---------------------------------------------------------- arrangement --
def _fold_into(pitch, lo, hi):
    while pitch < lo:
        pitch += 12
    while pitch > hi:
        pitch -= 12
    return pitch


def _center_octave(notes, target):
    """Shift the whole stem by octaves so its median lands near `target` —
    per-note folding alone would break phrases that cross the range edge."""
    if not notes:
        return notes
    med = float(np.median([n[0] for n in notes]))
    shift = 12 * round((target - med) / 12.0)
    return [[p + shift, s, e, v] for p, s, e, v in notes]


def _vel_to_vol(vel, lo=7, hi=15):
    return int(round(lo + (hi - lo) * min(127, vel) / 127.0))


_PREFER_KEY = {
    "velocity": lambda n: -n[3],
    "low": lambda n: n[0],
    "high": lambda n: -n[0],
}


def make_monophonic(notes, prefer="velocity"):
    """Overlap-trim [pitch,start,end,vel] into a strictly monophonic line.

    Later notes steal (hardware behavior). When two notes start together,
    keep the preferred one: higher velocity, lowest pitch, or highest pitch.
    """
    key = _PREFER_KEY[prefer]
    notes = sorted(notes, key=lambda n: (n[1], key(n)))
    out = []
    for p, s, e, v in notes:
        if e - s <= 0:
            continue
        if out:
            lp, ls, le, lv = out[-1]
            if s < le:                     # overlaps the running note
                if abs(s - ls) < 0.010:    # same strike: keep preferred (first)
                    continue
                out[-1] = [lp, ls, s, lv]  # trim the running note
                if out[-1][2] - out[-1][1] < MIN_NOTE_LEN:
                    out.pop()
        out.append([p, s, e, v])
    # merge same-pitch notes separated by a tiny gap; drop dust
    merged = []
    for p, s, e, v in out:
        if merged and merged[-1][0] == p and s - merged[-1][2] <= MERGE_GAP:
            merged[-1][2] = e
            continue
        merged.append([p, s, e, v])
    return [n for n in merged if n[2] - n[1] >= MIN_NOTE_LEN]


MIN_LEAD_VEL = 22       # basic-pitch picks up stem bleed as quiet ghost notes
LEAD_FILL_GAP = 1.5     # vocal rests longer than this get an instrumental fill


def arrange_lead(vocal_notes, other_notes, duration):
    """Vocals become the pulse-1 lead. Where the vocal rests, borrow the top
    line of the 'other' stem so the lead channel never sits idle — the
    classic chiptune-cover arrangement move."""
    vocal_notes = [n for n in vocal_notes if n[3] >= MIN_LEAD_VEL]
    vocal_notes = _center_octave(vocal_notes, 72)
    mono = make_monophonic(
        [[_fold_into(p, *LEAD_RANGE), s, e, v] for p, s, e, v in vocal_notes])

    gaps = []
    cursor = 0.0
    for p, s, e, v in mono + [[0, duration, duration, 0]]:
        if s - cursor >= LEAD_FILL_GAP:
            gaps.append((cursor, s))
        cursor = max(cursor, e)

    fills = []
    for ga, gb in gaps:
        inside = [[p, max(s, ga + 0.05), min(e, gb - 0.05), v]
                  for p, s, e, v in other_notes
                  if min(e, gb - 0.05) - max(s, ga + 0.05) >= MIN_NOTE_LEN]
        if not inside:
            continue
        inside = [[_fold_into(p, *LEAD_RANGE), s, e, v] for p, s, e, v in
                  _center_octave(inside, 74)]
        fills.extend(make_monophonic(inside, prefer="high"))

    out = [Note(start=s, end=e, pitch=p, volume=_vel_to_vol(v, 9, 15),
                duty=0.50, vibrato_cents=22.0 if (e - s) >= 0.35 else 0.0)
           for p, s, e, v in mono]
    # instrumental fills: thinner duty + a step quieter, so verses with real
    # vocals still read as the song's foreground
    out.extend(Note(start=s, end=e, pitch=p,
                    volume=min(13, _vel_to_vol(v, 8, 13)), duty=0.25,
                    vibrato_cents=14.0 if (e - s) >= 0.45 else 0.0)
               for p, s, e, v in fills)
    return sorted(out, key=lambda n: n.start), len(fills)


def arrange_bass(notes):
    notes = _center_octave(notes, 45)
    mono = make_monophonic(
        [[_fold_into(p, *BASS_RANGE), s, e, v] for p, s, e, v in notes],
        prefer="low")
    return [Note(start=s, end=e, pitch=p, volume=_vel_to_vol(v, 8, 14), duty=0.25)
            for p, s, e, v in mono]


def arrange_wave(notes):
    """Collapse the polyphonic 'other' stem into non-overlapping segments;
    chords become LSDJ-style arpeggios over up to 4 tones. Sweep-based:
    between consecutive note boundaries the active set is constant."""
    notes = [[_fold_into(p, *WAVE_RANGE), s, e, v] for p, s, e, v in notes
             if e - s >= MIN_NOTE_LEN]
    if not notes:
        return []
    starts = sorted(range(len(notes)), key=lambda i: notes[i][1])
    ends = sorted(range(len(notes)), key=lambda i: notes[i][2])
    edges = sorted({round(t, 4) for n in notes for t in (n[1], n[2])})
    active = set()
    si = ei = 0
    out = []
    for a, b in zip(edges, edges[1:]):
        while si < len(starts) and notes[starts[si]][1] <= a + 1e-6:
            active.add(starts[si]); si += 1
        while ei < len(ends) and notes[ends[ei]][2] <= a + 1e-6:
            active.discard(ends[ei]); ei += 1
        if not active or b - a < 0.045:
            continue
        act = sorted(active, key=lambda i: (-notes[i][3], notes[i][0]))[:4]
        tones = sorted({notes[i][0] for i in act})
        vol = _vel_to_vol(max(notes[i][3] for i in act), 7, 15)
        note = Note(start=a, end=b, pitch=tones[0],
                    arp_pitches=tuple(tones[1:]), volume=vol)
        # extend the previous segment instead of re-striking the same voicing
        if out and out[-1].pitch == note.pitch and out[-1].arp_pitches == note.arp_pitches \
                and abs(out[-1].end - a) < 0.02:
            out[-1].end = b
        else:
            out.append(note)
    return out


NOISE_PRESETS = {
    #        vol_hi env  shift div  w7    length
    "kick":  (15,   1,   7,    0,   False, 0.30),
    "snare": (13,   1,   4,    0,   False, 0.26),
    "hat":   (10,   1,   1,    0,   True,  0.07),
}


def arrange_noise(hits):
    out = []
    for t, kind, strength in hits:
        vol_hi, env, shift, div, w7, length = NOISE_PRESETS[kind]
        vol = max(6, int(round(vol_hi * (0.55 + 0.45 * strength))))
        out.append(NoiseHit(start=t, volume=min(15, vol), env_period=env,
                            clock_shift=shift, divisor_code=div,
                            width7=w7, length=length))
    # Hardware note-steal: a retrigger kills the previous hit's tail. The
    # renderer paints hits independently, so without this clamp a kick's
    # decay would resurface after a hat inside it ends.
    out.sort(key=lambda h: h.start)
    for h, nxt in zip(out, out[1:]):
        h.length = min(h.length, max(0.02, nxt.start - h.start))
    return out


# ------------------------------------------------------------------ QA --
def chroma_similarity(orig_path, rendered, sr):
    """Mean cosine similarity of beat-scale chroma between original and
    render — a smoke test that the transcription kept the harmony."""
    import librosa
    y_o, sr_o = librosa.load(orig_path, sr=22050, mono=True)
    y_r = librosa.resample(rendered.mean(axis=1), orig_sr=sr, target_sr=22050)
    n = min(len(y_o), len(y_r))
    c_o = librosa.feature.chroma_cqt(y=y_o[:n], sr=22050, hop_length=4096)
    c_r = librosa.feature.chroma_cqt(y=y_r[:n], sr=22050, hop_length=4096)
    m = min(c_o.shape[1], c_r.shape[1])
    c_o, c_r = c_o[:, :m], c_r[:, :m]
    num = np.sum(c_o * c_r, axis=0)
    den = np.linalg.norm(c_o, axis=0) * np.linalg.norm(c_r, axis=0) + 1e-9
    return float(np.mean(num / den))


# ---------------------------------------------------------------- main --
def _encode_mp3(path, audio, sr, bitrate):
    import lameenc
    enc = lameenc.Encoder()
    enc.set_bit_rate(bitrate)
    enc.set_in_sample_rate(sr)
    enc.set_channels(audio.shape[1])
    enc.set_quality(2)
    pcm = np.clip(audio * 32767.0, -32768, 32767).astype(np.int16)
    data = enc.encode(pcm.tobytes())
    data += enc.flush()
    with open(path, "wb") as f:
        f.write(bytes(data))


def _decode_lag(path, audio, sr, search=0.1):
    """Samples of extra latency the encode+decode round trip added at the
    front (LAME encoder delay), measured by cross-correlation."""
    from scipy import signal as sps
    y, sr2 = sf.read(path, dtype="float32", always_2d=True)
    if sr2 != sr:
        return 0
    n = min(len(y), len(audio), 5 * sr)
    a = audio[:n].mean(axis=1)
    b = y[:n].mean(axis=1)
    w = int(search * sr)
    corr = sps.correlate(b, a, mode="full", method="fft")
    center = n - 1
    window = corr[center - w:center + w + 1]
    return int(np.argmax(window)) - w


def write_mp3(path, audio, sr, bitrate=128):
    """Encode so that the DECODED file is sample-aligned with `audio`.

    LAME prepends an encoder delay (~1100 samples) that players which don't
    honor gapless metadata (HTMLAudioElement among them) never strip. The
    beat grids are measured on the original files' decoded timeline (PRD
    §8.3), so a constant ~25 ms skew here would land every judged beat late
    in 8-bit mode. Encode, measure the real round-trip lag, then re-encode
    with the front trimmed by exactly that much.
    """
    _encode_mp3(path, audio, sr, bitrate)
    lag = _decode_lag(path, audio, sr)
    if lag > 0:
        _encode_mp3(path, audio[lag:], sr, bitrate)
        lag = _decode_lag(path, audio, sr)  # residual vs the ORIGINAL timeline
    print(f"      decode alignment: residual lag {lag} samples "
          f"({lag * 1000.0 / sr:+.1f} ms)")


def render(input_path, output_path, work_dir, wavetable="saw", stereo=True,
           report_path=None):
    os.makedirs(work_dir, exist_ok=True)
    name = os.path.splitext(os.path.basename(input_path))[0]

    print(f"[1/5] decoding {input_path}")
    wav_path = os.path.join(work_dir, f"{name}.wav")
    if not os.path.exists(wav_path):
        duration = decode_to_wav(input_path, wav_path)
    else:
        info = sf.info(wav_path)
        duration = info.frames / info.samplerate
    print(f"      duration {duration:.1f}s")

    print("[2/5] separating stems (Demucs htdemucs)")
    stems = separate(wav_path, work_dir)

    print("[3/5] transcribing stems (basic-pitch) + classifying drums")
    trans = {}
    for stem in ("vocals", "bass", "other"):
        cache = os.path.join(work_dir, f"{name}.{stem}.notes.json")
        trans[stem] = transcribe_pitched(stems[stem], cache)
        print(f"      {stem}: {len(trans[stem])} raw notes")
    drum_cache = os.path.join(work_dir, f"{name}.drums.json")
    hits = classify_drums(stems["drums"], drum_cache)
    kinds = {k: sum(1 for h in hits if h[1] == k) for k in ("kick", "snare", "hat")}
    print(f"      drums: {len(hits)} hits {kinds}")

    print("[4/5] arranging four channels + APU render")
    lead, n_fills = arrange_lead(trans["vocals"], trans["other"], duration)
    plan = ChannelPlan(
        pulse1=lead,
        pulse2=arrange_bass(trans["bass"]),
        wave=arrange_wave(trans["other"]),
        noise=arrange_noise(hits),
        wavetable=wavetable,
    )
    counts = dict(pulse1=len(plan.pulse1), pulse2=len(plan.pulse2),
                  wave=len(plan.wave), noise=len(plan.noise))
    print(f"      events: {counts} (lead fills borrowed from 'other': {n_fills})")
    sr = 44100
    audio = render_song(plan, duration, sr=sr, stereo=stereo)

    print("[5/5] QA + encode")
    sim = chroma_similarity(input_path, audio, sr)
    print(f"      chroma similarity vs original: {sim:.3f}")
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    write_mp3(output_path, audio, sr)
    out_dur = len(audio) / sr
    print(f"      wrote {output_path} ({out_dur:.1f}s, "
          f"{os.path.getsize(output_path) / 1e6:.1f} MB)")

    report = dict(song=name, duration_s=round(duration, 2),
                  rendered_s=round(out_dur, 2), events=counts,
                  drum_kinds=kinds, chroma_similarity=round(sim, 3))
    if report_path:
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--work-dir", default=None,
                    help="cache dir for stems/transcriptions (default: temp)")
    ap.add_argument("--wavetable", default="saw",
                    choices=("saw", "triangle", "organ"))
    ap.add_argument("--mono", action="store_true")
    ap.add_argument("--report", default=None, help="write a JSON QA report")
    args = ap.parse_args()

    if args.work_dir:
        render(args.input, args.output, args.work_dir, args.wavetable,
               stereo=not args.mono, report_path=args.report)
    else:
        with tempfile.TemporaryDirectory() as td:
            render(args.input, args.output, td, args.wavetable,
                   stereo=not args.mono, report_path=args.report)


if __name__ == "__main__":
    main()
