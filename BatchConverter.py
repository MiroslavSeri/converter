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
        # Make sure ffmpeg and mediainfo are available before starting
        download_and_extract_ffmpeg()
        download_and_extract_mediainfo()

        # Input folder with videos
        self.input_dir = os.path.join(os.path.dirname(__file__), input_dir)

        # Decide how many CPU cores to use (reserve some for the system)
        total_cores = multiprocessing.cpu_count()
        self.max_workers = max(1, total_cores - reserve_cores)

        # Supported video formats
        self.supported_ext = (".mp4", ".avi", ".mkv", ".mov", ".flv", ".mpeg")

    def _get_video_files(self):
        """Return a list of all supported video files inside the input directory."""
        if not os.path.exists(self.input_dir):
            raise FileNotFoundError(f"Folder '{self.input_dir}' does not exist.")
        return [
            os.path.join(self.input_dir, f)
            for f in os.listdir(self.input_dir)
            if f.lower().endswith(self.supported_ext)
        ]

    def _convert_file(self, file_path, print_lock, progress_dict):
        """Convert a single video file using AnyToH265Converter."""
        try:
            converter = AnyToH265Converter(file_path, print_lock=print_lock, progress_dict=progress_dict)
            success = converter.convert()
            return (file_path, success, None)
        except Exception as e:
            # Return error details if conversion failed
            return (file_path, False, str(e))

    def convert_all(self):
        """Convert all supported video files in the input directory in parallel."""
        video_files = self._get_video_files()
        if not video_files:
            print("❌ No supported video files found in the folder.")
            return

        print(f"🔁 Found {len(video_files)} videos. Starting conversion with {self.max_workers} processes...\n")

        # Use a multiprocessing.Manager to share state across processes
        with Manager() as manager:
            print_lock = manager.Lock()       # Shared lock for synchronized printing
            progress_dict = manager.dict()    # Shared dictionary for conversion progress

            # Create a process pool for parallel video conversion
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {
                    executor.submit(self._convert_file, path, print_lock, progress_dict): path
                    for path in video_files
                }

                # Background thread that continuously prints conversion progress
                def print_loop():
                    last_output_line_count = 0
                    while not all(f.done() for f in futures):
                        lines = ["📊 Conversion in progress:\n"]

                        # Display progress of each file
                        for filename in sorted(progress_dict.keys()):
                            lines.append(f"  {filename:<30} {progress_dict[filename]}")

                        output = "\n".join(lines)

                        # Move cursor up to overwrite previous progress output
                        if last_output_line_count > 0:
                            sys.stdout.write("\033[F" * last_output_line_count)

                        sys.stdout.write(output + "\n")
                        sys.stdout.flush()

                        # Update how many lines were printed last time
                        last_output_line_count = len(lines) + 1
                        time.sleep(0.5)

                # Start the display thread
                display_thread = threading.Thread(target=print_loop)
                display_thread.start()

                # Wait for each conversion to finish and update progress
                for future in as_completed(futures):
                    file_path, success, error = future.result()
                    name = os.path.basename(file_path)
                    progress_dict[name] = "✅ Done" if success else f"❌ Error: {error}"

                # Wait until the progress printing thread finishes
                display_thread.join()

            print("\n🎉 All conversions finished.")


if __name__ == "__main__":
    reserve_cores = 2
    batch = BatchConverter(input_dir="input", reserve_cores=reserve_cores)
    batch.convert_all()
