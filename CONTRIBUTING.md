# contributing

## what to submit

Each rice lives in its own folder inside `rices/`. Your folder should contain exactly three files:

```
rices/your-username/
├── info.md         ← metadata + description
├── preview.mp4     ← screen recording, minimum 30 seconds
└── screenshot.png  ← a single clean screenshot for the table
```

## how to submit

1. Fork this repo
2. Create `rices/your-username/` and add your three files
3. Fill out `info.md` using the template below
4. Open a pull request

The README updates automatically once your PR is merged.

## video requirements

- Minimum **30 seconds** long
- `.mp4` format
- Show your actual desktop — not just a static wallpaper
- Keep the file under **50 MB**

> After your PR is merged, the video gets uploaded to the YouTube channel with full credit to you.

## info.md template
```md
---
author: your-github-username
wm: hyprland
distro: arch
terminal: kitty
shell: zsh
dotfiles: https://github.com/you/dotfiles
video:
description: Describe your setup in a few sentences. What's the vibe? Any custom configs worth mentioning?
---

<video src="./preview.mp4" controls width="100%"></video>
```

## questions

Open an issue.
