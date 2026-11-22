"""Minimal s-expression reader for KiCad files (read-only helpers)."""
import re
def parse(txt):
    tok=re.compile(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+')
    st=[[]]
    for m in tok.finditer(txt):
        t=m.group(0)
        if t=='(': st.append([])
        elif t==')': x=st.pop(); st[-1].append(x)
        else: st[-1].append(t[1:-1] if t[0]=='"' else t)
    return st[0][0]
def find(n,k): return [c for c in n if isinstance(c,list) and c and c[0]==k]
def one(n,k):
    r=find(n,k); return r[0] if r else None
