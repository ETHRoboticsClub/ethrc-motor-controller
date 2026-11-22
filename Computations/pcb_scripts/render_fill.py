"""Filled-copper picture of one copper layer: zone fills, tracks, pads and vias coloured by net, mm grid, board edge.
usage (system python with pcbnew): render_fill.py board.kicad_pcb out.png LAYER x0 y0 x1 y1 [px_per_mm] [refs]
LAYER: F.Cu, In1.Cu .. In4.Cu, B.Cu. refs: comma list of references to label (default: all in the window)."""
import sys,os,math,subprocess,pcbnew
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from render import COL
M=pcbnew.ToMM
EXTRA={'SW_5V':'#e8a000','CHASSIS':'#8b5a2b'}
def col(n):
    n=n.split('/')[-1]
    if n in EXTRA: return EXTRA[n]
    if n in COL: return COL[n]
    return '#b0b0b0' if n else '#ffffff'
def main():
    path,out,lname=sys.argv[1:4]; x0,y0,x1,y1=map(float,sys.argv[4:8]); s=float(sys.argv[8]) if len(sys.argv)>8 else 20
    only=set(sys.argv[9].split(',')) if len(sys.argv)>9 else None
    b=pcbnew.LoadBoard(path); L=b.GetLayerID(lname); W,H=(x1-x0)*s,(y1-y0)*s
    T=lambda x,y:'%.1f,%.1f'%((x-x0)*s,(y-y0)*s)
    o=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H:.0f}"><rect width="100%" height="100%" fill="#fafafa"/>']
    for g in range(math.ceil(x0),int(x1)+1):
        X=(g-x0)*s; o.append(f'<line x1="{X}" y1="0" x2="{X}" y2="{H}" stroke="#d8d8ee" stroke-width="{1.2 if g%5==0 else 0.4}"/>')
        if g%5==0: o.append(f'<text x="{X+2}" y="12" font-size="12" fill="#449">{g}</text>')
    for g in range(math.ceil(y0),int(y1)+1):
        Y=(g-y0)*s; o.append(f'<line x1="0" y1="{Y}" x2="{W}" y2="{Y}" stroke="#d8d8ee" stroke-width="{1.2 if g%5==0 else 0.4}"/>')
        if g%5==0: o.append(f'<text x="2" y="{Y-2}" font-size="12" fill="#449">{g}</text>')
    def poly(ps,fill,op,stroke='none'):
        for i in range(ps.OutlineCount()):
            d='M'+' L'.join(T(M(p.x),M(p.y)) for p in [ps.Outline(i).CPoint(j) for j in range(ps.Outline(i).PointCount())])+' Z'
            for h in range(ps.HoleCount(i)):
                hl=ps.Hole(i,h); d+=' M'+' L'.join(T(M(hl.CPoint(j).x),M(hl.CPoint(j).y)) for j in range(hl.PointCount()))+' Z'
            o.append(f'<path d="{d}" fill="{fill}" fill-opacity="{op}" fill-rule="evenodd" stroke="{stroke}" stroke-width="0.8"/>')
    for z in b.Zones():
        if z.GetIsRuleArea() or not z.IsOnLayer(L): continue
        poly(z.GetFilledPolysList(L),col(z.GetNetname()),0.45)
    for t in b.Tracks():
        if t.GetClass()=='PCB_VIA': continue
        if t.GetLayer()!=L: continue
        o.append(f'<line x1="{(M(t.GetStart().x)-x0)*s:.1f}" y1="{(M(t.GetStart().y)-y0)*s:.1f}" x2="{(M(t.GetEnd().x)-x0)*s:.1f}" y2="{(M(t.GetEnd().y)-y0)*s:.1f}" stroke="{col(t.GetNetname())}" stroke-width="{M(t.GetWidth())*s:.1f}" stroke-linecap="round"/>')
    labels={}
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if not p.IsOnLayer(L): continue
            poly(p.GetEffectivePolygon(L,pcbnew.ERROR_INSIDE),col(p.GetNetname()),0.95,'#333')
            if p.HasHole():
                x,y=M(p.GetPosition().x),M(p.GetPosition().y); o.append(f'<circle cx="{(x-x0)*s:.1f}" cy="{(y-y0)*s:.1f}" r="{M(p.GetDrillSize().x)/2*s:.1f}" fill="white"/>')
        x,y=M(fp.GetPosition().x),M(fp.GetPosition().y)
        if x0<x<x1 and y0<y<y1 and (only is None or fp.GetReference() in only) and any(p.IsOnLayer(L) for p in fp.Pads()): labels[fp.GetReference()]=(x,y)
    for t in b.Tracks():
        if t.GetClass()!='PCB_VIA': continue
        x,y=M(t.GetPosition().x),M(t.GetPosition().y)
        if not(x0-1<x<x1+1 and y0-1<y<y1+1): continue
        o.append(f'<circle cx="{(x-x0)*s:.1f}" cy="{(y-y0)*s:.1f}" r="{M(t.GetWidth(L))/2*s:.1f}" fill="{col(t.GetNetname())}" stroke="#222" stroke-width="0.8"/><circle cx="{(x-x0)*s:.1f}" cy="{(y-y0)*s:.1f}" r="{M(t.GetDrillValue())/2*s:.1f}" fill="white"/>')
    o.append(f'<circle cx="{(150-x0)*s:.1f}" cy="{(100-y0)*s:.1f}" r="{44*s:.1f}" fill="none" stroke="black" stroke-width="1.5"/>')
    for r,(x,y) in labels.items():
        o.append(f'<text x="{(x-x0)*s:.1f}" y="{(y-y0)*s:.1f}" font-size="{max(10,s*0.6):.0f}" font-family="sans-serif" font-weight="bold" fill="#000" stroke="#fff" stroke-width="2.5" paint-order="stroke" text-anchor="middle">{r}</text>')
    o.append('</svg>'); sv=out[:-4]+'.svg'; open(sv,'w').write('\n'.join(o))
    subprocess.run(['rsvg-convert',sv,'-o',out],check=True); os.remove(sv)
main()
