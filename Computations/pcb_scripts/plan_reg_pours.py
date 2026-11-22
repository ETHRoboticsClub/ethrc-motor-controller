"""Step 4 review round 1: U2's switch node and the +5V distribution become L6 pours instead of tracks.
LMR38020 section 9.5.1: short, wide SW connection from pin 8 to the inductor; wide VIN/VOUT/GND paths.
The +5V pour reaches L1's output pad, C39/C162, C62, U4 pin 1, C51/C58, U5 VIN and TP47.
usage: plan_reg_pours.py board.kicad_pcb plan.json"""
import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from route import *
B='B.Cu'
W=World(sys.argv[1])
# ------------------------------------------------------------------ switch node: pin 8 -> C31 -> L1 pad 1
W.drop_seg((173.712,94.405),(178.9,94.41))
W.add_zone('SW node L6','SW_5V',B,[(172.95,93.92),(175.70,93.92),(176.30,93.40),(179.20,93.40),(179.20,94.80),(172.95,94.80)],priority=22)
# ------------------------------------------------------------------ +5V: one pour from the inductor output to U4 and U5
for a,b in [((188.0,103.9),(187.4,104.5)),((187.4,104.5),(181.0,104.5)),((181.0,104.5),(179.5,104.5)),
            ((178.9,104.3),(178.9,101.5)),((178.9,101.5),(178.32,100.92)),((178.32,100.92),(177.5,100.925)),
            ((177.5,100.925),(175.5,100.925)),((175.5,100.925),(173.6,100.92)),((178.9,100.17),(178.9,101.5)),
            ((178.68,99.95),(178.9,100.17))]:
    W.drop_seg(a,b)
W.drop_zone('5V buck output L6')
W.add_zone('5V rail L6','+5V',B,[(172.85,100.12),(178.40,100.12),(178.40,99.10),(187.20,99.10),(187.20,91.00),(193.80,91.00),
                                 (193.80,105.00),(177.80,105.00),(177.80,102.00),(174.40,102.00),(174.40,101.30),(172.85,101.30)],priority=20)
# output caps: their GND pads become islands in the +5V pour, so each gets a second via to L5
for x,y in ((185.6,101.2),(186.1,103.35)):
    m=W.via_margin('GND',x,y)
    if m[0]<0: print('  !! GND via',(x,y),m)
    W.add_via('GND',x,y)
W.save(sys.argv[2])
