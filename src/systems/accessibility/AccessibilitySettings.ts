/** Mandatory day-one accessibility settings. See PRD §9.3. Persisted via SaveManager. */
export interface AccessibilitySettings {
  gameSpeed: 0.7 | 0.85 | 1.0;
  assistedTimingWindows: boolean;
  reducedMotion: boolean;
  photosensitivitySafeMode: boolean;
  captionsEnabled: boolean;
  practiceMode: boolean;
  /** Opt-in audible metronome tick over the music in fights (PRD §9.3).
   * Off by default: the judged beat IS the playing song's beat (§8.3). */
  beatTickEnabled: boolean;
  /** Sightread (§8.4): the "see the music" forecast lane -- upcoming beats
   * and telegraphed enemy strikes previewed on the fight HUD. */
  sightreadEnabled: boolean;
  /** Play the 8-bit Game Boy renders of the soundtrack (assets/audio/gb8,
   * from tools/gbmusic/render_gb.py) instead of the recorded tracks. The
   * renders are sample-aligned with the originals, so the measured beat
   * grids (§8.3) -- and therefore judgment -- are identical either way. */
  chiptuneAudio: boolean;
  volumeMusic: number;
  volumeSfx: number;
  volumeUi: number;
  keyBindings: Record<string, string>;
}

export const DEFAULT_ACCESSIBILITY_SETTINGS: AccessibilitySettings = {
  gameSpeed: 1.0,
  assistedTimingWindows: false,
  reducedMotion: false,
  photosensitivitySafeMode: false,
  captionsEnabled: true,
  practiceMode: false,
  beatTickEnabled: false,
  sightreadEnabled: false,
  chiptuneAudio: false,
  volumeMusic: 1,
  volumeSfx: 1,
  volumeUi: 1,
  keyBindings: {},
};
