/// <reference types="vite/client" />

import { loadAbility, loadBeatmap, loadEncounter, loadEnemy, loadHeroClass, loadCampaign, loadBossPhaseConfig, loadSongMap } from "./ContentLoader";
import type { SongMap } from "./schemas/SongMap";
import type { Ability } from "./schemas/Ability";
import type { Beatmap } from "./schemas/Beatmap";
import type { Encounter } from "./schemas/Encounter";
import type { Enemy } from "./schemas/Enemy";
import type { HeroClass } from "./schemas/HeroClass";
import type { CampaignDefinition } from "./schemas/CampaignNode";
import type { BossPhaseConfig } from "./schemas/BossPhaseConfig";
import campaignData from "./content/campaign/opening_biome.json";

const abilityModules = import.meta.glob("./content/abilities/*.json", { eager: true }) as Record<string, { default: unknown }>;
const beatmapModules = import.meta.glob("./content/beatmaps/*.json", { eager: true }) as Record<string, { default: unknown }>;
const encounterModules = import.meta.glob("./content/encounters/*.json", { eager: true }) as Record<string, { default: unknown }>;
const enemyModules = import.meta.glob("./content/enemies/*.json", { eager: true }) as Record<string, { default: unknown }>;
const heroClassModules = import.meta.glob("./content/heroes/*.json", { eager: true }) as Record<string, { default: unknown }>;
const bossPhaseModules = import.meta.glob("./content/bossPhases/*.json", { eager: true }) as Record<string, { default: unknown }>;
const songModules = import.meta.glob("./content/songs/*.json", { eager: true }) as Record<string, { default: unknown }>;

function indexBy<T>(
  modules: Record<string, { default: unknown }>,
  loader: (raw: unknown) => T,
  keyOf: (item: T) => string
): Map<string, T> {
  const map = new Map<string, T>();
  for (const mod of Object.values(modules)) {
    const item = loader(mod.default);
    map.set(keyOf(item), item);
  }
  return map;
}

export const abilities = indexBy(abilityModules, loadAbility, (a) => a.abilityId);
export const beatmaps = indexBy(beatmapModules, loadBeatmap, (b) => b.trackId);
export const encounters = indexBy(encounterModules, loadEncounter, (e) => e.encounterId);
export const enemies = indexBy(enemyModules, loadEnemy, (e) => e.enemyId);
export const heroClasses = indexBy(heroClassModules, loadHeroClass, (h) => h.heroId);
export const campaign: CampaignDefinition = loadCampaign(campaignData);
export const bossPhaseConfigs = indexBy(bossPhaseModules, loadBossPhaseConfig, (c) => c.encounterId);
export const songMaps = indexBy(songModules, loadSongMap, (s) => s.songId);

function getOrThrow<T>(map: Map<string, T>, kind: string, id: string): T {
  const item = map.get(id);
  if (!item) throw new Error(`Unknown ${kind}: "${id}"`);
  return item;
}

export const getAbility = (id: string): Ability => getOrThrow(abilities, "ability", id);
export const getBeatmap = (id: string): Beatmap => getOrThrow(beatmaps, "beatmap", id);
export const getEncounter = (id: string): Encounter => getOrThrow(encounters, "encounter", id);
export const getEnemy = (id: string): Enemy => getOrThrow(enemies, "enemy", id);
export const getHeroClass = (id: string): HeroClass => getOrThrow(heroClasses, "heroClass", id);
export const getSongMap = (id: string): SongMap => getOrThrow(songMaps, "songMap", id);

/** The fixed four-role party per PRD §8.4, in warrior/tank/mage/healer order. */
export function partyRoster(): HeroClass[] {
  return [getHeroClass("warrior"), getHeroClass("tank"), getHeroClass("mage"), getHeroClass("healer")];
}

export function getCampaignNode(nodeId: string) {
  const node = campaign.nodes.find((n) => n.nodeId === nodeId);
  if (!node) throw new Error(`Unknown campaign node: "${nodeId}"`);
  return node;
}

export function abilitiesForRole(role: Ability["role"]): Ability[] {
  return [...abilities.values()].filter((a) => a.role === role);
}

export function getBossPhaseConfig(encounterId: string): BossPhaseConfig | undefined {
  return bossPhaseConfigs.get(encounterId);
}
