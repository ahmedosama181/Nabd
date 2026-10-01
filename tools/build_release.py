#!/usr/bin/env python3
"""Build the small download for people who just want to run Nabd: dist/Nabd.zip.

It holds only what is needed to run the app (launchers, app.py, tracker/, web/, the Windows Python setup
script) plus the license, the third-party notices and a short "how to start" note. Tests, screenshots and
GitHub files stay in the repository.

    python3 tools/build_release.py              # -> dist/Nabd.zip
    python3 tools/build_release.py out/dir      # -> out/dir/Nabd.zip
"""
import os
import sys
import time
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = "Nabd"  # top folder inside the zip, and the zip's name

FILES = [
    "Start-Mac.command",
    "Start-Windows.bat",
    "app.py",
    "LICENSE",
    "THIRD_PARTY_NOTICES.md",
    "tools/bootstrap-windows.ps1",
]
FOLDERS = {"tracker": (".py",), "web": (".html", ".css", ".js")}  # folder -> file types to take
EXECUTABLE = {"Start-Mac.command"}

HOW_TO_START = """Nabd - Egyptian pound market pulse
==================================

macOS:   double-click "Start-Mac.command".
         The first time, macOS may block it ("Apple could not verify..."): open
         System Settings > Privacy & Security, scroll to Security and click "Open Anyway".
Windows: double-click "Start-Windows.bat".
         If "Windows protected your PC" appears, click "More info" > "Run anyway".

Nabd opens in your browser. To stop it, close the window that opened with it.
No installation needed: if the computer has no Python 3.8+, a private copy is set up
in the "runtime" folder the first time (delete that folder to remove it).

More: https://github.com/ahmedosama181/Nabd


نبض - نبض أسعار الجنيه المصري
=============================

ماك:     اضغط مرتين على "Start-Mac.command".
         في أول مرة قد يمنعه النظام: افتح إعدادات النظام > الخصوصية والأمان، ثم اضغط "فتح على أي حال".
ويندوز:  اضغط مرتين على "Start-Windows.bat".
         لو ظهرت رسالة الحماية: اضغط "More info" ثم "Run anyway".

تفتح الأداة في المتصفح. للإيقاف أغلق النافذة التي فتحت معها.
لا تحتاج لتثبيت أي شيء: لو الجهاز ليس عليه بايثون، يتم تجهيز نسخة خاصة في مجلد "runtime" في أول تشغيل.
"""


def runtime_files():
    """Repository paths (with forward slashes) that go into the zip."""
    out = list(FILES)
    for folder, types in FOLDERS.items():
        for base, dirs, names in os.walk(os.path.join(ROOT, folder)):
            dirs[:] = sorted(d for d in dirs if d != "__pycache__")
            for n in sorted(names):
                if n.endswith(types):
                    out.append(os.path.relpath(os.path.join(base, n), ROOT).replace(os.sep, "/"))
    return out


def fix_line_endings(rel, data):
    """Windows scripts need CRLF, the Mac launcher and Python files LF, whatever the checkout produced."""
    if rel.endswith((".bat", ".ps1")):
        return data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    if rel.endswith((".command", ".py")):
        return data.replace(b"\r\n", b"\n")
    return data


def build(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    target = os.path.join(out_dir, NAME + ".zip")
    stamp = time.localtime()[:6]

    def add(zf, rel, data, mode):
        info = zipfile.ZipInfo(NAME + "/" + rel, date_time=stamp)
        info.create_system = 3  # Unix, so the permission bits below are honoured when unzipping
        info.external_attr = (0o100000 | mode) << 16
        info.compress_type = zipfile.ZIP_DEFLATED
        zf.writestr(info, data)

    files = runtime_files()
    with zipfile.ZipFile(target, "w") as zf:
        for rel in files:
            with open(os.path.join(ROOT, rel), "rb") as fh:
                data = fh.read()
            add(zf, rel, fix_line_endings(rel, data), 0o755 if rel in EXECUTABLE else 0o644)
        add(zf, "How to start.txt", HOW_TO_START.replace("\n", "\r\n").encode("utf-8-sig"), 0o644)
    return target, files


if __name__ == "__main__":
    path, files = build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "dist"))
    print("%s: %d files, %.0f KB" % (path, len(files) + 1, os.path.getsize(path) / 1024))
