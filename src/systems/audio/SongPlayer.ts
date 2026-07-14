import sunshineUrl from "../../../assets/audio/sunshine_sally.mp3";
import deereaterUrl from "../../../assets/audio/deereater.mp3";
import glassriffUrl from "../../../assets/audio/glassriff.mp3";
import johnsAnusUrl from "../../../assets/audio/johns_anus.mp3";
import quotienceUrl from "../../../assets/audio/quotience.mp3";
import truckersUrl from "../../../assets/audio/truckers_for_christ.mp3";

/**
 * The real Inhalants soundtrack. This is a music game, so the music is the real
 * band -- six of their tracks, streamed with HTMLAudioElement and lazy-loaded
 * per scene (only the currently-playing song is ever fetched, so boot stays
 * light despite ~45MB of audio on disk). Each scene picks a mode; the player
 * crossfades to that mode's song and loops it.
 *
 * mode -> song
 *   menu    -> Sunshine Sally      (the title theme)
 *   explore -> Deereater           (the drowned overworld)
 *   combat  -> Glassriff / John's Anus / Truckers for Christ (rotates per fight)
 *   boss    -> Quotience           (the Conductor's hall)
 *
 * Mobile autoplay: browsers block play() until a user gesture. The gesture is
 * the AudioGateScene tap, which calls setMode("menu") from inside the handler,
 * so the first play() is gesture-driven and later scene changes inherit it.
 * play() rejections are swallowed -- a blocked song must never break a scene.
 */

type Mode = "menu" | "explore" | "combat" | "boss";

const MENU = sunshineUrl;
const EXPLORE = deereaterUrl;
const BOSS = quotienceUrl;
// Combat rotates so back-to-back fights don't loop the same track.
const COMBAT_ROTATION = [glassriffUrl, johnsAnusUrl, truckersUrl];

const FADE_MS = 900;

class SongPlayer {
  private cache = new Map<string, HTMLAudioElement>();
  private current: HTMLAudioElement | null = null;
  private currentUrl = "";
  private volume = 0.7;
  private combatIdx = 0;
  private fadeRaf: number | null = null;

  /** Master music volume 0..1 (from settings). */
  setVolume(v: number): void {
    this.volume = Math.max(0, Math.min(1, v));
    // If not mid-fade, apply immediately to the live song.
    if (this.current && this.fadeRaf === null) this.current.volume = this.volume;
  }

  /** Pick (and start) the song for a scene's mood. Idempotent per song. */
  setMode(mode: Mode): void {
    this.play(this.urlFor(mode));
  }

  /** Compatibility with the old MusicEngine API -- setMode already starts. */
  start(): void {
    if (this.current && this.current.paused) {
      const p = this.current.play();
      if (p) p.catch(() => {});
    }
  }

  stop(): void {
    if (this.current) this.fadeOut(this.current);
  }

  private urlFor(mode: Mode): string {
    switch (mode) {
      case "menu":
        return MENU;
      case "explore":
        return EXPLORE;
      case "boss":
        return BOSS;
      case "combat":
        return COMBAT_ROTATION[this.combatIdx++ % COMBAT_ROTATION.length];
    }
  }

  private get(url: string): HTMLAudioElement {
    let a = this.cache.get(url);
    if (!a) {
      a = new Audio(url);
      a.loop = true;
      a.preload = "none"; // only fetched when it first plays -> boot stays light
      a.volume = 0;
      this.cache.set(url, a);
    }
    return a;
  }

  private play(url: string): void {
    if (url === this.currentUrl && this.current && !this.current.paused) {
      // already the live song: just make sure the volume is right
      this.current.volume = this.volume;
      return;
    }
    const prev = this.current;
    const next = this.get(url);
    this.currentUrl = url;
    this.current = next;
    next.volume = 0;
    try {
      next.currentTime = 0;
    } catch {
      /* not yet seekable -- fine */
    }
    const p = next.play();
    if (p) p.catch(() => {}); // blocked until a gesture; setMode is re-called after the gate
    this.crossfade(prev && prev !== next ? prev : null, next);
  }

  /** HTMLMediaElement.volume throws outside [0,1]; rAF timing can nudge a naive
   * lerp slightly past either end, so every write goes through this. */
  private static vol(el: HTMLAudioElement, v: number): void {
    el.volume = v < 0 ? 0 : v > 1 ? 1 : v;
  }

  private crossfade(prev: HTMLAudioElement | null, next: HTMLAudioElement): void {
    if (this.fadeRaf !== null) cancelAnimationFrame(this.fadeRaf);
    const target = this.volume;
    const prevFrom = prev ? prev.volume : 0;
    const start = performance.now();
    const tick = (now: number): void => {
      const t = Math.max(0, Math.min(1, (now - start) / FADE_MS));
      SongPlayer.vol(next, target * t);
      if (prev) SongPlayer.vol(prev, prevFrom * (1 - t));
      if (t < 1) {
        this.fadeRaf = requestAnimationFrame(tick);
      } else {
        this.fadeRaf = null;
        if (prev) prev.pause();
      }
    };
    this.fadeRaf = requestAnimationFrame(tick);
  }

  private fadeOut(el: HTMLAudioElement): void {
    if (this.fadeRaf !== null) cancelAnimationFrame(this.fadeRaf);
    const from = el.volume;
    const start = performance.now();
    const tick = (now: number): void => {
      const t = Math.max(0, Math.min(1, (now - start) / FADE_MS));
      SongPlayer.vol(el, from * (1 - t));
      if (t < 1) this.fadeRaf = requestAnimationFrame(tick);
      else {
        this.fadeRaf = null;
        el.pause();
      }
    };
    this.fadeRaf = requestAnimationFrame(tick);
  }
}

/** One shared soundtrack for the whole game -- the real Inhalants tracks. */
export const music = new SongPlayer();
