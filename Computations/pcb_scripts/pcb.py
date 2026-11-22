"""Minimal KiCad PCB reader: footprints with absolute pad geometry and courtyards."""
import sys,math,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from sx import *
def rot(x,y,deg):
    a=math.radians(deg); return x*math.cos(a)+y*math.sin(a), -x*math.sin(a)+y*math.cos(a)
def short(n):
    return n.replace('/Project Architecture/','').replace('Motor Control - Top Level/','').replace('Motor Control - Inverter/','')
class Pad: pass
class FP: pass
def load(path):
    b=parse(open(path).read()); fps=[]
    for f in find(b,'footprint'):
        o=FP(); P={p[1]:p[2] for p in find(f,'property')}
        o.ref=P.get('Reference','?'); o.val=P.get('Value',''); o.mpn=P.get('Manufacturer Part Number','')
        at=one(f,'at'); o.x,o.y=float(at[1]),float(at[2]); o.rot=float(at[3]) if len(at)>3 else 0.0
        o.layer=one(f,'layer')[1]; o.lib=f[1]; o.pads=[]; o.attr=one(f,'attr')[1:] if one(f,'attr') else []
        o.locked=one(f,'locked') is not None; o.cy=[]
        for g in f:
            if isinstance(g,list) and g and g[0] in('fp_line','fp_rect','fp_poly','fp_circle'):
                l=one(g,'layer')
                if l and 'CrtYd' in l[1]:
                    for k in ('start','end'):
                        q=one(g,k)
                        if q:
                            dx,dy=rot(float(q[1]),float(q[2]),o.rot); o.cy.append((o.x+dx,o.y+dy))
                    if g[0]=='fp_circle':
                        c=one(g,'center'); e=one(g,'end'); r=math.dist((float(c[1]),float(c[2])),(float(e[1]),float(e[2])))
                        cx,cy=rot(float(c[1]),float(c[2]),o.rot)
                        o.cy+=[(o.x+cx-r,o.y+cy-r),(o.x+cx+r,o.y+cy+r)]
                    pl=one(g,'pts')
                    if pl:
                        for q in find(pl,'xy'):
                            dx,dy=rot(float(q[1]),float(q[2]),o.rot); o.cy.append((o.x+dx,o.y+dy))
        for p in find(f,'pad'):
            d=Pad(); d.num=p[1]; d.type=p[2]; d.shape=p[3]
            a=one(p,'at'); px,py=float(a[1]),float(a[2]); d.rot=float(a[3]) if len(a)>3 else 0.0
            dx,dy=rot(px,py,o.rot); d.x,d.y=o.x+dx,o.y+dy
            s=one(p,'size'); d.w,d.h=float(s[1]),float(s[2])
            n=one(p,'net'); d.net=short(n[2]) if n else ''; d.netfull=n[2] if n else ''
            d.layers=one(p,'layers')[1:]; dr=one(p,'drill'); d.drill=dr[1:] if dr else None
            d.ref=o.ref; d.polys=[]
            pr=one(p,'primitives')
            if pr:
                for gp in find(pr,'gr_poly'):
                    pts=[(float(q[1]),float(q[2])) for q in find(one(gp,'pts'),'xy')]
                    d.polys.append([ (d.x+rot(qx,qy,d.rot)[0], d.y+rot(qx,qy,d.rot)[1]) for qx,qy in pts])
            hw,hh=d.w/2,d.h/2
            d.box=[(d.x+rot(cx,cy,d.rot)[0], d.y+rot(cx,cy,d.rot)[1]) for cx,cy in ((-hw,-hh),(hw,-hh),(hw,hh),(-hw,hh))]
            o.pads.append(d)
        fps.append(o)
    return b,fps
def bbox(pts):
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]; return min(xs),min(ys),max(xs),max(ys)
