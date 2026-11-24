# xxj-summer-zjl
"""Check visible shape changes, stable physics and recovery after slow frames."""
import unittest
import numpy as np
try:
    from particles import ParticleCloud
except ImportError:
    ParticleCloud=None


class ParticleTest(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(ParticleCloud,'Particle morphing is not implemented')

    def test_morph_reaches_each_digit_and_can_return_to_tree(self):
        cloud=ParticleCloud(1200)
        tree=cloud.positions.copy()
        for shape in ('1','2','3','tree'):
            cloud.set_shape(shape)
            target=cloud.targets[shape]
            for _ in range(240): cloud.step(1/60,1.)
            self.assertLess(float(np.mean(np.linalg.norm(cloud.positions-target,axis=1))),.025)
            self.assertTrue(np.isfinite(cloud.positions).all())
            if shape != 'tree':
                self.assertGreater(float(np.mean(np.linalg.norm(cloud.positions-tree,axis=1))),.25)

    def test_scale_and_stalled_frame_remain_bounded(self):
        cloud=ParticleCloud(1200)
        cloud.set_shape('2')
        for _ in range(240): cloud.step(1/60,.6)
        small=np.std(cloud.positions[:,0])
        cloud.step(100,1.4)
        self.assertTrue(np.isfinite(cloud.positions).all())
        for _ in range(240): cloud.step(1/60,1.4)
        self.assertGreater(np.std(cloud.positions[:,0]),small*2)
        self.assertLess(np.max(np.abs(cloud.positions)),4.)


if __name__=='__main__': unittest.main()
