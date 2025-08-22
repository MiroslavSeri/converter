# BatchConverter.py
import os, sys, time, threading, multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import Manager

from download_ffmpeg import download_and_extract_ffmpeg
from download_MediaInfo import download_and_extract_mediainfo

def _enable_vt_output():
    # Povolit ANSI/VT v klasickém cmd/PowerShell
    if os.name == "nt":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            STD_OUTPUT_HANDLE = -11
            h = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
            mode = ctypes.c_uint()
            if kernel32.GetConsoleMode(h, ctypes.byref(mode)):
                ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
                kernel32.SetConsoleMode(h, mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING)
        except Exception:
            pass

def _base_dir():
    return os.path.dirname(sys.executable) if getattr(sys, "frozen", False) \
           else os.path.dirname(os.path.abspath(__file__))

# --- top-level worker, kvůli Windows + PyInstaller ---
def convert_one_file(file_path, progress_dict):
    try:
        from AnyToH265Converter import AnyToH265Converter
        conv = AnyToH265Converter(
            file_path,
            progress_dict=progress_dict,
            show_progress=False  # worker netiskne do konzole
        )
        ok = conv.convert()
        return (file_path, ok, None)
    except Exception as e:
        return (file_path, False, str(e))

class BatchConverter:
    def __init__(self, input_dir="input", reserve_cores=2):
        self.input_dir = os.path.join(_base_dir(), input_dir)
        total_cores = multiprocessing.cpu_count()
        self.max_workers = max(1, total_cores - reserve_cores)
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
        # stáhni binárky jednou dopředu (vedle .exe / .py)
        download_and_extract_ffmpeg()
        download_and_extract_mediainfo()

    def convert_all(self):
        files = self._get_video_files()
        if not files:
            print("❌ No supported video files found in the folder.")
            return

        # zajisti ffmpeg + MediaInfo před startem workerů
        self._ensure_tools()

        print(f"🔁 Found {len(files)} videos. Starting conversion with {self.max_workers} processes...\n")

        with Manager() as manager:
            progress_dict = manager.dict()

            ctx = multiprocessing.get_context("spawn")
            with ProcessPoolExecutor(max_workers=self.max_workers, mp_context=ctx) as executor:
                futures = {executor.submit(convert_one_file, p, progress_dict): p for p in files}

                stop = False
                def printer():
                    last = 0
                    while not stop:
                        lines = ["📊 Conversion in progress:\n"]
                        for k, v in sorted(progress_dict.items()):
                            lines.append(f"  {k:<40} {v}")
                        out = "\n".join(lines) + "\n"
                        if last:
                            try:
                                sys.stdout.write("\033[F" * last)
                            except Exception:
                                pass
                        sys.stdout.write(out)
                        sys.stdout.flush()
                        last = len(lines) + 1
                        if all(f.done() for f in futures):
                            break
                        time.sleep(0.5)

                t = threading.Thread(target=printer, daemon=True)
                t.start()

                for fut in as_completed(futures):
                    fp, ok, err = fut.result()
                    progress_dict[os.path.basename(fp)] = "✅ Done" if ok else f"❌ Error: {err or ''}"

                stop = True
                t.join()

        # finální snapshot
        print("\n📊 Final status:")
        for k, v in sorted(progress_dict.items()):
            print(f"  {k:<40} {v}")

        print("\n🎉 All conversions finished.")

if __name__ == "__main__":
    _enable_vt_output()
    multiprocessing.freeze_support()   # důležité pro Windows/EXE
    BatchConverter(input_dir="input", reserve_cores=2).convert_all()
