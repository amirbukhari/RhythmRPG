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

// url -> songId, matching src/data/content/songs/<songId>.json (PRD §8.3):
// combat judgment resolves the playing song's beat map through this.
const SONG_ID_BY_URL: Record<string, string> = {
  [sunshineUrl]: "sunshine_sally",
  [deereaterUrl]: "deereater",
  [glassriffUrl]: "glassriff",
  [johnsAnusUrl]: "johns_anus",
  [truckersUrl]: "truckers_for_christ",
  [quotienceUrl]: "quotience",
};

const FADE_MS = 900;

class SongPlayer {
  private cache = new Map<string, HTMLAudioElement>();
  private current: HTMLAudioElement | null = null;
  private currentUrl = "";
  private volume = 0.7;
  private combatIdx = 0;
  private fadeRaf: number | null = null;
  private rate = 1;

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

  /** songId of the live song (whether or not it is currently audible). */
  currentSongId(): string | null {
    return this.current ? (SONG_ID_BY_URL[this.currentUrl] ?? null) : null;
  }

  /**
   * FILE-TIME position (seconds) of the audibly playing song, or null when
   * nothing is actually sounding (no song, paused/blocked, or not enough
   * data buffered). Judgment (PRD §8.3) reads the beat from this -- callers
   * must fall back to the transport grid on null, never assume audio.
   */
  position(): number | null {
    const a = this.current;
    if (!a || a.paused || a.readyState < 2 /* HAVE_CURRENT_DATA */) return null;
    return a.currentTime;
  }

  /**
   * Jump the live song to a file position (seconds) -- §8.7 boss phase
   * transitions bind to beat-aligned section starts of the boss track.
   */
  seek(seconds: number): void {
    if (!this.current) return;
    try {
      this.current.currentTime = Math.max(0, seconds);
    } catch {
      /* not seekable yet -- the phase still escalates, just without the jump */
    }
  }

  /**
   * Playback rate, coupled to the accessibility game-speed setting during
   * fights (PRD §8.3.3): the judged grid lives in file-time, so slowing the
   * song and slowing judgment are the same operation and can never diverge.
   * Applied to every cached element so crossfades inherit it.
   */
  setRate(rate: number): void {
    this.rate = Math.max(0.5, Math.min(1.5, rate));
    for (const a of this.cache.values()) {
      a.playbackRate = this.rate;
      // Keep the band's pitch while slowed (default in modern browsers;
      // set explicitly where the property exists).
      if ("preservesPitch" in a) (a as HTMLAudioElement & { preservesPitch: boolean }).preservesPitch = true;
    }
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
      a.playbackRate = this.rate;
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
