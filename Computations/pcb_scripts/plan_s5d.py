"""Step 5 rework to the Microchip LAN9253 HW design checklist DS00003644B (user decision 2026-11-22).
- Pairs on L1 only, no vias (schematic swap at T1/T2 makes the pin order match), 0.18 mm at 0.5 mm pitch.
- 49.9 ohm terminations inline on the pairs right after the U9 escape (5-9 mm from the pins), +3V3_PHY side by via
  into an L6 mini-plane that also takes the T1/T2 centre taps, C144/C145 (bottom), FB5, pins 51/58/64.
- RBIAS R55 on top at pin 57 (2.4 mm trace, 0.25 mm); C126/C128/C134 at pins 56/59/58.
- Crystal: R84/R83 (0R) at OSCI/OSCO, XO around Y1's GND pad, hooks TP76 (XO, crystal side) and TP77 (GND).
- Test pads on the PHY supplies, OSCVDD12, the SII EEPROM bus and all eight pair lines (0.4 mm, inline, no stub).
usage: plan_s5d.py board.kicad_pcb plan.json   (board = synced and cleaned, see sync_board.py / cleanup_ecat.py)"""
import sys,os,math
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from route import *
F,B='F.Cu','B.Cu'; EW=0.18; R2=1/math.sqrt(2)
W=World(sys.argv[1]); P=W.pad
warn=[]
def T(net,layer,w,pts,tag=''):
    pts=clean([tuple(p) for p in pts]); m=W.margin(net,layer,w/2,pts)
    if m[0]<-0.005: warn.append(tag); print('  !! %-14s %s margin %.3f %s'%(tag or net,layer,m[0],m[1]))
    return W.add_track(net,layer,w,pts)
def V(net,p,tag=''):
    m=W.via_margin(net,*p)
    if m[0]<-0.005: warn.append(tag); print('  !! via %-10s %s margin %.3f %s'%(tag or net,tuple(round(v,2) for v in p),m[0],m[1]))
    return W.add_via(net,*p,check=False)
def R(net,layer,w,a,b,**kw):
    pts=W.route(net,layer,w,a,b,quiet=True,**kw); assert pts,(net,a,b); return T(net,layer,w,pts,net+' (routed)')
# ---------------------------------------------------------------- frames
o1=P('U9','52'); U1=(-R2,R2); N1=(-R2,-R2)                    # west face: s along pins 52->63, d outwards (NW)
f1=lambda s,d:(round(o1[0]+s*U1[0]+d*N1[0],4),round(o1[1]+s*U1[1]+d*N1[1],4))
o2=P('U9','1'); U2=(R2,R2); N2=(-R2,R2)                       # south-west face: s along pins 1->8, d outwards (SW)
f2=lambda s,d:(round(o2[0]+s*U2[0]+d*N2[0],4),round(o2[1]+s*U2[1]+d*N2[1],4))
pin=lambda k:P('U9',str(k)); s1=lambda k:(k-52)*0.5
def centre(ref): ps=W.R[ref].pads; return (sum(p.x for p in ps)/len(ps),sum(p.y for p in ps)/len(ps))
def put(ref,c,pad1_at,bottom=False):                         # two-pad part: centre c, pad "1" towards pad1_at
    W.place2(ref,c[0],c[1],'1',pad1_at,bottom=bottom)
def put2(ref,c,pad,at,bottom=False): W.place2(ref,c[0],c[1],pad,at,bottom=bottom)
def shift(ref,dx,dy): f=W.R[ref]; W.shift(ref,round(f.x+dx,3),round(f.y+dy,3))
def axial(c,u,L): return ((c[0]-u[0]*L/2,c[1]-u[1]*L/2),(c[0]+u[0]*L/2,c[1]+u[1]*L/2))
lock=[]
# ================================================================= placement
for r in ('R90','R91','TP21','TP22'): shift(r,0.0,-1.0)        # CS/IRQ pull-ups 1 mm north: port 0 runs west below them
# middle pins (frame 1): C126 @56, R55 (RBIAS) @57 on top, C134 @58, C128 @59 - all along d, pad 1 towards the face
put2('C126',f1(2.1,3.0),'1',f1(2.1,2.6)); put2('R55',f1(3.05,3.25),'1',f1(3.05,2.6))
put2('C134',f1(4.0,5.2),'1',f1(4.0,4.8)); put2('C128',f1(5.02,3.75),'1',f1(5.02,3.35))
# crystal (frame 2): R84 on XI, R83 on XO right at the pins; C116 0.62 mm away from the XO path; hooks south-west of Y1
put2('R84',f2(-0.45,2.25),'1',f2(-0.45,1.6)); put2('R83',f2(0.7,2.25),'2',f2(0.7,1.6))
c116=centre('C116'); cs,cd=((c116[0]-o2[0])*U2[0]+(c116[1]-o2[1])*U2[1]),((c116[0]-o2[0])*N2[0]+(c116[1]-o2[1])*N2[1])
put2('C116',f2(cs+0.62,cd),'1',f2(cs+0.62,cd+0.4))
W.shift('TP76',*f2(2.8,9.6)); W.shift('TP77',*f2(0.5,10.8))
put2('C144',(130.6,102.73),'1',(130.2,102.73),bottom=True); put2('C145',(130.6,116.17),'1',(130.2,116.17),bottom=True)
lock+=['C144','C145','R90','R91','TP21','TP22','C126','R55','C134','C128','R84','R83','C116','TP76','TP77']
# ================================================================= port 1 (frame 1 bends, then west, TX pair steps down)
yv=lambda s,d:o1[1]+R2*(s-d)
P1=[(63,'ECAT_P1_TX-',0.5),(62,'ECAT_P1_TX+',0.707),(61,'ECAT_P1_RX-',0.914),(60,'ECAT_P1_RX+',1.121)]
bend={net:f1(s1(k),dt) for k,net,dt in P1}
y1={net:bend[net][1] for net in bend}
xa=139.5; xb=xa+0.207; J=1.2                                    # TX pair: 45-degree step down by J
tx1p=[pin(62),bend['ECAT_P1_TX+'],(xa,y1['ECAT_P1_TX+']),(xa-J,y1['ECAT_P1_TX+']+J)]
tx1m=[pin(63),bend['ECAT_P1_TX-'],(xb,y1['ECAT_P1_TX-']),(xb-J,y1['ECAT_P1_TX-']+J)]
yTp,yTm=y1['ECAT_P1_TX+']+J,y1['ECAT_P1_TX-']+J
# TX pair: west to the turn, 45 deg south-west, TX1+ west into T2.3, TX1- south then west into T2.1
xt=133.0
tx1m+=[(xt,yTm),(129.9+0.0,yTm+(xt-129.9)),(129.9,P('T2','1')[1]-0.5),(129.4,P('T2','1')[1]),P('T2','1')]
tx1p+=[(xt-0.207,yTp),(xt-0.207-(P('T2','3')[1]-yTp),P('T2','3')[1]),P('T2','3')]
# RX pair: straight west; RX1+ steps onto T2.8, RX1- drops onto T2.6 west of the TX turn
rx1p=[pin(60),bend['ECAT_P1_RX+'],(130.5,y1['ECAT_P1_RX+']),(130.5-(y1['ECAT_P1_RX+']-P('T2','8')[1]),P('T2','8')[1]),P('T2','8')]
rx1m=[pin(61),bend['ECAT_P1_RX-'],(131.0,y1['ECAT_P1_RX-']),(131.0-(P('T2','6')[1]-y1['ECAT_P1_RX-']),P('T2','6')[1]),P('T2','6')]
# ================================================================= port 0 (straight out, staggered left turn west, TX pair rises north-west)
P0=[(55,'ECAT_P0_RX+',4.2),(54,'ECAT_P0_RX-',4.407),(53,'ECAT_P0_TX+',4.614),(52,'ECAT_P0_TX-',4.821)]
b0={net:f1(s1(k),dt) for k,net,dt in P0}; y0={net:b0[net][1] for net in b0}
xr=138.2                                                        # TX pair turns north-west here (TX- first)
tx0m=[pin(52),b0['ECAT_P0_TX-'],(xr,y0['ECAT_P0_TX-'])]; tx0p=[pin(53),b0['ECAT_P0_TX+'],(xr-0.207,y0['ECAT_P0_TX+'])]
for path,tgt in ((tx0m,P('T1','8')),(tx0p,P('T1','6'))):
    x,y=path[-1]; path+=[(x-(y-tgt[1]),tgt[1]),tgt]
rx0m=[pin(54),b0['ECAT_P0_RX-'],(132.0,y0['ECAT_P0_RX-']),(132.0-(y0['ECAT_P0_RX-']-P('T1','3')[1]),P('T1','3')[1]),P('T1','3')]
rx0p=[pin(55),b0['ECAT_P0_RX+'],(130.0,y0['ECAT_P0_RX+']),(130.0-(y0['ECAT_P0_RX+']-P('T1','1')[1]),P('T1','1')[1]),P('T1','1')]
# ================================================================= terminations inline (pad 2 on the line, pad 1 outwards)
stubs=[]
def term(ref,on,out,net):                                      # on: point on the line, out: unit vector to pad 1
    p2=(on[0]+out[0]*0.3,on[1]+out[1]*0.3)                       # pad 2 sits 0.3 mm outboard: clears the partner line
    put2(ref,(p2[0]+out[0]*0.4,p2[1]+out[1]*0.4),'2',p2); lock.append(ref); stubs.append((net,on,p2))
    return (p2[0]+out[0]*0.8,p2[1]+out[1]*0.8)                  # pad 1 centre
UP,DN=(0,-1),(0,1); SWd=(-R2,R2)
t1={}
t1['R64']=term('R64',(136.6,y1['ECAT_P1_RX+']),UP,'ECAT_P1_RX+'); t1['R66']=term('R66',(135.6,y1['ECAT_P1_RX-']),DN,'ECAT_P1_RX-')
t1['R60']=term('R60',(134.6,yTp),UP,'ECAT_P1_TX+'); t1['R62']=term('R62',(133.6,yTm),DN,'ECAT_P1_TX-')
t0={}
t0['R61']=term('R61',(138.9,y0['ECAT_P0_TX-']),UP,'ECAT_P0_TX-')
xp,yp=tx0p[2]; t0['R59']=term('R59',(xp-1.06,yp-1.06),SWd,'ECAT_P0_TX+')
t0['R65']=term('R65',(135.0,y0['ECAT_P0_RX-']),UP,'ECAT_P0_RX-'); t0['R63']=term('R63',(134.0,y0['ECAT_P0_RX+']),DN,'ECAT_P0_RX+')
# ================================================================= draw the pairs
for net,pts in (('ECAT_P1_TX-',tx1m),('ECAT_P1_TX+',tx1p),('ECAT_P1_RX+',rx1p),('ECAT_P1_RX-',rx1m),
                ('ECAT_P0_TX-',tx0m),('ECAT_P0_TX+',tx0p),('ECAT_P0_RX-',rx0m),('ECAT_P0_RX+',rx0p)):
    T(net,F,EW,pts,net)
for net,a,b in stubs: T(net,F,0.2,[a,b],'stub '+net)
# ================================================================= middle pins
T('+1V2_ESC',F,0.2,[pin(56),P('C126','1')],'pin56')
T('ESC_RBIAS',F,0.2,[pin(57),f1(2.5,1.62)],'RBIAS'); T('ESC_RBIAS',F,0.25,[f1(2.5,1.62),f1(3.05,2.17),P('R55','1')],'RBIAS wide')
T('+3V3_PHY',F,0.2,[pin(58),f1(3.0,1.3),f1(3.85,2.15),f1(3.85,4.4),f1(4.0,4.55),P('C134','1')],'pin58')
T('+1V2_ESC',F,0.2,[pin(59),f1(3.5,1.2),f1(4.35,2.05),f1(4.35,2.68),P('C128','1')],'pin59')
# ================================================================= crystal
T('ESC_XI',F,0.2,[pin(1),f2(0,0.6),f2(-0.45,1.05),P('R84','1')],'XI')
T('Net-(C117-Pad1)',F,0.2,[P('R84','2'),f2(-0.45,3.5),P('C117','1'),P('Y1','3')],'XI xtal')
T('ESC_XO',F,0.2,[pin(2),f2(0.5,0.6),f2(0.7,0.8),P('R83','2')],'XO')
xo=[P('R83','1'),f2(0.7,3.3),f2(1.0,3.6),f2(1.0,4.5),f2(2.5,4.5),f2(2.5,7.9)]
T('ESC_XO_XTAL',F,0.2,xo,'XO xtal')
T('ESC_XO_XTAL',F,0.2,[f2(2.5,7.9),P('Y1','1')],'XO pad'); T('ESC_XO_XTAL',F,0.2,[f2(2.5,7.9),P('C116','1')],'XO cap')
T('ESC_XO_XTAL',F,0.25,[P('C116','1'),P('TP76','1')],'hook')
T('ESC_OSCVDD12',F,0.2,[pin(3),f2(1.0,0.5),f2(1.65,1.15),f2(1.65,1.6),P('C120','1')],'OSCVDD12')
T('ESC_OSCVDD12',F,0.25,[P('C120','1'),P('C119','1')],'OSCVDD12 b')
# ================================================================= vias next to pads (never in the pad), joined by a short track
def free_spots(net,ref,num,r,reach,keep,prefer=None,layers=(F,B)):
    """grid points within reach of a pad, clear of everything on the given layers (zones ignored), not on the pad"""
    px,py=P(ref,num); pad=[o for o in W.obs if o['ref']==ref+'.'+num][0]; nc=W.canon(net)
    g=0.05; n=int(2*reach/g)+1; x0,y0=px-reach,py-reach; allz=tuple(z['ref'] for z in W.zones)
    ok=np.ones((n,n),bool)
    for lay in layers: ok&=~W.blocked(nc,lay,r,x0,y0,n,n,g,allow=allz,eps=0.02)
    X=x0+g*np.arange(n)[None,:]+np.zeros((n,1)); Y=y0+g*np.arange(n)[:,None]+np.zeros((1,n))
    D=np.hypot(X-px,Y-py); ok&=(D<=reach)&((W._dist(pad,X,Y)-r)>=keep)
    cost=D+(0 if prefer is None else 0.6*np.hypot(X-prefer[0],Y-prefer[1]))
    order=np.argsort(np.where(ok,cost,1e9),axis=None)
    for idx in order[:600]:
        j,i=divmod(int(idx),n)
        if not ok[j,i]: return
        yield (round(float(X[j,i]),3),round(float(Y[j,i]),3)),(px,py)
def via_near(net,ref,num,layer=F,reach=2.2,w=0.3,prefer=None):
    for (x,y),(px,py) in free_spots(net,ref,num,0.275,reach,0.08,prefer):
        if W.via_margin(net,x,y)[0]<0.02: continue
        if W.margin(net,layer,w/2,[(px,py),(x,y)],allow=tuple(z['ref'] for z in W.zones))[0]<0.0: continue   # pours yield
        W.add_via(net,x,y,check=False); W.add_track(net,layer,w,[(px,py),(x,y)]); return (x,y)
    warn.append(ref+num); print('  !! no via spot for %s.%s (%s)'%(ref,num,net))
# +3V3_PHY: terminations, centre taps, decoupling, FB5 -> L6 mini-plane
for ref in ('R61','R59','R65','R63','R64','R66','R60','R62'): via_near('+3V3_PHY',ref,'1')
for pin_ in ('2','7'):
    for Tr in ('T1','T2'): via_near('+3V3_PHY',Tr,pin_,prefer=(129.6,P(Tr,pin_)[1]))
T('+3V3_PHY',F,0.25,[pin(51),P('C135','1')],'pin51')
R('+3V3_PHY',F,0.3,P('FB5','1'),P('C135','1'),box=(140,101,146,107))
via_near('+3V3_PHY','C135','1'); via_near('+3V3_PHY','C134','1'); via_near('+3V3_PHY','FB5','1')
via_near('+3V3_PHY','U9','64',w=0.2,reach=1.6,prefer=(139.2,111.7))          # into the mini-plane, which also takes C133
W.add_zone('3V3_PHY mini-plane L6','+3V3_PHY',B,[(128.6,95.6),(133.2,95.6),(133.2,98.6),(143.6,98.6),(143.6,106.6),(141.2,109.0),
            (141.2,111.4),(138.0,113.0),(132.0,113.0),(132.0,118.2),(128.6,118.2)],priority=20)
for ref,pt in (('TP84',(140.0,y0['ECAT_P0_TX-'])),('TP83',(139.3,y0['ECAT_P0_TX+'])),('TP86',(138.6,y0['ECAT_P0_RX-'])),('TP85',(139.3,y0['ECAT_P0_RX+'])),
               ('TP89',(139.0,y1['ECAT_P1_RX+'])),('TP90',(138.3,y1['ECAT_P1_RX-'])),('TP87',(137.8,yTp)),('TP88',(137.1,yTm))):
    W.shift(ref,*pt); lock.append(ref)
    m=W.margin(W.padnet(ref,'1'),F,0.2,[pt,pt])
    if m[0]<0: warn.append(ref); print('  !! %s pad margin %.3f %s'%(ref,m[0],m[1]))
# GND: decoupling, crystal, centre-tap caps (bottom)
for ref,num in (('C126','2'),('R55','2'),('C134','2'),('C128','2'),('C117','2'),('Y1','2'),('Y1','4'),('C116','2'),('C119','2'),('C120','2'),('C135','2')):
    via_near('GND',ref,num)
for ref in ('C144','C145','C133'): via_near('GND',ref,'2',layer=B)
# ================================================================= test points
def tp_near(ref,tref,tnum,reach=2.5):                          # 0.5 mm test pad near a pad of its net, short 0.2 mm track
    net=W.padnet(ref,'1')
    for (x,y),(px,py) in free_spots(net,tref,tnum,0.3,reach,0.25,layers=(F,)):
        if W.margin(net,F,0.1,[(px,py),(x,y)])[0]<0.0: continue
        W.shift(ref,x,y); W.add_track(net,F,0.2,[(px,py),(x,y)]); lock.append(ref); return
    warn.append(ref); print('  !! no spot for',ref)
tp_near('TP78','C135','1'); tp_near('TP79','C128','1'); tp_near('TP80','C119','1'); tp_near('TP81','U8','1'); tp_near('TP82','U8','3')
W.plan['lock']=lock
W.save(sys.argv[2]); print('warnings',len(warn))
