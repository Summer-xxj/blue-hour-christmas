#!/usr/bin/env python3
# xxj-summer-zjl
"""星河入梦 — camera gestures, blue-violet stardust and champagne light."""
from __future__ import annotations
import argparse
import math
import os
from pathlib import Path
import time

os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT','1')
import numpy as np
import pygame
from camera import Camera
from gestures import GestureController
from story import Story
from rotation import RotationController
from dedication import ParticleDedication
from single_hand import SingleHand
from butterfly_swarm import ButterflySwarm
from summer_flock import SummerFlock
from particles import ParticleCloud
from textures import glow
from effects import Effects

S=2
W,H=1440*S,940*S
ROOT=Path(__file__).resolve().parent
GOLD=(255,210,140)
ICE=(171,199,255)


def chinese_font(size):
    path=Path('/System/Library/Fonts/STHeiti Light.ttc')
    return pygame.font.Font(str(path) if path.exists() else None,size)


class Scene:
    def __init__(self):
        self.cloud=ParticleCloud(9000)
        self.controller=GestureController()
        self.story=Story()
        self.cloud.positions=self.cloud.targets['empty'].copy()
        self.cloud.set_shape('empty')
        self.canvas=pygame.Surface((W,H))
        self.background=pygame.Surface((W,H))
        self.background.fill((3,5,14))
        stars=np.random.default_rng(1123)
        for x,y,brightness in stars.random((1700,3)):
            value=int(35+brightness**3*160)
            pygame.draw.circle(self.background,(int(value*.72),int(value*.8),value),
                               (int(x*W),int(y*H)),1 if brightness<.97 else 2)
        self.effects=Effects()
        self.butterfly_swarm=ButterflySwarm()
        self.summer_flock=SummerFlock(self.cloud.count,self.butterfly_swarm.template)
        self.armed=False
        self.last_burst=-10.
        self.fog=pygame.Surface((W//3,H//3))
        self.trails=pygame.Surface((W,H))
        self.trails.fill((0,0,0))
        self.tree_mix=0.
        self.scale=1.
        self.yaw=0.
        self.yaw_target=0.
        self.auto_rotation=0.
        self.time=0.
        self.paused=False
        self.help=True
        self.sparkles=[]
        self.sprite={}
        self.digit_sprite={}
        palette=[(95,140,255),(174,98,255),(173,210,255),GOLD,(244,139,222)]
        for tone,rgb in enumerate(palette):
            for size,radius in enumerate((2,3,5,8)):
                self.sprite[tone,size]=glow(radius*S,rgb,.7 if tone !=3 else .8,S)
                self.digit_sprite[tone,size]=glow(radius*S,rgb,.40 if tone !=3 else .50,S)
        self.shimmer={}
        for tone,rgb in enumerate(palette):
            for level in range(5):
                self.shimmer[tone,level]=glow((4+level*2)*S,rgb,.35+level*.27,S)
        self.star_sprite=glow(42*S,GOLD,1.2,S)
        self.title=chinese_font(27*S)
        self.ui=chinese_font(16*S)
        self.small=chinese_font(13*S)
        self.serif=pygame.font.Font('/System/Library/Fonts/Supplemental/Baskerville.ttc',20*S)
        self.greeting_font=pygame.font.Font('/System/Library/Fonts/Supplemental/SnellRoundhand.ttc',60*S)
        self.signature_font=pygame.font.Font('/System/Library/Fonts/Supplemental/SnellRoundhand.ttc',32*S)
        self.rotation=RotationController()
        self.single_hand=SingleHand()
        rng=np.random.default_rng(932)
        self.dispersal=rng.normal(0,.6,(self.cloud.count,3)).astype("float32")
        self.finger_stamp=0.
        self.signature_cn=pygame.font.Font('/System/Library/Fonts/Supplemental/Songti.ttc',23*S)
        self.camera_status='摄像头已关闭 · C 开启'
        self.camera_active=False
        self.hands=()
        self.preview=None
        self.buttons={}

    def cue(self,gesture):
        old=self.story.stage
        if self.story.accept(gesture,self.time):
            self.cloud.set_shape(self.story.stage)
            if self.story.stage=='tree':
                self.effects.burst()
                self.yaw=self.yaw_target=self.auto_rotation=0.
            print(f'演出: {old} → {self.story.stage}',flush=True)

    def reset_story(self):
        self.story.reset()
        self.single_hand=SingleHand()
        self.cloud.override=None
        self.rotation.reset()
        self.controller.reset_tracking()
        self.cloud.positions=self.cloud.targets['empty'].copy()
        self.cloud.velocity.fill(0)
        self.cloud.set_shape('empty')
        self.tree_mix=0.
        self.trails.fill((0,0,0))
        self.effects.bursts.clear()

    def text(self,text,pos,color=(184,190,216),font=None,center=False):
        pos=(pos[0]*S,pos[1]*S)
        image=(font or self.ui).render(text,True,color)
        rect=image.get_rect(center=pos) if center else image.get_rect(topleft=pos)
        self.canvas.blit(image,rect)
        return rect

    @property
    def center_x(self):
        return 720+140*self.tree_mix

    def project(self,points):
        angle=(self.yaw+self.auto_rotation)*self.tree_mix
        co,si=math.cos(angle),math.sin(angle)
        x=points[:,0]*co+points[:,2]*si
        z=-points[:,0]*si+points[:,2]*co
        perspective=1+z*.08
        unit=255-20*self.tree_mix
        return np.column_stack(((self.center_x+x*unit*perspective)*S,
                                (474+points[:,1]*unit+z*32)*S)),z

    def render(self,dt):
        if self.paused: dt=0
        self.yaw+=(self.yaw_target-self.yaw)*(1-math.exp(-dt*20))
        self.time+=dt
        t=self.time
        self.single_hand.tick(dt)
        if self.story.stage=='tree':
            self.cloud.override=(self.cloud.targets['tree']*self.controller.scale+
                self.dispersal*self.single_hand.scatter+self.single_hand.offset)
        else: self.cloud.override=None
        self.cloud.step(dt,self.controller.scale)
        self.scale+=(self.controller.scale-self.scale)*(1-math.exp(-dt*6))
        goal=1. if self.cloud.shape=='tree' else 0.
        self.tree_mix+=(goal-self.tree_mix)*(1-math.exp(-dt*3))
        self.auto_rotation+=dt*.085*self.tree_mix
        # Keep digits nearly frontal, without forcing a camera-angle jump.
        if goal==0: self.auto_rotation*=math.exp(-dt*3)
        screen=self.canvas
        screen.blit(self.background,(0,0))
        if self.story.stage=='empty':
            self._watermark()
            return screen
        self.fog.fill((0,0,0))
        points=self.cloud.positions.copy()
        if self.story.stage=='heart':
            points*=1+.018*math.sin(t*3.2)**7
            a=.19*math.sin(t*.65)
            px=points[:,0].copy()
            points[:,0]=px*math.cos(a)+points[:,2]*math.sin(a)
            points[:,2]=-px*math.sin(a)+points[:,2]*math.cos(a)
        points[:,0]+=np.sin(self.cloud.phase+t*.4)*.007
        points[:,1]+=np.cos(self.cloud.phase+t*.32)*.006
        xy,z=self.project(points)
        mix=self.single_hand.letter_mix
        if self.story.stage=='tree' and mix>.001:
            flock=self.summer_flock.positions(t)
            offset=self.single_hand.offset
            dest=np.column_stack(((720+(flock[:,0]+offset[0]*.67)*230)*S,
                                  (474+(flock[:,1]+offset[1])*230+flock[:,2]*24)*S))
            xy+=(dest-xy)*mix
            z+=(flock[:,2]-z)*mix
        depth=np.clip((z+1.3)/2.6,0,1)
        # Distant and nearby lights coexist. Alpha-free RGB sprites add light optically.
        jobs=[]
        for i,(x,y) in enumerate(xy):
            if not (-30*S<x<W+30*S and -30*S<y<H+30*S): continue
            tone=3 if self.cloud.gold[i] and i%3==0 else int(self.cloud.colors[i])
            if self.story.stage=='heart' and i%7==0: tone=4
            if self.story.stage=='core':
                if i%12: continue
                tone=3
            size=int(self.cloud.sizes[i])
            if mix>.55: size=min(size,1)
            if depth[i]<.25 and size>0: size-=1
            sprite=(self.sprite if self.tree_mix>.45 else self.digit_sprite)[tone,size]
            if i%11==0:
                brightness=(.5+.5*math.sin(t*(1.8+i%5*.22)+float(self.cloud.phase[i])))**12
                sprite=self.shimmer[tone,min(4,int(brightness*5))]
            r=sprite.get_width()//2
            jobs.append((sprite,(int(x)-r,int(y)-r)))
            if i%40==0:
                rgb=(15,10,4) if tone==3 else ((5,4,15) if tone==1 else (3,6,14))
                pygame.draw.circle(self.fog,rgb,(int(x/3),int(y/3)),2*S)
        # Broad scattered light gives particle clusters volume and soft luminous edges.
        screen.blit(pygame.transform.smoothscale(self.fog,(W,H)),(0,0),special_flags=pygame.BLEND_RGB_ADD)
        # Short fading trails are actual histories, not a static ribbon illustration.
        self.trails.fill((209,207,218),special_flags=pygame.BLEND_RGB_MULT)
        self.trails.fill((1,1,1),special_flags=pygame.BLEND_RGB_SUB)
        self._ribbons(t)
        screen.blit(self.trails,(0,0),special_flags=pygame.BLEND_RGB_ADD)
        screen.fblits(jobs,pygame.BLEND_RGB_ADD)
        # Twinkle sparse points without flickering the complete tree.
        for i in range(0,self.cloud.count,73):
            if math.sin(t*1.15+self.cloud.phase[i])>.88:
                x,y=xy[i]
                self._star(x,y,3.2*S,(160,149,135))
        if self.tree_mix>.02 and self.single_hand.scatter<.2:
            self.effects.crown(self)
        self.effects.draw(self,dt)
        if mix<.8: self.butterfly_swarm.draw(self)
        self._floating_dust(t)
        if self.story.stage=='tree' and mix<.98: self._ui()
        self._watermark()
        return screen

    def _watermark(self):
        if not hasattr(self, 'watermark'):
            font = pygame.font.Font('/System/Library/Fonts/Supplemental/Baskerville.ttc', 15*S)
            self.watermark = font.render('xxj-summer-zjl', True, (170, 158, 205))
            self.watermark.set_alpha(180)
        self.canvas.blit(self.watermark, (32*S, (940-44)*S))

    def _star(self,x,y,r,rgb):
        x,y,r=float(x),float(y),float(r)
        pygame.draw.aaline(self.canvas,rgb,(x-r,y),(x+r,y))
        pygame.draw.aaline(self.canvas,rgb,(x,y-r*1.4),(x,y+r*1.4))
        if r>7:
            pygame.draw.aaline(self.canvas,tuple(int(c*.6) for c in rgb),(x-r*.4,y-r*.4),(x+r*.4,y+r*.4))
            pygame.draw.aaline(self.canvas,tuple(int(c*.6) for c in rgb),(x-r*.4,y+r*.4),(x+r*.4,y-r*.4))

    def _ribbons(self,t):
        # These looser exterior filaments give the tree space to breathe.
        if self.tree_mix<.02 or self.single_hand.scatter>.2: return
        for strand in range(3):
            h=np.linspace(.07,1,260)
            angle=h*math.tau*3.8+t*.085+strand*.09
            radius=h**.9*(1.11+strand*.045)*self.scale
            pts=np.column_stack((radius*np.cos(angle),(h*2.36-1.18)*self.scale,radius*np.sin(angle)))
            projected,z=self.project(pts)
            rgb=tuple(int(c*self.tree_mix) for c in (87,85,190))
            pygame.draw.aalines(self.canvas,rgb,False,projected.tolist())
            for j in range(22):
                frac=(j/22+t*.025+strand*.011)%1
                idx=min(259,int(frac*259))
                x,y=projected[idx]
                sprite=self.sprite[1 if strand else 2,2 if strand==0 else 1]
                radius=sprite.get_width()//2
                self.trails.blit(sprite,(x-radius,y-radius),special_flags=pygame.BLEND_RGB_ADD)
        # A broad, gently broken ring of dust below the tree; no solid pedestal.
        for i in range(180):
            a=i/180*math.tau+t*.028
            r=(290+14*math.sin(i*2.7))*S
            x=self.center_x*S+math.cos(a)*r*self.scale
            y=812*S+math.sin(a)*r*.10*self.scale
            if i%3:
                sprite=self.sprite[1,0]
                self.canvas.blit(sprite,(x-3*S,y-3*S),special_flags=pygame.BLEND_RGB_ADD)

    def _floating_dust(self,t):
        for i in range(160):
            x=((i*127.29+math.sin(t*.1+i)*15)*S)%W
            y=((i*73.39-t*(1+i%4))*S)%H
            sprite=self.sprite[3 if i%3==0 else 2,0 if i%17 else 2]
            r=sprite.get_width()//2
            self.canvas.blit(sprite,(x-r,y-r),special_flags=pygame.BLEND_RGB_ADD)

    def _ui(self):
        self.buttons.clear()
        if not hasattr(self,'dedication'):
            self.dedication=ParticleDedication(S)
        fade=max(0,min(1,(self.time-self.story.changed_at-1.4)/1.5))
        self.dedication.draw(self.canvas,self.time,fade*(1-self.single_hand.letter_mix))


def run(args):
    pygame.display.init()
    pygame.font.init()
    window=pygame.Window('星河入梦 · 手势星树',size=(1200,783),
                         resizable=True,allow_high_dpi=True)
    window.minimum_size=(800,522)
    display=window.get_surface()
    print(f'Window {window.size}; native pixels {display.get_size()}; render {W}×{H}',flush=True)
    scene=Scene()
    camera=None
    def toggle_camera():
        nonlocal camera
        if camera:
            camera.stop()
            camera=None
            scene.camera_active=False
            scene.hands=()
            scene.preview=None
            scene.controller.reset_tracking()
            scene.rotation.reset()
            scene.camera_status='摄像头已关闭 · C 开启'
        else:
            camera=Camera(args.camera_index)
            camera.start()
            scene.camera_active=True
    if not args.no_camera and not args.smoke_test: toggle_camera()
    clock=pygame.time.Clock()
    running=True
    frame=0
    fullscreen=False
    drag=False
    viewport=pygame.Rect(0,0,*display.get_size())
    smoke_shapes=[]
    started=time.perf_counter()
    try:
        while running:
            dt=min(clock.tick(60)/1000,.1)
            for event in pygame.event.get():
                if event.type==pygame.QUIT: running=False
                elif event.type==pygame.KEYDOWN:
                    if event.key==pygame.K_ESCAPE:
                        if fullscreen:
                            fullscreen=False
                            window.set_windowed()
                            window.size=(1200,783)
                        else: running=False
                    elif event.key in (pygame.K_0,pygame.K_1,pygame.K_2,pygame.K_3):
                        scene.cue('tree' if event.key==pygame.K_0 else chr(event.key))
                    elif event.key==pygame.K_x: scene.cue('fist')
                    elif event.key==pygame.K_r: scene.reset_story()
                    elif event.key==pygame.K_SPACE: scene.paused=not scene.paused
                    elif event.key==pygame.K_b: scene.effects.burst()
                    elif event.key==pygame.K_h: scene.help=not scene.help
                    elif event.key==pygame.K_c: toggle_camera()
                    elif event.key==pygame.K_v and camera:
                        camera.show_preview=not camera.show_preview
                    elif event.key==pygame.K_f:
                        fullscreen=not fullscreen
                        if fullscreen: window.set_fullscreen(desktop=True)
                        else:
                            window.set_windowed()
                            window.size=(1200,783)
                elif event.type==pygame.MOUSEWHEEL:
                    scene.controller.scale=float(np.clip(scene.controller.scale+event.y*.055,.58,1.4))
                elif event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
                    dw,dh=window.get_surface().get_size()
                    ww,wh=window.size
                    px=(event.pos[0]*dw/ww-viewport.x)/viewport.w*W
                    py=(event.pos[1]*dh/wh-viewport.y)/viewport.h*H
                    if scene.buttons.get('camera',pygame.Rect(0,0,0,0)).inflate(18,18).collidepoint(px,py): toggle_camera()
                    else: drag=True
                elif event.type==pygame.MOUSEBUTTONUP: drag=False
                elif event.type==pygame.MOUSEMOTION and drag: scene.yaw_target+=event.rel[0]*.004
            if camera:
                hands,timestamp,status,preview=camera.snapshot()
                scene.hands=hands if time.monotonic()-timestamp<.7 else ()
                scene.camera_status=status
                scene.preview=preview
                if timestamp>scene.finger_stamp:
                    scene.finger_stamp=timestamp
                    selector=min(scene.hands,key=lambda h:h.x) if scene.hands else None
                    if scene.story.stage=='tree':
                        scene.controller.scale,burst=scene.single_hand.observe(selector,timestamp,scene.controller.scale)
                        if burst: scene.effects.burst()
                        scene.yaw_target+=scene.rotation.update(selector,timestamp)
                    else:
                        scene.rotation.reset()
                    if scene.story.stage=='tree':
                        scene.controller.reset_tracking()
                    else:
                        scene.controller.update([selector] if selector else [],timestamp)
                        if scene.controller.progress>=1:
                            scene.cue(scene.controller.candidate)
                        elif scene.controller.candidate is None:
                            scene.story.accept(None,scene.time)
            if args.smoke_test and frame%70==0 and frame>=70:
                scene.cue(('tree','1','2','3','fist','tree')[min(frame//70-1,5)])
            image=scene.render(1/30 if args.smoke_test else dt)
            display=window.get_surface()
            dw,dh=display.get_size()
            factor=min(dw/W,dh/H)
            viewport=pygame.Rect(0,0,max(1,int(W*factor)),max(1,int(H*factor)))
            viewport.center=(dw//2,dh//2)
            display.fill((2,3,10))
            display.blit(pygame.transform.smoothscale(image,viewport.size),viewport)
            window.flip()
            if args.smoke_test and frame%70==69:
                output=ROOT/'previews'/f'{scene.cloud.shape}.png'
                output.parent.mkdir(exist_ok=True)
                pygame.image.save(image,str(output))
                smoke_shapes.append(scene.cloud.shape)
            frame+=1
            if args.smoke_test and frame>=490: running=False
            if args.frames and frame>=args.frames: running=False
    finally:
        if camera: camera.stop()
        if args.capture:
            pygame.image.save(scene.canvas,args.capture)
        pygame.quit()
    if args.smoke_test:
        assert smoke_shapes==list(Story.sequence)
        assert np.isfinite(scene.cloud.positions).all()
        print(f'PASS: {frame} frames, {frame/(time.perf_counter()-started):.1f} fps; '
              f'9000 particles; shapes {smoke_shapes}; screenshots in previews/')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-camera',action='store_true')
    parser.add_argument('--camera-index',type=int,default=None)
    parser.add_argument('--smoke-test',action='store_true')
    parser.add_argument('--frames',type=int,default=0)
    parser.add_argument('--capture',type=str)
    run(parser.parse_args())
