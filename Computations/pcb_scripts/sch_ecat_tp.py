"""Schematic edits on 'Comms - EtherCat.kicad_sch' (2026-11-22, user-approved):
1. T1/T2 chip-side swap so the EtherCAT pairs route without crossings (Microchip DS00003644B 4.8.1):
   port 0 TX<->RX channel at T1 (Auto-MDIX), port 1 P<->N in both pairs at T2 (automatic polarity correction).
   The four wire segments into each transformer's chip-side pins are replaced by short stubs with local labels.
2. R83/R84 (XO/XI series resistors) fitted with 0R, BOM fields as R74.
3. EtherCAT test points TP76-TP90: hooks on ESC_XO and GND (Keystone 5004/5001), 0.5 mm pads on the PHY supplies,
   the oscillator supply, the SII EEPROM bus and the eight chip-side pair lines.
usage: sch_ecat_tp.py "Comms - EtherCat.kicad_sch" "MCU - IOs.kicad_sch"   (edits the first file in place)"""
import sys,re,uuid
path,tp_src=sys.argv[1:3]
t=open(path).read()
U=lambda: str(uuid.uuid4())
SHEET='/0650c7a8-acba-429c-9f8e-eec0baf0bc1c/fede4c36-00cc-4d3d-b71c-5243ba232202/d342497d-cef2-493b-b20b-1b91b7d9cc9b'
def blocks(text,pat):
    L=text.split('\n'); out=[]; i=0
    while i<len(L):
        if re.match(pat,L[i]):
            j=i
            while L[j]!='\t)': j+=1
            out.append('\n'.join(L[i:j+1])+'\n'); i=j+1
        else: i+=1
    return out
def shift(blk,dx,dy):
    return re.sub(r'\(at ([-\d.]+) ([-\d.]+)',lambda m:'(at %s %s'%(fmt(float(m.group(1))+dx),fmt(float(m.group(2))+dy)),blk)
fmt=lambda v:('%.2f'%v).rstrip('0').rstrip('.')
def newuuids(blk): return re.sub(r'\(uuid "[^"]+"\)',lambda m:'(uuid "%s")'%U(),blk)
add=[]
# ---------------------------------------------------------------- 1. T1/T2 swap
SWAP={  # pin end y -> new net (T1 at y 78.74, T2 at y 176.53; pins at x 332.74)
 68.58:'ECAT_P0_RX+',71.12:'ECAT_P0_RX-',76.2:'ECAT_P0_TX+',78.74:'ECAT_P0_TX-',
 166.37:'ECAT_P1_TX-',168.91:'ECAT_P1_TX+',173.99:'ECAT_P1_RX-',176.53:'ECAT_P1_RX+'}
ORIG={68.58:287.02,71.12:297.18,76.2:306.07,78.74:316.23,166.37:287.02,168.91:297.18,173.99:306.07,176.53:316.23}
lab_tpl=[b for b in blocks(t,r'^\t\(label "ECAT_P0_TX\+"')][0]
wire_tpl=blocks(t,r'^\t\(wire$')[0]
def wire(x1,y1,x2,y2):
    return re.sub(r'\(xy [-\d.]+ [-\d.]+\) \(xy [-\d.]+ [-\d.]+\)','(xy %s %s) (xy %s %s)'%(fmt(x1),fmt(y1),fmt(x2),fmt(y2)),newuuids(wire_tpl))
def label(name,x,y,rot=180,just='right bottom'):
    b=newuuids(lab_tpl).replace('(label "ECAT_P0_TX+"','(label "%s"'%name)
    b=re.sub(r'\(at [-\d.]+ [-\d.]+ \d+\)','(at %s %s %d)'%(fmt(x),fmt(y),rot),b)
    return b.replace('(justify right bottom)','(justify %s)'%just)
n_w=n_j=0
for y,net in SWAP.items():
    pat=r'\t\(wire\n\t\t\(pts\n\t\t\t\(xy %s %s\) \(xy 332.74 %s\)\n\t\t\)\n(?:\t\t[^\n]*\n)*?\t\)\n'%(re.escape(fmt(ORIG[y])),re.escape(fmt(y)),re.escape(fmt(y)))
    t,k=re.subn(pat,'',t); n_w+=k
    pj=r'\t\(junction\n\t\t\(at %s %s\)\n(?:\t\t[^\n]*\n)*?\t\)\n'%(re.escape(fmt(ORIG[y])),re.escape(fmt(y)))
    t,k=re.subn(pj,'',t); n_j+=k
    add.append(wire(332.74,y,325.12,y)); add.append(label(net,325.12,y))
assert n_w==8 and n_j==8,(n_w,n_j)
note_tpl=blocks(t,r'^\t\(text "25 MHz crystal"')[0]
def text(s,x,y,bold=False):
    b=newuuids(note_tpl).replace('(text "25 MHz crystal"','(text "%s"'%s)
    b=re.sub(r'\(at [-\d.]+ [-\d.]+ 0\)','(at %s %s 0)'%(fmt(x),fmt(y)),b)
    return b if bold else b.replace('\t\t\t\t(bold yes)\n','')
add.append(text('T1/T2 chip side deliberately swapped (2026-11-22) so every pair routes on L1 without vias:\\n'
                'port 0: U9 TX pair -> T1 RD pins 6/8, RX pair -> TD pins 1/3 (Auto-MDIX sorts TX/RX);\\n'
                'port 1: P and N exchanged in both pairs at T2 (automatic polarity correction).\\n'
                'Microchip LAN9253 HW design checklist DS00003644B 4.8.1.',290.83,22.86))
# ---------------------------------------------------------------- 2. R83/R84 fitted, 0R, fields as R74
R74={'Datasheet':'https://www.vishay.com/docs/20043/crcwhpe3.pdf','Supplier 1':'Digikey','Supplier Part Number 1':'541-0.0SBCT-ND',
     'Manufacturer':'Vishay','Manufacturer Part Number':'CRCW06030000Z0EAHP'}
def hidden_prop(k,v,x,y):
    return ('\t\t(property "%s" "%s"\n\t\t\t(at %s %s 0)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n'
            '\t\t\t\t(hide yes)\n\t\t\t)\n\t\t)\n')%(k,v,fmt(x),fmt(y))
for ref in ('R83','R84'):
    b=[x for x in blocks(t,r'^\t\(symbol$') if '(property "Reference" "%s"'%ref in x][0]
    nb=b.replace('(dnp yes)','(dnp no)').replace('(property "Value" "0"','(property "Value" "0R"').replace('(property "Datasheet" "~"','(property "Datasheet" "%s"'%R74['Datasheet'])
    a=re.search(r'\(at ([-\d.]+) ([-\d.]+)',nb); x,y=float(a.group(1)),float(a.group(2))
    extra=''.join(hidden_prop(k,v,x,y) for k,v in R74.items() if k!='Datasheet' and '(property "%s"'%k not in nb)
    nb=nb.replace('\t\t(pin "1"',extra+'\t\t(pin "1"',1)
    t=t.replace(b,nb)
# ---------------------------------------------------------------- 3. test points
src=open(tp_src).read()
lib=[b for b in re.findall(r'\t\t\(symbol "Connector:TestPoint"\n.*?\n\t\t\)\n',src,re.S)][0]
if '(symbol "Connector:TestPoint"' not in t:
    k=t.find('\t(lib_symbols\n')+len('\t(lib_symbols\n'); t=t[:k]+lib+t[k:]
tp_tpl=[b for b in blocks(src,r'^\t\(symbol$') if '(property "Reference" "TP17"' in b][0]
tp_tpl=re.sub(r'\(path "[^"]+"','(path "%s"'%SHEET,tp_tpl)
pw_tpl={lib_id:[b for b in blocks(t,r'^\t\(symbol$') if '(lib_id "%s")'%lib_id in b][0] for lib_id in ('power:GND','0_power_symbols_ethrc:+3V3_PHY','0_power_symbols_ethrc:+1V2_ESC')}
HOOK={'Datasheet':'https://www.mouser.com/datasheet/3/201/1/5000_5004.pdf','Manufacturer':'Keystone Electronics','Supplier 1':'Mouser'}
TPS=[('TP76','ESC_XO','hook','5004','534-5004','Miniature PC test point, yellow, crystal output OSCO (probe with an active probe only)'),
     ('TP77','GND','hook','5001','534-5001','Miniature PC test point, black, probe ground beside TP76'),
     ('TP78','+3V3_PHY','pad'),('TP79','+1V2_ESC','pad'),('TP80','ESC_OSCVDD12','pad'),('TP81','EE_SCL','pad'),('TP82','EE_SDA','pad'),
     ('TP83','ECAT_P0_TX+','pad'),('TP84','ECAT_P0_TX-','pad'),('TP85','ECAT_P0_RX+','pad'),('TP86','ECAT_P0_RX-','pad'),
     ('TP87','ECAT_P1_TX+','pad'),('TP88','ECAT_P1_TX-','pad'),('TP89','ECAT_P1_RX+','pad'),('TP90','ECAT_P1_RX-','pad')]
POWER={'GND':'power:GND','+3V3_PHY':'0_power_symbols_ethrc:+3V3_PHY','+1V2_ESC':'0_power_symbols_ethrc:+1V2_ESC'}
pwr_n=125
a0=re.search(r'\(at ([-\d.]+) ([-\d.]+) 270\)',tp_tpl); x0,y0=float(a0.group(1)),float(a0.group(2))
add.append(text('EtherCAT test points (TP76/TP77 hooks on the BOM, the others are bare pads)',30.48,232.41,bold=True))
for i,spec in enumerate(TPS):
    ref,net,kind=spec[:3]; col,row=divmod(i,5)
    X,Y=63.5+col*63.5,240.03+row*7.62
    b=shift(newuuids(tp_tpl),X-x0,Y-y0)
    b=b.replace('(property "Reference" "TP17"','(property "Reference" "%s"'%ref).replace('(reference "TP17")','(reference "%s")'%ref)
    b=b.replace('(property "Value" "ESC_RST"','(property "Value" "%s"'%net)
    if kind=='hook':
        mpn,spn,desc=spec[3:]
        b=b.replace('(in_bom no)','(in_bom yes)').replace('"0_testpoint:TestPoint_Pad_D0.5mm"','"0_testpoint:TestPoint_Keystone_5000-5004_Miniature"')
        b=b.replace('(property "Datasheet" "~"','(property "Datasheet" "%s"'%HOOK['Datasheet']).replace('(property "Description" "test point"','(property "Description" "%s"'%desc)
        extra=''.join(hidden_prop(k,v,X,Y) for k,v in (('Manufacturer',HOOK['Manufacturer']),('Manufacturer Part Number',mpn),('Supplier 1',HOOK['Supplier 1']),('Supplier Part Number 1',spn)))
        b=b.replace('\t\t(pin "1"',extra+'\t\t(pin "1"',1)
    add.append(b)
    xl=X-5.08; add.append(wire(xl,Y,X,Y))
    if net in POWER:
        lid=POWER[net]; up=(net!='GND'); yp=Y-2.54 if up else Y+2.54
        add.append(wire(xl,Y,xl,yp))
        pb=pw_tpl[lid]; pa=re.search(r'\(at ([-\d.]+) ([-\d.]+) 0\)',pb)
        pb=shift(newuuids(pb),xl-float(pa.group(1)),yp-float(pa.group(2)))
        pb=re.sub(r'\(mirror [xy]\)\n\t\t','',pb)
        old=re.search(r'"(#PWR\d+)"',pb).group(1); pb=pb.replace('"%s"'%old,'"#PWR%03d"'%pwr_n); pwr_n+=1
        add.append(pb)
    else:
        add.append(label(net,xl,Y))
end=t.rstrip().rfind('\t(sheet_instances')
if end<0: end=t.rstrip().rfind('\n)')+1
t=t[:end]+''.join(add)+t[end:]
open(path,'w').write(t)
print('wires removed',n_w,'junctions removed',n_j,'items added',len(add),'next #PWR',pwr_n)
