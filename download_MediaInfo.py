# download_MediaInfo.py
import os, sys, urllib.request, zipfile, tempfile, shutil

MEDIAINFO_ZIP_URL = "https://mediaarea.net/download/binary/libmediainfo0/25.07/MediaInfo_DLL_25.07_Windows_x64_WithoutInstaller.zip"

def _base_dir():
    return os.path.dirname(sys.executable) if getattr(sys, "frozen", False) \
           else os.path.dirname(os.path.abspath(__file__))

LOCAL_DIR = _base_dir()  # ← ukládej vedle EXE/PY
LOCAL_DLL = os.path.join(LOCAL_DIR, "MediaInfo.dll")

def show_download_progress(block_num, block_size, total_size):
    downloaded = block_num * block_size
    percent = int(downloaded * 100 / total_size) if total_size > 0 else 0
    sys.stdout.write(f"\r📦 Stahuji MediaInfo… {percent}%")
    sys.stdout.flush()

def download_and_extract_mediainfo():
    if os.path.exists(LOCAL_DLL):
        print("✅ MediaInfo.dll už existuje.")
        return

    print(f"⬇️ Stahuji MediaInfo z: {MEDIAINFO_ZIP_URL}")
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "mediainfo.zip")
        urllib.request.urlretrieve(MEDIAINFO_ZIP_URL, zip_path, reporthook=show_download_progress)
        print("\n📦 Rozbaluji…")

        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
            dll_member = next((n for n in names if n.endswith("MediaInfo.dll")), None)
            if not dll_member:
                raise RuntimeError("❌ V archivu jsem nenašel MediaInfo.dll")

            src = zf.extract(dll_member, tmpdir)
            shutil.copy2(src, LOCAL_DLL)

        print(f"✅ Uloženo: {LOCAL_DLL}")

if __name__ == "__main__":
    download_and_extract_mediainfo()
