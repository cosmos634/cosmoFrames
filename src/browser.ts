#!/usr/bin/env node
/** Optional Chromium/CDP renderer. Requires playwright-core and a running CDP browser. */
import { existsSync, readFileSync, mkdirSync, statSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { pathToFileURL } from "node:url";
import { spawn, type ChildProcessByStdio } from "node:child_process";
import type { Writable } from "node:stream";
import { once } from "node:events";

type Track = { src: string; start?: number; volume?: number };
type Project = {
  resolution: { width: number; height: number };
  fps?: number;
  duration?: number;
  output?: string;
  browser_entry?: string;
  audio?: string;
  audio_tracks?: Track[];
};

function fail(message: string): never {
  console.error("ERROR: " + message);
  process.exit(1);
}

type EncoderProcess = ChildProcessByStdio<Writable, null, null>;

async function waitForClose(proc: EncoderProcess): Promise<number> {
  return await new Promise((resolveCode, reject) => {
    proc.once("error", reject);
    proc.once("close", code => resolveCode(code ?? 1));
  });
}

async function writeFrame(proc: EncoderProcess, bytes: Buffer): Promise<void> {
  if (proc.stdin.destroyed) throw new Error("FFmpeg input pipe is closed.");
  if (!proc.stdin.write(bytes)) {
    await Promise.race([
      once(proc.stdin, "drain"),
      once(proc.stdin, "close").then(() => { throw new Error("FFmpeg closed its input pipe."); })
    ]);
  }
}

async function main(): Promise<void> {
  const projectPath = process.argv[2];
  if (!projectPath) fail("Usage: cosmoframes render-browser <project.json>");
  const absoluteProject = resolve(projectPath);
  if (!existsSync(absoluteProject)) fail("Project file not found: " + absoluteProject);
  let project: Project;
  try { project = JSON.parse(readFileSync(absoluteProject, "utf8")) as Project; }
  catch (error) { fail("Invalid project JSON: " + String(error)); }
  if (!project || typeof project !== "object") fail("Project JSON root must be an object.");
  if (typeof project.browser_entry !== "string" || !project.browser_entry.trim())
    fail('Browser project requires "browser_entry": "scene.html".');
  const base = dirname(absoluteProject);
  const entry = resolve(base, project.browser_entry);
  if (!existsSync(entry)) fail("Browser entry file not found: " + entry);
  const width = project.resolution?.width;
  const height = project.resolution?.height;
  const fps = project.fps ?? 30;
  const duration = project.duration ?? 5;
  if (!Number.isInteger(width) || !Number.isInteger(height) || width! < 1 || height! < 1 ||
      width! * height! > 8294400) fail("Invalid resolution or frame size exceeds 8.3 megapixels.");
  if (!Number.isFinite(fps) || !(fps > 0 && fps <= 60) ||
      !Number.isFinite(duration) || !(duration > 0 && duration <= 600))
    fail("FPS or duration is outside supported limits.");
  if (project.output !== undefined && (typeof project.output !== "string" || !project.output.trim()))
    fail("output must be a non-empty path string.");
  const ffmpeg = process.env.COSMOFRAMES_FFMPEG || "ffmpeg";
  const output = resolve(base, project.output || "browser-output.mp4");
  mkdirSync(dirname(output), { recursive: true });
  const tracks = [...(project.audio_tracks || [])];
  if (project.audio) tracks.unshift({ src: project.audio, start: 0, volume: 1 });
  for (let i = 0; i < tracks.length; i++) {
    const track = tracks[i];
    if (!track || typeof track.src !== "string" || !track.src.trim())
      fail("audio_tracks[" + i + "].src must be a non-empty path.");
    if (track.start !== undefined && (!Number.isFinite(track.start) || track.start < 0))
      fail("audio_tracks[" + i + "].start must be a non-negative number.");
    if (track.volume !== undefined && (!Number.isFinite(track.volume) || track.volume < 0 || track.volume > 4))
      fail("audio_tracks[" + i + "].volume must be between 0 and 4.");
  }
  const args = ["-y", "-loglevel", "error", "-f", "image2pipe", "-vcodec", "png",
    "-framerate", String(fps), "-i", "-"];
  const filters: string[] = [];
  const labels: string[] = [];
  for (let i = 0; i < tracks.length; i++) {
    const track = tracks[i];
    const audioPath = resolve(base, track.src);
    if (!existsSync(audioPath)) fail("Audio file not found: " + audioPath);
    args.push("-i", audioPath);
    const label = "a" + i;
    filters.push("[" + (i + 1) + ":a]atrim=duration=" + duration +
      ",asetpts=PTS-STARTPTS,adelay=" + Math.round((track.start || 0) * 1000) +
      ":all=1,volume=" + (track.volume ?? 1) + "[" + label + "]");
    labels.push("[" + label + "]");
  }
  if (labels.length === 1) filters.push(labels[0] + "anull[aout]");
  if (labels.length > 1) filters.push(labels.join("") + "amix=inputs=" + labels.length +
    ":duration=longest:dropout_transition=0[aout]");
  if (filters.length) args.push("-filter_complex", filters.join(";"), "-map", "0:v:0", "-map", "[aout]", "-c:a", "aac");
  else args.push("-an");
  args.push("-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
    "-movflags", "+faststart", "-t", String(duration), output);

  let chromium: any;
  try { ({ chromium } = await import("playwright-core")); }
  catch { fail("Optional dependency missing. Install it with: npm install playwright-core"); }
  const cdp = process.env.COSMOFRAMES_CDP_URL || "http://127.0.0.1:9222";
  let browser: any;
  try { browser = await chromium.connectOverCDP(cdp, { timeout: 5000 }); }
  catch { fail("Cannot connect to Chromium CDP at " + cdp +
    ". Start Chromium with --remote-debugging-port=9222 or set COSMOFRAMES_CDP_URL."); }
  let proc: EncoderProcess | undefined;
  try {
    const context = browser.contexts()[0] || await browser.newContext();
    const page = await context.newPage();
    await page.setViewportSize({ width, height });
    await page.goto(pathToFileURL(entry).href, { waitUntil: "load" });
    await page.evaluate(async () => { if (document.fonts?.ready) await document.fonts.ready; });
    proc = spawn(ffmpeg, args, { stdio: ["pipe", "ignore", "inherit"] });
    await once(proc, "spawn");
    const completion = waitForClose(proc).then(
      code => ({ code }),
      error => ({ error })
    );
    const frames = Math.ceil(duration * fps);
    console.log("Browser rendering %d frames at %dx%d %.2f FPS", frames, width, height, fps);
    const started = Date.now();
    for (let index = 0; index < frames; index++) {
      const time = index / fps;
      await page.evaluate(async ({ time, index }: { time: number; index: number }) => {
        const target = (window as any).cosmoframesRender || (window as any).renderAt;
        if (typeof target === "function") await target(time, index);
        for (const animation of document.getAnimations()) {
          animation.pause();
          animation.currentTime = time * 1000;
        }
      }, { time, index });
      const png = await page.screenshot({ type: "png", animations: "allow" });
      await writeFrame(proc, png);
      if (index && index % Math.max(1, Math.floor(fps * 2)) === 0)
        console.log("Progress: %d/%d frames", index, frames);
    }
    proc.stdin.end();
    const finished = await completion;
    if ("error" in finished) fail("FFmpeg process failed: " + String(finished.error));
    if (finished.code !== 0) fail("FFmpeg exited with code " + finished.code);
    if (!existsSync(output) || statSync(output).size === 0) fail("MP4 output was not created or is empty.");
    console.log("Created %s (%d bytes) in %.1fs", output,
      statSync(output).size, (Date.now() - started) / 1000);
    await page.close();
  } finally {
    if (proc && !proc.stdin.destroyed) proc.stdin.destroy();
    await browser.close().catch(() => undefined);
  }
}

main().catch(error => fail(String(error)));
