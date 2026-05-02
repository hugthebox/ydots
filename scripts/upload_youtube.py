import os
import sys
import re
import mimetypes
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RICES_DIR = os.path.join(BASE_DIR, "rices")

TITLE_TEMPLATES = [
    "{wm} rice 2025 | {distro} linux | {author}",
    "{distro} / {wm} desktop rice | {author}",
    "the most aesthetic {wm} setup | {distro} linux",
    "{wm} + {distro} | linux rice 2025",
]


def get_youtube():
    creds = Credentials(
        token=None,
        refresh_token=os.environ["YOUTUBE_REFRESH_TOKEN"],
        client_id=os.environ["YOUTUBE_CLIENT_ID"],
        client_secret=os.environ["YOUTUBE_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
    )
    creds.refresh(Request())
    return build("youtube", "v3", credentials=creds)


def parse_frontmatter(content):
    match = re.match(r"^---\r?\n(.*?)\r?\n---", content, re.DOTALL)
    if not match:
        return {}
    data = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            data[k.strip()] = v.strip()
    return data


def folder_index(folder):
    folders = sorted(
        d for d in os.listdir(RICES_DIR)
        if os.path.isdir(os.path.join(RICES_DIR, d))
    )
    try:
        return folders.index(folder)
    except ValueError:
        return 0


def build_title(data, folder):
    wm = data.get("wm", "unknown")
    distro = data.get("distro", "linux")
    author = data.get("author", "unknown")
    idx = folder_index(folder) % len(TITLE_TEMPLATES)
    return TITLE_TEMPLATES[idx].format(wm=wm, distro=distro, author=author)


def build_description(data):
    author = data.get("author", "unknown")
    wm = data.get("wm", "-")
    distro = data.get("distro", "-")
    terminal = data.get("terminal", "-")
    shell = data.get("shell", "-")
    dotfiles = data.get("dotfiles", "").strip()
    description = data.get("description", "").strip()

    wm_clean = wm.lower().replace(" ", "")
    distro_clean = distro.lower().replace(" ", "")

    raw_hashtags = [
        f"#{wm_clean}",
        f"#{distro_clean}linux",
        "#linuxrice",
        "#unixporn",
        "#ricing2025",
        "#dotfiles",
        "#desktopsetup",
    ]
    seen = set()
    hashtags = []
    for h in raw_hashtags:
        if h not in seen:
            seen.add(h)
            hashtags.append(h)
    hashtag_line = " ".join(hashtags)

    parts = []
    if description:
        parts.append(description)
        parts.append("")
    parts.append(f"wm/de: {wm}")
    parts.append(f"distro: {distro}")
    parts.append(f"terminal: {terminal}")
    parts.append(f"shell: {shell}")
    if dotfiles:
        url = dotfiles if dotfiles.startswith("http") else f"https://{dotfiles}"
        parts.append("")
        parts.append(url)
    parts.append("")
    parts.append("─────────────────────────────")
    parts.append(f"submitted by {author}")
    parts.append("https://github.com/jahamars/ydots")
    parts.append("")
    parts.append(hashtag_line)

    return "\n".join(parts)


def build_tags(data):
    wm = data.get("wm", "")
    distro = data.get("distro", "")
    author = data.get("author", "")
    base = [
        "linux rice",
        "unixporn",
        "ricing",
        "dotfiles",
        f"{wm} rice",
        f"{wm} dotfiles",
        f"{distro} linux",
        author,
    ]
    tags = [t for t in base if t and t != "-"]
    result = []
    total = 0
    for t in tags:
        if total + len(t) + (1 if result else 0) > 490:
            break
        result.append(t)
        total += len(t) + (1 if len(result) > 1 else 0)
    return result


def upload(folder):
    info_path = os.path.join(RICES_DIR, folder, "info.md")
    video_path = os.path.join(RICES_DIR, folder, "preview.mp4")
    thumb_path = os.path.join(RICES_DIR, folder, "screenshot.png")

    if not os.path.isfile(info_path):
        print(f"skipping {folder}: no info.md")
        return

    if not os.path.exists(video_path):
        print(f"skipping {folder}: no preview.mp4")
        return

    with open(info_path, encoding="utf-8") as f:
        content = f.read()

    data = parse_frontmatter(content)

    video_field = data.get("video", "").strip()
    if re.match(r"https?://", video_field):
        print(f"skipping {folder}: already uploaded ({video_field})")
        return

    title = build_title(data, folder)
    description = build_description(data)
    tags = build_tags(data)

    youtube = get_youtube()

    print(f"uploading: {title}")
    response = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": "28",
            },
            "status": {"privacyStatus": "public"},
        },
        media_body=MediaFileUpload(video_path, chunksize=-1, resumable=True),
    ).execute()

    video_id = response["id"]
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    print(f"uploaded: {video_url}")

    if os.path.exists(thumb_path):
        file_size_mb = os.path.getsize(thumb_path) / (1024 * 1024)
        if file_size_mb > 2.0:
            print(
                f"thumbnail skipped: screenshot.png is {file_size_mb:.2f} MB "
                f"(YouTube limit is 2 MB)"
            )
        else:
            try:
                mime_type, _ = mimetypes.guess_type(thumb_path)
                youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(
                        thumb_path, mimetype=mime_type or "image/png"
                    ),
                ).execute()
                print("thumbnail set")
            except Exception as e:
                print(f"thumbnail skipped: {e}")

    new_content = re.sub(
        r"^video:.*$",
        f"video: {video_url}",
        content,
        flags=re.MULTILINE,
    )

    with open(info_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"done: {folder}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: upload_youtube.py <folder> | --all")
        sys.exit(1)

    if sys.argv[1] == "--all":
        for name in sorted(os.listdir(RICES_DIR)):
            if os.path.isdir(os.path.join(RICES_DIR, name)):
                upload(name)
    else:
        upload(sys.argv[1])
