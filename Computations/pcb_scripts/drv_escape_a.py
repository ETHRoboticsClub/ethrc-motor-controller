"""Step 3, phase A, second slice: free the DRV8353 north-east pin row and route the five long driver nets.
- C91 (VCP-VM), C95 (VM 100 nF), C92 (VM bulk) leave the escape channel and line up south of it (y = 90.2).
- GLA, SHA, GHA run on L1 as a three-track highway (y = 88.07 / 88.57 / 89.07) and up the corridor east of Q11.
- SA+/SA- change to L6 next to the pins and next to the shunt (the pair has to swap sides once; the swap
  is the loop of SA- around the SA+ via at the shunt end).
- Snubber A parts move to the bottom, directly under the drain/source boundary of their FET.
usage (system python with pcbnew): drv_escape_a.py board.kicad_pcb"""
import sys,math,re,pcbnew
MM=pcbnew.FromMM
Q=0.70711
def drop_tracks_in_file(path,suffixes):
    """Remove the track segments of the given nets at text level (board.GetTracks() is broken in pcbnew 9.0.9)."""
    t=open(path).read(); codes=[m.group(1) for s in suffixes for m in re.finditer(r'\n\t\(net (\d+) "[^"]*'+re.escape(s)+r'"\)',t)]
    n=0
    for c in codes:
        t,k=re.subn(r'\t\(segment\n(?:\t\t[^\n]*\n)*?\t\t\(net '+c+r'\)\n(?:\t\t[^\n]*\n)*?\t\)\n','',t); n+=k
    # the switch-node sense link NT4 -> TP61 now carries the high-side gate return: 0.25 -> 0.4 mm
    t=t.replace('(start 177.6 74.82)\n\t\t(end 180.9 74.85)\n\t\t(width 0.25)','(start 177.6 74.82)\n\t\t(end 180.9 74.85)\n\t\t(width 0.4)')
    open(path,'w').write(t); return n
def main():
    print('old snubber links removed',drop_tracks_in_file(sys.argv[1],('SNUBH_A','SNUBL_A')))
    b=pcbnew.LoadBoard(sys.argv[1]); R={f.GetReference():f for f in b.GetFootprints()}
    P=lambda x,y: pcbnew.VECTOR2I(MM(x),MM(y))
    def pad(ref,num,shape=None):
        ps=[p for p in R[ref].Pads() if p.GetNumber()==num and (shape is None or p.GetShape()==shape)]
        p=ps[0]; return (p.GetPosition().x/1e6,p.GetPosition().y/1e6),p.GetNet()
    def net_of(ref,num): return pad(ref,num)[1]
    n=[0,0]
    def route(net,w,pts,layer=pcbnew.F_Cu):
        for a,c in zip(pts,pts[1:]):
            t=pcbnew.PCB_TRACK(b); t.SetStart(P(*a)); t.SetEnd(P(*c)); t.SetWidth(MM(w)); t.SetLayer(layer); t.SetNet(net); b.Add(t); n[0]+=1
    def via(net,x,y):
        v=pcbnew.PCB_VIA(b); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu)
        v.SetPosition(P(x,y)); v.SetWidth(pcbnew.F_Cu,MM(0.55)); v.SetDrill(MM(0.25)); v.SetNet(net); v.SetIsFree(True); b.Add(v); n[1]+=1
        return (x,y)
    def place(ref,x,y,want,bottom=False):
        """Move a footprint; choose the rotation that puts pad `want[0]` nearest to point want[1]."""
        fp=R[ref]
        if bottom and not fp.IsFlipped(): fp.Flip(fp.GetPosition(),pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        fp.SetPosition(P(x,y)); best=None
        for rot in (0,90,180,270):
            fp.SetOrientationDegrees(rot); (px,py),_=pad(ref,want[0]); d=math.hypot(px-want[1][0],py-want[1][1])
            if best is None or d<best[0]: best=(d,rot)
        fp.SetOrientationDegrees(best[1]); assert best[0]<0.05,(ref,best)
    def out(num,d):                     # point d mm outward (north-east) of a pin 1..10 centre
        (x,y),_=pad('U6',num); return (x+Q*d,y-Q*d)
    def ne_to_y(num,y1):                # follow the pin's outward diagonal until it reaches y1
        (x,y),_=pad('U6',num); return (x+(y-y1),y1)
    B=pcbnew.B_Cu
    # ---------------- placement
    place('C91',154.2,90.2,('2',(153.6,90.2)))          # VCP pad west, facing pin 5; VM pad east
    place('C95',157.1,90.2,('1',(156.5,90.2)))          # VM pad west, GND pad east
    place('C92',160.4,91.75,('1',(160.4,90.3)))         # VM pad north, next to the S2E bus via
    for ref,x,y in (('TP41',162.2,91.8),('TP57',183.2,75.3),('TP68',151.38,87.76)): R[ref].SetPosition(P(x,y))
    place('C98',175.0,72.65,('1',(175.0,72.25)),bottom=True)   # PHA pad north (under the source row)
    place('R21',175.0,74.85,('2',(175.0,75.75)),bottom=True)   # +VBAT pad south (under the drain edge)
    place('C99',166.4,79.75,('2',(166.4,79.35)),bottom=True)   # PHA pad north (under the drain edge)
    place('R22',166.4,81.95,('1',(166.4,82.85)),bottom=True)   # SRC_LS_A pad south (under the source row)
    # ---------------- nets
    gla=net_of('U6','8'); sha=net_of('U6','7'); gha=net_of('U6','6'); vcp=net_of('U6','5'); vm=net_of('U6','4')
    sap=net_of('U6','9'); san=net_of('U6','10'); gnd=b.FindNet('GND'); pha=net_of('C98','1'); src=net_of('R22','1')
    snh=net_of('R21','1'); snl=net_of('R22','2')
    # ---------------- gate highway on L1
    W=0.28; YG,YS,YH=88.07,88.57,89.07
    tp60,_=pad('TP60','1'); tp61,_=pad('TP61','1'); tp59,_=pad('TP59','1')
    route(gla,W,[pad('U6','8')[0],ne_to_y('8',YG),(tp60[0],YG),tp60])
    route(sha,W,[pad('U6','7')[0],ne_to_y('7',YS),(164.45,YS),(164.88,89.0)])
    route(sha,0.4,[(164.88,89.0),(180.4,89.0),(180.9,88.5),tp61])
    route(gha,W,[pad('U6','6')[0],ne_to_y('6',YH),(164.07,YH),(164.62,89.62)])
    route(gha,0.4,[(164.62,89.62),(180.93,89.62),(181.55,89.0),(181.55,70.95)])
    route(gha,0.25,[(181.55,70.95),(179.95,69.35),(179.95,68.45),(tp59[0],68.45),tp59])
    # ---------------- charge pump and VM at the driver
    c91v,_=pad('C91','2'); c91m,_=pad('C91','1'); c95m,_=pad('C95','1'); c95g,_=pad('C95','2'); c92m,_=pad('C92','1'); c92g,_=pad('C92','2')
    o5=out('5',0.75); route(vcp,0.25,[pad('U6','5')[0],o5,(c91v[0]-0.3,o5[1]),(c91v[0],c91v[1]+0.1)])
    YL=90.98; o4=ne_to_y('4',YL); o3=ne_to_y('3',YL)
    route(vm,0.2,[pad('U6','4')[0],o4,(c91m[0]-0.35,YL),(c91m[0],YL-0.35),c91m]); route(vm,0.2,[pad('U6','3')[0],o3])
    route(vm,0.4,[c91m,c95m]); via(vm,(c91m[0]+c95m[0])/2,90.2)
    route(gnd,0.4,[c95g,via(gnd,158.65,90.25)])
    route(vm,0.6,[c92m,(161.8,c92m[1]),(162.2,90.7)]); route(vm,0.3,[(162.2,90.7),pad('TP41','1')[0]])
    route(gnd,0.4,[c92g,via(gnd,160.4,94.45)])
    # ---------------- Kelvin pair of shunt A: L1 stubs, L6 run
    v9=via(sap,151.831,88.034); v10=via(san,150.735,88.281)
    route(sap,0.2,[pad('U6','9')[0],(v9[0],v9[1]+0.282),v9,pad('TP68','1')[0]])
    route(san,0.2,[pad('U6','10')[0],(v10[0],v10[1]+0.424),v10,pad('TP69','1')[0]])
    sp,_=pad('NT3','2'); sn,_=pad('NT5','1'); vsp=via(sap,164.4,84.95); vsn=via(san,164.4,85.95)
    route(sap,0.2,[sp,(164.75,sp[1]),vsp]); route(san,0.2,[sn,(164.75,sn[1]),vsn])
    route(sap,0.2,[v9,(v9[0],84.65),(v9[0]+0.2,84.45),(163.4,84.45),(163.9,84.95),vsp],B)
    route(san,0.2,[v10,(151.431,87.585),(151.431,84.25),(151.631,84.05),(164.5,84.05),(165.1,84.65),(165.1,85.25),vsn],B)
    # ---------------- snubbers A on the bottom, with their own vias to the top copper
    c98p,_=pad('C98','1'); c98s,_=pad('C98','2'); r21s,_=pad('R21','1'); route(snh,0.3,[c98s,r21s],B)
    for x in (174.1,175.9): route(pha,0.3,[c98p,via(pha,x,72.5)],B)
    c99s,_=pad('C99','1'); r22s,_=pad('R22','2'); r22p,_=pad('R22','1'); route(snl,0.3,[c99s,r22s],B)
    for x in (165.25,167.55): route(src,0.4,[r22p,via(src,x,82.75)],B)
    b.BuildConnectivity(); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(sys.argv[1],b)
    print('track segments added',n[0],'vias added',n[1])
main()
