const test = require("node:test");
const assert = require("node:assert/strict");
const { spawnSync } = require("node:child_process");
const { mkdtempSync, existsSync, rmSync } = require("node:fs");
const { tmpdir } = require("node:os");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const cli = path.join(root, "dist/cli.js");

function run(args) {
  return spawnSync(process.execPath, [cli, ...args], {
    cwd: root,
    encoding: "utf8"
  });
}

test("CLI help exits successfully", () => {
  const result = run(["--help"]);
  assert.equal(result.status, 0);
  assert.match(result.stdout, /cosmoframes info/);
});

test("CLI info reports renderer dependencies", () => {
  const result = run(["info"]);
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /CosmoFrames/);
  assert.match(result.stdout, /Pillow/);
});

test("CLI init creates a project that validates", () => {
  const temp = mkdtempSync(path.join(tmpdir(), "cosmoframes-test-"));
  const projectDir = path.join(temp, "sample", "project");
  try {
    const created = run(["init", projectDir]);
    assert.equal(created.status, 0, created.stderr);
    assert.ok(existsSync(path.join(projectDir, "project.json")));
    const validated = run(["validate", path.join(projectDir, "project.json")]);
    assert.equal(validated.status, 0, validated.stderr);
    assert.match(validated.stdout, /Valid project/);
  } finally {
    rmSync(temp, { recursive: true, force: true });
  }
});

test("CLI rejects unknown commands", () => {
  const result = run(["not-a-command"]);
  assert.equal(result.status, 2);
  assert.match(result.stderr, /Unknown command/);
});
