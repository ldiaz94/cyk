#!/usr/bin/env python3
"""Deterministic asciinema recording and animated GIF generator for cyk.

Runs build/cyk across a scripted tour of frames:
- stepping t on "42 Melody"
- toggling v to the bit-plane waterfall
- switching n to "Crowd" and "Sierpinski Harmony"
- tweaking knobs a/b
- live-editing a custom formula in e mode with syntax error caret underline
Writes doc/demo.cast and doc/img/demo.gif.
"""

import html
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parent.parent
CYK_BIN = ROOT / "build/cyk"
DOC_DIR = ROOT / "doc"
IMG_DIR = DOC_DIR / "img"
CAST_FILE = DOC_DIR / "demo.cast"
GIF_FILE = IMG_DIR / "demo.gif"

WIDTH = 72
HEIGHT = 18

# Scripted tour: list of (key_string_to_append, duration_seconds)
SCRIPT = [
    # 1. Initial frame: preset 1 "42 Melody", scope view, t = 0
    ("", 0.60),
    # 2. Stepping t on "42 Melody"
    (".", 0.15),
    (".", 0.15),
    (".", 0.15),
    (".", 0.15),
    (".", 0.15),
    (".", 0.15),
    (".", 0.15),
    (".", 0.15),
    (".", 0.15),
    (".", 0.60),
    # 3. Toggle v to bit-plane waterfall
    ("v", 0.40),
    (".", 0.20),
    (".", 0.20),
    (".", 0.20),
    (".", 0.60),
    # 4. Switch n to preset 2 "Crowd"
    ("n", 0.40),
    (".", 0.20),
    (".", 0.20),
    ("v", 0.40),
    (".", 0.20),
    (".", 0.50),
    # 5. Switch n to preset 3 "Sierpinski Harmony"
    ("n", 0.40),
    (".", 0.20),
    (".", 0.20),
    (".", 0.20),
    (".", 0.50),
    # 6. Tweak knobs a and b
    ("a", 0.25),
    ("a", 0.30),
    ("b", 0.25),
    ("b", 0.30),
    (".", 0.20),
    (".", 0.20),
    (".", 0.50),
    # 7. Live-edit custom formula in e mode
    ("e", 0.35),
    ("\x15", 0.35),
    ("t", 0.15),
    (" ", 0.10),
    ("*", 0.12),
    (" ", 0.10),
    ("(", 0.80),  # Syntax error caret underline!
    ("t", 0.12),
    (" ", 0.08),
    (">", 0.08),
    (">", 0.08),
    (" ", 0.08),
    ("8", 0.12),
    (" ", 0.08),
    ("|", 0.12),
    (" ", 0.08),
    ("t", 0.12),
    (" ", 0.08),
    (">", 0.08),
    (">", 0.08),
    (" ", 0.08),
    ("9", 0.12),
    (")", 0.45),  # Valid formula completed
    ("\n", 0.45),  # Return to normal mode
    (".", 0.20),
    (".", 0.20),
    (".", 0.20),
    (".", 0.20),
    (".", 0.20),
    (".", 1.40),  # Final hold on custom tune
]


def ansi_to_tspans(line: str) -> str:
    tokens = re.split(r"(\x1b\[[0-9;]*m)", line)
    tspans = []
    fill = "#c9d1d9"
    weight = "normal"
    for tok in tokens:
        if not tok:
            continue
        if tok == "\x1b[0m":
            fill = "#c9d1d9"
            weight = "normal"
        elif tok == "\x1b[1m":
            fill = "#ffffff"
            weight = "bold"
        elif tok == "\x1b[2m":
            fill = "#586e75"
            weight = "normal"
        elif tok == "\x1b[36m":
            fill = "#00e5ff"
            weight = "normal"
        elif tok == "\x1b[31;1m":
            fill = "#ff5555"
            weight = "bold"
        elif tok == "\x1b[32m":
            fill = "#3fb950"
            weight = "normal"
        elif tok.startswith("\x1b["):
            pass
        else:
            escaped = html.escape(tok)
            w_attr = ' font-weight="bold"' if weight == "bold" else ""
            tspans.append(f'<tspan fill="{fill}"{w_attr}>{escaped}</tspan>')
    return "".join(tspans)


def render_svg_frame(lines: list[str]) -> str:
    svg_lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="720" height="416" viewBox="0 0 720 416">',
        '  <rect width="100%" height="100%" rx="8" fill="#10141a" stroke="#253240" stroke-width="1"/>',
        '  <circle cx="24" cy="20" r="5" fill="#ff5f56"/>',
        '  <circle cx="40" cy="20" r="5" fill="#ffbd2e"/>',
        '  <circle cx="56" cy="20" r="5" fill="#27c93f"/>',
        '  <text x="360" y="24" font-family="DejaVu Sans Mono" font-size="12" fill="#7d8590" text-anchor="middle">cyk — bytebeat studio</text>',
    ]
    for i, line in enumerate(lines):
        y = 56 + i * 19.5
        tspans = ansi_to_tspans(line)
        svg_lines.append(
            f'  <text x="35" y="{y:.1f}" font-family="DejaVu Sans Mono, monospace" font-size="14.5" xml:space="preserve">{tspans}</text>'
        )
    svg_lines.append("</svg>")
    return "\n".join(svg_lines)


def main():
    if not CYK_BIN.exists():
        subprocess.run(
            ["raz", "-Werror", "-I", "src", "-o", "build/cyk", "src/Cyk.raz"],
            cwd=ROOT,
            check=True,
        )

    DOC_DIR.mkdir(parents=True, exist_ok=True)
    IMG_DIR.mkdir(parents=True, exist_ok=True)

    cast_events = []
    header = {
        "version": 2,
        "width": WIDTH,
        "height": HEIGHT,
        "timestamp": 1700000000,
        "env": {"TERM": "xterm-256color"},
    }

    current_keys = ""
    current_time = 0.0

    temp_dir = tempfile.TemporaryDirectory(prefix="cyk_cast_")
    tmp = Path(temp_dir.name)
    concat_lines = ["ffconcat version 1.0\n"]

    print(f"Generating {len(SCRIPT)} frames for demo.cast and demo.gif...")
    start_all = time.time()

    for idx, (step_keys, duration) in enumerate(SCRIPT):
        current_keys += step_keys
        # Run cyk in headless screen mode with ANSI color
        p = subprocess.run(
            [str(CYK_BIN), "-s", f"{WIDTH}x{HEIGHT}"],
            input=current_keys.encode("latin1"),
            capture_output=True,
            env={"CYK_COLOR": "1", "PATH": os.environ.get("PATH", "/usr/bin:/bin")},
        )
        raw_output = p.stdout.decode("utf-8")
        lines = raw_output.rstrip("\n").split("\n")

        # Format asciinema event
        prefix = "\x1b[2J\x1b[H" if idx == 0 else "\x1b[H"
        frame_text = prefix + "\r\n".join(lines) + "\r\n"
        cast_events.append([round(current_time, 4), "o", frame_text])

        # Generate SVG frame
        svg_str = render_svg_frame(lines)
        svg_path = tmp / f"frame_{idx:04d}.svg"
        png_path = tmp / f"frame_{idx:04d}.png"
        svg_path.write_text(svg_str, encoding="utf-8")

        # Convert SVG to PNG
        subprocess.run(
            ["rsvg-convert", str(svg_path), "-o", str(png_path)],
            check=True,
        )

        concat_lines.append(f"file {png_path.name}\n")
        concat_lines.append(f"duration {duration:.4f}\n")

        current_time += duration

    # Repeat last frame in concat demuxer
    last_png_name = f"frame_{len(SCRIPT)-1:04d}.png"
    concat_lines.append(f"file {last_png_name}\n")

    # Write asciinema cast file
    print(f"Writing {CAST_FILE} ({len(cast_events)} events, {current_time:.2f}s)...")
    with open(CAST_FILE, "w", encoding="utf-8") as f:
        f.write(json.dumps(header) + "\n")
        for row in cast_events:
            f.write(json.dumps(row) + "\n")

    # Write concat file
    concat_file = tmp / "concat.txt"
    concat_file.write_text("".join(concat_lines), encoding="utf-8")

    # Assemble animated GIF with ffmpeg palettegen + paletteuse
    print(f"Assembling {GIF_FILE} with ffmpeg...")
    palette_path = tmp / "palette.png"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-i",
            str(concat_file),
            "-vf",
            "palettegen=max_colors=32",
            str(palette_path),
        ],
        cwd=tmp,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-i",
            str(concat_file),
            "-i",
            str(palette_path),
            "-lavfi",
            "paletteuse=dither=none:diff_mode=rectangle",
            str(GIF_FILE),
        ],
        cwd=tmp,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    gif_size = GIF_FILE.stat().st_size
    cast_size = CAST_FILE.stat().st_size
    elapsed = time.time() - start_all
    print(
        f"Done in {elapsed:.1f}s! cast: {cast_size:,} bytes, gif: {gif_size:,} bytes ({current_time:.1f}s tour)"
    )


if __name__ == "__main__":
    main()
