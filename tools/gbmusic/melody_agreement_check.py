"""Diagnostic: does the render reproduce the actual MELODY of the song?

Extracts the dominant melodic line (with octave) from the original mix and
from the GB render, then measures how often the render's melody pitch
matches the original's — the real 'sounds like the tune' number that chroma
and pitch-class recall both miss.
"""
import sys
import numpy as np
import librosa

MEL_LO, MEL_HI = "C3", "C6"


def melody(path, hop=256):
    y, sr = librosa.load(path, sr=22050, mono=True)
    fmin = librosa.note_to_hz("C1")
    C = np.abs(librosa.cqt(y, sr=sr, hop_length=hop, fmin=fmin,
                           n_bins=72, bins_per_octave=12))
    freqs = librosa.cqt_frequencies(72, fmin=fmin, bins_per_octave=12)
    S = librosa.salience(C, freqs=freqs, harmonics=[1, 2, 3, 4, 5],
                         weights=[1.0, 0.5, 0.4, 0.3, 0.2], fill_value=0.0)
    lo = librosa.note_to_midi(MEL_LO) - 24   # bin index (C1 = midi 24)
    hi = librosa.note_to_midi(MEL_HI) - 24
    band = S[lo:hi + 1]
    mel_bin = lo + np.argmax(band, axis=0)
    strength = band.max(axis=0)
    voiced = strength > np.percentile(strength[strength > 0], 40)
    midi = 24 + mel_bin.astype(float)
    # median-smooth to drop spurious single-frame jumps
    from scipy.ndimage import median_filter
    midi = median_filter(midi, size=7)
    return midi, voiced, librosa.times_like(S, sr=sr, hop_length=hop)


def compare(orig, rend):
    mo, vo, to = melody(orig)
    mr, vr, tr = melody(rend)
    n = min(len(mo), len(mr))
    mo, vo, mr = mo[:n], vo[:n], mr[:n]
    sel = vo
    exact = np.abs(mo - mr) <= 1.0                 # same pitch AND octave
    pc = (np.abs(mo - mr) % 12)
    pcok = np.minimum(pc, 12 - pc) <= 1.0          # same pitch class only
    return float(exact[sel].mean()), float(pcok[sel].mean())


if __name__ == "__main__":
    for song in sys.argv[1:]:
        o = f"/home/user/RhythmRPG/assets/audio/{song}.mp3"
        r = f"/home/user/RhythmRPG/assets/audio/gb8/{song}.mp3"
        ex, pc = compare(o, r)
        print(f"{song:22s} melody exact(+octave) {ex:5.0%}   pitch-class {pc:5.0%}")
