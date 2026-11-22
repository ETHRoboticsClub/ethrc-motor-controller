"""Step 5, second half (user decision 2026-11-22: PDI on L4 inside a GND window cut into the L3/L4 +VBAT bus).
Layer use around U1/U9 (L3 and L4 are 0.109 mm apart, so an L4 track is referenced to whatever L3 carries):
- SOA/SOB/SOC (DRV8353 CSA -> ADC RC filters): L1 escape at U6, vias inside the encoder keepout circle (no L3/L4
  copper there), L4 stripline under U1's body to the filter cluster. Analog, so its own bundle, away from the PDI.
- PDI (LAN9253 SPI + SYNC0/1, IRQ, RST, CS): vias at U1's north-east face, L4 around the east and south of U1 and
  the ADC filters, to U9's south corner; branches along U9's east side to the east and north corners.
- L3 and L4 get a GND window (zone priority 15 > +VBAT 10) wherever these L4 tracks run, plus the enclosed island.
- Encoder SPI on L6 (U7, R8/R9, R45, R10 are bottom parts); NTC / VBAT sense on L6.
usage: plan_s5e.py board.kicad_pcb plan.json"""
import sys,os,math
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from route import *
F,B,L3,L4='F.Cu','B.Cu','In2.Cu','In3.Cu'; R2=1/math.sqrt(2)
W=World(sys.argv[1]); P=W.pad
ZA=lambda: tuple(z['ref'] for z in W.zones)
warn=[]
def vmargin(net,x,y,r=0.275):
    m=W.via_margin(net,x,y,r)
    for lay in (L3,L4):
        m2=W.margin(net,lay,r,[(x,y),(x,y)],allow=ZA())
        if m2[0]<m[0]: m=(m2[0],lay+' '+str(m2[1]))
    return m
def T(net,layer,w,pts,tag='',zones_yield=False):
    pts=clean([tuple(p) for p in pts]); m=W.margin(net,layer,w/2,pts,allow=ZA() if zones_yield or layer in (L3,L4) else ())
    if m[0]<-0.005: warn.append(tag or net); print('  !! %-14s %s margin %.3f %s'%(tag or net,layer,m[0],m[1]))
    return W.add_track(net,layer,w,pts)
def V(net,p,tag=''):
    m=vmargin(net,*p)
    if m[0]<-0.005: warn.append(tag or net); print('  !! via %-12s %s margin %.3f %s'%(tag or net,tuple(round(v,2) for v in p),m[0],m[1]))
    return W.add_via(net,p[0],p[1],check=False)
def show(tag,net,layer,w,pts):
    m=W.margin(net,layer,w/2,clean([tuple(p) for p in pts]),allow=ZA() if layer in (L3,L4) else ()); print('  %-10s %-6s %s margin %.3f %s'%(tag,net,layer,m[0],m[1]))
def pend(ref,num,d):                                  # point d mm beyond the outer end of a quad-flat pin (along its axis)
    f=W.R[ref]; px,py=P(ref,num); cx,cy=f.x,f.y
    p=[q for q in f.pads if q.num==num][0]; L=max(p.w,p.h)/2
    # pin axis: the face normal (U1/U6/U9 are rotated 45 deg, so the axis is one of the diagonals)
    ux,uy=px-cx,py-cy; a=math.atan2(uy,ux); k=round((a-math.pi/4)/(math.pi/2)); ang=math.pi/4+k*math.pi/2
    nx,ny=math.cos(ang),math.sin(ang); return (round(px+nx*(L+d),4),round(py+ny*(L+d),4))
def pin_in(ref,num,d=0.0):                            # point d mm inside the inner end of a quad-flat pin
    f=W.R[ref]; p=[q for q in f.pads if q.num==num][0]; return pend(ref,num,-2*max(p.w,p.h)/2-d)
# ================================================================= 1. current sense SOA/SOB/SOC
WS=0.2; Q=0.4                                             # analog lines 0.2 mm; 0.4 mm pitch at U6, 0.6 mm near vias
# L1 at U6: each pin exits SW, turns W above C93 (y 93.8/94.2/94.6 between SC- at 93.45 and C93 at 94.9),
# turns SW on lines x+y = const that clear the GND via of C93, then S, then SE into the encoder keepout circle.
sx=144.09                                                  # SOA's south leg: 0.575 west of C93's GND via (144.70, 95.90)
L1p={}
for k,(net,pn) in enumerate((('SOC','21'),('SOB','22'),('SOA','23'))):
    e=pend('U6',pn,0.0); yw=93.75+Q*k                      # W leg
    c1=(round(e[0]-(yw-e[1]),4),yw)                          # SW exit to the W leg
    sxk=sx-Q*(2-k); sw=239.755-Q*math.sqrt(2)*(2-k)         # SW line x+y = sw, S leg x = sxk
    c2=(round(sw-yw,4),yw); c3=(sxk,round(sw-sxk,4))
    se=47.825-Q*math.sqrt(2)*(2-k)                          # SE line x-y = se
    c4=(sxk,round(sxk-se,4))
    L1p[net]=[P('U6',pn),e,c1,c2,c3,c4]
# vias inside the keepout circle (no L3/L4 copper there; L2/L5 GND above and below), one E leg each
vxy={'SOA':(145.85,97.75),'SOB':(146.35,98.65),'SOC':(146.05,99.55)}
for net in ('SOA','SOB','SOC'):
    c4=L1p[net][-1]; vx,vy=vxy[net]; se=c4[0]-c4[1]
    c5=(round(vy+se,4),vy)                                   # SE line meets the via row y
    L1p[net]+= [c5,(vx,vy)] if vx>c5[0]+1e-6 else [(round(vy+se,4),vy)]
    if vx<=c5[0]+1e-6: vxy[net]=c5
for net,pts in L1p.items(): T(net,F,WS,pts,net+' L1 U6')
for net,v in vxy.items(): V(net,v,net+' via U6')
# L4: one E leg per via, then the bundle SE along x-y = 49 (SOB) under U1's west corner (midway between the pin-1 and
# pin-64 axes, so both pins keep room for an outboard via), S under U1's south corner, E to the filter cluster.
s0=49.0; dq=Q*math.sqrt(2)
off={'SOA':+1,'SOB':0,'SOC':-1}                              # SOA on the north-east side of the bundle
xS=162.5                                                   # S leg of SOB under the S corner (pins 16/17 at 161.1/163.9)
yE={'SOA':117.5,'SOB':118.1,'SOC':118.7}                   # E legs; 0.6 mm pitch past the filter-end vias
vB={'SOA':(165.0,117.5),'SOB':(167.3,118.1),'SOC':(169.4,115.33)}   # SOC via on x-y = 54.07: the lane between R6.1 and FB1.2
for net in ('SOA','SOB','SOC'):
    v=vxy[net]; sk=s0+off[net]*dq; xk=xS+off[net]*Q
    pts=[v,(round(v[1]+sk,4),v[1]),(xk,round(xk-sk,4)),(xk,yE[net])]
    if net=='SOC': pts+=[(vB[net][0],yE[net]),vB[net]]
    else: pts+=[vB[net]]
    T(net,L4,WS,pts,net+' L4')
    V(net,vB[net],net+' via filter')
# L1 at the filters: via -> test pad -> resistor pad 2 (the test pads sit beside the resistor pads)
T('SOA',F,WS,[vB['SOA'],(165.0,116.56),P('TP11','1')],'SOA L1 filt'); T('SOA',F,WS,[P('TP11','1'),P('R5','2')],'SOA tp-r')
T('SOB',F,WS,[vB['SOB'],(167.3,115.6),P('R6','2')],'SOB L1 filt'); T('SOB',F,WS,[P('R6','2'),P('TP12','1')],'SOB tp-r')
T('SOC',F,WS,[vB['SOC'],(167.81,113.74),P('R7','2')],'SOC L1 filt'); T('SOC',F,WS,[P('R7','2'),P('TP13','1')],'SOC tp-r')
# ================================================================= 2. PDI (LAN9253 SPI + SYNC/IRQ/RST/CS) on L4
WP=0.2; PP=0.4                                             # 0.2 mm lines, 0.4 mm pitch in the straight runs
for r in ('TP18','TP19','TP20','TP23','TP75'): W.shift(r,80.0,100.0+float(r[2:])*0.0)   # parked; re-placed on their lines at the end
ne0=P('U1','33')                                           # U1 north-east face frame: s along pins 33->48, d inwards (SW)
fne=lambda s,d:(round(ne0[0]-R2*s-R2*d,4),round(ne0[1]-R2*s+R2*d,4))
# Every other pin of 39..44 goes inboard (straight stubs >= 1 mm apart), the others leave outboard to the north.
# L4 depth order deep->shallow = band order inside->outside: CS, IRQ, SYNC0, MISO | RST, SYNC1 (north) | SCLK, MOSI (east)
vin={'ESC_CS':(0.0,4.4,'33'),'ESC_MISO':(1.5,2.6,'36'),'ESC_SYNC0':(3.0,3.2,'39'),'ESC_IRQ':(4.0,3.8,'41')}      # SENSE_VBAT (pin 43, inboard s 5.0 d 1.5) follows with the encoder
cvia={}
for net,(sv,dv,pn) in vin.items():
    v=fne(sv,dv); cvia[net]=v; V(net,v,net+' via U1 in')
    T(net,F,WP,[P('U1',pn),v],net+' stub in')
vout={'ESC_RST':('44',166.25,100.05),'SENSE_TEMP_MOT':('42',166.9,98.7),'ESC_SYNC1':('40',167.55,99.6)}
for net,(pn,x,y) in vout.items():
    e=pend('U1',pn,0.0); c=(x,round(e[1]-(x-e[0]),4))            # NE exit to x, then north to the via
    cvia[net]=(x,y); V(net,(x,y),net+' via U1 out'); T(net,F,WP,[P('U1',pn),e,c,(x,y)],net+' stub out')
def RT(net,layer,w,a,b,**kw):
    pts=W.route(net,layer,w,a,b,quiet=True,**kw)
    if not pts: warn.append(net+' route'); print('  !! no route',net,layer,a,b); return None
    return T(net,layer,w,pts,net+' routed '+layer)
# SCLK / MOSI leave through R4 / R3 (outboard): vias south-east of U1's east corner, clear of U5 (bottom) and its L3 VOS track
cvia['ESC_SCLK']=(172.5,104.89); cvia['ESC_MOSI']=(173.3,104.7)
V('ESC_SCLK',cvia['ESC_SCLK'],'SCLK via U1'); V('ESC_MOSI',cvia['ESC_MOSI'],'MOSI via U1')
T('ESC_SCLK',F,WP,[P('R4','2'),cvia['ESC_SCLK']],'SCLK R4-via')
T('ESC_MOSI',F,WP,[P('R3','2'),(170.3,101.25),(172.3,101.25),(173.3,102.25),cvia['ESC_MOSI']],'MOSI R3-via')
T('ESC_SCLK_MCU',F,WP,[P('U1','35'),P('R4','1')],'SCLK pin-R4'); T('ESC_MOSI_MCU',F,WP,[P('U1','37'),P('R3','1')],'MOSI pin-R3')
# the band, inside -> outside; inboard lines run south-east at their depth, then south east of the SOx vias, then west
band=['ESC_CS','ESC_IRQ','ESC_SYNC0','ESC_MISO','ESC_RST','ESC_SYNC1','ESC_SCLK','ESC_MOSI']
xs=dict(zip(band,(170.0,170.4,170.8,171.2,171.6,172.0,172.5,173.3)))
cdep={'ESC_RST':63.0,'ESC_SYNC1':63.85}
yw={n:round(122.8+PP*k,3) for k,n in enumerate(band)}       # west legs, CS north-most (clear of J15's holes)
lines={}
for n in band:
    v=cvia[n]
    if n in ('ESC_SCLK','ESC_MOSI'): pts=[v,(xs[n],yw[n])]
    elif n in cdep: c=cdep[n]; pts=[v,(v[0],round(v[0]-c,4)),(xs[n],round(xs[n]-c,4)),(xs[n],yw[n])]
    else: c=v[0]-v[1]; pts=[v,(xs[n],round(xs[n]-c,4)),(xs[n],yw[n])]
    lines[n]=pts
# branch to U9's east / north corners: SYNC0, IRQ, CS turn north (CS outermost)
bx={'ESC_SYNC0':152.5,'ESC_IRQ':153.1,'ESC_CS':153.7}
# CS: the only free escape of pin 50 is where C135's GND via sits -> move that via north-east, CS's via takes its place
W.drop_via(144.48,105.02); W.drop_seg((144.03,104.57),(144.48,105.02))
V('GND',(144.75,103.95),'C135 GND via'); T('GND',F,0.25,[P('C135','2'),(144.75,103.95)],'C135 GND')
u9v={'ESC_SYNC0':(152.5,111.0),'ESC_IRQ':(149.0,106.25),'ESC_CS':(144.45,105.27)}
lines['ESC_SYNC0']+= [(bx['ESC_SYNC0'],yw['ESC_SYNC0']),u9v['ESC_SYNC0']]
lines['ESC_IRQ']  += [(bx['ESC_IRQ'],yw['ESC_IRQ']),(bx['ESC_IRQ'],round(bx['ESC_IRQ']-42.75,4)),u9v['ESC_IRQ']]
lines['ESC_CS']   += [(bx['ESC_CS'],yw['ESC_CS']),(bx['ESC_CS'],round(bx['ESC_CS']-43.7,4)),(148.97,105.27),u9v['ESC_CS']]
# the rest rise north-west after the branch and end at staggered vias south of U9 (each via on its own line)
yf={'ESC_MISO':120.4,'ESC_RST':121.0,'ESC_SYNC1':121.6,'ESC_SCLK':122.2,'ESC_MOSI':122.8}
u9v.update({'ESC_MISO':(144.5,120.4),'ESC_RST':(145.2,121.0),'ESC_SYNC1':(147.18,121.6),'ESC_SCLK':(147.94,122.2),'ESC_MOSI':(146.42,122.8)})
c3=151.9-yw['ESC_MISO']
for k,n in enumerate(('ESC_MISO','ESC_RST','ESC_SYNC1','ESC_SCLK','ESC_MOSI')):
    c=c3-PP*math.sqrt(2)*k
    lines[n]+= [(round(c+yw[n],4),yw[n]),(round(c+yf[n],4),yf[n]),u9v[n]]
for n in band:
    T(n,L4,WP,lines[n],n+' L4 band')
    if n not in ('ESC_SYNC0',): V(n,u9v[n],n+' via U9')
V('ESC_SYNC0',u9v['ESC_SYNC0'],'SYNC0 via U9')
# ---- L1 at U9: the south-corner trio, RST chain, MISO through R56 (bottom), the branch pins
def RS(net,layer,w,a,b,pad=None,**kw):                   # A* from a via to a point, then straight into the pad
    pts=RT(net,layer,w,a,b,**kw)
    if pad is not None and pts: T(net,layer,w,[b,pad],net+' into pad')
U9B=(140.5,114.5,149.5,124.0)
# trio: SE exits staggered 0.5/0.6/0.7 so the south legs are 0.42 apart, then MOSI / SCLK fan out to 0.75 for the vias
for net,pn,e,jog in (('ESC_MOSI','17',0.4,-0.34),('ESC_SYNC1','18',0.5,0.0),('ESC_SCLK','19',0.6,0.34)):
    t=pend('U9',pn,0.0); c=(round(t[0]+R2*e,4),round(t[1]+R2*e,4)); v=u9v[net]
    jog=round(v[0]-c[0],4) if jog else 0.0                  # land the 45-degree jog exactly on the via's x
    pts=[P('U9',pn),t,c]+([(c[0],118.4),(v[0],round(118.4+abs(jog),4))] if jog else [])+[v]
    T(net,F,WP,pts,net+' L1 U9-S')
RS('ESC_RST',F,WP,u9v['ESC_RST'],P('R51','2'),box=U9B,bend=0.8)
RS('ESC_RST',F,WP,P('R51','2'),P('C118','1'),box=U9B,bend=0.8)
RS('ESC_RST',F,WP,P('C118','1'),P('TP17','1'),box=U9B,bend=0.8)
RS('ESC_RST',F,WP,P('TP17','1'),pend('U9','11',0.3),P('U9','11'),box=U9B,bend=0.8)
RS('ESC_MISO',B,WP,u9v['ESC_MISO'],P('R56','2'),box=U9B,bend=0.8)
best=None                                                # MISO_ESC: via south-west of pin 13, then L6 to R56.1
for i in range(-12,13):
    for j in range(-12,13):
        x,y=143.7+0.05*i,117.15+0.05*j; m=vmargin('ESC_MISO_ESC',x,y)[0]
        if m>0.02 and (best is None or math.hypot(x-143.9,y-116.9)<best[0]): best=(math.hypot(x-143.9,y-116.9),(round(x,3),round(y,3)))
vme=best[1]; print('  MISO_ESC via',vme); V('ESC_MISO_ESC',vme,'MISO_ESC via')
pc=P('U9','13'); T('ESC_MISO_ESC',F,WP,[vme,(vme[0],round(pc[1]+(pc[0]-vme[0]),4)),pc],'MISO_ESC pin-via')   # north, then 45 deg into pin 13
RS('ESC_MISO_ESC',B,WP,vme,P('R56','1'),box=U9B,bend=0.8)
NB=(138.5,98.5,153.0,111.5)
RS('ESC_SYNC0',F,WP,u9v['ESC_SYNC0'],pend('U9','34',0.3),P('U9','34'),box=NB,bend=0.8)
RS('ESC_IRQ',F,WP,u9v['ESC_IRQ'],pend('U9','44',0.3),P('U9','44'),box=NB,bend=0.8)
T('ESC_CS',F,WP,[P('U9','50'),pend('U9','50',0.0),u9v['ESC_CS']],'CS pin50-via')
# CS -> R90/TP21 and IRQ -> R91/TP22 (pull-ups north-west of U9) are left open: no L1 path, see the review note
# ================================================================= 3. motor NTC (SENSE_TEMP_MOT): L6 around U1's east side
vtm=(174.4,119.8); V('SENSE_TEMP_MOT',vtm,'TEMP_MOT via J7')
RT('SENSE_TEMP_MOT',B,WP,cvia['SENSE_TEMP_MOT'],vtm,box=(163.0,97.0,177.5,121.5),bend=0.8)
TB=(169.5,118.5,178.0,124.0)
RS('SENSE_TEMP_MOT',F,WP,vtm,P('R42','2'),box=TB,bend=0.8); RS('SENSE_TEMP_MOT',F,WP,P('R42','2'),P('TP36','1'),box=TB,bend=0.8)
RS('SENSE_TEMP_MOT',F,WP,P('TP36','1'),P('D16','2'),box=TB,bend=0.8); RS('SENSE_TEMP_MOT',F,WP,P('R42','2'),P('C111','1'),box=TB,bend=0.8)
RS('SENSE_TEMP_MOT',F,WP,vtm,P('J7','1'),box=TB,bend=0.8)
# ================================================================= 4. test points next to vias of their nets (0.5 mm pads, short L1 stub)
lock=[]
def tp_at(ref,anchor,reach=1.6,keep=0.0):
    net=W.padnet(ref,'1'); nc=W.canon(net); best=None
    for i in range(-int(reach/0.05),int(reach/0.05)+1):
        for j in range(-int(reach/0.05),int(reach/0.05)+1):
            x,y=anchor[0]+0.05*i,anchor[1]+0.05*j; d=math.hypot(x-anchor[0],y-anchor[1])
            if d<0.7 or d>reach or (best and d>=best[0]): continue
            if W.margin(nc,F,0.25,[(x,y),(x,y)])[0]<0.02: continue
            if W.margin(nc,F,0.1,[anchor,(x,y)])[0]<0.0: continue
            best=(d,(round(x,3),round(y,3)))
    if not best: warn.append(ref); print('  !! no spot for',ref); return
    W.shift(ref,*best[1]); W.add_track(nc,F,WP,[anchor,best[1]]); lock.append(ref); print('  ',ref,'at',best[1])
tp_at('TP18',cvia['ESC_SCLK']); tp_at('TP20',cvia['ESC_MOSI']); tp_at('TP75',cvia['ESC_SYNC1'])
tp_at('TP23',u9v['ESC_SYNC0']); tp_at('TP19',u9v['ESC_MISO'])
# ================================================================= 5. GND return vias beside the layer changes (L1 <-> L4 / L6)
def gnd_near(pts,n=1,reach=1.4):
    cx,cy=sum(p[0] for p in pts)/len(pts),sum(p[1] for p in pts)/len(pts); got=0
    cand=sorted(((math.hypot(cx+0.05*i-cx,cy+0.05*j-cy),round(cx+0.05*i,3),round(cy+0.05*j,3)) for i in range(-40,41) for j in range(-40,41)))
    for d,x,y in cand:
        if d>reach+1.5: break
        if min(math.hypot(x-p[0],y-p[1]) for p in pts)>reach: continue
        if vmargin('GND',x,y)[0]<0.03: continue
        W.add_via('GND',x,y,check=False); got+=1
        if got==n: return
    warn.append('gnd near %s'%(pts[0],)); print('  !! GND via missing near',pts[0])
gnd_near([cvia['ESC_CS'],cvia['ESC_MISO']]); gnd_near([cvia['ESC_SYNC0'],cvia['ESC_IRQ']])
gnd_near([cvia['ESC_RST'],cvia['ESC_SYNC1']]); gnd_near([cvia['ESC_SCLK'],cvia['ESC_MOSI']])
gnd_near([u9v['ESC_MISO'],u9v['ESC_RST']]); gnd_near([u9v['ESC_SYNC1'],u9v['ESC_SCLK'],u9v['ESC_MOSI']],n=2)
gnd_near([u9v['ESC_SYNC0']],reach=2.2); gnd_near([u9v['ESC_IRQ']]); gnd_near([u9v['ESC_CS']])
gnd_near([vxy['SOA'],vxy['SOB'],vxy['SOC']]); gnd_near([vB['SOA'],vB['SOB']]); gnd_near([vB['SOC']])
# stitching vias inside the enclosed L4 island (otherwise the window's L4 fill there is an unconnected island)
for q in ((156.0,116.0),(159.5,120.0),(152.0,118.5),(165.5,120.5)): gnd_near([q],reach=1.5)
# ================================================================= 6. GND window on L3/L4 under the L4 lines (priority 15 > +VBAT bus 10)
from shapely.geometry import LineString,Polygon,Point
from shapely.ops import unary_union
l4=[t for t in W.plan['tracks'] if t['layer']==L4]
geo=[LineString(t['pts']).buffer(1.1,cap_style=2,join_style=2) for t in l4]
geo.append(Polygon([(150.2,104.6),(153.6,103.3),(161.6,113.4),(161.6,117.1),(169.0,117.1),(169.0,122.4),(154.2,122.4),(154.2,110.5),(150.2,107.2)]))   # enclosed island + wedge at the circle
win=unary_union(geo).buffer(0.3,join_style=2).buffer(-0.3,join_style=2)
# the window is cut out of the +VBAT bus outline; the existing GND fill (L1/L3/L4/L6, priority 0) then fills it
vz=[z for z in W.zones if z['ref']=='zone:VBAT bus L3/L4'][0]
vb=Polygon(vz['pts']).difference(win)
pieces=[vb] if vb.geom_type=='Polygon' else sorted(vb.geoms,key=lambda g:-g.area)
for g in pieces[1:]: print('  !! +VBAT piece dropped, area %.1f mm2 at'%g.area,tuple(round(v,1) for v in g.centroid.coords[0]))
vb=pieces[0].simplify(0.02); assert not list(vb.interiors),'window would leave a hole in the +VBAT outline'
vpts=[(round(x,3),round(y,3)) for x,y in list(vb.exterior.coords)[:-1]]
print('  window area %.1f mm2, +VBAT outline %d pts (was %d), area %.0f -> %.0f mm2'%(win.area,len(vpts),len(vz['pts']),Polygon(vz['pts']).area,vb.area))
W.plan['zone_outline']={'VBAT bus L3/L4':vpts}
vz['pts']=vpts; vz['rings']=[vpts]; vz.pop('_bb',None)
# ================================================================= 7. CS / IRQ pull-ups and test points to the bottom, at the CS / IRQ vias
def flip_tp(ref,x,y):                                     # single-pad part to the bottom at (x, y)
    f=W.R[ref]; W.shift(ref,x,y)
    for q in f.pads: q.layers=[l.replace('F.','B.') for l in q.layers]
    W.refresh(ref); W.plan['place'].append(dict(ref=ref,x=x,y=y,pad='1',px=x,py=y,bottom=True))
W.place2('R90',145.85,105.27,'2',(145.2,105.27),bottom=True); W.place2('R91',148.25,105.6,'2',(148.25,106.25),bottom=True)
T('ESC_CS',B,WP,[u9v['ESC_CS'],P('R90','2')],'CS via-R90'); T('ESC_IRQ',B,WP,[u9v['ESC_IRQ'],P('R91','2')],'IRQ via-R91')
def tp_bottom(ref,anchor,reach=1.8):
    net=W.canon(W.padnet(ref,'1')); best=None
    for i in range(-36,37):
        for j in range(-36,37):
            x,y=anchor[0]+0.05*i,anchor[1]+0.05*j; d=math.hypot(x-anchor[0],y-anchor[1])
            if d<0.75 or d>reach or (best and d>=best[0]): continue
            if W.margin(net,B,0.3,[(x,y),(x,y)])[0]<0.02 or W.margin(net,B,0.1,[anchor,(x,y)])[0]<0.0: continue
            best=(d,(round(x,3),round(y,3)))
    if not best: warn.append(ref); print('  !! no bottom spot for',ref); return
    flip_tp(ref,*best[1]); W.add_track(net,B,WP,[anchor,best[1]]); lock.append(ref); print('  ',ref,'bottom at',best[1])
tp_bottom('TP21',P('R90','2')); tp_bottom('TP22',P('R91','2'))
lock+=['R90','R91']
W.plan['lock']=lock
W.save(sys.argv[2]); print('warnings',len(warn),warn)
