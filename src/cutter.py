import os
import subprocess

def cortar(start, end, index):
    out = f"output/clips/clip_{index:02}.mp4"
    os.makedirs(os.path.dirname(out), exist_ok=True)

    subprocess.run([
        "ffmpeg", "-y",
        "-threads", "4",
        "-i", "input/video.mp4",
        "-ss", str(start),
        "-to", str(end),
        "-c:v", "libx264",
        "-c:a", "aac",
        out
    ], check=True)

    return out
