"""Step 5b: EtherCAT chip-side pairs U9 -> T1 (port 0) and U9 -> T2 (port 1), RBIAS, and the decoupling on U9's west face.
Placement (approved 2026-11-22): C126/C134/C128 move into the wedge between the two ports, FB5 moves 0.7 mm towards
U9's north corner; all four are locked afterwards.
Port 0: RX on L1 straight out; TX on L6 (crosses under RX, its order at T1 is the other way round).
Port 1: both pairs are polarity-reversed between U9 and T2; RX1+ and TX1- each hop under their partner on L6.
Pairs 0.18 mm, 0.5 mm pitch (0.32 mm gap) out of the pins, 0.53 mm pitch (0.35 mm gap) elsewhere.
usage: plan_s5b.py board.kicad_pcb plan.json"""
import sys,os,math
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from route import *
from u9frame import Frame
F,B='F.Cu','B.Cu'; EW=0.18
W=World(sys.argv[1]); P=W.pad; Fr=Frame(W); xy=Fr.xy
def T(net,layer,w,pts,tag=''):
    pts=clean([tuple(p) for p in pts]); m=W.margin(net,layer,w/2,pts)
    if m[0]<-0.005: print('  !! %s %s %s margin %.3f %s'%(tag or net,layer,[(round(x,2),round(y,2)) for x,y in pts][:3],m[0],m[1]))
    return W.add_track(net,layer,w,pts)
def V(net,p,tag=''):
    m=W.via_margin(net,*p)
    if m[0]<-0.005: print('  !! via %s %s margin %.3f %s'%(tag or net,p,m[0],m[1]))
    return W.add_via(net,*p,check=False)
def R(net,layer,w,a,b,**kw):
    pts=W.route(net,layer,w,a,b,**kw); assert pts,(net,a,b); return W.add_track(net,layer,w,pts)
def center(ref): ps=W.R[ref].pads; return (sum(p.x for p in ps)/len(ps),sum(p.y for p in ps)/len(ps))
def move_center(ref,s,d):
    cx,cy=center(ref); tx,ty=xy(s,d); f=W.R[ref]; W.shift(ref,round(f.x+tx-cx,3),round(f.y+ty-cy,3))
def gnd_via(ref,num,layer=F,reach=1.6):
    px,py=P(ref,num); pad=[o for o in W.obs if o['ref']==ref+'.'+num][0]
    cands=sorted({(round(px+0.1*i,2),round(py+0.1*j,2)) for i in range(-16,17) for j in range(-16,17)},key=lambda q:math.dist(q,(px,py)))
    for x,y in cands:
        if math.dist((x,y),(px,py))>reach: break
        if float(W._dist(pad,np.array([x]),np.array([y]))[0])-0.275<0.1: continue
        if W.via_margin('GND',x,y)[0]<0.02 or W.margin('GND',layer,0.15,[(px,py),(x,y)])[0]<0.0: continue
        W.add_via('GND',x,y); W.add_track('GND',layer,0.3,[(px,py),(x,y)]); return (x,y)
    raise SystemExit('no GND via spot for %s.%s'%(ref,num))
pin=lambda k: P('U9',str(k)); s_of=Fr.pin_s
# ------------------------------------------------------------------ placement on the west face
fs,fd=Fr.sd(*center('FB5')); move_center('FB5',fs-0.7,fd)
move_center('C126',2.1,3.0); move_center('C134',3.55,3.4); move_center('C128',4.65,3.6)
W.plan['lock']=['FB5','C126','C134','C128']
# ------------------------------------------------------------------ port 1 escape: straight out, 45 deg left (west), staggered bends, trunks west
P1={63:('ECAT_P1_TX-',0.9),62:('ECAT_P1_TX+',1.107),61:('ECAT_P1_RX-',1.314),60:('ECAT_P1_RX+',1.521)}
bend={k:xy(s_of(k),dt) for k,(net,dt) in P1.items()}
xTp,xTm=131.8,132.3
h1=(133.4,bend[60][1]-0.3); u1=(130.55,111.4); h2=(xTm+0.3,114.2); u2=(130.55,114.6)
T('ECAT_P1_RX+',F,EW,[pin(60),bend[60],(h1[0]+0.3,bend[60][1]),h1],'RX1+ trunk')
T('ECAT_P1_RX-',F,EW,[pin(61),bend[61],(133.1,bend[61][1]),(133.1-(bend[61][1]-108.6),108.6),P('R66','2')],'RX1- trunk')
T('ECAT_P1_TX+',F,EW,[pin(62),bend[62],(xTp,bend[62][1]),(xTp,117.95),(xTp-0.5,118.45)],'TX1+ trunk')
T('ECAT_P1_TX-',F,EW,[pin(63),bend[63],(xTm,bend[63][1]),(xTm,h2[1]-0.3),h2],'TX1- trunk')
for net,h,u in (('ECAT_P1_RX+',h1,u1),('ECAT_P1_TX-',h2,u2)): V(net,h,net+' hop'); V(net,u,net+' up')
# ------------------------------------------------------------------ middle pins: decoupling and RBIAS (router, leftmost first)
# hand-placed: straight out, one 45-degree jog each, bends staggered so every gap stays >= 0.3 mm
T('+1V2_ESC',F,0.2,[pin(59),xy(3.5,1.6),xy(4.65,2.75),P('C128','1')],'pin 59 -> C128')
T('+3V3_PHY',F,0.2,[pin(58),xy(3.0,1.81),xy(3.55,2.36),P('C134','1')],'pin 58 -> C134')
vr=V('ESC_RBIAS',xy(2.8,4.3),'RBIAS via')
T('ESC_RBIAS',F,0.2,[pin(57),xy(2.5,2.02),xy(2.8,2.32),vr],'RBIAS')
R('ESC_RBIAS',B,0.25,vr,P('R55','1'),box=(136,102,146,112))
T('+1V2_ESC',F,0.2,[pin(56),P('C126','1')],'pin 56 -> C126')
# ------------------------------------------------------------------ port 0 RX: L1, straight out, then fan to R65/R63 and T1
D_RX=11.4
a_m,a_p=xy(s_of(54),D_RX),xy(s_of(55),D_RX)
T('ECAT_P0_RX-',F,EW,[pin(54),a_m],'RX0- trunk'); T('ECAT_P0_RX+',F,EW,[pin(55),a_p],'RX0+ trunk')
vm,vp=xy(-0.15,4.0),xy(0.43,4.75)
T('ECAT_P0_TX-',F,EW,[pin(52),xy(0,3.7),vm],'TX0- stub'); T('ECAT_P0_TX+',F,EW,[pin(53),xy(0.5,4.4),vp],'TX0+ stub')
V('ECAT_P0_TX-',vm,'TX0- via'); V('ECAT_P0_TX+',vp,'TX0+ via')
for ref in ('C126','C134','C128'): gnd_via(ref,'2')
R('ECAT_P0_RX+',F,EW,a_p,P('R63','2'),d0=(-1,-1),d0_len=0.3,box=(128,93,137,102))
R('ECAT_P0_RX-',F,EW,a_m,P('R65','2'),d0=(-1,-1),d0_len=0.3,box=(128,93,137,102))
R('ECAT_P0_RX+',F,EW,P('R63','2'),P('T1','6'),box=(126,93,135,101))
R('ECAT_P0_RX-',F,EW,P('R65','2'),P('T1','8'),box=(126,93,135,101))
# ------------------------------------------------------------------ port 0 TX: two vias each, L6 pair to T1, up next to R61 / R59
um,up=(130.3,101.1),(129.9,104.85)
V('ECAT_P0_TX-',um,'TX0- up'); V('ECAT_P0_TX+',up,'TX0+ up')
yN=vp[1]-0.67; yS=yN+0.53                                       # L6 pair: TX0- north (clears the TX0+ via), TX0+ south
T('ECAT_P0_TX+',B,EW,[vp,(vp[0]-(vp[1]-yS),yS),(131.9,yS),(131.9-(104.85-yS),104.85),up],'TX0+ L6')
T('ECAT_P0_TX-',B,EW,[vm,(vm[0]-(vm[1]-yN),yN),(131.68,yN),(131.68-(yN-101.86),101.86),um],'TX0- L6')
R('ECAT_P0_TX-',F,EW,um,P('R61','2'),box=(127,99,132,103)); R('ECAT_P0_TX-',F,EW,P('R61','2'),P('T1','3'),box=(126,99,131,103))
R('ECAT_P0_TX+',F,EW,up,P('R59','2'),box=(127,102,132,106)); R('ECAT_P0_TX+',F,EW,P('R59','2'),P('T1','1'),box=(126,102,131,106))
# ------------------------------------------------------------------ port 1: L6 hops and the T2 end
R('ECAT_P1_RX+',B,EW,h1,u1,box=(129,107,136,113)); R('ECAT_P1_RX+',F,EW,u1,P('R64','2'),box=(128,110,132,113)); R('ECAT_P1_RX+',F,EW,P('R64','2'),P('T2','6'),box=(126,109,131,113))
R('ECAT_P1_RX-',F,EW,P('R66','2'),P('T2','8'),box=(126,107,131,110))
R('ECAT_P1_TX+',F,EW,(xTp-0.5,118.45),P('R60','2'),box=(128,116,133,120)); R('ECAT_P1_TX+',F,EW,P('R60','2'),P('T2','1'),box=(126,116,131,119))
R('ECAT_P1_TX-',B,EW,h2,u2,box=(129,112,134,116)); R('ECAT_P1_TX-',F,EW,u2,P('R62','2'),box=(128,113,132,116)); R('ECAT_P1_TX-',F,EW,P('R62','2'),P('T2','3'),box=(126,113,131,116))
for lay in (F,B):
    W.add_zone('ECAT_MAGNETICS','',lay,[(126.5,93.5),(134.5,93.5),(134.5,119.5),(126.5,119.5)],keepout=True,allow=('tracks','vias','pours'))
W.save(sys.argv[2])
