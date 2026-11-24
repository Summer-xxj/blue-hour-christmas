# xxj-summer-zjl
import unittest
import numpy as np
from story import Story
from gestures import GestureController, Hand
from particles import ParticleCloud

class StoryTests(unittest.TestCase):
    def test_full_camera_gesture_sequence(self):
        story=Story(); controller=GestureController(); now=1.
        for gesture,stage in zip(('tree','1','2','3','fist','tree'),Story.sequence[1:]):
            for _ in range(9):
                now+=.1
                controller.update([Hand(gesture, .5, .5)],now)
                if controller.progress>=1:
                    story.accept(controller.candidate,now)
            self.assertEqual(story.stage,stage)
        story.accept('1',now+1)
        self.assertEqual(story.stage,'tree')
        story.reset(); self.assertEqual(story.stage,'empty')

    def test_no_skipping_or_repeated_open(self):
        s=Story()
        self.assertFalse(s.accept('3',1))
        self.assertTrue(s.accept('tree',2))
        for i in range(20): s.accept('tree',3+i)
        self.assertEqual(s.stage,'heart')
        s.accept('fist',30); self.assertEqual(s.stage,'heart')

    def test_new_targets_converge(self):
        p=ParticleCloud(1200)
        for shape in ('empty','heart','core','tree'):
            p.set_shape(shape)
            for _ in range(240): p.step(1/60,1)
            self.assertTrue(np.isfinite(p.positions).all())
            self.assertLess(np.mean(np.abs(p.positions-p.targets[shape])),.01)
        self.assertLess(np.max(np.linalg.norm(p.targets['core'],axis=1)),.07)
