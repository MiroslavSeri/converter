import os
import sys
import time
import threading
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import Manager

from AnyToH265Converter import AnyToH265Converter
from download_ffmpeg import download_and_extract_ffmpeg
from download_MediaInfo import download_and_extract_mediainfo


# --- stabilní worker pro ProcessPool (top-level funkce) ---
def convert_one_file(file_path, progress_dict):
    try:
        conv = AnyToH265Converter(
            file_path,
            print_lock=None,
            progress_dict=progress_dict,
            show_progress=False,   # worker nic netiskne; progress jde přes dict
        )
        ok = conv.convert()
        return (file_path, ok, None)
    except Exception as e:
        return (file_path, False, str(e))


class BatchConverter:
    def __init__(self, input_dir="input", reserve_cores=2):
        # vstupní složka
        self.input_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), input_dir)

        # kolik jader použít
        total_cores = multiprocessing.cpu_count()
        self.max_workers = max(1, total_cores - reserve_cores)

        # podporované přípony
        self.supported_ext = (".mp4", ".avi", ".mkv", ".mov", ".flv", ".mpeg")

    def _get_video_files(self):
        if not os.path.exists(self.input_dir):
            raise FileNotFoundError(f"Folder '{self.input_dir}' does not exist.")
        return [
            os.path.join(self.input_dir, f)
            for f in os.listdir(self.input_dir)
            if f.lower().endswith(self.supported_ext)
        ]

    def _ensure_tools(self):
        # stáhni jednou dopředu, ať workery hned jedou
        download_and_extract_ffmpeg()
        download_and_extract_mediainfo()

    def convert_all(self):
        video_files = self._get_video_files()
        if not video_files:
            print("❌ No supported video files found in the folder.")
            return

        # zajisti binárky před startem poolu
        self._ensure_tools()

        print(f"🔁 Found {len(video_files)} videos. Starting conversion with {self.max_workers} processes...\n")

        with Manager() as manager:
            progress_dict = manager.dict()  # sdílený slovník: {basename: "⏳ xx.x%"/"✅ Done"/"❌ Error"}

            # vytvoř pool s explicitním 'spawn' (Windows-friendly)
            ctx = multiprocessing.get_context("spawn")
            with ProcessPoolExecutor(max_workers=self.max_workers, mp_context=ctx) as executor:
                futures = {
                    executor.submit(convert_one_file, path, progress_dict): path
                    for path in video_files
                }

                # --- vlákno, které průběžně tiskne tabulku progresu ---
                stop_flag = manager.Value('b', False)

                def print_loop():
                    last_count = 0
                    while not stop_flag.value:
                        items = sorted(progress_dict.items())  # [(basename, status), ...]
                        lines = ["📊 Conversion in progress:\n"]
                        for name, status in items:
                            lines.append(f"  {name:<40} {status}")
                        output = "\n".join(lines) + "\n"

                        # přepiš předchozí blok
                        if last_count > 0:
                            sys.stdout.write("\033[F" * last_count)
                        sys.stdout.write(output)
                        sys.stdout.flush()
                        last_count = len(lines) + 1
                        time.sleep(0.5)

                display_thread = threading.Thread(target=print_loop, daemon=True)
                display_thread.start()

                # čekej na dokončení jednotlivých úloh
                for fut in as_completed(futures):
                    file_path, ok, err = fut.result()
                    key = os.path.basename(file_path)
                    progress_dict[key] = "✅ Done" if ok else f"❌ Error: {err or ''}"

                # ukonči tisk a dočisti
                stop_flag.value = True
                display_thread.join()

        print("\n🎉 All conversions finished.")


if __name__ == "__main__":
    multiprocessing.freeze_support()  # bezpečné i v terminálu
    reserve_cores = 2
    batch = BatchConverter(input_dir="input", reserve_cores=reserve_cores)
    batch.convert_all()
