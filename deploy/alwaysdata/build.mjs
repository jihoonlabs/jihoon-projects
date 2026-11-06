import {
  cp,
  mkdir,
  mkdtemp,
  readFile,
  readdir,
  writeFile,
} from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { execFileSync } from "node:child_process";

const repo = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "../..",
);
const run = (cmd, args, options = {}) =>
  execFileSync(cmd, args, { cwd: repo, stdio: "inherit", ...options });
const pendingChanges = execFileSync(
  "git",
  ["status", "--porcelain", "--untracked-files=all"],
  {
    cwd: repo,
    encoding: "utf8",
  },
).trim();
if (pendingChanges) {
  throw new Error(
    "Commit all release changes and clean the worktree before building.",
  );
}
const output = await mkdtemp(path.join(tmpdir(), "ticket-alwaysdata-"));
const release = path.join(output, "ticket-demo");
await mkdir(release);

// 同一originの相対URLをビルド時に固定。秘密値をフロントへ渡さない。
run("pnpm", ["exec", "next", "build"], {
  cwd: path.join(repo, "react"),
  env: {
    ...process.env,
    TICKET_STATIC_EXPORT: "true",
    NEXT_PUBLIC_API_URL: "",
    NEXT_PUBLIC_DEMO_MODE: "true",
  },
});

// 配布対象を明示し、.env・DB・ログ・private資料をコピーしない。
const sourceFiles = execFileSync("git", ["ls-files", "-z", "--", "laravel"], {
  cwd: repo,
  encoding: "utf8",
})
  .split("\0")
  .filter(Boolean);
const allowed =
  /^(app\/|bootstrap\/app\.php$|bootstrap\/providers\.php$|config\/|database\/migrations\/|database\/seeders\/DemoSeeder\.php$|public\/|resources\/views\/|routes\/|artisan$|composer\.(json|lock)$)/;
for (const file of sourceFiles) {
  const relative = file.slice("laravel/".length);
  if (
    !allowed.test(relative) ||
    relative.startsWith("public/storage/") ||
    relative.startsWith("public/build/")
  )
    continue;
  const dest = path.join(release, relative);
  await mkdir(path.dirname(dest), { recursive: true });
  await cp(path.join(repo, file), dest);
}
for (const dir of [
  "bootstrap/cache",
  "storage/app/private",
  "storage/app/public",
  "storage/framework/cache/data",
  "storage/framework/sessions",
  "storage/framework/views",
  "storage/logs",
]) {
  await mkdir(path.join(release, dir), { recursive: true });
}
await cp(path.join(repo, "react/out"), path.join(release, "public"), {
  recursive: true,
});
await cp(
  path.join(repo, "deploy/alwaysdata/.htaccess"),
  path.join(release, "public/.htaccess"),
);
await cp(
  path.join(repo, "deploy/alwaysdata/env.example"),
  path.join(release, ".env.example"),
);
await cp(
  path.join(repo, "docs/ticket/manual/deployment-alwaysdata.md"),
  path.join(output, "README.md"),
);
const sha = execFileSync("git", ["rev-parse", "HEAD"], {
  cwd: repo,
  encoding: "utf8",
}).trim();
await writeFile(path.join(output, "SOURCE.txt"), `${sha}\n`);
// 必須ファイルを確認。PHP依存は配布先でlockfileから導入する。
for (const file of [
  "public/index.php",
  "public/login/index.html",
  "public/tickets/index.html",
  "database/seeders/DemoSeeder.php",
])
  await readFile(path.join(release, file));
const files = await readdir(release);
if (files.includes(".env")) throw new Error("Unexpected .env in release");
run("tar", [
  "-czf",
  path.join(output, "ticket-demo.tar.gz"),
  "-C",
  output,
  "ticket-demo",
  "README.md",
  "SOURCE.txt",
]);
console.log(`Release: ${output}/ticket-demo.tar.gz`);
console.log(
  "Upload only this archive. Do not upload the repository or node_modules.",
);
