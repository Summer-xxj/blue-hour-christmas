# xxj-summer-zjl
"""Procedural optical textures: nebula, soft light and translucent swallowtails."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import pygame


def surface(image):
    return pygame.image.frombytes(image.tobytes(),image.size,image.mode)


def nebula(width,height):
    rng=np.random.default_rng(831)
    w,h=width//2,height//2
    y,x=np.mgrid[0:h,0:w].astype('float32')
    x/=w; y/=h
    field=np.zeros((h,w),dtype='float32')
    amplitude=1.
    for frequency in (5,11,23,47,95,180):
        noise=(rng.random((max(2,int(frequency*h/w)),frequency))*255).astype('uint8')
        layer=Image.fromarray(noise).resize((w,h),Image.Resampling.BICUBIC)
        field+=np.asarray(layer)/255*amplitude
        amplitude*=.53
    field=(field-field.min())/(field.max()-field.min())
    warp=.08*np.sin(y*13+x*8)+.035*np.sin(y*31-x*17)
    left=np.exp(-((x-(.11+.12*np.sin(y*6)+warp))/.18)**2)
    right=np.exp(-((x-(.88+.14*np.sin(y*8+2)+warp))/.19)**2)
    cloud=(left+right)*np.clip((field-.20)*1.7,0,1)**2
    galaxy=np.exp(-((y-(.18+.57*x+.055*np.sin(x*9)+warp*.45))/.16)**2)
    cloud+=galaxy*np.clip((field-.19)*1.8,0,1)**1.5
    filaments=(left+right)*np.exp(-((field-.56)/.085)**2)*.16
    purple=(.5+.5*np.sin(y*8+x*5))
    rgb=np.empty((h,w,3),dtype='float32')
    separation=1-.50*np.exp(-((x-.5)/.19)**2-((y-.50)/.36)**2)
    cloud*=separation
    rgb[:,:,0]=9+cloud*(26+purple*39)+filaments*35
    rgb[:,:,1]=13+cloud*(43-purple*13)+filaments*43
    rgb[:,:,2]=36+cloud*(104+purple*26)+filaments*92
    # A quiet halo lifts the subject from its dark immediate surroundings.
    halo=np.exp(-((x-.5)/.23)**2-((y-.52)/.42)**2)
    rgb+=halo[:,:,None]*np.array([3,3,13])
    image=Image.fromarray(np.uint8(np.clip(rgb,0,255))).resize((width,height),Image.Resampling.BICUBIC)
    draw=ImageDraw.Draw(image)
    for _ in range(4200):
        sx=int(rng.uniform(0,width)); sy=int(rng.uniform(0,height))
        value=int(rng.uniform(35,140))
        draw.point((sx,sy),fill=(int(value*.68),int(value*.76),value))
    return surface(image)


def glow(radius,rgb,strength=1.,pixel_scale=1.):
    axis=np.arange(-radius,radius+1,dtype='float32')
    yy,xx=np.meshgrid(axis,axis)
    d=xx*xx+yy*yy
    spread=max(1.,radius*.33)
    weight=(np.exp(-d/(spread*spread))*.25+np.exp(-d/(1.15*pixel_scale**2))*.95)*strength
    values=np.uint8(np.clip(weight[:,:,None]*np.asarray(rgb),0,255))
    return pygame.surfarray.make_surface(values.transpose(1,0,2))


def bezier(points,n=45):
    a,b,c,d=points
    return [((1-t)**3*a[0]+3*(1-t)**2*t*b[0]+3*(1-t)*t*t*c[0]+t**3*d[0],
             (1-t)**3*a[1]+3*(1-t)**2*t*b[1]+3*(1-t)*t*t*c[1]+t**3*d[1])
            for t in np.linspace(0,1,n)]


def butterfly_texture():
    size=640
    mask=Image.new('L',(size,size))
    md=ImageDraw.Draw(mask)
    cx,cy,unit=320,300,215
    def pos(p,side=1): return cx+p[0]*unit*side,cy+p[1]*unit
    upper=bezier([(0,0),(.25,-.50),(.75,-1.12),(1.19,-1.10)])
    upper+=bezier([(1.19,-1.10),(1.13,-.39),(.67,.06),(0,0)])
    lower=bezier([(0,0),(.39,-.02),(.98,.08),(.79,.44)])
    lower+=bezier([(.79,.44),(.53,.57),(.44,.30),(.29,1.03)])
    lower+=bezier([(.29,1.03),(.13,.67),(.12,.26),(0,0)])
    for side in (-1,1):
        md.polygon([pos(p,side) for p in upper],fill=185)
        md.polygon([pos(p,side) for p in lower],fill=160)
    y,x=np.mgrid[0:size,0:size]
    dx=(x-cx)/unit; dy=(y-cy)/unit
    shine=np.exp(-((np.abs(dx)-.45)**2+(dy+.40)**2)/.12)
    array=np.zeros((size,size,4),dtype='uint8')
    array[:,:,0]=np.clip(95+shine*82+np.maximum(0,dy)*30,0,255)
    array[:,:,1]=np.clip(105+shine*110,0,255)
    array[:,:,2]=np.clip(220+shine*35,0,255)
    array[:,:,3]=np.asarray(mask)
    wing=Image.fromarray(array)
    detail=Image.new('RGBA',(size,size))
    draw=ImageDraw.Draw(detail)
    for side in (-1,1):
        for path in (upper,lower):
            draw.line([pos(p,side) for p in path],fill=(208,203,255,180),width=2)
        for k in (.26,.40,.56,.74,.94):
            curve=bezier([(0,.02),(k*.28,-.33),(k*.87,-.42),(k*1.13,-.96)])
            draw.line([pos(p,side) for p in curve],fill=(229,199,142,210),width=2)
        for k in (.3,.5,.7):
            curve=bezier([(0,.04),(k*.6,.10),(k,.22),(k*.88,.40)])
            draw.line([pos(p,side) for p in curve],fill=(180,193,255,145),width=1)
        # Fine calligraphic curls, gently luminous rather than solid metal.
        for j in range(3):
            path=[]
            for t in np.linspace(0,math.pi*3,100):
                r=.085*(1-t/(math.pi*3))
                path.append(pos((.43+j*.13+r*math.cos(t),-.40-j*.13+r*math.sin(t)),side))
            draw.line(path,fill=(239,208,154,180),width=2)
        for k in range(26):
            t=k/25
            px,py=pos((1.02*t,-.82*t-.04),side)
            draw.ellipse((px-1.5,py-1.5,px+1.5,py+1.5),fill=(245,221,177,200))
        antenna=bezier([(0,-.04),(.04,-.18),(.14,-.23),(.13,-.18)])
        draw.line([pos(p,side) for p in antenna],fill=(245,221,184,210),width=2)
    draw.line([(cx,cy-15),(cx,cy+52)],fill=(255,232,185,230),width=4)
    # A blurred copy creates optically soft edges while preserving the vein detail.
    wing=Image.alpha_composite(wing,detail.filter(ImageFilter.GaussianBlur(4)))
    wing=Image.alpha_composite(wing,detail)
    return surface(wing)
