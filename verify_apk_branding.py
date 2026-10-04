"""Check decoded FINAL APK resources, not intermediate build inputs."""
from pathlib import Path
import sys, xml.etree.ElementTree as ET
from PIL import Image, ImageChops, ImageStat
res = Path(sys.argv[1]) / 'res'
source = Path('source/apps/readest-app/src-tauri/gen/android/app/src/main/res')
ns = '{http://schemas.android.com/apk/res/android}'
manifest = ET.parse(Path(sys.argv[1]) / 'AndroidManifest.xml').getroot()
app = manifest.find('application')
assert app is not None and app.get(ns+'icon') == '@mipmap/ic_launcher'
xmls = list(res.glob('mipmap-anydpi*/ic_launcher.xml'))
assert xmls, 'Final APK adaptive launcher XML missing'
for xml in xmls:
    tree = ET.parse(xml).getroot()
    assert tree.find('foreground').get(ns+'drawable') == '@mipmap/ic_launcher_foreground'
    assert tree.find('background').get(ns+'drawable') == '@mipmap/ic_launcher_background'
    assert tree.find('monochrome') is None, 'Stale themed icon'
for density in ['mdpi','hdpi','xhdpi','xxhdpi','xxxhdpi']:
    for name in ['ic_launcher','ic_launcher_round','ic_launcher_foreground','ic_launcher_background']:
        filename = f'mipmap-{density}/{name}.png'
        actual = Image.open(res/filename).convert('RGBA')
        expected = Image.open(source/filename).convert('RGBA')
        assert actual.size == expected.size, filename
        diff = ImageStat.Stat(ImageChops.difference(actual, expected)).mean
        assert max(diff) < 1, (filename, diff)
print('PASS: FINAL APK launcher manifest/XML and all 20 custom bitmaps match generated private artwork')

# Splash (window background) + notification small icon must be the preview art,
# not upstream's open-book. Compare by content: the packaged resource names are
# obfuscated by resource shrinking, so scan every bitmap for the book artwork.
src_res = Path('source/apps/readest-app/src-tauri/gen/android/app/src/main/res')
tts_icon = Path('source/apps/readest-app/src-tauri/plugins/tauri-plugin-native-tts/android/src/main/res/drawable/notification_icon.png')
expected_splash = Image.open(src_res / 'drawable/splash_icon.png').convert('RGBA')
expected_note = Image.open(tts_icon).convert('RGBA')
def same(a, b):
    if a.size != b.size: return False
    return max(ImageStat.Stat(ImageChops.difference(a, b)).mean) < 1
found_splash = found_note = False
for png in res.rglob('*.png'):
    if png.name.endswith('.9.png'): continue
    try: img = Image.open(png).convert('RGBA')
    except Exception: continue
    found_splash = found_splash or same(img, expected_splash)
    found_note = found_note or same(img, expected_note)
assert found_splash, 'Final APK does not contain the preview splash artwork'
assert found_note, 'Final APK does not contain the preview notification icon'
# Upstream book artwork (still bundled in the checkout under icons/) must not
# be packaged anywhere as a >=192px bitmap.
upstream = Image.open('source/apps/readest-app/src-tauri/icons/icon.png').convert('RGBA').resize((64, 64))
for png in res.rglob('*.png'):
    if png.name.endswith('.9.png'): continue
    try: img = Image.open(png).convert('RGBA')
    except Exception: continue
    if img.width < 192: continue
    d = max(ImageStat.Stat(ImageChops.difference(img.resize((64, 64)), upstream)).mean)
    assert d > 3, ('Upstream artwork still packaged', png.name)
print('PASS: splash + notification icon use the preview artwork; no upstream book bitmap remains')
