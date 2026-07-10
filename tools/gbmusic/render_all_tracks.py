"""
Renders every stage/boss-phase .lsdsng draft to a loop-ready battle track in
assets/audio/battle/, tempo- and loop-aligned to its beatmap.

For each (draft, beatmap) pair this:
  1. reads the beatmap's authored BPM and meterSequence from
     src/data/content/beatmaps/,
  2. computes the pattern loop length in quarter-note beats
     (sum of bars*num per meter segment -- the same math as
     src/systems/combat/MeterSequence.ts's patternLengthSeconds),
  3. renders the .lsdsng at the beatmap BPM, cut to the largest whole
     multiple of the pattern length (render_lsdsng.py --loop-beats), so the
     audio loops seamlessly against the in-game judgment grid,
  4. encodes to OGG Vorbis via ffmpeg for the web build.

Usage:  python3 render_all_tracks.py   (no args; paths are repo-relative)
"""

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BEATMAP_DIR = os.path.join(REPO, "src", "data", "content", "beatmaps")
OUT_DIR = os.path.join(REPO, "assets", "audio", "battle")

# draft .lsdsng -> the beatmap trackId it underlies (docs/design/music-direction.md)
TRACKS = {
    "opening_biome.lsdsng": "opening_biome_01",
    "mid_biome_1.lsdsng": "mid_biome_1_01",
    "mid_biome_2_clave.lsdsng": "mid_biome_2_clave_01",
    "mid_biome_3_syncopated.lsdsng": "mid_biome_3_syncopated_01",
    "boss_phase_1.lsdsng": "boss_conductor_p1",
    "boss_phase_2.lsdsng": "boss_conductor_p2",
    "boss_phase_3.lsdsng": "boss_conductor_p3",
}


def pattern_beats(meter_sequence):
    """Quarter-note beats in one full pattern loop; mirrors MeterSequence.ts
    (secondsPerBar = (60/bpm) * num, i.e. a bar is `num` quarter-note beats)."""
    return sum(seg["bars"] * seg["num"] for seg in meter_sequence)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    failures = []
    for lsdsng, track_id in TRACKS.items():
        beatmap_path = os.path.join(BEATMAP_DIR, f"{track_id}.json")
        with open(beatmap_path) as f:
            beatmap = json.load(f)
        bpm = beatmap["bpm"]
        loop_beats = pattern_beats(beatmap["meterSequence"])

        wav = os.path.join(OUT_DIR, f"{track_id}.wav")
        ogg = os.path.join(OUT_DIR, f"{track_id}.ogg")
        print(f"\n=== {lsdsng} -> {track_id}  (bpm={bpm}, loop={loop_beats} beats)")
        r = subprocess.run(
            [sys.executable, os.path.join(HERE, "render_lsdsng.py"),
             os.path.join(HERE, "output", lsdsng), wav,
             "--bpm", str(bpm), "--loop-beats", str(loop_beats)],
        )
        if r.returncode != 0:
            failures.append(track_id)
            continue
        r = subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", wav,
             "-c:a", "libvorbis", "-qscale:a", "4", ogg],
        )
        if r.returncode != 0:
            failures.append(track_id)
            continue
        os.remove(wav)
        print(f"  encoded {ogg} ({os.path.getsize(ogg) // 1024} KiB)")

    if failures:
        print(f"\nFAILED: {failures}")
        sys.exit(1)
    print(f"\nAll {len(TRACKS)} tracks rendered to {OUT_DIR}")


if __name__ == "__main__":
    main()
