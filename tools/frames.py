"""Sample N frames from a video into one contact sheet:  python tools/frames.py video.mp4 out.png [N]"""
import sys
import av
from PIL import Image

path, out = sys.argv[1], sys.argv[2]
n = int(sys.argv[3]) if len(sys.argv) > 3 else 9
frames = [f.to_image() for f in av.open(path).decode(video=0)]
picks = [frames[int(i * (len(frames) - 1) / (n - 1))] for i in range(n)]
w, h = picks[0].size
cols = 3
sheet = Image.new("RGB", (w * cols, h * ((n + cols - 1) // cols)))
for k, im in enumerate(picks):
    sheet.paste(im, ((k % cols) * w, (k // cols) * h))
sheet.save(out)
print(f"{len(frames)} frames, {len(frames)/30:.1f}s at 30fps (approx)")
