import Phaser from "phaser";
import type { BeatTier, HitEvent } from "../../systems/action/ActionCombat";

/**
 * M3 game feel: the 80 milliseconds after a blow lands.
 *
 * WHY HITSTOP HERE IS RENDER-ONLY, AND WHY THAT IS NOT A COMPROMISE
 * Every action game buys impact by freezing the simulation for a few frames.
 * This game cannot: PRD §10.2 (audio-clock authority) says judgment reads the
 * playing audio element's `currentTime`, and the song does not stop when the
 * sword lands. Pause the sim for 78ms and the sim's clock and the song's clock
 * disagree by 78ms forever after -- every subsequent judgment lies.
 *
 * So the sim never stops. The PICTURE stops: the two sprites hold their current
 * frame, shove apart along the impact axis, squash, and flash, while position
 * and judgment carry on underneath. That reads as weight for the same reason
 * real hitstop does -- the eye is reading held frames, not integrated physics --
 * and it costs the song nothing. `WorldFight.render()` writes sim positions
 * first and then calls `decorate()`, so the hold is always applied last and can
 * never fight the sim for authority.
 *
 * WHY THE TIER IS THE VOLUME KNOB
 * A rhythm game's whole promise is that landing ON the beat feels different, not
 * merely scores different. Before this, a perfect and an off-beat hit produced
 * an identical picture and differed only in a damage number and a text popup --
 * information, not sensation. Here the tier drives stop length, shove distance,
 * spark count, flash, shake and pitch together, so `perfect` is roughly three
 * and a half times the event that `off` is. You learn the beat through your
 * hands.
 */

/** Hold length in ms by tier. `off` is deliberately non-zero: every hit has
 * weight, or the low tiers feel broken rather than weak. */
const STOP_MS: Record<BeatTier, number> = { off: 24, good: 38, great: 56, perfect: 82 };
/** How far the target is shoved along the impact axis at the moment of contact,
 * in design-space px, by tier. It eases back to zero over the hold. */
const SHOVE_PX: Record<BeatTier, number> = { off: 1.5, good: 2.5, great: 4, perfect: 6 };
/** Camera shake amplitude by tier (Phaser's normalized units). */
const SHAKE: Record<BeatTier, number> = { off: 0, good: 0.0022, great: 0.0042, perfect: 0.0075 };
const TIER_COLOR: Record<BeatTier, number> = { off: 0x9fb0c0, good: 0x9fb0c0, great: 0x49c6bd, perfect: 0xf4d27a };

interface Hold {
  t: number;
  dur: number;
  nx: number;
  ny: number;
  shove: number;
  squash: number;
  sprite: Phaser.GameObjects.Sprite;
  resumeAnim: boolean;
}

export interface FeelSettings {
  reducedMotion: boolean;
  photosensitive: boolean;
}

export class GameFeel {
  private holds = new Map<string, Hold>();
  private settings: FeelSettings;

  constructor(
    private scene: Phaser.Scene,
    settings: FeelSettings,
  ) {
    this.settings = settings;
  }

  setSettings(s: FeelSettings): void {
    this.settings = s;
  }

  /** Punctuate one impact. `x`/`y` are WORLD coordinates of the contact point
   * (the caller adds the arena origin), `target` the sprite that got hit and
   * `attacker` the one that swung -- both hold their frame for the stop. */
  impact(ev: HitEvent, x: number, y: number, target?: Phaser.GameObjects.Sprite, attacker?: Phaser.GameObjects.Sprite): void {
    const { reducedMotion, photosensitive } = this.settings;
    const weight = ev.heavy ? 1.55 : 1;
    const fatal = ev.kind === "fall" ? 1.7 : 1;
    const dur = STOP_MS[ev.tier] * weight * fatal;
    const colour = ev.kind === "parry" ? 0x9fe8e0 : TIER_COLOR[ev.tier];

    // 1. the hold. Not motion (it is the ABSENCE of motion), so reduced-motion
    //    keeps it -- it is the part of the effect that carries the weight.
    if (target) this.hold(ev.targetId, target, ev.nx, ev.ny, SHOVE_PX[ev.tier] * weight * (reducedMotion ? 0 : 1), dur);
    if (attacker) this.hold(`${ev.targetId}:by`, attacker, -ev.nx, -ev.ny, reducedMotion ? 0 : 1.2 * weight, dur * 0.7);

    // 2. the impact frame: an additive ghost of the target, held for the stop
    //    and then gone in one step. This is what makes a frozen frame read as
    //    a STRUCK frame rather than a dropped one.
    if (target && !photosensitive) {
      const ghost = this.scene.add
        .image(target.x, target.y, target.texture.key, target.frame.name)
        .setFlipX(target.flipX)
        .setScale(target.scaleX * 1.14, target.scaleY * 0.92)
        .setBlendMode(Phaser.BlendModes.ADD)
        .setTint(colour)
        .setAlpha(reducedMotion ? 0.3 : 0.75)
        .setDepth(9.2);
      this.scene.tweens.add({ targets: ghost, alpha: 0, duration: dur * 1.5, ease: "Quad.easeIn", onComplete: () => ghost.destroy() });
    }

    // 3. sparks along the impact axis -- direction is information: it tells you
    //    which way the blow travelled, so a trade reads differently from a hit.
    if (!reducedMotion && !photosensitive) {
      const n = ev.tier === "perfect" ? 7 : ev.tier === "great" ? 5 : ev.tier === "good" ? 3 : 2;
      const spread = ev.kind === "parry" ? Math.PI * 2 : 1.5;
      const base = Math.atan2(ev.ny, ev.nx);
      for (let i = 0; i < n; i++) {
        const ang = base + (spread === Math.PI * 2 ? (i / n) * spread : ((i / Math.max(1, n - 1)) - 0.5) * spread);
        const speed = 26 + (i % 3) * 12 + (ev.heavy ? 14 : 0);
        const spark = this.scene.add
          .image(x, y, "spark")
          .setBlendMode(Phaser.BlendModes.ADD)
          .setTint(colour)
          .setScale(0.16 + (i % 2) * 0.08)
          .setAngle((ang * 180) / Math.PI)
          .setDepth(9.4);
        this.scene.tweens.add({
          targets: spark,
          x: x + Math.cos(ang) * speed,
          y: y + Math.sin(ang) * speed,
          scale: 0.03,
          alpha: 0,
          duration: 170 + (i % 3) * 70,
          ease: "Quad.easeOut",
          onComplete: () => spark.destroy(),
        });
      }
      // a single hard flash disc at the contact: the "connect" read
      const pop = this.scene.add
        .image(x, y, "glow")
        .setBlendMode(Phaser.BlendModes.ADD)
        .setTint(colour)
        .setScale(ev.heavy ? 0.22 : 0.15)
        .setAlpha(0.9)
        .setDepth(9.3);
      this.scene.tweens.add({ targets: pop, scale: pop.scale * 2.6, alpha: 0, duration: dur * 2, ease: "Cubic.easeOut", onComplete: () => pop.destroy() });
    }

    // 4. the camera. Only the player's own landed blows shake it -- shaking on
    //    every enemy nick turns the screen into soup.
    if (!reducedMotion && !photosensitive) {
      const amp = SHAKE[ev.tier] * weight * fatal * (ev.attackerTeam === "player" ? 1 : 0.7);
      if (amp > 0) this.scene.cameras.main.shake(Math.round(dur * 1.4), amp);
    }
  }

  private hold(key: string, sprite: Phaser.GameObjects.Sprite, nx: number, ny: number, shove: number, dur: number): void {
    const playing = sprite.anims?.isPlaying ?? false;
    if (playing) sprite.anims.pause();
    const prev = this.holds.get(key);
    this.holds.set(key, {
      t: 0,
      dur,
      nx,
      ny,
      shove,
      squash: 0.16,
      sprite,
      // never lose the fact that the clip WAS playing because a second hit
      // landed inside the first hold
      resumeAnim: playing || (prev?.resumeAnim ?? false),
    });
  }

  /** Advance the holds. Called once per frame with the real frame delta --
   * this is presentation, so a wall clock is the correct clock here. */
  update(deltaMs: number): void {
    for (const [key, h] of this.holds) {
      h.t += deltaMs;
      if (h.t < h.dur) continue;
      if (h.resumeAnim && h.sprite.active) h.sprite.anims.resume();
      this.holds.delete(key);
    }
  }

  /** Apply the hold to a sprite AFTER the sim has positioned it. `baseScale`
   * is the scale the renderer just set, so the squash composes with it instead
   * of replacing it. Returns true if a hold is active. */
  /**
   * How far into a hold `id` still is: 1 at contact, 0 at release, 0 when free.
   *
   * The renderer uses this for the HIT FLASH, which is the reason it exists.
   * A flash keyed to the sim's `hitstun` state instead was held for the whole
   * 150-250ms of hitstun -- a full white `setTintFill` silhouette that long
   * does not read as an impact, it reads as the sprite having broken, and it
   * erased the one frame of animation the hit was supposed to show off.
   * Keying it here instead ties it to the same tier-scaled hold as the shove,
   * the sparks and the shake, so a Perfect flashes harder AND longer than an
   * off-beat swing, for free.
   */
  flash(id: string): number {
    const h = this.holds.get(id);
    return h ? Math.max(0, 1 - h.t / h.dur) : 0;
  }

  decorate(id: string, sprite: Phaser.GameObjects.Sprite, baseScale: number): boolean {
    const h = this.holds.get(id) ?? this.holds.get(`${id}:by`);
    if (!h || h.sprite !== sprite) return false;
    const k = 1 - h.t / h.dur; // 1 at contact -> 0 at release
    const ease = k * k; // snaps out, so the shove is a jolt not a drift
    sprite.setPosition(Math.round(sprite.x + h.nx * h.shove * ease), Math.round(sprite.y + h.ny * h.shove * ease));
    sprite.setScale(baseScale * (1 + h.squash * ease), baseScale * (1 - h.squash * 0.7 * ease));
    return true;
  }

  /** True while anything is held -- lets the caller skip its own idle jitter. */
  get busy(): boolean {
    return this.holds.size > 0;
  }

  destroy(): void {
    for (const [, h] of this.holds) if (h.resumeAnim && h.sprite.active) h.sprite.anims.resume();
    this.holds.clear();
  }
}
