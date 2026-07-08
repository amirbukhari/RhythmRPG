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
  },
});
