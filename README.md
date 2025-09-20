# cppref

A cli cpp manual pages for Linux/MacOS!

![Demostration](https://github.com/user-attachments/assets/c543f02e-6695-4749-b0ac-566a1bf598b6)

## ✨ Features

- 📁 XDG base directories support.
- 🔎 Interactive lookup powered by [fzf](https://github.com/junegunn/fzf).
- 💻 Properly rendered contents.
- 💪 Async download for improved performance.
- ⏳ Pretty progress bar for downloading.

## ⚡️ Requirements

- [fzf](https://github.com/junegunn/fzf) for interactive lookup.
- [playwright](https://github.com/microsoft/playwright-python) chromium driver for subcommands `fetch` and `cache`, i.e., not offline mode.

## 🚀 Getting Started

Install by [uv](https://docs.astral.sh/uv/)

```bash
uv tool install cppref
```

Downloading manual page database.

```bash
dbdir="${XDG_DATA_HOME:-$HOME/.local/share}/cppref"
mkdir -p "$dbdir"
wget -O "$dbdir/index.db" https://github.com/ZachVec/cppref/releases/latest/download/index.db
```

Downloading processed manual pages if cppref is going to be used in offline mode.

```bash
man3dir="${XDG_DATA_HOME:-$HOME/.local/share}/man/man3"
mkdir -p "$man3dir"
wget -O /tmp/man3_archive.tar.gz https://github.com/ZachVec/cppref/releases/latest/download/man3_archive.tar.gz
tar xzf /tmp/man3_archive.tar.gz -C "$man3dir"
```
