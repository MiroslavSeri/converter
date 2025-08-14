# download_mediainfo.py
import os
import zipfile
import tempfile
import shutil
import urllib.request
from pathlib import Path

MEDIAINFO_URL = "https://mediaarea.net/download/binary/mediainfo/23.07/MediaInfo_CLI_23.07_Windows_x64.zip"
ROOT = Path(__file__).resolve().parent
MEDIAINFO_EXE_NAME = "mediainfo.exe"
LOCAL_MEDIAINFO_PATH = ROOT / MEDIAINFO_EXE_NAME

def download_and_extract_mediainfo():
    if LOCAL_MEDIAINFO_PATH.exists():
        print(f"✅ {MEDIAINFO_EXE_NAME} už existuje.")
        return LOCAL_MEDIAINFO_PATH

    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / "mediainfo.zip"
        print(f"⬇️ Stahuji z: {MEDIAINFO_URL}")
        urllib.request.urlretrieve(MEDIAINFO_URL, zip_path)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file in zip_ref.namelist():
                if os.path.basename(file).lower() == MEDIAINFO_EXE_NAME:
                    zip_ref.extract(file, tmpdir)
                    shutil.copy(Path(tmpdir) / file, LOCAL_MEDIAINFO_PATH)
                    print(f"✅ {MEDIAINFO_EXE_NAME} uložen do: {LOCAL_MEDIAINFO_PATH}")
                    return LOCAL_MEDIAINFO_PATH

    raise RuntimeError(f"❌ {MEDIAINFO_EXE_NAME} nebyl nalezen v archivu!")

def get_mediainfo_path():
    if not LOCAL_MEDIAINFO_PATH.exists():
        return download_and_extract_mediainfo()
    return LOCAL_MEDIAINFO_PATH

if __name__ == "__main__":
    path = download_and_extract_mediainfo()
    print(f"Používej: {path}")
