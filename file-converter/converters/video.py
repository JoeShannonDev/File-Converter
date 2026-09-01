"""Video/audio format conversion via a bundled ffmpeg binary."""
import subprocess
from pathlib import Path

import imageio_ffmpeg

VIDEO_FORMATS = ["mp4", "mov", "avi", "mkv", "webm", "gif"]
AUDIO_FORMATS = ["mp3", "wav", "flac", "m4a", "ogg"]

SUPPORTED_INPUT_EXTENSIONS = {
    ".mp4", ".mov", ".avi", ".mkv", ".webm",
    ".mp3", ".wav", ".flac", ".m4a", ".ogg",
}


def convert_video(input_path: str, output_path: str, target_format: str) -> str:
    """Convert a video/audio file to the target format using ffmpeg."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ffmpeg_exe, "-y", "-i", str(input_path)]

    # Converting to an audio-only format from a video file: drop video stream.
    if target_format.lower() in AUDIO_FORMATS and Path(input_path).suffix.lower() not in {
        ".mp3", ".wav", ".flac", ".m4a", ".ogg"
    }:
        cmd += ["-vn"]

    cmd.append(str(out))

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{result.stderr[-2000:]}")
    return str(out)
