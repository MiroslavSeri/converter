import os
import subprocess
import re
import sys
from pymediainfo import MediaInfo
from download_ffmpeg import download_and_extract_ffmpeg
from download_MediaInfo import download_and_extract_mediainfo

# --- správná základní složka ---
def _base_dir() -> str:
    return os.path.dirname(sys.executable) if getattr(sys, "frozen", False) \
           else os.path.dirname(os.path.abspath(__file__))

def _find_tool(name: str) -> str | None:
    b = _base_dir()
    cand = os.path.join(b, name)
    if os.path.isfile(cand):
        return cand
    cand2 = os.path.join(b, "_internal", name)
    if os.path.isfile(cand2):
        return cand2
    from shutil import which
    return which(name)

def _mediainfo_dll() -> str | None:
    for p in (os.path.join(_base_dir(), "MediaInfo.dll"),
              os.path.join(_base_dir(), "_internal", "MediaInfo.dll")):
        if os.path.isfile(p):
            return p
    return None

class AnyToH265Converter:
    def __init__(self, input_path, output_path=None, overwrite=True, print_lock=None, progress_dict=None, show_progress=False):
        self.input_path = input_path
        if not os.path.exists(self.input_path):
            raise FileNotFoundError(f"Soubor neexistuje: {self.input_path}")

        self.output_path = output_path or self._build_output_path()
        self.overwrite = overwrite

        self.ffmpeg_path = _find_tool("ffmpeg.exe")
        if not self.ffmpeg_path:
            raise FileNotFoundError("Nenalezen ffmpeg.exe")

        self._mi_dll = _mediainfo_dll()

        self.duration = self._get_duration()
        self.print_lock = print_lock
        self.progress_dict = progress_dict
        self.show_progress = show_progress
        self._last_percent_shown = -1.0
        self._progress_key = os.path.basename(self.input_path)

    def _build_output_path(self):
        base_name = os.path.splitext(os.path.basename(self.input_path))[0]
        output_dir = os.path.join(_base_dir(), "output")
        os.makedirs(output_dir, exist_ok=True)
        return os.path.join(output_dir, f"{base_name}.mp4")

    def _get_duration(self):
        try:
            if self._mi_dll:
                media_info = MediaInfo.parse(self.input_path, library_file=self._mi_dll)
            else:
                media_info = MediaInfo.parse(self.input_path)
            for track in media_info.tracks:
                if track.track_type == "Video" and track.duration:
                    return float(track.duration) / 1000.0
        except Exception:
            pass
        return None

    def _print(self, msg: str):
        if not self.show_progress:
            return
        if self.print_lock is not None:
            with self.print_lock:
                sys.stdout.write(msg)
                sys.stdout.flush()
        else:
            sys.stdout.write(msg)
            sys.stdout.flush()

    def convert(self):
        if os.path.exists(self.output_path) and not self.overwrite:
            self._print(f"⚠️  Přeskočeno: {os.path.basename(self.output_path)}\n")
            return False

        # inicializace sdíleného progressu
        if self.progress_dict is not None:
            self.progress_dict[self._progress_key] = "⏳ 0.0%"

        cmd = [
            self.ffmpeg_path,
            "-y",
            "-i", self.input_path,
            "-c:v", "libx265",
            "-preset", "slow",
            "-crf", "28",
            "-c:a", "aac",
            "-b:a", "128k",
            self.output_path
        ]

        process = subprocess.Popen(
            cmd,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            cwd=_base_dir()
        )
        time_pattern = re.compile(r"time=(\d+):(\d+):(\d+\.\d+)")

        if process.stderr:
            for line in process.stderr:
                match = time_pattern.search(line)
                if match and self.duration:
                    h, m, s = match.groups()
                    current_time = int(h) * 3600 + int(m) * 60 + float(s)
                    percent = max(0.0, min(100.0, (current_time / self.duration) * 100.0))

                    # update shared progress for batch UI
                    if self.progress_dict is not None:
                        self.progress_dict[self._progress_key] = f"⏳ {percent:.1f}%"

                    # optional local console progress
                    if percent - self._last_percent_shown >= 0.5:
                        self._print(f"\r⏳ {percent:.1f}%")
                        self._last_percent_shown = percent

        process.wait()
        ok = (process.returncode == 0)

        # finální status do sdíleného slovníku
        if self.progress_dict is not None:
            self.progress_dict[self._progress_key] = "✅ Done" if ok else "❌ Error"

        # volitelný výstup do konzole
        self._print("\n✅ Hotovo\n" if ok else "\n❌ Chyba\n")
        return ok


if __name__ == "__main__":
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()

    test_input = filedialog.askopenfilename(
        title="Vyber vstupní video",
        filetypes=[("Video soubory", "*.mp4;*.mkv;*.avi;*.mov"), ("Všechny soubory", "*.*")]
    )

    if not test_input:
        print("❌ Nebyl vybrán žádný soubor, konec.")
        sys.exit(1)

    if not _find_tool("ffmpeg.exe"):
        download_and_extract_ffmpeg()

    if not _mediainfo_dll():
        download_and_extract_mediainfo()

    AnyToH265Converter(test_input, show_progress=True).convert()
