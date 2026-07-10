# Music direction

Per PRD §11.2/§11.4, every v1 battle track is a distinct slice of the single
demo master (`assets/reference/audio-demo/AmirsMaster-ForDylanWithBabyVocals.mp3`,
~22 minutes) run through [`tools/gbmusic/`](../../tools/gbmusic/README.md),
not separately composed material.

## How the slices were chosen

Timestamp ranges were picked algorithmically by
[`tools/gbmusic/select_slices.py`](../../tools/gbmusic/select_slices.py),
not by ear, so the decision is reproducible and documented rather than
implicit. Method:

1. Compute onset-strength, RMS energy, and spectral centroid across the full
   master, normalize each to [0, 1].
2. Score every candidate window (5s hop) as `0.5*onset + 0.3*rms + 0.2*centroid`
   — rhythmic density weighted highest since that's what the game's judgment
   system actually tracks.
3. Assign the 7 stage/phase tracks in ascending complexity-target order
   (opening biome = calmest usable section, boss phase 3 = busiest), each
   taking the closest-scoring non-overlapping window to its target
   percentile, blocking that range out before picking the next.

This gives a monotonic complexity curve that tracks the encounter difficulty
curve in PRD §8.6/§8.7 — a defensible starting point, not a finished
listening pass. **Re-run `select_slices.py` and regenerate if anyone actually
listens to the master and disagrees with a placement** — nothing here is
final until a human confirms it sounds right for its stage.

## Chosen slices

| Stage | Master timestamp | Duration | Complexity score | Output |
|---|---|---:|---:|---|
| Opening biome | 04:40 | 75s | 0.187 | `tools/gbmusic/output/opening_biome.lsdsng` |
| Mid biome 1 (3/4, 6/8) | 16:25 | 60s | 0.199 | `tools/gbmusic/output/mid_biome_1.lsdsng` |
| Mid biome 2 (clave accents) | 11:55 | 55s | 0.211 | `tools/gbmusic/output/mid_biome_2_clave.lsdsng` |
| Mid biome 3 (syncopated elites) | 08:05 | 55s | 0.215 | `tools/gbmusic/output/mid_biome_3_syncopated.lsdsng` |
| Final boss — phase 1 | 20:00 | 45s | 0.220 | `tools/gbmusic/output/boss_phase_1.lsdsng` |
| Final boss — phase 2 | 03:00 | 45s | 0.227 | `tools/gbmusic/output/boss_phase_2.lsdsng` |
| Final boss — phase 3 | 14:25 | 50s | 0.237 | `tools/gbmusic/output/boss_phase_3.lsdsng` |

Full precision values (seconds, not mm:ss) are in
[`tools/gbmusic/stage_slices.json`](../../tools/gbmusic/stage_slices.json).

Each `.lsdsng` above is a machine-transcribed draft — see
`tools/gbmusic/README.md`'s limitations section. None of them are shippable
stems yet; each needs a hand-tuning pass in LSDJ before it satisfies the
delivery spec in PRD §11.2 (full mix preview, stems, tempo/meter maps,
authoring click reference, SFX pack).

## Rendered in-game tracks

All 7 drafts are now rendered to playable Game Boy-style audio
(`assets/audio/battle/*.ogg`) by `tools/gbmusic/render_all_tracks.py` (an
APU synthesizer over the parsed `.lsdsng` note data — no LSDJ ROM or
emulator needed; see the rendering section of `tools/gbmusic/README.md`).
Each file is rendered at its beatmap's authored BPM and cut to an exact
whole multiple of the beatmap's pattern loop, so it loops bar-aligned with
the judgment grid in-game (`src/systems/audio/BattleTracks.ts` /
`ChiptuneMusicPlayer.ts`). The transcribed tempi and the authored beatmap
BPMs match 1:1 (105/117/129/110/105/178/105), so no time-stretching is
involved. These renders inherit the drafts' machine-transcription caveats —
they make the tracks *hearable and shippable as placeholders*, not
hand-tuned final stems; re-run `render_all_tracks.py` after any hand-tuning
pass to refresh the game's audio.

## Final boss meter changes

The boss-phase slices above supply the *audio content* only. The actual
meter changes specified in PRD §8.7 (phase 2 alternating 4/4/3/4, phase 3
cycling 5/4/7/8/4/4/3/4) are authored separately as hard-coded
`meterSequence` data in that boss's beatmap JSON (`beatmap.schema.json`),
per PRD §10.5 — they are not, and cannot be, inferred from the source audio.
Whoever authors `boss_conductor_p2`/`p3` beatmaps needs the tempo reported
by each slice's conversion (phase 2: 178 BPM, phase 3: 105 BPM — see
`tools/gbmusic/output/*.lsdsng` metadata) to keep the bar math correct.

## Open follow-up

- These slices haven't been auditioned by a human yet. Listening + possible
  reassignment is the next step before treating any of them as locked.
- The art bible and narrative bible referenced in this directory's README
  are still unwritten.
