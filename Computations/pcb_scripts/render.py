"""Net-coloured pad map with mm grid, courtyards, zone outlines and optional markers.
usage: render.py board.kicad_pcb out.png F|B x0 y0 x1 y1 [px_per_mm] [markers.json]"""
import sys,os,json,subprocess,math
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from pcb import *
from geom import hull
COL={'+VBAT':'#e02020','GND':'#707070','PHA':'#ff9900','PHB':'#22aa22','PHC':'#2266ff','SRC_LS_A':'#aa44cc','SRC_LS_B':'#aa44cc','SRC_LS_C':'#aa44cc',
     'CHASSIS':'#8b5a2b','+3V3':'#ff66aa','+3V3_PHY':'#ff99cc','+5V':'#00bbcc','+A3V3':'#009977'}
def col(n):
    if n in COL: return COL[n]
    if n=='' or n.startswith('unconnected'): return '#ffffff'
    return '#c8c8c8'
def main():
    path,out,side=sys.argv[1:4]; x0,y0,x1,y1=map(float,sys.argv[4:8]); s=float(sys.argv[8]) if len(sys.argv)>8 else 14
    marks=json.load(open(sys.argv[9])) if len(sys.argv)>9 else []
    layer='F.Cu' if side=='F' else 'B.Cu'
    b,fps=load(path); W,H=(x1-x0)*s,(y1-y0)*s
    T=lambda x,y:(round((x-x0)*s,1),round((y-y0)*s,1))
    o=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="100%" height="100%" fill="#fafafa"/>']
    step=5 if (x1-x0)>40 else 1
    g=math.ceil(x0/step)*step
    while g<=x1:
        X=T(g,0)[0]; major=(g%(5*step if step==1 else 10)==0)
        o.append(f'<line x1="{X}" y1="0" x2="{X}" y2="{H}" stroke="#bbd" stroke-width="{1.2 if major else 0.4}"/>')
        if major: o.append(f'<text x="{X+2}" y="11" font-size="11" fill="#449">{g:g}</text>')
        g+=step
    g=math.ceil(y0/step)*step
    while g<=y1:
        Y=T(0,g)[1]; major=(g%(5*step if step==1 else 10)==0)
        o.append(f'<line x1="0" y1="{Y}" x2="{W}" y2="{Y}" stroke="#bbd" stroke-width="{1.2 if major else 0.4}"/>')
        if major: o.append(f'<text x="2" y="{Y-2}" font-size="11" fill="#449">{g:g}</text>')
        g+=step
    cx,cy=T(150,100); o.append(f'<circle cx="{cx}" cy="{cy}" r="{44*s}" fill="none" stroke="#000" stroke-width="1.5"/>')
    for z in find(b,'zone'):
        lay=one(z,'layer') or one(z,'layers')
        if layer not in lay[1:]: continue
        net=one(z,'net_name'); n=short(net[1]) if net else ''
        if n=='GND': continue
        pts=' '.join(f'{T(float(q[1]),float(q[2]))[0]},{T(float(q[1]),float(q[2]))[1]}' for q in find(one(one(z,'polygon'),'pts'),'xy'))
        c=col(n) if n else '#000'
        o.append(f'<polygon points="{pts}" fill="{c}" fill-opacity="{0.15 if n else 0.06}" stroke="{c}" stroke-width="1" stroke-dasharray="{"" if n else "6,4"}"/>')
    for f in fps:
        onside=(f.layer==layer)
        if onside and f.cy:
            h=hull(f.cy); pts=' '.join(f'{T(px,py)[0]},{T(px,py)[1]}' for px,py in h)
            o.append(f'<polygon points="{pts}" fill="none" stroke="#333" stroke-width="0.6" stroke-dasharray="3,2"/>')
        for p in f.pads:
            if not (layer in p.layers or '*.Cu' in p.layers or p.type=='thru_hole'): continue
            c=col(p.net)
            for pl in (p.polys+[p.box] if p.polys else [p.box]):
                if p.shape in('circle','oval') and not p.polys:
                    X,Y=T(p.x,p.y); o.append(f'<ellipse cx="{X}" cy="{Y}" rx="{p.w/2*s}" ry="{p.h/2*s}" fill="{c}" stroke="#333" stroke-width="0.4"/>')
                else:
                    pts=' '.join(f'{T(px,py)[0]},{T(px,py)[1]}' for px,py in pl); o.append(f'<polygon points="{pts}" fill="{c}" stroke="#333" stroke-width="0.4"/>')
            if s>=30 and onside and len(f.pads)>8:
                X,Y=T(p.x,p.y); o.append(f'<text x="{X}" y="{Y+2}" font-size="{max(5,s*0.22)}" text-anchor="middle" fill="#000">{p.num}</text>')
        if onside or any(p.type=='thru_hole' for p in f.pads):
            X,Y=T(f.x,f.y); big=len(f.pads)>4 or f.ref[0] in 'QJULTD'
            o.append(f'<text x="{X}" y="{Y}" font-size="{max(7,min(14,s*0.5)) if big else max(6,s*0.33)}" text-anchor="middle" fill="#000" font-weight="{"bold" if big else "normal"}">{f.ref}</text>')
    # draw vias and tracks
    nets={n[1]:(short(n[2]) if len(n)>2 else '') for n in find(b,'net')}
    for sgm in find(b,'segment'):
        if one(sgm,'layer')[1]!=layer: continue
        a1=one(sgm,'start'); a2=one(sgm,'end'); w=float(one(sgm,'width')[1]); n=nets.get(one(sgm,'net')[1],'')
        X1,Y1=T(float(a1[1]),float(a1[2])); X2,Y2=T(float(a2[1]),float(a2[2]))
        o.append(f'<line x1="{X1}" y1="{Y1}" x2="{X2}" y2="{Y2}" stroke="{col(n) if n in COL else "#0a8"}" stroke-width="{w*s}" stroke-linecap="round" stroke-opacity="0.85"/>')
    for v in find(b,'via'):
        a1=one(v,'at'); X,Y=T(float(a1[1]),float(a1[2])); r=float(one(v,'size')[1])/2*s; n=nets.get(one(v,'net')[1],'')
        o.append(f'<circle cx="{X}" cy="{Y}" r="{r}" fill="{col(n)}" stroke="#000" stroke-width="0.8"/><circle cx="{X}" cy="{Y}" r="{r*0.45}" fill="#fff"/>')
    R={f.ref:f for f in fps}
    for m in marks:
        if m.get('side','F')!=side: continue
        X,Y=T(m['x'],m['y']); rr=(0.2 if 'D0.4' in m.get('fp','') else 0.25)*s
        a=m.get('anchor','')
        if '.' in a and a.split('.')[0] in R:
            pp=[p for p in R[a.split('.')[0]].pads if p.num==a.split('.')[1]]
            if pp: ax,ay=T(pp[0].x,pp[0].y); o.append(f'<line x1="{X}" y1="{Y}" x2="{ax}" y2="{ay}" stroke="#0000ff" stroke-width="1"/>')
        o.append(f'<circle cx="{X}" cy="{Y}" r="{rr}" fill="#ffee00" stroke="#0000ff" stroke-width="1.2"/>')
        o.append(f'<text x="{X+rr+2}" y="{Y-rr}" font-size="{max(8,s*0.3)}" fill="#0000cc" font-weight="bold">{m["ref"]} {m.get("net","").split("/")[-1]}</text>')
    o.append('</svg>'); svg=out.replace('.png','.svg'); open(svg,'w').write('\n'.join(o)); subprocess.run(['rsvg-convert',svg,'-o',out],check=True)
if __name__=="__main__": main()
