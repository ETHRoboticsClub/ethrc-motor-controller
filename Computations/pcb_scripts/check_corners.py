"""List track corners of 90 degrees or sharper (two segments of one net and layer meeting at a point with no pad or via there).
usage (system python with pcbnew): check_corners.py board.kicad_pcb [x0 y0 x1 y1]"""
import sys,math,collections,pcbnew
M=pcbnew.ToMM
b=pcbnew.LoadBoard(sys.argv[1]); box=list(map(float,sys.argv[2:6])) if len(sys.argv)>5 else None
ends=collections.defaultdict(list); vias=set()
for t in b.Tracks():
    if t.GetClass()=='PCB_VIA': vias.add((round(M(t.GetPosition().x),3),round(M(t.GetPosition().y),3))); continue
    s=(round(M(t.GetStart().x),3),round(M(t.GetStart().y),3)); e=(round(M(t.GetEnd().x),3),round(M(t.GetEnd().y),3))
    if s==e: continue
    k=(t.GetNetname(),t.GetLayer())
    ends[k+(s,)].append(e); ends[k+(e,)].append(s)
pads=[]
for f in b.GetFootprints():
    for p in f.Pads(): pads.append(p)
def on_pad(net,pt):
    v=pcbnew.VECTOR2I(pcbnew.FromMM(pt[0]),pcbnew.FromMM(pt[1]))
    return any(p.GetNetname()==net and p.HitTest(v) for p in pads)
n=0
for (net,lay,pt),others in ends.items():
    if len(others)!=2 or pt in vias: continue
    if box and not (box[0]<=pt[0]<=box[2] and box[1]<=pt[1]<=box[3]): continue
    a,c=others; u=(a[0]-pt[0],a[1]-pt[1]); w=(c[0]-pt[0],c[1]-pt[1])
    ang=math.degrees(math.acos(max(-1,min(1,(u[0]*w[0]+u[1]*w[1])/(math.hypot(*u)*math.hypot(*w))))))
    if ang<=90.5 and not on_pad(net,pt):
        n+=1; print('%6.1f deg  %-22s %s at (%.2f, %.2f)'%(ang,net.split('/')[-1],b.GetLayerName(lay)[:2],pt[0],pt[1]))
print('corners <= 90 deg:',n)
