"""Step 5a: LAN9253 crystal Y1 (25 MHz) and its 1.2 V oscillator supply.
Short XI/XO on L1 over the L2 GND plane, load caps C116/C117 on their pins, one GND via per crystal / cap GND pad,
and a track/via keepout under the crystal circuit on L3, L4 and L6 (no other signals beneath it).
usage: plan_s5a.py board.kicad_pcb plan.json"""
import sys,os,math
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from route import *
F='F.Cu'; SW=(-1,1)
W=World(sys.argv[1]); P=W.pad
for net,a,b,kw in [('ESC_XI',P('U9','1'),P('C117','1'),dict(d0=SW,d0_len=0.5)),('ESC_XI',P('C117','1'),P('Y1','3'),{}),
                   ('ESC_OSCVDD12',P('U9','3'),P('C120','1'),dict(d0=SW,d0_len=0.5)),('ESC_OSCVDD12',P('C120','1'),P('C119','1'),{}),
                   ('ESC_XO',P('U9','2'),P('Y1','1'),dict(d0=SW,d0_len=0.5,bend=4.0)),('ESC_XO',P('Y1','1'),P('C116','1'),{})]:
    pts=W.route(net,F,0.2,a,b,box=(130,108,146,122),**kw)
    assert pts,net
    W.add_track(net,F,0.2,pts)
def gnd_via(ref,num,reach=1.6):
    """One GND via as close as possible to a pad (nearest valid grid point), joined to it with a short 0.3 mm track."""
    px,py=P(ref,num); pad=[o for o in W.obs if o['ref']==ref+'.'+num][0]
    off=lambda x,y: float(W._dist(pad,np.array([x]),np.array([y]))[0])-0.275>=0.1   # via fully outside the pad (no solder wicking)
    cands=sorted({(round(px+0.1*i,2),round(py+0.1*j,2)) for i in range(-16,17) for j in range(-16,17)},key=lambda q:math.dist(q,(px,py)))
    for x,y in cands:
        d=math.dist((x,y),(px,py))
        if d>reach: break
        if not off(x,y) or W.via_margin('GND',x,y)[0]<0.02 or W.margin('GND',F,0.15,[(px,py),(x,y)])[0]<0.0: continue
        W.add_via('GND',x,y); W.add_track('GND',F,0.3,[(px,py),(x,y)]); return
    raise SystemExit('no GND via spot for %s.%s'%(ref,num))
for ref,num in (('Y1','2'),('Y1','4'),('C116','2'),('C117','2'),('C119','2'),('C120','2')): gnd_via(ref,num)
for lay in ('In2.Cu','In3.Cu','B.Cu'):
    W.add_zone('Y1 crystal keepout '+lay,'',lay,[(132.8,117.4),(136.4,113.8),(140.2,111.4),(141.3,112.5),(139.0,117.7),(136.5,120.6)],keepout=True,allow=('vias','pours'))
W.save(sys.argv[2])
