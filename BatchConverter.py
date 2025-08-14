
import os
import sys
import time
import threading
import multiprocessing

from concurrent.futures import ProcessPoolExecutor, as_completed
from AnyToH265Converter import AnyToH265Converter
from download_ffmpeg import download_and_extract_ffmpeg
from download_MediaInfo import download_and_extract_mediainfo
from multiprocessing import Manager


class BatchConverter:
    def __init__(self, input_dir="input", reserve_cores=2):
        download_and_extract_ffmpeg()
        download_and_extract_mediainfo()
        self.input_dir = os.path.join(os.path.dirname(__file__), input_dir)
        total_cores = multiprocessing.cpu_count()
        self.max_workers = max(1, total_cores - reserve_cores)
        self.supported_ext = (".mp4", ".avi", ".mkv", ".mov", ".flv", ".mpeg")

    def _get_video_files(self):
        if not os.path.exists(self.input_dir):
            raise FileNotFoundError(f"Složka '{self.input_dir}' neexistuje.")
        return [
            os.path.join(self.input_dir, f)
            for f in os.listdir(self.input_dir)
            if f.lower().endswith(self.supported_ext)
        ]

    def _convert_file(self, file_path, print_lock, progress_dict):
        try:
            converter = AnyToH265Converter(file_path, print_lock=print_lock, progress_dict=progress_dict)
            success = converter.convert()
            return (file_path, success, None)
        except Exception as e:
            return (file_path, False, str(e))

    def convert_all(self):
        video_files = self._get_video_files()
        if not video_files:
            print("❌ Ve složce nejsou žádné podporované video soubory.")
            return

        print(f"🔁 Nalezeno {len(video_files)} videí. Spouštím konverzi pomocí {self.max_workers} procesů...\n")

        with Manager() as manager:
            print_lock = manager.Lock()
            progress_dict = manager.dict()

            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {
                    executor.submit(self._convert_file, path, print_lock, progress_dict): path
                    for path in video_files
                }

                # 🧵 Tisková smyčka (uvnitř kvůli přístupu k `futures`)
                def print_loop():
                    last_output_line_count = 0
                    while not all(f.done() for f in futures):
                        lines = ["📊 Probíhá konverze:\n"]

                        for filename in sorted(progress_dict.keys()):
                            lines.append(f"  {filename:<30} {progress_dict[filename]}")

                        output = "\n".join(lines)

                        # Posuň kurzor nahoru podle předchozího výstupu
                        if last_output_line_count > 0:
                            sys.stdout.write("\033[F" * last_output_line_count)

                        sys.stdout.write(output + "\n")
                        sys.stdout.flush()

                        last_output_line_count = len(lines)+1
                        time.sleep(0.5)
                   

                display_thread = threading.Thread(target=print_loop)
                display_thread.start()

                for future in as_completed(futures):
                    file_path, success, error = future.result()
                    name = os.path.basename(file_path)
                    progress_dict[name] = "✅ Hotovo" if success else f"❌ Chyba: {error}"

                display_thread.join()

            print("\n🎉 Vše hotovo.")

if __name__ == "__main__":
    reserve_cores = 2
    batch = BatchConverter(input_dir="input", reserve_cores=reserve_cores)
    batch.convert_all()

