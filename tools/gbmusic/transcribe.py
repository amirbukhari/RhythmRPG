"""Transcribes separated stems into a single multi-channel MIDI score.

Pitched stems (vocals, bass, other) go through basic-pitch (Spotify's
audio-to-MIDI model). The drums stem is not pitched content, so it's handled
with onset detection instead and written as fixed-pitch noise-channel
triggers on MIDI channel 9 (the General MIDI drum-channel convention that
lib/midi_to_lsdsng.py already special-cases).
"""

import mido
import librosa
from basic_pitch.inference import predict

# MIDI channel assignment. 9 is reserved for drums by GM convention.
LEAD_STEMS = {"vocals": 0, "bass": 1, "other": 2}
DRUM_CHANNEL = 9
TICKS_PER_BEAT = 480
DEFAULT_BPM = 120


def _transcribe_pitched(path):
    """Returns [(pitch, start_sec, end_sec), ...] for one stem."""
    _, midi_data, _ = predict(str(path))
    notes = []
    for instrument in midi_data.instruments:
        for note in instrument.notes:
            notes.append((note.pitch, note.start, note.end))
    return notes


def _detect_drum_hits(path, pitch=38, hit_len=0.08):
    """Onset-detects the drum stem and emits a short fixed-pitch note per hit."""
    y, sr = librosa.load(path, sr=None, mono=True)
    onsets = librosa.onset.onset_detect(y=y, sr=sr, units="time", backtrack=True)
    return [(pitch, float(t), float(t) + hit_len) for t in onsets]


def _estimate_tempo(stems):
    for key in ("drums", "bass", "other", "vocals"):
        path = stems.get(key)
        if not path:
            continue
        y, sr = librosa.load(path, sr=None, mono=True)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        if tempo and tempo > 0:
            return float(tempo)
    return DEFAULT_BPM


def build_song_midi(stems, output_path):
    """stems: {"vocals": path, "bass": path, "drums": path, "other": path}."""
    bpm = _estimate_tempo(stems)
    tempo_uspb = mido.bpm2tempo(round(bpm))
    print(f"Estimated tempo: {round(bpm)} BPM")

    events = []  # (channel, pitch, start_sec, end_sec)
    for name, channel in LEAD_STEMS.items():
        path = stems.get(name)
        if not path:
            continue
        notes = _transcribe_pitched(path)
        print(f"  {name}: {len(notes)} notes transcribed -> MIDI channel {channel}")
        events.extend((channel, pitch, start, end) for pitch, start, end in notes)

    if stems.get("drums"):
        hits = _detect_drum_hits(stems["drums"])
        print(f"  drums: {len(hits)} onsets detected -> MIDI channel {DRUM_CHANNEL}")
        events.extend((DRUM_CHANNEL, pitch, start, end) for pitch, start, end in hits)

    # (tick, ordinal, channel, pitch) where ordinal sorts note_off (0) before
    # note_on (1) at the same tick, so overlapping same-pitch notes don't collide.
    midi_events = []
    for channel, pitch, start, end in events:
        start_tick = int(round(mido.second2tick(start, TICKS_PER_BEAT, tempo_uspb)))
        end_tick = max(start_tick + 1, int(round(mido.second2tick(end, TICKS_PER_BEAT, tempo_uspb))))
        midi_events.append((start_tick, 1, channel, pitch))
        midi_events.append((end_tick, 0, channel, pitch))
    midi_events.sort(key=lambda e: (e[0], e[1]))

    track = mido.MidiTrack()
    track.append(mido.MetaMessage("set_tempo", tempo=tempo_uspb, time=0))

    last_tick = 0
    for tick, ordinal, channel, pitch in midi_events:
        delta = max(0, tick - last_tick)
        last_tick = tick
        if ordinal == 1:
            track.append(mido.Message("note_on", note=pitch, velocity=90, channel=channel, time=delta))
        else:
            track.append(mido.Message("note_off", note=pitch, velocity=0, channel=channel, time=delta))

    midi_file = mido.MidiFile(ticks_per_beat=TICKS_PER_BEAT)
    midi_file.tracks.append(track)
    midi_file.save(output_path)
    return bpm
