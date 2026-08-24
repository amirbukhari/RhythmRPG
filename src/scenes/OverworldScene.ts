import Phaser from "phaser";
import { GameContext } from "../state/GameContext";
import { campaign, getCampaignNode, getEncounter, songMaps } from "../data/ContentRegistry";
import { nearestBeatDistanceSeconds } from "../systems/audio/SongBeat";
import type { SongMap } from "../data/schemas/SongMap";
import { resolveEncounterId } from "../systems/progression/CampaignSelection";
import { nodeStatus, type NodeStatus } from "../systems/progression/CampaignReachability";
import { stepTarget, isWalkable, type Direction, type GridPosition } from "../systems/overworld/OverworldMovement";
import tilesetUrl from "../../assets/tilemaps/overworld_tileset.png";
import tilemapUrl from "../../assets/tilemaps/overworld.json?url";
import propsUrl from "../../assets/sprites/overworld/props.png";
import { BASE_WIDTH, BASE_HEIGHT, RENDER_SCALE } from "../config/GameConfig";
import { music } from "../systems/audio/SongPlayer";
import { WorldFight } from "./overworld/WorldFight";
import { composeWorldVenue } from "./env/ArenaComposer";
import dressingData from "../data/content/overworld/dressing.json";
import { worldScaleFor } from "./env/WorldScale";
import { NPCS, type NpcDef, type NpcLook } from "../data/content/dialogue";
import { CutsceneScene } from "./CutsceneScene";
import { sceneEnter } from "./Transition";

/** A dialogue NPC placed on a walkable tile in the world. */
interface PlacedNpc {
  def: NpcDef;
  col: number;
  row: number;
  fig: Phaser.GameObjects.Container;
  label: Phaser.GameObjects.Text;
}

/**
 * Per-role figure spec for drawNpc. These are drawn (not sprited) little
 * people -- so each role gets a distinct silhouette: robed vs. legged,
 * hooded vs. bare-headed, staffed, stooped, with skin/hair/robe tones that
 * read at 4x zoom. The point is that an elder, a child and a hooded stranger
 * are recognizably different bodies, not recolored blobs.
 */
type FigureSpec = {
  robe: number;
  robeLit: number;
  robeDark: number;
  skin: number;
  skinShade: number;
  hair: number;
  hood: boolean; // full cowl, face lost in shadow
  legs: boolean; // legs+tunic instead of a floor-length robe
  staff: boolean; // leans on a walking staff
  beard: boolean;
  stoop: number; // px the head/torso tips forward (age, reverence)
  scale: number;
  shoulder: number; // shoulder span
};
const FIGURE_SPECS: Record<NpcLook, FigureSpec> = {
  elder: { robe: 0x2f3742, robeLit: 0x46515d, robeDark: 0x1b2028, skin: 0xa88d72, skinShade: 0x6f5844, hair: 0xccd1d6, hood: false, legs: false, staff: true, beard: true, stoop: 2.1, scale: 0.98, shoulder: 6.6 },
  woman: { robe: 0x4a3129, robeLit: 0x6a483a, robeDark: 0x2b1c17, skin: 0xba8f76, skinShade: 0x7c5c49, hair: 0x281a16, hood: false, legs: false, staff: false, beard: false, stoop: 0.5, scale: 0.95, shoulder: 6.0 },
  man: { robe: 0x2c3a44, robeLit: 0x415560, robeDark: 0x18232b, skin: 0xac846a, skinShade: 0x6f5340, hair: 0x22190f, hood: false, legs: true, staff: false, beard: false, stoop: 0.4, scale: 1.0, shoulder: 7.2 },
  child: { robe: 0x3f5a3e, robeLit: 0x587659, robeDark: 0x243624, skin: 0xbe967a, skinShade: 0x836248, hair: 0x2f2219, hood: false, legs: true, staff: false, beard: false, stoop: 0.3, scale: 0.64, shoulder: 6.2 },
  pilgrim: { robe: 0x2a3742, robeLit: 0x3f505c, robeDark: 0x172029, skin: 0xa5805f, skinShade: 0x6c5142, hair: 0x2b251f, hood: false, legs: false, staff: true, beard: false, stoop: 1.0, scale: 0.98, shoulder: 6.4 },
  hooded: { robe: 0x20222c, robeLit: 0x34394b, robeDark: 0x101018, skin: 0x6a5c50, skinShade: 0x3f362e, hair: 0x24273a, hood: true, legs: false, staff: false, beard: false, stoop: 0.3, scale: 1.0, shoulder: 6.6 },
};

// v15.0 chunked ground: the painter emits a manifest describing the chunk
// grid; the chunks themselves are loaded in BootScene as `ground_chunk_<r>_<c>`.
type GroundManifest = { chunk: number; rows: number; cols: number; full_w: number; full_h: number; s: number };
const GROUND_MANIFEST = Object.values(
  import.meta.glob("../../assets/tilemaps/ground_plate_manifest.json", { eager: true, import: "default" })
)[0] as GroundManifest | undefined;

const TILE_SIZE = 16;
const STEP_DURATION_MS = 96; // was 160 -- walking felt sluggish (owner feedback)
const MARKER_COLORS: Record<NodeStatus, number> = { cleared: 0x44cc66, unlocked: 0xffe066, locked: 0x444444 };
const NODE_TYPE_LABEL: Record<string, string> = { battle: "B", elite: "E", boss: "!", camp: "C" };
// Emissive accent per foe for its overworld aura (mirrors ActionBattleScene).
const FOE_ACCENT: Record<string, number> = {
  the_conductor: 0xf0a648,
  elite_wraith: 0x49c6bd,
  drifter: 0x9fe8e0,
  slime: 0x9aca43,
};

interface Marker {
  nodeId: string;
  col: number;
  row: number;
}

interface Echo {
  id: string;
  title: string;
  text: string;
  col: number;
  row: number;
}

// Decorative props (props.py PROPS, minus the reserved "echo_rune" marker
// appended last) are frames 0..DECORATIVE_PROP_COUNT-1 on the shared sheet;
// the echo marker is always the frame right after them.
const DECORATIVE_PROP_COUNT = 6;
const ECHO_RUNE_FRAME = DECORATIVE_PROP_COUNT;
// Region 0 was named "shallows" and its kit was nautical -- boat, buoy,
// lifering, net, oar, crab, starfish. That is a harbour beach. Region 0 IS the
// Fold: its accent is Fold teal below, and world-bible §2 calls it "a gothic
// town built in the silt around a massive obelisk" at the bottom of a lightless
// sea. The name and the kit are now canon (tools/art/env_fold.py). The other
// four still carry retired names and are M4's problem.
const REGION_BIOMES = ["fold", "saltmines", "pit", "attic", "hall"];
// Per-region accent -- mirrors paint_ground's ACCENTS. Used by the region grade
// wash and the v14.2 per-region ambient particles.
//   Fold teal, Shelf green, Breach pale sand, Scar rust, Keep lamplight.
//
// THE FIFTH ONE WAS VIOLET, AND VIOLET MEANT NOTHING. It was `0x7a4eb4` and the
// comment called region 4 "the Stage" -- a name from the retired cosmology. Under
// world-bible §6.5 that region is THE KEEP: a drowned concert hall with a room
// built on the stage where the orchestra sat. "Warm, lit, stocked, comfortable.
// Padded bars, and no door on the inside."
//
// So the last region the player reaches is the WARMEST place in the game, and
// that is the point -- it has to look like the one safe room in a lightless sea,
// or Lunal's offer is not tempting and the ending is not a choice. The accent is
// BRASS (tools/art/palette.py), the same value the prayer-lamps and Mir's own
// tool are lit in. The trap is lit like everything the player has learned to
// trust. Nothing here is a new hue: it is the game's one warm accent, spent last.
const REGION_ACCENTS = [0x49c6bd, 0x58c07a, 0xe8d9a8, 0xc25424, 0xc6984e];

/**
 * Walkable pixel-art overworld (tilemap + tile-snapped movement + camera
 * follow), replacing the old text-menu MapScene as the between-battles hub.
 * Walking onto an unlocked campaign-node marker starts that node's battle;
 * the battle/results flow itself is unchanged. Movement is manual
 * tile-tweening, deliberately not Arcade/Matter physics -- nothing here
 * needs velocity, gravity, or swept collision, only "is the next tile
 * legal", which is pure grid math (OverworldMovement.ts).
 */
export class OverworldScene extends Phaser.Scene {
  private player!: Phaser.GameObjects.Sprite;
  private playerShadow!: Phaser.GameObjects.Ellipse;
  private playerGlow!: Phaser.GameObjects.Image;
  private playerPos: GridPosition = { col: 0, row: 0 };
  /** Nari (v12.0): follows Mir from the Fold until the loss beat on the
   * surface. Decorative -- never blocks tiles or triggers anything. */
  private nari: Phaser.GameObjects.Sprite | null = null;
  private nariShadow: Phaser.GameObjects.Ellipse | null = null;
  /** The exploration HUD, hidden for the duration of a fight. */
  private exploreHud: Phaser.GameObjects.GameObject[] = [];
  private controlHint: Phaser.GameObjects.Text | null = null;
  private moving = false;
  private walkable: boolean[][] = [];
  /** Region territory per tile, decoded from the ground layer's gids
   * (v13.0: regions are organic territories, not 26-column strips). */
  private regions: number[][] = [];
  private markers: Marker[] = [];
  private echoes: Echo[] = [];
  private echoGlows = new Map<string, Phaser.GameObjects.Image>();
  private echoFoundIds = new Set<string>();
  private echoCountText!: Phaser.GameObjects.Text;
  private echoPanel: Phaser.GameObjects.Container | null = null;
  private nearbyEcho: Echo | null = null;
  // Talkable NPCs (dialogue.ts) + the dialogue panel state.
  private npcs: PlacedNpc[] = [];
  private nearbyNpc: PlacedNpc | null = null;
  private dialoguePanel: Phaser.GameObjects.Container | null = null;
  private dialogueLines: string[] = [];
  private dialogueIdx = 0;
  private dialogueSets: string | null = null;
  private dialogueName = "";
  private obelisks: { col: number; row: number; glow: Phaser.GameObjects.Image }[] = [];
  private nearbyObelisk: { col: number; row: number; glow: Phaser.GameObjects.Image } | null = null;
  /** The Fold's town-obelisk tile (v14.0), read from the "town_obelisk" marker. */
  private townObeliskTile: GridPosition | null = null;
  /** v15.0 chunked painted ground; only the chunks in view are rendered. */
  private groundChunks: { img: Phaser.GameObjects.Image; w: number; h: number }[] = [];
  /** Live refs for the dynamic-ambience pass (v14.2): beat-reactive sanctuary,
   * current surge, distant lightning. All motion is cosmetic. */
  private worshippers: { body: Phaser.GameObjects.Graphics; lean: number }[] = [];
  private townCrownGlow: Phaser.GameObjects.Image | null = null;
  private eelgrass: { blade: Phaser.GameObjects.Rectangle; phase: number }[] = [];
  private overworldSongMap: SongMap | null = null;
  /** Cosmetic beat accumulator for the sanctuary pulse (visual only; never gameplay judgment). */
  private beatAccumMs = 0;
  /** Current-surge accumulator: a swell rolls the drowned flora every ~20s. */
  private surgeAccumMs = 0;
  private lightningFlash: Phaser.GameObjects.Image | null = null;
  private lightningAccumMs = 0;
  /** Every dynamic-ambience object, so the whole layer can be hidden + its
   * tweens paused while an in-world fight runs (the camera locks to the fight
   * room, so ambient is off-screen; keeping it animating just burns the frame
   * budget and, on weak hardware, drops fight-timing FPS / peaks memory). */
  private ambient: Phaser.GameObjects.GameObject[] = [];
  private ambientHidden = false;
  /** Live in-world fight (areas-not-arenas); null while exploring. */
  private fight: WorldFight | null = null;
  /** Canopy landforms drawn ABOVE the player (PRD v7.15); they alpha-fade
   * when the player walks beneath so the map keeps its sense of height. */
  private canopies: Phaser.GameObjects.Image[] = [];
  /** Screen-space UI pinned to the camera's visible rect. Under the 2x
   * retina zoom (RENDER_SCALE) with a scrolled follow camera, Phaser's
   * scrollFactor-0 transform drifts, so UI is pinned to worldView per frame
   * instead -- deterministic under any zoom. */
  private pinned: { obj: Phaser.GameObjects.GameObject & { setPosition(x: number, y: number): unknown; active: boolean }; dx: number; dy: number }[] = [];
  /** The standing foe's visuals per node, hidden when its fight goes live. */
  private nodeFoeVisuals = new Map<string, Phaser.GameObjects.GameObject[]>();
  private interactHint!: Phaser.GameObjects.Text;
  private cursors!: Phaser.Types.Input.Keyboard.CursorKeys;
  private wasd!: Record<"W" | "A" | "S" | "D", Phaser.Input.Keyboard.Key>;
  private interactKey!: Phaser.Input.Keyboard.Key;
  private fog: Phaser.GameObjects.TileSprite | null = null;
  /** Full-screen whisper of the local region's accent colour (updated per
   * frame from the camera's position) -- each region OWNS its light. */
  private regionGrade: Phaser.GameObjects.Rectangle | null = null;

  constructor() {
    super("OverworldScene");
  }

  preload(): void {
    // First scene-local preload in the codebase (BootScene only preloads
    // the shared hero portrait); guarded so a scene restart doesn't try to
    // re-register live cache keys.
    if (!this.textures.exists("overworld_tiles")) this.load.image("overworld_tiles", tilesetUrl);
    if (!this.cache.tilemap.exists("overworld")) this.load.tilemapTiledJSON("overworld", tilemapUrl);
    // Mir and the old-hero NPC sprites are loaded centrally in
    // BootScene (band_* keys); nothing hero-related to preload here.
    if (!this.textures.exists("ow_props")) this.load.spritesheet("ow_props", propsUrl, { frameWidth: 24, frameHeight: 32 });
  }

  create(): void {
    const profile = GameContext.activeProfile;
    if (!profile) {
      // Not a transition: there is no save, so there is nothing to fade FROM.
      this.scene.start("SaveScene");
      return;
    }
    sceneEnter(this, { zoom: false });

    this.moving = false;
    this.obelisks = [];
    this.fight = null;
    this.canopies = [];
    this.pinned = [];
    // v14.2 dynamic-ambience state: MUST be reset here, not just at field-init,
    // because Phaser reuses the scene instance across restarts (a fight victory
    // / the finale restart the overworld) and re-runs create() -- without this
    // the ambient arrays keep references to destroyed objects and accumulate.
    this.ambient = [];
    this.groundChunks = [];
    this.eelgrass = [];
    this.worshippers = [];
    this.townCrownGlow = null;
    this.lightningFlash = null;
    this.ambientHidden = false;
    this.beatAccumMs = 0;
    this.surgeAccumMs = 0;
    this.lightningAccumMs = 0;
    this.overworldSongMap = null;
    this.nodeFoeVisuals.clear();
    this.npcs = [];
    this.nearbyNpc = null;
    this.dialoguePanel = null;
    this.events.once(Phaser.Scenes.Events.SHUTDOWN, () => {
      this.fight?.destroy();
      this.fight = null;
    });
    music.setVolume(profile.settings.volumeMusic);
    music.setMode("explore");
    music.start();

    const map = this.make.tilemap({ key: "overworld" });
    const tileset = map.addTilesetImage("overworld_tileset", "overworld_tiles")!;
    const ground = map.createLayer("ground", tileset, 0, 0)!;
    // Design-audit-2 G1-G4: the ground is PAINTED, not stamped. The tile
    // layer stays authoritative for collision/terrain queries but its render
    // is replaced by the offline-painted plate (tools/overworld/paint_ground.py,
    // 2x texel density; rock as mesas, roads as ribbons, water as bodies) so
    // the ground lives in the same register as the AI-painted sprites.
    ground.setVisible(false);
    this.placeGroundChunks();

    this.walkable = [];
    this.regions = [];
    for (let row = 0; row < map.height; row++) {
      const rowFlags: boolean[] = [];
      const rowRegions: number[] = [];
      for (let col = 0; col < map.width; col++) {
        const tile = ground.getTileAt(col, row);
        const props = tile ? (tileset.getTileProperties(tile.index) as { collides?: boolean } | null) : null;
        rowFlags.push(!props?.collides);
        rowRegions.push(tile ? Math.min(4, Math.max(0, Math.floor((tile.index - 1) / 4))) : 0);
      }
      this.walkable.push(rowFlags);
      this.regions.push(rowRegions);
    }

    // Marker names in the tilemap ARE campaign node ids, plus two named
    // non-combat markers: "spawn" (Mir's start) and "town_obelisk" (the Fold's
    // monolith, v14.0) -- both filtered out of the fightable node markers.
    const objects = map.getObjectLayer("markers")!.objects;
    const spawnObject = objects.find((o) => o.name === "spawn")!;
    const townObeliskObject = objects.find((o) => o.name === "town_obelisk");
    this.markers = objects
      .filter((o) => o.name !== "spawn" && o.name !== "town_obelisk")
      .map((o) => ({ nodeId: o.name, col: Math.floor(o.x! / TILE_SIZE), row: Math.floor(o.y! / TILE_SIZE) }));
    const spawnTile = { col: Math.floor(spawnObject.x! / TILE_SIZE), row: Math.floor(spawnObject.y! / TILE_SIZE) };
    this.townObeliskTile = townObeliskObject
      ? { col: Math.floor(townObeliskObject.x! / TILE_SIZE), row: Math.floor(townObeliskObject.y! / TILE_SIZE) }
      : null;

    // Discoverable lore fragments scattered off the critical path (PRD
    // §8.8.2). Title/text/region are authored once, in the map data itself
    // (tools/overworld/generate_overworld_map.py), so the world and its
    // found-text can never drift apart.
    this.echoFoundIds = new Set(profile.echoesFound);
    this.echoes = (map.getObjectLayer("echoes")?.objects ?? []).map((o) => {
      const props = (o.properties as { name: string; value: string }[]) ?? [];
      const get = (name: string) => props.find((p) => p.name === name)?.value ?? "";
      return {
        id: o.name,
        title: get("title"),
        text: get("text"),
        col: Math.floor(o.x! / TILE_SIZE),
        row: Math.floor(o.y! / TILE_SIZE),
      };
    });

    this.decorate(map, ground, spawnTile);
    this.softenSeamsAndDapple(map);
    // each fight node's authored venue -- its biome floor blended into the
    // map + its kitbash set pieces -- stands IN the world, under the foe
    for (const marker of this.markers) {
      const venueBiome = REGION_BIOMES[this.regions[marker.row]?.[marker.col] ?? 0];
      composeWorldVenue(
        this,
        `arena_${venueBiome}`,
        marker.col * TILE_SIZE + TILE_SIZE / 2,
        marker.row * TILE_SIZE + TILE_SIZE / 2,
        // scale/placement audit: venue set pieces must stand on land (grass
        // or path) -- offsets that land in water/rock skip the piece. The
        // baked fight-ground clearing (paint_ground.py) counts as land even
        // where the tiles beneath are water (the boss ring bridges the lake).
        (x, y) => {
          const discR = marker.nodeId === "boss_1" ? 108 : 58; // matches paint_ground radii
          const ddx = x - marker.col * TILE_SIZE - TILE_SIZE / 2;
          const ddy = y - marker.row * TILE_SIZE - TILE_SIZE / 2;
          if (ddx * ddx + ddy * ddy < discR * discR) return true;
          const gid = ground.getTileAt(Math.floor(x / TILE_SIZE), Math.floor(y / TILE_SIZE))?.index;
          if (gid == null || gid <= 0) return false;
          const local = (gid - 1) % 4; // 0 grass 1 path 2 water 3 rock
          return local === 0 || local === 1;
        }
      );
    }
    for (const marker of this.markers) this.drawMarker(profile, marker);
    for (const echo of this.echoes) this.drawEcho(echo);
    // The Fold's massive obelisk and its ring of worshippers -- the drowned
    // town at prayer (v14.0). Doubles as the town's save point.
    this.placeTownObelisk();

    // The player on the map is Mir, the guitarist (tools/pixelart/newband.py
    // generation, conformed by bake_cast.py). His sheets are side-facing
    // only, so one run cycle serves every direction (flipped for left); the
    // idle is his breathing stand. Frame counts are read off the loaded
    // textures so re-authoring the sheets can't desync the ranges.
    const lastFrame = (key: string) => this.textures.get(key).frameTotal - 2; // -1 for __BASE
    if (!this.anims.exists("leader_walk")) {
      this.anims.create({
        key: "leader_walk",
        frames: this.anims.generateFrameNumbers("band_mir_run", { start: 0, end: lastFrame("band_mir_run") }),
        frameRate: 12,
        repeat: -1,
      });
    }
    if (!this.anims.exists("leader_idle")) {
      this.anims.create({
        key: "leader_idle",
        frames: this.anims.generateFrameNumbers("band_mir", { start: 0, end: lastFrame("band_mir") }),
        frameRate: 5,
        repeat: -1,
      });
    }

    // Return to the node just fought rather than the fixed spawn point --
    // nodes sit along the road, so respawning at the start after every
    // battle would force pointless backtracking. Read-once, like the other
    // GameContext handoff fields.
    const returnMarker = this.markers.find((m) => m.nodeId === GameContext.returnToNodeId);
    GameContext.returnToNodeId = null;
    this.playerPos = returnMarker
      ? { col: returnMarker.col, row: returnMarker.row }
      : { col: Math.floor(spawnObject.x! / TILE_SIZE), row: Math.floor(spawnObject.y! / TILE_SIZE) };

    // Contact shadow grounds Mir like the props/foes around him, and a soft
    // teal under-glow lifts him a value step above the
    // scenery (AAA audit O4) so the eye finds him in the dark world.
    this.playerShadow = this.add.ellipse(0, 0, 13, 4, 0x05060a, 0.4).setDepth(4.4);
    this.playerGlow = this.add
      .image(0, 0, "glow")
      .setBlendMode(Phaser.BlendModes.ADD)
      .setTint(0x49c6bd)
      .setScale(0.32)
      .setAlpha(0.2)
      .setDepth(4.35);
    this.player = this.add.sprite(0, 0, "band_mir", 0);
    // Mir's frames are 48x48 with the figure ~37px tall; scaled to ~0.52 he
    // stands ~1.2 tiles against the 16px tiles (feet-anchored so he sits on
    // the tile centre). Idle breathes until the player moves.
    this.player.setOrigin(0.5, 0.9).setScale(0.125); // 200px HD frames (hd_cast.py): 25px world, 4x canvas density
    this.player.setDepth(5);
    this.player.play("leader_idle");
    this.snapPlayerToGrid();

    // Nari follows (v12.0) -- until he is lost on the surface (§8.4).
    this.nari = null;
    this.nariShadow = null;
    if (!profile.nariLostAt && this.textures.exists("band_nari")) {
      if (!this.anims.exists("nari_idle")) {
        this.anims.create({ key: "nari_idle", frames: this.anims.generateFrameNumbers("band_nari", { start: 0, end: lastFrame("band_nari") }), frameRate: 4, repeat: -1 });
        this.anims.create({ key: "nari_walk", frames: this.anims.generateFrameNumbers("band_nari_run", { start: 0, end: lastFrame("band_nari_run") }), frameRate: 9, repeat: -1 });
      }
      this.nariShadow = this.add.ellipse(0, 0, 8, 3, 0x05060a, 0.35).setDepth(4.3);
      this.nari = this.add.sprite(0, 0, "band_nari", 0).setOrigin(0.5, 0.9).setScale(0.125).setDepth(4.55);
      this.nari.play("nari_idle");
      // Beside and half a step behind -- NOT on his father's own tile, which
      // is where he used to spawn, invisible inside Mir's sprite for the whole
      // first walk. He is the emotional load of act one; he has to be on
      // screen from the first frame.
      this.nari.setPosition(
        this.playerPos.col * TILE_SIZE + TILE_SIZE / 2 - 7,
        this.playerPos.row * TILE_SIZE + TILE_SIZE / 2 + 3
      );
      this.nariShadow.setPosition(this.nari.x, this.nari.y + 1);
    }

    // Retina render (design-audit-3): the canvas is 2x; zooming the camera
    // keeps every world coordinate identical while art renders at its real
    // texel density (the follow camera centers, so no centerOn needed).
    this.cameras.main.setZoom(RENDER_SCALE);
    this.cameras.main.setBounds(0, 0, map.widthInPixels, map.heightInPixels);
    // roundPixels was TRUE: on a 4x-zoomed camera it snaps the scroll to whole
    // world-pixels every frame, so following the smoothly-tweening player made
    // the whole screen JITTER. Off = smooth. A gentle lerp softens the grid.
    this.cameras.main.startFollow(this.player, false, 0.55, 0.55);
    this.cameras.main.roundPixels = false;

    const keyboard = this.input.keyboard!;
    this.cursors = keyboard.createCursorKeys();
    this.wasd = keyboard.addKeys("W,A,S,D") as OverworldScene["wasd"];
    this.interactKey = keyboard.addKey("E");
    keyboard.on("keydown-ESC", () => this.scene.launch("SettingsOverlay", { returnTo: "OverworldScene" }));

    this.addAtmosphere();

    // The HUD used to be a full-width black strip carrying
    // "Arrows/WASD: move   E: interact   ESC: settings" -- readable, and the
    // first thing in every single frame of the game. A control list pinned over
    // the art forever is a debug overlay: it says "unfinished" louder than any
    // missing asset. So the strip is gone, both labels carry their own dark
    // stroke instead (the same trick `interactHint` below already used), and the
    // key hint TEACHES ONCE -- `retireControlHint` fades it out on Mir's first
    // step, because a player who has moved has learned how to move.
    //
    // Still tracked as a group so a fight can hide it: these verbs are wrong the
    // instant combat starts (see WorldFightHost.setExploreHudVisible).
    this.controlHint = this.pinToScreen(
      this.add
        .text(4, 4, "ARROWS / WASD  ·  E  INTERACT  ·  ESC  SETTINGS", {
          fontFamily: "monospace",
          fontSize: "7px",
          color: "#9fb0ad",
          stroke: "#05060a",
          strokeThickness: 3,
        })
        .setDepth(20),
      4,
      4
    );
    this.exploreHud = [this.controlHint];
    this.echoCountText = this.pinToScreen(
      this.add
        .text(BASE_WIDTH - 4, 4, "", {
          fontFamily: "monospace",
          fontSize: "7px",
          color: "#49c6bd",
          stroke: "#05060a",
          strokeThickness: 3,
        })
        .setOrigin(1, 0)
        .setDepth(20),
      BASE_WIDTH - 4,
      4
    );
    if (this.echoCountText) this.exploreHud.push(this.echoCountText);
    this.updateEchoCountText();

    // A quiet prompt near the player, shown only when an undiscovered echo is close.
    this.interactHint = this.add
      .text(0, 0, "E: read", { fontFamily: "monospace", fontSize: "7px", color: "#f4d27a", stroke: "#05060a", strokeThickness: 3 })
      .setOrigin(0.5, 1)
      .setDepth(21)
      .setVisible(false);

    // The opening cutscene -- the Rite (the obelisk opens, the litho speaks the
    // rule that condemns Nari). Self-gates on the "seen_rite" flag so it plays
    // once, at the start of a new game. Deferred a tick so create() settles
    // before the scene pauses under the overlay.
    this.time.delayedCall(20, () => CutsceneScene.play(this, "rite_opening"));
  }

  private updateEchoCountText(): void {
    this.echoCountText.setText(`Echoes ${this.echoFoundIds.size}/${this.echoes.length}`);
  }

  /**
   * A screen-space vignette (darkened edges) plus a faint cold overcast --
   * cheap, camera-locked, and the single biggest "this feels like a mood,
   * not a tech demo" win. Skipped under photosensitivity-safe mode.
   */
  private addAtmosphere(): void {
    const reduced = Boolean(GameContext.activeProfile?.settings.reducedMotion);
    const safe = Boolean(GameContext.activeProfile?.settings.photosensitivitySafeMode);
    const width = BASE_WIDTH;
    const height = BASE_HEIGHT;

    if (!safe) {
      // Drifting fog: a seamless haze tile scrolled slowly over the world for
      // depth. Screen-locked and additive at low alpha so it reads as light
      // haze, never a grey wash. Held still (just present) under reduced motion.
      this.fog = this.pinToScreen(
        this.add.tileSprite(0, 0, width, height, "fx_haze").setOrigin(0, 0),
        0,
        0
      )
        .setDepth(13)
        .setBlendMode(Phaser.BlendModes.SCREEN)
        .setAlpha(reduced ? 0.05 : 0.1);

      // Raking god-ray shafts across the top -- additive, faint, evocative of
      // light falling through a drowned sky. Skipped under reduced motion.
      if (!reduced) {
        const rays = this.pinToScreen(this.add.image(width / 2, 0, "fx_godray").setOrigin(0.5, 0), width / 2, 0)
          .setDepth(14)
          .setBlendMode(Phaser.BlendModes.ADD)
          .setTint(0x9fe8e0)
          .setAlpha(0.3)
          .setDisplaySize(width * 1.2, height);
        this.tweens.add({ targets: rays, alpha: 0.46, duration: 4200, yoyo: true, repeat: -1, ease: "Sine.inOut" });

        // A second, DIAGONAL shaft slicing the whole scene (the HLD shot's
        // signature move): rotated, wider than the screen, slow sway.
        const slice = this.pinToScreen(this.add.image(width * 0.68, height * 0.4, "fx_godray"), width * 0.68, height * 0.4)
          .setDepth(14)
          .setBlendMode(Phaser.BlendModes.ADD)
          .setTint(0xc8f0dc)
          .setAlpha(0.16)
          .setRotation(0.42)
          .setDisplaySize(width * 0.9, height * 2.2);
        this.tweens.add({ targets: slice, alpha: 0.26, rotation: 0.36, duration: 6400, yoyo: true, repeat: -1, ease: "Sine.inOut" });

        // Ambient light motes (the HLD comparison: their air is ALIVE) --
        // a dozen tiny additive specks drifting up-screen, screen-pinned so
        // they read wherever the camera is. Deterministic layout.
        for (let i = 0; i < 12; i++) {
          const mx = ((i * 73 + 29) % 100) / 100 * width;
          const my = ((i * 41 + 13) % 100) / 100 * height;
          const mote = this.pinToScreen(
            this.add.image(mx, my, "glow").setScale(0.05 + (i % 3) * 0.02),
            mx,
            my
          )
            .setDepth(13.5)
            .setBlendMode(Phaser.BlendModes.ADD)
            .setTint(i % 4 === 0 ? 0xf0c078 : 0x9fe8e0)
            .setAlpha(0);
          this.tweens.add({
            targets: mote,
            alpha: { from: 0, to: 0.35 + (i % 3) * 0.1 },
            duration: 1600 + i * 230,
            yoyo: true,
            repeat: -1,
            delay: i * 420,
            ease: "Sine.inOut",
          });
        }
      }
    }

    // (A foreground corner-foliage layer was tried here -- HLD's depth
    // trick -- but every canopy asset reads as an occluding sheet at frame
    // scale, not a fringe. The depth layering is carried by the canopy
    // overhangs in-world, the diagonal shaft, and the motes instead.)

    // per-region ambient grade: a low-alpha additive wash of the local
    // accent, tint updated as the camera crosses regions
    this.regionGrade = this.pinToScreen(
      this.add.rectangle(0, 0, width, height, 0xffffff, 0.05).setOrigin(0, 0),
      0,
      0
    )
      .setBlendMode(Phaser.BlendModes.ADD)
      .setDepth(12.5) as Phaser.GameObjects.Rectangle;

    const g = this.pinToScreen(this.add.graphics().setDepth(15), 0, 0);
    // cold overcast tint
    g.fillStyle(0x0b1420, 0.06).fillRect(0, 0, width, height);
    // vignette: nested translucent frames, darker toward the edge
    const steps = 10;
    for (let i = 0; i < steps; i++) {
      const t = i / steps;
      g.fillStyle(0x05060a, 0.06);
      const inset = Math.round((t * Math.min(width, height)) / 4.6);
      g.fillRect(0, 0, width, inset); // top
      g.fillRect(0, height - inset, width, inset); // bottom
      g.fillRect(0, 0, inset, height); // left
      g.fillRect(width - inset, 0, inset, height); // right
    }
  }

  update(_time: number, deltaMs: number): void {
    if (!this.player) return;
    this.repositionPinned();
    this.cullGroundChunks();
    // Ambience runs only while exploring: during an in-world fight it is
    // off-screen (camera locked to the fight room), so hide + pause it so the
    // fight owns the whole frame budget (fixes CI fight-timing on weak GPUs).
    if (this.fight) {
      this.setAmbientHidden(true);
    } else {
      this.setAmbientHidden(false);
      this.driveAmbience(deltaMs);
    }
    if (this.regionGrade) {
      const tc = Math.floor(this.cameras.main.midPoint.x / TILE_SIZE);
      const tr = Math.floor(this.cameras.main.midPoint.y / TILE_SIZE);
      const ri = this.regions[tr]?.[tc] ?? 0;
      this.regionGrade.fillColor = REGION_ACCENTS[ri];
    }
    this.playerShadow.setPosition(this.player.x, this.player.y + 2);
    this.playerGlow.setPosition(this.player.x, this.player.y - 6);
    // Canopy overhangs go translucent while the player is beneath them (the
    // fade is legibility, not decoration -- kept under reduced motion). The
    // trigger zone is the sprite's real footprint, not a fixed radius.
    for (const c of this.canopies) {
      const d = Phaser.Math.Distance.Between(this.player.x, this.player.y, c.x, c.y - c.displayHeight * 0.5);
      const target = d < Math.max(42, c.displayWidth * 0.65) ? 0.35 : 1;
      c.alpha += (target - c.alpha) * Math.min(1, deltaMs / 120);
    }
    if (this.fight) {
      // a fight is live IN the world: the sim drives the player; tile
      // movement and interactions pause until it resolves
      if (!this.fight.update(deltaMs)) this.fight = null;
      return;
    }
    if (this.nari) {
      this.nariShadow?.setPosition(this.nari.x, this.nari.y + 1);
      if (!this.tweens.isTweening(this.nari) && this.nari.anims.getName() !== "nari_idle") this.nari.play("nari_idle");
    }
    if (this.fog && !GameContext.activeProfile?.settings.reducedMotion) {
      this.fog.tilePositionX += 0.08;
      this.fog.tilePositionY -= 0.03;
    }
    this.updateNearbyEcho();
    this.updateNearbyNpc();
    if (Phaser.Input.Keyboard.JustDown(this.interactKey) && !this.echoPanel) {
      if (this.dialoguePanel) this.advanceDialogue();
      else if (this.nearbyNpc) this.openDialogue(this.nearbyNpc);
      else if (this.nearbyEcho) this.discoverEcho(this.nearbyEcho);
      else if (this.nearbyObelisk) this.restAtObelisk(this.nearbyObelisk);
    }
    if (this.dialoguePanel) return; // frozen while talking
    if (this.moving) return;
    const dir = this.heldDirection();
    if (dir) this.tryStep(dir);
    else if (this.player.anims.getName() !== "leader_idle") {
      this.player.play("leader_idle"); // drop back to the breathing stand
    }
  }

  /** Finds the closest interactable within one tile of the player (an
   * undiscovered echo, else a save-obelisk) and points the "E:" prompt at it. */
  private updateNearbyEcho(): void {
    this.nearbyEcho =
      this.echoes.find(
        (e) => !this.echoFoundIds.has(e.id) && Math.abs(e.col - this.playerPos.col) <= 1 && Math.abs(e.row - this.playerPos.row) <= 1
      ) ?? null;
    this.nearbyObelisk =
      this.obelisks.find((o) => Math.abs(o.col - this.playerPos.col) <= 1 && Math.abs(o.row - this.playerPos.row) <= 1) ?? null;
    if (this.nearbyEcho) {
      this.interactHint
        .setText("E: read")
        .setPosition(this.nearbyEcho.col * TILE_SIZE + TILE_SIZE / 2, this.nearbyEcho.row * TILE_SIZE - 4)
        .setVisible(true);
    } else if (this.nearbyObelisk) {
      this.interactHint
        .setText("E: pray")
        .setPosition(this.nearbyObelisk.col * TILE_SIZE + TILE_SIZE / 2, this.nearbyObelisk.row * TILE_SIZE - 8)
        .setVisible(true);
    } else {
      this.interactHint.setVisible(false);
    }
  }

  /**
   * Marks an echo found, persists it to the save (so it stays found across
   * sessions -- PRD §8.8.2), and shows its one-line fragment in a framed
   * panel until the player dismisses it or walks away.
   */
  private discoverEcho(echo: Echo): void {
    const profile = GameContext.activeProfile;
    if (!profile) return;
    if (!this.echoFoundIds.has(echo.id)) {
      this.echoFoundIds.add(echo.id);
      profile.echoesFound.push(echo.id);
      void GameContext.persistActiveProfile();
      GameContext.analytics.track("echo_found", { echoId: echo.id });
      if (this.echoCountText) this.exploreHud.push(this.echoCountText);
    this.updateEchoCountText();
      const glow = this.echoGlows.get(echo.id);
      if (glow) {
        this.tweens.killTweensOf(glow);
        glow.setScale(0.3).setAlpha(0.12);
      }
    }
    this.showEchoPanel(echo);
  }

  private showEchoPanel(echo: Echo): void {
    this.echoPanel?.destroy();
    const panelW = Math.min(BASE_WIDTH - 24, 220);
    const panel = this.add.nineslice(0, 0, "ui_panel", undefined, panelW, 40, 5, 5, 5, 5);
    const title = this.add
      .text(0, -12, echo.title.toUpperCase(), { fontFamily: "monospace", fontSize: "7px", color: "#f4d27a" })
      .setOrigin(0.5, 0.5);
    const body = this.add
      .text(0, 2, echo.text, { fontFamily: "monospace", fontSize: "7px", color: "#e8e2d4", align: "center", wordWrap: { width: panelW - 16 } })
      .setOrigin(0.5, 0);
    this.echoPanel = this.pinToScreen(
      this.add.container(BASE_WIDTH / 2, BASE_HEIGHT - 30, [panel, title, body]).setDepth(25),
      BASE_WIDTH / 2,
      BASE_HEIGHT - 30
    );
    this.repositionPinned();
    this.time.delayedCall(3800, () => this.dismissEchoPanel());
  }

  private dismissEchoPanel(): void {
    this.echoPanel?.destroy();
    this.echoPanel = null;
  }

  // --- talkable NPCs + dialogue (content/dialogue.ts) ----------------------
  /** Place each authored NPC on the nearest walkable tile, drawn as a small
   *  procedural figure with a name label shown only when the player is near. */
  private placeNpcs(map: Phaser.Tilemaps.Tilemap, ground: Phaser.Tilemaps.TilemapLayer): void {
    const walkable = (c: number, r: number) => {
      const k = ((ground.getTileAt(c, r)?.index ?? 0) - 1) % 4;
      return k === 0 || k === 1; // grass or path
    };
    for (const def of NPCS) {
      const snapped = this.nearestWalkable(def.col, def.row, walkable, map);
      if (!snapped) continue;
      const [col, row] = snapped;
      const x = col * TILE_SIZE + TILE_SIZE / 2;
      const y = row * TILE_SIZE + TILE_SIZE - 2;
      const fig = this.drawNpc(x, y, def.look);
      const label = this.add
        .text(x, y - 20, def.name, { fontFamily: "monospace", fontSize: "6px", color: "#d8ceb6", stroke: "#05060a", strokeThickness: 3 })
        .setOrigin(0.5, 1)
        .setDepth(21)
        .setVisible(false);
      this.npcs.push({ def, col, row, fig, label });
    }
  }

  /** Nearest grass/path tile to (c0,r0) within a small radius, or null. */
  private nearestWalkable(
    c0: number,
    r0: number,
    walkable: (c: number, r: number) => boolean,
    map: Phaser.Tilemaps.Tilemap
  ): [number, number] | null {
    for (let rad = 0; rad <= 6; rad++) {
      for (let dr = -rad; dr <= rad; dr++) {
        for (let dc = -rad; dc <= rad; dc++) {
          if (Math.max(Math.abs(dr), Math.abs(dc)) !== rad) continue;
          const c = c0 + dc;
          const r = r0 + dr;
          if (c < 1 || r < 1 || c >= map.width - 1 || r >= map.height - 1) continue;
          if (walkable(c, r)) return [c, r];
        }
      }
    }
    return null;
  }

  /**
   * A little drawn person, built from a role spec: contact shadow, staff,
   * a far arm, legs-or-robe, a tapered torso with a cool rim-light, a near
   * arm, neck, and a head with hair (or a full hood, face in shadow), a
   * shaded cheek and eyes. Elders stoop over a staff; children are small
   * with legs; the hooded stranger has no face. Idle bob unless reduced
   * motion. Deliberately NOT two stacked ellipses.
   */
  private drawNpc(x: number, y: number, look: NpcLook): Phaser.GameObjects.Container {
    const S = FIGURE_SPECS[look];
    const lean = S.stoop;
    const g = this.add.graphics();

    // soft contact shadow (narrow -- they take up little room)
    g.fillStyle(0x05060a, 0.3).fillEllipse(0, 2.5, 10, 3.2);

    // walking staff, planted just ahead of the figure (drawn behind the body)
    if (S.staff) {
      g.lineStyle(1.4, 0x3a2b1c, 1);
      g.beginPath();
      g.moveTo(4.4, 2.5);
      g.lineTo(3.6, -18);
      g.strokePath();
      g.fillStyle(0x574632, 1).fillCircle(3.5, -18.4, 1.6);
    }

    // far arm, shadowed, tucked along the back side -- thin and bony
    g.fillStyle(S.robeDark, 1);
    g.fillRoundedRect(lean - 4.4, -11.2, 1.8, 7.6, 0.9);

    // lower body: legs + short tunic, or a floor-length robe
    if (S.legs) {
      g.fillStyle(S.robeDark, 1);
      g.fillRoundedRect(-2.5, -6.4, 2.0, 6.8, 0.9); // back leg
      g.fillStyle(S.robe, 1);
      g.fillRoundedRect(0.5, -6.4, 2.0, 6.8, 0.9); // front leg
      g.fillStyle(0x141110, 1); // shoes
      g.fillEllipse(-1.4, 0.7, 3.2, 1.8);
      g.fillEllipse(1.7, 0.7, 3.2, 1.8);
    } else {
      g.fillStyle(S.robe, 1); // robe hanging off a thin frame
      g.fillPoints(
        [
          new Phaser.Geom.Point(-3.7, -12),
          new Phaser.Geom.Point(3.7, -12),
          new Phaser.Geom.Point(2.5, -7),
          new Phaser.Geom.Point(5.2, 1.2),
          new Phaser.Geom.Point(-5.2, 1.2),
          new Phaser.Geom.Point(-2.5, -7),
        ],
        true
      );
      g.fillStyle(S.robeDark, 0.5); // fold shadows down the hanging cloth
      g.fillTriangle(0.5, -7, 2.1, 1.2, -1.0, 1.2);
      g.fillRect(lean - 2.6, -6.5, 0.7, 7); // a slack side fold
      g.fillStyle(S.robeLit, 0.35);
      g.fillRect(-1.3, -6, 0.6, 6.4); // a thread of light on a raised fold
    }

    // torso, narrow and hollow, tipped forward by the lean
    const tx = lean * 0.3;
    g.fillStyle(S.robe, 1);
    g.fillPoints(
      [
        new Phaser.Geom.Point(-3.4 + tx, -12),
        new Phaser.Geom.Point(3.4 + tx, -12),
        new Phaser.Geom.Point(2.1, -6.4),
        new Phaser.Geom.Point(-2.1, -6.4),
      ],
      true
    );
    g.fillStyle(S.robeLit, 0.9); // cool rim-light down the front-left edge
    g.fillPoints(
      [
        new Phaser.Geom.Point(-3.4 + tx, -12),
        new Phaser.Geom.Point(-1.7 + tx, -12),
        new Phaser.Geom.Point(-1.1, -6.4),
        new Phaser.Geom.Point(-2.1, -6.4),
      ],
      true
    );
    g.fillStyle(S.robeDark, 0.4); // a hollow-chest shadow down the sternum
    g.fillRect(tx - 0.4, -11, 0.8, 4.4);

    // narrow, bony shoulders
    g.fillStyle(S.robeLit, 1);
    g.fillEllipse(tx, -12, S.shoulder, 2.9);
    g.fillStyle(S.robeDark, 0.45); // hollow above the collarbone
    g.fillEllipse(tx, -10.6, S.shoulder * 0.68, 1.3);

    // near arm, across the front -- thin, ending in a bony hand
    const ax = 2.2 + lean * 0.4;
    g.fillStyle(S.robe, 1);
    g.fillRoundedRect(ax, -11.2, 1.9, 6.9, 0.9);
    g.fillStyle(S.robeLit, 0.4);
    g.fillRoundedRect(ax, -11.2, 0.9, 6.9, 0.9);
    g.fillStyle(S.skinShade, 1); // the hand
    g.fillEllipse(ax + 0.95, -3.9, 1.9, 1.7);

    // a long, thin neck (gaunt) with a hollow at the throat
    g.fillStyle(S.skin, 1);
    g.fillRect(lean - 0.9, -15.2, 1.8, 3.4);
    g.fillStyle(S.skinShade, 1);
    g.fillEllipse(lean, -12.1, 2.2, 1.2);

    // head (skin) -- narrower skull, sunken far cheek + temple hollow
    const hx = lean;
    const hy = -16.6;
    g.fillStyle(S.skin, 1);
    g.fillCircle(hx, hy, 2.7);
    g.fillStyle(S.skinShade, 1);
    g.fillEllipse(hx + 1.1, hy + 0.4, 2.1, 4.6); // hollow far cheek
    g.fillEllipse(hx + 1.5, hy - 1.1, 1.4, 1.7); // temple hollow

    if (S.hood) {
      // full cowl: cloth over the crown, the face lost in interior shadow
      g.fillStyle(S.hair, 1);
      g.fillPoints(
        [
          new Phaser.Geom.Point(hx - 3.7, -12.4),
          new Phaser.Geom.Point(hx - 3.1, -18),
          new Phaser.Geom.Point(hx, -20.3),
          new Phaser.Geom.Point(hx + 3.1, -18),
          new Phaser.Geom.Point(hx + 3.7, -12.4),
        ],
        true
      );
      g.fillStyle(0x05060a, 0.84); // the dark inside the hood
      g.fillEllipse(hx, hy + 0.2, 3.1, 4.2);
      g.fillStyle(S.robeLit, 0.75); // a rim of light on the hood's crest
      g.fillEllipse(hx - 1.4, -18.3, 2.0, 1.9);
    } else {
      // hair: a cap over the crown, then carve a gaunt face out beneath it
      g.fillStyle(S.hair, 1);
      g.fillEllipse(hx, hy - 1.4, 5.7, 4.0);
      g.fillRect(hx - 2.85, hy - 1.6, 5.7, 1.9);
      g.fillStyle(S.skin, 1);
      g.fillEllipse(hx + 0.2, hy + 1.0, 3.5, 3.3); // narrow jaw
      g.fillStyle(S.skinShade, 1); // hollow cheeks (both sides)
      g.fillEllipse(hx + 1.2, hy + 1.1, 1.6, 3.0);
      g.fillStyle(S.skinShade, 0.6);
      g.fillEllipse(hx - 1.2, hy + 1.4, 1.2, 2.0);
      g.fillStyle(S.skin, 1); // a catchlight on the near cheekbone
      g.fillEllipse(hx - 0.7, hy + 0.1, 1.3, 1.1);
      if (S.beard) {
        g.fillStyle(S.hair, 1); // a thin, straggly beard
        g.fillEllipse(hx, hy + 2.6, 3.3, 2.7);
      }
      g.fillStyle(0x0c0a10, 0.5); // a sunken shadow band across the eye sockets
      g.fillEllipse(hx, hy + 0.15, 3.6, 1.5);
      g.fillStyle(0x0c0a10, 0.85); // deep-set eyes
      g.fillCircle(hx - 0.9, hy + 0.2, 0.55);
      g.fillCircle(hx + 1.1, hy + 0.2, 0.55);
    }

    const c = this.add.container(x, y, [g]).setDepth(4.45).setScale(S.scale);
    if (!GameContext.activeProfile?.settings.reducedMotion) {
      this.tweens.add({ targets: c, y: y - 1.2, duration: 1500 + (Math.floor(x * 7) % 700), yoyo: true, repeat: -1, ease: "Sine.inOut" });
    }
    return c;
  }

  /** Finds the NPC within one tile of the player and points the "E: talk"
   *  prompt at it (NPCs take priority over echoes/obelisks for the hint). */
  private updateNearbyNpc(): void {
    if (this.dialoguePanel) {
      this.nearbyNpc = null;
      return;
    }
    const near = this.npcs.find((n) => Math.abs(n.col - this.playerPos.col) <= 1 && Math.abs(n.row - this.playerPos.row) <= 1) ?? null;
    for (const n of this.npcs) n.label.setVisible(n === near);
    this.nearbyNpc = near;
    if (near) {
      this.interactHint
        .setText("E: talk")
        .setPosition(near.col * TILE_SIZE + TILE_SIZE / 2, near.row * TILE_SIZE - 8)
        .setVisible(true);
    }
  }

  /** Narrative flags satisfied right now: explicit save flags + derived beats. */
  private storyFlagSet(): Set<string> {
    const p = GameContext.activeProfile;
    const s = new Set<string>(p?.storyFlags ?? []);
    if (p?.leftFoldAt) s.add("leftFold");
    if (p?.nariLostAt) s.add("nariLost");
    for (const id of p?.campaignProgress.clearedNodeIds ?? []) s.add(`cleared:${id}`);
    return s;
  }

  private openDialogue(npc: PlacedNpc): void {
    const flags = this.storyFlagSet();
    const beat = npc.def.beats.find((b) => !b.requires || flags.has(b.requires));
    if (!beat) return;
    this.dialogueLines = beat.lines;
    this.dialogueIdx = 0;
    this.dialogueSets = beat.sets ?? null;
    this.dialogueName = npc.def.name;
    this.showDialoguePanel();
  }

  private advanceDialogue(): void {
    if (this.dialogueIdx < this.dialogueLines.length - 1) {
      this.dialogueIdx++;
      this.showDialoguePanel();
    } else {
      this.closeDialogue();
    }
  }

  private showDialoguePanel(): void {
    // Fully tear down the previous panel (container.destroy() takes its child
    // text objects with it) so nothing from the last line lingers underneath.
    this.dialoguePanel?.destroy();
    this.dialoguePanel = null;

    const PAD = 9;
    const GAP = 3;
    const panelW = Math.min(BASE_WIDTH - 16, 236);
    const wrapW = panelW - PAD * 2;

    // Build the children left-aligned inside the padding, measure the wrapped
    // body, then size the panel to fit name + body + hint (auto-height: long
    // lines grow the box instead of spilling out of a fixed 46px frame).
    const name = this.add
      .text(0, 0, this.dialogueName.toUpperCase(), { fontFamily: "monospace", fontSize: "7px", color: "#f4d27a" })
      .setOrigin(0, 0);
    const body = this.add
      .text(0, 0, this.dialogueLines[this.dialogueIdx], {
        fontFamily: "monospace",
        fontSize: "7px",
        color: "#e8e2d4",
        align: "left",
        lineSpacing: 2,
        wordWrap: { width: wrapW, useAdvancedWrap: true },
      })
      .setOrigin(0, 0);
    const more = this.dialogueIdx < this.dialogueLines.length - 1;
    const hint = this.add
      .text(0, 0, more ? "E ▸" : "E ✕", { fontFamily: "monospace", fontSize: "6px", color: "#9fb0c0" })
      .setOrigin(1, 1);

    const nameH = 9;
    const hintH = 8;
    const panelH = PAD + nameH + GAP + body.height + GAP + hintH + PAD - 6;
    const panel = this.add.nineslice(0, 0, "ui_panel", undefined, panelW, panelH, 5, 5, 5, 5).setOrigin(0, 0);

    name.setPosition(PAD, PAD - 1);
    body.setPosition(PAD, PAD + nameH + GAP);
    hint.setPosition(panelW - PAD, panelH - PAD + 3);

    // Anchor the (top-left origin) panel bottom-centered, clear of the HUD.
    const px = Math.round((BASE_WIDTH - panelW) / 2);
    const py = Math.round(BASE_HEIGHT - panelH - 8);
    const container = this.add.container(px, py, [panel, name, body, hint]).setDepth(26);
    this.dialoguePanel = this.pinToScreen(container, px, py);
    this.repositionPinned();
  }

  private closeDialogue(): void {
    this.dialoguePanel?.destroy();
    this.dialoguePanel = null;
    if (this.dialogueSets) {
      const p = GameContext.activeProfile;
      if (p) {
        const flags = p.storyFlags ?? (p.storyFlags = []);
        if (!flags.includes(this.dialogueSets)) {
          flags.push(this.dialogueSets);
          void GameContext.persistActiveProfile();
        }
      }
      this.dialogueSets = null;
    }
  }

  /** Grid position test seam, read via the DEV-only __meterfallDebug hook. */
  getPlayerGridPosition(): GridPosition {
    return { ...this.playerPos };
  }

  /** Test seam: a node marker's tile position, so e2e specs never have to hardcode map coordinates. */
  getMarkerGridPosition(nodeId: string): GridPosition {
    const marker = this.markers.find((m) => m.nodeId === nodeId);
    if (!marker) throw new Error(`No overworld marker for node "${nodeId}"`);
    return { col: marker.col, row: marker.row };
  }

  /** Test seam: total map row count, so e2e specs never have to hardcode map dimensions. */
  getMapRowCount(): number {
    return this.walkable.length;
  }

  /**
   * Test seam (reached via the DEV-only __meterfallDebug hook): snaps the
   * player onto a node's marker tile and re-runs the same encounter-trigger
   * check a real step onto it performs. Exists because pixel-perfect
   * keyboard pathing across the whole map is exactly the slow/flaky
   * automation the e2e suite already avoids (see jumpToEncounter).
   */
  debugTeleportToNode(nodeId: string): void {
    const marker = this.markers.find((m) => m.nodeId === nodeId);
    if (!marker) throw new Error(`No overworld marker for node "${nodeId}"`);
    this.playerPos = { col: marker.col, row: marker.row };
    this.snapPlayerToGrid();
    this.checkEncounterTrigger();
  }

  /**
   * The control hint has done its job the moment the player moves. Fades it out
   * once and drops the reference, so a fight's HUD toggle can never bring a
   * retired hint back.
   */
  private retireControlHint(): void {
    const hint = this.controlHint;
    if (!hint) return;
    this.controlHint = null;
    this.exploreHud = this.exploreHud.filter((o) => o !== hint);
    if (Boolean(GameContext.activeProfile?.settings.reducedMotion)) {
      hint.destroy();
      return;
    }
    this.tweens.add({
      targets: hint,
      alpha: 0,
      duration: 900,
      delay: 550,
      ease: "Sine.in",
      onComplete: () => hint.destroy(),
    });
  }

  private heldDirection(): Direction | null {
    if (this.cursors.left.isDown || this.wasd.A.isDown) return "left";
    if (this.cursors.right.isDown || this.wasd.D.isDown) return "right";
    if (this.cursors.up.isDown || this.wasd.W.isDown) return "up";
    if (this.cursors.down.isDown || this.wasd.S.isDown) return "down";
    return null;
  }

  private tryStep(dir: Direction): void {
    // Mir's art is side-facing; face the walk direction (flip for left) and
    // run the one walk cycle for every direction.
    this.faceDirection(dir);

    const target = stepTarget(this.playerPos, dir);
    if (!isWalkable(this.walkable, target)) return;

    const vacated = { ...this.playerPos };
    this.moving = true;
    this.retireControlHint();
    this.playerPos = target;
    if (this.player.anims.getName() !== "leader_walk" || !this.player.anims.isPlaying) this.player.play("leader_walk");
    this.tweens.add({
      targets: this.player,
      x: target.col * TILE_SIZE + TILE_SIZE / 2,
      y: target.row * TILE_SIZE + TILE_SIZE / 2,
      duration: STEP_DURATION_MS,
      onComplete: () => {
        this.moving = false;
        this.checkLeaveFold();
        this.checkNariLoss();
        this.checkEncounterTrigger();
      },
    });
    this.stepNari(vacated);
  }

  /** Nari toddles to the tile his father just left. */
  private stepNari(spot: GridPosition): void {
    if (!this.nari) return;
    const tx = spot.col * TILE_SIZE + TILE_SIZE / 2;
    const ty = spot.row * TILE_SIZE + TILE_SIZE / 2 + 2;
    if (tx > this.nari.x) this.nari.setFlipX(true);
    else if (tx < this.nari.x) this.nari.setFlipX(false);
    if (this.nari.anims.getName() !== "nari_walk" || !this.nari.anims.isPlaying) this.nari.play("nari_walk");
    this.tweens.add({ targets: this.nari, x: tx, y: ty, duration: STEP_DURATION_MS + 30 });
  }

  /** The threshold beat (v14.0): Mir's first step OUT of the Fold (region 0,
   * the underwater town) and onto the climb. This is where the campaign
   * begins -- no foe stands inside the sanctuary, so the chorus only starts
   * once the town is behind him. Fires once, persisted on the save. */
  private checkLeaveFold(): void {
    const profile = GameContext.activeProfile;
    if (!profile || profile.leftFoldAt) return;
    if ((this.regions[this.playerPos.row]?.[this.playerPos.col] ?? 0) === 0) return; // still in the Fold
    profile.leftFoldAt = Date.now();
    void GameContext.persistActiveProfile();
    // The threshold cutscene (leaving the Fold); falls back to a toast if it's
    // already been seen.
    if (!CutsceneScene.play(this, "leaving_fold")) this.showToast("THE FOLD BEHIND YOU", "Only up, from here.");
  }

  /** The loss beat (§8.4 v12.0): Mir's first step onto the surface -- the
   * Scar, region index 3 -- and Nari is gone. Once, persisted on the save. */
  private checkNariLoss(): void {
    const profile = GameContext.activeProfile;
    if (!this.nari || !profile || profile.nariLostAt) return;
    if ((this.regions[this.playerPos.row]?.[this.playerPos.col] ?? 0) < 3) return;
    profile.nariLostAt = Date.now();
    void GameContext.persistActiveProfile();
    const nari = this.nari;
    const shadow = this.nariShadow;
    this.nari = null;
    this.nariShadow = null;
    const reduced = Boolean(profile.settings.reducedMotion);
    if (reduced) {
      nari.destroy();
      shadow?.destroy();
    } else {
      this.tweens.add({
        targets: nari,
        alpha: 0,
        duration: 2400,
        onComplete: () => {
          nari.destroy();
          shadow?.destroy();
        },
      });
    }
    // The taking cutscene (Nari lost at the Breach); falls back to a toast.
    if (!CutsceneScene.play(this, "nari_taken")) this.showToast("NARI?", "He was right behind you.");
  }

  /** Flips Mir to face the walk direction. Only horizontal moves change the
   * flip; up/down keep the last-faced side (his art is side-only). His
   * hand-drawn sheets natively face LEFT (see the run cycle's lean), so
   * moving right is the flipped side -- getting this backwards makes him
   * moonwalk everywhere. */
  private faceDirection(dir: Direction): void {
    if (dir === "left") this.player.setFlipX(false);
    else if (dir === "right") this.player.setFlipX(true);
  }

  /**
   * Walking onto an unlocked marker starts its fight IN PLACE (areas, not
   * arenas -- PRD §8.2 v7.6): the camera locks to a screen-sized room of the
   * actual world around the foe and the action sim runs right there. No
   * separate battle scene loads. Cleared and locked markers are walk-over
   * no-ops: cleared nodes sit on the road onward, and v1 has no re-fighting.
   */
  private checkEncounterTrigger(): void {
    const profile = GameContext.activeProfile;
    if (!profile || this.fight) return;
    const marker = this.markers.find((m) => m.col === this.playerPos.col && m.row === this.playerPos.row);
    if (!marker) return;
    if (nodeStatus(campaign, profile.campaignProgress, marker.nodeId) !== "unlocked") return;

    const encounterId = resolveEncounterId(getCampaignNode(marker.nodeId));
    if (!encounterId) return; // camp nodes have no encounter
    GameContext.pendingEncounterId = encounterId;
    GameContext.pendingNodeId = marker.nodeId;
    // the standing foe hands over to the live fight
    for (const o of this.nodeFoeVisuals.get(marker.nodeId) ?? []) (o as Phaser.GameObjects.Sprite).setVisible(false);
    const nodeX = marker.col * TILE_SIZE + TILE_SIZE / 2;
    const nodeY = marker.row * TILE_SIZE + TILE_SIZE / 2;
    this.fight = new WorldFight(
      {
        scene: this,
        playerSprite: this.player,
        // the trampled fight-ground clearing is BAKED into the painted plate
        // at every node (paint_ground.py), so this circle is always fightable
        // even where the map tiles underneath are water/rock -- every fight
        // gets a real room that IS the world, not an overlay
        setExploreHudVisible: (visible) => {
          for (const o of this.exploreHud) (o as Phaser.GameObjects.Image).setVisible(visible);
        },
        isWorldWalkable: (px, py) => {
          const dx = px - nodeX;
          const dy = py - nodeY;
          if (dx * dx + dy * dy < 64 * 64) return true;
          return isWalkable(this.walkable, { col: Math.floor(px / TILE_SIZE), row: Math.floor(py / TILE_SIZE) });
        },
      },
      marker.nodeId,
      encounterId,
      nodeX,
      nodeY
    );
  }

  /** Test seam: whether an in-world fight is currently live. */
  isFightActive(): boolean {
    return this.fight !== null;
  }

  /** Test seam: the live fight's sim arena (null while exploring). */
  getFightArena(): unknown {
    return this.fight?.simArena ?? null;
  }

  /**
   * Dresses the map so it doesn't read as hard-cut tile blocks: a bright foam
   * line + dark bank wherever water meets land, and gothic props (bones,
   * tombstones, dead trees, fungus, reeds, obelisk shards) scattered
   * deterministically on grass, clear of node markers, the spawn, and the
   * road. Purely decorative -- props don't affect walkability.
   */
  private decorate(map: Phaser.Tilemaps.Tilemap, ground: Phaser.Tilemaps.TilemapLayer, spawnTile: GridPosition): void {
    // Every region contributes 4 tiles (grass/path/water/rock, in that
    // order -- tools/pixelart/tiles.py region_tiles) at GID region*4+local+1,
    // so the local kind is always (gid-1) % 4 regardless of which of the
    // five regions a tile belongs to (tools/overworld/generate_overworld_map.py).
    const localKind = (gid: number) => (gid - 1) % 4;
    const isGrassGid = (gid: number | undefined) => gid !== undefined && localKind(gid) === 0;

    void isGrassGid;
    void spawnTile;
    const shore = this.add.graphics().setDepth(1);

    // Every prop in the world is placed BY HAND (owner: "items need to be
    // placed with intention. none of this scattering shit") -- authored
    // vignettes, singletons, and landmark landforms in dressing.json. The
    // hash-scatter system is deleted.
    this.placeAuthoredDressing(shore);
    this.placeRegionGates(map, ground, shore);
    this.addLivingDetail(map, ground);
  }

  /**
   * The world moves (the HLD bar: their air is alive; ours must be MORE so):
   * teal glints pulse on open water and every canopy crown sways. All of it
   * deterministic and skipped under reduced motion.
   */
  private addLivingDetail(map: Phaser.Tilemaps.Tilemap, ground: Phaser.Tilemaps.TilemapLayer): void {
    const reduced = Boolean(GameContext.activeProfile?.settings.reducedMotion);
    if (reduced) return;
    // water glints: sparse hash-picked open-water tiles get a slow pulse
    for (let row = 2; row < map.height - 2; row++) {
      for (let col = 2; col < map.width - 2; col++) {
        const gid = ground.getTileAt(col, row)?.index;
        if (gid == null || (gid - 1) % 4 !== 2) continue;
        const h = ((col * 40503) ^ (row * 2654435761)) >>> 0;
        if (h % 100 >= 4) continue;
        const gx = col * TILE_SIZE + ((h >> 5) % TILE_SIZE);
        const gy = row * TILE_SIZE + ((h >> 9) % TILE_SIZE);
        const glint = this.add
          .image(gx, gy, "glow")
          .setBlendMode(Phaser.BlendModes.ADD)
          .setTint(0x9fe8e0)
          .setScale(0.06)
          .setAlpha(0)
          .setDepth(1.2);
        this.tweens.add({
          targets: glint,
          alpha: { from: 0, to: 0.4 },
          scaleX: 0.1,
          duration: 1800 + (h % 1400),
          yoyo: true,
          repeat: -1,
          delay: h % 2600,
          ease: "Sine.inOut",
        });
      }
    }
    // canopy sway: every overhanging crown breathes
    for (const c of this.canopies) {
      this.tweens.add({
        targets: c,
        angle: (c.x + c.y) % 2 === 0 ? 1.3 : -1.2,
        duration: 4200 + ((c.x * 7 + c.y * 13) % 1800),
        yoyo: true,
        repeat: -1,
        ease: "Sine.inOut",
      });
    }
    this.addDrownedLife(map, ground);
  }

  /**
   * The drowned regions (Fold + Kelp Shelf) are UNDERWATER, so the water
   * column itself is alive (v14.1): sediment/bubbles rise off the seafloor and
   * beds of eelgrass sway in the current. This replaces the water glints the
   * drowned regions lost when their puddles were removed -- the area reads as
   * submerged, not dry, and it MOVES. Deterministic, reduced-motion-gated
   * (caller already returned under reduced motion), and a fixed pool of
   * repeat:-1 tweens so nothing accumulates over a long session.
   */
  private addDrownedLife(map: Phaser.Tilemaps.Tilemap, ground: Phaser.Tilemaps.TilemapLayer): void {
    for (let row = 2; row < map.height - 2; row++) {
      for (let col = 2; col < map.width - 2; col++) {
        const region = this.regions[row]?.[col] ?? 0;
        if (region > 1) continue; // drowned regions only
        const gid = ground.getTileAt(col, row)?.index;
        if (gid == null || (gid - 1) % 4 !== 0) continue; // seafloor (grass/silt) only
        const h = ((col * 26777) ^ (row * 2246822519)) >>> 0;
        const bucket = h % 1200; // v15.0: sparser per-tile on the ~10x world so total stays bounded
        const bx = col * TILE_SIZE + ((h >> 5) % TILE_SIZE);
        const by = row * TILE_SIZE + ((h >> 9) % TILE_SIZE);
        if (bucket < 3) {
          // a rising sediment mote / bubble: born at the floor, drifts up the
          // water column, fading as it goes, then loops from the floor again.
          const mote = this.amb(this.add
            .image(bx, by, "glow")
            .setBlendMode(Phaser.BlendModes.ADD)
            .setTint(0x8fe0d8)
            .setScale(0.05)
            .setAlpha(0)
            .setDepth(4.2));
          this.tweens.add({
            targets: mote,
            y: { from: by + 2, to: by - 22 - (h % 14) },
            alpha: { from: 0.42, to: 0 },
            scaleX: 0.09,
            scaleY: 0.09,
            duration: 3200 + (h % 2600),
            repeat: -1,
            delay: h % 3400,
            ease: "Sine.out",
          });
        } else if (bucket < 7) {
          // an eelgrass frond rooted to the floor. Its sway (and the periodic
          // current surge that bends every blade at once) is driven in
          // driveAmbience so a swell can roll the whole bed together (v14.2).
          const tall = 7 + (h % 6);
          const blade = this.amb(this.add
            .rectangle(bx, by + 4, 2, tall, 0x24463a)
            .setOrigin(0.5, 1)
            .setDepth(1.3)
            .setAlpha(0.9));
          this.eelgrass.push({ blade, phase: (h % 628) / 100 });
        }
      }
    }
    this.addFauna(map, ground);
    this.addSurfaceAmbience(map, ground);
    this.addRoamingNPCs(map, ground);
    this.placeNpcs(map, ground);
    this.addWeather();
  }

  /** Register a dynamic-ambience object so it can be hidden/paused during fights. */
  private amb<T extends Phaser.GameObjects.GameObject>(o: T): T {
    this.ambient.push(o);
    return o;
  }

  /** Hide (stop rendering) and pause the tweens of all ambient objects, or
   * restore them. Called on fight enter/exit so the ambient layer costs nothing
   * while the fight owns the frame. */
  private setAmbientHidden(hidden: boolean): void {
    if (hidden === this.ambientHidden) return;
    this.ambientHidden = hidden;
    for (const o of this.ambient) {
      (o as unknown as { setVisible?: (v: boolean) => unknown }).setVisible?.(!hidden);
      for (const t of this.tweens.getTweensOf(o)) {
        if (hidden) t.pause();
        else t.resume();
      }
    }
  }

  /** Per-frame cosmetic ambience (v14.2): the sanctuary pulses on the song's
   * beat, the drowned beds sway and periodically surge, and distant lightning
   * flickers over the Stage. Purely visual -- never gameplay-timing judgment,
   * which stays on TransportClock (PRD §10.2). Skipped under reduced motion. */
  private driveAmbience(deltaMs: number): void {
    if (GameContext.activeProfile?.settings.reducedMotion) return;
    this.beatAccumMs += deltaMs;
    // distance (seconds) to the nearest beat: the real deereater grid when the
    // song is audible, else a steady 103.36-BPM fallback so it still breathes.
    const beatMs = 60000 / 103.36;
    let beatDist: number;
    const pos = music.position();
    if (this.overworldSongMap && pos !== null) {
      beatDist = nearestBeatDistanceSeconds(this.overworldSongMap, pos);
    } else {
      const phase = (this.beatAccumMs % beatMs) / beatMs;
      beatDist = Math.min(phase, 1 - phase) * (beatMs / 1000);
    }
    const beat = Math.max(0, 1 - beatDist / 0.16); // 1 on the beat, 0 between
    const breathe = 0.5 + 0.5 * Math.sin(this.beatAccumMs / 1100);
    if (this.townCrownGlow) {
      this.townCrownGlow.setAlpha(0.4 + beat * 0.5).setScale(0.6 + beat * 0.24 + breathe * 0.03);
    }
    for (const w of this.worshippers) w.body.setAngle(w.lean * -(2.5 + beat * 6)); // the congregation bows on the beat

    // the current surge: a swell rolls through the drowned beds every ~20s
    this.surgeAccumMs += deltaMs;
    const sp = this.surgeAccumMs % 20000;
    const surge = sp < 2600 ? Math.sin((sp / 2600) * Math.PI) : 0;
    const swayT = this.beatAccumMs / 1000;
    for (const e of this.eelgrass) e.blade.setAngle(Math.sin(swayT * 1.3 + e.phase) * 7 + surge * 15);

    // distant lightning over the Stage -- gated behind photosensitivity safe mode
    this.lightningAccumMs += deltaMs;
    if (this.lightningFlash && this.lightningAccumMs > 16000) {
      this.lightningAccumMs = 0;
      if (!GameContext.activeProfile?.settings.photosensitivitySafeMode) {
        const f = this.lightningFlash;
        this.tweens.killTweensOf(f);
        f.setAlpha(0);
        this.tweens.add({ targets: f, alpha: 0.42, duration: 80, yoyo: true, repeat: 1, repeatDelay: 70, ease: "Quad.out" });
      }
    }
  }

  private isDrownedFloor(col: number, row: number, ground: Phaser.Tilemaps.TilemapLayer): boolean {
    if ((this.regions[row]?.[col] ?? 9) > 1) return false;
    const gid = ground.getTileAt(col, row)?.index ?? 0;
    return (gid - 1) % 4 === 0;
  }

  /**
   * Drifting fauna (v14.2): loose fish schools and pulsing jellyfish in the
   * drowned water column, crabs scuttling the seafloor, and an eel coiled by
   * the rocks. Deterministic hash placement, fixed pools of repeat:-1 tweens.
   */
  private addFauna(map: Phaser.Tilemaps.Tilemap, ground: Phaser.Tilemaps.TilemapLayer): void {
    let eelPlaced = false;
    for (let row = 3; row < map.height - 3; row++) {
      for (let col = 3; col < map.width - 3; col++) {
        if (!this.isDrownedFloor(col, row, ground)) continue;
        const h = ((col * 374761393) ^ (row * 668265263)) >>> 0;
        const bx = col * TILE_SIZE + 8;
        const by = row * TILE_SIZE + 8;
        if (h % 5210 < 2) {
          // a loose school: 3 fish clustered, patrolling together
          const size = h % 2 === 0 ? 1 : 0.8;
          for (let f = 0; f < 3; f++) {
            const fh = (h + f * 2654435761) >>> 0;
            const fx = bx + ((fh >> 3) % 14) - 7;
            const fy = by + ((fh >> 7) % 12) - 6;
            const fish = this.amb(this.add.graphics().setDepth(4.15).setPosition(fx, fy).setScale(size));
            fish.fillStyle(0x315f56, 0.92);
            fish.fillEllipse(0, 0, 9, 4);
            fish.fillTriangle(-4, 0, -8, -3, -8, 3);
            fish.fillStyle(0x8fe0d8, 0.5);
            fish.fillCircle(2, -1, 0.8);
            const range = 34 + (fh % 34);
            this.tweens.add({
              targets: fish,
              x: fx + range,
              duration: 3000 + (fh % 2400),
              yoyo: true,
              repeat: -1,
              delay: (fh % 1200),
              ease: "Sine.inOut",
              onYoyo: () => (fish.scaleX = -size),
              onRepeat: () => (fish.scaleX = size),
            });
            this.tweens.add({ targets: fish, y: fy - 6, duration: 1500 + (fh % 900), yoyo: true, repeat: -1, ease: "Sine.inOut" });
          }
        } else if (h % 6170 < 2) {
          // a jellyfish: drifts up the column, bell pulsing, then loops
          const jelly = this.amb(this.add.graphics().setDepth(4.18).setPosition(bx, by).setAlpha(0.9));
          jelly.fillStyle(0x6fd8cf, 0.5);
          jelly.fillEllipse(0, 0, 13, 9);
          jelly.fillStyle(0x9ff0e6, 0.35);
          jelly.fillEllipse(0, -1, 8, 5);
          jelly.lineStyle(1, 0x6fd8cf, 0.4);
          for (let t = -3; t <= 3; t += 2) jelly.lineBetween(t, 3, t + 1, 12);
          this.tweens.add({ targets: jelly, y: by - 66, alpha: 0, duration: 9000 + (h % 4000), repeat: -1, delay: h % 5000, ease: "Sine.inOut" });
          this.tweens.add({ targets: jelly, scaleY: 0.72, duration: 1300 + (h % 700), yoyo: true, repeat: -1, ease: "Sine.inOut" });
        } else if (h % 6400 < 2) {
          // a crab scuttling sideways on the floor, with pauses
          const crab = this.amb(this.add.graphics().setDepth(4.16).setPosition(bx, by));
          crab.fillStyle(0x835043, 0.95);
          crab.fillEllipse(0, 0, 7, 4);
          crab.lineStyle(1, 0x6a3f34, 0.9);
          crab.lineBetween(-3, 0, -5, 2);
          crab.lineBetween(3, 0, 5, 2);
          const dir = (h & 1) === 0 ? 1 : -1;
          this.tweens.add({
            targets: crab,
            x: bx + dir * (10 + (h % 8)),
            duration: 1500,
            yoyo: true,
            hold: 900,
            repeatDelay: 1400,
            repeat: -1,
            ease: "Sine.inOut",
          });
        } else if (!eelPlaced && h % 9070 < 2) {
          // one eel, coiled by the rocks, undulating in place
          const eel = this.amb(this.add.graphics().setDepth(4.17).setPosition(bx, by));
          eel.fillStyle(0x223129, 0.95);
          for (let s = 0; s < 6; s++) eel.fillCircle(s * 4 - 10, Math.sin(s) * 2, 3 - s * 0.25);
          eel.fillStyle(0x8fe0d8, 0.5);
          eel.fillCircle(-11, 0, 0.9);
          this.tweens.add({ targets: eel, angle: 9, duration: 1900, yoyo: true, repeat: -1, ease: "Sine.inOut" });
          eelPlaced = true;
        }
      }
    }
  }

  /**
   * Region-keyed airborne ambience for the surfaced world (v14.2): pale spray
   * over the Breach waterline, ash + rising embers across the Scar, drifting
   * violet spores on the Stage approach. Each region gets its own signature so
   * all five biomes breathe, not just the drowned ones.
   */
  private addSurfaceAmbience(map: Phaser.Tilemaps.Tilemap, ground: Phaser.Tilemaps.TilemapLayer): void {
    for (let row = 2; row < map.height - 2; row++) {
      for (let col = 2; col < map.width - 2; col++) {
        const region = this.regions[row]?.[col] ?? 0;
        if (region < 2) continue; // drowned regions handled by addDrownedLife
        const gid = ground.getTileAt(col, row)?.index ?? 0;
        if ((gid - 1) % 4 !== 0) continue; // walkable ground only
        const h = ((col * 2246822519) ^ (row * 3266489917)) >>> 0;
        const bucket = h % 2400; // v15.0: sparser per-tile on the ~10x world
        const px = col * TILE_SIZE + ((h >> 5) % TILE_SIZE);
        const py = row * TILE_SIZE + ((h >> 9) % TILE_SIZE);
        if (region === 3) {
          if (bucket < 1) {
            // ash: a grey fleck drifting down and sideways on the hot wind
            const ash = this.amb(this.add.rectangle(px, py, 2, 2, 0x6b6157, 0.5).setDepth(4.2));
            this.tweens.add({ targets: ash, y: py + 20 + (h % 12), x: px + 10 - (h % 20), alpha: 0, duration: 4200 + (h % 2600), repeat: -1, delay: h % 3800, ease: "Sine.in" });
          } else if (bucket < 3) {
            // ember: a warm spark lifting off the scorched ground
            const ember = this.amb(this.add.image(px, py, "glow").setBlendMode(Phaser.BlendModes.ADD).setTint(0xff8a3c).setScale(0.05).setAlpha(0).setDepth(4.25));
            this.tweens.add({ targets: ember, y: py - 18 - (h % 14), alpha: { from: 0.5, to: 0 }, duration: 3000 + (h % 2200), repeat: -1, delay: h % 3400, ease: "Sine.out" });
          }
        } else if (region === 4) {
          if (bucket < 2) {
            // Keep: dust, hanging in lamplight. A drowned concert hall is the
            // one interior in the game, so its ambient particle is the thing
            // that only exists indoors -- motes turning over in warm light,
            // the most domestic image available. EMBER, not the old 0xb18cf0
            // violet: there is no violet in this world (§3), and a spore is
            // something growing, which is the opposite of what this room is.
            const spore = this.amb(this.add.image(px, py, "glow").setBlendMode(Phaser.BlendModes.ADD).setTint(0xf4d27a).setScale(0.045).setAlpha(0).setDepth(4.22));
            this.tweens.add({ targets: spore, y: py - 24 - (h % 16), x: px + 6 - (h % 12), alpha: { from: 0.36, to: 0 }, duration: 5200 + (h % 3200), repeat: -1, delay: h % 4200, ease: "Sine.inOut" });
          }
        } else if (region === 2 && bucket < 1) {
          // Breach: faint pale sea-spray over the crossing
          const spray = this.amb(this.add.image(px, py, "glow").setBlendMode(Phaser.BlendModes.ADD).setTint(0xd8efe6).setScale(0.05).setAlpha(0).setDepth(4.2));
          this.tweens.add({ targets: spray, y: py - 14 - (h % 10), alpha: { from: 0.3, to: 0 }, duration: 3600 + (h % 2000), repeat: -1, delay: h % 3000, ease: "Sine.out" });
        }
      }
    }
  }

  /**
   * Roaming ambient life (v14.2): pilgrims pacing the roads (the world is
   * peopled, not just dressed) and a lone fisher at the Breach waterline. Each
   * walks a short pre-validated segment on a repeat tween -- no pathfinding,
   * nothing added per frame.
   */
  private addRoamingNPCs(map: Phaser.Tilemaps.Tilemap, ground: Phaser.Tilemaps.TilemapLayer): void {
    const isPath = (c: number, r: number) => ((ground.getTileAt(c, r)?.index ?? 0) - 1) % 4 === 1;
    let pilgrims = 0;
    for (let row = 3; row < map.height - 3 && pilgrims < 4; row++) {
      for (let col = 3; col < map.width - 3 && pilgrims < 4; col++) {
        if (!isPath(col, row)) continue;
        const h = ((col * 40503) ^ (row * 1900987)) >>> 0;
        if (h % 43 !== 0) continue; // sparse
        // measure the road run around this tile on each axis; walk the longer
        let west = 0, east = 0, north = 0, south = 0;
        while (west < 4 && isPath(col - west - 1, row)) west++;
        while (east < 4 && isPath(col + east + 1, row)) east++;
        while (north < 4 && isPath(col, row - north - 1)) north++;
        while (south < 4 && isPath(col, row + south + 1)) south++;
        const horiz = west + east, vert = north + south;
        if (Math.max(horiz, vert) < 2) continue;
        const useH = horiz >= vert;
        const aCol = useH ? col - west : col;
        const aRow = useH ? row : row - north;
        const bCol = useH ? col + east : col;
        const bRow = useH ? row : row + south;
        const ax = aCol * TILE_SIZE + 8, ay = aRow * TILE_SIZE + 12;
        const bx = bCol * TILE_SIZE + 8, by = bRow * TILE_SIZE + 12;
        const p = this.amb(this.drawPilgrim(ax, ay));
        this.tweens.add({
          targets: p,
          x: bx,
          y: by,
          duration: 2600 + (h % 1800) * (useH ? horiz : vert),
          yoyo: true,
          repeat: -1,
          hold: 500 + (h % 900),
          repeatDelay: 500 + (h % 900),
          delay: h % 1600,
          ease: "Sine.inOut",
          onStart: () => (p.scaleX = bx >= ax ? 1 : -1),
          onYoyo: () => (p.scaleX = bx >= ax ? -1 : 1),
          onRepeat: () => (p.scaleX = bx >= ax ? 1 : -1),
        });
        this.tweens.add({ targets: p, scaleY: 0.94, duration: 340, yoyo: true, repeat: -1, ease: "Sine.inOut" });
        pilgrims++;
      }
    }
    // the fisher: a Breach-shore tile facing open water, line bobbing on the tide
    for (let row = 3; row < map.height - 3; row++) {
      let done = false;
      for (let col = 3; col < map.width - 3; col++) {
        if ((this.regions[row]?.[col] ?? 0) !== 2) continue;
        if (((ground.getTileAt(col, row)?.index ?? 0) - 1) % 4 !== 0) continue; // stand on ground
        const waterEast = ((ground.getTileAt(col + 1, row)?.index ?? 0) - 1) % 4 === 2;
        const waterWest = ((ground.getTileAt(col - 1, row)?.index ?? 0) - 1) % 4 === 2;
        if (!waterEast && !waterWest) continue;
        const fx = col * TILE_SIZE + 8, fy = row * TILE_SIZE + 12;
        const face = waterEast ? 1 : -1;
        const fisher = this.amb(this.drawPilgrim(fx, fy));
        fisher.scaleX = face;
        const rod = this.amb(this.add.graphics().setDepth(4.41));
        rod.lineStyle(1, 0x2a2018, 0.9);
        rod.lineBetween(fx + face * 3, fy - 12, fx + face * 12, fy - 18);
        const float = this.amb(this.add.image(fx + face * 14, fy - 6, "glow").setBlendMode(Phaser.BlendModes.ADD).setTint(0xf4d27a).setScale(0.04).setAlpha(0.5).setDepth(4.42));
        this.tweens.add({ targets: float, y: fy - 3, duration: 1700, yoyo: true, repeat: -1, ease: "Sine.inOut" });
        done = true;
        break;
      }
      if (done) break;
    }
  }

  /** A standing hooded figure (pilgrim/fisher): shadow, robe, bowed head, all
   * in one graphics so it translates and flips as a unit. */
  private drawPilgrim(x: number, y: number): Phaser.GameObjects.Graphics {
    const p = this.add.graphics().setDepth(4.42).setPosition(x, y);
    p.fillStyle(0x05060a, 0.35);
    p.fillEllipse(0, 2, 9, 3); // shadow
    p.fillStyle(0x222f38, 1);
    p.fillEllipse(0, -7, 7, 13); // robe
    p.fillStyle(0x2e3f48, 1);
    p.fillEllipse(-1.5, -7, 4, 12); // front light
    p.fillStyle(0x18232b, 1);
    p.fillCircle(0, -14, 2.7); // head
    return p;
  }

  /**
   * Weather beats (v14.2): a distant lightning glow poised over the Stage
   * (fired from driveAmbience, gated by photosensitivity safe mode) and a few
   * tide shimmers sweeping the Breach waterline.
   */
  private addWeather(): void {
    const boss = this.markers.find((m) => m.nodeId === "boss_1");
    if (boss) {
      this.lightningFlash = this.amb(this.add
        .image(boss.col * TILE_SIZE + 8, boss.row * TILE_SIZE - 36, "glow")
        .setBlendMode(Phaser.BlendModes.ADD)
        .setTint(0xbfe8ff)
        .setScale(3.4)
        .setAlpha(0)
        .setDepth(11));
    }
    // tide shimmers: bright bars sweeping a few Breach-water tiles
    let shimmers = 0;
    for (let row = 2; row < this.regions.length - 2 && shimmers < 5; row++) {
      for (let col = 2; col < (this.regions[row]?.length ?? 0) - 2 && shimmers < 5; col++) {
        if ((this.regions[row]?.[col] ?? 0) !== 2) continue;
        const h = ((col * 917) ^ (row * 337)) >>> 0;
        if (h % 29 !== 0) continue;
        const sx = col * TILE_SIZE + 8, sy = row * TILE_SIZE + 8;
        const bar = this.amb(this.add.rectangle(sx, sy, 18, 2, 0xd8efe6, 0.28).setBlendMode(Phaser.BlendModes.ADD).setDepth(1.25));
        this.tweens.add({ targets: bar, x: sx + 14, alpha: 0.06, duration: 2600 + (h % 1800), yoyo: true, repeat: -1, delay: h % 2200, ease: "Sine.inOut" });
        shimmers++;
      }
    }
  }

  /**
   * Authored set-dressing: composed mini-scenes (a fled camp, a shrine, a
   * wrecked cart) where every piece has a story reason to be where it is,
   * plus lone singletons and landmark landforms. Data-driven from
   * dressing.json; each piece appears at most twice per region, so the art
   * library reads as a world, not a repeating texture.
   */
  private placeAuthoredDressing(shore: Phaser.GameObjects.Graphics): void {
    const reduced = Boolean(GameContext.activeProfile?.settings.reducedMotion);
    const file = dressingData as {
      regions: {
        region: string;
        placements: { vignette: string; key: string; col: number; row: number; dx: number; dy: number; scale: number; flip: boolean }[];
      }[];
    };
    // `col`/`row` are ABSOLUTE tiles on the 356x200 map. They used to be
    // region-local, offset by `regionIndex * 26` -- a formula from the pre-v15
    // map, which was ~10x smaller than the world it was still indexing. Region 0
    // actually occupies cols 0-75, rows 127-199, so every hand-authored vignette
    // was being drawn ~140 tiles north of the region it belonged to, in a corner
    // of the Saltmines. The region name now only says which biome a placement
    // belongs to; where it goes is where it says (tools/overworld/place_fold.py).
    for (const region of file.regions) {
      if (REGION_BIOMES.indexOf(region.region) < 0) continue;
      for (const p of region.placements) {
        if (!this.textures.exists(p.key)) continue;
        const x = p.col * TILE_SIZE + TILE_SIZE / 2 + p.dx;
        const y = p.row * TILE_SIZE + TILE_SIZE + p.dy;
        const canopy = /landform_canopy/.test(p.key);
        const landform = /landform_/.test(p.key);
        // canonical world scale wins over the authored value (one unit for
        // the whole world -- a chair can never outgrow a building again)
        const src = this.textures.get(p.key).getSourceImage();
        const scale = worldScaleFor(p.key, src.height) ?? p.scale;
        // The contact shadow is sized from the SPRITE, not from a constant. It
        // was a flat 12x4 ellipse, which is a plausible shadow for a crate and
        // an invisible one under a 95px-wide house -- the Fold's buildings read
        // as floating until this was proportional.
        const footW = landform ? (canopy ? 34 : 46) : Math.max(12, src.width * scale * 0.74);
        shore
          .fillStyle(0x05060a, landform ? 0.3 : 0.3)
          .fillEllipse(x, y - 1, footW, Math.max(4, footW * 0.11));
        const img = this.add
          .image(x, y, p.key)
          .setOrigin(0.5, 1)
          .setScale(scale)
          .setFlipX(p.flip)
          .setTint(0xd6dce6)
          .setDepth(canopy ? 6.5 : landform ? 2.5 : 2);
        if (canopy) this.canopies.push(img);
        // A lit building spills light onto the ground in front of it. Without
        // this the houses sat on the silt like cut-outs: the windows were warm
        // and the tile under the door was not, which is the one thing a lit
        // window cannot do. Wide, weak, and warm -- it should never read as a
        // second lamp, only as the reason the doorstep is visible.
        // Warm spill from the lit windows onto the ground at the foot of a
        // house. Scaled from the SPRITE, not from the glow texture's own size --
        // the first cut divided the display width by two constants, which on the
        // 356px-wide terrace produced a pale lens WIDER AND TALLER than the
        // building and read as a puddle in front of it. A spill is a shallow
        // pool right at the wall: 62% of the facade wide, an eighth of that
        // deep, and faint.
        if (/env_fold_house/.test(p.key)) {
          const spillW = src.width * scale * 0.62;
          const glowSrc = this.textures.get("glow").getSourceImage();
          this.add
            .image(x, y - 1, "glow")
            .setBlendMode(Phaser.BlendModes.ADD)
            .setTint(0xe8b070)
            .setScale(spillW / glowSrc.width, (spillW * 0.13) / glowSrc.height)
            .setAlpha(0.13)
            .setDepth(1.9);
        }
        // emissive pieces cast their light -- the night world reads lit
        if (/lantern|crystal|tidepool|brazier|candle|torch|dockpost|votives|belljar|lamp$|geode|hourglass|campfire|shrine/.test(p.key)) {
          const teal = /tidepool|belljar|dockpost/.test(p.key);
          const tint = teal ? 0x49c6bd : 0xf0a648;
          this.add
            .image(x, y - 6, "glow")
            .setBlendMode(Phaser.BlendModes.ADD)
            .setTint(tint)
            .setScale(0.4)
            .setAlpha(0.32)
            .setDepth(2.1);
          // fireflies: 2-3 sparks orbit every flame (alive, not decorated).
          // Deterministic per position; skipped under reduced motion.
          if (!reduced) {
            const h = ((p.col * 92821) ^ (p.row * 68917)) >>> 0;
            for (let i = 0; i < 2 + (h % 2); i++) {
              const spark = this.add
                .image(x + ((h >> (i * 4)) % 9) - 4, y - 8 - ((h >> (i * 3)) % 6), "glow")
                .setBlendMode(Phaser.BlendModes.ADD)
                .setTint(tint)
                .setScale(0.05)
                .setAlpha(0)
                .setDepth(5.5);
              this.tweens.add({
                targets: spark,
                y: spark.y - 7 - (i * 3),
                x: spark.x + (i % 2 === 0 ? 3 : -3),
                alpha: { from: 0, to: 0.5 },
                duration: 1500 + ((h >> i) % 900),
                yoyo: true,
                repeat: -1,
                delay: i * 520 + (h % 400),
                ease: "Sine.inOut",
              });
            }
          }
        }
      }
    }
  }

  /**
   * Region-entry vistas (goal: intentional): where the main road crosses a
   * region boundary, the NEXT region announces itself -- its most iconic
   * landform stands north of the road and one of its lit props flanks the
   * south side, so every border crossing reads as a composed gateway instead
   * of a tint change.
   */
  private placeRegionGates(map: Phaser.Tilemaps.Tilemap, ground: Phaser.Tilemaps.TilemapLayer, shore: Phaser.GameObjects.Graphics): void {
    const GATE_PROPS: Record<string, string> = {
      saltmines: "env_saltmines_scatter_lantern",
      pit: "env_pit_scatter_torch",
      attic: "env_attic_scatter_lamp",
      hall: "env_hall_scatter_candelabra",
    };
    for (let k = 1; k < REGION_BIOMES.length; k++) {
      const bcol = k * 26;
      const rows: number[] = [];
      for (let r = 1; r < map.height - 1; r++) {
        const gid = ground.getTileAt(bcol, r)?.index;
        if (gid != null && gid > 0 && (gid - 1) % 4 === 1) rows.push(r);
      }
      if (rows.length === 0) continue;
      const row = rows[Math.floor(rows.length / 2)];
      const biome = REGION_BIOMES[k];
      const gx = bcol * TILE_SIZE + TILE_SIZE / 2;
      const outcrop = `env_${biome}_landform_outcrop2`;
      if (this.textures.exists(outcrop)) {
        const oy = (row - 3) * TILE_SIZE;
        shore.fillStyle(0x05060a, 0.3).fillEllipse(gx, oy - 2, 42, 9);
        this.add.image(gx, oy, outcrop).setOrigin(0.5, 1).setScale(1).setDepth(2.5).setTint(0xd6dce6);
      }
      const prop = GATE_PROPS[biome];
      if (prop && this.textures.exists(prop)) {
        const py = (row + 4) * TILE_SIZE;
        const ps = worldScaleFor(prop, this.textures.get(prop).getSourceImage().height) ?? 0.7;
        shore.fillStyle(0x05060a, 0.28).fillEllipse(gx, py - 1, 12, 4);
        this.add.image(gx, py, prop).setOrigin(0.5, 1).setScale(ps).setDepth(2).setTint(0xd6dce6);
        this.add
          .image(gx, py - 8, "glow")
          .setBlendMode(Phaser.BlendModes.ADD)
          .setTint(0xf0a648)
          .setScale(0.45)
          .setAlpha(0.38)
          .setDepth(2.1);
      }
    }
  }

  /**
   * Two cheap, static, world-space passes that kill the last "flat tilemap"
   * tells: (1) a soft cross-fade band at each region boundary so the five
   * moods bleed into one another instead of meeting on a razor-straight line;
   * (2) a large-scale shadow-dapple overlay (the fog texture, world-space,
   * dark, low alpha) so the repeated grass stamp dissolves under organic
   * light variation far larger than the 16px grid.
   */
  private softenSeamsAndDapple(map: Phaser.Tilemaps.Tilemap): void {
    // Region cross-fade is BAKED into the painted ground plate now
    // (paint_ground.py blends the region bases over a wide band); only the
    // organic shadow dapple remains a runtime layer.
    if (!GameContext.activeProfile?.settings.photosensitivitySafeMode) {
      // world-space shadow dapple: soft dark blobs, tiled large, breaking the grid
      this.add
        .tileSprite(0, 0, map.widthInPixels, map.heightInPixels, "fx_haze")
        .setOrigin(0, 0)
        .setDepth(1)
        .setTileScale(2.4)
        .setTint(0x05060a)
        .setAlpha(0.09);
    }
  }



  /** Draws an undiscovered echo's rune + a soft additive glow pulse (found ones stay marked but dim). */
  private drawEcho(echo: Echo): void {
    const x = echo.col * TILE_SIZE + TILE_SIZE / 2;
    const y = echo.row * TILE_SIZE + TILE_SIZE / 2;
    const found = this.echoFoundIds.has(echo.id);
    this.add.image(x, y, "ow_props", ECHO_RUNE_FRAME).setOrigin(0.5, 1).setScale(0.5).setDepth(2).setAlpha(found ? 0.55 : 1);

    const reduced = Boolean(GameContext.activeProfile?.settings.reducedMotion);
    const glow = this.add
      .image(x, y - 10, "glow")
      .setBlendMode(Phaser.BlendModes.ADD)
      .setTint(0x49c6bd)
      .setScale(found ? 0.3 : 0.45)
      .setAlpha(found ? 0.12 : 0.4)
      .setDepth(2);
    this.echoGlows.set(echo.id, glow);
    if (!found && !reduced) {
      this.tweens.add({ targets: glow, scale: 0.6, alpha: 0.65, yoyo: true, repeat: -1, duration: 900 });
    }
  }

  /**
   * Areas, not arenas (PRD §8.2 v7.6): a fight node is not an abstract map
   * pin -- the foe itself STANDS in the world at its place, and the player
   * stumbles into it. Locked foes wait as dark silhouettes past the frontier;
   * cleared places keep only a faint released-soul ember. Camp nodes (no
   * encounter) keep the plain marker. Every fight node also gets a
   * save-obelisk placed on a nearby walkable tile (§8.8: rest + save before
   * the fight).
   */
  private drawMarker(profile: NonNullable<typeof GameContext.activeProfile>, marker: Marker): void {
    const status = nodeStatus(campaign, profile.campaignProgress, marker.nodeId);
    const x = marker.col * TILE_SIZE + TILE_SIZE / 2;
    const y = marker.row * TILE_SIZE + TILE_SIZE / 2;
    const node = getCampaignNode(marker.nodeId);
    const reduced = profile.settings.reducedMotion;

    // Representative foe: the first enemy of the node's first pool encounter,
    // or its fixed encounter (the boss uses a fixed encounterId, not a pool).
    const encounterId = node.encounterPool?.[0] ?? node.encounterId;
    const foeId = encounterId ? getEncounter(encounterId).enemyWave[0] : null;

    if (!foeId) {
      // camp node: the old plain marker
      const circle = this.add.circle(x, y, 6, MARKER_COLORS[status]);
      this.add
        .text(x, y, NODE_TYPE_LABEL[node.type] ?? "?", { fontFamily: "monospace", fontSize: "7px", color: "#000000" })
        .setOrigin(0.5);
      if (status === "unlocked" && !reduced) {
        this.tweens.add({ targets: circle, scale: 1.25, yoyo: true, repeat: -1, duration: 500 });
      }
      return;
    }

    this.placeObelisk(marker);

    if (status === "cleared") {
      // the foe is gone; a released-soul ember marks where it stood
      const ember = this.add
        .image(x, y, "glow")
        .setBlendMode(Phaser.BlendModes.ADD)
        .setTint(0x49c6bd)
        .setScale(0.22)
        .setAlpha(0.22)
        .setDepth(2);
      if (!reduced) this.tweens.add({ targets: ember, alpha: 0.1, yoyo: true, repeat: -1, duration: 1600 });
      return;
    }

    const colossal = foeId === "the_conductor";
    const tex = colossal ? "conductor_colossal" : `enemy_${foeId}`;
    const accent = FOE_ACCENT[foeId] ?? 0xffffff;
    const footY = y + TILE_SIZE / 2 - 1;

    // contact shadow + emissive aura ground the foe in the world
    const foeShadow = this.add.ellipse(x, footY, colossal ? 30 : 20, colossal ? 9 : 6, 0x05060a, 0.4).setDepth(3);
    const aura = this.add
      .image(x, footY - 10, "glow")
      .setBlendMode(Phaser.BlendModes.ADD)
      .setTint(accent)
      .setScale(colossal ? 0.9 : 0.55)
      .setAlpha(status === "locked" ? 0.08 : 0.3)
      .setDepth(3);

    const foe = this.add.sprite(x, footY, tex, 0).setOrigin(0.5, 1).setScale(0.25).setDepth(4.5);
    // the live fight hides these when the player walks into the foe
    this.nodeFoeVisuals.set(marker.nodeId, [foe, aura, foeShadow]);
    if (status === "locked") {
      // past the frontier: a dark, motionless silhouette waiting in the fog.
      // A faint additive accent rim behind it keeps the shade's hue identity
      // (design-audit-3: a flat black cutout read as a rendering bug, and
      // every locked foe looked the same).
      const rim = this.add
        .sprite(x, footY, tex, 0)
        .setOrigin(0.5, 1)
        .setScale(1.07)
        .setBlendMode(Phaser.BlendModes.ADD)
        .setTint(accent)
        .setAlpha(0.22)
        .setDepth(4.45);
      foe.setTint(0x232c40).setAlpha(0.95);
      this.nodeFoeVisuals.get(marker.nodeId)!.push(rim);
    } else {
      const animKey = `ow_foe_${tex}`;
      if (!this.anims.exists(animKey)) {
        this.anims.create({ key: animKey, frames: this.anims.generateFrameNumbers(tex, { start: 0, end: 1 }), frameRate: 1.6, repeat: -1 });
      }
      foe.play(animKey);
      if (!reduced) this.tweens.add({ targets: aura, alpha: 0.5, scale: aura.scale * 1.25, yoyo: true, repeat: -1, duration: 900 });
    }
  }

  /**
   * Places a save-obelisk on a walkable tile near a fight node (PRD §8.8:
   * rest + save before the fight). Two tiles out so standing beside the
   * obelisk never overlaps the fight-trigger tile itself.
   */
  private placeObelisk(marker: Marker): void {
    const candidates: GridPosition[] = [
      { col: marker.col - 2, row: marker.row },
      { col: marker.col + 2, row: marker.row },
      { col: marker.col, row: marker.row + 2 },
      { col: marker.col, row: marker.row - 2 },
      { col: marker.col - 2, row: marker.row + 1 },
      { col: marker.col + 2, row: marker.row + 1 },
    ];
    const spot = candidates.find(
      (c) => isWalkable(this.walkable, c) && !this.markers.some((m) => m.col === c.col && m.row === c.row)
    );
    if (!spot) return;
    const x = spot.col * TILE_SIZE + TILE_SIZE / 2;
    const y = spot.row * TILE_SIZE + TILE_SIZE - 1;
    this.add.ellipse(x, y, 16, 5, 0x05060a, 0.4).setDepth(3);
    const glow = this.add
      .image(x, y - 12, "glow")
      .setBlendMode(Phaser.BlendModes.ADD)
      .setTint(0x49c6bd)
      .setScale(0.4)
      .setAlpha(0.35)
      .setDepth(3);
    // The waystone goes through `worldScaleFor` like every other piece in the
    // world -- it was drawn at `setScale(1)`, which is the one thing §4 of the
    // style contract forbids ("one unit for the whole world, so a chair can
    // never outgrow a building"). WorldScale has had its 2.4m entry all along.
    const stoneSrc = this.textures.exists("env_shared_save_obelisk")
      ? this.textures.get("env_shared_save_obelisk").getSourceImage()
      : null;
    if (stoneSrc) {
      this.add
        .image(x, y, "env_shared_save_obelisk")
        .setOrigin(0.5, 1)
        .setScale(worldScaleFor("env_shared_save_obelisk", stoneSrc.height) ?? 0.24)
        .setTint(0xd6dce6)
        .setDepth(4);
    } else {
      // art not shipped yet: a simple standing stone so the save point still exists
      this.add.rectangle(x, y - 7, 6, 14, 0x2c3a4a).setDepth(4);
    }
    this.obelisks.push({ col: spot.col, row: spot.row, glow });
  }

  /**
   * The Fold's town obelisk (v14.0): a single MASSIVE monolith at the heart
   * of the prayer plaza, ringed by kneeling worshippers -- the drowned town
   * caught mid-prayer, the thing the two Fold echoes speak of ("we woke on
   * the floor and it was already listening"). Drawn procedurally in the
   * painterly, sprite-free register the world settled into (v11.2 purge), and
   * registered as the town's save point so "E: pray" here saves like any
   * obelisk. There is no fight in the Fold; this is what the sanctuary is for.
   */
  /**
   * v15.0: place every painted ground chunk at its world position. A chunk of
   * `chunk` px at S density covers `chunk*(TILE_SIZE/s)` world px; with S==16
   * that is 1:1, so a 1024px chunk covers 1024 world px at scale 1. Chunks are
   * culled to the camera view each frame in cullGroundChunks (bounds overdraw).
   */
  private placeGroundChunks(): void {
    if (!GROUND_MANIFEST) return;
    const { chunk, rows, cols, s } = GROUND_MANIFEST;
    const scale = TILE_SIZE / s; // world px per plate px
    const cpx = chunk * scale; // world px per chunk
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const key = `ground_chunk_${r}_${c}`;
        if (!this.textures.exists(key)) continue;
        const src = this.textures.get(key).getSourceImage();
        const img = this.add.image(c * cpx, r * cpx, key).setOrigin(0, 0).setScale(scale).setDepth(0);
        this.groundChunks.push({ img, w: src.width * scale, h: src.height * scale });
      }
    }
  }

  /** Render only the ground chunks intersecting the camera view (+margin). */
  private cullGroundChunks(): void {
    if (!this.groundChunks.length) return;
    const v = this.cameras.main.worldView;
    const m = 48;
    for (const { img, w, h } of this.groundChunks) {
      const vis = img.x < v.right + m && img.x + w > v.left - m && img.y < v.bottom + m && img.y + h > v.top - m;
      if (img.visible !== vis) img.setVisible(vis);
    }
  }

  private placeTownObelisk(): void {
    const tile = this.townObeliskTile;
    if (!tile) return;
    const reduced = Boolean(GameContext.activeProfile?.settings.reducedMotion);
    const cx = tile.col * TILE_SIZE + TILE_SIZE / 2;
    const baseY = tile.row * TILE_SIZE + TILE_SIZE; // feet at the tile's bottom edge

    // Kneeling worshippers ring the dais first (drawn under the monolith), each
    // bowed toward the obelisk. Deterministic ring so the town looks authored.
    const RING = 26;
    const count = 7;
    for (let i = 0; i < count; i++) {
      // Bias the ring to the near/side arcs so none sit dead in front of Mir's
      // approach up the plaza; skip the top of the circle (behind the stone).
      const ang = Math.PI * 0.5 + (i / count) * Math.PI * 1.6 + 0.2;
      const wx = cx + Math.cos(ang) * RING;
      const wy = baseY - 6 + Math.sin(ang) * (RING * 0.42);
      this.drawWorshipper(wx, wy, wx < cx, reduced, i);
    }

    // A broad soft contact shadow, then a low stone dais the monolith stands on.
    this.add.ellipse(cx, baseY, 58, 18, 0x05060a, 0.42).setDepth(3.2);
    this.add.ellipse(cx, baseY - 1, 42, 12, 0x1b2530, 1).setDepth(3.3);
    this.add.ellipse(cx, baseY - 3, 34, 9, 0x27343f, 1).setDepth(3.35);

    // The monolith itself is AUTHORED ART now (tools/art/env_fold.py `obelisk`),
    // not five `Graphics` polygons.
    //
    // What was here drew a flat silhouette, a flat lit half, and five identical
    // cyan rectangles down the middle. In the shipped build it read as a grey
    // gradient WEDGE with tick marks -- and style-contract §0 has a rule for
    // exactly this: "an abstraction is not an image." This is the first
    // landmark a new player sees, the save point they come back to all game,
    // and the object the premise hangs off; a triangle will not do. The sprite
    // carries quarried stone, faint courses, chipped edges, an old waterline of
    // salt, and a recessed channel of carved glyphs that reads as WRITING.
    //
    // `worldScaleFor` sizes it from the canon 9m (WorldScale), so it stands
    // ~8.4 tiles tall -- five times Mir, which is what "massive" has to mean.
    const obeliskSrc = this.textures.exists("env_fold_obelisk") ? this.textures.get("env_fold_obelisk").getSourceImage() : null;
    const obeliskScale = obeliskSrc ? (worldScaleFor("env_fold_obelisk", obeliskSrc.height) ?? 0.3) : 0.3;
    const H = obeliskSrc ? obeliskSrc.height * obeliskScale : 96;
    if (obeliskSrc) {
      this.add
        .image(cx, baseY - 1, "env_fold_obelisk")
        .setOrigin(0.5, 1)
        .setScale(obeliskScale)
        .setDepth(4.6);
    }

    // The crown-light: a pulsing teal glow at the pyramidion, the beacon the
    // whole ascent is drawn to. A fainter body-glow lifts the stone off the dark.
    // The body-glow is now a HALO AT THE FOOT, not a wash over the shaft. At
    // scale 1.0 / alpha 0.22 it was tuned against the old flat-polygon monolith,
    // where washing teal over grey was the only thing giving it presence. Over
    // the authored sprite the same glow covered the whole stone and bleached out
    // the courses, the chips and the waterline -- the art was there and the
    // lighting was hiding it.
    const bodyGlow = this.add
      .image(cx, baseY - H * 0.18, "glow")
      .setBlendMode(Phaser.BlendModes.ADD)
      .setTint(0x49c6bd)
      .setScale(0.42, 0.3)
      .setAlpha(0.13)
      .setDepth(4.5);
    const crownGlow = this.add
      .image(cx, baseY - 2 - H - 6, "glow")
      .setBlendMode(Phaser.BlendModes.ADD)
      .setTint(0x8fe6dd)
      .setScale(0.66)
      .setAlpha(0.45)
      .setDepth(4.7);
    // The body-glow breathes on its own; the CROWN pulses on the song's beat,
    // driven from driveAmbience (v14.2) -- the obelisk is "listening" to the
    // chorus, so it lights on the beat. Store the ref for that driver.
    if (!reduced) {
      this.tweens.add({ targets: bodyGlow, alpha: 0.2, yoyo: true, repeat: -1, duration: 2600, ease: "Sine.inOut" });
    }
    this.townCrownGlow = crownGlow;
    // Resolve the overworld song's beat grid once (deereater, "explore" mode)
    // so the beat driver can pulse the sanctuary on the real beat.
    const songId = music.currentSongId();
    this.overworldSongMap = songId ? (songMaps.get(songId) ?? null) : null;

    // Register as the town save point: standing on any of the dais-adjacent
    // tiles and pressing E prays/saves, reusing the obelisk interaction.
    this.obelisks.push({ col: tile.col, row: tile.row, glow: crownGlow });
  }

  /** One kneeling worshipper: a hunched silhouette bowed toward the obelisk.
   * The bow itself is driven collectively on the beat by driveAmbience, so the
   * whole congregation nods to the chorus together (v14.2). */
  private drawWorshipper(x: number, y: number, faceRight: boolean, reduced: boolean, _seed: number): void {
    this.add.ellipse(x, y + 1.5, 13, 4.5, 0x05060a, 0.4).setDepth(4.36);
    const lean = faceRight ? 1 : -1;
    // Draw in LOCAL coords so setAngle pivots around the worshipper's ground
    // point (x,y) rather than swinging the shape about the world origin.
    const body = this.add.graphics().setDepth(4.4).setPosition(x, y);
    // the robe pooled on the ground where they kneel
    body.fillStyle(0x1a252e, 1);
    body.fillEllipse(0, -0.6, 11.5, 5);
    // hunched back/torso, bowed toward the stone -- thin and starved
    body.fillStyle(0x243139, 1);
    body.fillEllipse(lean * 1.9, -4.4, 8.4, 8.8);
    body.fillStyle(0x1a242c, 0.5); // a hollow shadow down the curled spine
    body.fillEllipse(lean * 1.2, -4.2, 2.0, 7.4);
    body.fillStyle(0x30414a, 0.9); // cold rim-light up the curve of the back
    body.fillEllipse(-lean * 2.4, -5, 3.4, 7.8);
    // a thin arm laid forward toward the obelisk, a bony hand at its end
    body.fillStyle(0x1c2830, 1);
    body.fillEllipse(lean * 4.0, -3.2, 5.0, 2.2);
    body.fillStyle(0x0f1720, 1);
    body.fillEllipse(lean * 6.0, -2.8, 1.8, 1.6);
    // bowed head, and a faint hood crest catching the light
    body.fillStyle(0x121b22, 1);
    body.fillCircle(lean * 4.3, -7.4, 2.5);
    body.fillStyle(0x2a3842, 0.85);
    body.fillEllipse(lean * 3.8, -9.0, 2.9, 2.1);
    body.setAngle(lean * -4);
    if (!reduced) this.worshippers.push({ body, lean });
  }

  /** Rest at a save-obelisk: persist the save and acknowledge it in-world. */
  private restAtObelisk(obelisk: { col: number; row: number; glow: Phaser.GameObjects.Image }): void {
    void GameContext.persistActiveProfile();
    GameContext.analytics.track("obelisk_rest");
    if (!GameContext.activeProfile?.settings.reducedMotion) {
      this.tweens.add({ targets: obelisk.glow, alpha: 0.9, scale: 0.9, yoyo: true, duration: 350 });
    }
    this.showToast("THE OBELISK HEARS", "Progress saved.");
  }

  /** A small self-dismissing framed message (same visual family as the echo panel). */
  private showToast(title: string, body: string): void {
    this.echoPanel?.destroy();
    const panelW = 150;
    const panel = this.add.nineslice(0, 0, "ui_panel", undefined, panelW, 32, 5, 5, 5, 5);
    const t = this.add.text(0, -8, title, { fontFamily: "monospace", fontSize: "7px", color: "#49c6bd" }).setOrigin(0.5);
    const b = this.add.text(0, 4, body, { fontFamily: "monospace", fontSize: "7px", color: "#e8e2d4" }).setOrigin(0.5);
    this.echoPanel = this.pinToScreen(
      this.add.container(BASE_WIDTH / 2, BASE_HEIGHT - 26, [panel, t, b]).setDepth(25),
      BASE_WIDTH / 2,
      BASE_HEIGHT - 26
    );
    this.repositionPinned();
    this.time.delayedCall(2200, () => this.dismissEchoPanel());
  }

  /** Pin a UI object at a design-space offset from the camera's top-left. */
  pinToScreen<T extends Phaser.GameObjects.GameObject & { setPosition(x: number, y: number): unknown; active: boolean }>(
    obj: T,
    dx: number,
    dy: number
  ): T {
    this.pinned.push({ obj, dx, dy });
    return obj;
  }

  private repositionPinned(): void {
    const v = this.cameras.main.worldView;
    this.pinned = this.pinned.filter((p) => p.obj.active);
    for (const p of this.pinned) p.obj.setPosition(v.x + p.dx, v.y + p.dy);
  }

  private snapPlayerToGrid(): void {
    this.player.setPosition(this.playerPos.col * TILE_SIZE + TILE_SIZE / 2, this.playerPos.row * TILE_SIZE + TILE_SIZE / 2);
  }
}
