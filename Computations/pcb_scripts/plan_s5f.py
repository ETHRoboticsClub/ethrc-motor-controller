"""Step 5, last part (2026-11-22): encoder SPI and SENSE_VBAT, on the board after plan_s5e.
Approved placement changes: R8/R9 to the bottom under U1's south-east face (pins 19/21); R45 turned 180 deg in place.
Topology (frame of U1's SE face: s along pins 17->32 from pin 17, d inwards, both in mm):
- U7 trunk on L6 leaves U1 north-west in the order SCLK, MISO, BRD_CS, MOSI (s 1.0 / 1.9 / 2.8 / 3.6).
- J8 bundle on L6 leaves U1 south-west in the order SCLK, MISO, MOSI, EXT_CS (d 7.0 / 6.2 / 5.4 / 4.6).
  SCLK forks on L6 (it is on the edge of both bundles); MISO forks on its L1 carry; MOSI's J8 branch hops on L1.
- L1 under U1's body (free copper) carries BRD_CS (pin 26), MISO (pin 57), EXT_CS (pin 51) and the MOSI hop.
- SENSE_VBAT: L6 from its inboard via, out through U1's SE face at s 4.4, south past the ADC filters, via to L1 at R44.
usage: plan_s5f.py board.kicad_pcb plan.json"""
import sys,os,math
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from route import *
F,B,L3,L4='F.Cu','B.Cu','In2.Cu','In3.Cu'; R2=1/math.sqrt(2); WP=0.2
W=World(sys.argv[1]); P=W.pad
ZA=lambda: tuple(z['ref'] for z in W.zones)
warn=[]; lock=[]
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
def RS(net,layer,w,a,b,pad=None,**kw):
    pts=RT(net,layer,w,a,b,**kw)
    if pad is not None and pts: T(net,layer,w,[b,pad],net+' into pad')
    return pts
def gnd_near(pts,n=1,reach=1.4):
    cx,cy=sum(p[0] for p in pts)/len(pts),sum(p[1] for p in pts)/len(pts); got=0
    cand=sorted(((math.hypot(0.05*i,0.05*j),round(cx+0.05*i,3),round(cy+0.05*j,3)) for i in range(-40,41) for j in range(-40,41)))
    for d,x,y in cand:
        if min(math.hypot(x-p[0],y-p[1]) for p in pts)>reach: continue
        if vmargin('GND',x,y)[0]<0.03: continue
        W.add_via('GND',x,y,check=False); got+=1
        if got==n: return (x,y)
    warn.append('gnd near %s'%(pts[0],)); print('  !! GND via missing near',pts[0])
def pend(ref,num,d):                                  # point d mm beyond the outer end of a quad-flat / QFN pin
    f=W.R[ref]; px,py=P(ref,num); p=[q for q in f.pads if q.num==num][0]; L=max(p.w,p.h)/2
    a=math.atan2(py-f.y,px-f.x); base=math.radians(f.rot%90); k=round((a-base)/(math.pi/2)); ang=base+k*math.pi/2
    return (round(px+math.cos(ang)*(L+d),4),round(py+math.sin(ang)*(L+d),4))
se0=P('U1','17')
fse=lambda s,d:(round(se0[0]+R2*(s-d),4),round(se0[1]-R2*(s+d),4))
# ================================================================= 1. placement: R45 turned, R8/R9 under U1's SE face
r45_1=P('R45','1'); c45=(W.R['R45'].x,W.R['R45'].y)
W.place2('R45',c45[0],c45[1],'2',r45_1,bottom=True)            # MISO_IC pad to the west, ENC_MISO pad to the east
W.place2('R8',*fse(1.0,2.545),'1',fse(1.0,2.14),bottom=True)   # MCU pad towards the pins, encoder pad inwards
W.place2('R9',*fse(2.0,2.545),'1',fse(2.0,2.14),bottom=True)
lock+=['R45','R8','R9']
# ================================================================= 2. U1 side
v19,v21=fse(1.0,1.25),fse(2.0,1.25)
for net,pn,v,r in (('ENC_SCLK_MCU','19',v19,'R8'),('ENC_MOSI_MCU','21',v21,'R9')):
    V(net,v,net+' via'); T(net,F,WP,[P('U1',pn),v],net+' stub'); T(net,B,WP,[v,P(r,'1')],net+' to '+r)
vB=fse(2.8,4.0)                                                 # BRD_CS: L1 carry from pin 26 to its trunk slot
V('ENC_BRD_CS',vB,'BRD_CS via'); T('ENC_BRD_CS',F,WP,[P('U1','26'),fse(4.5,4.0),vB],'BRD_CS carry')
vMU,vMJ=fse(1.9,6.2),fse(0.3,6.2)                               # MISO: L1 carry from pin 57, fork to both bundles
V('ENC_MISO',vMU,'MISO via U7'); V('ENC_MISO',vMJ,'MISO via J8')
T('ENC_MISO',F,WP,[P('U1','57'),fse(3.5,7.0),fse(2.7,6.2),vMU,vMJ],'MISO carry')
vEJ=fse(0.3,4.6)                                                # EXT_CS: L1 carry from pin 51 below the MOSI hop
V('ENC_EXT_CS',vEJ,'EXT_CS via J8')
T('ENC_EXT_CS',F,WP,[P('U1','51'),fse(6.5,9.8),fse(4.3,9.8),fse(4.3,4.6),vEJ],'EXT_CS carry')
vO1,vOJ=fse(3.6,5.4),fse(0.3,5.4)                               # MOSI: J8 branch hops on L1
V('ENC_MOSI',vO1,'MOSI hop up'); V('ENC_MOSI',vOJ,'MOSI via J8'); T('ENC_MOSI',F,WP,[vO1,vOJ],'MOSI hop')
# trunk lines (L6) out of U1's NW face, J8 lines out of its SW face
D_OUT=12.6; S_OUT=-2.6
trunk={'ENC_SCLK':[P('R8','2'),fse(1.0,D_OUT)],'ENC_MISO':[vMU,fse(1.9,D_OUT)],
       'ENC_BRD_CS':[vB,fse(2.8,D_OUT)],'ENC_MOSI':[P('R9','2'),fse(2.35,3.3),fse(3.6,3.3),fse(3.6,D_OUT)]}
for net,pts in trunk.items(): T(net,B,WP,pts,net+' trunk')
j8={'ENC_SCLK':[fse(1.0,7.0),fse(S_OUT,7.0)],'ENC_MISO':[vMJ,fse(S_OUT,6.2)],
    'ENC_MOSI':[vOJ,fse(S_OUT,5.4)],'ENC_EXT_CS':[vEJ,fse(S_OUT,4.6)]}
for net,pts in j8.items(): T(net,B,WP,pts,net+' J8 start')
for p in (v19,v21): pass
gnd_near([v19,v21]); gnd_near([vB,vO1])
for q in ((0.25,3.7),(0.2,8.0)): V('GND',fse(*q),'GND by the J8 column')   # return vias for the MISO / MOSI / EXT_CS drops
# ================================================================= 3. U7 end (L6): MOSI east side, BRD_CS via TP27, MISO to R45, SCLK around R45
UB=(146.0,96.5,158.5,105.0)
RS('ENC_MOSI',B,WP,trunk['ENC_MOSI'][-1],pend('U7','4',0.25),P('U7','4'),box=UB,bend=0.8)
RS('ENC_BRD_CS',B,WP,trunk['ENC_BRD_CS'][-1],P('TP27','1'),box=UB,bend=0.8); RS('ENC_BRD_CS',B,WP,P('TP27','1'),pend('U7','5',0.25),P('U7','5'),box=UB,bend=0.8)
RS('ENC_MISO_IC',B,WP,pend('U7','7',0.25),P('R45','2'),box=UB,bend=0.8); T('ENC_MISO_IC',B,WP,[P('U7','7'),pend('U7','7',0.25)],'MISO_IC pad')
RS('ENC_MISO',B,WP,trunk['ENC_MISO'][-1],P('R45','1'),box=UB,bend=0.8)
p12=P('U7','12'); e12=pend('U7','12',0.0)                      # up U7's west side, one 45-degree step into pin 12
a12=(round(e12[0]-0.55,4),round(p12[1]+1.1,4))
if RT('ENC_SCLK',B,WP,trunk['ENC_SCLK'][-1],a12,box=(145.5,96.5,158.0,105.6),bend=0.8):
    T('ENC_SCLK',B,WP,[a12,(a12[0],round(p12[1]+0.3,4)),(round(e12[0]-0.25,4),p12[1]),p12],'SCLK into pin 12')
# ================================================================= 4. J8 bundle (L6) south of U9, vias east of D17, L1 into D17 / J8
def free_via(net,near,reach=0.8):
    best=None
    for i in range(-16,17):
        for j in range(-16,17):
            x,y=near[0]+0.05*i,near[1]+0.05*j; d=math.hypot(x-near[0],y-near[1])
            if d>reach or (best and d>=best[0]): continue
            if vmargin(net,x,y)[0]>=0.03: best=(d,(round(x,3),round(y,3)))
    if not best: warn.append('via '+net); print('  !! no via spot',net,near); return near
    return best[1]
# two GND return vias of the U9-south trio (plan_s5e) sat in the bundle's strip: move them north of y 122.95
for q in ((147.73,123.45),(147.18,123.45)): W.drop_via(*q)
trio=[(147.18,121.6),(147.94,122.2),(146.42,122.8)]; got=[]
for d,x,y in sorted((math.hypot(0.05*i,0.05*j),round(147.2+0.05*i,3),round(122.2+0.05*j,3)) for i in range(-40,41) for j in range(-40,41)):
    if y>122.6 or min(math.hypot(x-p[0],y-p[1]) for p in trio)>1.4: continue
    if any(math.hypot(x-g[0],y-g[1])<0.8 for g in got) or vmargin('GND',x,y)[0]<0.03: continue
    W.add_via('GND',x,y,check=False); got.append((x,y))
    if len(got)==2: break
print('  trio GND vias moved to',got)
jv={}
for net,near in (('ENC_SCLK',(128.0,121.3)),('ENC_MISO',(127.55,122.15)),('ENC_MOSI',(127.1,123.0)),('ENC_EXT_CS',(126.8,124.1))):
    jv[net]=free_via(net,near); V(net,jv[net],net+' via D17')
# the strip under U9's south vias holds exactly four lines (y 123.4..124.6, XT60 +VBAT pour below): explicit west run,
# then 45 degrees up to the vias, SCLK (north line) to the east-most via
for k,net in enumerate(('ENC_SCLK','ENC_MISO','ENC_MOSI','ENC_EXT_CS')):
    y=round(123.4+0.4*k,3); wpt=(150.0+0.4*k,y); v=jv[net]
    RS(net,B,WP,j8[net][-1],wpt,box=(148.5,109.0,160.0,125.3),bend=1.0)
    T(net,B,WP,[wpt,(round(v[0]+(y-v[1]),4),y),v],net+' J8 run')
RS('ENC_MISO',B,WP,jv['ENC_MISO'],P('R10','1'),box=(124.0,119.0,129.5,124.0),bend=0.8)
# L1: D17 board-side pins -> test points -> vias; flow-through links; connector-side pins -> J8
JB=(118.5,118.5,129.5,128.0)
RS('ENC_SCLK',F,WP,P('D17','5'),P('TP24','1'),box=JB,bend=0.8); RS('ENC_SCLK',F,WP,P('TP24','1'),jv['ENC_SCLK'],box=JB,bend=0.8)
RS('ENC_MISO',F,WP,P('D17','4'),jv['ENC_MISO'],box=JB,bend=0.8)
RS('ENC_MOSI',F,WP,P('D17','2'),P('TP26','1'),box=JB,bend=0.8); RS('ENC_MOSI',F,WP,P('TP26','1'),jv['ENC_MOSI'],box=JB,bend=0.8)
RS('ENC_EXT_CS',F,WP,P('D17','1'),P('TP28','1'),box=JB,bend=0.8); RS('ENC_EXT_CS',F,WP,P('TP28','1'),jv['ENC_EXT_CS'],box=JB,bend=0.8)
for a,b_ in (('5','6'),('4','7'),('2','9'),('1','10')): T(W.padnet('D17',a),F,WP,[P('D17',a),P('D17',b_)],'D17 flow-through %s-%s'%(a,b_))
RS('ENC_MISO',F,WP,P('D17','7'),P('TP25','1'),box=JB,bend=0.8)
RS('ENC_SCLK',F,WP,P('D17','6'),P('J8','3'),box=JB,bend=0.8)
RS('ENC_MOSI',F,WP,P('D17','9'),P('J8','5'),box=JB,bend=0.8)
RS('ENC_EXT_CS',F,WP,P('D17','10'),P('J8','6'),box=JB,bend=0.8)
n4=W.padnet('J8','4'); v4=free_via(n4,(122.95,124.4),reach=1.0); V(n4,v4,'J8.4 via')
RS(n4,F,WP,P('J8','4'),v4,box=JB,bend=0.8); RS(n4,B,WP,v4,P('R10','2'),box=JB,bend=0.8)
gnd_near([jv['ENC_SCLK'],jv['ENC_MISO']]); gnd_near([jv['ENC_MOSI'],jv['ENC_EXT_CS']]); gnd_near([v4])
# ================================================================= 5. SENSE_VBAT: L6 from U1's NE face out through the SE face, south to R43/R44
vV=fse(8.0,7.0)                                               # = the reserved inboard spot of pin 43 (NE face s 5.0, d 1.5)
V('SENSE_VBAT',vV,'VBAT via U1'); T('SENSE_VBAT',F,WP,[P('U1','43'),vV],'VBAT stub')
T('SENSE_VBAT',B,WP,[vV,fse(4.4,7.0),fse(4.4,-2.5)],'VBAT under U1')
vV2=free_via('SENSE_VBAT',(158.5,122.2),reach=1.0); V('SENSE_VBAT',vV2,'VBAT via R44')
RS('SENSE_VBAT',B,WP,fse(4.4,-2.5),vV2,box=(155.5,110.5,172.0,124.6),bend=1.0)
VB=(148.5,120.5,160.0,124.4)
RS('SENSE_VBAT',F,WP,vV2,P('TP38','1'),box=VB,bend=0.8); RS('SENSE_VBAT',F,WP,P('TP38','1'),P('C112','1'),box=VB,bend=0.8)
RS('SENSE_VBAT',F,WP,P('C112','1'),P('R44','1'),box=VB,bend=0.8); RS('SENSE_VBAT',F,WP,P('R44','1'),P('R43','2'),box=VB,bend=0.8)
# ================================================================= 6. ADC filter links on L1: U1 pin -> C (1 nF, at the pin) -> R (22 R)
FB=(162.5,109.5,170.0,117.5)
for pn,c,r in (('17','C14','R5'),('20','C15','R6'),('25','C16','R7')):
    net=W.padnet(c,'1'); RS(net,F,WP,pend('U1',pn,0.15),P(c,'1'),box=FB,bend=0.8); T(net,F,WP,[P('U1',pn),pend('U1',pn,0.15)],net+' pin')
    T(net,F,WP,[P(c,'1'),P(r,'1')],net+' C-R')
print('  trunk ends',{n:p[-1] for n,p in trunk.items()}); print('  J8 starts',{n:p[-1] for n,p in j8.items()})
W.plan['lock']=lock
W.save(sys.argv[2]); print('warnings',len(warn),warn)
