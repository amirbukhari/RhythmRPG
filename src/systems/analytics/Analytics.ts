// PRD §14: anonymous, local-or-consented telemetry. No PII, no network calls
// in v1 -- events are consent-gated and only logged/kept in memory here;
// wiring to a real sink is a later, non-v1 concern (PRD §10 has no backend).

export type AnalyticsEvent =
  | "audio_gate_completed"
  | "calibration_completed"
  | "battle_started"
  | "ability_used"
  | "judgment_perfect"
  | "judgment_miss"
  | "assist_mode_enabled"
  | "sightread_used"
  | "encounter_failed"
  | "encounter_cleared"
  | "boss_phase_reached"
  | "save_loaded"
  | "echo_found";

export interface AnalyticsRecord {
  event: AnalyticsEvent;
  payload?: Record<string, unknown>;
  timestampMs: number;
}

export class Analytics {
  private consent = false;
  private records: AnalyticsRecord[] = [];

  constructor(private readonly now: () => number = () => Date.now()) {}

  setConsent(consent: boolean): void {
    this.consent = consent;
  }

  hasConsent(): boolean {
    return this.consent;
  }

  track(event: AnalyticsEvent, payload?: Record<string, unknown>): void {
    if (!this.consent) return;
    this.records.push({ event, payload, timestampMs: this.now() });
  }

  getRecords(): readonly AnalyticsRecord[] {
    return this.records;
  }

  clear(): void {
    this.records = [];
  }
}
