"""Step 3, phase A: local gate networks at the FETs, switch-node sense exit, snubber links, DRV8353 local caps.
The five long runs from the driver to phase A (GHA, SHA, GLA, SA+, SA-) are not included: the driver's
north-east pins are walled in by C91/C95/C92 (see the review note).
usage (system python with pcbnew): routes_a.py board.kicad_pcb"""
import sys,math,pcbnew
MM=pcbnew.FromMM
def main():
    b=pcbnew.LoadBoard(sys.argv[1]); R={f.GetReference():f for f in b.GetFootprints()}
    def pad(ref,num,shape=None):
        ps=[p for p in R[ref].Pads() if p.GetNumber()==num and (shape is None or p.GetShape()==shape)]
        p=ps[0]; return (p.GetPosition().x/1e6,p.GetPosition().y/1e6),p.GetNet()
    Q=0.70711; NORMAL={0:(Q,-Q),1:(-Q,-Q),2:(-Q,Q),3:(Q,Q)}
    def outward(ref,num,d):
        (x,y),net=pad(ref,num); nx,ny=NORMAL[(int(num)-1)//10]; return (x+nx*d,y+ny*d)
    def inward(ref,num,d): return outward(ref,num,-d)
    n=0
    def route(net,w,pts):
        nonlocal n
        for a,c in zip(pts,pts[1:]):
            t=pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(MM(a[0]),MM(a[1]))); t.SetEnd(pcbnew.VECTOR2I(MM(c[0]),MM(c[1])))
            t.SetWidth(MM(w)); t.SetLayer(pcbnew.F_Cu); t.SetNet(net); b.Add(t); n+=1
    def via(net,x,y):
        v=pcbnew.PCB_VIA(b); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu)
        v.SetPosition(pcbnew.VECTOR2I(MM(x),MM(y))); v.SetWidth(pcbnew.F_Cu,MM(0.55)); v.SetDrill(MM(0.25)); v.SetNet(net); v.SetIsFree(True); b.Add(v)
    # --- high side A: gate resistor network at Q11 (TP59 moved north of D4)
    R['TP59'].SetPosition(pcbnew.VECTOR2I(MM(177.72),MM(68.15)))
    d42,fgha=pad('D4','2'); r181,_=pad('R18','1'); g11,_=pad('Q11','1')
    route(fgha,0.4,[d42,r181,(r181[0],72.3),(g11[0],73.0),g11])
    d41,gha=pad('D4','1'); r182,_=pad('R18','2'); tp59,_=pad('TP59','1')
    route(gha,0.4,[d41,r182]); route(gha,0.25,[d41,tp59])
    # --- switch-node sense: tie pad to the test point in the gate corridor (exit under the FET edge)
    sh,sha=pad('NT4','1',pcbnew.PAD_SHAPE_CIRCLE); tp61,_=pad('TP61','1'); route(sha,0.25,[sh,tp61])
    # --- low side A: gate resistor network at Q1
    g1,fgla=pad('Q1','1'); r192,_=pad('R19','2'); d52,_=pad('D5','2'); d61,_=pad('D6','1')
    route(fgla,0.4,[g1,r192]); route(fgla,0.25,[d52,r192,d61])
    d51,gla=pad('D5','1'); r191,_=pad('R19','1'); tp60,_=pad('TP60','1')
    route(gla,0.4,[d51,r191]); route(gla,0.25,[d51,tp60])
    # --- snubber A, links between the two parts of each RC (parts are DNP)
    a,snh=pad('R21','1'); c,_=pad('C98','2'); route(snh,0.25,[a,(a[0],c[1]-0.35),c])
    a,snl=pad('R22','2'); c,_=pad('C99','1'); route(snl,0.25,[a,(a[0],c[1]),c])
    # --- DRV8353 local caps on the south-east and south-west sides (all phases)
    p2,cph=pad('U6','2'); c1,_=pad('C94','1'); route(cph,0.25,[p2,outward('U6','2',0.75),c1])
    p1,cpl=pad('U6','1'); c2,_=pad('C94','2'); o=outward('U6','1',0.45); route(cpl,0.25,[p1,o,(o[0]+0.82,o[1]+0.72),(c2[0]-0.68,c2[1]+0.57),c2])
    p40,vg=pad('U6','40'); c961,_=pad('C96','1'); route(vg,0.25,[p40,outward('U6','40',0.6),c961])
    p38,dv=pad('U6','38'); c971,_=pad('C97','1'); route(dv,0.25,[p38,outward('U6','38',0.6),c971])
    p24,a3=pad('U6','24'); c931,_=pad('C93','1'); route(a3,0.25,[p24,outward('U6','24',0.6),c931])
    for num in ('39','25'):
        p,g=pad('U6',num); route(g,0.25,[p,inward('U6',num,1.2)])
    gnd=b.FindNet('GND'); via(gnd,154.5,96.1); via(gnd,144.7,95.9)
    b.BuildConnectivity(); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(sys.argv[1],b); print('track segments added',n,'+ 2 GND vias')
main()
