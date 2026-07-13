#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="$ROOT_DIR/backup"
OUTPUT_FILE="$OUTPUT_DIR/db.json"
MEDIA_ARCHIVE="$OUTPUT_DIR/media.tar.gz"

mkdir -p "$OUTPUT_DIR"

echo "Creating database fixture at $OUTPUT_FILE"
docker compose exec -T web python CorpMarket/manage.py dumpdata \
  users adverts chats reviews \
  --indent 2 \
  --natural-foreign \
  --natural-primary \
  > "$OUTPUT_FILE"

echo "Archiving media to $MEDIA_ARCHIVE"
tar -czf "$MEDIA_ARCHIVE" -C "$ROOT_DIR/CorpMarket" media

echo "Done"
