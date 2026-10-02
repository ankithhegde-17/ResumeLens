"""Copy existing assets to Vercel's CDN without moving local Flask files."""
from pathlib import Path
import shutil

root = Path(__file__).resolve().parents[1]
target = root / 'public' / 'static'
target.mkdir(parents=True, exist_ok=True)
for source in (root / 'static').iterdir():
    if source.is_file() and source.name != 'login-hero.png':
        shutil.copy2(source, target / source.name)
print('Prepared /static/* CDN assets; templates remain in templates/.')
