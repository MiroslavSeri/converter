import os
import sys
from pymediainfo import MediaInfo

# přípony "raw" HEVC bez kontejneru
RAW_HEVC_EXT = {".hevc", ".h265", ".265"}

def _base_dir() -> str:
    return os.path.dirname(sys.executable) if getattr(sys, "frozen", False) \
           else os.path.dirname(os.path.abspath(__file__))

def _mediainfo_dll() -> str | None:
    for p in (
        os.path.join(_base_dir(), "MediaInfo.dll"),
        os.path.join(_base_dir(), "_internal", "MediaInfo.dll"),
    ):
        if os.path.isfile(p):
            return p
    return None

def select_video_file() -> str:
    """Otevře dialog a vrátí vybraný soubor (nebo '')."""
    try:
        import tkinter as tk
        from tkinter import filedialog
    except Exception:
        return ""  # když není k dispozici Tkinter

    root = tk.Tk()
    root.withdraw()
    root.update()
    path = filedialog.askopenfilename(
        title="Select a video file",
        initialdir=_base_dir(),
        filetypes=[("Video files",
                    "*.mp4 *.mkv *.avi *.mov *.flv *.wmv *.mpeg *.mpg *.hevc *.h265 *.265"),
                   ("All files", "*.*")]
    )
    root.destroy()
    return path or ""

def _get_input_path() -> str:
    """1) pokud je v argv, vezme ho; 2) jinak otevře dialog; 3) vrátí '' při zrušení."""
    if len(sys.argv) > 1 and sys.argv[1]:
        return sys.argv[1]
    return select_video_file()

class VideoAnalyzer:
    def __init__(self, file_path: str):
        if not file_path:
            raise ValueError("No file provided.")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File does not exist: {file_path}")
        if not os.path.isfile(file_path):
            raise ValueError(f"Given path is not a file: {file_path}")

        self.file_path = file_path
        self.video_format = None
        self.audio_format = None
        self._mi_dll = _mediainfo_dll()

        # pro knihovnu MediaInfo zkusíme explicitní cestu, pokud existuje
        if self._mi_dll:
            os.environ.setdefault("MEDIAINFO_PATH", self._mi_dll)

        self._analyze()

    def _analyze(self):
        try:
            mi = MediaInfo.parse(self.file_path, library_file=self._mi_dll) if self._mi_dll else MediaInfo.parse(self.file_path)
            for t in mi.tracks:
                if t.track_type == "Video" and self.video_format is None:
                    self.video_format = {
                        "codec": getattr(t, "codec", None),
                        "format": getattr(t, "format", None),
                        "width": getattr(t, "width", None),
                        "height": getattr(t, "height", None),
                        "frame_rate": getattr(t, "frame_rate", None),
                        "codec_id": getattr(t, "codec_id", None),
                    }
                elif t.track_type == "Audio" and self.audio_format is None:
                    self.audio_format = {
                        "codec": getattr(t, "codec", None),
                        "format": getattr(t, "format", None),
                        "channels": getattr(t, "channel_s", None),
                        "sampling_rate": getattr(t, "sampling_rate", None),
                    }
        except Exception:
            # necháme prázdno; volající si poradí
            pass

    def get_video_format(self):
        return self.video_format

    def get_audio_format(self):
        return self.audio_format

    def is_media(self) -> bool:
        # U raw HEVC ber rovnou jako video (MediaInfo někdy selže)
        ext = os.path.splitext(self.file_path)[1].lower()
        if ext in RAW_HEVC_EXT:
            return True
        return self.video_format is not None or self.audio_format is not None

    def is_hevc(self) -> bool:
        """True, když je video HEVC/H.265 (včetně raw .hevc/.h265/.265)."""
        ext = os.path.splitext(self.file_path)[1].lower()
        if ext in RAW_HEVC_EXT:
            return True
        if not self.video_format:
            return False
        fmt = (self.video_format.get("format") or "").lower()
        cid = (self.video_format.get("codec_id") or "").lower()
        return ("hevc" in fmt or "h265" in fmt or
                "hvc1" in cid or "hev1" in cid or "hevc" in cid)

# interaktivní/CLI režim
if __name__ == "__main__":
    path = _get_input_path()
    if not path:
        print("❌ No file selected.")
    else:
        try:
            analyzer = VideoAnalyzer(path)
            if not analyzer.is_media():
                print("❌ File does not contain any video or audio tracks.")
            else:
                video = analyzer.get_video_format()
                audio = analyzer.get_audio_format()

                print(f"\n📄 File: {path}")
                if video:
                    print("🎥 Video:")
                    for k, v in video.items():
                        print(f"  {k.capitalize()}: {v}")
                else:
                    print("❌ No video track found.")

                if audio:
                    print("🔊 Audio:")
                    for k, v in audio.items():
                        print(f"  {k.capitalize()}: {v}")
                else:
                    print("❌ No audio track found.")

                print(f"\nHEVC detected: {'Yes' if analyzer.is_hevc() else 'No'}")
        except Exception as e:
            import traceback
            print(f"❗ Error: {e}")
            traceback.print_exc()

    # drž konzoli otevřenou při spuštění dvojklikem
    try:
        if sys.stdin is None or not hasattr(sys.stdin, "isatty") or not sys.stdin.isatty():
            os.system("pause")
        else:
            input("\nStiskni Enter pro ukončení…")
    except Exception:
        pass
