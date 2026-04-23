## Setup commands

### Core

```
uv sync
uv run main.py
```

Exposed an API server on `http://localhost:6185` by default.

### Dashboard(WebUI)

```
cd dashboard
pnpm install # First time only. Use npm install -g pnpm if pnpm is not installed.
pnpm dev
```

Runs on `http://localhost:3000` by default.

## Dev environment tips

1. When modifying the WebUI, be sure to maintain componentization and clean code. Avoid duplicate code.
2. Do not add any report files such as xxx_SUMMARY.md.
3. After finishing, use `ruff format .` and `ruff check .` to format and check the code.
4. When committing, ensure to use conventional commits messages, such as `feat: add new agent for data analysis` or `fix: resolve bug in provider manager`.
5. Use English for all new comments.
6. For path handling, use `pathlib.Path` instead of string paths, and use `astrbot.core.utils.path_utils` to get the AstrBot data and temp directory.

## PR instructions

1. Title format: use conventional commit messages
2. Use English to write PR title and descriptions.

## Local Vendor Boundary

1. This repo is now a vendor-style AstrBot checkout that should stay as close to upstream as possible.
2. Do not add long-lived product customizations here. `auto route`, `Kimi search injection`, custom config fields, and custom WebUI toggles belong in `/Users/davidl/Documents/Codex/AstrBot-custom`.
3. The only acceptable long-lived local diff here is a thin, generic compatibility patch that is still needed at runtime.
4. If a patch can be upstreamed or removed by moving logic into a plugin, prefer that over growing local core drift.

## Upgrade Workflow

1. Do not use the WebUI zip updater for this local deployment path.
2. Upgrade this repo by Git against official upstream tags, then re-apply the approved thin patches.
3. The default local entrypoint for upgrades is `/Users/davidl/Documents/Codex/AstrBot-custom/scripts/update_astrbot_vendor.sh`.
4. After updating, re-link plugins from `/Users/davidl/Documents/Codex/AstrBot-custom`, restart `com.davidl.astrbot`, then verify `curl http://127.0.0.1:8787/healthz`.

## Patch Discipline

1. Keep patches small, generic, and test-backed.
2. Current approved thin-patch classes are:
   - reasoning-only visible fallback
   - `qwen3-rerank` payload compatibility
3. Debug-only local instrumentation should not be kept here by default. If it must stay, isolate it as a clearly justified patch.
4. Do not silently commit unrelated local helper scripts or runtime artifacts.
