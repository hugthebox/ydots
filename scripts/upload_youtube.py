import os
import sys
import re
import mimetypes
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


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


def build_title(data):
    distro = data.get("distro", "linux").capitalize()
    wm     = data.get("wm", "unknown").capitalize()
    author = data.get("author", "unknown")
    return f"{distro} / {wm} / {author}"


def build_description(data):
    author      = data.get("author", "unknown")
    wm          = data.get("wm", "-")
    distro      = data.get("distro", "-")
    terminal    = data.get("terminal", "-")
    shell       = data.get("shell", "-")
    dotfiles    = data.get("dotfiles", "")
    description = data.get("description", "")

    tags_list = ["unixporn", "ricing", "linux", wm, distro, terminal, shell, author]
    hashtags  = " ".join(
        f"#{t.lower().replace(' ', '')}"
        for t in tags_list
        if t and t != "-"
    )

    parts = [
        f"{distro.capitalize()} / {wm.capitalize()} / {terminal} / {shell}",
        f"Dotfiles: {dotfiles}" if dotfiles else "",
        "",
        description,
        "",
        "─────────────────────────────",
        f"Submitted by {author} via github.com/jahamars/ydots",
        "",
        hashtags,
    ]

    return "\n".join(p for p in parts if p is not None)


def build_tags(data):
    wm       = data.get("wm", "")
    distro   = data.get("distro", "")
    terminal = data.get("terminal", "")
    shell    = data.get("shell", "")
    author   = data.get("author", "")
    base  = ["unixporn", "ricing", "linux", "rice", "desktop"]
    extra = [wm, distro, terminal, shell, author, f"{distro}linux", f"{wm}wm"]
    return base + [t for t in extra if t and t != "-"]


def upload(folder):
    info_path  = os.path.join(BASE_DIR, "rices", folder, "info.md")
    video_path = os.path.join(BASE_DIR, "rices", folder, "preview.mp4")
    thumb_path = os.path.join(BASE_DIR, "rices", folder, "screenshot.png")

    if not os.path.isfile(info_path):
        print(f"skipping {folder}: no info.md")
        return

    if not os.path.exists(video_path):
        print(f"skipping {folder}: no preview.mp4")
        return

    with open(info_path, encoding="utf-8") as f:
        content = f.read()

    data = parse_frontmatter(content)

    if data.get("video", "").strip():
        print(f"skipping {folder}: already uploaded ({data['video']})")
        return

    title       = build_title(data)
    description = build_description(data)
    tags        = build_tags(data)

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
        media_body=MediaFileUpload(video_path, chunksize=-1, resumable=True)
    ).execute()

    video_id  = response["id"]
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    print(f"uploaded: {video_url}")

    if os.path.exists(thumb_path):
        file_size_mb = os.path.getsize(thumb_path) / (1024 * 1024)
        if file_size_mb > 2.0:
            print(
                f"thumbnail skipped: screenshot.png is {file_size_mb:.2f} MB "
                f"(YouTube limit is 2 MB — compress it first)"
            )
        else:
            try:
                mime_type, _ = mimetypes.guess_type(thumb_path)
                youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(
                        thumb_path,
                        mimetype=mime_type or "image/png"
                    )
                ).execute()
                print("thumbnail set")
            except Exception as e:
                print(f"thumbnail skipped (verify channel in YouTube Studio): {e}")

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
        print("usage: upload_youtube.py <folder>")
        sys.exit(1)
    upload(sys.argv[1])
