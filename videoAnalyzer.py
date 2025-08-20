import os
from pymediainfo import MediaInfo
import tkinter as tk
from tkinter import filedialog

class VideoAnalyzer:
    def __init__(self, file_path):
        # Check if the given path exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File does not exist: {file_path}")
        # Check if the path points to a file (not a directory)
        if not os.path.isfile(file_path):
            raise ValueError(f"Given path is not a file: {file_path}")

        self.file_path = file_path
        self.video_format = None
        self.audio_format = None
        # Perform analysis when the object is created
        self._analyze()

    def _analyze(self):
        """Extract video and audio information using pymediainfo"""
        try:
            media_info = MediaInfo.parse(self.file_path)

            for track in media_info.tracks:
                # Extract video information (only the first video track)
                if track.track_type == 'Video' and self.video_format is None:
                    self.video_format = {
                        'codec': track.codec,
                        'format': track.format,
                        'width': track.width,
                        'height': track.height,
                        'frame_rate': track.frame_rate
                    }
                # Extract audio information (only the first audio track)
                elif track.track_type == 'Audio' and self.audio_format is None:
                    self.audio_format = {
                        'codec': track.codec,
                        'format': track.format,
                        'channels': track.channel_s,
                        'sampling_rate': track.sampling_rate
                    }
        except Exception as e:
            print(f"⚠️ Error while analyzing file: {e}")

    def get_video_format(self):
        """Return video metadata dictionary"""
        return self.video_format

    def get_audio_format(self):
        """Return audio metadata dictionary"""
        return self.audio_format

    def is_media(self):
        """Check if the file contains at least one video or audio track"""
        return self.video_format is not None or self.audio_format is not None
    
def select_video_file():
    """Open file dialog for selecting a video file (starting in script folder)"""
    # Get the directory where the current script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Create hidden root window for the file dialog
    root = tk.Tk()
    root.withdraw()   # hide the empty main window
    root.update()     # ensure the dialog appears on top

    # Open file dialog limited to common video file types
    file_path = filedialog.askopenfilename(
        title="Select a video file",
        initialdir=script_dir,
        filetypes=[("Video files", "*.mp4 *.mkv *.avi *.mov *.flv *.wmv *.mpeg *.mpg")]
    )

    # Destroy the hidden root window after use
    root.destroy()

    # Return the selected file path (empty string if cancelled)
    return file_path

if __name__ == "__main__":
    path = select_video_file()
    
    try:
        analyzer = VideoAnalyzer(path)

        if not analyzer.is_media():
            print("❌ File does not contain any video or audio tracks.")
        else:
            video = analyzer.get_video_format()
            audio = analyzer.get_audio_format()

            # Print video information if available
            if video:
                print("🎥 Video:")
                for k, v in video.items():
                    print(f"  {k.capitalize()}: {v}")
            else:
                print("❌ No video track found.")

            # Print audio information if available
            if audio:
                print("🔊 Audio:")
                for k, v in audio.items():
                    print(f"  {k.capitalize()}: {v}")
            else:
                print("❌ No audio track found.")

    except Exception as e:
        print(f"❗ Error: {e}")
