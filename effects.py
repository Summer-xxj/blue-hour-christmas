# xxj-summer-zjl
"""Reference-inspired violet orbital dust, gold meteor shower and radial bursts."""
import math
import numpy as np
import pygame


class Effects:
    def __init__(self):
        self.rng=np.random.default_rng(2026)
        self.rings=self.rng.random((3500,4))
        self.meteors=self.rng.random((70,4))
        self.streams=self.rng.random((950,4))
        self.bursts=[]
        self.ornaments=[]
        # Open point paths, never opaque images or filled polygons.
        from textures import bezier
        for i in range(19):
            if i%3==0:
                wing=[]
                for side in (-1,1):
                    for controls in (
                        [(0,0),(.4,-.3),(1.4,-1.8),(1.,-.25)],
                        [(1.,-.25),(.7,.15),(.45,.2),(0,0)],
                        [(0,0),(.9,.2),(.85,.5),(.22,1.5)],
                        [(.22,1.5),(.4,.45),(.1,.4),(0,0)]):
                        wing.extend([(x*side,y) for x,y in bezier(controls,n=13)])
                shape=np.asarray(wing)*.057
            else:
                paths=[ [(-1,-.7),(1,-.7),(1,.8),(-1,.8),(-1,-.7)],
                        [(0,-.7),(0,.8)], [(-1,-.12),(1,-.12)],
                        [(0,-.7),(-.75,-1.35),(-.8,-.8),(0,-.7),
                         (.75,-1.35),(.8,-.8),(0,-.7)] ]
                shape=np.asarray([np.asarray(a)*(1-f)+np.asarray(b)*f
                    for path in paths for a,b in zip(path,path[1:])
                    for f in np.linspace(0,1,7,endpoint=False)])*.037
            self.ornaments.append(shape)
        self.anchor_indices=None

    def burst(self):
        a=self.rng.uniform(0,math.tau,1000)
        speed=self.rng.uniform(50,440,1000)
        self.bursts.append([0.,np.column_stack((np.cos(a)*speed,np.sin(a)*speed)),
                            self.rng.uniform(.6,1.6,1000)])
        self.bursts=self.bursts[-3:]

    def draw(self,scene,dt):
        canvas=scene.canvas
        s=canvas.get_width()/1440
        t=scene.time
        jobs=[]
        for a,r,v,q in (self.rings if scene.tree_mix>.1 else []):
            angle=a*math.tau+t*(.03+v*.07)
            radius=170+r**.8*490
            x=(scene.center_x+math.cos(angle)*radius)*s
            y=(768+math.sin(angle)*radius*.20)*s
            sprite=scene.sprite[1 if q<.6 else 2,0]
            rr=sprite.get_width()/2
            jobs.append((sprite,(float(x)-rr,float(y)-rr)))
        canvas.fblits(jobs,pygame.BLEND_RGB_ADD)
        if scene.tree_mix>.1 and scene.single_hand.scatter<.2:
            self.tree_details(scene,s,t)
        for a,b,c,d in (self.meteors if scene.story.stage=='tree' else []):
            life=(t*(.065+c*.055)+a*4)%4
            if life>1.15: continue
            x=(180+b*1600-life*420)*s
            y=(-120+d*300+life*420)*s
            for j in range(12):
                fade=(1-j/12)**2
                rgb=tuple(int(v*fade) for v in (255,211,151))
                p=(x+j*8*s,y-j*8*s)
                pygame.draw.aaline(canvas,rgb,p,(p[0]+8*s,p[1]-8*s))
            sprite=scene.sprite[3,2]; rr=sprite.get_width()/2
            canvas.blit(sprite,(float(x)-rr,float(y)-rr),special_flags=pygame.BLEND_RGB_ADD)
        alive=[]
        for age,vel,life in self.bursts:
            age+=dt
            if age>3: continue
            alive.append([age,vel,life])
            distance=(1-math.exp(-age*1.1))/1.1
            for i,(vx,vy) in enumerate(vel):
                if age>life[i]*2: continue
                x=(scene.center_x+vx*distance)*s
                y=(474+vy*distance+age*age*24)*s
                tail=max(0,distance-.035)
                fade=max(0,1-age/(life[i]*2))
                pygame.draw.aaline(canvas,(int(200*fade),int(132*fade),int(44*fade)),
                    (x,y),((scene.center_x+vx*tail)*s,(474+vy*tail+age*age*24)*s))
                sprite=scene.sprite[3,0 if i%5 else 1];rr=sprite.get_width()/2
                canvas.blit(sprite,(float(x)-rr,float(y)-rr),special_flags=pygame.BLEND_RGB_ADD)
        self.bursts=alive

    def tree_details(self,scene,s,t):
        canvas=scene.canvas
        turn=abs(scene.yaw_target-scene.yaw)
        count=min(950,500+int(turn*900))
        values=self.streams[:count]
        h=.13+values[:,0]*.87
        age=(values[:,1]+t*.16)%1
        angle=h*math.tau*3.8+values[:,2]*1.8+age*(1.4+turn)
        radius=h**.9*(1.06+age*(.35+min(turn,.8)))
        points=np.column_stack((radius*np.cos(angle),(h*2.36-1.18)-age*.22,
                                radius*np.sin(angle)))*scene.scale
        xy,_=scene.project(points)
        old=points.copy()
        old[:,0]=radius*np.cos(angle-.035)*scene.scale
        old[:,2]=radius*np.sin(angle-.035)*scene.scale
        prev,_=scene.project(old)
        for i,((x,y),(ox,oy)) in enumerate(zip(xy,prev)):
            fade=float((1-age[i])*.8+.2)*scene.tree_mix
            pygame.draw.aaline(canvas,(int(240*fade),int(183*fade),int(93*fade)),
                               (float(ox),float(oy)),(float(x),float(y)))
            sprite=scene.sprite[3,1 if i%7==0 else 0];r=sprite.get_width()/2
            canvas.blit(sprite,(x-r,y-r),special_flags=pygame.BLEND_RGB_ADD)
        if self.anchor_indices is None:
            self.anchor_indices=[]
            tree=scene.cloud.targets['tree']
            for i in range(19):
                h=.25+i/19*.70; a=i*2.399; r=h**.9*1.02
                anchor=np.array([r*math.cos(a),h*2.36-1.18,r*math.sin(a)])
                self.anchor_indices.append(int(np.argmin(np.sum((tree-anchor)**2,axis=1))))
        for i,shape in enumerate(self.ornaments):
            anchor=scene.cloud.positions[self.anchor_indices[i]]
            _,z=scene.project(anchor[None,:])
            if z[0]<-.15: continue
            a=i*2.399
            local=shape.copy()*scene.scale*scene.tree_mix
            if i%3==0: local[:,0]*=.65+.35*math.sin(t*1.6+i)**2
            pts=np.repeat(anchor[None,:],len(local),axis=0)
            pts[:,0]+=local[:,0]*math.cos(a)
            pts[:,2]+=local[:,0]*math.sin(a)
            pts[:,1]+=local[:,1]
            xy,_=scene.project(pts)
            jobs=[]
            for j,(x,y) in enumerate(xy):
                sprite=scene.digit_sprite[3 if j%4==0 else (2 if i%3 else 1),0]
                rr=sprite.get_width()/2
                jobs.append((sprite,(float(x)-rr,float(y)-rr)))
            canvas.fblits(jobs,pygame.BLEND_RGB_ADD)

    def crown(self,scene):
        t=scene.time
        corners=[]
        for k in range(10):
            a=-math.pi/2+k*math.pi/5
            radius=.075 if k%2==0 else .032
            corners.append(np.array([math.cos(a)*radius,math.sin(a)*radius,0.]))
        points=[]
        for k in range(10):
            for j in range(12):
                f=j/12
                p=corners[k]*(1-f)+corners[(k+1)%10]*f
                p[2]=math.sin(j*2.3+k)*.006
                p[1]-=1.30
                points.append(p)
        xy,_=scene.project(np.asarray(points)*scene.scale)
        jobs=[]
        for i,(x,y) in enumerate(xy):
            level=int(3*(.5+.5*math.sin(t*2+i*.6))**10)
            sprite=scene.shimmer[3,level] if i%13==0 else scene.digit_sprite[3,0]
            rr=sprite.get_width()/2
            jobs.append((sprite,(float(x)-rr,float(y)-rr)))
        scene.canvas.fblits(jobs,pygame.BLEND_RGB_ADD)
