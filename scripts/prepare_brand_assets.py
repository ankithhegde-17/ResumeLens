"""Create lightweight web logos and favicons from the supplied logo image.

Run: python scripts/prepare_brand_assets.py "path/to/logo.png"
"""
import sys
from pathlib import Path

from PIL import Image, ImageOps


def prepare(source):
    static = Path(__file__).resolve().parents[1] / 'static'
    with Image.open(source) as original:
        image = original.convert('RGBA')
        # Pad instead of stretching so the supplied mark keeps its proportions.
        for name, size in [('logo.png', 128), ('favicon.png', 32),
                           ('apple-touch-icon.png', 180)]:
            icon = ImageOps.pad(image, (size, size), method=Image.Resampling.LANCZOS,
                                color='white')
            icon.save(static / name, optimize=True)
        icon = ImageOps.pad(image, (256, 256), method=Image.Resampling.LANCZOS,
                            color='white')
        icon.save(static / 'favicon.ico', sizes=[(16, 16), (32, 32), (48, 48)])


if __name__ == '__main__':
    prepare(sys.argv[1])
