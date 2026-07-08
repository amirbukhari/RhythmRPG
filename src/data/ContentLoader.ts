import Ajv, { type ValidateFunction } from "ajv";

import beatmapSchema from "../../docs/technical/schemas/beatmap.schema.json";
import abilitySchema from "../../docs/technical/schemas/ability.schema.json";
import encounterSchema from "../../docs/technical/schemas/encounter.schema.json";

import type { Beatmap } from "./schemas/Beatmap";
import type { Ability } from "./schemas/Ability";
import type { Encounter } from "./schemas/Encounter";
import type { Enemy } from "./schemas/Enemy";
import type { HeroClass } from "./schemas/HeroClass";
import type { CampaignDefinition } from "./schemas/CampaignNode";

// PRD §10.5: no encounter timing may be hardcoded in scene logic — everything
// gameplay-relevant is loaded through here and validated against the
// canonical schemas in docs/technical/schemas/ before a scene ever sees it.
const ajv = new Ajv({ allErrors: true, strict: false });

const validateBeatmap = ajv.compile(beatmapSchema) as ValidateFunction<Beatmap>;
const validateAbility = ajv.compile(abilitySchema) as ValidateFunction<Ability>;
const validateEncounter = ajv.compile(encounterSchema) as ValidateFunction<Encounter>;

export class ContentValidationError extends Error {
  constructor(kind: string, id: string, reason: string) {
    super(`Invalid ${kind} "${id}": ${reason}`);
    this.name = "ContentValidationError";
  }
}

export function loadBeatmap(data: unknown): Beatmap {
  if (!validateBeatmap(data)) {
    throw new ContentValidationError(
      "beatmap",
      (data as { trackId?: string })?.trackId ?? "?",
      ajv.errorsText(validateBeatmap.errors, { separator: "; " })
    );
  }
  return data;
}

export function loadAbility(data: unknown): Ability {
  if (!validateAbility(data)) {
    throw new ContentValidationError(
      "ability",
      (data as { abilityId?: string })?.abilityId ?? "?",
      ajv.errorsText(validateAbility.errors, { separator: "; " })
    );
  }
  return data;
}

export function loadEncounter(data: unknown): Encounter {
  if (!validateEncounter(data)) {
    throw new ContentValidationError(
      "encounter",
      (data as { encounterId?: string })?.encounterId ?? "?",
      ajv.errorsText(validateEncounter.errors, { separator: "; " })
    );
  }
  return data;
}

// Enemy has no formal JSON Schema (see schemas/Enemy.ts) so this is a manual
// shape check rather than an ajv-compiled validator, kept intentionally
// strict so bad enemy data still fails loudly at load time instead of at
// battle time.
export function loadEnemy(data: unknown): Enemy {
  const enemy = data as Partial<Enemy> | null | undefined;
  const id = enemy?.enemyId ?? "?";
  const fail = (message: string): never => {
    throw new ContentValidationError("enemy", id, message);
  };
  if (!enemy || typeof enemy !== "object") return fail("not an object");
  if (typeof enemy.enemyId !== "string" || !enemy.enemyId) return fail("enemyId must be a non-empty string");
  if (typeof enemy.name !== "string" || !enemy.name) return fail("name must be a non-empty string");
  if (typeof enemy.maxHp !== "number" || enemy.maxHp <= 0) return fail("maxHp must be a positive number");
  if (!Array.isArray(enemy.intents) || enemy.intents.length === 0) return fail("intents must be a non-empty array");
  for (const intent of enemy.intents) {
    if (typeof intent.telegraph !== "string" || !intent.telegraph) return fail("each intent needs a telegraph string");
    if (!intent.effect || (intent.effect.type !== "damage" && intent.effect.type !== "debuff")) {
      return fail("each intent needs an effect of type damage|debuff");
    }
    if (typeof intent.effect.value !== "number") return fail("each intent effect needs a numeric value");
  }
  return enemy as Enemy;
}

// HeroClass also has no formal JSON Schema -- same rationale as loadEnemy.
export function loadHeroClass(data: unknown): HeroClass {
  const heroClass = data as Partial<HeroClass> | null | undefined;
  const id = heroClass?.heroId ?? "?";
  const fail = (message: string): never => {
    throw new ContentValidationError("heroClass", id, message);
  };
  if (!heroClass || typeof heroClass !== "object") return fail("not an object");
  if (typeof heroClass.heroId !== "string" || !heroClass.heroId) return fail("heroId must be a non-empty string");
  if (!["warrior", "tank", "mage", "healer"].includes(heroClass.role as string)) return fail("role must be one of warrior|tank|mage|healer");
  if (typeof heroClass.name !== "string" || !heroClass.name) return fail("name must be a non-empty string");
  if (typeof heroClass.maxHp !== "number" || heroClass.maxHp <= 0) return fail("maxHp must be a positive number");
  if (typeof heroClass.maxFocus !== "number" || heroClass.maxFocus <= 0) return fail("maxFocus must be a positive number");
  if (!Array.isArray(heroClass.abilityIds) || heroClass.abilityIds.length === 0) return fail("abilityIds must be a non-empty array");
  return heroClass as HeroClass;
}

// CampaignDefinition also has no formal JSON Schema -- same rationale.
export function loadCampaign(data: unknown): CampaignDefinition {
  const campaign = data as Partial<CampaignDefinition> | null | undefined;
  const fail = (message: string): never => {
    throw new ContentValidationError("campaign", campaign?.startNodeId ?? "?", message);
  };
  if (!campaign || typeof campaign !== "object") return fail("not an object");
  if (typeof campaign.startNodeId !== "string" || !campaign.startNodeId) return fail("startNodeId must be a non-empty string");
  if (!Array.isArray(campaign.nodes) || campaign.nodes.length === 0) return fail("nodes must be a non-empty array");
  const ids = new Set(campaign.nodes.map((n) => n.nodeId));
  if (!ids.has(campaign.startNodeId)) return fail(`startNodeId "${campaign.startNodeId}" is not in nodes`);
  for (const node of campaign.nodes) {
    if (typeof node.nodeId !== "string" || !node.nodeId) return fail("each node needs a non-empty nodeId");
    if (!["battle", "elite", "camp", "boss"].includes(node.type)) return fail(`node "${node.nodeId}" has an invalid type`);
    if (node.type !== "camp" && !node.encounterId) return fail(`node "${node.nodeId}" of type "${node.type}" needs an encounterId`);
    for (const nextId of node.next) {
      if (!ids.has(nextId)) return fail(`node "${node.nodeId}" points to unknown next node "${nextId}"`);
    }
  }
  return campaign as CampaignDefinition;
}
