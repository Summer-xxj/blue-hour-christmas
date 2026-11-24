# xxj-summer-zjl
"""Geometry and stable interaction, independent of camera and drawing libraries."""
from dataclasses import dataclass
from math import dist, isfinite, sqrt


@dataclass(frozen=True)
class Hand:
    gesture: str | None
    pinch: float
    x: float
    points: tuple = ()


def _straight(a, b, c):
    u = [b[i]-a[i] for i in range(3)]
    v = [c[i]-b[i] for i in range(3)]
    length = sqrt(sum(x*x for x in u)*sum(x*x for x in v))
    return length > 1e-9 and sum(x*y for x,y in zip(u,v))/length > .55


def classify(points):
    if len(points) != 21 or not all(isfinite(v) for p in points for v in p):
        return None
    palm = max(dist(points[0],points[9]), 1e-6)
    extended=[]
    for base in (5,9,13,17):
        tip,pip=points[base+3],points[base+1]
        extended.append(_straight(points[base],pip,tip)
                        and dist(tip,points[0]) > dist(pip,points[0])+palm*.14)
    if all(extended): return 'tree'
    if not any(extended): return 'fist'
    if extended == [True,False,False,False]: return '1'
    if extended == [True,True,False,False]:
        thumb=(_straight(points[1],points[2],points[4])
               and dist(points[4],points[5]) > palm*.65)
        return '3' if thumb else '2'
    if extended == [True,True,True,False]: return '3'
    return None


class GestureController:
    def __init__(self, dwell=.45):
        self.shape='tree'
        self.scale=1.
        self.dwell=dwell
        self.candidate=None
        self.since=0.
        self.progress=0.
        self.last_observation=None

    def reset_tracking(self):
        self.candidate=None
        self.progress=0.
        self.last_observation=None

    def update(self, hands, now):
        if self.last_observation is not None:
            if now<=self.last_observation: return self.shape,self.scale
            if now-self.last_observation>.35:
                self.candidate=None
                self.progress=0.
        self.last_observation=now
        hands=sorted(hands,key=lambda h:h.x)
        gesture=hands[0].gesture if hands else None
        if gesture != self.candidate:
            self.candidate,self.since=gesture,now
        self.progress=min(1.,max(0.,(now-self.since)/self.dwell)) if gesture else 0.
        if gesture in ('tree','1','2','3') and self.progress >= 1:
            self.shape=gesture
        if len(hands)>1 and isfinite(hands[1].pinch):
            aperture=max(0.,min(1.,(hands[1].pinch-.12)/1.35))
            self.scale=.58+aperture*.82
        return self.shape,self.scale
