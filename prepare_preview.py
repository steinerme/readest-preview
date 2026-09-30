"""Apply preview-only packaging changes after Tauri Android scaffolding."""
from pathlib import Path
import json
import os
import xml.etree.ElementTree as ET

root = Path('source/apps/readest-app')
android = root / 'src-tauri/gen/android'
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
