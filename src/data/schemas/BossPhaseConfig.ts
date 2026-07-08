// Not a PRD §10.5 canonical schema -- same rationale as Enemy/HeroClass/
// CampaignNode. The encounter schema is intentionally one encounter -> one
// trackId; a multi-phase boss (PRD §8.7) needs an ordered list of
// beatmaps keyed to enemy HP thresholds, which nothing else describes.

export interface BossPhase {
  /** Beatmap (and therefore tempo/meterSequence) active during this phase. */
  trackId: string;
  /** Phase becomes active once the boss's HP fraction drops to/below this. Phase 0 is implicitly 1.0. */
  hpThreshold: number;
}

export interface BossPhaseConfig {
  encounterId: string;
  phases: BossPhase[];
}
