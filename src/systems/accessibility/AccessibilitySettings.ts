/** Mandatory day-one accessibility settings. See PRD §9.3. Persisted via SaveManager. */
export interface AccessibilitySettings {
  gameSpeed: 0.7 | 0.85 | 1.0;
  assistedTimingWindows: boolean;
  reducedMotion: boolean;
  photosensitivitySafeMode: boolean;
  captionsEnabled: boolean;
  practiceMode: boolean;
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
  volumeMusic: 1,
  volumeSfx: 1,
  volumeUi: 1,
  keyBindings: {},
};
