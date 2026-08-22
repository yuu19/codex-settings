from __future__ import annotations

import json
import math
from collections import deque
from pathlib import Path

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "pets" / "akita-inu.png"
PACKAGE_DIR = Path("/mnt/c/Users/yusuk/.codex/pets/akita-inu")
CELL_W = 192
CELL_H = 208
COLS = 8
ROWS = 9
ATLAS_W = CELL_W * COLS
ATLAS_H = CELL_H * ROWS


def color_distance(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    return math.sqrt(sum((int(x) - int(y)) ** 2 for x, y in zip(a, b)))


def remove_connected_background(image: Image.Image, tolerance: float = 42.0) -> Image.Image:
    rgba = image.convert("RGBA")
    px = rgba.load()
    width, height = rgba.size
    border_samples: list[tuple[int, int, int]] = []

    for x in range(width):
        border_samples.append(px[x, 0][:3])
        border_samples.append(px[x, height - 1][:3])
    for y in range(height):
        border_samples.append(px[0, y][:3])
        border_samples.append(px[width - 1, y][:3])

    bg = tuple(
        int(sum(sample[channel] for sample in border_samples) / len(border_samples))
        for channel in range(3)
    )

    visited = bytearray(width * height)
    queue: deque[tuple[int, int]] = deque()

    def enqueue(x: int, y: int) -> None:
        idx = y * width + x
        if visited[idx]:
            return
        if color_distance(px[x, y][:3], bg) <= tolerance:
            visited[idx] = 1
            queue.append((x, y))

    for x in range(width):
        enqueue(x, 0)
        enqueue(x, height - 1)
    for y in range(height):
        enqueue(0, y)
        enqueue(width - 1, y)

    while queue:
        x, y = queue.popleft()
        r, g, b, _ = px[x, y]
        px[x, y] = (r, g, b, 0)
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < width and 0 <= ny < height:
                enqueue(nx, ny)

    return rgba


def trim_and_fit(image: Image.Image) -> Image.Image:
    bbox = image.getbbox()
    if bbox is None:
        raise RuntimeError("source image became empty after background removal")

    pet = image.crop(bbox)
    pet.thumbnail((158, 178), Image.Resampling.LANCZOS)
    return pet


def transform_for_state(base: Image.Image, row: int, col: int) -> tuple[Image.Image, int, int]:
    frame = base.copy()
    x_offset = 0
    y_offset = 0

    if row == 0:  # idle
        y_offset = [0, -1, -2, -1, 0, 1, 0, -1][col]
    elif row == 1:  # running-right
        x_offset = [-7, -5, -3, -1, 1, 3, 5, 7][col]
        y_offset = [0, -2, 0, 2, 0, -2, 0, 2][col]
    elif row == 2:  # running-left
        frame = ImageOps.mirror(frame)
        x_offset = [7, 5, 3, 1, -1, -3, -5, -7][col]
        y_offset = [0, -2, 0, 2, 0, -2, 0, 2][col]
    elif row == 3:  # waving
        y_offset = [0, -1, -2, -3, -2, -1, 0, -1][col]
    elif row == 4:  # jumping
        y_offset = [0, -8, -16, -22, -16, -8, -2, 0][col]
    elif row == 5:  # failed
        y_offset = [4, 5, 6, 6, 5, 4, 5, 6][col]
    elif row == 6:  # waiting
        x_offset = [-2, -1, 0, 1, 2, 1, 0, -1][col]
    elif row == 7:  # running
        y_offset = [0, -2, -4, -2, 0, 1, 0, -1][col]
    elif row == 8:  # review
        x_offset = [1, 2, 3, 2, 1, 0, 1, 2][col]
        y_offset = [0, 0, -1, -1, 0, 0, -1, -1][col]

    return frame, x_offset, y_offset


def main() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(SOURCE)

    cleaned = remove_connected_background(Image.open(SOURCE))
    base = trim_and_fit(cleaned)
    atlas = Image.new("RGBA", (ATLAS_W, ATLAS_H), (0, 0, 0, 0))

    for row in range(ROWS):
        for col in range(COLS):
            frame, x_offset, y_offset = transform_for_state(base, row, col)
            x = col * CELL_W + (CELL_W - frame.width) // 2 + x_offset
            y = row * CELL_H + CELL_H - frame.height - 10 + y_offset
            atlas.alpha_composite(frame, (x, y))

    PACKAGE_DIR.mkdir(parents=True, exist_ok=True)
    atlas.save(PACKAGE_DIR / "spritesheet.webp", "WEBP", lossless=True, quality=100)
    atlas.save(PACKAGE_DIR / "spritesheet.png")
    (PACKAGE_DIR / "source.png").write_bytes(SOURCE.read_bytes())

    manifest = {
        "id": "akita-inu",
        "displayName": "Akita Inu",
        "description": "A friendly tan and white Akita Inu companion based on the provided reference image.",
        "spritesheetPath": "spritesheet.webp",
    }
    (PACKAGE_DIR / "pet.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
