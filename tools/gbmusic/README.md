# gbmusic — audio → Game Boy chiptune pipeline

Two paths from a mixed audio file (e.g. an MP3 master) to Game Boy chiptune:

1. **Direct render (`render_gb.py` + `gb_apu.py`)** — separates, transcribes,
   and then synthesizes the result through a numpy model of the DMG's APU,
   emitting a finished, listenable MP3. **This produced the committed 8-bit
   soundtrack in `assets/audio/gb8/`** — sample-aligned with the originals,
   so the measured beat grids in `src/data/content/songs/` judge both
   versions identically, and the in-game `Soundtrack: 8-BIT GAME BOY`
   settings toggle can swap them mid-song.
2. **LSDJ project (`convert.py`, the original path)** — emits a **Little
   Sound Dj** (`.lsdsng`) project for hand-tuning in the tracker and
   rendering on an emulator/real hardware. Higher ceiling, but the LSDJ ROM
   is not redistributable, so nothing in this repo can render it to audio.

## Direct render

```bash
pip install --user -r requirements.txt   # + torch CPU wheels for demucs
python3 render_gb.py ../../assets/audio/<song>.mp3 \
    ../../assets/audio/gb8/<song>.mp3 \
    --work-dir /tmp/gb_work_<song> --report report.json
```

Stages (stems and transcriptions cache in `--work-dir`, so arrangement
tweaks re-render in seconds):

1. Demucs (htdemucs) → vocals / bass / other / drums, driven through its
   Python API (torchaudio's file loader now needs torchcodec, so audio I/O
   goes through soundfile).
2. basic-pitch on the pitched stems; onset detection + spectral-band rules
   (calibrated on these stems) classify each drum hit kick/snare/hat.
3. Arrangement: vocals → pulse 1 (50% duty lead, vibrato on held notes;
   vocal rests are back-filled with the top line of "other" at 25% duty);
   bass → pulse 2 (25% duty, octave-centered into the pulse register's
   64 Hz floor); other → wave (chords collapsed to LSDJ-style arpeggios,
   ≤4 tones at 30 Hz); drums → noise (three LFSR presets, 7-bit "metallic"
   mode for hats).
4. `gb_apu.py` renders the four channels with hardware-accurate duty
   patterns, 11-bit frequency-register pitch quantization, 4-bit 64 Hz
   envelopes, a real 15/7-bit LFSR, and the DMG's DC-blocking output
   high-pass — 4x oversampled, then decimated to 44.1 kHz.
5. QA: prints beat-scale chroma cosine similarity against the original
   (the committed six score 0.83–0.90), then encodes MP3 via lameenc.

## LSDJ project path (original)

`convert.py` is adapted from the author's own [lsdj-midi-studio](https://github.com/amirbukhari/lsdj-midi-studio)
project, which vendors and Python-3-fixes [alexras/pylsdj](https://github.com/alexras/pylsdj)
(MIT). That project converts **MIDI → `.lsdsng`**; this tool adds the missing
front half — **audio → MIDI** — via stem separation + transcription, chosen
specifically because it maps cleanly onto Game Boy hardware.

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

## Auditioning / rendering the result

`.lsdsng` is a project file, not audio — you need LSDJ itself to hear it:

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
