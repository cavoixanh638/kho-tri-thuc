"""Read one bounded video frame from a local staging file."""

import subprocess
from io import BytesIO
from pathlib import Path

from PIL import Image

_VIDEO_FORMATS = "mov,matroska,webm,avi,mpeg,mpegts,flv,ogg"
_VIDEO_MAX_PIXELS = 33_554_432
_VIDEO_TIMEOUT = 15


class VideoThumbnailError(Exception):
    """A reason to fall back to a video placeholder."""


def read_video_frame(source: Path, max_edge: int, ffmpeg: str | Path) -> Image.Image:
    # Size for the display aspect ratio, including non-square source pixels.
    display_width = "max(1,ih*dar)"
    factor = f"min(1,{max_edge}/max({display_width},ih))"
    scale = (
        f"scale=w='max(1,round({display_width}*{factor}))':"
        f"h='max(1,round(ih*{factor}))',setsar=1"
    )
    command = [
        str(ffmpeg),
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-protocol_whitelist",
        "file",
        "-format_whitelist",
        _VIDEO_FORMATS,
        "-threads",
        "1",
        "-max_pixels",
        str(_VIDEO_MAX_PIXELS),
        "-i",
        str(source),
        "-map",
        "0:V:0",
        "-frames:v",
        "1",
        "-filter_threads",
        "1",
        "-vf",
        scale,
        "-threads",
        "1",
        "-pix_fmt",
        "rgb24",
        "-c:v",
        "png",
        "-f",
        "image2pipe",
        "pipe:1",
    ]
    try:
        completed = subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=_VIDEO_TIMEOUT,
            check=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except FileNotFoundError as error:
        raise VideoThumbnailError("ffmpeg_unavailable") from error
    except subprocess.TimeoutExpired as error:
        raise VideoThumbnailError("video_timeout") from error
    except subprocess.CalledProcessError as error:
        raise VideoThumbnailError("invalid_video") from error

    try:
        with Image.open(BytesIO(completed.stdout), formats=["PNG"]) as frame:
            if max(frame.size) > max_edge:
                raise VideoThumbnailError("invalid_video")
            return frame.convert("RGB")
    except (OSError, Image.DecompressionBombError) as error:
        raise VideoThumbnailError("invalid_video") from error
