# xxj-summer-zjl
"""Local-only camera worker. Keeps inference away from the animation thread."""
from pathlib import Path
import os
import sys
import threading
import time
from math import dist
from gestures import Hand, classify

MODEL=Path(__file__).parent/'assets'/'hand_landmarker.task'
os.environ.setdefault('MPLCONFIGDIR',str(Path(__file__).parent/'.cache'/'matplotlib'))


class Camera:
    def __init__(self,index=None):
        self.index=index
        self.lock=threading.Lock()
        self.stop_event=threading.Event()
        self.thread=None
        self.hands=()
        self.timestamp=0.
        self.status='摄像头准备中…'
        self.preview=None
        self.show_preview=False

    def start(self):
        if self.thread and self.thread.is_alive(): return
        self.stop_event.clear()
        try:
            self._authorize()
        except Exception as exc:
            self._publish(status=f'摄像头暂不可用 · {type(exc).__name__}：{exc}')

    def _authorize(self):
        if sys.platform=='darwin':
            import AVFoundation as AV
            status=AV.AVCaptureDevice.authorizationStatusForMediaType_(AV.AVMediaTypeVideo)
            if status==0:
                self._publish(status='请在系统弹窗中允许摄像头 · 画面仅在本机识别')
                def authorized(granted):
                    if self.stop_event.is_set(): return
                    if granted: self._spawn()
                    else: self._publish(status='未获摄像头权限 · 请到系统设置中允许后重试')
                self._authorization_callback=authorized
                AV.AVCaptureDevice.requestAccessForMediaType_completionHandler_(AV.AVMediaTypeVideo,authorized)
                return
            if status!=3:
                self._publish(status='未获摄像头权限 · 请到系统设置中允许后重试')
                return
        self._spawn()

    def _spawn(self):
        self.thread=threading.Thread(target=self._run,daemon=True,name='hand-camera')
        self.thread.start()

    def snapshot(self):
        with self.lock:
            return self.hands,self.timestamp,self.status,self.preview

    def _publish(self,hands=(),status=None,preview=None):
        with self.lock:
            self.hands=tuple(hands)
            self.timestamp=time.monotonic()
            if status: self.status=status
            self.preview=preview

    def _run(self):
        cap=None
        detector=None
        try:
            if self.stop_event.is_set(): return
            import cv2
            import mediapipe as mp
            if self.stop_event.is_set(): return
            if not MODEL.exists():
                raise FileNotFoundError('缺少手部模型，请运行 setup.py')
            options=mp.tasks.vision.HandLandmarkerOptions(
                base_options=mp.tasks.BaseOptions(model_asset_path=str(MODEL)),
                running_mode=mp.tasks.vision.RunningMode.VIDEO,num_hands=2,
                min_hand_detection_confidence=.55,min_hand_presence_confidence=.55,
                min_tracking_confidence=.55)
            detector=mp.tasks.vision.HandLandmarker.create_from_options(options)
            if self.stop_event.is_set(): return
            index=self.index
            if index is None:
                import AVFoundation as AV
                devices=list(AV.AVCaptureDevice.devicesWithMediaType_(AV.AVMediaTypeVideo))
                index=next((i for i,d in enumerate(devices)
                            if any(word in str(d.localizedName()).lower()
                                   for word in ('macbook','facetime','built-in','内建','内置'))),None)
                if index is None:
                    self._publish(status='未找到内置摄像头 · 可用 --camera-index 指定其他摄像头')
                    return
                print('使用摄像头：'+str(devices[index].localizedName()),flush=True)
            cap=cv2.VideoCapture(index,cv2.CAP_AVFOUNDATION)
            if not cap.isOpened():
                self._publish(status='摄像头未开启 · 请允许摄像头权限，再按 C 重试')
                return
            cap.set(cv2.CAP_PROP_FRAME_WIDTH,640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT,480)
            last_ms=-1
            failures=0
            while not self.stop_event.is_set():
                started=time.monotonic()
                ok,frame=cap.read()
                if not ok:
                    failures+=1
                    if failures>12:
                        self._publish(status='摄像头画面中断 · 按 C 关闭，再按 C 重试')
                        return
                    self.stop_event.wait(.08)
                    continue
                failures=0
                rgb=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
                timestamp=max(last_ms+1,int(time.monotonic()*1000))
                last_ms=timestamp
                result=detector.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB,data=rgb),timestamp)
                hands=[]
                aspect=frame.shape[1]/frame.shape[0]
                for landmarks in result.hand_landmarks:
                    points=[(p.x*aspect,p.y,p.z*aspect) for p in landmarks]
                    palm=max(dist(points[0],points[9]),1e-6)
                    pinch=dist(points[4],points[8])/palm
                    mirrored=tuple((1-p.x,p.y) for p in landmarks)
                    hands.append(Hand(classify(points),pinch,1-landmarks[0].x,mirrored))
                preview=None
                if self.show_preview:
                    preview=cv2.resize(cv2.flip(rgb,1),(192,144)).tobytes()
                status=(f'已识别 {len(hands)} 只手' if hands else '摄像头已开启 · 抬起手试试看')
                self._publish(hands,status,preview)
                self.stop_event.wait(max(0.,1/24-(time.monotonic()-started)))
        except Exception as exc:
            self._publish(status=f'摄像头暂不可用 · {type(exc).__name__}：{exc}')
        finally:
            if cap is not None: cap.release()
            if detector is not None: detector.close()
            if self.stop_event.is_set(): self._publish(status='摄像头已关闭 · C 开启')

    def stop(self):
        self.stop_event.set()
        if self.thread: self.thread.join(timeout=2.)
