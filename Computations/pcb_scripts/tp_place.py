"""Place test point pads next to a pad of their net. usage: tp_place.py board.kicad_pcb tp_comps.json out.json"""
import sys,os,json,math
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from pcb import *
from geom import *
RES=0.05; HP=('+VBAT','PHA','PHB','PHC','SRC_LS_A','SRC_LS_B','SRC_LS_C')
TP_R={'0_testpoint:TestPoint_Pad_D0.5mm':0.25,'0_testpoint:TestPoint_Pad_D0.4mm':0.20}
SPACING=1.27; WIN=5.0; RADIAL_COS=0.93
HOLD=()
ICS=('U1','U6','U9','U10','U7','U2','U5')
# preferences: anchors = list of "REF.pad" tried in order (else every pad of the net); point = free target inside a pour of the same net
PREF={
 'TP39':dict(point=(146.0,127.9)), 'TP40':dict(point=(131.6,83.6)),
 'TP19':dict(fixed=(168.98,103.42,'F','U1.36')),
 'TP61':dict(fixed=(180.9,74.85,'F','NT4.1')), 'TP64':dict(fixed=(148.6,75.6,'F','NT8.1')), 'TP67':dict(fixed=(138.5,74.85,'F','NT11.1')),
 'TP68':dict(anchors=['U6.9']), 'TP69':dict(anchors=['U6.10']), 'TP70':dict(anchors=['U6.12']), 'TP71':dict(anchors=['U6.11']), 'TP72':dict(anchors=['U6.19']), 'TP73':dict(anchors=['U6.20']), 'TP41':dict(anchors=['C92.1','C95.1','C91.1']),
 'TP46':dict(anchors=['C147.1']), 'TP47':dict(anchors=['C51.1','C58.1','C62.1'],side='B'),
 'TP48':dict(anchors=['C1.1','C4.1','C5.1','C9.1']), 'TP49':dict(anchors=['C121.1','C125.1','C127.1','C129.1','C123.1']), 'TP50':dict(anchors=['C115.2','R46.1','C12.1']),
 'TP51':dict(anchors=['FB1.1','C2.1','R33.1']),
 'TP52':dict(point=(156.5,97.5)), 'TP53':dict(point=(172.0,112.0)), 'TP54':dict(point=(137.0,107.0)), 'TP55':dict(point=(152.0,122.5)),
 'TP56':dict(point=(183.0,108.5)), 'TP57':dict(point=(181.5,71.5)), 'TP58':dict(point=(116.5,74.5)),
 'TP59':dict(anchors=['R18.2','D4.1']), 'TP60':dict(anchors=['R19.1','D5.1']), 'TP62':dict(anchors=['R24.1','D9.1']), 'TP63':dict(anchors=['R23.1','D7.1']),
 'TP65':dict(anchors=['R29.1','D11.1']), 'TP66':dict(anchors=['R28.1','D10.1']),
 'TP11':dict(anchors=['R5.2']), 'TP12':dict(anchors=['R6.2']), 'TP13':dict(anchors=['R7.2']),
 'TP14':dict(anchors=['J15.2','D1.5','D1.6']), 'TP15':dict(anchors=['J15.4','D1.4','D1.7']), 'TP16':dict(anchors=['J15.3','C13.1','D1.1','D1.10']),
 'TP36':dict(anchors=['R42.2','C111.1','D16.2']), 'TP37':dict(anchors=['R41.2','C110.1','D15.2','TH1.1']), 'TP38':dict(anchors=['C112.1','R44.1','R43.2']),
}
def raster(poly,x0,y0,nx,ny):
    m=np.zeros((ny,nx),bool)
    if len(poly)<3: return m
    xs=x0+(np.arange(nx)+0.5)*RES; ys=y0+(np.arange(ny)+0.5)*RES
    X,Y=np.meshgrid(xs,ys); n=len(poly)
    for k in range(n):
        xa,ya=poly[k]; xb,yb=poly[(k+1)%n]
        if ya==yb: continue
        m^=((ya>Y)!=(yb>Y)) & (X < (xb-xa)*(Y-ya)/(yb-ya)+xa)
    return m
def dilate(m,r):
    if r<=0 or not m.any(): return m.copy()
    ny,nx=m.shape; k=int(math.ceil(r/RES)); out=m.copy()
    for dy in range(-k,k+1):
        w=int(math.floor(math.sqrt(max(0,(r/RES)**2-dy*dy))))
        src=m[max(0,-dy):ny-max(0,dy),:]
        if src.size==0: continue
        cs=np.cumsum(np.pad(src,((0,0),(w+1,w))).astype(np.int32),axis=1)
        h=(cs[:,2*w+1:]-cs[:,:-(2*w+1)])>0
        out[max(0,dy):ny-max(0,-dy),:]|=h[:,:nx]
    return out
class Board:
    def __init__(s,path):
        s.b,s.fps=load(path)
        s.pads={'F':[],'B':[]}; s.cy={'F':[],'B':[]}
        for f in s.fps:
            side='F' if f.layer=='F.Cu' else 'B'
            if f.cy: s.cy[side].append((f.ref,hull(f.cy)))
            for p in f.pads:
                polys=(p.polys+[p.box]) if p.polys else [p.box]
                bx=bbox([q for pl in polys for q in pl])
                for sd,ly in (('F','F.Cu'),('B','B.Cu')):
                    if ly in p.layers or '*.Cu' in p.layers or p.type in('thru_hole','np_thru_hole'):
                        s.pads[sd].append((p,polys,bx))
        s.zones=[]; s.areas=[]
        for z in find(s.b,'zone'):
            net=one(z,'net_name'); lay=one(z,'layer') or one(z,'layers'); nm=one(z,'name')
            pts=[(float(q[1]),float(q[2])) for q in find(one(one(z,'polygon'),'pts'),'xy')]
            if one(z,'keepout'): s.areas.append((nm[1] if nm else '',lay[1:],pts))
            else: s.zones.append((short(net[1]) if net else '',lay[1:],pts,nm[1] if nm else ''))
        s.fid=[(f.x,f.y) for f in s.fps if f.ref.startswith('FM')]
        s.centre={f.ref:(f.x,f.y) for f in s.fps}
    def masks(s,side,net,r,cx,cy,placed):
        x0,y0=cx-WIN,cy-WIN; n=int(2*WIN/RES); ly='F.Cu' if side=='F' else 'B.Cu'
        hp=net in HP
        fb=np.zeros((n,n),bool); tr=np.zeros((n,n),bool)
        w=(x0,y0,x0+2*WIN,y0+2*WIN)
        def near(bx,m): return bx[0]<w[2]+m and bx[2]>w[0]-m and bx[1]<w[3]+m and bx[3]>w[1]-m
        for ref,poly in s.cy[side]:
            if near(bbox(poly),0.5): fb|=dilate(raster(poly,x0,y0,n,n),r+0.05)
        for p,polys,bx in s.pads[side]:
            if p.net==net or not near(bx,1.0): continue
            clr=(0.5 if (hp or p.net in HP) else 0.2)+0.06   # raster tolerance
            m=np.zeros((n,n),bool)
            for pl in polys: m|=raster(pl,x0,y0,n,n)
            fb|=dilate(m,r+clr); tr|=dilate(m,0.1+clr)
        for znet,lays,pts,name in s.zones:
            if ly not in lays or znet==net or znet=='GND': continue
            if near(bbox(pts),1.0):
                m=raster(pts,x0,y0,n,n); clr=(0.5 if (hp or znet in HP) else 0.2)+0.06
                fb|=dilate(m,r+clr); tr|=dilate(m,0.1+clr)
        for name,lays,pts in s.areas:
            if name=='ECAT_ISOLATION' and near(bbox(pts),0.5): fb|=raster(pts,x0,y0,n,n)
        xs=x0+(np.arange(n)+0.5)*RES; ys=y0+(np.arange(n)+0.5)*RES; X,Y=np.meshgrid(xs,ys)
        fb|=((X-150)**2+(Y-100)**2)>(44-0.5-r)**2
        for fx,fy in s.fid: fb|=((X-fx)**2+(Y-fy)**2)<(1.6+r)**2
        for px,py,ps in placed:
            if ps==side: fb|=((X-px)**2+(Y-py)**2)<SPACING**2
        return fb,tr,X,Y,x0,y0,n
    def in_zone(s,side,net,x,y):
        ly='F.Cu' if side=='F' else 'B.Cu'
        return [nm for znet,lays,pts,nm in s.zones if znet==net and ly in lays and inside(pts,x,y)]
def place(path,comps_path):
    B=Board(path); comps=json.load(open(comps_path)); out=[]; fails=[]
    onboard={f.ref:f for f in B.fps if f.ref.startswith('TP')}
    placed=[(f.x,f.y,'F' if f.layer=='F.Cu' else 'B') for f in onboard.values()]
    padidx={}
    for sd in 'FB':
        for p,polys,bx in B.pads[sd]: padidx.setdefault((p.ref+'.'+p.num,sd),(p,polys,bx))
    order=sorted(comps.values(),key=lambda c:(0 if c['ref'] in PREF and 'anchors' in PREF[c['ref']] else 1, int(c['ref'][2:])))
    # crowded driver-area signals first
    order.sort(key=lambda c:-1 if 'fixed' in PREF.get(c['ref'],{}) else 0 if short(c['net']) in ('SA+','SA-','SB+','SB-','SC+','SC-','SHA','SHB','SHC','GHA','GHB','GHC','GLA','GLB','GLC') else 1)
    for c in order:
        if c['ref'] in HOLD or c['ref'] in onboard: continue
        ref=c['ref']; net=short(c['net']); r=TP_R[c['fp']]; pref=PREF.get(ref,{}); best=None
        sides=[pref['side']] if 'side' in pref else ['F','B']
        if 'fixed' in pref:
            fx,fy,fs,fa=pref['fixed']; best=(0.0,fx,fy,fs,fa); sides=[]
        for side in sides:
            if 'point' in pref:
                cx,cy=pref['point']; fb,tr,X,Y,x0,y0,n=B.masks(side,net,r,cx,cy,placed)
                ly='F.Cu' if side=='F' else 'B.Cu'
                zm=np.zeros((n,n),bool)
                for znet,lays,pts,nm in B.zones:
                    if znet==net and ly in lays and (net!='GND' or 'fill' in nm): zm|=raster(pts,x0,y0,n,n)
                if net=='GND':   # GND fill is knocked out by every higher-priority pour
                    for znet,lays,pts,nm in B.zones:
                        if znet!='GND' and ly in lays: zm&=~dilate(raster(pts,x0,y0,n,n),r+0.6)
                ok=~fb & zm
                if ok.any():
                    d=np.hypot(X-cx,Y-cy); d[~ok]=1e9; j,i=np.unravel_index(np.argmin(d),d.shape)
                    cand=(float(d[j,i]),float(X[j,i]),float(Y[j,i]),side,'pour')
                    if best is None or cand[0]<best[0]: best=cand
            else:
                anchors=pref.get('anchors') or sorted([a for (a,sd) in padidx if sd==side and padidx[(a,sd)][0].net==net and not a.startswith('TP')],key=lambda a:(a.split('.')[0] in ICS,a))
                for rank,a in enumerate(anchors):
                    if (a,side) not in padidx: continue
                    p,polys,bx=padidx[(a,side)]
                    if p.net!=net: continue
                    fb,tr,X,Y,x0,y0,n=B.masks(side,net,r,p.x,p.y,placed)
                    pm=np.zeros((n,n),bool)
                    for pl in polys: pm|=raster(pl,x0,y0,n,n)
                    # distance to pad edge via dilation rings
                    dist=np.full((n,n),1e9)
                    isic=a.split('.')[0] in ICS
                    for rr in np.arange(1.0 if isic else 0.5,4.0,0.1):
                        ring=dilate(pm,rr+r)&(dist>1e8); dist[ring]=rr
                    ok=~fb & (dist<1e8)
                    js,is_=np.nonzero(ok)
                    if len(js)==0: continue
                    cands=sorted(zip(dist[js,is_],js,is_))
                    for dval,j,i in cands[::5]:
                        x,y=float(X[j,i]),float(Y[j,i])
                        if isic:   # stay on the pin's own escape line, pointing away from the IC
                            ox,oy=B.centre[a.split('.')[0]]; v1=(p.x-ox,p.y-oy); v2=(x-p.x,y-p.y)
                            n1=math.hypot(*v1); n2=math.hypot(*v2)
                            if n1==0 or n2==0 or (v1[0]*v2[0]+v1[1]*v2[1])/(n1*n2)<RADIAL_COS: continue
                        # straight track to the pad centre must be clear outside the pad
                        L=math.hypot(p.x-x,p.y-y); m=max(2,int(L/RES)); clear=True
                        for k in range(m+1):
                            sx=x+(p.x-x)*k/m; sy=y+(p.y-y)*k/m; jj=int((sy-y0)/RES); ii=int((sx-x0)/RES)
                            if 0<=jj<n and 0<=ii<n and tr[jj,ii] and not pm[jj,ii]: clear=False; break
                        if clear:
                            score=float(dval)+(0.6*rank if pref.get('anchors') else (1.2 if isic else 0))+(0 if side=='F' else 5)
                            cand=(score,x,y,side,a)
                            if best is None or cand[0]<best[0]: best=cand
                            break
                    if best is not None and pref.get('anchors') and best[4]==a: break
            if best is not None and best[3]=='F': break
        if best is None: fails.append(ref); continue
        placed.append((best[1],best[2],best[3]))
        out.append(dict(ref=ref,net=net,fp=c['fp'],x=round(best[1],2),y=round(best[2],2),side=best[3],anchor=best[4],score=round(best[0],2)))
    return out,fails,B
if __name__=='__main__':
    out,fails,B=place(sys.argv[1],sys.argv[2]); json.dump(out,open(sys.argv[3],'w'),indent=0)
    import collections
    print('placed',len(out),collections.Counter(o['side'] for o in out),'failed',fails)
    for o in sorted(out,key=lambda o:int(o['ref'][2:])): print(o['ref'].ljust(5),o['net'][:26].ljust(26),o['side'],(o['x'],o['y']),'->',o['anchor'],o['score'])
