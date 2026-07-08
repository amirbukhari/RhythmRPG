"""Splits a mixed audio file into vocals/bass/drums/other stems with Demucs.

These four stems map directly onto the Game Boy's four sound channels:
vocals -> pulse 1 (lead), bass -> pulse 2, other (harmony/instruments) ->
wave, drums -> noise.
"""

import os
import subprocess
import sys

STEM_NAMES = ["vocals", "bass", "drums", "other"]


def separate(audio_path, work_dir, model="htdemucs"):
    """Runs Demucs on audio_path. Returns {stem_name: wav_path}."""
    out_root = os.path.join(work_dir, "demucs_out")
    cmd = [
        sys.executable, "-m", "demucs.separate",
        "-n", model,
        "-o", out_root,
        audio_path,
    ]
    subprocess.run(cmd, check=True)

    track_name = os.path.splitext(os.path.basename(audio_path))[0]
    stem_dir = os.path.join(out_root, model, track_name)
    stems = {name: os.path.join(stem_dir, f"{name}.wav") for name in STEM_NAMES}
    missing = [name for name, path in stems.items() if not os.path.exists(path)]
    if missing:
        raise RuntimeError(f"Demucs did not produce expected stems: {missing} (looked in {stem_dir})")
    return stems
