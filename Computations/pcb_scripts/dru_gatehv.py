"""HV-clearance exemption for the high-side gate nets against their own phase. usage: dru_gatehv.py file.kicad_dru
GHx and FET_GHx swing between SHx (= PHx) and about PHx + 11 V, so they never sit more than ~13 V from PHx."""
import sys
p=sys.argv[1]; t=open(p).read()
hv="""!(A.NetName == '*PHC' && B.NetName == '*SHC') && """
ex=hv+" && ".join(f"!(A.NetName == '*PH{x}' && (B.NetName == '*GH{x}' || B.NetName == '*FET_GH{x}'))" for x in 'ABC')+" && "
assert hv in t or 'FET_GHA' in t
if 'FET_GHA' not in t:
    t=t.replace(hv,ex,1)
    t=t.replace("# +VBAT against the charge-pump nodes VCP and CPH is excluded too: they ride at most ~11 V above VM.",
"# +VBAT against the charge-pump nodes VCP and CPH is excluded too: they ride at most ~11 V above VM.\n# Each high-side gate net GHx / FET_GHx is excluded against its own phase: it stays within ~13 V of PHx.")
open(p,'w').write(t); print('rules updated')
