"""Small 2D geometry helpers (mm)."""
import math
def hull(pts):
    pts=sorted(set((round(x,4),round(y,4)) for x,y in pts))
    if len(pts)<3: return pts
    def cr(o,a,b): return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lo=[]
    for p in pts:
        while len(lo)>=2 and cr(lo[-2],lo[-1],p)<=0: lo.pop()
        lo.append(p)
    up=[]
    for p in reversed(pts):
        while len(up)>=2 and cr(up[-2],up[-1],p)<=0: up.pop()
        up.append(p)
    return lo[:-1]+up[:-1]
def inside(poly,x,y):
    n=len(poly); c=False
    for k in range(n):
        xa,ya=poly[k]; xb,yb=poly[(k+1)%n]
        if (ya>y)!=(yb>y) and x<(xb-xa)*(y-ya)/(yb-ya)+xa: c=not c
    return c
def seg_dist(px,py,ax,ay,bx,by):
    dx,dy=bx-ax,by-ay; L=dx*dx+dy*dy
    t=0 if L==0 else max(0,min(1,((px-ax)*dx+(py-ay)*dy)/L))
    return math.hypot(px-(ax+t*dx),py-(ay+t*dy))
def poly_dist(poly,x,y):
    """distance from point to polygon (0 if inside)"""
    if len(poly)>=3 and inside(poly,x,y): return 0.0
    n=len(poly)
    if n==1: return math.hypot(x-poly[0][0],y-poly[0][1])
    return min(seg_dist(x,y,*poly[k],*poly[(k+1)%n]) for k in range(n))
def seg_poly_dist(ax,ay,bx,by,poly,step=0.1):
    L=math.hypot(bx-ax,by-ay); n=max(1,int(L/step))
    return min(poly_dist(poly,ax+(bx-ax)*k/n,ay+(by-ay)*k/n) for k in range(n+1))
