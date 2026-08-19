#!/usr/bin/env bash
# Push the corpus to Cloudflare KV.
#
# Nothing is mirrored: original scans stay at the source archive and the site
# links out to them. What ships is the browse indexes, the per-machine records
# and the rendered documents.
#
#   tools/publish.sh local  [docId ...]   seed the wrangler dev simulator
#   tools/publish.sh remote               push the whole corpus
set -euo pipefail
cd "$(dirname "$0")/.."

MODE="${1:-local}"; shift || true
if [ "$MODE" = "local" ]; then FLAG="--local"; WR="npx wrangler"; else FLAG="--remote"; WR="cf-run npx wrangler"; fi

kv() { $WR kv key put --binding INDEX $FLAG "$1" --path "$2" >/dev/null && echo "  KV  $1"; }

echo "== browse indexes"
kv machines data/index/machines.json
kv docs     data/index/docs.json
kv boards   data/boards.json
[ -f data/index/chips.json ] && kv chips data/index/chips.json
for f in data/index/postings/*.json; do
  [ -f "$f" ] && kv "p:$(basename "$f" .json)" "$f"
done

echo "== machine records + documents"
if [ "$MODE" = "remote" ]; then
  # Thousands of keys: bulk upload in chunks rather than one call per key.
  python3 tools/kv_bulk.py --out /tmp/crt-kv
  for chunk in /tmp/crt-kv/*.json; do
    $WR kv bulk put --binding INDEX $FLAG "$chunk" >/dev/null && echo "  bulk $(basename "$chunk")"
  done
else
  for slug in "${@:-pong asteroid breakout 1942 puckman}"; do
    [ -f "data/machine/$slug.json" ] && kv "m:$slug" "data/machine/$slug.json"
  done
  for did in "$@"; do
    [ -f "cache/text/$did.json" ] && kv "d:$did" "cache/text/$did.json"
  done
fi
echo "done."
