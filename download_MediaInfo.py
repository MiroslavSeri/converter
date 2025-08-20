# download_mediainfo.py
import os
import zipfile
import tempfile
import shutil
import urllib.request
from pathlib import Path

# URL to download MediaInfo (Windows CLI version)
MEDIAINFO_URL = "https://mediaarea.net/download/binary/mediainfo/23.07/MediaInfo_CLI_23.07_Windows_x64.zip"

# Root directory (the folder where this script is located)
ROOT = Path(__file__).resolve().parent

# The name of the executable we are looking for
MEDIAINFO_EXE_NAME = "mediainfo.exe"

# Full local path where mediainfo.exe will be saved
LOCAL_MEDIAINFO_PATH = ROOT / MEDIAINFO_EXE_NAME


def download_and_extract_mediainfo():
    """
    Downloads and extracts MediaInfo CLI from the official ZIP archive.
    If the executable already exists locally, the function does nothing.
    Returns the path to the mediainfo.exe file.
    """
    # If mediainfo.exe already exists, no need to download again
    if LOCAL_MEDIAINFO_PATH.exists():
        print(f"✅ {MEDIAINFO_EXE_NAME} already exists.")
        return LOCAL_MEDIAINFO_PATH

    # Create a temporary folder for download and extraction
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / "mediainfo.zip"

        # Download the ZIP file
        print(f"⬇️ Downloading from: {MEDIAINFO_URL}")
        urllib.request.urlretrieve(MEDIAINFO_URL, zip_path)

        # Open the ZIP archive and search for mediainfo.exe
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file in zip_ref.namelist():
                # Match exactly "mediainfo.exe" regardless of folder inside the archive
                if os.path.basename(file).lower() == MEDIAINFO_EXE_NAME:
                    # Extract mediainfo.exe into the temporary folder
                    zip_ref.extract(file, tmpdir)

                    # Copy it into the project root
                    shutil.copy(Path(tmpdir) / file, LOCAL_MEDIAINFO_PATH)
                    print(f"✅ {MEDIAINFO_EXE_NAME} saved to: {LOCAL_MEDIAINFO_PATH}")
                    return LOCAL_MEDIAINFO_PATH

    # If mediainfo.exe was not found in the archive, raise an error
    raise RuntimeError(f"❌ {MEDIAINFO_EXE_NAME} not found in the archive!")


def get_mediainfo_path():
    """
    Returns the path to mediainfo.exe.
    Downloads and extracts it first if it doesn’t exist locally.
    """
    if not LOCAL_MEDIAINFO_PATH.exists():
        return download_and_extract_mediainfo()
    return LOCAL_MEDIAINFO_PATH


if __name__ == "__main__":
    # Run the download and extraction when script is executed directly
    path = download_and_extract_mediainfo()
    print(f"Use this executable: {path}")
