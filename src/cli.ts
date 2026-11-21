#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { resolve, dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const py = process.env.COSMOFRAMES_PYTHON || "python";
const args = process.argv.slice(2);
const command = args[0] || "help";
function runPython(action: string, project?: string, extra: string[] = []): void {
  const script = join(root, "python", "engine.py");
  if (!existsSync(script)) { console.error("Python engine not found. Run from the project directory."); process.exit(1); }
  const result = spawnSync(py, [script, action, ...(project ? [resolve(project)] : []), ...extra], { stdio: "inherit", env: process.env });
  if (result.error) { console.error("Unable to start Python: " + result.error.message); process.exit(1); }
  process.exit(result.status ?? 1);
}
function help(): void {
  console.log("CosmoFrames 1.0\nUsage:\n  cosmoframes info\n  cosmoframes init <name>\n  cosmoframes validate <project.json>\n  cosmoframes preview <project.json> [--time seconds]\n  cosmoframes render <project.json>\n\nSet COSMOFRAMES_PYTHON to choose the Python executable.");
}
switch (command) {
  case "info": runPython("info"); break;
  case "init": if (!args[1]) { console.error("Usage: cosmoframes init <name>"); process.exit(2); } runPython("init", undefined, [args[1]]); break;
  case "validate":
  case "render": if (!args[1]) { console.error("Usage: cosmoframes " + command + " <project.json>"); process.exit(2); } runPython(command, args[1]); break;
  case "preview": if (!args[1]) { console.error("Usage: cosmoframes preview <project.json> [--time seconds]"); process.exit(2); } runPython("preview", args[1], args.slice(2)); break;
  case "help": case "--help": case "-h": help(); break;
  default: console.error("Unknown command: " + command); help(); process.exit(2);
}
