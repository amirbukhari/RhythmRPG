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
  volumeMusic: 1,
  volumeSfx: 1,
  volumeUi: 1,
  keyBindings: {},
};
