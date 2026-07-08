export type JudgmentTier = "perfect" | "great" | "good" | "miss";

/** Base judgment windows in milliseconds, before accessibility modifiers. See PRD §8.3. */
export const JUDGMENT_WINDOWS_MS: Record<Exclude<JudgmentTier, "miss">, number> = {
  perfect: 45,
  great: 90,
  good: 140,
};

export const STORY_MODE_WINDOW_MULTIPLIER = 1.25;

/**
 * Classifies an input against its target time. All inputs must be timestamped
 * against TransportClock.currentTime, never Date.now() or requestAnimationFrame.
 */
export function judge(
  deltaMs: number,
  options: { storyMode?: boolean; assistMultiplier?: number } = {}
): JudgmentTier {
  const multiplier = (options.storyMode ? STORY_MODE_WINDOW_MULTIPLIER : 1) * (options.assistMultiplier ?? 1);
  const abs = Math.abs(deltaMs);

  if (abs <= JUDGMENT_WINDOWS_MS.perfect * multiplier) return "perfect";
  if (abs <= JUDGMENT_WINDOWS_MS.great * multiplier) return "great";
  if (abs <= JUDGMENT_WINDOWS_MS.good * multiplier) return "good";
  return "miss";
}
