import os
import zipfile
import urllib.request
import tempfile
import shutil
import sys

# URL to download the official FFmpeg (Windows build)
FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"

# The name of the binary we want to extract
FFMPEG_EXE_NAME = "ffmpeg.exe"

# Local path where ffmpeg.exe will be saved (same folder as this script)
LOCAL_FFMPEG_PATH = os.path.join(os.path.dirname(__file__), FFMPEG_EXE_NAME)


def show_download_progress(block_num, block_size, total_size):
    """
    Callback function for urlretrieve – shows download progress in percentage.
    block_num   -> number of blocks already downloaded
    block_size  -> size of one block
    total_size  -> total file size
    """
    downloaded = block_num * block_size
    percent = int(downloaded * 100 / total_size) if total_size > 0 else 0
    sys.stdout.write(f"\r📦 Downloading... {percent}%")
    sys.stdout.flush()


def download_and_extract_ffmpeg():
    """
    Downloads the FFmpeg archive, extracts it, and saves ffmpeg.exe
    into the project directory. If the file already exists, nothing happens.
    """
    # If ffmpeg.exe already exists, no need to download
    if os.path.exists(LOCAL_FFMPEG_PATH):
        print("✅ ffmpeg.exe already exists.")
        return

    print(f"⬇️ Downloading FFmpeg from: {FFMPEG_URL}")

    # Temporary folder for download and extraction
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "ffmpeg.zip")

        # Download the zip file with progress reporting
        urllib.request.urlretrieve(FFMPEG_URL, zip_path, reporthook=show_download_progress)

        print("\n📦 Extracting archive...")

        # Open the ZIP archive and search for bin/ffmpeg.exe
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file in zip_ref.namelist():
                if file.endswith("bin/ffmpeg.exe"):
                    # Extract only ffmpeg.exe into the temp directory
                    zip_ref.extract(file, tmpdir)

                    # Full path to the extracted ffmpeg.exe
                    full_exe_path = os.path.join(tmpdir, file)

                    # Copy it into the project folder
                    shutil.copy(full_exe_path, LOCAL_FFMPEG_PATH)
                    print("✅ ffmpeg.exe has been successfully saved to the project.")
                    return

        # If ffmpeg.exe was not found in the archive, raise an error
        raise RuntimeError("❌ ffmpeg.exe not found in the archive!")


if __name__ == "__main__":
    # Run the main function when script is executed directly
    download_and_extract_ffmpeg()
