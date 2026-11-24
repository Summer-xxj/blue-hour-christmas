# xxj-summer-zjl
"""Behavioral fixtures: sustained finger poses should select, noise must not."""
import math
import unittest
try:
    from gestures import Hand, GestureController, classify
except ImportError:
    Hand = GestureController = classify = None


def pose(fingers, rotate=0):
    p = [(0., 0., 0.) for _ in range(21)]
    p[0] = (0., .9, 0.)
    for i, x in enumerate((-.22, -.07, .09, .24)):
        m = 5+4*i
        if i in fingers:
            ys = (.52, .27, .10, -.05)
        else:
            ys = (.52, .37, .49, .61)
        for j, y in enumerate(ys):
            p[m+j] = (x, y, 0.)
    p[1:5] = [(-.17,.70,0),(-.30,.64,0),(-.22,.58,0),(-.13,.60,0)]
    if rotate:
        c,s=math.cos(rotate),math.sin(rotate)
        p=[(x*c-y*s,x*s+y*c,z) for x,y,z in p]
    return p


class GesturesTest(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(classify, 'Gesture interpretation is not implemented')

    def test_digits_and_rotated_hands(self):
        for fingers, expected in [({0},'1'),({0,1},'2'),({0,1,2},'3'),({0,1,2,3},'tree')]:
            for rotation in (0, math.pi/2, -.8):
                self.assertEqual(classify(pose(fingers,rotation)), expected)

    def test_requires_stable_pose(self):
        c=GestureController()
        hand=Hand('2',.6,.25)
        c.update([hand],0.)
        c.update([hand],.2)
        self.assertEqual(c.shape,'tree')
        c.update([hand],.46)
        self.assertEqual(c.shape,'2')

    def test_noise_and_tracking_loss_do_not_change_shape(self):
        c=GestureController()
        for i in range(20):
            c.update([Hand(str(1+i%3),.4,.2)],i*.1)
        self.assertEqual(c.shape,'tree')
        c.update([Hand('1',.4,.2)],3.)
        c.update([],3.3)
        c.update([Hand('1',.4,.2)],3.6)
        self.assertEqual(c.shape,'tree')
        c.update([Hand('1',.4,.2)],3.9)
        c.update([Hand('1',.4,.2)],4.1)
        self.assertEqual(c.shape,'1')
        c.update([],9.)
        self.assertEqual(c.shape,'1')

    def test_two_hand_roles_ignore_detection_order_and_clamp_scale(self):
        c=GestureController()
        left=Hand('3',.5,.2)
        right=Hand('1',0.,.8)
        c.update([right,left],0.)
        c.update([left,right],.3)
        c.update([left,right],.6)
        self.assertEqual(c.shape,'3')
        self.assertGreaterEqual(c.scale,.55)
        self.assertLess(c.scale,.75)
        c.update([left,Hand(None,5.,.8)],1.)
        self.assertLessEqual(c.scale,1.45)
        self.assertGreater(c.scale,1.2)

    def test_repeated_frame_and_observation_gap_cannot_finish_dwell(self):
        c=GestureController()
        hand=Hand('2',.5,.3)
        for _ in range(50): c.update([hand],1.)
        self.assertEqual(c.shape,'tree')
        c.update([hand],1.6)
        self.assertEqual(c.shape,'tree')
        c.update([hand],1.9)
        c.update([hand],2.1)
        self.assertEqual(c.shape,'2')


if __name__=='__main__': unittest.main()
