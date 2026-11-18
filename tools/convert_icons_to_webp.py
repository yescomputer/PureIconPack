#!/usr/bin/env python3
"""
Lossless PNG -> WebP converter for res/drawable-nodpi icon assets.
Verifies 100% pixel-identical visible RGBA values before replacing each PNG.
"""

from __future__ import annotations

import io
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
NODPI_DIR = ROOT / "app" / "src" / "main" / "res" / "drawable-nodpi"


def verify_visible_rgba_identical(img_a: Image.Image, img_b: Image.Image) -> bool:
    if img_a.size != img_b.size:
        return False
    rgba_a = img_a.convert("RGBA").tobytes()
    rgba_b = img_b.convert("RGBA").tobytes()
    if rgba_a == rgba_b:
        return True
    # WebP lossless normalizes RGB under fully transparent pixels (alpha == 0) unless exact=True;
    # verify alpha channel is 100% identical and RGB is 100% identical for every alpha > 0 pixel.
    mv_a = memoryview(rgba_a)
    mv_b = memoryview(rgba_b)
    for idx in range(0, len(mv_a), 4):
        a1 = mv_a[idx + 3]
        a2 = mv_b[idx + 3]
        if a1 != a2:
            return False
        if a1 != 0 and mv_a[idx : idx + 3] != mv_b[idx : idx + 3]:
            return False
    return True


def convert_one(png_path: Path) -> tuple[str, int, int, bool]:
    orig_bytes = png_path.read_bytes()
    orig_size = len(orig_bytes)

    with Image.open(io.BytesIO(orig_bytes)) as im:
        im_rgba = im.convert("RGBA")
        buf = io.BytesIO()
        im_rgba.save(buf, format="WEBP", lossless=True, method=4)
        webp_bytes = buf.getvalue()

    if len(webp_bytes) >= orig_size:
        return (png_path.name, orig_size, orig_size, False)

    with Image.open(io.BytesIO(orig_bytes)) as a, Image.open(io.BytesIO(webp_bytes)) as b:
        if not verify_visible_rgba_identical(a, b):
            raise RuntimeError(f"Pixel verification failed for {png_path.name}")

    webp_path = png_path.with_suffix(".webp")
    webp_path.write_bytes(webp_bytes)
    png_path.unlink()
    return (png_path.name, orig_size, len(webp_bytes), True)


def main() -> int:
    png_files = sorted(NODPI_DIR.glob("*.png"))
    if not png_files:
        print("No PNG files remaining in drawable-nodpi.")
        return 0

    total_before = 0
    total_after = 0
    converted = 0
    kept_png = 0

    workers = min(16, (os.cpu_count() or 8))
    print(f"Converting {len(png_files)} PNG icons to lossless WebP using {workers} threads...")

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(convert_one, p) for p in png_files]
        for fut in as_completed(futures):
            _, before, after, did_convert = fut.result()
            total_before += before
            total_after += after
            if did_convert:
                converted += 1
            else:
                kept_png += 1

    saved_mb = (total_before - total_after) / (1024 * 1024)
    pct = (1.0 - (total_after / total_before)) * 100.0 if total_before else 0.0
    print(
        f"Done: converted={converted}, kept_smaller_png={kept_png} | "
        f"Before={total_before / (1024*1024):.2f} MB -> After={total_after / (1024*1024):.2f} MB "
        f"(Saved {saved_mb:.2f} MB / {pct:.1f}%)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
