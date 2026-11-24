# xxj-summer-zjl
"""Download the MediaPipe hand landmark model for local gesture recognition."""
from pathlib import Path
from urllib.request import urlretrieve
import hashlib

URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
SHA256 = "fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1"
model = Path(__file__).parent / "assets" / "hand_landmarker.task"
model.parent.mkdir(exist_ok=True)
if not model.exists():
    urlretrieve(URL, model)
if hashlib.sha256(model.read_bytes()).hexdigest() != SHA256:
    model.unlink(missing_ok=True)
    raise SystemExit("模型校验失败，请检查下载地址后重试")
print("手势模型准备完成")
