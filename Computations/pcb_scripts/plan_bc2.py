# stage 2: long runs of phases B and C (executed inside plan_bc.py)
def pin(n): return W.pad('U6',str(n))
def mid(a,b): return ((a[0]+b[0])/2,(a[1]+b[1])/2)
def show(name,pts): print('   ',name,[(round(x,2),round(y,2)) for x,y in pts])
NW=(-1,-1)
for ref,x,y in (('TP72',140.75,92.4),('TP73',140.75,94.05)): W.shift(ref,x,y)
# ---- driver-side vias of the phase B shunt pair (mirror image of phase A)
v11=V('SB-',148.895,88.281); v12=V('SB+',147.799,88.033)
T('SB+',F,0.2,[pin(12),(v12[0],v12[1]+0.282),v12]+link(v12,W.pad('TP70','1'))[1:]); T('SB-',F,0.2,[pin(11),(v11[0],v11[1]+0.424),v11]+link(v11,W.pad('TP71','1'))[1:])
# ---- high side B pair: pins 14/15 -> under C105 -> slot between Q4 and Q2 (east half) -> R24 / NT8
cb=mid(pin(14),pin(15)); xs=cb[0]-round((cb[0]-139.0)/0.05)*0.05; ys=cb[1]-round((cb[1]-85.85)/0.05)*0.05          # slot centre of the east pair, on the router grid
ctr=W.route('GHB',F,0.78,cb,(xs,ys),d0=NW,d0_len=0.9,quiet=True); show('HS-B centre',ctr)
ctr=ctr+[(xs,76.5)]
ghb=offset(ctr,0.25)+[(xs-0.25,71.55),(142.22,71.55),W.pad('TP62','1')]; shb=offset(ctr,-0.25)+[(xs+0.25,74.82),W.pad('NT8','1')]
T('GHB',F,0.28,ghb,allow=(ZV,'zone:PHB L1')); T('SHB',F,0.28,shb,allow=(ZV,'zone:PHB L1'))
# ---- high side C pair + GLC: under the LEDs D3 and D13; the pair turns north west of D13 into the slot (west half)
p17=pin(17); xw=xs-1.25                                                       # SHC lane in the slot
c3=[p17,(p17[0]-(p17[1]-90.5),90.5),(137.35,90.5),(137.35,86.75),(xw,86.75-(xw-137.35)),(xw,76.5)]
T('SHC',F,0.28,c3[:-1]+[(xw,74.82),(137.3,74.82)],allow=(ZV,)); T('GHC',F,0.28,offset(c3,-0.5)+[(xw+0.5,70.7)],allow=(ZV,))
va=V('GLC',136.7,91.0); vb=V('GLC',136.7,93.5)
T('GLC',F,0.28,offset(c3[:3],0.5)[:2]+[va]); T('GLC',B,0.28,[va,vb])
# ---- shunt C pair: south of the LEDs, between the two GLC vias, into the band between the cap via rows, then north-west to the ties
c=mid(pin(19),pin(20)); a=(c[0]-0.424,c[1]-0.424)
sc=[c,a,(a[0]-0.5,a[1]),(a[0]-0.5-(93.2-a[1]),93.2),(137.67,93.2),(133.97,89.5),(129.5,89.5)]
scp=offset(sc,-0.25)[:-1]+[(128.3,89.25),(128.3,88.02),(125.45,85.17),W.pad('NT9','1')]
scn=offset(sc,0.25)[:-1]+[(127.88,89.75),(127.88,88.19),(125.52,85.83),W.pad('NT10','1')]
T('SC+',F,0.2,scp,allow=('zone:SRC_LS_C L1',)); T('SC-',F,0.2,scn,allow=('zone:SRC_LS_C L1',))
T('SC+',F,0.2,[W.pad('TP72','1'),(140.75,92.95)]); T('SC-',F,0.2,[W.pad('TP73','1'),(140.75,93.45)])
# ---- GLC after its hop: south of the pair, then alone under R30 to R28
glc=[vb,(vb[0]-3.25,90.25),(127.3,90.25),(125.75,88.7),(121.2,88.7)]
T('GLC',F,0.28,glc); t=W.route('GLC',F,0.28,glc[-1],(119.5,86.0),pad_end=0.15,d0=(-1,0),d0_len=0.2); T('GLC',F,0.28,t); show('GLC end',t)
# ---- GLB: around the west end of the SB vias to D7
t=W.route('GLB',F,0.28,pin(13),(149.0,85.95),d0=NW,d0_len=1.0,pad_end=0.1,eps=0.015); T('GLB',F,0.28,t); show('GLB',t)
# ---- shunt B pair: L1 stubs under C104, L6 run south of the SA vias (SB+ passes north of the SB- via, then between it and the SA- via)
s1=V('SB+',155.5,85.03); s2=V('SB-',154.745,85.70)
T('SB+',F,0.2,link(W.pad('NT6','1'),s1),allow=('zone:SRC_LS_B L1',)); T('SB-',F,0.2,link(W.pad('NT7','1'),s2))
T('SB+',B,0.2,link(v12,(148.5,87.65))+[(149.25,87.65),(150.5,88.9),(152.2,88.9),(152.45,88.65),(152.45,85.4),(152.82,85.03),s1])
T('SB-',B,0.2,[v11,(149.934,89.32),(152.45,89.32),(152.87,88.9),(152.87,86.1),(153.27,85.70),s2])
