# xxj-summer-zjl
import math
import unittest
import numpy as np
from gestures import Hand
from rotation import RotationController


def hand(x,y,gesture='1'):
    return Hand(gesture,.5,x,tuple((x,y) if i==8 else (.5,.7) for i in range(21)))

class RotationTests(unittest.TestCase):
    def circle(self,fps,direction=1):
        r=RotationController(); total=0
        for t in np.arange(0,2+1/fps,1/fps):
            a=direction*t*math.pi
            total+=r.update(hand(.5+.04*math.cos(a),.5+.04*math.sin(a)),float(t))
        return total

    def test_small_circles_work_in_both_directions_and_frame_rates(self):
        for fps in (15,24,30,60):
            self.assertGreater(self.circle(fps),4.)
            self.assertLess(self.circle(fps,-1),-4.)

    def test_stationary_jitter_does_not_spin(self):
        r=RotationController(); rng=np.random.default_rng(44); total=0
        for i in range(180):
            x,y=rng.normal(.5,.0005,2)
            total+=r.update(hand(x,y),i/30)
        self.assertLess(abs(total),.08)

    def test_slow_horizontal_motion_accumulates(self):
        r=RotationController(); total=0
        for i in range(120): total+=r.update(hand(.4+i*.001,.5),i/60)
        self.assertGreater(total,.7)

    def test_tracking_loss_and_duplicate_frame_do_not_jump(self):
        r=RotationController()
        r.update(hand(.5,.5),1)
        self.assertEqual(r.update(hand(.8,.5),1),0)
        self.assertEqual(r.update(None,1.1),0)
        self.assertEqual(r.update(hand(.9,.5),1.2),0)
        self.assertEqual(r.update(hand(.1,.5),2),0)
        self.assertEqual(r.update(hand(.8,.5,'fist'),2.1),0)
