import { defineConfig } from "vite";

// Served from https://amirbukhari.github.io/RhythmRPG/ (a GitHub Pages
// project site, not a custom domain), so asset URLs need the repo-name base
// path in production. Local dev keeps root-relative paths.
const isGithubPagesBuild = process.env.GITHUB_PAGES === "true";

export default defineConfig({
  root: ".",
  base: isGithubPagesBuild ? "/RhythmRPG/" : "/",
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
});
