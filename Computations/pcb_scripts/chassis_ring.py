"""CHASSIS ring as in the Amulet controller: a 1.5 mm CHASSIS band along the board edge on all six layers
(0.3 mm inside the edge, 0.5 mm zone clearance), bulges around the mounting holes H1-H4 and the XT60 pegs,
top-layer fingers to the connector shell pads and to the hole RC parts, and stitching vias around the ring.
The ECAT_ISOLATION rule area is trimmed so the ring and the J9/J10 shell fingers can fill.
usage (system python with pcbnew): chassis_ring.py board.kicad_pcb"""
import sys,os,math,pcbnew
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from route import World
F=pcbnew.FromMM; M=pcbnew.ToMM
CX,CY=150.0,100.0
R_OUT,R_IN,R_VIA=43.7,42.2,42.95      # ring band and via circle (board radius 44 mm)
HOLES={'H1':(162.0,63.0),'H2':(170.0,133.5),'H3':(138.0,63.0),'H4':(129.0,133.5)}; R_BULGE=3.7
PEGS=[(164.98,138.22),(134.52,138.22)]                       # XT60 J2/J3 MP2, plated, all layers
RADIAL=[('J1','MP1'),('J1','MP2'),('J12','MP1'),('J12','MP2'),('J7','MP1'),('J7','MP2'),('J8','MP1'),('J8','MP2'),
        ('J9','MP1'),('J9','MP2'),('J10','MP1'),('J10','MP2'),('C153','1'),('R75','1')]
HOLE_RC=[('R73','1',(141.2,63.1)),('R76','1',(158.8,63.1))]   # each finger also runs over C152.1 / C114.1
FIDUCIALS=[(150.0,57.5),(188.5,82.5),(112.0,82.5)]
VIA_PITCH=2.5
def circle(cx,cy,r):
    c=pcbnew.SHAPE_LINE_CHAIN(); n=max(32,int(2*math.pi*r/0.2))
    for k in range(n): a=2*math.pi*k/n; c.Append(F(cx+r*math.cos(a)),F(cy+r*math.sin(a)))
    c.SetClosed(True); p=pcbnew.SHAPE_POLY_SET(); p.AddOutline(c); return p
def bar(a,b,w):
    (ax,ay),(bx,by)=a,b; l=math.hypot(bx-ax,by-ay); ux,uy=(bx-ax)/l,(by-ay)/l; nx,ny=-uy*w/2,ux*w/2
    c=pcbnew.SHAPE_LINE_CHAIN()
    for x,y in ((ax+nx,ay+ny),(bx+nx,by+ny),(bx-nx,by-ny),(ax-nx,ay-ny)): c.Append(F(x),F(y))
    c.SetClosed(True); p=pcbnew.SHAPE_POLY_SET(); p.AddOutline(c); return p
def radial_end(x,y,r=R_IN+0.6):
    a=math.atan2(y-CY,x-CX); return (CX+r*math.cos(a),CY+r*math.sin(a))
def cu_layers(): s=pcbnew.LSET(); [s.AddLayer(l) for l in (pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu,pcbnew.In4_Cu,pcbnew.B_Cu)]; return s
def add_zone(b,name,layers,poly,prio,net):
    z=pcbnew.ZONE(b); z.SetLayerSet(layers); z.SetNet(net); z.SetZoneName(name); z.SetAssignedPriority(prio)
    z.SetLocalClearance(F(0.5)); z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL); z.SetMinThickness(F(0.25))
    for i in range(poly.OutlineCount()):
        z.Outline().AddOutline(poly.Outline(i))
        for h in range(poly.HoleCount(i)): z.Outline().AddHole(poly.Hole(i,h))
    b.Add(z); return z
def main():
    path=sys.argv[1]; W=World(path); b=pcbnew.LoadBoard(path); net=b.FindNet('CHASSIS')
    R={f.GetReference():f for f in b.GetFootprints()}
    def padpos(ref,num): p=[q for q in R[ref].Pads() if q.GetNumber()==num][0]; return (M(p.GetPosition().x),M(p.GetPosition().y)),p
    # ---------------------------------------------------------------- ring, hole bulges and XT60 pegs (all layers)
    ring=circle(CX,CY,R_OUT); ring.BooleanSubtract(circle(CX,CY,R_IN))
    for x,y in HOLES.values(): ring.BooleanAdd(circle(x,y,R_BULGE))
    for x,y in PEGS: ring.BooleanAdd(circle(x,y,0.9)); ring.BooleanAdd(bar((x,y),radial_end(x,y),1.2))
    ring.Simplify()
    print('ring: outlines',ring.OutlineCount(),'holes',ring.HoleCount(0))
    add_zone(b,'CHASSIS ring',cu_layers(),ring,100,net)
    # ---------------------------------------------------------------- top-layer fingers
    fingers=[]
    for ref,num in RADIAL:
        (x,y),p=padpos(ref,num); w=1.0 if ref.startswith('J') else 0.6
        fingers.append((ref+'.'+num,bar((x,y),radial_end(x,y),w)))
    for ref,num,to in HOLE_RC:
        (x,y),p=padpos(ref,num); fingers.append((ref+'.'+num,bar((x,y),to,0.6)))
    top=pcbnew.LSET(); top.AddLayer(pcbnew.F_Cu)
    for name,poly in fingers: add_zone(b,'CHASSIS finger '+name,top,poly,101,net)
    # ---------------------------------------------------------------- ECAT_ISOLATION: keep it inside r = 42.0 and off the J9/J10 shell fingers
    iso=[z for z in b.Zones() if z.GetIsRuleArea() and z.GetZoneName()=='ECAT_ISOLATION'][0]
    keep=pcbnew.SHAPE_POLY_SET(iso.Outline()); keep.BooleanIntersection(circle(CX,CY,42.0))
    for name,poly in fingers:
        if name.split('.')[0] in ('J9','J10'):
            q=pcbnew.SHAPE_POLY_SET(poly); q.Inflate(F(0.3),pcbnew.CORNER_STRATEGY_CHAMFER_ALL_CORNERS,F(0.01)); keep.BooleanSubtract(q)
    keep.Simplify(); iso.Outline().RemoveAllContours()
    for i in range(keep.OutlineCount()):
        iso.Outline().AddOutline(keep.Outline(i))
        for h in range(keep.HoleCount(i)): iso.Outline().AddHole(keep.Hole(i,h))
    # ---------------------------------------------------------------- stitching vias on the ring
    n=int(2*math.pi*R_VIA/VIA_PITCH); placed=[]; skipped=0
    for k in range(n):
        a=2*math.pi*k/n; x,y=round(CX+R_VIA*math.cos(a),3),round(CY+R_VIA*math.sin(a),3)
        if any(math.dist((x,y),f)<1.7 for f in FIDUCIALS) or any(math.dist((x,y),h)<R_BULGE+0.3 for h in HOLES.values()): skipped+=1; continue
        m=W.via_margin('CHASSIS',x,y)
        if m[0]<0.05: skipped+=1; print('  via skipped at (%.2f, %.2f): %.2f mm against %s'%(x,y,m[0],m[1])); continue
        W.add_via('CHASSIS',x,y,check=False); placed.append((x,y))
        v=pcbnew.PCB_VIA(b); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu); v.SetPosition(pcbnew.VECTOR2I(F(x),F(y)))
        v.SetWidth(pcbnew.F_Cu,F(0.55)); v.SetDrill(F(0.25)); v.SetNet(net); v.SetIsFree(True); b.Add(v)
    print('stitching vias',len(placed),'skipped',skipped)
    b.BuildConnectivity(); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(path,b)
main()
