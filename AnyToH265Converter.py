import os
import subprocess
import re
import sys
from pymediainfo import MediaInfo


class AnyToH265Converter:
    def __init__(self, input_path, output_path=None, overwrite=True, print_lock=None, progress_dict=None, show_progress=False):

        self.input_path = input_path
        if not os.path.exists(self.input_path):
            raise FileNotFoundError(f"Soubor neexistuje: {self.input_path}")

        self.output_path = output_path or self._build_output_path()
        self.overwrite = overwrite
        self.ffmpeg_path = os.path.join(os.path.dirname(__file__), "ffmpeg.exe")
        self.duration = self._get_duration()
        self.print_lock = print_lock
        self.progress_dict = progress_dict
        self.show_progress = show_progress
        self._last_percent_shown = -1

    def _build_output_path(self):
        base_name = os.path.splitext(os.path.basename(self.input_path))[0]
        output_dir = os.path.join(os.path.dirname(__file__), "output")
        os.makedirs(output_dir, exist_ok=True)
        return os.path.join(output_dir, f"{base_name}.mp4")

    def _get_duration(self):
        media_info = MediaInfo.parse(self.input_path)
        for track in media_info.tracks:
            if track.track_type == "Video" and track.duration:
                return float(track.duration) / 1000  # ms → s
        return None

    def _print_progress(self, current_time):
        if self.duration:
            percent = (current_time / self.duration) * 100
           # if percent - self._last_percent_shown >= 1:
            self._last_percent_shown = percent
            if self.progress_dict is not None:
                self.progress_dict[os.path.basename(self.input_path)] = f"{percent:.1f}%"
            if self.show_progress:
                sys.stdout.write(f"\r⏳ {os.path.basename(self.input_path)}: {percent:.1f}%")
                sys.stdout.flush()

    def _print(self, message):
        if self.show_progress:
            if self.print_lock:
                with self.print_lock:
                    print(message)
            else:
                print(message)

    def convert(self):
        if os.path.exists(self.output_path) and not self.overwrite:
            self._print(f"⚠️  Přeskočeno (existuje): {os.path.basename(self.output_path)}")
            return False

     #   self._print(f"🔄 Převádím {os.path.basename(self.input_path)} → {self.output_path}")

        cmd = [
            self.ffmpeg_path,
            "-i", self.input_path,
            "-c:v", "libx265",
            "-preset", "slow",
            "-crf", "28",
            "-c:a", "aac",
            "-b:a", "128k",
            self.output_path
        ]

        if self.overwrite:
            cmd.append("-y")

        process = subprocess.Popen(cmd, stderr=subprocess.PIPE, universal_newlines=True)
        time_pattern = re.compile(r"time=(\d+):(\d+):(\d+\.\d+)")

        try:
            for line in process.stderr:
                match = time_pattern.search(line)
                if match:
                    h, m, s = match.groups()
                    current_time = int(h) * 3600 + int(m) * 60 + float(s)
                    self._print_progress(current_time)

            process.wait()
            self._print(f"\n✅ Hotovo: {os.path.basename(self.output_path)}")
            return process.returncode == 0

        except Exception as e:
            self._print(f"\n❌ Chyba při převodu: {e}")
            return False


# 🔧 Ukázka použití (testovací main)
if __name__ == "__main__":
    test_input = os.path.join(os.path.dirname(__file__), "input", "1.mp4")
    if not os.path.exists(test_input):
        print(f"❌ Testovací soubor neexistuje: {test_input}")
    else:
        converter = AnyToH265Converter(test_input, show_progress=True)
        converter.convert()
