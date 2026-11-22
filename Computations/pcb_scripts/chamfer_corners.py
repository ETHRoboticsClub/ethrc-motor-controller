"""Replace track corners of 90 degrees or sharper by a 45-degree chamfer (best practice: no right-angle corners).
Only plain corners: exactly two segments of one net and layer meet, no pad or via at the point.
Chamfer leg = min(cmax, 45 % of the shorter segment). Zones are refilled. Run DRC afterwards.
usage (system python with pcbnew): chamfer_corners.py board.kicad_pcb [cmax_mm=0.4]"""
import sys,math,collections,pcbnew
M=pcbnew.ToMM; F=pcbnew.FromMM
b=pcbnew.LoadBoard(sys.argv[1]); cmax=float(sys.argv[2]) if len(sys.argv)>2 else 0.4
key=lambda v:(round(M(v.x),3),round(M(v.y),3))
ends=collections.defaultdict(list); vias=set(); tracks=[]
for t in b.Tracks():
    if t.GetClass()=='PCB_VIA': vias.add(key(t.GetPosition())); continue
    if t.GetClass()!='PCB_TRACK': continue
    tracks.append(t); ends[(t.GetNetCode(),t.GetLayer(),key(t.GetStart()))].append((t,'s')); ends[(t.GetNetCode(),t.GetLayer(),key(t.GetEnd()))].append((t,'e'))
pads=[p for f in b.GetFootprints() for p in f.Pads()]
def on_pad(code,v): return any(p.GetNetCode()==code and p.HitTest(v) for p in pads)
n=0; done=set()
for (code,lay,pt),lst in list(ends.items()):
    if len(lst)!=2 or pt in vias: continue
    (t1,w1),(t2,w2)=lst
    if t1 is t2 or id(t1) in done or id(t2) in done: continue
    P=pcbnew.VECTOR2I(F(pt[0]),F(pt[1]))
    A=t1.GetEnd() if w1=='s' else t1.GetStart(); C=t2.GetEnd() if w2=='s' else t2.GetStart()
    u=(M(A.x)-pt[0],M(A.y)-pt[1]); w=(M(C.x)-pt[0],M(C.y)-pt[1]); lu,lw=math.hypot(*u),math.hypot(*w)
    if lu<1e-3 or lw<1e-3: continue
    ang=math.degrees(math.acos(max(-1,min(1,(u[0]*w[0]+u[1]*w[1])/(lu*lw)))))
    if ang>90.5 or on_pad(code,P): continue
    c=min(cmax,0.45*lu,0.45*lw)
    if c<0.05: continue
    P1=pcbnew.VECTOR2I(F(pt[0]+u[0]/lu*c),F(pt[1]+u[1]/lu*c)); P2=pcbnew.VECTOR2I(F(pt[0]+w[0]/lw*c),F(pt[1]+w[1]/lw*c))
    (t1.SetStart if w1=='s' else t1.SetEnd)(P1); (t2.SetStart if w2=='s' else t2.SetEnd)(P2)
    nt=pcbnew.PCB_TRACK(b); nt.SetStart(P1); nt.SetEnd(P2); nt.SetWidth(min(t1.GetWidth(),t2.GetWidth())); nt.SetLayer(lay); nt.SetNetCode(code); b.Add(nt)
    done.add(id(t1)); done.add(id(t2)); n+=1
b.BuildConnectivity(); pcbnew.ZONE_FILLER(b).Fill(b.Zones())          # refill: old fills would clash with the new chamfers
pcbnew.SaveBoard(sys.argv[1],b); print('chamfered',n,'corners')
