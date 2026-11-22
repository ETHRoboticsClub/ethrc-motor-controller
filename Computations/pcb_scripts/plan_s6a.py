"""Step 6, slice A (2026-11-22): U1 <-> DRV8353 (U6) control and SPI, MGH/MGL to the encoder (U7). Runs on the board
after plan_s6_prep.py. Approved: DRV_CS on PB3; test points TP1-TP10/TP35 and pull-ups R16/R17 re-placed on their own
routes; C113 at (150.7, 96.9); DRV SPI SCLK/MOSI/CS on L3 inside the encoder keepout circle (tracks at r <= 4.3 mm, where
L4 has no copper), MISO on L6.
Frames: U6 south-east face gse(s,d) from pin 31, south-west face ax(pin,t,off); U1 south-west face f1(k,d), k = pin number.
usage: plan_s6a.py board.kicad_pcb plan.json"""
import sys,os,math
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from route import *
from route2 import route2,add_route2
F,B,L3,L4='F.Cu','B.Cu','In2.Cu','In3.Cu'; R2=1/math.sqrt(2); WP=0.2
W=World(sys.argv[1]); P=W.pad
ZA=lambda: tuple(z['ref'] for z in W.zones)
warn=[]; lock=[]
PARK=['TP1','TP2','TP3','TP4','TP5','TP6','TP7','TP8','TP9','TP10','TP35','R16','R17']
for r in PARK: W.obs=[o for o in W.obs if not o['ref'].startswith(r+'.')]   # placed on their routes at the end
def vmargin(net,x,y,r=0.275):
    m=W.via_margin(net,x,y,r)
    for lay in (L3,L4):
        m2=W.margin(net,lay,r,[(x,y),(x,y)],allow=ZA())
        if m2[0]<m[0]: m=(m2[0],lay+' '+str(m2[1]))
    return m
def T(net,layer,w,pts,tag=''):
    pts=clean([tuple(p) for p in pts]); m=W.margin(net,layer,w/2,pts,allow=ZA() if layer in (L3,L4) else ())
    if m[0]<-0.005: warn.append(tag or net); print('  !! %-16s %s margin %.3f %s'%(tag or net,layer,m[0],m[1]))
    return W.add_track(net,layer,w,pts)
def V(net,p,tag=''):
    m=vmargin(net,*p)
    if m[0]<-0.005: warn.append(tag or net); print('  !! via %-12s %s margin %.3f %s'%(tag or net,tuple(round(v,2) for v in p),m[0],m[1]))
    return W.add_via(net,p[0],p[1],check=False)
def RT(net,layer,w,a,b,**kw):
    pts=W.route(net,layer,w,a,b,quiet=True,**kw)
    if not pts: warn.append(net+' route'); print('  !! no route',net,layer,a,b); return None
    return T(net,layer,w,pts,net+' routed '+layer)
def R3(net,a,b,box,**kw):                               # multi-layer route (L1/L3/L6); a,b = (layer,(x,y))
    r=route2(W,net,WP,a,b,box,**kw)
    if not r: warn.append(net+' route2'); return None
    for L,p in r['segs']: T(net,L,WP,p,net+' r2 '+L)
    for v in r['vias']: V(net,v,net+' r2 via')
    return r
def gnd_near(pts,n=1,reach=1.4,lo=0.75):
    cx,cy=sum(p[0] for p in pts)/len(pts),sum(p[1] for p in pts)/len(pts); got=0
    for d,x,y in sorted(((math.hypot(0.05*i,0.05*j),round(cx+0.05*i,3),round(cy+0.05*j,3)) for i in range(-40,41) for j in range(-40,41))):
        if min(math.hypot(x-p[0],y-p[1]) for p in pts)>reach or min(math.hypot(x-p[0],y-p[1]) for p in pts)<lo: continue
        if vmargin('GND',x,y)[0]<0.03: continue
        W.add_via('GND',x,y,check=False); got+=1
        if got==n: return (x,y)
    warn.append('gnd near %s'%(pts[0],)); print('  !! GND via missing near',pts[0])
p31=P('U6','31'); gse=lambda s,d:(round(p31[0]+R2*(s+d),4),round(p31[1]+R2*(-s+d),4))
ax=lambda pin,t,off=0.0:(round(P('U6',pin)[0]-R2*t+R2*off,4),round(P('U6',pin)[1]+R2*t+R2*off,4))
p1=P('U1','1'); f1=lambda k,d:(round(p1[0]+R2*(0.5*(k-1)-d),4),round(p1[1]+R2*(0.5*(k-1)+d),4))
def on_axis_se(e,x):                                     # point on the SE-face pin axis through pad end e, at abscissa x
    return (round(x,4),round(e[1]+(x-e[0]),4))
# ======================================================= 1. encoder U7: C113 (moved in the prep plan) to U7's +3V3 pin 13
c113=[p for p in W.R['C113'].pads if p.num=='1'][0]
T('+3V3',B,0.25,[(c113.x,c113.y),(c113.x,97.8),(149.45,97.8),(149.25,98.0),P('U7','13')],'C113 to U7.13')
# ======================================================= 2. DRV SPI landing row at U6's south-west face (one row, depth 0.9)
LAND={'DRV_MISO':('27',-0.42),'DRV_MOSI':('28',-0.14),'DRV_SCLK':('29',0.14),'DRV_CS':('30',0.42)}
vland={}
for n,(pin,off) in LAND.items():
    v=ax(pin,1.1 if n=='DRV_MISO' else 1.05,off); vland[n]=v; V(n,v,n+' landing')
    j0=0.45 if abs(off)>0.3 else 0.6                       # outer stubs jog early, inner ones late, so neighbours stay 0.5 apart
    T(n,F,WP,[ax(pin,0.3),ax(pin,j0),ax(pin,j0+abs(off),off),v],n+' landing stub')
# ======================================================= 3. control lines at U6's south-east face: fan, HIZ vias, L6 tie
E={k:gse(0.5*(k-31),0.3) for k in range(31,38)}
LANE={'PWM_PHASEA':151.75,'PWM_PHASEB':152.15,'PWM_PHASEC':152.55,'MOTOR_HIZ':152.95}
YS=101.2                                                  # the lanes continue south from here (step 4 of this plan)
LS={'PWM_PHASEA':151.45,'PWM_PHASEB':151.85,'PWM_PHASEC':152.25,'MOTOR_HIZ':152.65}   # lanes through the C130..C1 passage
T('PWM_PHASEA',F,WP,[E[32],on_axis_se(E[32],151.75),(151.75,98.68),(151.45,98.98),(151.45,YS)],'PWMA fan')
v33=(152.4,97.6); T('MOTOR_HIZ',F,WP,[E[33],on_axis_se(E[33],152.4),v33],'HIZ33 stub'); V('MOTOR_HIZ',v33,'HIZ33 via')
T('PWM_PHASEB',F,WP,[E[34],on_axis_se(E[34],153.0),(153.0,98.0),(151.85,99.15),(151.85,YS)],'PWMB fan')
v35=(153.65,97.5); T('MOTOR_HIZ',F,WP,[E[35],on_axis_se(E[35],153.65),v35],'HIZ35 stub'); V('MOTOR_HIZ',v35,'HIZ35 via')
T('PWM_PHASEC',F,WP,[E[36],on_axis_se(E[36],154.4),(154.4,97.9),(152.25,100.05),(152.25,YS)],'PWMC fan')
W.drop_via(154.5,96.1)                                    # unconnected stitching via on HIZ37's axis; one goes back nearby
T('MOTOR_HIZ',F,WP,[E[37],on_axis_se(E[37],154.95),(154.95,98.4),(152.65,100.7),(152.65,YS)],'HIZ37 fan')
v37=(154.4,98.95); V('MOTOR_HIZ',v37,'HIZ main via')         # on HIZ37's diagonal, 0.74 mm from PWMC
T('MOTOR_HIZ',B,WP,[v33,(152.5,97.5),(153.6,97.5),v35,(153.65,98.2),v37],'HIZ tie L6')
# ENABLE: lane x 150.2 from the south, 45 degrees into pin 31's end
T('MOTOR_ENABLE',F,WP,[(150.2,YS),(150.2,round(E[31][1]+(E[31][0]-150.2),4)),E[31]],'ENABLE into pin 31')
# ======================================================= 4. U1 south-west face: the wrap (PWMA/B/C, HIZ) on L1 into the lanes
a_=lambda k:0.5*(k-1)                                       # along-face mm of pin k in the f1 frame
F1=lambda a,d:f1(1+2*a,d)
def wrap(net,k,dout,dw,dcor,ac,turn,lane,yj,aoff=0.0,w=WP):
    """pad end -> out to dout -> W-diagonal to dw -> NW at dw -> N-diagonal (from along ac) to dcor -> NW to the turn point
    (real x = turn) -> north -> 45-degree jog west at y=yj onto the lane -> north to YS"""
    a=a_(k); pts=[F1(a,0.6)]
    if aoff: pts+=[F1(a,0.8),F1(a+aoff,0.8+abs(aoff))]; a+=aoff        # step sideways off a neighbouring part
    if dw>dout: pts+=[F1(a,dout),F1(a-(dw-dout),dw)]
    else: pts+=[F1(a,dw)]
    if dcor<dw: pts+=[F1(ac,dw),F1(ac-(dw-dcor),dcor)]
    at=(turn-p1[0])/R2+dcor                                   # along where the NW run at dcor reaches real x = turn
    t=F1(at,dcor); pts+=[t,(t[0],yj),(lane,round(yj-(t[0]-lane),4)),(lane,YS)]
    T(net,F,w,pts,net+' wrap')
wrap('PWM_PHASEA',14,3.6,4.0,3.18,3.0,152.18,151.45,107.4,aoff=-0.05)
wrap('PWM_PHASEB',13,3.2,3.6,2.78,3.2,152.58,151.85,107.234)
wrap('PWM_PHASEC',12,2.8,3.2,2.38,3.4,152.98,152.25,107.068)
wrap('MOTOR_HIZ',4,1.98,1.98,1.98,0,153.38,152.65,106.902)
# ======================================================= 5. U6 pin 25 (GND) into the exposed pad, FAULT leaves pin 26 along pin 25's axis
T('GND',F,WP,[P('U6','25'),ax('25',-0.75)],'U6.25 to EP')
fault_u6=ax('25',1.3)
T('MOTOR_FAULT',F,WP,[ax('26',0.3),ax('26',0.34),ax('25',0.838),fault_u6],'FAULT at U6')   # between U6.25's end and the MISO via
# NRST keeps the strip inside U1's south-west pin row (slice B): reserve it
for a,b in ((F1(a_(7),-0.6),F1(a_(7),-0.95)),(F1(a_(7),-0.95),F1(a_(17.3),-0.95))):
    W.obs.append(dict(k='s',p=(a[0],a[1],b[0],b[1]),r=0.1,net='NRST',lay={F},ref='reserve'))
# ======================================================= 6. FAULT and ENABLE: U1 face -> L6 under the west corner -> L1 west of the lanes
vF=F1(2.15,1.2); vE=F1(0.9,1.2)                              # face vias (inside the PWM wrap, outside HIZ for FAULT)
T('MOTOR_FAULT',F,WP,[F1(a_(8),0.6),F1(a_(8),0.9),F1(a_(8)-0.3,1.2),vF],'FAULT to its face via'); V('MOTOR_FAULT',vF,'FAULT face via')
T('MOTOR_ENABLE',F,WP,[F1(a_(3),0.6),F1(a_(3),0.75),F1(0.9,0.85),vE],'ENABLE to its face via'); V('MOTOR_ENABLE',vE,'ENABLE face via')
rF=(149.35,104.6); rE=(150.55,104.65); V('MOTOR_FAULT',rF,'FAULT room via'); V('MOTOR_ENABLE',rE,'ENABLE room via')
for n,a0,b0 in (('MOTOR_ENABLE',vE,rE),('MOTOR_FAULT',vF,rF)):
    RT(n,B,WP,a0,b0,box=(147.5,103.6,158.5,113.5))
RT('MOTOR_ENABLE',F,WP,rE,(150.2,YS),box=(148.5,100.5,151.3,105.5))
fw=ax('25',1.6); RT('MOTOR_FAULT',F,WP,rF,(fw[0],97.3),box=(144.8,96.5,150.2,105.2))
T('MOTOR_FAULT',F,WP,[(fw[0],97.3),fw,fault_u6],'FAULT tail west of the MISO via')
# ======================================================= 7. DRV SPI: U1 north-west face -> R1/R2 -> L3 inside the encoder circle -> U6
p49=P('U1','49'); f49=lambda u,v:(round(p49[0]+R2*(-u-v),4),round(p49[1]+R2*(u-v),4))   # U1 NW face, u along pins 49->64, v outwards
def rpad(ref,num): return [(p.x,p.y) for p in W.R[ref].pads if p.num==num][0]
T('DRV_SCLK_MCU',F,WP,[f49(1.5,0.0),rpad('R1','2')],'SCLK_MCU into R1')
T('DRV_MOSI_MCU',F,WP,[f49(2.5,0.0),rpad('R2','2')],'MOSI_MCU into R2')
SPI_SRC={'DRV_SCLK':rpad('R1','1'),'DRV_MOSI':rpad('R2','1'),'DRV_CS':f49(3.5,0.6)}
BOXS=(146.5,94.5,161.0,103.0)
# MISO and MOSI on L6: parallel lanes around U6's thermal pad (SE edge x+y=245.52, SW edge x-y=54.1), MISO inside
def lane(o):
    se=245.52+o*math.sqrt(2); sw=54.1-o*math.sqrt(2); return se,sw,((se+sw)/2,(se-sw)/2)
def land_tail(n,o,cin,yw,h=0.3):
    """Line arriving heading NW along x-y=cin turns onto the SE-edge lane at offset o, runs round U6's south corner
    (45-degree chamfer of half-length h), up the SW-edge lane, then west at y=yw and south-west into its landing via.
    Every bend is 45 degrees. Returns (A* target, explicit tail)."""
    se,sw,c=lane(o); v=vland[n]; s_v=v[0]+v[1]; k=h/math.sqrt(2)
    K=((se+cin)/2,(se-cin)/2); p0=(K[0]+0.3,K[1]+0.3); p1=(K[0]-0.3,K[1]+0.3)
    c1=(c[0]+k,c[1]-k); c2=(c[0]-k,c[1]-k)
    q1=(yw+sw,yw); q2=(s_v-yw,yw)
    r=lambda q:(round(q[0],4),round(q[1],4))
    return r(p0),[r(p0),r(p1),r(c1),r(c2),r(q1),r(q2),v]
vMO=(156.6,100.05); T('DRV_MOSI',F,WP,[SPI_SRC['DRV_MOSI'],(156.6,99.81),vMO],'MOSI to its via'); V('DRV_MOSI',vMO,'MOSI via')
q6=(155.75,99.55)                                              # TP6 (MOSI) on the bottom, next to MOSI's via
f6=W.R['TP6']
for p in f6.pads: p.layers=[l.replace('F.','B.') for l in p.layers]
W.plan['place'].append(dict(ref='TP6',x=q6[0],y=q6[1],pad='1',px=q6[0],py=q6[1],bottom=True))
for p in f6.pads: p.x,p.y=q6; p.box=[(q6[0]+(b[0]-f6.x),q6[1]+(b[1]-f6.y)) for b in p.box]
f6.x,f6.y=q6; W.refresh('TP6'); print('  TP6 margin',W.margin(W.canon('DRV_MOSI'),B,0.25,[q6,q6]))
vMI=f49(2.0,-1.05); T('DRV_MISO',F,WP,[f49(2.0,0.0),vMI],'MISO inboard'); V('DRV_MISO',vMI,'MISO inboard via')
gMI,tMI=land_tail('DRV_MISO',0.4,58.6,95.1); RT('DRV_MISO',B,WP,vMI,gMI,box=(150.0,92.5,161.8,103.0)); T('DRV_MISO',B,WP,tMI,'MISO round U6')
gMO,tMO=land_tail('DRV_MOSI',0.8,57.9,95.85); T('DRV_MOSI',B,WP,[vMO,(156.1,100.05),q6],'MOSI via to TP6'); RT('DRV_MOSI',B,WP,q6,gMO,box=(150.0,92.5,159.5,101.8)); T('DRV_MOSI',B,WP,tMO,'MOSI round U6')
for n in ('DRV_SCLK','DRV_CS'):                              # L1 -> L3 inside the encoder circle -> landing via
    r=R3(n,(F,SPI_SRC[n]),(L3,vland[n]),BOXS,layers=(F,L3),via_cost=4.0)
    print('  %-10s'%n,'ok' if r else 'FAILED',r and r['vias'])
# ======================================================= 8. FAN_CTRL, BOOT0
vFA=f49(3.0,-1.05); T('FAN_CTRL',F,WP,[f49(3.0,0.0),vFA],'FAN inboard'); V('FAN_CTRL',vFA,'FAN via')     # TP35 goes on the bottom
T('BOOT0',F,WP,[f49(6.0,0.0),f49(6.0,0.95),f49(5.29,1.66),rpad('R77','1')],'BOOT0 to R77')
# ======================================================= 9. test points and pull-ups on their own tracks
def net_tracks(net,layer):
    full=W.full[W.canon(net)]
    return [t['pts'] for t in W.plan['tracks'] if t['net']==full and t['layer']==layer]
def samples(polys,step=0.05):
    for pts in polys:
        for a,c in zip(pts,pts[1:]):
            L=math.dist(a,c); n=max(1,int(L/step))
            for i in range(n+1): yield (a[0]+(c[0]-a[0])*i/n,a[1]+(c[1]-a[1])*i/n)
def place_tp(ref,net,layer,near,bottom=False,keep=0.02):
    """Put a 0.5 mm test pad on the net's own track (layer), nearest to `near`, with clearance to everything else."""
    best=None
    holes=[(o['x'],o['y']) for o in W.obs if o['k']=='c' and o['ref'] in ('via','newvia')]
    pads=[(p.x,p.y) for f in W.fps if f.ref!=ref for p in f.pads if (layer if not bottom else B) in p.layers or '*.Cu' in p.layers]
    for q in samples(net_tracks(net,layer)):
        m=W.margin(W.canon(net),layer,0.25,[q,q])[0]
        if m<keep: continue
        if any(math.dist(q,h)<0.7 for h in holes) or any(math.dist(q,c)<0.75 for c in pads): continue   # never on a via or another pad
        d=math.dist(q,near)
        if best is None or d<best[0]: best=(d,q)
    if not best: warn.append('TP '+ref); print('  !! no spot for',ref); return None
    q=(round(best[1][0],4),round(best[1][1],4)); f=W.R[ref]
    if bottom:
        for p in f.pads: p.layers=[l.replace('F.','B.') for l in p.layers]
        W.plan['place'].append(dict(ref=ref,x=q[0],y=q[1],pad='1',px=q[0],py=q[1],bottom=True))
        dx,dy=q[0]-f.x,q[1]-f.y
        for p in f.pads: p.x+=dx; p.y+=dy; p.box=[(b[0]+dx,b[1]+dy) for b in p.box]
        f.x,f.y=q; W.refresh(ref)
    else: W.shift(ref,*q)
    print('  %-5s on %-12s %s at %s (%.1f mm from %s)'%(ref,net,layer,q,best[0],tuple(round(v,1) for v in near))); return q
def place_pullup(ref,net,near,keep=0.03):
    """Two-pad pull-up on the bottom: signal pad (2) on the net's own L6 track, +3V3 pad (1) beside it."""
    f=W.R[ref]; sig=[p for p in f.pads if p.net==W.canon(net)][0]; oth=[p for p in f.pads if p is not sig][0]
    pitch=math.dist((sig.x,sig.y),(oth.x,oth.y)); best=None
    for q in samples(net_tracks(net,B),0.1):
        for k in range(8):
            a=math.radians(45*k); c=(q[0]+0.5*pitch*math.cos(a),q[1]+0.5*pitch*math.sin(a))
            W.place2(ref,c[0],c[1],sig.num,q,bottom=True); W.plan['place'].pop()
            pp=[p for p in W.R[ref].pads if p.num==oth.num][0]
            m=W.margin(pp.net,B,0.0,pp.box+[pp.box[0]])[0]
            if m<keep: continue
            d=math.dist(q,near)
            if best is None or d<best[0]: best=(d,c,q)
    if not best: warn.append('pull-up '+ref); print('  !! no spot for',ref); return None
    W.place2(ref,round(best[1][0],4),round(best[1][1],4),sig.num,best[2],bottom=True)
    print('  %-5s on %-12s L6 at %s (%.1f mm from %s)'%(ref,net,tuple(round(v,3) for v in best[1]),best[0],tuple(round(v,1) for v in near)))
for ref,net,near in (('TP1','MOTOR_ENABLE',(150.85,97.52)),('TP2','MOTOR_HIZ',(155.87,110.17)),('TP3','MOTOR_FAULT',(157.28,111.58)),
                     ('TP8','PWM_PHASEA',(151.95,98.17)),('TP9','PWM_PHASEB',(159.1,113.4)),('TP10','PWM_PHASEC',(152.82,95.35)),
                     ('TP4','DRV_SCLK',(158.66,98.31)),('TP7','DRV_CS',(148.88,97.42))):
    place_tp(ref,net,F,near)
place_tp('TP5','DRV_MISO',B,(158.5,100.24),bottom=True)
e35=(round(vFA[0]-0.95,4),round(vFA[1]-0.95,4)); T('FAN_CTRL',B,WP,[vFA,e35],'FAN to TP35'); place_tp('TP35','FAN_CTRL',B,e35,bottom=True)
place_pullup('R17','DRV_MISO',(156.0,98.0))
place_pullup('R16','MOTOR_FAULT',(153.0,106.5))
lock+=['TP1','TP2','TP3','TP4','TP5','TP6','TP7','TP8','TP9','TP10','TP35','R16','R17']
# ======================================================= 10. GND return vias beside every group of signal vias
for grp,reach in (([vland[n] for n in LAND],1.6),([vMO],1.6),([vMI,vFA],1.6),([vF,vE],1.6),([rF,rE],1.6)):          # HIZ tie vias: static enable, no room for a return via in the PWM fan
    gnd_near(grp,n=1,reach=reach)
print('  stitching via replacing (154.5, 96.1):',gnd_near([(154.5,96.1)],n=1,reach=1.3,lo=0.0))
W.plan['lock']=lock
W.save(sys.argv[2]); print('warnings',len(warn),warn)
