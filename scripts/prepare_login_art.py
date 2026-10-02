"""Re-encode the existing login illustration for efficient browser delivery."""
from pathlib import Path

from PIL import Image


static = Path(__file__).resolve().parents[1] / 'static'
with Image.open(static / 'login-hero.png') as original:
    image = original.convert('RGB')
    image.thumbnail((1200, 1500), Image.Resampling.LANCZOS)
    image.save(static / 'login-hero.webp', quality=88, method=6)
