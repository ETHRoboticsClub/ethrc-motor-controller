"""Redraw the net-tie bridge as a copper graphic (KiCad stock pattern) instead of a second pad numbered 1.
usage: nt_bridge.py board.kicad_pcb          -> the NetTie-2_SMD_Pad*mm footprints on a board
       nt_bridge.py --lib file.kicad_mod ... -> library footprints (old or new file format)"""
import sys,re,uuid
def block_end(t,s):
    d=0;k=s;instr=False
    while True:
        ch=t[k]
        if instr:
            if ch=='\\': k+=1
            elif ch=='"': instr=False
        elif ch=='"': instr=True
        elif ch=='(': d+=1
        elif ch==')':
            d-=1
            if d==0: return k
        k+=1
def board(path):
    t=open(path).read(); out=[]; i=0; n=0
    for m in re.finditer(r'\n\t\(footprint "0_net_tie:NetTie-2_SMD_Pad([0-9.]+)mm"',t):
        s=m.start()+1; e=block_end(t,s); blk=t[s:e+1]; w=float(m.group(1)); d=w
        pm=re.search(r'\n\t\t\(pad "1" smd rect',blk)
        if not pm: continue
        ps=pm.start()+1; pe=block_end(blk,ps)
        g=('\t\t(fp_poly\n\t\t\t(pts\n\t\t\t\t(xy %g %g) (xy %g %g) (xy %g %g) (xy %g %g)\n\t\t\t)\n\t\t\t(stroke\n\t\t\t\t(width 0)\n\t\t\t\t(type solid)\n\t\t\t)\n'
           '\t\t\t(fill yes)\n\t\t\t(layer "F.Cu")\n\t\t\t(uuid "%s")\n\t\t)')%(-d,-w/2,d,-w/2,d,w/2,-d,w/2,uuid.uuid4())
        blk=blk[:ps]+g+blk[pe+1:]
        out.append(t[i:s]); out.append(blk); i=e+1; n+=1
    out.append(t[i:]); open(path,'w').write(''.join(out)); print(path,': bridges redrawn on',n,'footprints')
def lib(path):
    t=open(path).read(); m=re.search(r'NetTie-2_SMD_Pad([0-9.]+)mm',t); w=float(m.group(1)); d=w
    pm=re.search(r'\n  \(pad "1" smd rect',t)
    if not pm: print(path,': nothing to do'); return
    ps=pm.start()+1; pe=block_end(t,ps)
    g=('  (fp_poly (pts (xy %g %g) (xy %g %g) (xy %g %g) (xy %g %g))\n    (stroke (width 0) (type solid)) (fill solid) (layer "F.Cu") (tstamp %s))')%(-d,-w/2,d,-w/2,d,w/2,-d,w/2,uuid.uuid4())
    open(path,'w').write(t[:ps]+g+t[pe+1:]); print(path,': bridge redrawn')
if sys.argv[1]=='--lib':
    for p in sys.argv[2:]: lib(p)
else: board(sys.argv[1])
