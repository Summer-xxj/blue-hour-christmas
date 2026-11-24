# xxj-summer-zjl
"""Calligraphic text sampled into separate luminous grains, in a fixed left margin."""
from pathlib import Path
import math
import numpy as np
import pygame
from PIL import Image, ImageDraw, ImageFont


class ParticleDedication:
    def __init__(self,scale):
        self.scale=scale
        self.origin=(35*scale,300*scale)
        self.size=(440*scale,175*scale)
        mask=Image.new('L',self.size)
        draw=ImageDraw.Draw(mask)
        font_path='/System/Library/Fonts/Supplemental/SnellRoundhand.ttc'
        for label,size,y in [('Merry Christmas',54,12),('from Summer',38,102)]:
            font=ImageFont.truetype(font_path,size*scale)
            box=draw.textbbox((0,0),label,font=font)
            x=(self.size[0]-(box[2]-box[0]))/2-box[0]
            draw.text((x,y*scale-box[1]),label,font=font,fill=255)
        rng=np.random.default_rng(122503)
        field=np.asarray(mask)
        step=3  # native render pixels: distinct pinpoints, not a filled text bitmap
        yy,xx=np.mgrid[0:self.size[1]:step,0:self.size[0]:step]
        xx=np.clip(xx+rng.integers(0,2,xx.shape),0,self.size[0]-1)
        yy=np.clip(yy+rng.integers(0,2,yy.shape),0,self.size[1]-1)
        keep=field[yy,xx]>100
        self.points=np.column_stack((xx[keep],yy[keep]))
        self.phase=rng.uniform(0,math.tau,len(self.points))
        self.base=pygame.Surface(self.size)
        self.spark=pygame.Surface((9,9))
        axis=np.arange(-4,5); y,x=np.meshgrid(axis,axis)
        weight=np.exp(-(x*x+y*y)/1.8)+.07*np.exp(-(x*x+y*y)/8)
        rgb=np.uint8(np.clip(weight[:,:,None]*[255,229,180],0,255))
        self.spark=pygame.surfarray.make_surface(rgb)
        for i,(x,y) in enumerate(self.points):
            tone=(239,207,155) if y<95*scale else (185,192,245)
            light=.5+rng.random()*.45
            pygame.draw.circle(self.base,tuple(int(c*light) for c in tone),(int(x),int(y)),1)
        self.layer=pygame.Surface(self.size)

    def draw(self,canvas,time,fade):
        self.layer.blit(self.base,(0,0))
        for i in range(0,len(self.points),17):
            pulse=(.5+.5*math.sin(time*2.1+self.phase[i]))**16
            if pulse>.45:
                x,y=self.points[i]
                self.layer.blit(self.spark,(int(x)-4,int(y)-4),special_flags=pygame.BLEND_RGB_ADD)
        self.layer.fill((int(255*fade),)*3,special_flags=pygame.BLEND_RGB_MULT)
        canvas.blit(self.layer,self.origin,special_flags=pygame.BLEND_RGB_ADD)
