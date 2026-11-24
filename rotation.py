# xxj-summer-zjl
"""Track fingertip paths rather than assuming the palm is the circle centre."""
from collections import deque
import math
import numpy as np


class RotationController:
    def __init__(self):
        self.reset()

    def reset(self):
        self.timestamp=None
        self.filtered=None
        self.anchor=None
        self.history=deque()
        self.last_pointing=-10.

    def update(self,hand,now):
        if self.timestamp is not None and now<=self.timestamp:
            return 0.
        # Allow a short ambiguous pose, but stop immediately on fist/open hand/loss.
        valid=(hand is not None and len(hand.points)==21 and
               (hand.gesture=='1' or (hand.gesture is None and now-self.last_pointing<.18)))
        if not valid:
            self.reset()
            return 0.
        if hand.gesture=='1': self.last_pointing=now
        tip=np.asarray(hand.points[8][:2],dtype=float)
        if not np.isfinite(tip).all():
            self.reset()
            return 0.
        if self.timestamp is None or now-self.timestamp>.25:
            self.history.clear()
            self.filtered=tip.copy(); self.anchor=tip.copy()
            self.timestamp=now; self.history.append((now,tip.copy()))
            return 0.
        dt=now-self.timestamp
        self.timestamp=now
        self.filtered+=(tip-self.filtered)*(1-math.exp(-dt/.035))
        delta=self.filtered-self.anchor
        distance=float(np.linalg.norm(delta))
        # Keep the anchor on tiny steps so slow movement accumulates, not disappears.
        if distance<.0015: return 0.
        if distance>.18:
            self.reset()
            return 0.
        previous=self.anchor.copy()
        self.anchor=self.filtered.copy()
        self.history.append((now,self.anchor.copy()))
        while self.history and now-self.history[0][0]>.7:
            self.history.popleft()
        turn=float(delta[0])*9.
        if len(self.history)>=6:
            points=np.array([p for _,p in self.history])
            origin=points.mean(axis=0)
            q=points-origin
            matrix=np.column_stack((2*q,np.ones(len(q))))
            solution,_,_,singular=np.linalg.lstsq(matrix,np.sum(q*q,axis=1),rcond=None)
            center=solution[:2]+origin
            radii=np.linalg.norm(points-center,axis=1)
            radius=float(radii.mean())
            # Reject straight lines and jitter before interpreting angular motion.
            if (.012<radius<.35 and singular[-1]>.001 and
                    float(radii.std())<radius*.12 and
                    float(np.linalg.norm(np.ptp(points,axis=0)))>radius*.55):
                a=previous-center; b=self.anchor-center
                angle=math.atan2(a[0]*b[1]-a[1]*b[0],float(np.dot(a,b)))
                turn=angle*1.3
        return float(np.clip(turn,-min(.45,dt*12),min(.45,dt*12)))
