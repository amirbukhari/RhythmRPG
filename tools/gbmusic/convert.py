#!/usr/bin/env python3
"""
Audio -> Game Boy (LSDJ) chiptune conversion pipeline.

    input.mp3 --ffmpeg--> clip.wav --demucs--> {vocals,bass,drums,other}.wav
        --basic-pitch / onset-detect--> score.mid --pylsdj--> output.lsdsng

LSDJ's phrase/chain/instrument slots cap how much material fits in one
song (a few minutes at most), so by default this trims the input to a
--duration-second clip before processing. Pass --duration 0 to run the
whole file; the converter will print a warning and truncate if it runs
out of slots.

Usage:
    python3 convert.py <input_audio> <output.lsdsng> [--start 0] [--duration 60]

The output .lsdsng can be loaded into LSDJ (hardware, emulator, or the
sibling lsdj-midi-studio web app) to audition and hand-tune the result.
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

from separate_stems import separate  # noqa: E402
from transcribe import build_song_midi  # noqa: E402
from midi_to_lsdsng import convert_midi_to_lsdsng  # noqa: E402

DEFAULT_TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "drumbeat.lsdsng")

# vocals -> pulse1 (lead), bass -> pulse2, other -> wave, drums -> noise.
# Must match the channel numbers transcribe.py writes into the MIDI file.
CHANNEL_MAPPING = {"pu1": 0, "pu2": 1, "wav": 2, "noi": 9}


def trim_audio(input_path, out_path, start, duration):
    cmd = ["ffmpeg", "-y", "-i", input_path, "-ss", str(start)]
    if duration:
        cmd += ["-t", str(duration)]
    cmd += ["-ac", "2", "-ar", "44100", out_path]
    subprocess.run(cmd, check=True, capture_output=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input_audio")
    parser.add_argument("output_lsdsng")
    parser.add_argument("--start", type=float, default=0.0, help="Clip start offset in seconds (default: 0)")
    parser.add_argument(
        "--duration", type=float, default=60.0,
        help="Clip length in seconds, 0 for the full file (default: 60)",
    )
    parser.add_argument("--template", default=DEFAULT_TEMPLATE, help="LSDJ template .lsdsng providing the instrument bank")
    parser.add_argument("--work-dir", default=None, help="Keep intermediate stems/MIDI here instead of a temp dir")
    args = parser.parse_args()

    work_dir = args.work_dir or tempfile.mkdtemp(prefix="gbmusic_")
    os.makedirs(work_dir, exist_ok=True)
    print(f"Working directory: {work_dir}")

    clip_path = os.path.join(work_dir, "clip.wav")
    duration = None if args.duration <= 0 else args.duration
    print(f"[1/4] Trimming input: start={args.start}s duration={duration or 'full file'}")
    trim_audio(args.input_audio, clip_path, args.start, duration)

    print("[2/4] Separating stems with Demucs (vocals / bass / drums / other)...")
    stems = separate(clip_path, work_dir)

    print("[3/4] Transcribing stems to a combined MIDI score...")
    midi_path = os.path.join(work_dir, "score.mid")
    build_song_midi(stems, midi_path)

    print(f"[4/4] Converting MIDI to an LSDJ song (template: {args.template})...")
    meta = convert_midi_to_lsdsng(
        midi_path,
        args.output_lsdsng,
        template_path=args.template,
        forced_mapping=CHANNEL_MAPPING,
    )
    print(f"\nDone: {args.output_lsdsng}")
    print(meta)

    if not args.work_dir:
        shutil.rmtree(work_dir, ignore_errors=True)
    else:
        print(f"Intermediate files kept in: {work_dir}")


if __name__ == "__main__":
    main()
