import os
import re

RICES_DIR = "rices"
README_PATH = "README.md"


def parse_frontmatter(content):
    match = re.match(r"^---\n(.*?)\n---\n?", content, re.DOTALL)
    if not match:
        return {}, content
    data = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            data[key.strip()] = val.strip()
    body = content[match.end():].strip()
    return data, body


def build_readme(rices):
    lines = [
        "# linux/unix rices",
        "",
        "A community collection of linux/unix desktop setups - curated and featured on [YouTube](https://www.youtube.com/@xpltt).",
        "",
        "Want to be featured? Read [CONTRIBUTING.md](CONTRIBUTING.md) and open a pull request.",
        "",
        "---",
        "",
        "## setups",
        "",
    ]

    if not rices:
        lines.append("*no submissions yet - be the first*")
    else:
        lines.append("| preview | author | wm / de | distro | video | dotfiles |")
        lines.append("|---------|--------|---------|--------|-------|----------|")

        for rice in rices:
            folder   = rice["folder"]
            author   = rice.get("author", folder)
            wm       = rice.get("wm", "-")
            distro   = rice.get("distro", "-")
            video    = rice.get("video", "").strip()
            dotfiles = rice.get("dotfiles", "").strip()

            screenshot_path = f"rices/{folder}/screenshot.png"
            has_shot = os.path.exists(screenshot_path)

            preview       = f'<img src="{screenshot_path}" width="220">' if has_shot else "-"
            author_cell   = f"[{author}](rices/{folder}/info.md)"
            video_cell    = f"[watch]({video})" if video else "-"
            dotfiles_cell = f"[link]({dotfiles})" if dotfiles else "-"

            lines.append(
                f"| {preview} | {author_cell} | {wm} | {distro} | {video_cell} | {dotfiles_cell} |"
            )

    lines += ["", "---", "", "*[↑ back to top](#linux-rices)*", ""]
    return "\n".join(lines)


def main():
    rices = []

    if not os.path.isdir(RICES_DIR):
        print("rices/ directory not found")
        return

    for folder in sorted(os.listdir(RICES_DIR)):
        info_path = os.path.join(RICES_DIR, folder, "info.md")
        if not os.path.isfile(info_path):
            continue
        with open(info_path) as f:
            content = f.read()
        data, _ = parse_frontmatter(content)
        data["folder"] = folder
        rices.append(data)

    readme = build_readme(rices)
    with open(README_PATH, "w") as f:
        f.write(readme)

    print(f"done - {len(rices)} rice(s) indexed")


if __name__ == "__main__":
    main()
