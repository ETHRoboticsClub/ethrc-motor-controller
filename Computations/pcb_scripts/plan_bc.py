"""Step 3, phases B and C: plan (vias, part moves, local links, long runs). usage: plan_bc.py board.kicad_pcb plan.json [stage]
Stage 1: fixed vias, moves, local links.  Stage 2: + long runs.  Stage 3: + bulk-cap and shunt-return vias."""
import sys,os,math
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from route import *
Q=0.70711; F,B='F.Cu','B.Cu'
W=World(sys.argv[1]); STAGE=int(sys.argv[3]) if len(sys.argv)>3 else 3
def V(net,x,y): return W.add_via(net,x,y)
def T(net,layer,w,pts,allow=()):
    pts=clean([tuple(p) for p in pts]); m=W.margin(net,layer,w/2,pts,allow)
    if m[0]<-0.005: print('  !! track',net,layer,[(round(x,2),round(y,2)) for x,y in pts][:4],'margin',round(m[0],3),m[1])
    return W.add_track(net,layer,w,pts)
GU=(-2.1,-0.7,0.7,2.1); GV=(-1.95,-1.3,-0.65,0.0,0.65,1.3,1.95); PCY=-0.785
def grid(ref):
    f=W.R[ref]; a=math.radians(f.rot); c,s=math.cos(a),math.sin(a)
    return [(f.x+u*c+(PCY+v)*s,f.y-u*s+(PCY+v)*c) for u in GU for v in GV]
ZV='zone:VBAT HS-C/HS-B L1'
# =============================================================== stage 1: moves
# snubbers B and C go under their FETs (decision 93)
W.drop_net('SNUBH_B'); W.drop_net('SNUBL_B'); W.drop_net('SNUBH_C'); W.drop_net('SNUBL_C')
for c,r,cx,cpad,rpad in (('C106','R31',132.5,'1','2'),('C102','R26',142.5,'1','2')):       # high side: PHx - C - R - +VBAT
    W.place2(c,cx,72.65,cpad,(cx,72.25),bottom=True); W.place2(r,cx,74.85,rpad,(cx,75.75),bottom=True)
for c,r,cx,cpad,rpad in (('C107','R32',124.9,'2','1'),('C103','R27',155.9,'2','1')):       # low side: PHx - C - R - SRC_LS_x
    W.place2(c,cx,79.75,cpad,(cx,79.35),bottom=True); W.place2(r,cx,81.95,rpad,(cx,82.85),bottom=True)
# switch-node tie of phase B to the west end of Q2's source row (the gate pair arrives from the west)
W.drop_seg((144.4,74.8),(144.4,74.15)); W.place2('NT8',140.3,74.82,'1',(140.0,74.82))
for ref,x,y in (('TP67',137.3,74.82),('TP70',148.25,87.76),('TP71',149.38,87.69)): W.shift(ref,x,y)
W.shift('C34',158.0,86.5)                                     # its GND pad comes under the R25 return vias, the VM pad leaves room for the SB vias
# phase A highway dips south of R25 so that the shunt gets a row of return vias; C95 and C92 follow
p6,p7,p8=W.pad('U6','6'),W.pad('U6','7'),W.pad('U6','8'); n6=(p6[0]+p6[1]-89.07,89.07); n7=(p7[0]+p7[1]-88.57,88.57); n8=(p8[0]+p8[1]-88.07,88.07)
for a,b in ((n8,(160.78,88.07)),((160.78,88.07),(160.78,87.08)),(n7,(164.45,88.57)),((164.45,88.57),(164.88,89.0)),(n6,(164.07,89.07)),((164.07,89.07),(164.62,89.62)),
            ((154.8,90.2),(156.5,90.2)),((157.7,90.2),(158.65,90.25)),((160.4,90.3),(161.8,90.3)),((161.8,90.3),(162.2,90.7))): W.drop_seg(a,b)
W.place2('C95',157.5,90.75,'1',(156.9,90.75)); W.shift('C92',160.4,92.2)
sha=[n7,(156.55,88.57),(156.98,89.0),(164.88,89.0)]; gla=offset(sha,0.5)
T('SHA',F,0.28,sha); T('GLA',F,0.28,[n8]+gla[1:3]+[(160.78,88.5),(160.78,87.08)]); T('GHA',F,0.28,[n6,(156.3,89.07),(156.85,89.62),(164.62,89.62)])
T('+VBAT',F,0.4,[(154.8,90.2),(155.9,90.2),(156.45,90.75),(156.9,90.75)]); T('GND',F,0.4,[(158.15,90.75),(158.65,90.25)]); T('+VBAT',F,0.6,[(160.4,90.7),(162.2,90.7)])
# =============================================================== stage 1: fixed vias
for q,net in (('Q5','PHC'),('Q4','+VBAT'),('Q2','+VBAT'),('Q3','PHB')):
    for x,y in grid(q): V(net,x,y)
for k in range(6): V('+VBAT',131.2+k,82.9); V('+VBAT',141.2+k,82.9)
for k in range(4): V('GND',127.4,76.6+2*k)                                             # HG1 caps
for x in (114.7,116.8):                                                                 # WE caps, in pad like the EE caps
    V('+VBAT',x,77.6); V('GND',x,80.4); V('+VBAT',x,81.8); V('GND',x,84.6)
V('+VBAT',159.8,79.6); V('+VBAT',159.8,78.15); V('GND',159.8,75.2); V('GND',159.8,81.7)  # VG3 caps
for x in (131.6,133.4): V('PHC',x,72.5)
for x,y in ((139.95,72.55),(140.6,72.55),(141.25,72.55),(141.8,72.5),(142.55,72.2),(143.2,72.55),(143.85,72.55),(144.5,72.55),(145.15,72.55)): V('PHB',x,y)       # Q2 sources to L3/L4/L6 (the gate pad cuts the L1 path)
for x in (123.75,126.05): V('SRC_LS_C',x,82.75)
for x in (154.75,157.05): V('SRC_LS_B',x,82.75)
V('+VBAT',154.05,87.05)                                                                 # C104 / C34 / C72
for y in (85.55,86.15,86.75,87.35): V('GND',159.6,y)                                    # R25 return
for x in (158.07,158.69,159.31,159.93): V('GND',x,87.86)
# =============================================================== stage 1: local links
# --- phase C
T('FET_GLC',F,0.4,[W.pad('Q5','1'),(119.5,84.22)]); T('FET_GLC',F,0.25,[(119.5,84.22),W.pad('D12','1')])
T('GLC',F,0.4,[(119.5,85.78),W.pad('D10','1')]); T('GLC',F,0.25,link(W.pad('TP66','1'),(119.0,85.9)))
T('FET_GHC',F,0.4,[(136.6,69.0),(136.6,73.835)]); T('GHC',F,0.4,[(138.3,69.0),(138.3,70.5)]); T('GHC',F,0.25,[(138.4,70.67),W.pad('TP65','1')])
T('SHC',F,0.28,[W.pad('NT11','1'),(137.3,74.82)],allow=('zone:PHC L1',))
# --- phase B
g3=W.pad('Q3','1'); T('FET_GLB',F,0.4,[g3,(g3[0],83.0),(150.5,84.0)]); T('FET_GLB',F,0.25,[(150.5,84.22),W.pad('D8','1')],allow=(ZV,))
T('GLB',F,0.4,[(150.5,85.78),W.pad('D7','1')]); T('GLB',F,0.25,[W.pad('TP63','1'),(149.62,85.78)])
T('FET_GHB',F,0.4,[(144.78,69.0),(144.78,70.5)]); T('FET_GHB',F,0.4,[(144.9,70.5),(146.1,71.7),(146.1,73.835)],allow=('zone:PHB L1',))
T('GHB',F,0.4,[(143.2,69.0),(143.2,70.5)]); T('GHB',F,0.25,[(143.0,70.83),W.pad('TP62','1')])
T('PHB',F,0.2,[W.pad('NT8','2'),(140.6,74.15)])
T('+VBAT',F,0.4,[(154.05,87.05),(154.9,87.05)])                                         # C104 VM pad to its via
T('+VBAT',B,0.4,[(154.05,87.05),(154.05,87.9)]); T('+VBAT',B,0.4,[(154.05,87.05),(154.05,86.9),(156.6,86.9)])   # C72 and C34 VM pads
T('+VBAT',B,0.4,link((154.3,89.1),(155.65,90.2))); T('GND',B,0.4,link((157.2,89.2),(158.65,90.25)))   # C72 pads to the VM and GND vias of C91/C95                                       # C72 VM pad to the VM via as well
# --- snubbers: R-C mid points, phase vias, source vias (bottom)
for c,r,ph,src in (('C106','R31','PHC',None),('C102','R26','PHB',None),('C107','R32','PHC','SRC_LS_C'),('C103','R27','PHB','SRC_LS_B')):
    hs=src is None; cs=W.pad(c,'2' if hs else '1'); rs=W.pad(r,'1' if hs else '2'); T(W.padnet(c,'2' if hs else '1'),B,0.3,[cs,rs])
    if hs:
        cp=W.pad(c,'1'); vs={'C106':((131.6,72.5),(133.4,72.5)),'C102':((141.8,72.5),(143.2,72.55))}[c]
        for v in vs: T(ph,B,0.3,link(cp,v))
    else:
        rp=W.pad(r,'1'); xs={'R32':(123.75,126.05),'R27':(154.75,157.05)}[r]
        for x in xs: T(src,B,0.4,link(rp,(x,82.75)))
HERE=os.path.dirname(os.path.abspath(__file__))
def mark(): return {k:len(v) for k,v in W.plan.items()}
W.plan['marks']=[]
W.plan['marks'].append(mark())
if STAGE>=2: exec(open(os.path.join(HERE,'plan_bc2.py')).read())
W.plan['marks'].append(mark())
if STAGE>=3: exec(open(os.path.join(HERE,'plan_bc3.py')).read())
W.save(sys.argv[2])
