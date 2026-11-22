"""Clearance-aware planning helper for scripted routing: obstacle model of a board, a 45-degree grid router,
parallel bundles and via checks. It only plans; apply_plan.py writes the result into the board.

    W=World('board.kicad_pcb')
    pts=W.route('GHC','F.Cu',0.28,start,end)          # list of (x,y), 0/45/90 degree segments only
    W.add_track('GHC','F.Cu',0.28,pts); W.add_via('GND',x,y); W.save('plan.json')
"""
import sys,os,math,heapq,json
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from pcb import *
CX,CY,RB=150.0,100.0,44.0            # board outline: circle
EDGE=0.3                              # copper to board edge
def is_hv(n): return n=='+VBAT' or (n.startswith('PH') and len(n)==3)
def clearance(a,b):
    """Required copper clearance between two different nets on an outer layer (mirrors the .kicad_dru HV rule)."""
    if is_hv(a) or is_hv(b):
        if is_hv(a) and is_hv(b): return 0.5
        hv,o=(a,b) if is_hv(a) else (b,a)
        if 'SNUB' in o: return 0.2
        if hv.startswith('PH') and o in ('SH'+hv[2],'GH'+hv[2],'FET_GH'+hv[2]): return 0.2
        if hv=='+VBAT' and o in('VCP','CPH'): return 0.2
        return 0.5
    return 0.2
def link(a,b,diag_first=False):
    """Connect two exact points with one straight and one 45-degree segment."""
    dx,dy=b[0]-a[0],b[1]-a[1]; m=min(abs(dx),abs(dy)); sx=1 if dx>=0 else -1; sy=1 if dy>=0 else -1
    if m<1e-6 or abs(abs(dx)-abs(dy))<1e-6: return [a,b]
    if diag_first: c=(a[0]+sx*m,a[1]+sy*m)
    else: c=(b[0]-sx*m,b[1]-sy*m)
    return [a,c,b]
def clean(pts):
    out=[pts[0]]
    for p in pts[1:]:
        if math.dist(p,out[-1])>1e-6: out.append(p)
    k=1
    while k<len(out)-1:
        (ax,ay),(bx,by),(cx,cy)=out[k-1],out[k],out[k+1]
        if abs((bx-ax)*(cy-by)-(by-ay)*(cx-bx))<1e-7 and (bx-ax)*(cx-bx)+(by-ay)*(cy-by)>0: out.pop(k)
        else: k+=1
    return out
def offset(pts,d):
    """Parallel copy of a polyline, d mm to the left of the travel direction (screen: y down)."""
    n=len(pts); L=[]
    for k in range(n-1):
        (ax,ay),(bx,by)=pts[k],pts[k+1]; l=math.hypot(bx-ax,by-ay); ux,uy=(bx-ax)/l,(by-ay)/l
        nx,ny=uy,-ux                                   # left of travel with y pointing down
        L.append(((ax+nx*d,ay+ny*d),(ux,uy)))
    out=[L[0][0]]
    for k in range(1,n-1):
        (p,u),(q,v)=L[k-1],L[k]; den=u[0]*v[1]-u[1]*v[0]
        if abs(den)<1e-9: out.append(q); continue
        t=((q[0]-p[0])*v[1]-(q[1]-p[1])*v[0])/den; out.append((p[0]+u[0]*t,p[1]+u[1]*t))
    (ax,ay),(bx,by)=pts[-2],pts[-1]; l=math.hypot(bx-ax,by-ay); out.append((bx+(by-ay)/l*d,by-(bx-ax)/l*d))
    return out
DIRS=[(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1),(0,-1),(1,-1)]
def dir_of(v):
    a=math.degrees(math.atan2(v[1],v[0]))%360; return int(round(a/45))%8
class World:
    def __init__(self,path):
        self.path=path; self.b,self.fps=load(path); self.R={f.ref:f for f in self.fps}
        self.full={}; self.obs=[]; self.plan={'place':[],'move':[],'drop_nets':[],'drop_segs':[],'vias':[],'tracks':[]}
        nets={}
        for n in find(self.b,'net'):
            if len(n)>=3 and isinstance(n[2],str): nets[n[1]]=n[2]; self.full[short(n[2])]=n[2]
        self.netcode=nets
        for f in self.fps: self._fp_obs(f)
        for v in find(self.b,'via'):
            a=one(v,'at'); self.obs.append(dict(k='c',x=float(a[1]),y=float(a[2]),r=float(one(v,'size')[1])/2,net=short(nets.get(one(v,'net')[1],'')),lay=None,ref='via',hole=float(one(v,'drill')[1])/2))
        for t in find(self.b,'segment'):
            s,e=one(t,'start'),one(t,'end')
            self.obs.append(dict(k='s',p=(float(s[1]),float(s[2]),float(e[1]),float(e[2])),r=float(one(t,'width')[1])/2,net=short(nets.get(one(t,'net')[1],'')),lay={one(t,'layer')[1]},ref='trk'))
        self.zones=[]
        for z in find(self.b,'zone'):
            net=one(z,'net_name'); n=short(net[1]) if net else ''
            ko=one(z,'keepout')
            if ko is not None:                                   # rule area: an obstacle only where it forbids tracks
                tr=one(ko,'tracks')
                if not (tr and tr[1]=='not_allowed'): continue
                n='#KEEPOUT'
            elif n in('GND',''): continue
            lay=one(z,'layer') or one(z,'layers'); nm=one(z,'name')
            rings=[[(float(q[1]),float(q[2])) for q in find(one(pl,'pts'),'xy')] for pl in find(z,'polygon')]   # outline, then holes
            self.zones.append(dict(k='p',pts=rings[0],rings=rings,net=n,lay=set(lay[1:]),ref='zone:'+(nm[1] if nm else '')))
    def _fp_obs(self,f):
        for p in f.pads:
            lay=set()
            for l in p.layers:
                if l=='*.Cu': lay=None; break
                if l.endswith('.Cu'): lay.add(l)
            if lay is not None and not lay:
                if p.type=='np_thru_hole': lay=None
                else: continue
            if p.shape=='circle' or (p.shape=='oval' and abs(p.w-p.h)<1e-6): o=dict(k='c',x=p.x,y=p.y,r=max(p.w,p.h)/2)
            else: o=dict(k='p',pts=p.box)
            o.update(net=p.net,lay=lay,ref=f.ref+'.'+p.num,npth=(p.type=='np_thru_hole'))
            for poly in getattr(p,'polys',[]):                 # custom pad primitives
                self.obs.append(dict(k='p',pts=poly,net=p.net,lay=lay,ref=f.ref+'.'+p.num))
            if p.drill:
                try: o['hole']=float([d for d in p.drill if d not in('oval',) and not isinstance(d,list)][0])/2; o['hx'],o['hy']=p.x,p.y
                except Exception: pass
            self.obs.append(o)
    def refresh(self,ref):
        """Rebuild the obstacles of one footprint after a planned move (pads given as absolute boxes)."""
        self.obs=[o for o in self.obs if not o['ref'].startswith(ref+'.')]; self._fp_obs(self.R[ref])
    # ---------------------------------------------------------------- planning primitives
    def canon(self,n):
        """Accept a net by its last path element (e.g. 'SW_5V' for 'Power - Generation/SW_5V')."""
        if n in self.full or n in ('','#KEEPOUT'): return n
        c=[k for k in self.full if k.split('/')[-1]==n]
        assert len(c)==1,('net name not unique or unknown',n,c); return c[0]
    def pad(self,ref,num,k=0):
        ps=[p for p in self.R[ref].pads if p.num==num]; p=ps[k]; return (p.x,p.y)
    def padnet(self,ref,num): return [p for p in self.R[ref].pads if p.num==num][0].net
    def shift(self,ref,x,y):
        """Plan a pure translation of a footprint to (x,y)."""
        f=self.R[ref]; dx,dy=x-f.x,y-f.y
        for p in f.pads:
            p.x+=dx; p.y+=dy; p.box=[(q[0]+dx,q[1]+dy) for q in p.box]
        f.x,f.y=x,y; self.plan['move'].append(dict(ref=ref,x=x,y=y)); self.refresh(ref)
    def place2(self,ref,x,y,num,at,bottom=False):
        """Plan a two-pad part: centre (x,y), pad `num` at point `at`, the other pad opposite; optional flip to the bottom."""
        f=self.R[ref]; ux,uy=at[0]-x,at[1]-y; l=math.hypot(ux,uy); ux,uy=ux/l,uy/l
        for p in f.pads:
            rel=(p.rot-f.rot)%180; a_len,c_len=(p.w,p.h) if (rel<1 or rel>179) else (p.h,p.w)
            s=1 if p.num==num else -1; p.x,p.y=x+s*ux*l,y+s*uy*l
            p.box=[(p.x+ux*ca*a_len/2-uy*cc*c_len/2,p.y+uy*ca*a_len/2+ux*cc*c_len/2) for ca,cc in ((-1,-1),(1,-1),(1,1),(-1,1))]
            if bottom: p.layers=[q.replace('F.','B.') for q in p.layers]
            else: p.layers=[q.replace('B.','F.') for q in p.layers]
        f.x,f.y=x,y
        f.layer='B.Cu' if bottom else 'F.Cu'
        self.plan['place'].append(dict(ref=ref,x=x,y=y,pad=num,px=at[0],py=at[1],bottom=bottom)); self.refresh(ref)
    def add_track(self,net,layer,w,pts):
        net=self.canon(net)
        pts=clean([tuple(p) for p in pts])
        for a,c in zip(pts,pts[1:]):
            self.obs.append(dict(k='s',p=(a[0],a[1],c[0],c[1]),r=w/2,net=net,lay={layer},ref='new'))
        self.plan['tracks'].append(dict(net=self.full[net],layer=layer,w=w,pts=[[round(x,4),round(y,4)] for x,y in pts])); return pts
    def add_via(self,net,x,y,check=True,d=0.55,drill=0.25):
        net=self.canon(net)
        if check:
            m=self.via_margin(net,x,y,r=d/2)
            if m[0]<-1e-3: print('  !! via',net,(x,y),'margin',round(m[0],3),'against',m[1])
        self.obs.append(dict(k='c',x=x,y=y,r=d/2,net=net,lay=None,ref='newvia',hole=drill/2))
        self.plan['vias'].append(dict(net=self.full[net],x=round(x,4),y=round(y,4),d=d,drill=drill)); return (x,y)
    def add_zone(self,name,net,layer,pts,priority=20,keepout=False,allow=()):
        """Plan a copper pour, or (keepout=True) a one-layer rule area with no tracks, vias or pours;
        allow may name 'vias' and/or 'pours' to permit them inside the rule area."""
        net=self.canon(net)
        self.plan.setdefault('zones',[]).append(dict(name=name,net='' if keepout else self.full[net],layer=layer,pts=[[x,y] for x,y in pts],priority=priority,keepout=keepout,allow=list(allow)))
        if not (keepout and 'tracks' in allow):
            self.zones.append(dict(k='p',pts=[tuple(p) for p in pts],net='#KEEPOUT' if keepout else net,lay={layer},ref='zone:'+name))
    def drop_zone(self,name):
        """Plan the removal of an existing zone (outline and fill), given by its name."""
        n=len(self.zones); self.zones=[z for z in self.zones if z['ref']!='zone:'+name]
        if len(self.zones)!=n-1: print('  !! drop_zone matched',n-len(self.zones),'zones for',name)
        self.plan.setdefault('drop_zones',[]).append(name)
    def drop_via(self,x,y,tol=0.02):
        """Plan the removal of one existing via at (x, y)."""
        n=len(self.obs); self.obs=[o for o in self.obs if not (o['ref']=='via' and math.hypot(o['x']-x,o['y']-y)<tol)]
        if len(self.obs)!=n-1: print('  !! drop_via matched',n-len(self.obs),'vias at',(x,y))
        self.plan.setdefault('drop_vias',[]).append([x,y])
    def drop_net(self,suffix):
        self.plan['drop_nets'].append(suffix); self.obs=[o for o in self.obs if not (o['ref']=='trk' and o['net'].endswith(suffix))]
    def drop_seg(self,a,b,tol=0.02):
        """Plan the removal of one existing track segment, given by its end points."""
        def hit(o):
            if o['ref']!='trk' or o['k']!='s': return False
            p=o['p']; e1,e2=(p[0],p[1]),(p[2],p[3])
            return (math.dist(e1,a)<tol and math.dist(e2,b)<tol) or (math.dist(e1,b)<tol and math.dist(e2,a)<tol)
        n=len(self.obs); self.obs=[o for o in self.obs if not hit(o)]
        if len(self.obs)!=n-1: print('  !! drop_seg matched',n-len(self.obs),'segments for',a,b)
        self.plan['drop_segs'].append([a[0],a[1],b[0],b[1]])
    def save(self,out): json.dump(self.plan,open(out,'w'),indent=0); print('plan:',{k:len(v) for k,v in self.plan.items() if k!='marks'})
    # ---------------------------------------------------------------- distance queries
    def _dist(self,o,X,Y):
        if o['k']=='c': return np.hypot(X-o['x'],Y-o['y'])-o['r']
        if o['k']=='s':
            ax,ay,bx,by=o['p']; dx,dy=bx-ax,by-ay; L=dx*dx+dy*dy
            t=np.zeros_like(X) if L==0 else np.clip(((X-ax)*dx+(Y-ay)*dy)/L,0,1)
            return np.hypot(X-(ax+t*dx),Y-(ay+t*dy))-o['r']
        d=np.full(X.shape,1e9); ins=np.zeros(X.shape,bool)
        for pts in o.get('rings',[o['pts']]):                  # even-odd over outline and holes
            n=len(pts)
            for k in range(n):
                ax,ay=pts[k]; bx,by=pts[(k+1)%n]; dx,dy=bx-ax,by-ay; L=dx*dx+dy*dy
                t=np.zeros_like(X) if L==0 else np.clip(((X-ax)*dx+(Y-ay)*dy)/L,0,1)
                d=np.minimum(d,np.hypot(X-(ax+t*dx),Y-(ay+t*dy)))
                if ay!=by:
                    c=((ay>Y)!=(by>Y))&(X<(bx-ax)*(Y-ay)/(by-ay)+ax); ins^=c
        return np.where(ins,-d,d)
    def _need(self,o,net,layer,pad_to_pad=False):
        """clearance this obstacle demands from copper of `net` on `layer` (None: not an obstacle)."""
        if o['lay'] is not None and layer not in o['lay']: return None
        if o['net']=='#KEEPOUT': return 0.0
        if o['net']==net and net!='': return None
        if o.get('npth'): return 0.3
        c=clearance(o['net'],net)
        r=o['ref']
        if c>0.2 and (r.startswith('NT') or r.startswith('U6.') or r.startswith('U2.')): c=0.2
        return c
    def blocked(self,net,layer,hw,x0,y0,nx,ny,g,allow=(),eps=0.05,extra=()):
        X=x0+g*np.arange(nx)[None,:]+np.zeros((ny,1)); Y=y0+g*np.arange(ny)[:,None]+np.zeros((1,nx))
        B=(np.hypot(X-CX,Y-CY)>RB-EDGE-hw-eps)
        x1,y1=x0+g*(nx-1),y0+g*(ny-1)
        inner=max(math.hypot(x-CX,y-CY) for x in (x0,x1) for y in (y0,y1))<41.0    # window clear of the CHASSIS ring band
        for o in self.obs+self.zones+list(extra):
            if o['ref'] in allow: continue
            if inner and len(o.get('rings',()))>1 and o['net']=='CHASSIS': continue
            c=self._need(o,net,layer)
            if c is None: continue
            m=c+hw+eps
            if o['k']=='c': bb=(o['x']-o['r'],o['y']-o['r'],o['x']+o['r'],o['y']+o['r'])
            elif o['k']=='s': bb=(min(o['p'][0],o['p'][2])-o['r'],min(o['p'][1],o['p'][3])-o['r'],max(o['p'][0],o['p'][2])+o['r'],max(o['p'][1],o['p'][3])+o['r'])
            else: xs=[p[0] for p in o['pts']]; ys=[p[1] for p in o['pts']]; bb=(min(xs),min(ys),max(xs),max(ys))
            if bb[2]+m<x0 or bb[0]-m>x1 or bb[3]+m<y0 or bb[1]-m>y1: continue
            i0=max(0,int((bb[0]-m-x0)/g)); i1=min(nx,int((bb[2]+m-x0)/g)+2); j0=max(0,int((bb[1]-m-y0)/g)); j1=min(ny,int((bb[3]+m-y0)/g)+2)
            if i0>=i1 or j0>=j1: continue
            B[j0:j1,i0:i1]|=(self._dist(o,X[j0:j1,i0:i1],Y[j0:j1,i0:i1])<m)
        return B
    def _bbox(self,o):
        b=o.get('_bb')
        if b is None:
            if o['k']=='c': b=(o['x']-o['r'],o['y']-o['r'],o['x']+o['r'],o['y']+o['r'])
            elif o['k']=='s': b=(min(o['p'][0],o['p'][2])-o['r'],min(o['p'][1],o['p'][3])-o['r'],max(o['p'][0],o['p'][2])+o['r'],max(o['p'][1],o['p'][3])+o['r'])
            else: xs=[q[0] for q in o['pts']]; ys=[q[1] for q in o['pts']]; b=(min(xs),min(ys),max(xs),max(ys))
            o['_bb']=b
        return b
    def margin(self,net,layer,hw,pts,allow=()):
        net=self.canon(net)
        """smallest (distance - required clearance) of a polyline of half-width hw; (value, culprit)."""
        best=(9.0,None); P=[]
        for a,c in zip(pts,pts[1:]):
            n=max(1,int(math.dist(a,c)/0.04)); P+=[(a[0]+(c[0]-a[0])*k/n,a[1]+(c[1]-a[1])*k/n) for k in range(n+1)]
        X=np.array([p[0] for p in P]); Y=np.array([p[1] for p in P])
        e=RB-EDGE-hw-float(np.max(np.hypot(X-CX,Y-CY)))
        if e<best[0]: best=(e,'board edge')
        inner=float(np.max(np.hypot(X-CX,Y-CY)))<41.0           # polyline clear of the CHASSIS ring band
        lx0,ly0,lx1,ly1=float(X.min())-2.5,float(Y.min())-2.5,float(X.max())+2.5,float(Y.max())+2.5
        for o in self.obs+self.zones:
            if o['ref'] in allow: continue
            bb=self._bbox(o)
            if bb[2]<lx0 or bb[0]>lx1 or bb[3]<ly0 or bb[1]>ly1: continue   # far away: cannot set the minimum
            if inner and len(o.get('rings',()))>1 and o['net']=='CHASSIS': continue
            c=self._need(o,net,layer)
            if c is None: continue
            v=float(np.min(self._dist(o,X,Y)))-c-hw
            if v<best[0]: best=(v,o['ref']+' '+o['net'])
        return best
    def via_margin(self,net,x,y,r=0.275):
        net=self.canon(net)
        best=(9.0,None)
        for layer in ('F.Cu','B.Cu'):
            m=self.margin(net,layer,r,[(x,y),(x,y)],allow=tuple(z['ref'] for z in self.zones))
            if m[0]<best[0]: best=(m[0],layer+' '+str(m[1]))
        for o in self.obs:                                   # drill to drill
            if 'hole' in o:
                hx,hy=o.get('hx',o.get('x')),o.get('hy',o.get('y'))
                if hx is None: continue
                need=0.254 if o['net']==net else 0.5
                v=math.hypot(hx-x,hy-y)-o['hole']-0.125-need
                if v<best[0]: best=(v,'hole '+o['ref'])
        return best
    # ---------------------------------------------------------------- router
    def route(self,net,layer,w,start,end,g=0.05,d0=None,d0_len=0.0,allow=(),pad_end=0.0,bend=1.2,margin_mm=3.0,box=None,eps=0.05,quiet=False):
        """A* on a grid anchored at `start` (exact). Ends at the grid node nearest `end` (within pad_end, default one cell),
        then joins `end` exactly with a straight+45 link. d0: forced initial direction vector for d0_len mm."""
        net=self.canon(net)
        hw=w/2; sx,sy=start; ex,ey=end
        if box is None: box=(min(sx,ex)-margin_mm,min(sy,ey)-margin_mm,max(sx,ex)+margin_mm,max(sy,ey)+margin_mm)
        i_off=int(math.ceil((sx-box[0])/g)); j_off=int(math.ceil((sy-box[1])/g)); x0=sx-i_off*g; y0=sy-j_off*g
        nx=int((box[2]-x0)/g)+1; ny=int((box[3]-y0)/g)+1
        B=self.blocked(net,layer,hw,x0,y0,nx,ny,g,allow=allow,eps=eps)
        ti=int(round((ex-x0)/g)); tj=int(round((ey-y0)/g)); tol=int(round(pad_end/g))
        si,sj=i_off,j_off; B[sj,si]=False
        INF=1e18; best={}; pq=[]
        if d0 is not None:
            d=dir_of(d0); steps=max(1,int(round(d0_len/(g*math.hypot(*DIRS[d])))))
            i,j=si,sj; cost=0.0
            for _ in range(steps): i+=DIRS[d][0]; j+=DIRS[d][1]; cost+=g*math.hypot(*DIRS[d])
            starts=[(cost,i,j,d,(si,sj,d))]
        else: starts=[(0.0,si,sj,d,None) for d in range(8)]
        def h(i,j):
            dx,dy=abs(i-ti),abs(j-tj); return g*(max(dx,dy)+0.41421356*min(dx,dy))
        prev={}
        for c,i,j,d,p in starts:
            best[(i,j,d)]=c; prev[(i,j,d)]=p; heapq.heappush(pq,(c+h(i,j),c,i,j,d))
        goal=None; pops=0
        while pq:
            f,c,i,j,d=heapq.heappop(pq)
            if best.get((i,j,d),INF)<c-1e-9: continue
            pops+=1
            if max(abs(i-ti),abs(j-tj))<=tol: goal=(i,j,d); break
            for dd,pen in ((0,0.0),(1,bend),(-1,bend)):
                nd=(d+dd)%8; di,dj=DIRS[nd]; ni,nj=i+di,j+dj
                if ni<0 or nj<0 or ni>=nx or nj>=ny or B[nj,ni]: continue
                nc=c+g*math.hypot(di,dj)+pen
                if nc<best.get((ni,nj,nd),INF)-1e-9:
                    best[(ni,nj,nd)]=nc; prev[(ni,nj,nd)]=(i,j,d); heapq.heappush(pq,(nc+h(ni,nj),nc,ni,nj,nd))
            if pops>2500000: break
        if goal is None:
            print('  !! no route',net,layer,start,end,'pops',pops); return None
        path=[]; s=goal
        while s is not None: path.append((x0+s[0]*g,y0+s[1]*g)); s=prev.get(s)
        path.reverse()
        if pad_end==0 and math.dist(path[-1],end)>1e-6:
            # back off a little and join the exact end point with a straight + 45-degree link (no micro segments)
            done=False
            for back in (0.6,0.3,0.0):
                k=len(path)-1
                while k>0 and math.dist(path[k],end)<back: k-=1
                for df in (False,True):
                    tail=link(path[k],end,df)
                    if self.margin(net,layer,hw,tail,allow)[0]>-0.045:
                        path=path[:k+1]+tail[1:]; done=True; break
                if done: break
            if not done: path=path+link(path[-1],end)[1:]
        path=clean(path)
        if not quiet:
            m=self.margin(net,layer,hw,path,allow); print('  route',net.ljust(6),layer,'len',round(sum(math.dist(a,c) for a,c in zip(path,path[1:])),1),'pts',len(path),'margin',round(m[0],3),m[1])
        return path
def rot_inv(x,y,deg):
    a=math.radians(deg); return x*math.cos(a)-y*math.sin(a), x*math.sin(a)+y*math.cos(a)
