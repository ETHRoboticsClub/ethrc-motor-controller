"""Step 6 preparation (approved 2026-11-22):
- DRV_CS moved from U1 pin 24 (PB0) to pin 56 (PB3) in the schematic; the board got it by Update PCB from Schematic.
- R1/R2 (DRV SCLK/MOSI series resistors) turn 180 degrees in place, so the MCU pad faces U1.
- R50/R52 (EEPROM I2C pull-ups) leave the passage between U1's west corner and U9 and go under U8 (bottom).
- C113 (U7's 1 uF decoupling, bottom) moves 2.1 mm east, 0.1 mm north and turns 90 deg: +3V3 pad towards U7's north side, GND pad towards
  U6's thermal pad; this frees the via sites for the DRV SPI at U6's south-west face and the L6 path of MISO/MOSI.
- R91 (ESC_IRQ pull-up, bottom) turns 135 deg about its ESC_IRQ pad, out of the via spot west of the PWM lanes.
- C129 (U9's 100 nF) moves 0.3 mm along U9's face and 0.25 mm towards U9, so four control lines pass U1's west corner on L1.
- MGH/MGL are no longer wired (schematic: the firmware reads the MA732's flags in register 27 over SPI, which also
  gives the datasheet's corrected MGL); U1 pins 9/10 and U7 pins 11/16 become no-connect.
usage: plan_s6_prep.py board.kicad_pcb plan.json"""
import sys,os,math
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from route import World
W=World(sys.argv[1])
for ref in ('R1','R2'):                                  # pad 2 (MCU side) goes where pad 1 was
    p1=[p for p in W.R[ref].pads if p.num=='1'][0]; p2=[p for p in W.R[ref].pads if p.num=='2'][0]
    W.place2(ref,round((p1.x+p2.x)/2,4),round((p1.y+p2.y)/2,4),'2',(p1.x,p1.y))
# bottom, under U8's SE side: signal pad (2) west toward U8, +3V3 pad (1) east
W.place2('R50',139.7,120.3,'2',(139.05,120.3),bottom=True)
W.place2('R52',139.7,121.7,'2',(139.05,121.7),bottom=True)
W.place2('C113',151.2,96.9,'1',(151.2,97.3),bottom=True)
W.shift('C129',151.071,108.505)                             # 0.3 mm along U9's face towards C130 and 0.25 mm towards U9 (courtyards clear)
W.plan['pad_nets']=[dict(ref='U1',pad='9',net='unconnected-(U1B-PC1-Pad9)'),dict(ref='U1',pad='10',net='unconnected-(U1B-PC2-Pad10)'),
                    dict(ref='U7',pad='11',net='unconnected-(U7-MGL-Pad11)'),dict(ref='U7',pad='16',net='unconnected-(U7-MGH-Pad16)')]
p2=[p for p in W.R['R91'].pads if p.num=='2'][0]                  # R91 turned 135 deg about its ESC_IRQ pad
W.place2('R91',round(p2.x+0.65*math.cos(math.radians(135)),4),round(p2.y+0.65*math.sin(math.radians(135)),4),'2',(p2.x,p2.y),bottom=True)
W.plan['lock']=['R1','R2','R50','R52','C113','C129','R91']
W.save(sys.argv[2]); print('prep plan written')
