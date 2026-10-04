"""Apply preview-only packaging changes after Tauri Android scaffolding."""
from pathlib import Path
import json
import os
import xml.etree.ElementTree as ET
import shutil

root = Path('source/apps/readest-app')
android = root / 'src-tauri/gen/android'
# Tauri writes into gen/android/app/src/main/res when scaffolding exists.
# The workflow runs icon generation AFTER git restore. Never copy the stale
# upstream icons/android directory over the newly generated private artwork.
from PIL import Image
res = android / 'app/src/main/res'
foreground = Image.open('branding/android-foreground.png').convert('RGBA')
for density, size in [('mdpi', 108), ('hdpi', 162), ('xhdpi', 216), ('xxhdpi', 324), ('xxxhdpi', 432)]:
    actual = Image.open(res / f'mipmap-{density}/ic_launcher_foreground.png').convert('RGBA')
    expected = foreground.resize((size, size), Image.Resampling.LANCZOS)
    assert actual.size == expected.size
    # Independent visual fingerprint catches accidentally restored old artwork.
    from PIL import ImageChops, ImageStat
    difference = ImageStat.Stat(ImageChops.difference(actual, expected)).mean
    assert max(difference) < 3, (density, difference)
    for stale in (res / f'mipmap-{density}').glob('*monochrome*'):
        stale.unlink()
# Do not ship an old Readest-themed monochrome icon under Android 13+.
icon_xml = android / 'app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml'
icon_tree = ET.parse(icon_xml)
for child in list(icon_tree.getroot()):
    if child.tag == 'monochrome':
        icon_tree.getroot().remove(child)
icon_tree.write(icon_xml, encoding='utf-8', xml_declaration=True)
# Window-background splash (shown while the activity is created, e.g. when
# switching back from another app) and the media notification small icon were
# still upstream's open-book artwork. Replace both with the preview artwork.
from PIL import ImageChops as _IC, ImageDraw as _ID, ImageOps as _IO, ImageFilter as _IF
_art = Image.open('branding/app-icon.png').convert('RGBA')
_s = 432
_splash = _art.resize((_s, _s), Image.Resampling.LANCZOS)
_mask = Image.new('L', (_s * 4, _s * 4), 0)
_ID.Draw(_mask).rounded_rectangle((0, 0, _s * 4 - 1, _s * 4 - 1), radius=int(_s * 4 * 0.22), fill=255)
_mask = _mask.resize((_s, _s), Image.Resampling.LANCZOS)
_splash.putalpha(_IC.multiply(_splash.getchannel('A'), _mask))
_splash.save(res / 'drawable/splash_icon.png')
# Status-bar icons are alpha masks: derive a legible silhouette from the artwork.
_n = 96
_im = _art.convert('RGB').resize((_n * 4, _n * 4), Image.Resampling.LANCZOS)
_g = _IO.autocontrast(_im.convert('L'), cutoff=2)
_sat = _im.convert('HSV').split()[1]
_fig = _IC.lighter(_g.point(lambda p: 255 if p > 85 else 0), _sat.point(lambda p: 255 if p > 80 else 0)).filter(_IF.MedianFilter(9))
_tone = _g.point(lambda p: int(255 * min(1, max(0, (p - 35) / 110)) ** 0.8))
_alpha = _IC.multiply(_IC.lighter(_IC.multiply(_fig, _tone), _fig.point(lambda p: int(p * 0.62))), _g.point(lambda p: 0 if p < 48 else 255))
_circle = Image.new('L', _im.size, 0)
_ID.Draw(_circle).ellipse((0, 0, _im.size[0] - 1, _im.size[1] - 1), fill=255)
_alpha = _IC.multiply(_alpha, _circle).resize((_n, _n), Image.Resampling.LANCZOS)
_note = Image.new('RGBA', (_n, _n), (255, 255, 255, 0))
_note.putalpha(_alpha)
_tts = root / 'src-tauri/plugins/tauri-plugin-native-tts/android/src/main/res/drawable/notification_icon.png'
assert _tts.exists()
_note.save(_tts)
# In-app/PWA icons use the same full square illustration.
from PIL import Image
image = Image.open('branding/app-icon.png')
for name, size in [('icon.png', 512), ('icon-tiny.png', 32), ('apple-touch-icon.png', 180)]:
    image.resize((size, size), Image.Resampling.LANCZOS).save(root / 'public' / name)
image.save(root / 'public/favicon.ico', sizes=[(16, 16), (32, 32), (48, 48)])
gradle = android / 'app/build.gradle.kts'
text = gradle.read_text()
old = 'applicationId = "com.bilingify.readest"'
assert text.count(old) == 1
# Keep namespace / Kotlin package / Tauri JNI identity unchanged. Android's
# installed package and private data directory follow applicationId instead.
text = text.replace(old, 'applicationId = "com.bilingify.readest.preview"')
old_code = 'versionCode = tauriProperties.getProperty("tauri.android.versionCode", "1").toInt()'
assert old_code in text
text = text.replace(old_code, f'versionCode = {20000 + int(os.environ["GITHUB_RUN_NUMBER"])}')
gradle.write_text(text)

ns = 'http://schemas.android.com/apk/res/android'
ET.register_namespace('android', ns)
manifest = android / 'app/src/main/AndroidManifest.xml'
tree = ET.parse(manifest)
application = tree.getroot().find('application')
assert application is not None
application.set(f'{{{ns}}}label', 'Readest Preview')
for activity in application.findall('activity'):
    activity.set(f'{{{ns}}}label', 'Readest Preview')
    # Do not steal the official app's sign-in callbacks or verified app links.
    # This preview is for local reading; cloud OAuth is not certified here.
    for intent in list(activity.findall('intent-filter')):
        schemes = [x.get(f'{{{ns}}}scheme') for x in intent.findall('data')]
        if any(s and s not in ('file', 'content') for s in schemes):
            activity.remove(intent)
tree.write(manifest, encoding='utf-8', xml_declaration=True)

config = root / 'src-tauri/tauri.conf.json'
obj = json.loads(config.read_text())
obj['build']['beforeBuildCommand'] = 'pnpm build --webpack && pnpm upload-sourcemaps'
config.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')
print('Prepared separate package: com.bilingify.readest.preview')
