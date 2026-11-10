#!/usr/bin/env python3
"""Check every skin in skins/, write the gallery into README.md, and pack
each skin as dist/<id>.plinthskin.

    python3 scripts/skins.py check     # check skins; fail if README.md is stale
    python3 scripts/skins.py gallery   # check skins and rewrite the gallery
    python3 scripts/skins.py pack      # check skins and write dist/*.plinthskin

Needs only Python 3. The rules follow Plinth's skin format:
https://github.com/rubycatco/plinth/blob/main/docs/SKINS.md
"""
import json
import os
import re
import struct
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKINS = os.path.join(ROOT, "skins")
README = os.path.join(ROOT, "README.md")
DIST = os.path.join(ROOT, "dist")
RELEASE = "https://github.com/rubycatco/plinth-skins/releases/latest/download"

# KnockSynth.voices, in Plinth's Sources/PlinthCore/KnockSynth.swift.
VOICES = {"wood", "lacquer", "ink", "cartoon", "pixel", "jade", "bowl", "key",
          "bamboo", "stone", "piston", "crt", "bead", "plate", "porcelain",
          "bell", "stamp", "chime", "board", "ceramic", "temple"}
LICENSES = {"CC0-1.0", "CC-BY-4.0"}
FRAMES = re.compile(r"^(idle|blink|hit)(-[1-9][0-9]*)?\.png$")
OTHER = {"mallet.png", "impact.png", "skin.json"}
MAX_BYTES = 3 * 1024 * 1024
START, END = "<!-- gallery:start -->", "<!-- gallery:end -->"


def png_size(path):
    """Width, height and whether the PNG can be transparent, from its header."""
    with open(path, "rb") as f:
        head = f.read(33)
    if head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
        return None
    width, height, _, color = struct.unpack(">IIBB", head[16:26])
    return width, height, color in (4, 6)  # gray+alpha, RGBA


def check(skin):
    """The problems with skins/<skin>, and its skin.json."""
    folder = os.path.join(SKINS, skin)
    problems = []
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", skin):
        problems.append("folder name: use lowercase letters, digits and hyphens")
    files = sorted(os.listdir(folder))
    total = 0
    for name in files:
        path = os.path.join(folder, name)
        if os.path.islink(path) or os.path.isdir(path):
            problems.append(f"{name}: only files, no folders or links")
            continue
        total += os.path.getsize(path)
        if not (FRAMES.match(name) or name in OTHER):
            problems.append(f"{name}: not part of a skin")
    if total > MAX_BYTES:
        problems.append(f"skin is {total // 1024} KB; keep it under {MAX_BYTES // 1024 // 1024} MB")
    if "idle.png" not in files:
        problems.append("idle.png is missing")
    sizes = {}
    for name in files:
        if name.endswith(".png") and not os.path.islink(os.path.join(folder, name)):
            info = png_size(os.path.join(folder, name))
            if info is None:
                problems.append(f"{name}: not a PNG")
                continue
            w, h, alpha = info
            if w != h:
                problems.append(f"{name}: {w}x{h} is not square")
            if not alpha:
                problems.append(f"{name}: needs a transparent background (an alpha channel)")
            if FRAMES.match(name):
                sizes[name] = w
    if len(set(sizes.values())) > 1:
        problems.append(f"frames differ in size: {sizes}")
    for seq in ("blink", "hit"):
        numbered = sorted(int(m.group(1)) for n in files if (m := re.fullmatch(seq + r"-(\d+)\.png", n)))
        if numbered and f"{seq}.png" in files:
            problems.append(f"{seq}.png and {seq}-N.png: use one or the other")
        if numbered and numbered != list(range(1, len(numbered) + 1)):
            problems.append(f"{seq}-N.png: number from 1 with no gaps")

    meta = {}
    try:
        with open(os.path.join(folder, "skin.json"), encoding="utf-8") as f:
            meta = json.load(f)
    except FileNotFoundError:
        problems.append("skin.json is missing")
    except ValueError as e:
        problems.append(f"skin.json is not valid JSON: {e}")
    if not isinstance(meta, dict):
        problems.append("skin.json must be an object")
        meta = {}
    for key in ("name", "author"):
        if not isinstance(meta.get(key), str) or not meta[key].strip():
            problems.append(f"skin.json: \"{key}\" is required")
    names = meta.get("names")
    if names is not None and not (isinstance(names, dict) and names
                                  and all(isinstance(v, str) and v.strip() for v in names.values())):
        problems.append("skin.json: \"names\" must map language codes to names, such as {\"zh-Hans\": \"纸鹤\"}")
    if meta.get("license") not in LICENSES:
        problems.append(f"skin.json: \"license\" must be one of {sorted(LICENSES)}")
    if "voice" in meta and meta["voice"] not in VOICES:
        problems.append(f"skin.json: \"voice\" must be one of {sorted(VOICES)}")
    strike = meta.get("strike")
    if strike is not None and not (isinstance(strike, list) and len(strike) == 2
                                   and all(isinstance(v, (int, float)) and 0 <= v <= 1 for v in strike)):
        problems.append("skin.json: \"strike\" must be two numbers between 0 and 1")
    if "likeness" in meta and not str(meta["likeness"]).startswith("https://"):
        problems.append("skin.json: \"likeness\" must link to the person's consent")
    return problems, meta


def all_skins():
    names = sorted(n for n in os.listdir(SKINS) if os.path.isdir(os.path.join(SKINS, n))) if os.path.isdir(SKINS) else []
    skins, failed = [], False
    for name in names:
        problems, meta = check(name)
        for p in problems:
            print(f"skins/{name}: {p}", file=sys.stderr)
        failed |= bool(problems)
        skins.append((name, meta))
    if failed:
        sys.exit(1)
    return skins


def gallery(skins):
    if not skins:
        return "No skins yet. [Add the first one](CONTRIBUTING.md)."
    rows = ["| | Skin | By | Knock | |", "| :-: | --- | --- | --- | --- |"]
    for name, meta in skins:
        voice = meta.get("voice", "wood")
        author = meta["author"].replace("|", "\\|")
        # The name, then its names in other languages.
        others = meta.get("names", {})
        title = " · ".join([f"**{meta['name']}**"] + [others[k] for k in sorted(others)]).replace("|", "\\|")
        rows.append(f'| <img src="skins/{name}/idle.png" width="120" alt=""> | {title} | {author} | '
                    f"`{voice}` | [Download]({RELEASE}/{name}.plinthskin) |")
    return "\n".join(rows)


def readme_with(table):
    text = open(README, encoding="utf-8").read()
    before, rest = text.split(START, 1)
    _, after = rest.split(END, 1)
    return f"{before}{START}\n{table}\n{END}{after}"


def pack(skins):
    os.makedirs(DIST, exist_ok=True)
    for name, _ in skins:
        out = os.path.join(DIST, f"{name}.plinthskin")
        # The skin folder itself, as `ditto -c -k --keepParent` makes it.
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for file in sorted(os.listdir(os.path.join(SKINS, name))):
                z.write(os.path.join(SKINS, name, file), f"{name}/{file}")
        print(out)


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else "check"
    skins = all_skins()
    wanted = readme_with(gallery(skins))
    if command == "gallery":
        open(README, "w", encoding="utf-8").write(wanted)
    elif command == "pack":
        pack(skins)
    elif command == "check":
        if open(README, encoding="utf-8").read() != wanted:
            sys.exit("README.md's gallery is out of date: run python3 scripts/skins.py gallery")
        print(f"{len(skins)} skins OK")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
