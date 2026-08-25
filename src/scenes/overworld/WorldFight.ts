import Phaser from "phaser";
import { GameContext } from "../../state/GameContext";
import { getEncounter, getBeatmap, getEnemy, getCampaignNode, songMaps, bossPhaseConfigs } from "../../data/ContentRegistry";
import { TransportClock } from "../../systems/audio/TransportClock";
import { BeatTick } from "../../systems/audio/BeatTick";
import { SfxPlayer } from "../../systems/audio/SfxPlayer";
import { GameFeel } from "./GameFeel";
import { applyRelics } from "../../systems/progression/Relics";
import { music } from "../../systems/audio/SongPlayer";
import { tierAt, tierForOffset, beatIndexAt, nextBeat, nearestBeatDistanceSeconds, TIER_WINDOWS } from "../../systems/audio/SongBeat";
import type { SongMap } from "../../data/schemas/SongMap";
import { BASE_WIDTH, BASE_HEIGHT } from "../../config/GameConfig";
import {
  createArena,
  step,
  player as getPlayer,
  enemies as getEnemies,
  ULTIMATE_GROOVE_COST,
  HEAVY,
  SPECIAL,
  ULTIMATE,
  type Arena,
  type BeatTier,
  type FrameInput,
} from "../../systems/action/ActionCombat";
import { sceneGoto } from "../Transition";

/** Remappable combat actions (PRD §9.3) with their default key names. */
type CombatAction = "light" | "heavy" | "special" | "parry" | "dash" | "ultimate";
const DEFAULT_ACTION_KEYS: Record<CombatAction, string> = { light: "J", heavy: "K", special: "L", parry: "I", dash: "SHIFT", ultimate: "U" };

/** Resolve a stored KeyboardEvent.key binding ("z", "Shift", " ") to a
 * Phaser key name, falling back to the default when unset/unmappable. */
function keyNameFor(binding: string | undefined, fallback: string): string {
  if (!binding) return fallback;
  const name = binding === " " ? "SPACE" : binding.toUpperCase();
  return name in Phaser.Input.Keyboard.KeyCodes ? name : fallback;
}

const FACING_LUNGE: Record<string, { x: number; y: number }> = {
  up: { x: 0, y: -1 },
  down: { x: 0, y: 1 },
  left: { x: -1, y: 0 },
  right: { x: 1, y: 0 },
};

const TIER_LABEL: Record<Exclude<BeatTier, "off">, { text: string; color: string }> = {
  perfect: { text: "PERFECT", color: "#f4d27a" },
  great: { text: "GREAT", color: "#49c6bd" },
  good: { text: "GOOD", color: "#9fb0c0" },
};

/**
 * In-world combat (PRD §8.2 v7.6, owner: "the boss arenas shouldn't be
 * different places... it should be part of the overall world"). A fight no
 * longer loads a separate arena scene: when the player walks into a foe, the
 * camera locks to a screen-sized room of the ACTUAL overworld around it and
 * the action sim runs right there -- same ground, same props, same world.
 * ActionCombat is Phaser-free, so the sim's arena is simply mapped onto a
 * world-space rectangle. On any outcome the same rewards/Results flow as
 * before runs (restarting the scene cleans everything up).
 */

// Authored foe sheets are 4x their world size (tools/art/contract.py SCALE),
// so every foe renders at 0.25. Lunal (world-bible §8) is authored at 200px
// like the band and renders at Mir's own 0.125 -- human-scaled on purpose,
// his height class, not a colossus.
const FIGHT_SCALE: Record<string, number> = { lunal: 0.125, elite_wraith: 0.25, drifter: 0.25, slime: 0.25 };
/** Mir's authored states (tools/art/mir.py) and the frame rate each reads
 * best at. `attack`/`heavy` are driven frame-by-frame off the sim's attack
 * phase instead of played, so anticipation-impact-recovery lands exactly on
 * the frames the sim is actually in. */
const MIR_CLIP: Record<string, { key: string; fps: number; loop: boolean }> = {
  idle: { key: "band_mir", fps: 5, loop: true },
  run: { key: "band_mir_run", fps: 12, loop: true },
  dash: { key: "band_mir_dash", fps: 14, loop: false },
  parry: { key: "band_mir_parry", fps: 16, loop: false },
  hurt: { key: "band_mir_hurt", fps: 12, loop: false },
  down: { key: "band_mir_down", fps: 6, loop: false },
};

/** Foe states (tools/art/foes.py). `telegraph` is the load-bearing one: the
 * silhouette class flips for the whole windup, so an incoming attack is
 * readable in peripheral vision, on the beat, without reading a HUD. */
const FOE_CLIP: Record<string, { fps: number; loop: boolean }> = {
  idle: { fps: 3, loop: true },
  move: { fps: 9, loop: true },
  telegraph: { fps: 10, loop: false },
  attack: { fps: 16, loop: false },
  hurt: { fps: 14, loop: false },
  dead: { fps: 7, loop: false },
};

const FIGHT_ACCENT: Record<string, number> = {
  lunal: 0x9fb8c0,
  elite_wraith: 0x49c6bd,
  drifter: 0x9fe8e0,
  slime: 0x9aca43,
};

export interface WorldFightHost {
  scene: Phaser.Scene;
  playerSprite: Phaser.GameObjects.Sprite;
  /** Tile walkability in WORLD pixels -- impassable tiles become sim obstacles. */
  isWorldWalkable(px: number, py: number): boolean;
  /** Hide the exploration HUD for the duration of a fight. The hint strip
   * still read "WASD: move  E: interact" mid-combat, which is worse than no
   * HUD: it tells the player the wrong verbs at the exact moment the verbs
   * changed. Optional so tests can host a fight without one. */
  setExploreHudVisible?(visible: boolean): void;
}

export class WorldFight {
  private scene: Phaser.Scene;
  private host: WorldFightHost;
  private playerSprite: Phaser.GameObjects.Sprite;
  private rect: Phaser.Geom.Rectangle;
  private clock = new TransportClock();
  private tick: BeatTick | null = null;
  private sfx: SfxPlayer | null = null;
  /** M3 game feel -- the 80ms after a blow lands. See GameFeel.ts for why the
   * stop is render-only. */
  private feel!: GameFeel;
  /** The leader's own scale, owned by OverworldScene: captured once so the
   * impact squash composes with it instead of overwriting it. */
  private playerBaseScale = 1;
  private prevPlayerHp = -1;
  private prevLogLen = 0;
  private wasDashing = false;
  private arena: Arena | null = null; // null until the async clock is up
  private beatSeconds = 0.5; // file-time seconds per beat (HUD/fallback pacing)
  private songMap: SongMap | null = null;
  private gameSpeed = 1;
  private lastBeatIdx = -1;
  private tierPopup: Phaser.GameObjects.Text | null = null;
  private caption: Phaser.GameObjects.Text | null = null;
  private captionUntil = 0;
  private prevGroove = 0;
  private grooveWasFull = false;
  private wasWindup = new Set<string>();
  private deadHandled = new Set<string>();
  // Boss phases (§8.7): HP thresholds -> escalation + song-section jumps.
  private phaseThresholds: { hpThreshold: number; section?: string }[] = [];
  private phaseIdx = 0;
  private sightread: Phaser.GameObjects.Graphics | null = null;
  private encounterId: string;
  private nodeId: string | null;
  private isBoss = false;
  private finished = false;

  private cursors: Phaser.Types.Input.Keyboard.CursorKeys;
  private moveKeys: Record<"W" | "A" | "S" | "D", Phaser.Input.Keyboard.Key>;
  private spaceKey: Phaser.Input.Keyboard.Key;
  private actionKeys: Record<CombatAction, Phaser.Input.Keyboard.Key>;

  private sprites = new Map<string, Phaser.GameObjects.Sprite>();
  private shadows = new Map<string, Phaser.GameObjects.Ellipse>();
  private auras = new Map<string, Phaser.GameObjects.Image>();
  private accents = new Map<string, number>();
  private enemyIds = new Map<string, string>();
  private lastEnemyHp = new Map<string, number>();
  /** Last animation state driven per sprite, so a clip is only restarted when
   * the state actually changes (otherwise a one-shot never plays past frame 0). */
  private foeState = new Map<string, string>();
  private namePlates = new Map<string, Phaser.GameObjects.Text>();
  private playerState = "";
  private fx: Phaser.GameObjects.Graphics;
  private bars: Phaser.GameObjects.Graphics;
  private plate: Phaser.GameObjects.Graphics;
  private beatPulse: Phaser.GameObjects.Arc;
  private attackGlow: Phaser.GameObjects.Image;
  private hud: Phaser.GameObjects.GameObject[] = [];
  /** Persistent ground-scuff decals stamped at every hit -- the fight scars
   * the ground it happens on (the HLD boss-room "battle happened here"
   * read), rather than resetting to pristine after every impact spark. */
  private groundDecals: Phaser.GameObjects.RenderTexture | null = null;
  private decalStamp: Phaser.GameObjects.Image | null = null;
  /** M3: the room's edge bleeds when Mir is struck. Kept separate from the
   * arena frame so it can flash without disturbing the letterbox. */
  private hurtFrame: Phaser.GameObjects.Graphics | null = null;
  /** The arena frame: the visual statement that the world just became a room. */
  private frameBars: Phaser.GameObjects.Rectangle[] = [];
  private frameVignette: Phaser.GameObjects.Graphics | null = null;

  constructor(host: WorldFightHost, nodeId: string, encounterId: string, nodeWorldX: number, nodeWorldY: number) {
    this.scene = host.scene;
    this.host = host;
    this.playerSprite = host.playerSprite;
    this.encounterId = encounterId;
    this.nodeId = nodeId;
    const encounter = getEncounter(encounterId);
    this.isBoss = encounter.encounterId.startsWith("boss_");

    // a screen-sized room of the real world around the foe, clamped to the map
    const cam = this.scene.cameras.main;
    const bounds = cam.getBounds();
    const rx = Phaser.Math.Clamp(nodeWorldX - BASE_WIDTH / 2, bounds.x, bounds.right - BASE_WIDTH);
    const ry = Phaser.Math.Clamp(nodeWorldY - BASE_HEIGHT / 2, bounds.y, bounds.bottom - BASE_HEIGHT);
    this.rect = new Phaser.Geom.Rectangle(rx, ry, BASE_WIDTH, BASE_HEIGHT);
    cam.stopFollow();
    cam.pan(this.rect.centerX, this.rect.centerY, 320, "Sine.easeInOut");

    const kb = this.scene.input.keyboard!;
    this.cursors = kb.createCursorKeys();
    this.moveKeys = kb.addKeys("W,A,S,D") as WorldFight["moveKeys"];
    this.spaceKey = kb.addKey("SPACE");
    // Combat bindings are remappable (PRD §9.3); defaults J/K/L/I/SHIFT/U.
    const bindings = GameContext.activeProfile?.settings.keyBindings ?? {};
    this.actionKeys = Object.fromEntries(
      (Object.keys(DEFAULT_ACTION_KEYS) as CombatAction[]).map((action) => [
        action,
        kb.addKey(keyNameFor(bindings[action], DEFAULT_ACTION_KEYS[action])),
      ])
    ) as WorldFight["actionKeys"];

    this.fx = this.scene.add.graphics().setDepth(8);
    this.bars = this.scene.add.graphics().setDepth(8.5);
    this.attackGlow = this.scene.add.image(0, 0, "glow").setBlendMode(Phaser.BlendModes.ADD).setTint(0xf4d27a).setDepth(7).setAlpha(0);
    // ground scars: depth 3 sits above the painted plate/venue dressing (<=2.6)
    // and below every fighter's shadow/sprite (>=3.5), so scuffs read as part
    // of the ground, not a decal floating over the fight.
    this.groundDecals = this.scene.add.renderTexture(this.rect.x, this.rect.y, BASE_WIDTH, BASE_HEIGHT).setOrigin(0, 0).setDepth(3);
    this.decalStamp = this.scene.add.image(0, 0, "glow").setVisible(false);

    // HUD: the camera is locked to this.rect for the whole fight, so
    // screen-space UI is simply placed at rect + design offset (the retina
    // zoom made scrollFactor-0 drift under scrolled cameras -- see
    // OverworldScene.pinToScreen for the moving-camera variant).
    const ox = this.rect.x;
    const oy = this.rect.y;
    const plateBg = this.scene.add
      .nineslice(ox + 3, oy + BASE_HEIGHT - 33, "ui_panel", undefined, 96, 30, 5, 5, 5, 5)
      .setOrigin(0, 0)
      .setDepth(20)
      .setAlpha(0.94);
    const plateName = this.scene.add
      .text(ox + 9, oy + BASE_HEIGHT - 30, "MIR", { fontFamily: "monospace", fontSize: "6px", color: "#9fe8e0" })
      .setDepth(21);
    this.beatPulse = this.scene.add.circle(ox + 90, oy + BASE_HEIGHT - 26, 3, 0x49c6bd).setDepth(21);
    // graphics draw in design coords; positioning the object at the room's
    // corner maps them into the visible rect
    this.plate = this.scene.add.graphics().setDepth(21).setPosition(ox, oy);
    this.hud.push(plateBg, plateName, this.beatPulse, this.plate);

    // ---- the arena frame -------------------------------------------------
    // The camera locking to a room of the real world is the moment the game
    // changes mode, and nothing used to SAY so -- a fight started and the
    // screen looked exactly like walking. Two devices, both cheap and both
    // reversible: the edges of the room darken hard (so the eye is pushed to
    // the two figures in the middle), and the frame closes to a shallow
    // letterbox. Together they read as a stage, and the moment they retract
    // is the moment the world opens back up.
    // Taking damage has to be felt at the EDGE of vision, not only on the
    // 22-pixel figure the player is already staring at: in a fight this dense
    // the sprite's white flash is inside the same foveal patch as everything
    // else. A red inset frame is peripheral by construction. Photosensitivity
    // safe mode never shows it (it is a luminance flash by definition) -- the
    // HP bar, the hurt voice and the hitstun tint all still report the hit.
    this.hurtFrame = this.scene.add.graphics().setDepth(19.2).setPosition(ox, oy).setAlpha(0);
    for (let i = 0; i < 8; i++) {
      const inset = i * 4;
      this.hurtFrame.fillStyle(0x7d1b20, 0.1);
      this.hurtFrame.fillRect(inset, inset, BASE_WIDTH - inset * 2, BASE_HEIGHT - inset * 2);
    }
    this.hud.push(this.hurtFrame);

    this.frameVignette = this.scene.add.graphics().setDepth(18.5).setPosition(ox, oy).setAlpha(0);
    for (let i = 0; i < 7; i++) {
      const inset = i * 5;
      this.frameVignette.fillStyle(0x05060a, 0.09);
      this.frameVignette.fillRect(inset, inset, BASE_WIDTH - inset * 2, BASE_HEIGHT - inset * 2);
    }
    // Bars slide in from off-frame. Tweening `y` rather than `height`: a
    // Phaser Shape computes its display origin when its size is set, so a
    // height tween under a bottom origin drew the bar off the bottom edge.
    const BAR = 7;
    this.frameBars = [
      this.scene.add.rectangle(ox, oy - BAR, BASE_WIDTH, BAR, 0x05060a, 1).setOrigin(0, 0).setDepth(19.4),
      this.scene.add.rectangle(ox, oy + BASE_HEIGHT, BASE_WIDTH, BAR, 0x05060a, 1).setOrigin(0, 0).setDepth(19.4),
    ];
    this.hud.push(this.frameVignette, ...this.frameBars);
    const reducedMotion = Boolean(GameContext.activeProfile?.settings.reducedMotion);
    const barRest = [oy, oy + BASE_HEIGHT - BAR];
    if (reducedMotion) {
      this.frameVignette.setAlpha(1);
      this.frameBars.forEach((bar, i) => bar.setY(barRest[i]));
    } else {
      this.scene.tweens.add({ targets: this.frameVignette, alpha: 1, duration: 340, ease: "Quad.easeOut" });
      this.frameBars.forEach((bar, i) => {
        this.scene.tweens.add({ targets: bar, y: barRest[i], duration: 300, ease: "Quad.easeOut" });
      });
    }

    // The exploration verbs are wrong now; swap in the combat ones.
    this.host.setExploreHudVisible?.(false);
    if (this.isBoss) {
      const name = getEnemy(encounter.enemyWave[0]).name.toUpperCase();
      this.hud.push(
        this.scene.add
          .nineslice(ox + BASE_WIDTH / 2 - 71, oy + 4, "ui_panel_boss", undefined, 142, 22, 5, 5, 5, 5)
          .setOrigin(0, 0)
          .setDepth(20)
          .setAlpha(0.94),
        this.scene.add
          .text(ox + BASE_WIDTH / 2, oy + 8, name, { fontFamily: "monospace", fontSize: "6px", color: "#f0a648" })
          .setOrigin(0.5, 0)
          .setDepth(21)
      );
    }

    void this.start(encounter.enemyWave, nodeWorldX, nodeWorldY);
  }

  private async start(enemyWave: string[], foeX: number, foeY: number): Promise<void> {
    const encounter = getEncounter(this.encounterId);
    const settings = GameContext.activeProfile!.settings;
    this.gameSpeed = settings.gameSpeed;

    // BEAT TRUTH (PRD §8.3): the judged beat is the playing song's authored
    // beat grid, read from the element's own position. Game speed scales the
    // song's playbackRate and the sim together (the grid lives in file-time,
    // so heard and judged beat cannot diverge under any speed setting).
    music.setVolume(settings.volumeMusic);
    music.setRate(this.gameSpeed);
    music.setMode(this.isBoss ? "boss" : "combat");
    music.start();
    const songId = music.currentSongId();
    this.songMap = songId ? (songMaps.get(songId) ?? null) : null;

    // Fallback grid for when the song is not audible (blocked autoplay,
    // headless test runs): the transport at the song's fitted tempo -- or,
    // with no song map at all, the encounter's legacy beatmap tempo.
    const fileBpm = this.songMap?.bpm ?? getBeatmap(encounter.trackId).bpm;
    this.beatSeconds = 60 / fileBpm;
    await this.clock.start(fileBpm * this.gameSpeed);
    if (this.finished) return; // torn down while the clock spun up

    // The always-on sonifier click is retired (it clicked a grid unrelated
    // to the music); the audible tick is now the opt-in §9.3 assist.
    if (settings.beatTickEnabled) {
      this.tick = new BeatTick();
      this.tick.setVolume(settings.volumeMusic * 0.5);
    }
    this.sfx = new SfxPlayer();
    this.sfx.setVolume(settings.volumeSfx);
    this.playerBaseScale = this.playerSprite.scaleX;
    this.feel = new GameFeel(this.scene, {
      reducedMotion: Boolean(settings.reducedMotion),
      photosensitive: Boolean(settings.photosensitivitySafeMode),
    });
    GameContext.analytics.track("battle_started", { encounterId: this.encounterId });

    // Fight text layer: tier popups (§11.3 judgment feedback) + captions
    // for musically meaningful events (§9.3, when enabled).
    this.tierPopup = this.scene.add
      .text(0, 0, "", { fontFamily: "monospace", fontSize: "8px", color: "#f4d27a", stroke: "#05060a", strokeThickness: 3 })
      .setOrigin(0.5, 1)
      .setDepth(22)
      .setAlpha(0);
    this.caption = this.scene.add
      .text(this.rect.x + BASE_WIDTH / 2, this.rect.y + BASE_HEIGHT - 13, "", {
        fontFamily: "monospace",
        fontSize: "7px",
        color: "#a89d84",
        stroke: "#05060a",
        strokeThickness: 3,
      })
      .setOrigin(0.5, 1)
      .setDepth(22)
      .setAlpha(0);
    this.hud.push(this.caption);
    if (settings.sightreadEnabled) {
      this.sightread = this.scene.add.graphics().setDepth(21).setPosition(this.rect.x, this.rect.y);
      this.hud.push(this.sightread);
    }

    // One-time controls hint with the player's actual (possibly remapped)
    // bindings; practice mode announces its no-fail state (§9.3).
    const b = GameContext.activeProfile?.settings.keyBindings ?? {};
    const keyOf = (a: CombatAction): string => keyNameFor(b[a], DEFAULT_ACTION_KEYS[a]);
    // A persistent combat strip that replaces the exploration one, in the
    // same slot, so the verbs on screen are always the verbs that work. It
    // rides ON the top letterbox bar rather than adding a third band.
    const ox = this.rect.x;
    const oy = this.rect.y;
    this.hud.push(
      this.scene.add
        .text(
          ox + BASE_WIDTH / 2,
          oy + 1,
          `${keyOf("light")} light   ${keyOf("heavy")} heavy   ${keyOf("parry")} parry   ${keyOf("dash")} dash   ${keyOf("special")} special   ${keyOf("ultimate")} ult`,
          { fontFamily: "monospace", fontSize: "6px", color: "#9fb0c0" }
        )
        .setOrigin(0.5, 0)
        .setDepth(19.6)
    );

    // Boss phases (§8.7): HP thresholds -> aggression + song-section jumps.
    if (this.isBoss) {
      const config = bossPhaseConfigs.get(this.encounterId);
      if (config) this.phaseThresholds = config.phases.map((p) => ({ hpThreshold: p.hpThreshold, section: p.section }));
    }

    const enemyHps = encounter.enemyWave.map((id) => getEnemy(id).maxHp);
    const arena = createArena(this.rect.width, this.rect.height, enemyHps);
    // Relics (§8.5) apply their real effects at fight start.
    applyRelics(arena, GameContext.activeProfile?.relicInventory ?? []);
    // Practice mode (§9.3): the sim floors player HP at 1 -- no fail state.
    if (settings.practiceMode) {
      arena.practice = true;
      this.showCaption("PRACTICE — THE CHORUS HOLDS YOU UP (no fail state)", 4);
    }

    // impassable terrain (water/rock tiles) becomes sim obstacles, one 16px
    // box per blocked tile, so fighters fight on the actual walkable ground
    const TILE = 16;
    const obstacles: { x: number; y: number; w: number; h: number }[] = [];
    for (let ty = Math.floor(this.rect.y / TILE) * TILE; ty < this.rect.bottom; ty += TILE) {
      for (let tx = Math.floor(this.rect.x / TILE) * TILE; tx < this.rect.right; tx += TILE) {
        if (!this.host.isWorldWalkable(tx + TILE / 2, ty + TILE / 2)) {
          obstacles.push({ x: tx - this.rect.x, y: ty - this.rect.y, w: TILE, h: TILE });
        }
      }
    }
    arena.obstacles = obstacles;

    // the player fights from where they actually stand; the foe wave spawns
    // around where the foe actually stood -- the world does not rearrange
    const p = getPlayer(arena);
    p.pos.x = Phaser.Math.Clamp(this.playerSprite.x - this.rect.x, 12, this.rect.width - 12);
    p.pos.y = Phaser.Math.Clamp(this.playerSprite.y - this.rect.y, 12, this.rect.height - 12);
    // A STANDOFF, not a coincidence. The foe stands on the node marker and the
    // player walks onto that same marker to start the fight, so both fighters
    // used to spawn inside each other -- the single worst readability bug in
    // the build: the opening frame of every fight was one unreadable blob.
    // The wave now backs off along the axis it was approached from, far enough
    // that the first thing the player sees is two separate silhouettes.
    const STANDOFF = 52;
    let ax = foeX - this.rect.x - p.pos.x;
    let ay = foeY - this.rect.y - p.pos.y;
    let len = Math.hypot(ax, ay);
    if (len < 1) {
      // Dead-on, which is in fact the NORMAL case: the room is centred on the
      // node the player just stepped onto, so foe and player and room centre
      // are all the same point. Back the foe off along the direction Mir is
      // facing instead -- he walked into this thing, so it should be in front
      // of him -- with a little downscreen bias so the two silhouettes are
      // never perfectly stacked on one horizontal line.
      ax = this.playerSprite.flipX ? 1 : -1;
      ay = 0.32;
      len = Math.hypot(ax, ay);
    }
    ax /= len;
    ay /= len;
    // fan the wave out PERPENDICULAR to the standoff axis, so a three-foe
    // wave is a line facing the player rather than a column behind itself
    getEnemies(arena).forEach((e, i) => {
      const fan = (i - (enemyWave.length - 1) / 2) * 30;
      e.pos.x = Phaser.Math.Clamp(p.pos.x + ax * STANDOFF - ay * fan, 16, this.rect.width - 16);
      e.pos.y = Phaser.Math.Clamp(p.pos.y + ay * STANDOFF + ax * fan, 16, this.rect.height - 16);

      const enemyId = enemyWave[i];
      // §8.6 curriculum: per-foe tempo/damage from authored content
      const def = getEnemy(enemyId);
      e.aggr = def.action?.aggression;
      e.strikeDamage = def.action?.damage;
      const tex = `enemy_${enemyId}`;
      const scale = FIGHT_SCALE[enemyId] ?? 0.25;
      const accent = FIGHT_ACCENT[enemyId] ?? 0xffffff;
      this.accents.set(e.id, accent);
      this.enemyIds.set(e.id, enemyId);
      this.lastEnemyHp.set(e.id, e.hp);
      const wx = this.rect.x + e.pos.x;
      const wy = this.rect.y + e.pos.y;
      this.shadows.set(e.id, this.scene.add.ellipse(wx, wy, 26, 8, 0x05060a, 0.42).setDepth(4.3));
      this.auras.set(
        e.id,
        this.scene.add.image(wx, wy - 8, "glow").setBlendMode(Phaser.BlendModes.ADD).setTint(accent).setDepth(4.32).setScale(1).setAlpha(0.35)
      );
      this.registerFoeClips(enemyId);
      const s = this.scene.add.sprite(wx, wy, tex, 0).setOrigin(0.5, 0.9).setScale(scale).setDepth(4.6);
      s.play(`foe_${enemyId}_idle`);
      this.foeState.set(e.id, "idle");
      this.sprites.set(e.id, s);
      if (!this.isBoss) {
        const plate = this.scene.add
          .text(wx, wy, def.name.toUpperCase(), {
            fontFamily: "monospace",
            fontSize: "6px",
            color: "#9fb0c0",
            stroke: "#05060a",
            strokeThickness: 3,
          })
          .setOrigin(0.5, 1)
          .setDepth(8.6)
          .setAlpha(0.85);
        this.namePlates.set(e.id, plate);
        this.hud.push(plate);
      }
    });
    this.arena = arena;
  }

  /** Full §8.3 four-tier judgment of "now" against the audible song's grid
   * (file-time windows, so reduced game speed widens them in real time);
   * transport-grid fallback when nothing is audible. */
  private judgeTier(): BeatTier {
    const calibMs = GameContext.activeProfile?.calibrationOffsetMs ?? 0;
    const assist = GameContext.activeProfile?.settings.assistedTimingWindows ? 1.5 : 1;

    const pos = music.position();
    if (this.songMap && pos !== null) return tierAt(this.songMap, pos, calibMs, assist);

    // Fallback: nothing audible (blocked autoplay / headless) -- judge on
    // the transport grid at the same tempo, as before beat maps existed.
    const t = this.clock.currentTime - calibMs / 1000;
    const beatSec = this.beatSeconds / this.gameSpeed; // transport runs in real time
    const phase = ((t % beatSec) + beatSec) % beatSec;
    return tierForOffset(Math.min(phase, beatSec - phase), assist);
  }

  /**
   * How "on the beat" NOW is, as a continuous 0..1 -- 1 exactly on a grid beat,
   * falling to 0 at the outer edge of the `good` window.
   *
   * The point is that the light the player sees IS the window they are judged
   * against, rather than a decoration that happens to sit near it. A binary
   * blink (what this replaced) tells you the beat has passed; a falling ramp
   * tells you how much of the window is left, which is a thing you can learn to
   * play. It widens with the assist setting for the same reason.
   */
  /** `beatFlash()` sampled once per rendered frame -- the enemy pass and the
   * HUD must agree, and sampling twice in one frame can straddle a beat. */
  private lastBeatFlash = 0;

  private beatFlash(): number {
    const calibMs = GameContext.activeProfile?.calibrationOffsetMs ?? 0;
    const assist = GameContext.activeProfile?.settings.assistedTimingWindows ? 1.5 : 1;
    const w = TIER_WINDOWS.good * assist;
    const pos = music.position();
    if (this.songMap && pos !== null) {
      const d = nearestBeatDistanceSeconds(this.songMap, pos - calibMs / 1000);
      return Math.max(0, 1 - d / w);
    }
    const t = this.clock.currentTime - calibMs / 1000;
    const beatSec = this.beatSeconds / this.gameSpeed;
    const phase = ((t % beatSec) + beatSec) % beatSec;
    return Math.max(0, 1 - Math.min(phase, beatSec - phase) / w);
  }

  /**
   * RELEASE GATE #1a's SEAM: is *now* inside the judged beat window?
   *
   * This is not visual code and nothing in the renderer calls it. It exists so
   * `tests/e2e/beat-truth.spec.ts` can sample the judged grid across a beat
   * interval and assert that the answer FLIPS -- a constant answer means
   * judgment has stopped tracking the playing audio, which is the one failure
   * the gate is there to catch.
   *
   * It was deleted along with the binary beat blink it used to drive, on the
   * (correct) grounds that the blink was worse than `beatFlash`'s falling ramp
   * -- but deleting the renderer's use of a value is not the same as deleting
   * the value, and it silently took release gate #1a's assertion with it. It is
   * defined in terms of `beatFlash` precisely so it cannot drift away from what
   * the player is actually judged against: same song map, same calibration
   * offset, same assist widening, same audio clock.
   */
  isOnBeat(): boolean {
    return this.beatFlash() > 0;
  }

  /** Stamps 2-3 small dark scuffs into the ground at a hit's WORLD position --
   * a persistent scar, not a transient spark. Reduced-motion still gets the
   * scuffs (they're static ground detail, not motion) but photosensitivity
   * safe mode skips them (rapid stamping during a flurry is still "flashing
   * new content" territory). Coordinates are LOCAL to the render texture,
   * which sits at this.rect's origin. */
  private stampScuff(worldX: number, worldY: number, color: number): void {
    if (!this.groundDecals || !this.decalStamp) return;
    if (GameContext.activeProfile?.settings.photosensitivitySafeMode) return;
    const lx = worldX - this.rect.x;
    const ly = worldY - this.rect.y;
    const n = 2 + Math.floor(Math.random() * 2);
    for (let i = 0; i < n; i++) {
      const dx = (Math.random() - 0.5) * 14;
      const dy = (Math.random() - 0.5) * 8 + 3; // biased toward the feet, not the head
      this.decalStamp
        .setTint(color)
        .setAlpha(0.55 + Math.random() * 0.25)
        .setScale(0.13 + Math.random() * 0.06)
        .setAngle(Math.random() * 360);
      this.groundDecals.draw(this.decalStamp, lx + dx, ly + dy);
    }
  }

  /** §11.3 judgment feedback: a brief tier label above the player. Off-tier
   * presses show nothing (information, not punishment). */
  private showTierPopup(tier: BeatTier): void {
    if (tier === "off" || !this.tierPopup) return;
    const p = this.arena ? getPlayer(this.arena) : null;
    if (!p) return;
    const label = TIER_LABEL[tier];
    this.tierPopup
      .setText(label.text)
      .setColor(label.color)
      .setPosition(Math.round(this.rect.x + p.pos.x), Math.round(this.rect.y + p.pos.y - 18))
      .setAlpha(1);
    this.scene.tweens.killTweensOf(this.tierPopup);
    this.scene.tweens.add({ targets: this.tierPopup, alpha: 0, y: this.tierPopup.y - 6, duration: 420 });
  }

  /** Caption line for musically meaningful events (§9.3). The controls hint
   * and practice notice always show; event captions require the setting. */
  private showCaption(text: string, seconds: number): void {
    if (!this.caption) return;
    this.caption.setText(text).setAlpha(1);
    this.captionUntil = this.scene.time.now + seconds * 1000;
  }

  private readInput(): FrameInput {
    const m = this.moveKeys;
    const left = this.cursors.left.isDown || m.A.isDown;
    const right = this.cursors.right.isDown || m.D.isDown;
    const up = this.cursors.up.isDown || m.W.isDown;
    const down = this.cursors.down.isDown || m.S.isDown;
    const move = { x: (right ? 1 : 0) - (left ? 1 : 0), y: (down ? 1 : 0) - (up ? 1 : 0) };
    const JD = Phaser.Input.Keyboard.JustDown;
    const k = this.actionKeys;
    const light = JD(k.light) || JD(this.spaceKey);
    const heavy = JD(k.heavy);
    const special = JD(k.special);
    const dash = JD(k.dash);
    const parry = JD(k.parry);
    const ultimate = JD(k.ultimate);
    const acted = light || heavy || special || dash || parry || ultimate;
    let tier: BeatTier = "off";
    if (acted) {
      tier = this.judgeTier();
      // Per-tier events feed the §5 on-beat-rate KPI (binary pair kept for
      // continuity with the pre-tier data).
      const tierEvent = { perfect: "judgment_perfect", great: "judgment_great", good: "judgment_good", off: "judgment_off" } as const;
      GameContext.analytics.track(tierEvent[tier], { encounterId: this.encounterId });
      GameContext.analytics.track(tier === "perfect" || tier === "great" ? "judgment_onbeat" : "judgment_offbeat", {
        encounterId: this.encounterId,
      });
      this.showTierPopup(tier);
    }
    const onBeat = tier === "perfect" || tier === "great";
    return { move, dash, light, heavy, special, ultimate, parry, onBeat, tier };
  }

  /** Test seam: the live sim (null until the audio clock is up). */
  get simArena(): Arena | null {
    return this.arena;
  }

  /** Drive one frame. Returns true while the fight is live. */
  update(deltaMs: number): boolean {
    if (this.finished) return false;
    if (!this.arena) return true; // clock still starting
    // Game speed slows the whole fight with the slowed song (§8.3.3).
    const dt = Math.min(deltaMs / 1000, 1 / 30) * this.gameSpeed;
    this.prevGroove = this.arena.groove;
    // Hand the sim the audible beat BEFORE stepping it, so foes telegraph onto
    // the grid the player is being judged against -- the same measured grid,
    // read off the same playing audio element (§10.2). When nothing is audible
    // this stays undefined and the sim falls back to its wall-clock telegraph.
    const beatPos = this.songMap ? music.position() : null;
    this.arena.beat = this.songMap && beatPos !== null ? (nextBeat(this.songMap, beatPos) ?? undefined) : undefined;
    step(this.arena, this.readInput(), dt);
    // M3: punctuate what the sim says happened, before anything infers it from
    // HP deltas. `deltaMs` (not `dt`) because a hold is presentation and must
    // run in real time even when the song -- and the sim -- is slowed (§8.3.3).
    this.feel.update(deltaMs);
    this.consumeImpacts();
    if (this.tick && this.songMap) {
      const pos = music.position();
      if (pos !== null) {
        const idx = beatIndexAt(this.songMap, pos);
        if (idx !== this.lastBeatIdx) {
          if (idx >= 0 && this.lastBeatIdx !== -1) this.tick.trigger();
          this.lastBeatIdx = idx;
        }
      }
    }

    const settings = GameContext.activeProfile?.settings;
    // Battle SFX from sim state transitions (never from render state).
    const p = getPlayer(this.arena);
    if (this.prevPlayerHp >= 0 && p.hp < this.prevPlayerHp - 0.01) {
      this.sfx?.hurt();
      this.stampScuff(this.playerSprite.x, this.playerSprite.y, 0x8a2020);
    }
    this.prevPlayerHp = p.hp;
    const reduced = Boolean(settings?.reducedMotion);
    if (p.state === "dash" && !this.wasDashing) {
      this.sfx?.dash();
      // dash after-images: two teal ghosts of the leader, fading fast
      if (!reduced) {
        for (let i = 0; i < 2; i++) {
          const ghost = this.scene.add
            .image(this.playerSprite.x, this.playerSprite.y, this.playerSprite.texture.key, this.playerSprite.frame.name)
            .setFlipX(this.playerSprite.flipX)
            .setScale(this.playerSprite.scaleX, this.playerSprite.scaleY)
            .setTint(0x49c6bd)
            .setAlpha(0.45 - i * 0.15)
            .setDepth(4.5);
          this.scene.tweens.add({ targets: ghost, alpha: 0, duration: 180 + i * 90, onComplete: () => ghost.destroy() });
        }
      }
    }
    this.wasDashing = p.state === "dash";
    if (this.arena.log.length > this.prevLogLen) {
      if (this.arena.log[this.arena.log.length - 1] === "parry!") {
        this.sfx?.parry();
        // parry burst: an expanding cyan ring at the player (§11.5 VFX)
        if (!reduced) {
          const ring = this.scene.add.circle(this.playerSprite.x, this.playerSprite.y - 6, 7).setStrokeStyle(2, 0x9fe8e0, 1).setDepth(9);
          this.scene.tweens.add({ targets: ring, scale: 3, alpha: 0, duration: 260, onComplete: () => ring.destroy() });
        }
      }
      this.prevLogLen = this.arena.log.length;
    }

    // Ultimate went off this tick (§8.5): the full-Groove verse.
    if (this.prevGroove >= ULTIMATE_GROOVE_COST && this.arena.groove <= this.prevGroove - ULTIMATE_GROOVE_COST) {
      GameContext.analytics.track("ultimate_used", { encounterId: this.encounterId });
      this.sfx?.ultimate();
      if (!settings?.reducedMotion && !settings?.photosensitivitySafeMode) this.scene.cameras.main.shake(280, 0.012);
      if (settings?.captionsEnabled) this.showCaption("♪ ULTIMATE — THE VERSE BREAKS THE SONG", 2);
      this.grooveWasFull = false;
    } else if (!this.grooveWasFull && this.arena.groove >= ULTIMATE_GROOVE_COST) {
      this.grooveWasFull = true;
      if (settings?.captionsEnabled) this.showCaption("GROOVE FULL — ULTIMATE READY", 2.5);
    } else if (this.arena.groove < ULTIMATE_GROOVE_COST) {
      this.grooveWasFull = false;
    }

    this.checkBossPhase();
    if (this.caption && this.caption.alpha > 0 && this.scene.time.now > this.captionUntil) {
      this.caption.setAlpha(Math.max(0, this.caption.alpha - deltaMs / 300));
    }
    this.render();
    if (this.arena.outcome !== "ongoing") {
      this.finished = true;
      this.finish(this.arena.outcome);
      return false;
    }
    return true;
  }

  /** Turn this tick's sim events into hitstop, impact frames and sparks
   * (M3). The sim states damage, tier and direction, so nothing here has to
   * guess: an off-beat jab and a perfect heavy produce visibly different
   * events, which is the whole point of judging on a beat. */
  private consumeImpacts(): void {
    const evs = this.arena?.events;
    if (!evs || !evs.length) return;
    for (const ev of evs) {
      const targetSprite = ev.targetId === "player" ? this.playerSprite : this.sprites.get(ev.targetId);
      const attackerSprite = ev.attackerTeam === "player" ? this.playerSprite : undefined;
      this.feel.impact(ev, this.rect.x + ev.x, this.rect.y + ev.y, targetSprite, attackerSprite);
      // one voice per event, pitched by tier -- the ear learns the beat too.
      // The parry voice is fired off the log, so it is not doubled here.
      if (ev.kind !== "parry" && ev.targetTeam === "enemy") this.sfx?.impact(ev.tier, ev.heavy, ev.kind === "fall");
      if (ev.kind === "hit" && ev.targetTeam === "player") this.bleedFrame(ev.heavy);
    }
  }

  /** Flash the room's edge red -- Mir has been hit. */
  private bleedFrame(heavy: boolean): void {
    const settings = GameContext.activeProfile?.settings;
    if (!this.hurtFrame || settings?.photosensitivitySafeMode) return;
    this.scene.tweens.killTweensOf(this.hurtFrame);
    this.hurtFrame.setAlpha(heavy ? 0.95 : 0.7);
    this.scene.tweens.add({
      targets: this.hurtFrame,
      alpha: 0,
      duration: settings?.reducedMotion ? 120 : heavy ? 480 : 320,
      ease: "Quad.easeOut",
    });
  }

  /** Register one Phaser animation per authored foe state, once per foe type.
   * Frame counts are read off the loaded texture so re-authoring a strip in
   * `tools/art/` can never desync the engine's ranges. */
  private registerFoeClips(foeId: string): void {
    for (const [state, spec] of Object.entries(FOE_CLIP)) {
      const key = `foe_${foeId}_${state}`;
      if (this.scene.anims.exists(key)) continue;
      const tex = state === "idle" ? `enemy_${foeId}` : `enemy_${foeId}_${state}`;
      if (!this.scene.textures.exists(tex)) continue;
      const last = this.scene.textures.get(tex).frameTotal - 2; // -1 for __BASE
      this.scene.anims.create({
        key,
        frames: this.scene.anims.generateFrameNumbers(tex, { start: 0, end: Math.max(0, last) }),
        frameRate: spec.fps,
        repeat: spec.loop ? -1 : 0,
      });
    }
  }

  /** Which authored state a foe is in RIGHT NOW. The order is a priority
   * ladder, not a switch: death outranks pain, pain outranks intent. */
  private foeStateFor(e: ReturnType<typeof getEnemies>[number]): string {
    if (e.state === "dead") return "dead";
    if (e.state === "hitstun") return "hurt";
    if (e.attack) return "attack";
    if (e.ai?.mode === "windup") return "telegraph";
    if (Math.hypot(e.vel.x, e.vel.y) > 8) return "move";
    return "idle";
  }

  /** Same ladder for Mir. `attack`/`heavy` are handled by the caller (they are
   * scrubbed by attack phase rather than played), so they are absent here. */
  private playerStateFor(p: ReturnType<typeof getPlayer>): string {
    if (p.hp <= 0 || p.state === "dead") return "down";
    if (p.state === "hitstun") return "hurt";
    if (p.parryTimer > 0) return "parry";
    if (p.state === "dash") return "dash";
    if (Math.hypot(p.vel.x, p.vel.y) > 12) return "run";
    return "idle";
  }

  /** §8.7: advance the boss phase when its HP crosses the next authored
   * threshold -- playback jumps to the phase's bound song section (the
   * judged grid follows automatically: it IS the same grid), the enemy
   * tempo escalates, and the transition is announced. */
  private checkBossPhase(): void {
    if (!this.isBoss || !this.arena || this.phaseIdx >= this.phaseThresholds.length - 1) return;
    const boss = getEnemies(this.arena)[0];
    if (!boss || boss.state === "dead") return;
    const next = this.phaseThresholds[this.phaseIdx + 1];
    if (boss.hp / boss.maxHp > next.hpThreshold) return;

    this.phaseIdx += 1;
    this.arena.enemyAggression = 1 + 0.35 * this.phaseIdx;
    const section = next.section ? this.songMap?.sections?.find((s) => s.name === next.section) : undefined;
    if (section) music.seek(section.startMs / 1000);
    GameContext.analytics.track("boss_phase_reached", { encounterId: this.encounterId, phase: this.phaseIdx + 1 });
    const numeral = ["I", "II", "III", "IV"][this.phaseIdx] ?? String(this.phaseIdx + 1);
    const settings = GameContext.activeProfile?.settings;
    if (settings?.captionsEnabled) this.showCaption(`♪ THE MUSIC SHIFTS — MOVEMENT ${numeral}`, 3);
    if (!settings?.reducedMotion && !settings?.photosensitivitySafeMode) this.scene.cameras.main.shake(220, 0.008);
  }

  /** Test seam: current boss phase index (0-based). */
  get bossPhaseIndex(): number {
    return this.phaseIdx;
  }

  private render(): void {
    const arena = this.arena!;
    this.lastBeatFlash = GameContext.activeProfile?.settings.photosensitivitySafeMode ? 0 : this.beatFlash();
    const reduced = Boolean(GameContext.activeProfile?.settings.reducedMotion);
    const p = getPlayer(arena);

    // player: drive the leader's actual world sprite
    const pwx = this.rect.x + p.pos.x;
    const pwy = this.rect.y + p.pos.y;
    this.playerSprite.setPosition(Math.round(pwx), Math.round(pwy));
    this.feel.decorate("player", this.playerSprite, this.playerBaseScale);
    if (p.facing === "left") this.playerSprite.setFlipX(false);
    else if (p.facing === "right") this.playerSprite.setFlipX(true);
    if (p.attack) {
      // Scrub the swing off the SIM's own phase rather than playing a clip, so
      // anticipation / impact / recovery land on exactly the frames the sim is
      // in -- the difference between a swing that connects and one that looks
      // like it happened next to the enemy. Heavy has its own longer arc.
      const heavy = p.attack.def === HEAVY || p.attack.def === SPECIAL || p.attack.def === ULTIMATE;
      const tex = heavy && this.scene.textures.exists("band_mir_heavy") ? "band_mir_heavy" : "band_mir_attack";
      const total = this.scene.textures.get(tex).frameTotal - 1; // -1 for __BASE
      const ph = p.attack.phase === "startup" ? 0 : p.attack.phase === "active" ? 1 : 2;
      // startup occupies the first half of the strip (the wind-up is the part
      // worth frames), impact one frame, recovery the tail
      const frame =
        ph === 0
          ? Math.min(total - 1, Math.floor(total * 0.4))
          : ph === 1
            ? Math.min(total - 1, Math.floor(total * 0.6))
            : total - 1;
      if (this.playerSprite.anims.isPlaying) this.playerSprite.anims.stop();
      this.playerSprite.setTexture(tex, frame);
      this.playerState = "";
    } else {
      const want = this.playerStateFor(p);
      if (want !== this.playerState) {
        this.playerState = want;
        const clip = MIR_CLIP[want];
        // The overworld already owns `leader_idle`/`leader_walk`; reuse them so
        // one figure never has two competing idle definitions.
        const key = want === "idle" ? "leader_idle" : want === "run" ? "leader_walk" : `mir_${want}`;
        if (clip && !this.scene.anims.exists(key) && this.scene.textures.exists(clip.key)) {
          const last = this.scene.textures.get(clip.key).frameTotal - 2;
          this.scene.anims.create({
            key,
            frames: this.scene.anims.generateFrameNumbers(clip.key, { start: 0, end: Math.max(0, last) }),
            frameRate: clip.fps,
            repeat: clip.loop ? -1 : 0,
          });
        }
        if (this.scene.anims.exists(key)) this.playerSprite.play(key, true);
      } else if (!this.playerSprite.anims.isPlaying && (want === "idle" || want === "run")) {
        this.playerSprite.play(want === "idle" ? "leader_idle" : "leader_walk");
      }
    }
    // Same as the foes (see GameFeel.flash): the flash is the hold, not the
    // hitstun. Mir's own hold key is the target id the sim emitted for him.
    const pfl = reduced ? 0 : this.feel.flash(p.id);
    if (pfl > 0.5) this.playerSprite.setTintFill(0xffffff);
    else if (pfl > 0) this.playerSprite.setTint(0xffb9a8);
    else this.playerSprite.clearTint();
    this.playerSprite.setAlpha(p.iframes > 0 && !reduced ? (Math.floor(this.scene.time.now / 60) % 2 ? 0.4 : 1) : 1);

    // attack glow arc
    if (p.attack?.phase === "active") {
      const d = { up: [0, -1], down: [0, 1], left: [-1, 0], right: [1, 0] }[p.facing];
      this.attackGlow
        .setPosition(pwx + d[0] * p.attack.def.reach, pwy + d[1] * p.attack.def.reach)
        .setScale((p.attack.def.radius / 48) * (p.attack.onBeat ? 1.5 : 1))
        .setAlpha(p.attack.onBeat ? 0.9 : 0.6);
    } else {
      this.attackGlow.setAlpha(0);
    }

    // enemies
    this.fx.clear();
    for (const e of getEnemies(arena)) {
      const s = this.sprites.get(e.id);
      if (!s) continue;
      const wx = this.rect.x + e.pos.x;
      const wy = this.rect.y + e.pos.y;
      if (e.state === "dead") {
        // death dissolve (§11.5 VFX): one burst + a sink-and-fade, once
        if (!this.deadHandled.has(e.id)) {
          this.deadHandled.add(e.id);
          this.auras.get(e.id)?.setAlpha(0);
          this.shadows.get(e.id)?.setAlpha(0);
          this.namePlates.get(e.id)?.setVisible(false);
          // the authored death: it stops holding itself together. Played once,
          // and the fade below rides on top of it rather than replacing it.
          const deathKey = `foe_${this.enemyIds.get(e.id) ?? ""}_dead`;
          if (this.scene.anims.exists(deathKey)) {
            this.foeState.set(e.id, "dead");
            s.play(deathKey, true);
          }
          if (!reduced) {
            for (let i = 0; i < 3; i++) {
              const spark = this.scene.add
                .image(s.x + (i - 1) * 6, s.y - 10 - i * 4, "spark")
                .setBlendMode(Phaser.BlendModes.ADD)
                .setDepth(9)
                .setScale(0.3)
                .setTint(this.accents.get(e.id) ?? 0xfff4d0);
              this.scene.tweens.add({ targets: spark, scale: 1.3, alpha: 0, angle: 70, duration: 380 + i * 80, onComplete: () => spark.destroy() });
            }
            this.scene.tweens.add({ targets: s, alpha: 0.08, y: s.y + 3, duration: 550 });
          } else {
            s.setAlpha(0.08);
          }
        }
        continue;
      }
      // The six authored states carry the anticipation / impact / recovery
      // read now (tools/art/foes.py), so the only thing left for code is the
      // LUNGE -- travel toward the target on the active frames, which is what
      // sells contact. The old scale tweens faked the whole performance and
      // are gone; a state is only a state if the shape changes.
      const foeId = this.enemyIds.get(e.id) ?? "";
      const base = FIGHT_SCALE[foeId] ?? 0.25;
      const want = this.foeStateFor(e);
      if (want !== this.foeState.get(e.id)) {
        this.foeState.set(e.id, want);
        const key = `foe_${foeId}_${want}`;
        if (this.scene.anims.exists(key)) s.play(key, true);
      }
      const lunge = e.attack?.phase === "active" ? 5 : 0;
      const d = FACING_LUNGE[e.facing] ?? { x: 0, y: 0 };
      s.setScale(base);
      s.setPosition(Math.round(wx + d.x * lunge), Math.round(wy + d.y * lunge)).setDepth(4.6 + e.pos.y / 1000);
      this.feel.decorate(e.id, s, base);
      this.shadows.get(e.id)?.setPosition(Math.round(wx), Math.round(wy));
      const windup = e.ai?.mode === "windup";
      if (windup && !this.wasWindup.has(e.id)) {
        this.wasWindup.add(e.id);
        // SIGHTREAD, NOT CAPTIONS. This was gated on `captionsEnabled`, which is
        // on by default and is a §9.3 AUDIO caption setting -- it exists so a
        // player who cannot hear the music still gets "♪ THE MUSIC SHIFTS" and
        // "GROOVE FULL". An incoming attack is not audio: it is a visual tell,
        // and duplicating it as text put a centre-screen all-caps warning
        // banner in every fight, several times per fight, by default. It is a
        // combat FORECAST assist, so it belongs to `sightreadEnabled` (§8.4,
        // "see the music" -- which the setting's own doc comment already says
        // covers "telegraphed enemy strikes previewed on the fight HUD").
        // Nothing is lost: the tell itself is now a closing ground ring, a
        // six-state telegraph pose and a red aura, all three on by default.
        if (GameContext.activeProfile?.settings.sightreadEnabled) {
          const side = e.pos.x < getPlayer(arena).pos.x ? "LEFT" : "RIGHT";
          this.showCaption(`⚠ ATTACK INCOMING — ${side}`, 1.2);
        }
      } else if (!windup) {
        this.wasWindup.delete(e.id);
      }
      const accent = this.accents.get(e.id) ?? 0xffffff;
      // The foes breathe with the song too, so the beat is legible in
      // peripheral vision while you are watching a telegraph rather than a HUD.
      // A winding-up foe stops breathing and goes hard red: the one state that
      // must never be mistaken for ambience.
      this.auras
        .get(e.id)
        ?.setPosition(wx, wy - 8)
        .setTint(windup ? 0xc22f34 : accent)
        // 0.7 was tuned when the aura WAS the telegraph. With a closing ground
        // ring under the foe it is a 64px red cloud on top of one, and in the
        // Fold it washed straight over the waystone standing behind it.
        .setAlpha(windup ? 0.34 : 0.2 + this.lastBeatFlash * 0.26)
        .setScale(windup ? 0.72 : 1);
      // THE TELEGRAPH IS A GROUND TELL, not a ring drawn round the creature.
      // A 2px hard red circle is 8 screen pixels of pure 0xc22f34 at the 4x
      // zoom, sitting on top of the foe's silhouette: it read as a debug gizmo
      // and it hid the telegraph POSE, which is the animation state that
      // actually tells you what is coming (§11.5 ships six states per foe for
      // exactly this). Two rings on the floor instead -- thin, and the inner
      // one closing as the wind-up completes, so the tell is a countdown.
      if (windup) {
        const t = Phaser.Math.Clamp(1 - (e.ai?.timer ?? 0) / 0.42, 0, 1);
        this.fx.lineStyle(1, 0xc22f34, 0.55).strokeEllipse(wx, wy - 1, 30, 11);
        this.fx.lineStyle(1, 0xe04434, 0.85).strokeEllipse(wx, wy - 1, 30 - 22 * t, 11 - 8 * t);
      }
      // The hit flash is driven by GameFeel's hold, not by `hitstun`: see
      // GameFeel.flash. Hard white for the front half, a warm bruise as it
      // releases, then the art comes back.
      const fl = reduced ? 0 : this.feel.flash(e.id);
      if (fl > 0.5) s.setTintFill(0xffffff);
      else if (fl > 0) s.setTint(0xffcdb4);
      else s.clearTint();
      // The undirected spark and the untyped `hit()` voice that used to live
      // here are retired: both were inferred from an HP delta, so neither could
      // know the tier, the weight, or which way the blow travelled, and both
      // fired in the same shape for a jab and an ultimate. GameFeel does it off
      // the sim's own events now (`consumeImpacts`). What stays is the GROUND
      // SCAR, which is not an impact effect -- it is world state, and it wants
      // the render position rather than the contact point.
      const prev = this.lastEnemyHp.get(e.id) ?? e.hp;
      if (e.hp < prev - 0.01) {
        const r = (accent >> 16) & 0xff, g = (accent >> 8) & 0xff, b = accent & 0xff;
        this.stampScuff(wx, wy, ((r * 0.6) << 16) | ((g * 0.6) << 8) | (b * 0.6));
      }
      this.lastEnemyHp.set(e.id, e.hp);
    }

    // bars + plate
    this.bars.clear();
    const foes = getEnemies(arena);
    let nearestId = "";
    let nearestD = Infinity;
    for (const f of foes) {
      if (f.state === "dead") continue;
      const d = Math.hypot(f.pos.x - p.pos.x, f.pos.y - p.pos.y);
      if (d < nearestD) {
        nearestD = d;
        nearestId = f.id;
      }
    }
    for (let i = 0; i < foes.length; i++) {
      const f = foes[i];
      if (f.state === "dead") continue;
      if (this.isBoss && i === 0) continue; // boss bar is screen-space below
      const s = this.sprites.get(f.id);
      const w = 16;
      const x = Math.round(this.rect.x + f.pos.x - w / 2);
      const y = Math.round(this.rect.y + f.pos.y - (s ? s.displayHeight * 0.95 : 24));
      this.bars.fillStyle(0x05060a, 0.8).fillRect(x - 1, y - 1, w + 2, 3);
      // the bar goes RED only while it is winding up; the rest of the time it
      // is the foe's own accent, so "about to hit you" is a colour change the
      // eye catches without reading anything
      const winding = f.ai?.mode === "windup" || Boolean(f.attack);
      this.bars.fillStyle(winding ? 0xc22f34 : (this.accents.get(f.id) ?? 0xc22f34), 1);
      this.bars.fillRect(x, y, Math.max(0, Math.round((f.hp / f.maxHp) * w)), 1);
      // A named foe is a foe you can lose to. Nameplates were boss-only, so
      // every ordinary fight was a fight against an unlabelled shape. Only ONE
      // plate is shown -- the nearest live foe -- because a wave of three
      // stacks three labels into an illegible pile, and the label the player
      // needs is the one on the thing about to hit them.
      const plate = this.namePlates.get(f.id);
      if (plate) {
        const near = f.id === nearestId;
        plate.setVisible(near);
        if (near) plate.setPosition(Math.round(this.rect.x + f.pos.x), y - 3);
      }
    }

    // The beat, breathing rather than blinking (see beatFlash). Safe mode holds
    // it still: a 2Hz pulse is inside the flash guideline, but the setting means
    // "no rhythmic luminance change", and the tier popup still says everything
    // this says.
    const bf = this.lastBeatFlash;
    this.beatPulse.setScale(1 + bf * 0.85).setFillStyle(Phaser.Display.Color.Interpolate.ColorWithColor(
      Phaser.Display.Color.ValueToColor(0x49c6bd),
      Phaser.Display.Color.ValueToColor(0xf4d27a),
      100,
      Math.round(bf * 100),
    ).color ?? 0x49c6bd);
    const g = this.plate;
    g.clear();
    const px0 = 9;
    const hpY = BASE_HEIGHT - 22;
    const hpW = 78;
    g.fillStyle(0x05060a, 0.9).fillRect(px0 - 1, hpY - 1, hpW + 2, 5);
    g.fillStyle(0x7d1b20, 1).fillRect(px0, hpY, hpW, 3);
    g.fillStyle(0x49c6bd, 1).fillRect(px0, hpY, Math.max(0, Math.round((p.hp / p.maxHp) * hpW)), 3);
    for (let i = 0; i < 5; i++) g.fillStyle(i < arena.focus ? 0xf4d27a : 0x2a3138, 1).fillRect(px0 + i * 7, hpY + 7, 5, 3);
    const grW = 40;
    g.fillStyle(0x2a3138, 1).fillRect(px0 + 38, hpY + 7, grW, 3);
    // Groove: pulses bright when the ultimate is ready (§8.5).
    const grooveReady = arena.groove >= ULTIMATE_GROOVE_COST;
    const pulse = grooveReady && Math.floor(this.scene.time.now / 220) % 2 === 0;
    // SALT, not amethyst. This was 0xb98fca -- the master palette's `u`, captioned
    // "sapphire purses, twilight, esoteric" from the game's previous art
    // direction -- and it put a magenta pip in the corner of every fight. There
    // is no purple in this world. Groove needs to be legible against HP (teal)
    // and focus (amber) without inventing a fourth hue, so it is bone: pale,
    // unmistakably neither of the other two, and the right register for a meter
    // whose payoff is "the verse breaks the song".
    g.fillStyle(pulse ? 0xf4efe2 : 0xa89d84, 1).fillRect(px0 + 38, hpY + 7, Math.round((arena.groove / 100) * grW), 3);
    if (this.isBoss && foes[0] && foes[0].state !== "dead") {
      const bw = 130;
      const bx = BASE_WIDTH / 2 - bw / 2;
      g.fillStyle(0x1a0507, 1).fillRect(bx, 18, bw, 4);
      g.fillStyle(0xe04434, 1).fillRect(bx, 18, Math.max(0, Math.round((foes[0].hp / foes[0].maxHp) * bw)), 4);
      // authored phase markers on the trough (§8.7)
      for (let i = 1; i < this.phaseThresholds.length; i++) {
        g.fillStyle(0x05060a, 1).fillRect(bx + Math.round(this.phaseThresholds[i].hpThreshold * bw) - 1, 17, 1, 6);
      }
    }

    this.drawSightread(arena);
  }

  /** Sightread (§8.4): the "see the music" forecast lane -- the next ~2.5s
   * of song beats scroll toward a now-line, with telegraphed enemy strikes
   * marked in red so the player reads the fight before it lands. */
  private drawSightread(arena: Arena): void {
    if (!this.sightread) return;
    const g = this.sightread;
    g.clear();
    const pos = music.position();
    if (!this.songMap || pos === null) return;
    const laneW = 92;
    const laneX = BASE_WIDTH - laneW - 6;
    const laneY = BASE_HEIGHT - 12;
    const horizon = 2.5; // seconds of forecast, in file-time
    g.fillStyle(0x05060a, 0.72).fillRect(laneX - 3, laneY - 5, laneW + 6, 10);
    g.fillStyle(0xf4d27a, 1).fillRect(laneX, laneY - 4, 1, 8); // the now-line
    // upcoming beats from the grid (loop-aware into the next pass)
    const beats = this.songMap.beatTimesMs;
    const posMs = pos * 1000;
    for (let pass = 0; pass < 2; pass++) {
      const shift = pass * this.songMap.durationMs;
      for (const b of beats) {
        const dt = (b + shift - posMs) / 1000;
        if (dt < 0) continue;
        if (dt > horizon) break;
        const x = laneX + (dt / horizon) * laneW;
        g.fillStyle(0x49c6bd, 0.9).fillRect(Math.round(x), laneY - 2, 1, 4);
      }
      if (beats.length > 0 && (beats[0] + shift - posMs) / 1000 > horizon) break;
    }
    // telegraphed enemy strikes: windup remainder + attack startup, sim-time
    // (sim and song both run at gameSpeed, so the axes agree)
    for (const e of getEnemies(arena)) {
      if (e.state === "dead" || e.ai?.mode !== "windup") continue;
      const dt = Math.max(0, e.ai.timer) + 0.28; // ENEMY_STRIKE startup
      if (dt > horizon) continue;
      const x = laneX + (dt / horizon) * laneW;
      g.fillStyle(0xc22f34, 1).fillRect(Math.round(x) - 1, laneY - 4, 3, 8);
    }
  }

  /** Rewards + campaign progression (ported from the retired arena scene's
   * finishBattle) -> ResultsScene; restarting scenes cleans everything up. */
  private finish(outcome: "victory" | "defeat"): void {
    this.host.setExploreHudVisible?.(true);
    this.clock.stop();
    this.tick?.dispose();
    this.sfx?.dispose();
    this.feel?.destroy();
    music.setRate(1); // the world outside the fight runs (and sounds) at 1x
    const profile = GameContext.activeProfile!;
    const encounter = getEncounter(this.encounterId);
    const victory = outcome === "victory";
    const newlyUnlockedSkills: string[] = [];

    if (victory) {
      profile.campaignProgress.xp += encounter.victoryRewards.xp;
      profile.campaignProgress.currency += encounter.victoryRewards.currency;
      if (this.nodeId) {
        if (!profile.campaignProgress.clearedNodeIds.includes(this.nodeId)) profile.campaignProgress.clearedNodeIds.push(this.nodeId);
        const node = getCampaignNode(this.nodeId);
        if (node.next.length > 0) profile.campaignProgress.currentNodeId = node.next[0];
        if (node.type === "boss") {
          for (const classId of ["warrior", "tank", "mage", "healer"]) {
            const skillId = `${classId}_tier2`;
            if (!profile.unlockedSkills.includes(skillId)) {
              profile.unlockedSkills.push(skillId);
              newlyUnlockedSkills.push(skillId);
            }
          }
          // The FINAL boss: route the results screen into the ending.
          if (node.next.length === 0) {
            GameContext.campaignJustCompleted = true;
            profile.campaignCompletedAt ??= Date.now();
          }
        }
      }
      GameContext.analytics.track("encounter_cleared", { encounterId: this.encounterId });
    } else {
      GameContext.analytics.track("encounter_failed", { encounterId: this.encounterId });
    }

    const relicChoices = victory
      ? (encounter.victoryRewards.relicChoices ?? []).filter((id) => !profile.relicInventory.includes(id))
      : [];

    GameContext.lastBattleResult = {
      outcome: victory ? "victory" : "defeat",
      encounterId: this.encounterId,
      xp: victory ? encounter.victoryRewards.xp : 0,
      currency: victory ? encounter.victoryRewards.currency : 0,
      relicChoices,
      unlockedSkills: newlyUnlockedSkills,
    };
    GameContext.pendingEncounterId = null;
    GameContext.returnToNodeId = this.nodeId;
    GameContext.pendingNodeId = null;

    void GameContext.persistActiveProfile().then(() => sceneGoto(this.scene, "ResultsScene"));
  }

  /** Immediate teardown (scene shutdown while a fight is live). */
  destroy(): void {
    this.host.setExploreHudVisible?.(true);
    this.finished = true;
    this.clock.stop();
    this.tick?.dispose();
    this.sfx?.dispose();
    this.feel?.destroy();
    music.setRate(1);
  }
}
