# gbmusic — audio → Game Boy (LSDJ) chiptune pipeline

Converts a mixed audio file (e.g. an MP3 master) into a **Little Sound Dj**
(`.lsdsng`) project, so it can be auditioned, hand-tuned, and rendered as an
authentic Game Boy chiptune — matching the 8-bit pixel-art direction in
[`docs/product/PRD.md`](../../docs/product/PRD.md).

Adapted from the author's own [lsdj-midi-studio](https://github.com/amirbukhari/lsdj-midi-studio)
project, which vendors and Python-3-fixes [alexras/pylsdj](https://github.com/alexras/pylsdj)
(MIT). That project converts **MIDI → `.lsdsng`**; this tool adds the missing
front half — **audio → MIDI** — via stem separation + transcription, chosen
specifically because it maps cleanly onto Game Boy hardware. pylsdj's own
dependency [alexras/bread](https://github.com/alexras/bread) (MIT) is also
vendored under `lib/bread` — pure Python, but its sdist can't build on
current Ubuntu setuptools (see `lib/bread/VENDORED.md`).

## Why stem separation first

The Game Boy APU has exactly four channels: two pulse, one wave, one noise.
That happens to line up with a typical song's stems:

| Stem | Game Boy channel | Role |
|---|---|---|
| vocals | pulse 1 | lead |
| bass | pulse 2 | bass |
| other (harmony/instruments) | wave | chords/pads |
| drums | noise | rhythm |

So rather than transcribing the whole mix (which produces a muddy result
when vocals, drums, and instruments are all superimposed), the pipeline
splits the mix with [Demucs](https://github.com/facebookresearch/demucs)
first, transcribes each stem independently, and assigns each straight to its
matching channel.

## Pipeline

```
input.mp3
  │  ffmpeg (trim to a clip — LSDJ's phrase/chain slots cap song length)
  ▼
clip.wav
  │  Demucs (htdemucs model)
  ▼
vocals.wav  bass.wav  other.wav  drums.wav
  │             │          │         │
  │  basic-pitch (audio→MIDI)        │  librosa onset detection
  ▼             ▼          ▼         ▼
        score.mid (one file, one MIDI channel per stem)
  │  lib/midi_to_lsdsng.py (vendored pylsdj)
  ▼
output.lsdsng
```

## Setup

Dependencies were installed with `pip install --user` (see
`requirements.txt`); `pylsdj` is vendored under `lib/pylsdj` (not on PyPI in
a working Python 3 state — see `lib/pylsdj/LICENSE` for provenance) so no
extra install step is needed for it. `ffmpeg` must be on `PATH`.

```bash
pip install --user -r requirements.txt
```

## Usage

```bash
python3 convert.py <input_audio> <output.lsdsng> [--start 0] [--duration 60]
```

- `--duration` (default 60s) trims the input before processing. LSDJ has a
  fixed number of phrase/chain/instrument slots, so a full-length track
  can't fit in one song anyway — pick the section you actually want
  chiptune-ified. Pass `--duration 0` to run the whole file; the converter
  will print `Warning: Out of phrase/chain slots! Truncating song.` and cut
  off gracefully if it runs out of room.
- `--template` points at an `.lsdsng` used only for its instrument bank
  (pulse/wave/noise patch settings); defaults to `templates/drumbeat.lsdsng`.
- `--work-dir` keeps the intermediate stems and `score.mid` around for
  inspection instead of using a temp directory.

Example (already run, output committed as a demo):

```bash
python3 convert.py \
  ../../assets/reference/audio-demo/AmirsMaster-ForDylanWithBabyVocals.mp3 \
  output/amirs_master_clip_30-60s.lsdsng \
  --start 30 --duration 30
```

## Sourcing all battle tracks from one master

Per PRD §11.2, every v1 battle track is a distinct slice of this same
~22-minute demo master — not separately composed material. Run the pipeline
once per stage/boss-phase, picking a different `--start`, and give each
output a name that identifies the stage it's for, e.g.:

```bash
python3 convert.py <master.mp3> output/opening_biome.lsdsng     --start   0 --duration 60
python3 convert.py <master.mp3> output/mid_biome_1.lsdsng       --start  90 --duration 60
python3 convert.py <master.mp3> output/mid_biome_2_clave.lsdsng --start 240 --duration 45
python3 convert.py <master.mp3> output/boss_phase_1.lsdsng      --start 480 --duration 40
python3 convert.py <master.mp3> output/boss_phase_2.lsdsng      --start 520 --duration 40
python3 convert.py <master.mp3> output/boss_phase_3.lsdsng      --start 560 --duration 40
```

Which timestamp ranges actually fit each stage's intended feel is a
music-direction call, not something this tool decides — record the chosen
mapping in `docs/design/music-direction.md` once picked. Each `.lsdsng`
still needs its own hand-tuning pass in LSDJ; the final boss's meter changes
(PRD §8.7) are authored separately in the beatmap JSON regardless of which
slice underlies them — see PRD §10.5.

## Rendering to audio without LSDJ: `render_lsdsng.py`

`.lsdsng` is a project file, not audio. For a long time that meant rendering
required LSDJ itself (emulator or hardware — see the next section), which
this repo can't automate: the LSDJ ROM isn't redistributable, and PyBoy's
public API exposes no audio-buffer export (investigated and documented in
PRD §20.2 history). `render_lsdsng.py` closes that gap by synthesizing the
four Game Boy APU channels directly:

```bash
python3 render_lsdsng.py output/opening_biome.lsdsng out.wav [--bpm N] [--loop-beats N]
python3 render_all_tracks.py   # renders all 7 stage/boss tracks into assets/audio/battle/ as OGG
```

- pu1 → 50% duty pulse, pu2 → 25% duty pulse, wav → 4-bit-quantized
  triangle, noi → 15-bit LFSR noise, with GB-style stepped (15-level)
  volume envelopes.
- `--bpm` renders at an overridden tempo; `render_all_tracks.py` uses each
  beatmap's authored BPM so audio and judgment grid stay bar-aligned.
- `--loop-beats` cuts the render to a whole multiple of the beatmap's
  pattern loop length (quarter-note beats), making the file seamlessly
  loopable against gameplay.
- Faithful to what *this pipeline writes*, not a general LSDJ player: FX
  columns, tables, grooves, and vibrato are ignored because
  `lib/midi_to_lsdsng.py` never writes them. A hand-tuned `.lsdsng` that
  uses those features still needs the LSDJ path below to be heard fully.

The in-game battle tracks (`assets/audio/battle/*.ogg`, loaded via
`src/systems/audio/BattleTracks.ts`) are produced by `render_all_tracks.py`.
Re-run it after regenerating or hand-tuning any draft.

Renderer dependencies: `numpy` (synthesis), plus the vendored `lib/bread`
and `lib/pylsdj` with `bitstring` (parsing) — see `requirements.txt`.
`render_all_tracks.py` additionally needs `ffmpeg` on `PATH` for OGG
encoding. The heavyweight transcription deps (Demucs, basic-pitch) are NOT
needed just to render.

## Auditioning / rendering via LSDJ itself

For final-quality renders of hand-tuned projects (real envelope/FX
behavior), LSDJ remains the reference player:

1. **Emulator (fastest):** load `output/*.lsdsng` into any Game Boy emulator
   that supports LSDJ `.sav` injection (e.g. via `pylsdj.SAVFile`, as the
   sibling `lsdj-midi-studio` web app's `server.py` does), or open it
   directly in a desktop LSDJ-compatible tracker/emulator.
2. **Real hardware:** copy the `.lsdsng` onto an LSDJ save via a flashcart.
3. Once it sounds right, **export real Game Boy audio** by recording the
   emulator's output (or your hardware's line-out) to WAV — that recording
   is what should land in `assets/audio/` as the actual battle-track stem,
   per the PRD's audio content spec.

**The LSDJ ROM (`lsdj*.gb`) is never committed to this repo.** Its license
(freeware for personal/educational use only, no redistribution) forbids it —
see `.gitignore`. You need your own licensed copy to run an emulator.

## Known limitations

- **Automatic transcription is lossy.** basic-pitch does polyphonic pitch
  detection reasonably well on a clean vocal/bass/instrument stem, but it
  will still misfire on vibrato, pitch bends, breathy vocals, and dense
  harmony. Treat the `.lsdsng` output as a first-pass draft to hand-edit in
  LSDJ, not a finished track.
- **Drums are onset-triggered, not transcribed.** Every detected hit fires
  the same noise-channel note (`hit_len=0.08s`, pitch fixed) — it captures
  rhythm, not kit variety (kick vs. snare vs. hat). Vary this by hand in
  LSDJ afterward, or extend `transcribe.py`'s `_detect_drum_hits` with
  spectral-band splitting if that matters for a given track.
- **Tempo is a single global estimate** (`librosa.beat.beat_track` on the
  drum stem, falling back to bass/other/vocals). Tracks with tempo changes
  or rubato will drift.
- One MIDI channel maps to exactly one Game Boy channel — a stem with real
  polyphony (e.g. a chord-heavy "other" stem) gets flattened to whichever
  notes basic-pitch reports as active at each 16th-note step; LSDJ's wave
  channel is monophonic, so true chords are not reproducible without manual
  arpeggiation in the tracker.
