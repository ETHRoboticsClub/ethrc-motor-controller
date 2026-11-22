"""Step 4: regulators. LMR38020 (U2, 5 V buck), TPSM861253 (U5, 3.3 V module), LP2992 (U4, A3V3 LDO); all on the bottom.
Follows the datasheet layout guidance: input-cap loop first, small SW node, thermal vias under the U2 pad, FB divider at
the pin with the +5V sense taken at the output, a separate VOS path for U5, the U5 centre slot kept free of copper.
usage: plan_reg.py board.kicad_pcb plan.json"""
import sys,os,math
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from route import *
F,B,L3='F.Cu','B.Cu','In2.Cu'
W=World(sys.argv[1])
def V(net,x,y): return W.add_via(net,x,y)
def T(net,layer,w,pts,allow=()):
    pts=clean([tuple(p) for p in pts]); m=W.margin(net,layer,w/2,pts,allow)
    if m[0]<-0.005: print('  !! track',net,layer,[(round(x,2),round(y,2)) for x,y in pts][:4],'margin',round(m[0],3),m[1])
    return W.add_track(net,layer,w,pts)
def pick(net,cands,why,need=0.02,many=1,space=0.8):
    got=[]
    for x,y in cands:
        if len(got)>=many: break
        if any(math.dist((x,y),g)<space for g in got): continue
        if W.via_margin(net,x,y)[0]>=need: got.append(V(net,x,y))
    if len(got)<many: print('  -- %s: %d of %d vias'%(why,len(got),many),W.via_margin(net,*cands[0]))
    return got
P=W.pad
# ------------------------------------------------------------------ pours and rule areas
W.add_zone('VBAT buck input L6','+VBAT',B,[(155.6,91.65),(161.2,91.65),(161.2,90.1),(165.2,90.1),(165.2,91.65),(169.25,91.65),(169.25,93.75),(155.6,93.75)],priority=21)
W.add_zone('5V buck output L6','+5V',B,[(187.2,91.0),(193.8,91.0),(193.8,104.3),(187.2,104.3)])
W.add_zone('U5 centre slot','',B,[(171.65,101.5),(172.35,101.5),(172.35,103.85),(171.65,103.85)],keepout=True)
# ------------------------------------------------------------------ U2 LMR38020
for x in (170.15,171.0,171.85):                                                   # 4 x 3 thermal vias in the pad
    for y in (90.775,91.925,93.075,94.225): V('GND',x,y)
pick('+VBAT',[(x,92.1) for x in (157.7,158.4,159.1,159.8,160.5,161.2,165.7,166.4)],'buck input to the L3/L4 bus',many=4,space=1.3)
for x in (157.25,160.29,163.5): pick('GND',[(x,96.95),(x,97.05),(x+0.6,96.95),(x-0.6,96.95)],'input cap GND')
pick('GND',[(166.21,95.75),(166.4,95.8),(167.2,95.6)],'C29 / pin 1 GND')
T('SW_5V',B,0.8,[P('U2','8'),(178.9,94.41)])
T('Net-(U2-BOOT)',B,0.3,[P('U2','7'),(174.95,93.14),(175.21,93.4)])
T('Net-(U2-FB)',B,0.25,[P('U2','5'),(175.0,90.59),(175.19,90.4),(176.5,90.4)])
T('Net-(U2-RT{slash}SYNC)',B,0.25,[P('U2','4'),(166.71,90.59)])
T('Net-(U2-PG)',B,0.25,[P('U2','6'),(174.9,91.86),(175.6,91.16),(177.59,91.16)])
T('+5V',B,0.25,[P('R81','1'),(177.59,89.6),P('R80','2')])                         # divider top and PG pull-up
T('+5V',B,0.25,[P('R80','2'),(177.59,89.3),(177.65,89.24),(187.3,89.24),(187.9,89.84),(187.9,91.8)])   # sense from the inductor output, 2 mm off SW
# ------------------------------------------------------------------ +5V distribution on L6
near=lambda cx,cy:sorted([(round(184.0+0.1*i,2),round(98.8+0.1*j,2)) for i in range(27) for j in range(55)],key=lambda q:math.dist(q,(cx,cy)))
pick('GND',near(186.1,100.69),'output cap GND C39'); pick('GND',near(186.1,102.79),'output cap GND C162')
T('+5V',B,0.6,[(188.0,103.9),(187.4,104.5),P('C62','1')])
T('+5V',B,0.6,[P('C62','1'),(179.5,104.5)])
T('+5V',B,0.3,[(178.6,104.55),(178.0,105.15),(178.0,105.85),(178.6,106.45)])        # LP2992 ON/OFF (pin 3) to VIN (pin 1)
T('+5V',B,0.6,[(178.9,104.3),(178.9,101.5),(178.32,100.92),P('C51','1'),P('C58','1'),(173.6,100.92)])
T('+5V',B,0.3,[P('TP47','1'),(178.9,100.17),(178.9,101.5)])
v5=pick('+5V',[(171.2,95.9),(171.0,95.85),(170.9,96.1),(171.4,95.8)],'+5V to the top (CAN)')[0]
T('+5V',B,0.3,[v5,(v5[0],96.2),(173.35,96.2),P('R14','1')])
T('+5V',B,0.3,[P('R14','1'),(173.35,98.35),(178.4,98.35),(178.68,98.63),P('TP47','1')])   # north of the U10 pad vias
T('+5V',F,0.25,[v5,P('TP46','1'),(171.89,97.15),P('C147','1'),(172.52,97.03),P('U10','3')])
pick('GND',[(176.5,99.4),(176.5,99.3),(176.5,99.5)],'U5 input cap GND')
# ------------------------------------------------------------------ U5 TPSM861253
T('Net-(U5-EN)',B,0.2,[P('U5','6'),(172.0,99.4),(172.55,98.85)])
T('Net-(U5-EN)',B,0.2,[(172.0,99.4),(171.5,98.9)])
T('Net-(U5-EN)',B,0.2,[(171.55,98.67),(171.55,97.5)])
T('+3V3',B,0.6,[(170.4,102.1),P('C87','1')])
vb=pick('+3V3',[(170.85,104.4),(170.85,104.6),(171.1,104.5),(170.6,104.5)],'+3V3 exit')[0]
T('+3V3',B,0.6,[(170.85,103.5),(170.85,vb[1]),vb])
va=pick('+3V3',[(174.05,99.4),(174.1,99.35),(174.0,99.5),(174.15,99.3)],'VOS hop')[0]
T('+3V3',B,0.2,[P('U5','7'),(172.5,99.75),(172.85,va[1]),va])
T('+3V3',L3,0.2,link(va,vb))                                                        # VOS: own path on L3, between GND layers
pick('GND',[(170.6,99.45),(169.0,100.0),(170.4,99.5)],'U5 PGND')
pick('GND',[(168.2,100.9),(168.0,100.9),(168.1,100.5)],'C87 GND')
# ------------------------------------------------------------------ U4 LP2992
T('+A3V3',B,0.4,[P('U4','5'),P('C86','1')])
T('ADJ_A3V3',B,0.25,[P('U4','4'),(176.6,106.71),(176.6,108.0)])
T('GND',B,0.4,[P('U4','2'),(180.4,105.5),(180.6,105.7),P('C62','2')])
pick('GND',[(180.2,106.6),(179.6,107.3),(181.0,106.8)],'U4 / C62 GND')
pick('GND',[(175.0,102.6),(175.9,102.6),(174.2,102.6)],'C86 GND')
W.save(sys.argv[2])
