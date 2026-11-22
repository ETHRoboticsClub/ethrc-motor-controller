"""TPSM861253 (RDX0007A): pads 1-4 are solder-mask defined, copper must reach >= 0.05 mm past each mask opening.
Pads 2 (SW) and 3 (VOUT) were 0.5 x 0.5 mm anchors under 1.4 x 2.2 mm openings; give them 1.5 x 2.3 mm copper.
usage: u5_pads.py --lib footprint.kicad_mod   |   u5_pads.py board.kicad_pcb   (board: system python with pcbnew)"""
import sys,re
if sys.argv[1]=='--lib':
    p=sys.argv[2]; t=open(p).read(); n=0
    for num,x in (('2','-1.15'),('3','1.15')):
        old='(pad "%s" smd rect\n\t\t(at %s 0.675)\n\t\t(size 0.5 0.5)'%(num,x); new='(pad "%s" smd rect\n\t\t(at %s 0.675)\n\t\t(size 1.5 2.3)'%(num,x)
        if old in t: t=t.replace(old,new); n+=1
    open(p,'w').write(t); print('library pads changed',n)
else:
    import pcbnew
    b=pcbnew.LoadBoard(sys.argv[1]); f=b.FindFootprintByReference('U5'); n=0
    for pd in f.Pads():
        if pd.GetNumber() in ('2','3') and pd.GetSize().x<pcbnew.FromMM(1.0):
            pd.SetSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.5),pcbnew.FromMM(2.3))); n+=1
    b.BuildConnectivity(); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(sys.argv[1],b); print('board pads changed',n)
