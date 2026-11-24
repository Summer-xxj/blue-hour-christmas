# xxj-summer-zjl
import unittest
from single_hand import SingleHand
from gestures import Hand

def hand(x=.5,y=.5,pose='tree'):
    return Hand(pose,.5,x,tuple((x,y) for _ in range(21)))

class SingleHandTests(unittest.TestCase):
    def test_zoom_held_pose(self):
        c=SingleHand(); c.observe(hand(pose='fist'),1,1)
        self.assertEqual(c.observe(hand(pose='fist'),1.3,1)[0],.58)
        c.observe(hand(),1.4,.58)
        self.assertEqual(c.observe(hand(),1.7,.58)[0],1.4)
    def test_wave_overrides_zoom_and_reassembles(self):
        c=SingleHand(); c.observe(hand(),1,1)
        scale,burst=c.observe(hand(.6),1.1,1)
        self.assertTrue(burst); self.assertEqual(scale,1)
        for _ in range(10): c.tick(.03)
        self.assertGreater(c.scatter,.8)
        self.assertGreater(c.offset[0],0)
        for _ in range(180): c.tick(1/30)
        self.assertLess(c.scatter,.001)
    def test_pointing_and_tracking_loss_never_burst(self):
        c=SingleHand(); c.observe(hand(pose='1'),1,1)
        self.assertFalse(c.observe(hand(.7,pose='1'),1.1,1)[1])
        c.observe(None,1.2,1)
        self.assertFalse(c.observe(hand(.1),1.3,1)[1])
