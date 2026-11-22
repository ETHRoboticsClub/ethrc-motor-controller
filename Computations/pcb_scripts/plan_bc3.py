# stage 3: remaining bulk-cap vias and the shunt C return (executed inside plan_bc.py); each via is checked against the planned copper
def pick(net,cands,why):
    for x,y in cands:
        if W.via_margin(net,x,y)[0]>=0.0: V(net,x,y); return True
    print('  -- no free spot:',why,net,cands[0],W.via_margin(net,*cands[0])); return False
W.shift('TP64',139.65,74.82)                                                         # SHB test point on the tie link
n=0
for x in (129,131,133,135): n+=pick('GND',[(x,86.2),(x,86.3),(x-0.4,86.2)],'S1W GND')
n+=pick('GND',[(136.6,86.2),(136.5,86.3)],'S1W GND C73'); n+=pick('GND',[(141.0,87.95),(140.7,87.95)],'S1W GND C67')
n+=pick('GND',[(143.7,87.95),(143.8,88.0)],'S1W GND C84 / C105'); n+=pick('GND',[(144.9,87.95),(145.0,88.0)],'S1W GND C56 / C105'); n+=pick('GND',[(147.0,86.2),(146.95,86.3)],'S1W GND C57')
for x in (129,131,133,135): n+=pick('GND',[(x,88.4),(x,88.3)],'S3W GND')
for x in (129,131,133): n+=pick('+VBAT',[(x,91.35),(x,91.45)],'S3W VBAT')
for x in (118.9,120.9,122.9,124.9): n+=pick('+VBAT',[(x,90.2),(x,90.35)],'S2W VBAT')
for x in (118.9,120.9,122.9): n+=pick('GND',[(x,87.4),(x,87.5)],'S2W GND')
for x in (123.3,123.95,124.6,125.25,125.9): n+=pick('GND',[(x,87.95),(x,88.0)],'R30 return row')
for y in (86.5,87.15): n+=pick('GND',[(123.05,y),(122.95,y)],'R30 return west')
print('stage 3 vias placed',n)
