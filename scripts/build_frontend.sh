#!/usr/bin/env bash
# Build the console and sync the hashed bundle into the directory FastAPI serves.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$REPO_ROOT/web/frontend"
STATIC_DIR="$REPO_ROOT/web/static"

cd "$FRONTEND_DIR"
[ -d node_modules ] || npm ci
rm -rf dist
npm run build

# Asset filenames are content-hashed, so stale bundles must go or index.html
# will keep pointing at a file that no longer matches the source.
rm -rf "$STATIC_DIR/assets"
mkdir -p "$STATIC_DIR"
cp -R dist/. "$STATIC_DIR/"

echo "Synced $(ls "$STATIC_DIR/assets" | tr '\n' ' ')-> web/static"
