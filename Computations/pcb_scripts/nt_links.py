"""Add the 0.2 mm link from each Kelvin net tie's power-side pad into the shunt or source pad it senses.
Each link ends exactly on the tie pad's centre. usage (system python with pcbnew): nt_links.py board.kicad_pcb [dx]"""
import sys,pcbnew
MM=pcbnew.FromMM
POWER=('GND','SRC_LS','PH')
# tie, y of the far end of the link (inside the shunt or source pad)
TARGET={'NT3':84.65,'NT6':84.65,'NT9':84.65,'NT5':86.35,'NT7':86.35,'NT10':86.35,'NT11':74.15,'NT8':74.15,'NT4':74.15}
def main():
    b=pcbnew.LoadBoard(sys.argv[1]); dx=float(sys.argv[2]) if len(sys.argv)>2 else 0.0
    R={f.GetReference():f for f in b.GetFootprints()}; n=0
    for ref,ty in TARGET.items():
        pad=[p for p in R[ref].Pads() if p.GetNetname().split('/')[-1].startswith(POWER)][0]
        sense=[p for p in R[ref].Pads() if p is not pad and not p.GetNetname().split('/')[-1].startswith(POWER)][0]
        c=pad.GetPosition(); away=-1 if sense.GetPosition().x>c.x else 1
        t=pcbnew.PCB_TRACK(b); t.SetStart(c); t.SetEnd(pcbnew.VECTOR2I(c.x+MM(away*dx),MM(ty)))
        t.SetWidth(MM(0.2)); t.SetLayer(pcbnew.F_Cu); t.SetNet(pad.GetNet()); b.Add(t); n+=1
    b.BuildConnectivity(); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(sys.argv[1],b); print('links added',n)
main()
