"""Modpack zip'ini CurseForge projesine yükler.

Kullanım: python3 modpack/tools/upload.py <proje_numarası> [release|beta|alpha]
Upload token ortam ağına kayıtlıdır (X-Api-Token başlığına proxy ekler).
"""
import json
import os
import sys
import uuid
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIP = os.path.join(ROOT, "StarPath-1.0.0.zip")
CHANGELOG = os.path.join(ROOT, "yayin", "degisiklikler.md")
MC_1_21_1 = 11779  # "Minecraft 1.21" türündeki 1.21.1

project_id = int(sys.argv[1])
release_type = sys.argv[2] if len(sys.argv) > 2 else "beta"

metadata = {
    "changelog": open(CHANGELOG, encoding="utf-8").read(),
    "changelogType": "markdown",
    "displayName": "Star Path 1.0.0",
    "gameVersions": [MC_1_21_1],
    "releaseType": release_type,
}

boundary = uuid.uuid4().hex
body = b"".join([
    f"--{boundary}\r\nContent-Disposition: form-data; name=\"metadata\"\r\n\r\n".encode(),
    json.dumps(metadata, ensure_ascii=False).encode("utf-8"),
    f"\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{os.path.basename(ZIP)}\"\r\n"
    "Content-Type: application/zip\r\n\r\n".encode(),
    open(ZIP, "rb").read(),
    f"\r\n--{boundary}--\r\n".encode(),
])
req = urllib.request.Request(
    f"https://minecraft.curseforge.com/api/projects/{project_id}/upload-file",
    data=body, method="POST",
    headers={"X-Api-Token": os.environ.get("CF_UPLOAD_TOKEN", "proxy-injected"),
             "Content-Type": f"multipart/form-data; boundary={boundary}",
             "User-Agent": "modpack-builder"})
try:
    with urllib.request.urlopen(req, timeout=300) as r:
        print(r.status, r.read().decode())
except urllib.error.HTTPError as e:
    print(e.code, e.read().decode())
    sys.exit(1)
