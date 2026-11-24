# xxj-summer-zjl
"""A single stroke of tiny, independently beating butterflies for each letter."""
import numpy as np
from textures import bezier


def letter_paths():
    def curve(*p): return bezier(p,n=30)
    s=curve((.91,.14),(.45,-.19),(-.33,.18),(.19,.43))+curve((.19,.43),(.37,.55),(1.08,.48),(.91,.80))+curve((.91,.80),(.81,1.05),(.28,1.06),(.04,.85))
    u=[(.04,0),(.04,.64)]+curve((.04,.64),(.04,1.12),(.96,1.12),(.96,.64))+[(.96,0)]
    m=[(.04,1),(.04,0),(.53,.60),(.98,0),(.98,1)]
    e=[(.99,0),(.04,0),(.04,1),(.99,1)]
    r=[(.04,1),(.04,0),(.48,0)]+curve((.48,0),(1.18,-.02),(1.18,.53),(.48,.53))+[(.04,.53)]
    return [[s],[u],[m],[m],[e,[(.04,.49),(.80,.49)]],[r,[(.47,.53),(.99,1)]]]


class SummerFlock:
    def __init__(self,count,template):
        paths=[]
        for i,letter in enumerate(letter_paths()):
            for stroke in letter:
                points=np.asarray(stroke)*[.61,.93]+[i*.78-2.255,-.465]
                arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))]
                marks=np.linspace(0,arc[-1],max(2,round(arc[-1]/.091)+1))
                paths.extend(np.column_stack([np.interp(marks,arc,v) for v in points.T]))
        rng=np.random.default_rng(2125)
        self.centers=np.column_stack([np.asarray(paths),rng.uniform(-.055,.055,len(paths))])
        ids=np.arange(count)%len(paths)
        samples=np.arange(count)//len(paths)
        self.wing=template[(samples*37+ids*5)%len(template)]
        self.ids=ids
        self.phase=rng.uniform(0,2*np.pi,len(paths))
        self.scale=rng.uniform(.031,.045,len(paths))

    def positions(self,t):
        ids=self.ids
        phase=self.phase
        fold=.53+.43*np.sin(t*4.4+phase)
        turn=.50*np.sin(t*.9+phase)
        x,y=self.wing[:,:2].T
        side=x*np.cos(fold)[ids]; depth=np.abs(x)*np.sin(fold)[ids]
        wing=np.column_stack((side*np.cos(turn)[ids]+depth*np.sin(turn)[ids],y,
                              depth*np.cos(turn)[ids]-side*np.sin(turn)[ids]))
        return self.centers[ids]+wing*self.scale[ids,None]
