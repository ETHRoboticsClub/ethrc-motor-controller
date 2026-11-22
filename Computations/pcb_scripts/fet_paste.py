"""FDMT80040DC footprint: split the drain pad's solder paste into 5 x 4 windows so that via-in-pad vias sit in the streets.
usage: fet_paste.py board.kicad_pcb | fet_paste.py --lib file.kicad_mod"""
import sys,re,uuid
US=(-2.8,-1.4,0.0,1.4,2.8); VS=(-1.95,-0.65,0.65,1.95); PCY=-0.785; WIN=(0.95,0.85)
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
def windows(ind,rot):
    a=(' %g'%rot) if rot else ''
    return ''.join('\n%s(pad "" smd rect\n%s\t(at %g %g%s)\n%s\t(size %g %g)\n%s\t(layers "F.Paste")\n%s\t(uuid "%s")\n%s)'%(ind,ind,u,PCY+v,a,ind,WIN[0],WIN[1],ind,ind,uuid.uuid4(),ind) for v in VS for u in US)
def convert(blk,ind,rot):
    m=re.search(r'\n'+ind+r'\(pad "5" smd rect\n'+ind+r'\t\(at 0 -0\.785[^\n]*\n'+ind+r'\t\(size 5\.23 6\.9\)',blk)
    if not m or '(layers "F.Paste")' in blk: return blk,False
    ps=m.start()+1; pe=block_end(blk,ps); pad=blk[ps:pe+1]
    assert '(layers "F.Cu" "F.Mask" "F.Paste")' in pad
    pad=pad.replace('(layers "F.Cu" "F.Mask" "F.Paste")','(layers "F.Cu" "F.Mask")')
    return blk[:ps]+pad+windows(ind,rot)+blk[pe+1:],True
if sys.argv[1]=='--lib':
    t=open(sys.argv[2]).read(); t2,ok=convert(t,'\t',0); open(sys.argv[2],'w').write(t2); print(sys.argv[2],'converted' if ok else 'unchanged')
else:
    t=open(sys.argv[1]).read(); out=[]; i=0; n=0
    for m in re.finditer(r'\n\t\(footprint "0_transistor_fet:FDMT80040DC"',t):
        s=m.start()+1; e=block_end(t,s); blk=t[s:e+1]
        at=re.search(r'\n\t\t\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)',blk); rot=float(at.group(3) or 0)
        blk2,ok=convert(blk,'\t\t',rot); out.append(t[i:s]); out.append(blk2); i=e+1; n+=ok
    out.append(t[i:]); open(sys.argv[1],'w').write(''.join(out)); print(sys.argv[1],': paste windows on',n,'FETs')
