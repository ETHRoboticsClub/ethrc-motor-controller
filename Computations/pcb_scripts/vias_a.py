"""Step 3, phase A: via-in-pad on Q11 (high side, +VBAT) and Q1 (low side, PHA), bulk-cap vias, shunt GND field.
usage (system python with pcbnew): vias_a.py board.kicad_pcb"""
import sys,math,pcbnew
MM=pcbnew.FromMM
TL='/Project Architecture/Motor Control - Top Level/Motor Control - Inverter/'
GU=(-2.1,-0.7,0.7,2.1); GV=(-1.95,-1.3,-0.65,0.0,0.65,1.3,1.95); PCY=-0.785
def grid(fp):
    p=fp.GetPosition(); a=math.radians(fp.GetOrientationDegrees()); c,s=math.cos(a),math.sin(a)
    return [((p.x/1e6)+u*c+(PCY+v)*s,(p.y/1e6)-u*s+(PCY+v)*c) for u in GU for v in GV]
def main():
    b=pcbnew.LoadBoard(sys.argv[1]); R={f.GetReference():f for f in b.GetFootprints()}
    V=[]
    V+=[('+VBAT',x,y,'Q11 drain') for x,y in grid(R['Q11'])]
    V+=[(TL+'PHA',x,y,'Q1 drain') for x,y in grid(R['Q1'])]
    V+=[('+VBAT',173.7+k,82.9,'bus row at S1E caps') for k in range(6)]
    V+=[('GND',171.7+2*k,86.1,'S1E caps GND') for k in range(5)]
    V+=[('GND',169.8,76.6+2*k,'HG2 caps GND') for k in range(4)]
    V+=[('GND',182.4,76.6+2*k,'HG3 caps GND') for k in range(4)]
    V+=[('+VBAT',184.1,77.6,'EE caps'),('+VBAT',184.1,81.8,'EE caps'),('GND',184.1,80.4,'EE caps'),('GND',184.1,84.6,'EE caps')]
    V+=[('GND',162.2,87.9,'S2E caps'),('GND',164.2,87.9,'S2E caps'),('+VBAT',162.2,90.7,'S2E caps'),('+VBAT',164.2,90.7,'S2E caps')]
    V+=[('GND',x,y,'R20 return field') for x in (167.4,168.1,168.8) for y in (86.2,86.9,87.6,88.3)]
    V+=[('GND',x,88.3,'R20 return field') for x in (165.3,166.0,166.7)]
    have={(round(v.GetPosition().x/1e4),round(v.GetPosition().y/1e4)) for v in b.GetTracks() if v.Type()==pcbnew.PCB_VIA_T}
    n=0
    for net,x,y,why in V:
        if (round(x*100),round(y*100)) in have: continue
        v=pcbnew.PCB_VIA(b); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu)
        v.SetPosition(pcbnew.VECTOR2I(MM(x),MM(y))); v.SetWidth(pcbnew.F_Cu,MM(0.55)); v.SetDrill(MM(0.25)); v.SetNet(b.FindNet(net)); v.SetIsFree(True); b.Add(v); n+=1
    b.BuildConnectivity(); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(sys.argv[1],b)
    import collections; print('vias added',n,dict(collections.Counter(w for _,_,_,w in V)))
main()
