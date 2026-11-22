"""Apply a schematic netlist (kicadxml) to a board, like Update PCB from Schematic for the cases used here:
pad nets, value / DNP / BOM fields of existing footprints, and new footprints (placed at a staging point off the board).
usage (system python with pcbnew): sync_board.py board.kicad_pcb netlist.xml libdir [stage_x stage_y]"""
import sys,xml.etree.ElementTree as ET,pcbnew
MM=pcbnew.FromMM
board,netp,libdir=sys.argv[1:4]; sx,sy=(float(sys.argv[4]),float(sys.argv[5])) if len(sys.argv)>5 else (80.0,100.0)
r=ET.parse(netp).getroot(); b=pcbnew.LoadBoard(board)
padnet={}
unesc=lambda s: s.replace('{slash}','/')
for n in r.iter('net'):
    for x in n.iter('node'): padnet[(x.get('ref'),x.get('pin'))]=unesc(n.get('name'))
bynet={}
for code,ni in b.GetNetsByNetcode().items(): bynet[unesc(ni.GetNetname())]=ni      # board keeps '/' inside a name as {slash}
have={f.GetReference():f for f in b.GetFootprints()}
SKIP_FIELDS=('Footprint','Reference','Value')
added=changed=0; k=0
for c in r.iter('comp'):
    ref=c.get('ref'); fpid=c.findtext('footprint') or ''
    props={p.get('name'):p.get('value') for p in c.iter('property')}
    if 'exclude_from_board' in props: continue
    fields={f.get('name'):(f.text or '') for f in c.iter('field')}
    f=have.get(ref)
    if f is None:
        lib,name=fpid.split(':'); f=pcbnew.FootprintLoad(libdir+'/'+lib+'.pretty',name); assert f is not None,fpid
        f.SetReference(ref); f.SetFPIDAsString(fpid)
        sp=c.find('sheetpath'); ts=sp.get('tstamps'); f.SetPath(pcbnew.KIID_PATH(ts+c.findtext('tstamps').split()[0] if ts.endswith('/') else ts+'/'+c.findtext('tstamps').split()[0]))
        f.SetSheetname(sp.get('names')); f.SetSheetfile(props.get('Sheetfile',''))
        b.Add(f); f.SetPosition(pcbnew.VECTOR2I(MM(sx+3.0*(k%10)),MM(sy+3.0*(k//10)))); k+=1; added+=1
    old=(f.GetValue(),f.IsDNP())
    f.SetValue(c.findtext('value') or '')
    f.SetDNP('dnp' in props); f.SetExcludedFromBOM('exclude_from_bom' in props); f.SetExcludedFromPosFiles('exclude_from_bom' in props and fpid.startswith('0_testpoint'))
    for kf,v in fields.items():
        if kf in SKIP_FIELDS: continue
        g=f.GetFieldByName(kf)
        if g is None: f.SetField(kf,v); g=f.GetFieldByName(kf); g.SetVisible(False)
        elif g.GetText()!=v: g.SetText(v)
    if c.findtext('datasheet'):
        g=f.GetFieldByName('Datasheet')
        if g is not None: g.SetText(c.findtext('datasheet'))
    for pad in f.Pads():
        want=padnet.get((ref,pad.GetNumber()))
        if want is None: continue
        if unesc(pad.GetNetname())!=want:
            net=bynet.get(want)
            if net is None: net=pcbnew.NETINFO_ITEM(b,want); b.Add(net); bynet[want]=net
            pad.SetNet(net); changed+=1
    if old!=(f.GetValue(),f.IsDNP()): print('  updated',ref,old,'->',(f.GetValue(),f.IsDNP()))
pcbnew.SaveBoard(board,b); print('footprints added',added,'pad nets changed',changed)
