"""Step 5c: EtherCAT cable side. T1 -> J9 (port 0) and T2 -> J10 (port 1) on L1 inside ECAT_ISOLATION, centre taps through
the 75 ohm Bob Smith resistors to C155/C156 (1 nF 2 kV) on L6, C155/C156 to the CHASSIS ring on L6, drain pins to the
shell pads. Each pair runs coupled (0.53 mm pitch) down the 1.33 mm channel between the connector and the magnetics.
usage: plan_s5c.py board.kicad_pcb plan.json"""
import sys,os,math
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from route import *
F,B='F.Cu','B.Cu'; EW=0.18
W=World(sys.argv[1]); P=W.pad
def T(net,layer,w,pts,tag=''):
    pts=clean([tuple(p) for p in pts]); m=W.margin(net,layer,w/2,pts)
    if m[0]<-0.005: print('  !! %s %s margin %.3f %s'%(tag or net,layer,m[0],m[1]))
    return W.add_track(net,layer,w,pts)
def V(net,p):
    m=W.via_margin(net,*p)
    if m[0]<-0.005: print('  !! via %s %s margin %.3f %s'%(net,p,m[0],m[1]))
    return W.add_via(net,*p,check=False)
XW,XE=117.25,117.78                                  # channel lanes: west (towards the connector) and east
def port(Tr,J,p,cbl,ct_r,ct_t,bob_r,bob_t,cap,ring_x):
    y=lambda n: P(Tr,n)[1]; yj=lambda n: P(J,n)[1]; x0=P(Tr,'9')[0]
    T(cbl+'RX-',F,EW,[P(Tr,'9'),(XW,y('9')),(XW,yj('2')-0.25),(XW-0.25,yj('2')),P(J,'2')],p+' RX-')
    T(cbl+'RX+',F,EW,[P(Tr,'11'),(XE,y('11')),(XE,yj('3')-0.25),(XE-0.25,yj('3')),P(J,'3')],p+' RX+')
    if yj('4')>y('14'):                              # TX- runs down to the connector
        T(cbl+'TX-',F,EW,[P(Tr,'14'),(118.4,y('14')),(118.4-(yj('4')-y('14')),yj('4')),P(J,'4')],p+' TX-')
        T(cbl+'TX+',F,EW,[P(Tr,'16'),(117.15,y('16')),(117.15-(y('16')-yj('5')),yj('5')),P(J,'5')],p+' TX+')
    else:                                            # TX- runs up to the connector
        T(cbl+'TX-',F,EW,[P(Tr,'14'),(118.4,y('14')),(118.4-(y('14')-yj('4')),yj('4')),P(J,'4')],p+' TX-')
        T(cbl+'TX+',F,EW,[P(Tr,'16'),(XE,y('16')),(XE,yj('5')+0.25),(XE-0.25,yj('5')),P(J,'5')],p+' TX+')
    # centre taps: via beside the pad (not in it), L6 to the 75 ohm resistor
    for pin,(vx,vy),res in (('10',(120.25,y('10')-0.38),ct_r),('15',(120.25,y('15')+0.57),ct_t)):
        net=W.padnet(Tr,pin); px,py=P(Tr,pin); v=V(net,(vx,vy))
        T(net,F,0.3,[(px,py),(vx-abs(vy-py),py),(vx,vy)],p+' CT'+pin)
        rx,ry=P(res,'1'); T(net,B,0.3,[(vx,vy),(vx+abs(ry-vy),ry),(rx,ry)],p+' CT'+pin+' L6')
    # Bob Smith node and the 2 kV cap to CHASSIS
    node=W.padnet(cap,'1'); cx,cy=P(cap,'1')
    for res in (bob_r,bob_t): rx,ry=P(res,'2'); T(node,B,0.3,[(rx,ry),(rx,cy)],p+' Bob')
    T('CHASSIS',B,0.4,[P(cap,'2'),(ring_x,cy)],p+' C to ring')
    # cable drain to the shell pad (both CHASSIS)
    T('CHASSIS',F,0.3,W.route('CHASSIS',F,0.3,P(J,'1'),P(J,'MP1'),quiet=True,box=(110,95,118,120)),p+' drain')
port('T1','J9','P0','ECAT_P0_CBL_','R86','R85','R86','R85','C155',107.4)
port('T2','J10','P1','ECAT_P1_CBL_','R88','R87','R88','R87','C156',109.3)
W.add_zone('ECAT_MAGNETICS','',F,[(114.6,93.5),(120.7,93.5),(120.7,119.0),(114.6,119.0)],keepout=True,allow=('tracks','vias','pours'))
W.save(sys.argv[2])
