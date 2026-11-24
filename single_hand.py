# xxj-summer-zjl
"""Single-hand controls after the tree reveal; fast waving takes priority over zoom."""
import numpy as np

class SingleHand:
    def __init__(self):
        self.previous=None
        self.pose=None
        self.pose_since=0.
        self.remaining=0.
        self.scatter=0.
        self.flight_age=0.
        self.letter_mix=0.
        self.offset=np.zeros(3)
        self.target_offset=np.zeros(3)

    def observe(self,hand,now,scale):
        if hand is None or len(hand.points)!=21:
            self.previous=None; self.pose=None
            return scale,False
        center=np.mean([hand.points[i][:2] for i in (0,5,9,13,17)],axis=0)
        speed=0.
        if self.previous is not None:
            old,stamp=self.previous
            if 0<now-stamp<.25: speed=float(np.linalg.norm(center-old)/(now-stamp))
        self.previous=(center,now)
        waving=speed>.65 and hand.gesture!='1'
        burst=waving and self.remaining<=0
        if burst: self.flight_age=0.
        if waving: self.remaining=2.8 if burst else max(self.remaining,1.7)
        elif self.remaining>0 and speed>.10: self.remaining=max(self.remaining,1.7)
        if self.remaining>0:
            self.target_offset=np.array([np.clip((center[0]-.5)*3,-.9,.9),
                                         np.clip((center[1]-.5)*2.4,-.65,.65),0.])
            self.pose=None
            return scale,burst
        if hand.gesture!=self.pose:
            self.pose=hand.gesture; self.pose_since=now
        if speed<.35 and now-self.pose_since>.22:
            if self.pose=='fist': scale=.58
            elif self.pose=='tree': scale=1.4
        return scale,burst

    def tick(self,dt):
        self.remaining=max(0,self.remaining-dt)
        goal=1. if self.remaining>0 else 0.
        if self.remaining>0: self.flight_age+=dt
        letter_goal=float(self.remaining>0 and self.flight_age>.45)
        self.letter_mix+=(letter_goal-self.letter_mix)*(1-np.exp(-dt*(3.8 if letter_goal else 5.)))
        self.scatter+=(goal-self.scatter)*(1-np.exp(-dt*(9 if goal else 3)))
        self.offset+=(self.target_offset*self.scatter-self.offset)*(1-np.exp(-dt*8))
