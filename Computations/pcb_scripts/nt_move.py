"""Move the Kelvin net ties onto the shunts and the high-side source pads.
Each tie lies in the gap next to its pad with its sense copper 0.2 mm clear of the pad; the 0.3 mm link from the
tie's power-side pad into the pad is left for routing (KiCad 9.0.9 reports a track entering this footprint's own
pad as a short on some ties, depending on check order).
usage (system python with pcbnew): nt_move.py board.kicad_pcb"""
import sys,math,pcbnew
MM=pcbnew.FromMM
# shunt centre, exit side of the sense pair (+1 east, -1 west), P tie, N tie
SHUNTS=[((166.0,85.5),-1,'NT3','NT5'),((158.0,85.5),-1,'NT6','NT7'),((124.5,85.5),+1,'NT9','NT10')]
# switch-node ties below the last source pad of each high-side FET: ref, x of the PH circle, y, spacing to the SH circle (east)
HS=[('NT11',134.3,74.82,0.8),('NT8',144.4,74.80,0.6),('NT4',176.8,74.82,0.8)]
POWER=('GND','SRC_LS','PH')
def circles(fp):
    return [(p.GetNetname(),p.GetPosition().x/1e6,p.GetPosition().y/1e6) for p in fp.Pads() if p.GetShape()==pcbnew.PAD_SHAPE_CIRCLE]
def place(fp,pwr,sense):
    fp.SetLocked(False); fp.SetPosition(pcbnew.VECTOR2I(MM((pwr[0]+sense[0])/2),MM((pwr[1]+sense[1])/2))); best=None
    ispwr=lambda n:n.split('/')[-1].startswith(POWER)
    for rot in (0,90,180,-90):
        fp.SetOrientationDegrees(rot)
        err=sum(math.hypot(x-(pwr if ispwr(n) else sense)[0],y-(pwr if ispwr(n) else sense)[1]) for n,x,y in circles(fp))
        if best is None or err<best[0]: best=(err,rot)
    fp.SetOrientationDegrees(best[1]); assert best[0]<0.01,(fp.GetReference(),best)
def main():
    b=pcbnew.LoadBoard(sys.argv[1]); R={f.GetReference():f for f in b.GetFootprints()}
    for (cx,cy),e,pref,nref in SHUNTS:
        for ref,sgn in ((pref,-1),(nref,+1)):
            pwr=(cx+e*0.20,cy+sgn*0.33); sense=(cx+e*0.60,cy+sgn*0.33); place(R[ref],pwr,sense)
            print(ref,'power pad',pwr,'sense pad',(round(sense[0],2),sense[1]))
    for ref,x,y,d in HS:
        place(R[ref],(x,y),(x+d,y)); print(ref,'power pad',(x,y),'sense pad',(round(x+d,2),y))
    b.BuildConnectivity(); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(sys.argv[1],b)
main()
