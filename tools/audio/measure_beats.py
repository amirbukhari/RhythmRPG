#!/usr/bin/env python3
"""Measure per-track beat maps for the six Inhalants songs (PRD §8.3 / P1).

For each MP3 in assets/audio/ this runs librosa beat tracking and emits a song
beat map JSON into src/data/content/songs/:

  {
    "songId":            "glassriff",
    "bpm":               <fitted global BPM (nominal; HUD / tick rate)>,
    "firstBeatOffsetMs": <first tracked beat, ms into the file>,
    "durationMs":        <file duration, ms>,
    "beatTimesMs":       [<every tracked beat, ms>...]   // the judgment grid
  }

The full beatTimesMs grid is the source of truth for judgment (real band
recordings drift; a constant bpm+offset line is only the fallback/summary).
Judgment code (src/systems/audio/SongBeat.ts) snaps to the nearest grid entry.

These are algorithmically measured (librosa onset-strength beat tracker) and
validated by the stability metrics printed below. PRD §8.3 calls for a human
listening pass on top; re-run this script after any track changes:

  pip install numpy soundfile librosa
  python3 tools/audio/measure_beats.py
"""

import json
import os
import sys

import numpy as np
import librosa

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AUDIO = os.path.join(ROOT, "assets", "audio")
OUT = os.path.join(ROOT, "src", "data", "content", "songs")

SONGS = [
    "sunshine_sally",
    "deereater",
    "glassriff",
    "johns_anus",
    "truckers_for_christ",
    "quotience",
]


def measure(song_id: str) -> dict:
    path = os.path.join(AUDIO, f"{song_id}.mp3")
    y, sr = librosa.load(path, sr=22050, mono=True)
    duration = len(y) / sr

    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    tempo, beats = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr, trim=False, units="time")
    tempo = float(np.atleast_1d(tempo)[0])
    beats = np.asarray(beats, dtype=float)
    if len(beats) < 8:
        raise RuntimeError(f"{song_id}: beat tracker found only {len(beats)} beats")

    # Stability metrics: how well does a constant-BPM line fit the real grid?
    ibis = np.diff(beats)
    med = float(np.median(ibis))
    stable = float(np.mean(np.abs(ibis - med) < 0.05 * med))
    fitted_bpm = 60.0 / med

    return {
        "songId": song_id,
        "bpm": round(fitted_bpm, 2),
        "firstBeatOffsetMs": int(round(beats[0] * 1000)),
        "durationMs": int(round(duration * 1000)),
        "beatTimesMs": [int(round(b * 1000)) for b in beats],
        "_metrics": {
            "trackerTempo": round(tempo, 2),
            "beats": len(beats),
            "ibiMedianMs": int(round(med * 1000)),
            "ibiWithin5pct": round(stable, 3),
        },
    }


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    print(f"{'song':<22}{'bpm':>8}{'offset':>9}{'dur':>9}{'beats':>7}{'stable':>8}")
    for song_id in SONGS:
        m = measure(song_id)
        metrics = m.pop("_metrics")
        with open(os.path.join(OUT, f"{song_id}.json"), "w") as f:
            json.dump(m, f)
            f.write("\n")
        print(
            f"{song_id:<22}{m['bpm']:>8.2f}{m['firstBeatOffsetMs']/1000:>8.2f}s"
            f"{m['durationMs']/1000:>8.1f}s{metrics['beats']:>7}{metrics['ibiWithin5pct']:>8.1%}"
            + ("" if metrics["ibiWithin5pct"] > 0.85 else "   <-- drifty: grid (not bpm line) is authoritative")
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
