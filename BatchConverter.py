# BatchConverter.py
import os, sys, time, threading, multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import Manager
from collections import deque
import subprocess

from pymediainfo import MediaInfo  # ⬅️ kvůli _is_hevc
from download_ffmpeg import download_and_extract_ffmpeg
from download_MediaInfo import download_and_extract_mediainfo

RAW_HEVC_EXT = {".hevc", ".h265", ".265"}  # ⬅️ raw HEVC bez kontejneru

def _enable_vt_output():
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

def _find_tool(name: str) -> str | None:
    b = _base_dir()
    meipass = getattr(sys, "_MEIPASS", None)
    for p in (
        os.path.join(b, name),
        os.path.join(b, "_internal", name),
        os.path.join(meipass, name) if meipass else "",
        os.path.join(meipass, "_internal", name) if meipass else "",
    ):
        if p and os.path.isfile(p):
            return p
    from shutil import which
    return which(name)

def _mediainfo_dll() -> str | None:
    b = _base_dir()
    meipass = getattr(sys, "_MEIPASS", None)
    for p in (
        os.path.join(b, "MediaInfo.dll"),
        os.path.join(b, "_internal", "MediaInfo.dll"),
        os.path.join(meipass, "MediaInfo.dll") if meipass else "",
        os.path.join(meipass, "_internal", "MediaInfo.dll") if meipass else "",
    ):
        if p and os.path.isfile(p):
            return p
    return None

# ------------------ HEVC detekce + remux (JEDNODUŠE) ------------------

def _is_hevc(path: str) -> bool:
    """True, pokud je soubor HEVC/H.265 (včetně raw .hevc/.h265/.265)."""
    ext = os.path.splitext(path)[1].lower()
    if ext in RAW_HEVC_EXT:
        return True
    try:
        mi = MediaInfo.parse(path)
        for t in mi.tracks:
            if t.track_type == "Video":
                fmt = (getattr(t, "format", "") or "").lower()
                cid = (getattr(t, "codec_id", "") or "").lower()
                if "hevc" in fmt or "h265" in fmt or "hvc1" in cid or "hev1" in cid or "hevc" in cid:
                    return True
    except Exception:
        pass
    return False

def _ffmpeg_copy_remux(input_path: str, progress_dict, key: str) -> tuple[bool, str | None]:
    """Rychlý remux bez rekomprese. Raw HEVC → -f hevc + výstup .mkv, jinak zachová kontejner."""
    ff = _find_tool("ffmpeg.exe")
    if not ff:
        return False, "ffmpeg.exe not found"

    ext = os.path.splitext(input_path)[1].lower()
    base = os.path.splitext(os.path.basename(input_path))[0]
    out_dir = os.path.join(_base_dir(), "output")
    os.makedirs(out_dir, exist_ok=True)

    input_opts = []
    if ext in RAW_HEVC_EXT:
        input_opts = ["-f", "hevc"]
        out_path = os.path.join(out_dir, base + ".mkv")
    else:
        out_path = os.path.join(out_dir, base + ext)

    # nech stav neutrální ("⏳ 0.0%") – nastavuje ho worker

    cmd = [
        ff,
        "-hide_banner", "-v", "error", "-nostdin",
        "-y",
        *input_opts,
        "-i", input_path,
        "-c", "copy",
        out_path
    ]

    last = deque(maxlen=8)
    p = subprocess.Popen(cmd, stderr=subprocess.PIPE, universal_newlines=True, cwd=_base_dir())
    if p.stderr:
        for line in p.stderr:
            ls = (line or "").strip()
            if ls:
                last.append(ls)
    p.wait()
    ok = (p.returncode == 0)
    err = None if ok else ("\n".join(last) or "ffmpeg copy failed")

    if progress_dict is not None:
        progress_dict[key] = "✅ Done" if ok else f"❌ Error: {err}"
    return ok, err

# ------------------ Worker ------------------

def convert_one_file(file_path, progress_dict):
    try:
        base = os.path.basename(file_path)

        # Před startem nastav neutrální stav
        if progress_dict is not None:
            progress_dict[base] = "⏳ 0.0%"

        # HEVC? -> remux; jinak transcode přes AnyToH265Converter
        if _is_hevc(file_path):
            ok, err = _ffmpeg_copy_remux(file_path, progress_dict, base)
            return (file_path, ok, err)
        else:
            from AnyToH265Converter import AnyToH265Converter
            conv = AnyToH265Converter(
                file_path,
                progress_dict=progress_dict,
                show_progress=False
            )
            ok = conv.convert()
            err = getattr(conv, "last_error", "")
            return (file_path, ok, err if not ok else None)

    except Exception as e:
        return (file_path, False, str(e))

# ------------------ Třída BatchConverter ------------------

class BatchConverter:
    def __init__(self, input_dir="input", reserve_cores=2):
        self.input_dir = os.path.join(_base_dir(), input_dir)
        total_cores = multiprocessing.cpu_count()
        self.max_workers = max(1, total_cores - reserve_cores)
        self.supported_ext = (".mp4", ".avi", ".mkv", ".mov", ".flv", ".mpeg", ".mpg", ".hevc", ".h265", ".265")

    def _get_video_files(self):
        if not os.path.exists(self.input_dir):
            raise FileNotFoundError(f"Folder '{self.input_dir}' does not exist.")
        return [
            os.path.join(self.input_dir, f)
            for f in os.listdir(self.input_dir)
            if f.lower().endswith(self.supported_ext)
        ]

    def _ensure_tools(self):
        # stáhni jen pokud opravdu chybí (MEIPASS-aware)
        if _find_tool("ffmpeg.exe"):
            print("✅ ffmpeg.exe already exists.")
        else:
            download_and_extract_ffmpeg()

        if _mediainfo_dll():
            print("✅ MediaInfo.dll už existuje.")
        else:
            download_and_extract_mediainfo()

    def convert_all(self):
        files = self._get_video_files()
        if not files:
            print("❌ No supported video files found in the folder.")
            return

        self._ensure_tools()
        print(f"🔁 Found {len(files)} videos. Starting conversion with {self.max_workers} processes...\n")

        final_items = []

        with Manager() as manager:
            progress_dict = manager.dict()

            ctx = multiprocessing.get_context("spawn")
            with ProcessPoolExecutor(max_workers=self.max_workers, mp_context=ctx) as executor:
                futures = {executor.submit(convert_one_file, p, progress_dict): p for p in files}

                stop_event = threading.Event()

                def printer():
                    last = 0
                    while not stop_event.is_set():
                        try:
                            items = list(progress_dict.items())
                        except (BrokenPipeError, EOFError):
                            break
                        lines = ["📊 Conversion in progress:\n"]
                        for k, v in sorted(items):
                            name = k if len(k) <= 40 else k[:37] + "..."
                            lines.append(f"  {name:<40} {v}")
                        out = "\n".join(lines) + "\n"
                        if last:
                            try:
                                sys.stdout.write(f"\x1b[{last}F")
                            except Exception:
                                pass
                        sys.stdout.write(out); sys.stdout.flush()
                        last = len(lines) + 1
                        if all(f.done() for f in futures):
                            break
                        time.sleep(0.5)

                t = threading.Thread(target=printer, daemon=True)
                t.start()

                for fut in as_completed(futures):
                    fp, ok, err = fut.result()
                    progress_dict[os.path.basename(fp)] = "✅ Done" if ok else f"❌ Error: {err or ''}"

                stop_event.set()
                t.join()

                # snapshot ještě uvnitř Manageru
                try:
                    final_items = sorted(list(progress_dict.items()))
                except Exception:
                    final_items = []

        print("\n📊 Final status:")
        for k, v in final_items:
            print(f"  {k:<40} {v}")
        print("\n🎉 All conversions finished.")

if __name__ == "__main__":
    _enable_vt_output()
    multiprocessing.freeze_support()
    BatchConverter(input_dir="input", reserve_cores=2).convert_all()
