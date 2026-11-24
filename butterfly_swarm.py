# xxj-summer-zjl
"""Small open, three-dimensional butterflies built only from emissive points."""
import math
import numpy as np
import pygame
from textures import bezier


class ButterflySwarm:
    def __init__(self):
        rng=np.random.default_rng(913)
        self.phase=rng.uniform(0,math.tau,24)
        self.size=rng.uniform(.055,.10,24)
        self.anchors=None
        points=[]
        for side in (-1,1):
            for curve in (
                [(0,0),(.35,-.55),(1.65,-1.8),(1.25,-.5)],
                [(1.25,-.5),(.95,-.05),(.35,.1),(0,0)],
                [(0,0),(1.05,.15),(.8,.65),(.28,1.45)],
                [(.28,1.45),(.45,.45),(.08,.4),(0,0)],
                [(0,0),(.4,-.35),(.75,-.65),(1.35,-1.13)],
            ):
                points.extend((x*side,y,0.) for x,y in bezier(curve,n=12))
        points.extend((0.,y,0.) for y in np.linspace(-.3,.4,9))
        self.template=np.array(points)
        self.sprites={}

    def wings(self,time,index):
        p=self.template.copy()
        phase=self.phase[index]
        fold=.25+.95*(.5+.5*math.sin(time*4.5+phase))
        x=p[:,0].copy()
        p[:,0]=x*math.cos(fold)
        p[:,2]=np.abs(x)*math.sin(fold)+.12*np.sin(p[:,1]*2)*np.abs(x)
        # Each butterfly turns independently, revealing its folded wing volume.
        yaw=.7*math.sin(time*.8+phase)+phase
        x=p[:,0].copy(); z=p[:,2].copy()
        p[:,0]=x*math.cos(yaw)+z*math.sin(yaw)
        p[:,2]=-x*math.sin(yaw)+z*math.cos(yaw)
        roll=.3*math.sin(time+phase)
        x=p[:,0].copy(); y=p[:,1].copy()
        p[:,0]=x*math.cos(roll)-y*math.sin(roll)
        p[:,1]=x*math.sin(roll)+y*math.cos(roll)
        return p*self.size[index]

    def draw(self,scene):
        amount=scene.single_hand.scatter
        if scene.story.stage!='tree' or amount<.035: return
        if self.anchors is None:
            self.anchors=np.linspace(600,scene.cloud.count-600,24,dtype=int)
        level=max(1,min(8,int(amount*8)))
        for tone in (1,2,3):
            key=(tone,level)
            if key not in self.sprites:
                sprite=scene.digit_sprite[tone,0].copy()
                sprite.fill((int(255*level/8),)*3,special_flags=pygame.BLEND_RGB_MULT)
                self.sprites[key]=sprite
        jobs=[]
        for i,anchor in enumerate(self.anchors):
            center=scene.cloud.positions[anchor].copy()
            center+=np.array([math.sin(scene.time*.8+self.phase[i])*.10,
                             math.cos(scene.time+self.phase[i])*.10,0])*amount
            points=self.wings(scene.time,i)*amount+center
            xy,z=scene.project(points)
            for j,(x,y) in enumerate(xy):
                tone=3 if j%9==0 else (2 if z[j]>center[2] else 1)
                sprite=self.sprites[tone,level]; r=sprite.get_width()/2
                jobs.append((sprite,(float(x)-r,float(y)-r)))
        scene.canvas.fblits(jobs,pygame.BLEND_RGB_ADD)
