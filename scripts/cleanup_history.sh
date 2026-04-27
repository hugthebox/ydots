set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

echo "━━━ BEFORE cleanup ━━━"
echo "  .git size: $(du -sh .git | cut -f1)"
echo "  total repo: $(du -sh . | cut -f1)"
echo ""

if ! command -v git-filter-repo &>/dev/null; then
    echo "ERROR: git-filter-repo not found."
    echo "Install it:  pip install git-filter-repo"
    exit 1
fi

echo "Purging all *.mp4, *.mkv, *.avi, *.mov, *.webm blobs from history..."
echo ""

git filter-repo \
    --invert-paths \
    --path-glob '*.mp4' \
    --path-glob '*.mkv' \
    --path-glob '*.avi' \
    --path-glob '*.mov' \
    --path-glob '*.webm' \
    --force

echo ""
echo "Running aggressive GC..."
git reflog expire --expire=now --all
git gc --prune=now --aggressive

echo ""
echo "━━━ AFTER cleanup ━━━"
echo "  .git size: $(du -sh .git | cut -f1)"
echo "  total repo: $(du -sh . | cut -f1)"

echo ""
echo "✅ Done! Now force-push:"
echo "   git remote add origin <your-remote-url>"
echo "   git push origin main --force"
echo ""
echo "⚠️  All collaborators must re-clone the repo after this."
