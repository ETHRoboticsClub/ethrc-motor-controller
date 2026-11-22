"""Add test point footprints to a board from the schematic netlist data (what Update PCB from Schematic does).
usage (system python with pcbnew): tp_import.py board.kicad_pcb comps.json placement.json libdir"""
import sys,json,pcbnew
MM=pcbnew.FromMM
def main():
    path,comps_p,place_p,libdir=sys.argv[1:5]
    comps=json.load(open(comps_p)); place={p['ref']:p for p in json.load(open(place_p))}
    b=pcbnew.LoadBoard(path); have={f.GetReference() for f in b.GetFootprints()}; n=0
    for ref,pl in place.items():
        if ref in have: continue
        c=comps[ref]; lib,name=c['fp'].split(':')
        fp=pcbnew.FootprintLoad(libdir,name); assert fp is not None,name
        fp.SetReference(ref); fp.SetValue(c['value']); fp.SetFPIDAsString(c['fp'])
        fp.SetPath(pcbnew.KIID_PATH(c['sheet_ts']+c['ts'])); fp.SetSheetname(c['sheet_names']); fp.SetSheetfile(c['props']['Sheetfile'])
        for k,v in c['fields'].items():
            if k in ('Footprint',): continue
            if k in ('Datasheet','Description'):
                f=fp.GetFieldByName(k)
                if f is not None: f.SetText(v)
                continue
            fp.SetField(k,v)
            f=fp.GetFieldByName(k)
            if f is not None: f.SetVisible(False)
        fp.SetExcludedFromBOM(True); fp.SetExcludedFromPosFiles(True)
        net=b.FindNet(c['net']); assert net is not None,c['net']
        b.Add(fp)
        fp.SetPosition(pcbnew.VECTOR2I(MM(pl['x']),MM(pl['y'])))
        if pl['side']=='B': fp.Flip(fp.GetPosition(),pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        for pad in fp.Pads(): pad.SetNet(net)
        n+=1
    b.BuildConnectivity()
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(path,b); print('added',n,'test points; footprints now',len(b.GetFootprints()))
main()
