set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RICES_DIR="$REPO_ROOT/rices"
deleted=0
skipped=0

echo "Scanning for uploaded preview.mp4 files..."
echo ""

for folder in "$RICES_DIR"/*/; do
    name=$(basename "$folder")
    info="$folder/info.md"
    video="$folder/preview.mp4"

    if [ ! -f "$video" ]; then
        continue
    fi

    if [ ! -f "$info" ]; then
        echo "$name: has preview.mp4 but no info.md — skipping"
        skipped=$((skipped + 1))
        continue
    fi

    if grep -qE '^video:\s*https?://.*youtube\.com' "$info"; then
        size=$(du -h "$video" | cut -f1)
        echo "$name: deleting preview.mp4 ($size) — already on YouTube"
        rm "$video"

        video_url=$(grep -oP '^video:\s*\K(https?://\S+)' "$info" || true)
        if [ -n "$video_url" ]; then
            video_id=$(echo "$video_url" | grep -oP 'v=\K[^&]+' || true)
            if [ -n "$video_id" ]; then
                sed -i "s|<video src=\"./preview.mp4\"[^>]*>.*</video>|[![preview](https://img.youtube.com/vi/${video_id}/maxresdefault.jpg)](${video_url})|g" "$info"
            fi
        fi

        deleted=$((deleted + 1))
    else
        echo "  ⏭  $name: preview.mp4 exists but NOT yet uploaded — keeping"
        skipped=$((skipped + 1))
    fi
done

echo ""
echo "━━━ Summary ━━━"
echo "  Deleted: $deleted video(s)"
echo "  Skipped: $skipped video(s)"

if [ "$deleted" -gt 0 ]; then
    echo ""
    echo "Now commit the changes:"
    echo "  git add -A rices/"
    echo "  git commit -m 'chore: remove uploaded preview.mp4 files'"
fi
