"""
Picks non-overlapping timestamp ranges from the source master for each
battle-track stage in PRD §8.6/§8.7, ordered so musical complexity rises
alongside encounter difficulty (opening biome = calmest section found,
boss phase 3 = busiest).

Complexity per candidate window = weighted mean of normalized onset-strength,
RMS energy, and spectral centroid (0.5 / 0.3 / 0.2) — rhythmic density
weighted highest since that's what the game's mechanics actually track.
For each stage, in ascending complexity-target order, we take the
non-overlapping candidate window closest to that stage's target percentile
of the complexity distribution, then block out that time range before
picking the next stage. This is an algorithmic starting point for music
direction, not a substitute for a human listening pass — see
docs/design/music-direction.md.
"""

import json
import os

import librosa
import numpy as np

MASTER_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..",
    "assets", "reference", "audio-demo", "AmirsMaster-ForDylanWithBabyVocals.mp3",
)
OUTPUT_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stage_slices.json")

MARGIN_SECONDS = 10.0  # skip intro/outro fades
STEP_SECONDS = 5.0

# (stage name, duration seconds) in ascending complexity-target order.
STAGES = [
    ("opening_biome", 75),
    ("mid_biome_1", 60),
    ("mid_biome_2_clave", 55),
    ("mid_biome_3_syncopated", 55),
    ("boss_phase_1", 45),
    ("boss_phase_2", 45),
    ("boss_phase_3", 50),
]


def _normalize(values):
    return (values - values.min()) / (values.ptp() + 1e-9)


def _windowed_mean(values, times, start, end):
    mask = (times >= start) & (times < end)
    if not mask.any():
        return 0.0
    return float(values[mask].mean())


def select_slices():
    y, sr = librosa.load(MASTER_PATH, sr=22050, mono=True)
    duration = librosa.get_duration(y=y, sr=sr)

    onset_env = _normalize(librosa.onset.onset_strength(y=y, sr=sr))
    onset_times = librosa.times_like(onset_env, sr=sr)
    rms = _normalize(librosa.feature.rms(y=y)[0])
    rms_times = librosa.times_like(rms, sr=sr)
    centroid = _normalize(librosa.feature.spectral_centroid(y=y, sr=sr)[0])
    cen_times = librosa.times_like(centroid, sr=sr)

    def complexity(start, end):
        o = _windowed_mean(onset_env, onset_times, start, end)
        r = _windowed_mean(rms, rms_times, start, end)
        c = _windowed_mean(centroid, cen_times, start, end)
        return 0.5 * o + 0.3 * r + 0.2 * c

    max_stage_duration = max(d for _, d in STAGES)
    candidates = []
    t = MARGIN_SECONDS
    while t + max_stage_duration <= duration - MARGIN_SECONDS:
        candidates.append(t)
        t += STEP_SECONDS

    scored = {
        name: sorted(
            ((start, complexity(start, start + d)) for start in candidates if start + d <= duration - MARGIN_SECONDS),
            key=lambda x: x[1],
        )
        for name, d in STAGES
    }

    used_intervals = []

    def overlaps(a_start, a_end):
        return any(a_start < e and s < a_end for s, e in used_intervals)

    n = len(STAGES)
    results = {}
    for i, (name, d) in enumerate(STAGES):
        target_percentile = (i + 0.5) / n
        pool = scored[name]
        target_idx = int(target_percentile * (len(pool) - 1))
        order = sorted(range(len(pool)), key=lambda idx: abs(idx - target_idx))
        chosen = next(((pool[idx][0], pool[idx][1]) for idx in order if not overlaps(pool[idx][0], pool[idx][0] + d)), None)
        if chosen is None:
            raise RuntimeError(f"No non-overlapping slot found for stage '{name}'")
        start, score = chosen
        used_intervals.append((start, start + d))
        results[name] = {"start": round(start, 1), "duration": d, "complexity_score": round(score, 3)}

    return results


if __name__ == "__main__":
    slices = select_slices()
    with open(OUTPUT_JSON, "w") as f:
        json.dump(slices, f, indent=2)
    for name, info in slices.items():
        mm, ss = divmod(int(info["start"]), 60)
        print(f"{name:24s} start={info['start']:7.1f}s ({mm:02d}:{ss:02d})  duration={info['duration']:4d}s  complexity={info['complexity_score']:.3f}")
    print(f"\nWrote {OUTPUT_JSON}")
