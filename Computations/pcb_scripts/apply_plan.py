"""Write a plan made with route.py into a board. usage (system python with pcbnew): apply_plan.py board.kicad_pcb plan.json"""
import sys,json,math,re,pcbnew
MM=pcbnew.FromMM
LAYER={'F.Cu':pcbnew.F_Cu,'B.Cu':pcbnew.B_Cu,'In1.Cu':pcbnew.In1_Cu,'In2.Cu':pcbnew.In2_Cu,'In3.Cu':pcbnew.In3_Cu,'In4.Cu':pcbnew.In4_Cu}
def drop_tracks_in_file(path,suffixes):
    t=open(path).read(); n=0
    for s in suffixes:
        for m in re.finditer(r'\n\t\(net (\d+) "[^"]*'+re.escape(s)+r'"\)',t):
            t,k=re.subn(r'\t\(segment\n(?:\t\t[^\n]*\n)*?\t\t\(net '+m.group(1)+r'\)\n(?:\t\t[^\n]*\n)*?\t\)\n','',t); n+=k
    open(path,'w').write(t); return n
def drop_segs_in_file(path,segs,tol=0.02):
    t=open(path).read(); n=0
    def rep(m):
        nonlocal n
        s=re.search(r'\(start ([-\d.]+) ([-\d.]+)\)',m.group(0)); e=re.search(r'\(end ([-\d.]+) ([-\d.]+)\)',m.group(0))
        a=(float(s.group(1)),float(s.group(2))); b=(float(e.group(1)),float(e.group(2)))
        for x1,y1,x2,y2 in segs:
            if (math.dist(a,(x1,y1))<tol and math.dist(b,(x2,y2))<tol) or (math.dist(a,(x2,y2))<tol and math.dist(b,(x1,y1))<tol): n+=1; return ''
        return m.group(0)
    t=re.sub(r'\t\(segment\n(?:\t\t[^\n]*\n)*?\t\)\n',rep,t); open(path,'w').write(t); return n
ZONE='''\t(zone
\t\t(net {code})
\t\t(net_name "{net}")
\t\t(layer "{layer}")
\t\t(uuid "{uuid}")
\t\t(name "{name}")
\t\t(hatch edge 0.5)
\t\t(priority {prio})
\t\t(connect_pads yes
\t\t\t(clearance 0)
\t\t)
\t\t(min_thickness 0.25)
\t\t(filled_areas_thickness no)
\t\t(fill yes
\t\t\t(thermal_gap 0.5)
\t\t\t(thermal_bridge_width 0.5)
\t\t)
\t\t(polygon
\t\t\t(pts
\t\t\t\t{pts}
\t\t\t)
\t\t)
\t)
'''
KEEPOUT='''\t(zone
\t\t(net 0)
\t\t(net_name "")
\t\t(layer "{layer}")
\t\t(uuid "{uuid}")
\t\t(name "{name}")
\t\t(hatch edge 0.5)
\t\t(connect_pads
\t\t\t(clearance 0)
\t\t)
\t\t(min_thickness 0.25)
\t\t(filled_areas_thickness no)
\t\t(keepout
\t\t\t(tracks not_allowed)
\t\t\t(vias not_allowed)
\t\t\t(pads allowed)
\t\t\t(copperpour not_allowed)
\t\t\t(footprints allowed)
\t\t)
\t\t(placement
\t\t\t(enabled no)
\t\t\t(sheetname "")
\t\t)
\t\t(fill
\t\t\t(thermal_gap 0.5)
\t\t\t(thermal_bridge_width 0.5)
\t\t)
\t\t(polygon
\t\t\t(pts
\t\t\t\t{pts}
\t\t\t)
\t\t)
\t)
'''
def add_zones_in_file(path,zones):
    import uuid
    t=open(path).read(); codes={m.group(2):m.group(1) for m in re.finditer(r'\n\t\(net (\d+) "([^"]*)"\)',t)}
    blocks=''
    for z in zones:
        if '(name "%s")'%z['name'] in t: sys.exit('zone exists already: '+z['name'])
        pts=' '.join('(xy %g %g)'%(x,y) for x,y in z['pts'])
        if z.get('keepout'): blocks+=KEEPOUT.format(layer=z['layer'],uuid=uuid.uuid4(),name=z['name'],pts=pts)
        else: blocks+=ZONE.format(code=codes[z['net']],net=z['net'],layer=z['layer'],uuid=uuid.uuid4(),name=z['name'],prio=z['priority'],pts=pts)
    end='\t(embedded_fonts no)\n)'; assert t.rstrip().endswith(end),'unexpected board file ending'
    k=t.rstrip().rfind(end); t=t[:k]+blocks+t[k:]; open(path,'w').write(t); return len(zones)
def main():
    board,plan=sys.argv[1:3]; p=json.load(open(plan)); txt=open(board).read()
    for v in p['vias'][:3]:
        if re.search(r'\(via\s*\(at %s %s\)'%(re.escape('%g'%v['x']),re.escape('%g'%v['y'])),txt): sys.exit('plan looks applied already: via at %s %s exists'%(v['x'],v['y']))
    if p.get('drop_nets'): print('track segments removed',drop_tracks_in_file(board,p['drop_nets']))
    if p.get('drop_segs'): print('single segments removed',drop_segs_in_file(board,p['drop_segs']),'of',len(p['drop_segs']))
    if p.get('zones'): print('zones added',add_zones_in_file(board,p['zones']))
    b=pcbnew.LoadBoard(board); R={f.GetReference():f for f in b.GetFootprints()}
    P=lambda x,y: pcbnew.VECTOR2I(MM(x),MM(y))
    for m in p.get('move',[]): R[m['ref']].SetPosition(P(m['x'],m['y']))
    for m in p.get('place',[]):
        fp=R[m['ref']]
        if m.get('bottom') and not fp.IsFlipped(): fp.Flip(fp.GetPosition(),pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        fp.SetPosition(P(m['x'],m['y'])); best=None
        for rot in (0,90,180,270,45,135,225,315):
            fp.SetOrientationDegrees(rot)
            q=[d for d in fp.Pads() if d.GetNumber()==m['pad']][0].GetPosition(); d=math.hypot(q.x/1e6-m['px'],q.y/1e6-m['py'])
            if best is None or d<best[0]: best=(d,rot)
        fp.SetOrientationDegrees(best[1]); assert best[0]<0.05,(m,best)
    for v in p['vias']:
        o=pcbnew.PCB_VIA(b); o.SetViaType(pcbnew.VIATYPE_THROUGH); o.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu); o.SetPosition(P(v['x'],v['y']))
        o.SetWidth(pcbnew.F_Cu,MM(v.get('d',0.55))); o.SetDrill(MM(v.get('drill',0.25))); o.SetNet(b.FindNet(v['net'])); o.SetIsFree(True); b.Add(o)
    n=0
    for t in p['tracks']:
        net=b.FindNet(t['net']); assert net is not None,t['net']
        for a,c in zip(t['pts'],t['pts'][1:]):
            o=pcbnew.PCB_TRACK(b); o.SetStart(P(*a)); o.SetEnd(P(*c)); o.SetWidth(MM(t['w'])); o.SetLayer(LAYER[t['layer']]); o.SetNet(net); b.Add(o); n+=1
    b.BuildConnectivity(); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(board,b)
    print('applied: moves',len(p.get('move',[]))+len(p.get('place',[])),'vias',len(p['vias']),'segments',n)
main()
