import os
import re
import subprocess
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RICES_DIR = os.path.join(BASE_DIR, "rices")
MAX_VIDEO_MB = 50
REQUIRED_FIELDS = ["author", "wm", "distro", "terminal", "shell", "description"]


def parse_frontmatter(content):
    match = re.match(r"^---\r?\n(.*?)\r?\n---", content.lstrip(), re.DOTALL)
    if not match:
        return {}
    data = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            data[key.strip()] = val.strip()
    return data


def changed_rice_folders(base_ref):
    """Only validate folders touched by this PR, so pre-existing bad
    submissions elsewhere in the repo don't fail unrelated PRs."""
    try:
        out = subprocess.run(
            ["git", "diff", "--name-only", f"{base_ref}...HEAD"],
            cwd=BASE_DIR, capture_output=True, text=True, check=True,
        ).stdout
    except subprocess.CalledProcessError as e:
        print(f"warning: git diff failed ({e}), falling back to all folders")
        out = ""

    folders = set()
    for path in out.splitlines():
        parts = path.split("/")
        if len(parts) >= 2 and parts[0] == "rices":
            folders.add(parts[1])

    if not folders and os.path.isdir(RICES_DIR):
        folders = {
            d for d in os.listdir(RICES_DIR)
            if os.path.isdir(os.path.join(RICES_DIR, d))
        }
    return sorted(folders)


def validate_folder(folder):
    errors = []
    path = os.path.join(RICES_DIR, folder)
    info_path = os.path.join(path, "info.md")
    video_path = os.path.join(path, "preview.mp4")
    shot_path = os.path.join(path, "screenshot.png")

    if not os.path.isdir(path):
        return [f"rices/{folder} does not exist (deleted or renamed?)"]

    allowed = {"info.md", "preview.mp4", "screenshot.png"}
    extra = set(os.listdir(path)) - allowed
    if extra:
        errors.append(f"unexpected files in folder: {', '.join(sorted(extra))}")

    if not os.path.isfile(info_path):
        errors.append("missing info.md")
        return errors

    with open(info_path, encoding="utf-8") as f:
        content = f.read()
    data = parse_frontmatter(content)

    if not data:
        errors.append("info.md has no valid frontmatter (missing --- block, or a leading blank line before it)")

    for field in REQUIRED_FIELDS:
        if not data.get(field, "").strip():
            errors.append(f"missing or empty '{field}:' in frontmatter")

    if not os.path.isfile(video_path):
        errors.append("missing preview.mp4")
    else:
        size_mb = os.path.getsize(video_path) / (1024 * 1024)
        if size_mb > MAX_VIDEO_MB:
            errors.append(f"preview.mp4 is {size_mb:.1f}MB, exceeds the {MAX_VIDEO_MB}MB limit")

    if not os.path.isfile(shot_path):
        errors.append("missing screenshot.png")

    video_field = data.get("video", "").strip()
    if video_field and re.match(r"https?://", video_field):
        errors.append("'video:' should be left empty in new submissions — it's filled in automatically after merge")

    return errors


def main():
    base_ref = sys.argv[1] if len(sys.argv) > 1 else "origin/main"
    folders = changed_rice_folders(base_ref)

    if not folders:
        print("no rices/** changes detected — nothing to validate")
        return

    had_errors = False
    for folder in folders:
        errors = validate_folder(folder)
        if errors:
            had_errors = True
            print(f"\n❌ rices/{folder}:")
            for e in errors:
                print(f"   - {e}")
        else:
            print(f"✅ rices/{folder}: looks good")

    if had_errors:
        print("\nsubmission validation failed — fix the issues above")
        sys.exit(1)
    print("\nall changed submissions passed validation")


if __name__ == "__main__":
    main()
