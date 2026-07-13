#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT_DIR="${1:-$ROOT_DIR/backup}"
INPUT_FILE="$INPUT_DIR/db.json"
MEDIA_ARCHIVE="$INPUT_DIR/media.tar.gz"

if [[ ! -f "$INPUT_FILE" ]]; then
  echo "Fixture file not found: $INPUT_FILE" >&2
  exit 1
fi

if [[ ! -f "$MEDIA_ARCHIVE" ]]; then
  echo "Media archive not found: $MEDIA_ARCHIVE" >&2
  exit 1
fi

echo "Loading fixture from $INPUT_FILE"
cat "$INPUT_FILE" | docker compose exec -T web python CorpMarket/manage.py loaddata --format=json -

echo "Restoring media from $MEDIA_ARCHIVE"
tar -xzf "$MEDIA_ARCHIVE" -C "$ROOT_DIR/CorpMarket"

echo "Done"
