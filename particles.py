# xxj-summer-zjl
"""One particle population, persistent identities, four softly attracting shapes."""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def digit_target(text,count,rng):
    image=Image.new('L',(400,500))
    draw=ImageDraw.Draw(image)
    path=Path('/System/Library/Fonts/Supplemental/Didot.ttc')
    font=ImageFont.truetype(str(path) if path.exists() else 'DejaVuSerif.ttf',440)
    box=draw.textbbox((0,0),text,font=font)
    draw.text(((400-box[2]+box[0])/2-box[0],(500-box[3]+box[1])/2-box[1]),text,font=font,fill=255)
    ys,xs=np.nonzero(np.asarray(image)>100)
    indices=rng.integers(0,len(xs),count)
    unit=(ys.max()-ys.min())/2.20
    x=(xs[indices]-(xs.max()+xs.min())/2)/unit+rng.normal(0,.014,count)
    y=(ys[indices]-(ys.max()+ys.min())/2)/unit+rng.normal(0,.014,count)
    z=rng.normal(0,.11,count)
    result=np.column_stack((x,y,z)).astype('float32')
    # Spatial ordering prevents needless particle crossings during the morph.
    return result[np.lexsort((result[:,0],result[:,1]))]


class ParticleCloud:
    def __init__(self,count=9000):
        self.rng=rng=np.random.default_rng(1225)
        self.count=count
        h=rng.uniform(0,1,count)**.64
        gold=rng.random(count)<.42
        angle=rng.uniform(0,np.pi*2,count)
        # Golden helices coexist with a broad blue/violet branched volume.
        ribbon=gold & (rng.random(count)<.73)
        angle[ribbon]=h[ribbon]*np.pi*2*3.8+rng.normal(0,.052,ribbon.sum())
        radius=h**.88*(.80+.20*np.sin(h*np.pi*10)**2)
        radius*=rng.uniform(.68,1.02,count)
        radius[ribbon]=h[ribbon]**.9*1.08+rng.normal(0,.013,ribbon.sum())
        tree=np.column_stack((radius*np.cos(angle),h*2.36-1.18,radius*np.sin(angle)))
        order=np.lexsort((tree[:,0],tree[:,1]))
        self.targets={'tree':tree[order].astype('float32')}
        for digit in '123': self.targets[digit]=digit_target(digit,count,rng)
        # Filled 3D heart: particles throughout its volume, with a legible outer silhouette.
        accepted=[]
        while sum(len(batch) for batch in accepted)<count:
            sample=rng.uniform((-1.2,-.72,-1.1),(1.2,.72,1.3),(count*2,3))
            x,depth,up=sample.T
            inside=(x*x+2.25*depth*depth+up*up-1)**3-x*x*up**3-.1125*depth*depth*up**3<=0
            accepted.append(sample[inside])
        volume=np.concatenate(accepted)[:count]
        heart=np.column_stack((volume[:,0],-volume[:,2],volume[:,1]))
        self.targets['heart']=heart[np.lexsort((heart[:,0],heart[:,1]))].astype('float32')
        direction=rng.normal(size=(count,3))
        direction/=np.linalg.norm(direction,axis=1)[:,None]
        self.targets['core']=(direction*rng.uniform(.008,.06,(count,1))).astype('float32')
        angle=rng.uniform(0,2*np.pi,count)
        radius=rng.uniform(3.5,6.,count)
        self.targets['empty']=np.column_stack((np.cos(angle)*radius,np.sin(angle)*radius,
                                              rng.uniform(-.5,.5,count))).astype('float32')
        self.gold=gold[order]
        self.phase=rng.uniform(0,2*np.pi,count).astype('float32')
        self.sizes=rng.choice([0,1,2,3],count,p=[.51,.33,.14,.02])
        self.colors=rng.integers(0,3,count)
        self.positions=self.targets['tree'].copy()
        self.velocity=np.zeros_like(self.positions)
        self.shape='tree'
        self.scale=1.
        self.override=None

    def set_shape(self,shape):
        if shape not in self.targets: raise ValueError(f'Unknown shape: {shape}')
        if shape != self.shape:
            self.shape=shape
            # Small tangential impulse draws curved trajectories through the morph.
            self.velocity[:,0]+=self.positions[:,2]*.5
            self.velocity[:,2]-=self.positions[:,0]*.5

    def step(self,dt,scale):
        dt=max(0.,min(float(dt),.1))
        self.scale=float(np.clip(scale,.58,1.4))
        # Fixed-size substeps remain stable even after dragging or pausing a window.
        steps=max(1,int(np.ceil(dt/(1/120))))
        step=dt/steps
        target=self.targets[self.shape]*self.scale if self.override is None else self.override
        for _ in range(steps):
            acceleration=(target-self.positions)*24-self.velocity*8.5
            self.velocity+=acceleration*step
            self.positions+=self.velocity*step
