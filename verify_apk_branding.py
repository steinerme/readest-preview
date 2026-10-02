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
