"""Audio → authentic 8-bit Game Boy audio, end to end.

The original gbmusic pipeline (convert.py) stops at an .lsdsng project that
needs LSDJ to be heard. This renderer goes all the way to sound:

    input.mp3
      | soundfile decode (wav for the separator)
      v
    Demucs htdemucs -> vocals / bass / other / drums stems
      |                                            |
      | pYIN f0 + basic-pitch + chroma chords      | onset detect + spectral
      v                                            v  band split
    arrange.py (the v2 cover engine):           kick / snare / hat
      vocals -> pulse 1  (pYIN-traced lead, vibrato, instrumental fills)
      bass   -> pulse 2  (pYIN + chord roots, staccato 8ths, sweep kicks)
      chords -> wave     (detected progression -> authored arp patterns)
      drums  -> noise    (grid-snapped, one hit per 16th, 3 LFSR presets)
      |
      v
    gb_apu.render_song  ->  44.1 kHz stereo  ->  MP3 (lameenc)

Everything is quantized to the song's own measured beat grid
(src/data/content/songs/<id>.json, the grid the game judges by), so the
render is machine-tight and stays sample-aligned with the original — the
same beat maps judge both versions.

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
import arrange
from gb_apu import render_song

STEM_NAMES = ["vocals", "bass", "drums", "other"]


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
           report_path=None, style="balanced"):
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

    print(f"[4/5] arranging the cover (v6, style={style}) + coverage + APU render")
    plan, arr_stats = arrange.build_plan(
        name, stems, work_dir, duration, trans["other"], hits,
        bass_notes=trans["bass"], trans=trans, mix_path=input_path,
        wavetable=wavetable, style=style)
    counts = dict(pulse1=len(plan.pulse1), pulse2=len(plan.pulse2),
                  wave=len(plan.wave), noise=len(plan.noise))
    print(f"      events: {counts}")
    print(f"      arrangement: {arr_stats}")
    sr = 44100
    echo = (arr_stats["echo_delay_s"], 0.4, arr_stats["echo_wet"])
    audio = render_song(plan, duration, sr=sr, stereo=stereo,
                        mix=(1.0, 0.86, arr_stats["mix_wave"], 0.5), echo=echo)

    print("[5/5] QA + encode")
    print(f"      melody agreement (is it the tune): {arr_stats.get('melody_agreement')}")
    sim = chroma_similarity(input_path, audio, sr)
    print(f"      chroma similarity vs original: {sim:.3f}")
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    write_mp3(output_path, audio, sr)
    out_dur = len(audio) / sr
    print(f"      wrote {output_path} ({out_dur:.1f}s, "
          f"{os.path.getsize(output_path) / 1e6:.1f} MB)")

    report = dict(song=name, duration_s=round(duration, 2),
                  rendered_s=round(out_dur, 2), events=counts,
                  style=style, arrangement=arr_stats,
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
    ap.add_argument("--style", default="balanced",
                    choices=("clean", "balanced", "full"),
                    help="production style / density (see arrange.STYLES)")
    args = ap.parse_args()

    if args.work_dir:
        render(args.input, args.output, args.work_dir, args.wavetable,
               stereo=not args.mono, report_path=args.report, style=args.style)
    else:
        with tempfile.TemporaryDirectory() as td:
            render(args.input, args.output, td, args.wavetable,
                   stereo=not args.mono, report_path=args.report, style=args.style)


if __name__ == "__main__":
    main()
