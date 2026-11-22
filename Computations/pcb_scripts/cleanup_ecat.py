"""Remove the step 5b EtherCAT / RBIAS / crystal routing before the checklist rework (2026-11-22):
all tracks and vias of the chip-side pair nets, RBIAS, XI/XO and the crystal-side nets, OSCVDD12, plus the
+1V2_ESC / +3V3_PHY stubs and GND stubs/vias of the old west-face decoupling and crystal caps.
usage (system python with pcbnew): cleanup_ecat.py board.kicad_pcb"""
import sys,math,pcbnew
M=pcbnew.ToMM
b=pcbnew.LoadBoard(sys.argv[1])
NETS={'ECAT_P0_TX+','ECAT_P0_TX-','ECAT_P0_RX+','ECAT_P0_RX-','ECAT_P1_TX+','ECAT_P1_TX-','ECAT_P1_RX+','ECAT_P1_RX-',
      'ESC_RBIAS','ESC_XI','ESC_XO','ESC_XO_XTAL','Net-(C117-Pad1)','Net-(C116-Pad1)','ESC_OSCVDD12'}
REGION=(135.0,101.5,146.0,113.5)                      # west face of U9
inreg=lambda x,y:REGION[0]<=x<=REGION[2] and REGION[1]<=y<=REGION[3]
gnd_pads=[]
for r,n in (('C126','2'),('C134','2'),('C128','2'),('C116','2'),('C117','2'),('C119','2'),('C120','2'),('Y1','2'),('Y1','4')):
    p=[q for q in b.FindFootprintByReference(r).Pads() if q.GetNumber()==n][0]; gnd_pads.append((M(p.GetPosition().x),M(p.GetPosition().y)))
kill=[]
for t in b.Tracks():
    n=t.GetNetname().split('/')[-1]
    s=(M(t.GetStart().x),M(t.GetStart().y)); e=(M(t.GetEnd().x),M(t.GetEnd().y))
    if n in NETS: kill.append(t); continue
    if n in ('+1V2_ESC','+3V3_PHY') and inreg(*s) and inreg(*e): kill.append(t); continue
    if n=='GND' and any(math.dist(s,g)<1.7 or math.dist(e,g)<1.7 for g in gnd_pads) and (t.GetClass()=='PCB_VIA' or math.dist(s,e)<1.8): kill.append(t)
for t in kill: b.Remove(t)
pcbnew.SaveBoard(sys.argv[1],b); print('removed',len(kill),'tracks/vias')
