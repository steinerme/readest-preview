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
