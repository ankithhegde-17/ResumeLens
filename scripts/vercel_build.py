"""Copy existing assets to Vercel's CDN without moving local Flask files."""
from pathlib import Path
import shutil

root = Path(__file__).resolve().parents[1]
target = root / 'public' / 'static'
target.mkdir(parents=True, exist_ok=True)
retired = {'login-hero.png','login-hero.webp','favicon.svg'}
for filename in retired:
    previous = target / filename
    if previous.is_file(): previous.unlink()  # Only generated copies, never source artwork.
for source in (root / 'static').iterdir():
    # Preserve original artwork locally; retired login assets are not published.
    if source.is_file() and source.name not in retired:
        shutil.copy2(source, target / source.name)
print('Prepared /static/* CDN assets; templates remain in templates/.')
