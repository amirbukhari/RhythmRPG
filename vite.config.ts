import { defineConfig } from "vite";

// Served from https://amirbukhari.github.io/RhythmRPG/ (a GitHub Pages project
// site, not a custom domain), so built asset URLs need the repo-name base path
// or they resolve to the domain root and 404. Key this off the build command,
// NOT an env var: every production build gets the Pages base, so a deploy can
// never silently ship root-relative URLs if someone forgets to set a flag.
// Local dev (command === "serve") keeps root-relative paths.
export default defineConfig(({ command }) => ({
  root: ".",
  base: command === "build" ? "/RhythmRPG/" : "/",
  server: {
    port: 5173,
  },
  build: {
    outDir: "dist",
    // Reach older mobile Safari/WebViews: Vite's default target (~Safari 14+)
    // ships syntax that hard-crashes older iPhones into a silent black
    // screen. es2019/safari13 transpiles that away at negligible size cost.
    target: ["es2019", "safari13"],
    rollupOptions: {
      output: {
        // Engine libraries change never; game code changes every deploy.
        // Splitting them means a returning phone only re-downloads the
        // (small) game chunk -- and kills the >500kb single-chunk warning.
        manualChunks: {
          phaser: ["phaser"],
          tone: ["tone"],
        },
      },
    },
  },
}));
