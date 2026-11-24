# xxj-summer-zjl
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from camera import Camera


class CameraTest(unittest.TestCase):
    def test_stopped_worker_never_acquires_device(self):
        worker=Camera()
        worker.stop_event.set()
        opened=[]
        detector=SimpleNamespace(close=lambda:None)
        landmarker=SimpleNamespace(create_from_options=lambda _:detector)
        mp=SimpleNamespace(tasks=SimpleNamespace(BaseOptions=lambda **_:None,
            vision=SimpleNamespace(HandLandmarker=landmarker,HandLandmarkerOptions=lambda **_:None,
                                   RunningMode=SimpleNamespace(VIDEO=1))))
        cv=SimpleNamespace(VideoCapture=lambda *_:opened.append(True),CAP_AVFOUNDATION=1)
        with patch.dict(sys.modules,{'cv2':cv,'mediapipe':mp}):
            worker._run()
        self.assertEqual(opened,[])
        self.assertEqual(worker.status,'摄像头已关闭 · C 开启')

    def test_permission_api_failure_does_not_crash_app(self):
        def broken(_): raise RuntimeError('permission service unavailable')
        api=SimpleNamespace(AVCaptureDevice=SimpleNamespace(authorizationStatusForMediaType_=broken),
                            AVMediaTypeVideo='video')
        worker=Camera()
        with patch.dict(sys.modules,{'AVFoundation':api}): worker.start()
        self.assertIn('暂不可用',worker.status)
        self.assertIsNone(worker.thread)
