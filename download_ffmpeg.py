import os
import zipfile
import urllib.request
import tempfile
import shutil
import sys

FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
FFMPEG_EXE_NAME = "ffmpeg.exe"

# ⬅️ přidáno: správná základna (vedle .exe v onefile, jinak vedle .py)
def _base_dir():
    return os.path.dirname(sys.executable) if getattr(sys, "frozen", False) \
           else os.path.dirname(os.path.abspath(__file__))

# ⬅️ upraveno: ukládej vedle EXE / PY
LOCAL_FFMPEG_PATH = os.path.join(_base_dir(), FFMPEG_EXE_NAME)


def show_download_progress(block_num, block_size, total_size):
    downloaded = block_num * block_size
    percent = int(downloaded * 100 / total_size) if total_size > 0 else 0
    sys.stdout.write(f"\r📦 Downloading... {percent}%")
    sys.stdout.flush()


def download_and_extract_ffmpeg():
    if os.path.exists(LOCAL_FFMPEG_PATH):
        print("✅ ffmpeg.exe already exists.")
        return

    print(f"⬇️ Downloading FFmpeg from: {FFMPEG_URL}")

    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "ffmpeg.zip")
        urllib.request.urlretrieve(FFMPEG_URL, zip_path, reporthook=show_download_progress)

        print("\n📦 Extracting archive...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file in zip_ref.namelist():
                if file.endswith("bin/ffmpeg.exe"):
                    zip_ref.extract(file, tmpdir)
                    full_exe_path = os.path.join(tmpdir, file)
                    shutil.copy(full_exe_path, LOCAL_FFMPEG_PATH)
                    print("✅ ffmpeg.exe has been successfully saved to the project.")
                    return

        raise RuntimeError("❌ ffmpeg.exe not found in the archive!")


if __name__ == "__main__":
    download_and_extract_ffmpeg()
