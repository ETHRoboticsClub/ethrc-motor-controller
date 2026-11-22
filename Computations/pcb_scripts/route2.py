"""Two-layer grid router (L1 / L6 with through vias) on top of route.World.
A via is allowed only where it clears copper on L1, L6 and the inner tracks (L3/L4 lines; pours give way), so
step 5's L4 bundles are respected. Paths use 0/45/90-degree moves only, bends and vias cost extra.

    from route2 import route2
    res=route2(W,'NET',0.2,('F.Cu',(x,y)),('B.Cu',(x,y)),box=(x0,y0,x1,y1))
    # res = dict(segs=[(layer,[pts])...], vias=[(x,y)...]); add_route2(W,'NET',0.2,res) plans it
"""
import math,heapq
import numpy as np
from route import World,DIRS,link,clean
LAY=('F.Cu','B.Cu')
def via_map(W,net,x0,y0,nx,ny,g,r=0.275,eps=0.03):
    allz=tuple(z['ref'] for z in W.zones)
    m=np.zeros((ny,nx),bool)
    for lay in LAY: m|=W.blocked(net,lay,r,x0,y0,nx,ny,g,allow=allz,eps=eps)
    for lay in ('In2.Cu','In3.Cu'): m|=W.blocked(net,lay,r,x0,y0,nx,ny,g,allow=allz,eps=eps)
    # drill to drill with every hole (different nets need 0.5 mm hole to hole, i.e. centres 0.75 apart)
    X=x0+g*np.arange(nx)[None,:]; Y=y0+g*np.arange(ny)[:,None]
    for o in W.obs:
        if 'hole' not in o: continue
        hx,hy=o.get('hx',o.get('x')),o.get('hy',o.get('y'))
        if hx is None or hx<x0-1 or hx>x0+g*nx+1 or hy<y0-1 or hy>y0+g*ny+1: continue
        need=0.254 if o['net']==net else 0.5
        m|=(np.hypot(X-hx,Y-hy)<o['hole']+0.125+need)
    return ~m
INNER=('In2.Cu','In3.Cu')
CIRCLE=((150.0,100.0),4.3)          # L3 may only be used inside the encoder keepout circle, 0.7 mm clear of the pour edge
def route2(W,net,w,start,end,box,g=0.1,via_cost=2.0,bend=0.6,layers=LAY,max_pops=3000000,quiet=False,eps=0.04,circle=CIRCLE):
    net=W.canon(net); hw=w/2
    (sl,(sx,sy)),(el,(ex,ey))=start,end
    i_off=int(math.ceil((sx-box[0])/g)); j_off=int(math.ceil((sy-box[1])/g)); x0=sx-i_off*g; y0=sy-j_off*g
    nx=int((box[2]-x0)/g)+1; ny=int((box[3]-y0)/g)+1
    allz=tuple(z['ref'] for z in W.zones)
    BL={}
    for L in layers:
        if L in INNER:                                  # inner layers: pours give way only inside the keepout circle
            B=W.blocked(net,L,hw,x0,y0,nx,ny,g,eps=eps,allow=allz)
            X=x0+g*np.arange(nx)[None,:]; Y=y0+g*np.arange(ny)[:,None]
            (cx,cy),r=circle; B|=(np.hypot(X-cx,Y-cy)>r-hw)
            if L=='In2.Cu':                             # never run over an L4 track (tracks only; vias are handled above)
                for o in W.obs:
                    if o['k']=='s' and o.get('lay') and 'In3.Cu' in o['lay'] and o['net']!=net:
                        B|=(W._dist(o,X,Y)<o['r']+hw+0.3)
            BL[L]=B
        else: BL[L]=W.blocked(net,L,hw,x0,y0,nx,ny,g,eps=eps)
    VM=via_map(W,net,x0,y0,nx,ny,g)
    si,sj=i_off,j_off; BL[sl][sj,si]=False
    ti=int(round((ex-x0)/g)); tj=int(round((ey-y0)/g))
    li={L:k for k,L in enumerate(layers)}
    def h(i,j): dx,dy=abs(i-ti),abs(j-tj); return g*(max(dx,dy)+0.41421356*min(dx,dy))
    INF=1e18; best={}; prev={}; pq=[]
    s0=(si,sj,li[sl],-1); best[s0]=0.0; prev[s0]=None; heapq.heappush(pq,(h(si,sj),0.0,s0))
    goal=None; pops=0
    while pq:
        f,c,s=heapq.heappop(pq)
        if best.get(s,INF)<c-1e-9: continue
        pops+=1
        if pops>max_pops: break
        i,j,l,d=s
        if abs(i-ti)<=1 and abs(j-tj)<=1 and layers[l]==el: goal=s; break
        cand=[]
        for dd in ((0,) if d<0 else (0,1,-1)) if d>=0 else range(8):
            nd=(d+dd)%8 if d>=0 else dd; di,dj=DIRS[nd]; ni,nj=i+di,j+dj
            if 0<=ni<nx and 0<=nj<ny and not BL[layers[l]][nj,ni]:
                cand.append(((ni,nj,l,nd),g*math.hypot(di,dj)+(bend if (d>=0 and nd!=d) else 0.0)))
        if VM[j,i]:                                       # change layer here (through via)
            for l2 in range(len(layers)):
                if l2!=l and not BL[layers[l2]][j,i]: cand.append(((i,j,l2,-1),via_cost))
        for ns,dc in cand:
            nc=c+dc
            if nc<best.get(ns,INF)-1e-9:
                best[ns]=nc; prev[ns]=s; heapq.heappush(pq,(nc+h(ns[0],ns[1]),nc,ns))
    if goal is None:
        if not quiet: print('  !! route2: no route',net,start,end,'pops',pops)
        return None
    chain=[]; s=goal
    while s is not None: chain.append(s); s=prev[s]
    chain.reverse()
    segs=[]; vias=[]; cur=[]; curl=chain[0][2]
    for (i,j,l,d) in chain:
        p=(round(x0+i*g,4),round(y0+j*g,4))
        if l!=curl:
            segs.append((layers[curl],cur)); vias.append(p); cur=[p]; curl=l
        elif not cur or cur[-1]!=p: cur.append(p)
    # join the exact end point: back off along the path and use a straight + 45-degree link (no micro segments)
    done=False
    for back in range(0,min(len(cur),12)):
        k=len(cur)-1-back
        if k<0: break
        for df in (False,True):
            tail=link(cur[k],(ex,ey),df)
            if W.margin(net,layers[curl],hw,tail)[0]>-0.02 and all(math.dist(a,b)>0.12 or a==b for a,b in zip(tail,tail[1:])):
                cur=cur[:k]+tail; done=True; break
        if done: break
    if not done: cur=cur+link(cur[-1],(ex,ey))[1:]
    while len(cur)>2 and math.dist(cur[-2],(ex,ey))<0.3: cur.pop(-2)      # no stubs inside the end pad or via
    segs.append((layers[curl],cur))
    segs=[(L,clean(p)) for L,p in segs if len(clean(p))>=2]
    if not quiet:
        ln=sum(math.dist(a,b) for _,p in segs for a,b in zip(p,p[1:])); print('  route2 %-14s len %5.1f vias %d pops %d'%(net.split('/')[-1],ln,len(vias),pops))
    return dict(segs=segs,vias=vias)
def add_route2(W,net,w,res):
    for L,p in res['segs']: W.add_track(net,L,w,p)
    for v in res['vias']: W.add_via(net,v[0],v[1],check=False)
