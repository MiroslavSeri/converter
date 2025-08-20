import os
import subprocess
import re
import sys
from pymediainfo import MediaInfo
from download_ffmpeg import download_and_extract_ffmpeg
from download_MediaInfo import download_and_extract_mediainfo


class AnyToH265Converter:
    def __init__(self, input_path, output_path=None, overwrite=True, print_lock=None, progress_dict=None, show_progress=False):
        self.input_path = input_path
        if not os.path.exists(self.input_path):
            raise FileNotFoundError(f"Soubor neexistuje: {self.input_path}")  # check file exists

        self.output_path = output_path or self._build_output_path()          # build default output path if not given
        self.overwrite = overwrite                                           # overwrite existing files?
        self.ffmpeg_path = os.path.join(os.path.dirname(__file__), "ffmpeg.exe")  # assume ffmpeg.exe is next to script
        self.duration = self._get_duration()                                 # get video duration for progress
        self.print_lock = print_lock                                         # optional print lock for threading
        self.progress_dict = progress_dict                                   # optional dict to store progress
        self.show_progress = show_progress                                   # show progress to console?
        self._last_percent_shown = -1                                        # track last shown percent (unused here)

    def _build_output_path(self):
        base_name = os.path.splitext(os.path.basename(self.input_path))[0]   # get file name without extension
        output_dir = os.path.join(os.path.dirname(__file__), "output")       # create ./output directory
        os.makedirs(output_dir, exist_ok=True)
        return os.path.join(output_dir, f"{base_name}.mp4")                  # return output path in ./output

    def _get_duration(self):
        media_info = MediaInfo.parse(self.input_path)                        # analyze file with MediaInfo
        for track in media_info.tracks:
            if track.track_type == "Video" and track.duration:               # first video track with duration
                return float(track.duration) / 1000  # ms → s
        return None

    def _print_progress(self, current_time):
        if self.duration:                                                    # only if duration is known
            percent = (current_time / self.duration) * 100                   # calculate percent
            # if percent - self._last_percent_shown >= 1:                    # throttling (disabled)
            self._last_percent_shown = percent                               # store last percent
            if self.progress_dict is not None:
                self.progress_dict[os.path.basename(self.input_path)] = f"{percent:.1f}%"  # update dict
            if self.show_progress:
                sys.stdout.write(f"\r⏳ {os.path.basename(self.input_path)}: {percent:.1f}%")  # print on same line
                sys.stdout.flush()

    def _print(self, message):
        if self.show_progress:                                               # only if progress printing is enabled
            if self.print_lock:                                              # if lock is used (multiprocessing)
                with self.print_lock:
                    print(message)
            else:
                print(message)

    def convert(self):
        if os.path.exists(self.output_path) and not self.overwrite:          # skip if output exists and overwrite=False
            self._print(f"⚠️  Přeskočeno (existuje): {os.path.basename(self.output_path)}")
            return False

        cmd = [
            self.ffmpeg_path,                                                # ffmpeg executable
            "-i", self.input_path,                                           # input file
            "-c:v", "libx265",                                               # use H.265 codec
            "-preset", "slow",                                               # encoding speed vs compression
            "-crf", "28",                                                    # quality factor (lower = better quality)
            "-c:a", "aac",                                                   # audio codec
            "-b:a", "128k",                                                  # audio bitrate
            self.output_path                                                 # output file
        ]

        if self.overwrite:
            cmd.append("-y")                                                 # force overwrite

        process = subprocess.Popen(cmd, stderr=subprocess.PIPE, universal_newlines=True)  # run ffmpeg
        time_pattern = re.compile(r"time=(\d+):(\d+):(\d+\.\d+)")            # regex to parse "time=hh:mm:ss.xx"

        try:
            for line in process.stderr:                                      # read stderr line by line
                match = time_pattern.search(line)
                if match:
                    h, m, s = match.groups()
                    current_time = int(h) * 3600 + int(m) * 60 + float(s)    # convert time to seconds
                    self._print_progress(current_time)                       # update progress

            process.wait()                                                   # wait for ffmpeg to finish
            self._print(f"\n✅ Hotovo: {os.path.basename(self.output_path)}") # print success
            return process.returncode == 0                                   # True if ffmpeg exited cleanly

        except Exception as e:
            self._print(f"\n❌ Chyba při převodu: {e}")                       # print error
            return False


# 🔧 Example usage (test main)
if __name__ == "__main__":
    test_input = os.path.join(os.path.dirname(__file__), "input", "1.mp4")   # test input in ./input/1.mp4
    download_and_extract_ffmpeg()                                            # make sure ffmpeg is available
    download_and_extract_mediainfo()                                         # make sure mediainfo is available
    if not os.path.exists(test_input):
        print(f"❌ Testovací soubor neexistuje: {test_input}")
    else:
        converter = AnyToH265Converter(test_input, show_progress=True)       # create converter
        converter.convert()                                                  # run conversion
